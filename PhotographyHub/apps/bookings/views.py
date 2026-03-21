from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking


def photographer_dashboard(request):
    pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING).order_by("-created_at")[:25]
    return render(request, "bookings/photographer_dashboard.html", {"bookings": pending_bookings})


@require_POST
def accept_job(request, booking_id: int):
    with transaction.atomic():
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=booking_id)
        if booking.status != Booking.Status.PENDING:
            return JsonResponse({"detail": "Job already taken"}, status=409)

        booking.status = Booking.Status.ASSIGNED
        if request.user.is_authenticated:
            booking.assigned_photographer = request.user
        booking.save(update_fields=["status", "assigned_photographer"])

    return JsonResponse({"detail": "Booking assigned successfully", "booking_id": booking.id})
