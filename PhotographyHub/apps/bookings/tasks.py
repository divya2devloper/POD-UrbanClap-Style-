import math

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.db import transaction

from apps.accounts.models import PhotographerProfile
from apps.bookings.models import Booking

RIPPLE_INCREMENT_KM = 5
RIPPLE_MAX_RADIUS_KM = 60


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    r_lat1 = math.radians(lat1)
    r_lat2 = math.radians(lat2)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(r_lat1) * math.cos(r_lat2) * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * c


def _notify_photographer(photographer_user_id: int, booking_id: int, distance_km: float) -> None:
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    async_to_sync(channel_layer.group_send)(
        f"photographer_{photographer_user_id}",
        {
            "type": "booking.ping",
            "booking_id": booking_id,
            "distance_km": round(distance_km, 2),
        },
    )


@shared_task
def expand_ripple_logic() -> None:
    pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING)

    for booking in pending_bookings:
        with transaction.atomic():
            locked_booking = Booking.objects.select_for_update().get(pk=booking.pk)
            if locked_booking.status != Booking.Status.PENDING:
                continue

            new_radius = min(
                locked_booking.current_ping_radius + RIPPLE_INCREMENT_KM,
                RIPPLE_MAX_RADIUS_KM,
            )
            if new_radius != locked_booking.current_ping_radius:
                locked_booking.current_ping_radius = new_radius
                locked_booking.save(update_fields=["current_ping_radius", "updated_at"])

            photographers = PhotographerProfile.objects.select_related("user").all().iterator()
            for profile in photographers:
                distance = haversine_km(
                    float(locked_booking.customer_latitude),
                    float(locked_booking.customer_longitude),
                    float(profile.base_latitude),
                    float(profile.base_longitude),
                )
                if (
                    distance <= float(locked_booking.current_ping_radius)
                    and distance <= float(profile.max_travel_radius)
                ):
                    _notify_photographer(profile.user_id, locked_booking.id, distance)
