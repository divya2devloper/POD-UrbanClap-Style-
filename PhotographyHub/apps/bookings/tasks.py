import logging
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
def track_booking_ripple(self, booking_id, is_premium_pass=True):
    """
    Task to expand the ping radius for a specific booking.
    Handles:
    - 5 min priority for Premium Photographers.
    - 2-4 hour Radar Expiry.
    - Radius expansion up to 60km.
    """
    from django.utils import timezone
    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            
            # 1. Stop if already assigned or cancelled
            if booking.status != Booking.Status.PENDING:
                logger.info(f"Booking {booking_id} status is {booking.status}. Stopping ripple.")
                return

            # 2. Check Expiry (Radar Logic)
            if booking.expires_at and timezone.now() > booking.expires_at:
                booking.status = Booking.Status.CANCELLED
                booking.save(update_fields=["status"])
                logger.info(f"Booking {booking_id} expired. Radar closed.")
                # Send notification to customer?
                return

            # 3. Find matching photographers for current radius
            matches = find_matching_photographers(booking, premium_only=is_premium_pass)
            
            if matches:
                notify_photographers(booking, matches)
            
            # 4. Schedule next step
            if is_premium_pass:
                # After 5 mins of premium priority, notify everyone in the same radius
                track_booking_ripple.apply_async(
                    (booking_id,), 
                    kwargs={"is_premium_pass": False}, 
                    countdown=300
                )
                logger.info(f"Premium pass done for Booking {booking_id}. Standard pass scheduled in 5m.")
            else:
                # Standard pass done, expand radius if under 60km
                if booking.current_ping_radius < 60:
                    booking.current_ping_radius += 5
                    booking.save(update_fields=["current_ping_radius"])
                    
                    # Restart with premium pass for the new radius
                    track_booking_ripple.apply_async(
                        (booking_id,), 
                        kwargs={"is_premium_pass": True}, 
                        countdown=300
                    )
                    logger.info(f"Radius expanded to {booking.current_ping_radius}km for Booking {booking_id}.")
                else:
                    logger.info(f"Max radius reached for Booking {booking_id}. Monitoring radar.")
                    # We might still want to check for expiry every 10 mins if no expansion left
                    track_booking_ripple.apply_async(
                        (booking_id,), 
                        kwargs={"is_premium_pass": False}, 
                        countdown=600
                    )

    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} does not exist.")
    except Exception as e:
        logger.exception(f"Error in ripple task for Booking {booking_id}: {str(e)}")
        raise self.retry(exc=e)

def find_matching_photographers(booking, premium_only=False):
    """
    Identify photographers within the current ping radius.
    """
    booking_coords = (booking.customer_latitude, booking.customer_longitude)
    
    # Base filter
    filters = {
        "is_available": True,
        "categories": booking.category
    }
    
    if premium_only:
        filters["is_premium_partner"] = True
        
    photographers = PhotographerProfile.objects.filter(**filters).exclude(
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
    
    for profile in matches:
        # Notify via Channels
        async_to_sync(channel_layer.group_send)(
            f"user_{profile.user.id}",
            {
                "type": "booking_alert",
                "booking_id": booking.id,
                "category": booking.category.name,
                "radius": booking.current_ping_radius,
                "message": f"New {booking.category.name} job available within {booking.current_ping_radius}km!"
            }
        )
        new_notified_ids.append(profile.user.id)
        
    booking.notified_photographer_ids = new_notified_ids
    booking.save()
