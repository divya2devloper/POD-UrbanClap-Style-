import logging
from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.db.models import F
from geopy.distance import geodesic
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.bookings.models import Booking
from apps.accounts.models import PhotographerProfile

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=12)
def track_booking_ripple(self, booking_id, step=0):
    """
    Refined Dispatch Logic:
    - Step 0 (0-10 min): Premium Only (in their radius)
    - Step 1 (10-15 min): Tier 1 (0–5km)
    - Step 2 (15-20 min): Tier 2 (5–7km)
    - Step 3 (20-25 min): Tier 3 (7–10km)
    - After Step 3: Wait 2 hours (or 4h if saved) then cancel.
    """
    from django.utils import timezone
    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            
            if booking.status != Booking.Status.PENDING:
                logger.info(f"Booking {booking_id} status is {booking.status}. Stopping ripple.")
                return

            now = timezone.now()
            
            # Dynamic Expiry Logic
            # Default expiry for Step 3 is 2 hours after Step 3 starts.
            # If saved, it expands to 4 hours.
            if step > 3:
                # Check if it has been unassigned for 2 hours since Step 3
                # Or 4 hours if saved.
                wait_time = timedelta(hours=4) if booking.is_saved_by_photographer else timedelta(hours=2)
                if booking.expires_at and now > booking.expires_at:
                    booking.status = Booking.Status.CANCELLED
                    booking.save(update_fields=["status"])
                    send_whatsapp_notification(booking, "deny")
                    return
                
                # Check again in 30 mins
                track_booking_ripple.apply_async((booking_id,), kwargs={"step": 4}, countdown=1800)
                return

            if step == 0:
                # Step 0: Premium Only, use max potential radius (e.g. 60km) to find all premium partners
                # we'll use a large radius but find_matching_photographers handles individual profile.max_travel_radius
                booking.current_ping_radius = 60 
                matches = find_matching_photographers(booking, premium_only=True)
            else:
                tier_map = {1: 5, 2: 7, 3: 10}
                booking.current_ping_radius = tier_map.get(step, 10)
                matches = find_matching_photographers(booking, premium_only=False)

            booking.save(update_fields=["current_ping_radius"])

            if matches:
                notify_photographers(booking, matches)
            
            # Schedule next step
            next_step = step + 1
            countdown = 300 # Default 5 mins
            if step == 0:
                countdown = 600 # 10 minute premium priority
            
            if step == 3:
                # Step 3 reached, set expiry to 2h from now (or 4h if saved later)
                booking.expires_at = now + timedelta(hours=2)
                booking.save(update_fields=["expires_at"])
                next_step = 4
                countdown = 600 # Check every 10 mins for expiry or status change

            track_booking_ripple.apply_async(
                (booking_id,), 
                kwargs={"step": next_step}, 
                countdown=countdown
            )
            logger.info(f"Step {step} done for Booking {booking_id}. Next step in {countdown}s.")

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} does not exist.")
    except Exception as e:
        logger.exception(f"Error in ripple task for Booking {booking_id}: {str(e)}")
        raise self.retry(exc=e)

def send_whatsapp_notification(booking, type="confirm"):
    """
    Placeholder for WhatsApp Business API integration.
    Types: "confirm" (Assigned), "deny" (Cancelled/Expired)
    """
    customer_phone = getattr(booking.customer, "phone", "N/A")
    logger.info(f"WHATSAPP: Sending {type} message to {customer_phone} for Booking #{booking.id}")

@shared_task
def check_upload_deadline(booking_id):
    """
    Checks if 48 hours have passed since end_qr_scanned_at and if 3 links are uploaded.
    If not, applies a 20% penalty.
    """
    try:
        booking = Booking.objects.get(pk=booking_id)
        if not (booking.gallery_link1 and booking.gallery_link2 and booking.gallery_link3):
            booking.upload_penalty_applied = True
            booking.save()
            logger.info(f"20% Upload Penalty applied to Booking {booking_id}.")
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found for deadline check.")
    except Exception as e:
        logger.exception(f"Error in deadline check for Booking {booking_id}: {str(e)}")

def find_matching_photographers(booking, premium_only=False):
    """
    Identify photographers within the current ping radius.
    Matches photographers who offer ANY of the services selected in the booking.
    """
    from apps.bookings.models import Category
    booking_coords = (booking.customer_latitude, booking.customer_longitude)
    
    # 1. Determine required category names based on booking booleans
    required_service_names = []
    if booking.has_photo: required_service_names.append("Photos")
    if booking.has_video: required_service_names.append("Videos")
    if booking.has_shorts: required_service_names.append("Shorts (< 2 min)")
    if booking.has_drone: required_service_names.append("Drone")

    if not required_service_names:
        # Default fallback if somehow none selected
        required_service_names = ["Photos"]

    # 2. Get the corresponding Category IDs
    required_category_ids = Category.objects.filter(name__in=required_service_names).values_list('id', flat=True)
    
    # 3. Base filter: available and offers at least one of the required services
    filters = {
        "is_available": True,
        "categories__id__in": required_category_ids,
    }
    
    if premium_only:
        filters["is_premium_partner"] = True
        # If booking has a specific category (Expertise field), prioritize those experts in Step 0
        if booking.category_id:
            filters["categories__id"] = booking.category_id
        
    photographers = PhotographerProfile.objects.filter(**filters).distinct().exclude(
        user_id__in=booking.notified_photographer_ids
    )

    
    matches = []
    
    for profile in photographers:
        photog_coords = (profile.base_latitude, profile.base_longitude)
        distance = geodesic(booking_coords, photog_coords).km
        
        # Check if within booking's current ping AND photographer's max travel radius
        if distance <= booking.current_ping_radius and distance <= profile.max_travel_radius:
            matches.append(profile)
            
    return matches

def notify_photographers(booking, matches):
    """
    Send real-time alerts via Django Channels.
    """
    channel_layer = get_channel_layer()
    
    new_notified_ids = list(booking.notified_photographer_ids)
    
    # Generate dynamic service string
    services_list = []
    if booking.has_photo: services_list.append("Photo")
    if booking.has_video: services_list.append("Video")
    if booking.has_shorts: services_list.append("Shorts")
    if booking.has_drone: services_list.append("Drone")
    services_str = ", ".join(services_list) or "Photography"

    for profile in matches:
        # Notify via Channels
        async_to_sync(channel_layer.group_send)(
            f"user_{profile.user.id}",
            {
                "type": "booking_alert",
                "booking_id": booking.id,
                "category": services_str,
                "radius": booking.current_ping_radius,
                "message": f"New {services_str} job available within {booking.current_ping_radius}km!"
            }
        )
        new_notified_ids.append(profile.user.id)
        
    booking.notified_photographer_ids = new_notified_ids
    booking.save()
