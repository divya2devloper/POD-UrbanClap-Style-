from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking


@require_POST
@transaction.atomic
def accept_job(request, booking_id):
    booking = Booking.objects.select_for_update().filter(pk=booking_id).first()
    if booking is None:
        return JsonResponse({"detail": "Booking not found."}, status=404)

    if booking.status != Booking.Status.PENDING:
        return JsonResponse({"detail": "Job already taken."}, status=409)

    booking.status = Booking.Status.ASSIGNED
    booking.assigned_photographer = request.user
    booking.save(update_fields=["status", "assigned_photographer", "updated_at"])
    return JsonResponse({"detail": "Job accepted.", "booking_id": booking.id}, status=200)
