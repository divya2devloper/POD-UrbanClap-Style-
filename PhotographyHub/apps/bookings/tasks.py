from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from apps.accounts.models import PhotographerProfile
from apps.bookings.models import Booking
from apps.bookings.utils import haversine_distance_km


@shared_task
def expand_ripple_logic():
    channel_layer = get_channel_layer()
    pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING).only(
        "id", "customer_latitude", "customer_longitude", "current_ping_radius"
    )

    photographers = list(
        PhotographerProfile.objects.select_related("user").only(
            "user_id", "base_latitude", "base_longitude", "max_travel_radius"
        )
    )

    for booking in pending_bookings:
        next_radius = min(booking.current_ping_radius + 5, 60)
        if next_radius != booking.current_ping_radius:
            booking.current_ping_radius = next_radius
            booking.save(update_fields=["current_ping_radius"])

        booking_lat = float(booking.customer_latitude)
        booking_lon = float(booking.customer_longitude)

        for photographer in photographers:
            distance_km = haversine_distance_km(
                booking_lat,
                booking_lon,
                float(photographer.base_latitude),
                float(photographer.base_longitude),
            )
            if distance_km <= booking.current_ping_radius and distance_km <= photographer.max_travel_radius:
                async_to_sync(channel_layer.group_send)(
                    f"photographer_{photographer.user_id}",
                    {
                        "type": "booking_ping",
                        "booking_id": booking.id,
                        "distance_km": round(distance_km, 2),
                        "ping_radius_km": booking.current_ping_radius,
                    },
                )
