from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Booking, BookingPing
from .utils import haversine_distance
from apps.accounts.models import PhotographerProfile
import logging

logger = logging.getLogger(__name__)

MAX_PING_RADIUS = 60.0
RADIUS_INCREMENT = 5.0


@shared_task
def expand_ripple_logic():
    """
    Celery task that runs every 5 minutes.
    For each Pending booking:
    1. Increases current_ping_radius by 5km (capped at 60km)
    2. Finds photographers whose home base is within the ping radius AND within their max_travel_radius
    3. Sends a WebSocket ping to those photographers
    """
    pending_bookings = Booking.objects.filter(status='Pending')
    channel_layer = get_channel_layer()

    for booking in pending_bookings:
        if booking.current_ping_radius < MAX_PING_RADIUS:
            booking.current_ping_radius = min(
                booking.current_ping_radius + RADIUS_INCREMENT,
                MAX_PING_RADIUS
            )
            booking.save(update_fields=['current_ping_radius'])

        available_photographers = PhotographerProfile.objects.filter(is_available=True)
        pinged_photographer_ids = set(BookingPing.objects.filter(
            booking=booking
        ).values_list('photographer_id', flat=True))

        for photographer in available_photographers:
            if photographer.id in pinged_photographer_ids:
                continue

            distance = haversine_distance(
                booking.customer_latitude,
                booking.customer_longitude,
                photographer.base_latitude,
                photographer.base_longitude,
            )

            if distance <= booking.current_ping_radius and distance <= photographer.max_travel_radius:
                BookingPing.objects.get_or_create(
                    booking=booking,
                    photographer=photographer,
                )

                try:
                    async_to_sync(channel_layer.group_send)(
                        f"photographer_{photographer.user.id}",
                        {
                            "type": "new_booking_ping",
                            "booking_id": booking.id,
                            "service_name": booking.service_name,
                            "customer_address": booking.customer_address,
                            "scheduled_at": booking.scheduled_at.isoformat(),
                            "budget": str(booking.budget) if booking.budget else None,
                            "distance_km": round(distance, 2),
                        }
                    )
                    logger.info(f"Pinged photographer {photographer.user.id} for booking {booking.id}")
                except Exception as e:
                    logger.error(f"Failed to send WebSocket ping: {e}")
