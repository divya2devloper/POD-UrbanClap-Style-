from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking, Category


DEFAULT_CATEGORIES = [
    {"name": "Wedding", "slug": "wedding", "description": "Candid, cinematic and traditional wedding coverage."},
    {"name": "Product", "slug": "product", "description": "Catalog, ecommerce and brand-ready product shoots."},
    {"name": "Event", "slug": "event", "description": "Corporate, private and social event storytelling."},
]


def homepage(request):
    categories = Category.objects.order_by("name")
    source_categories = categories if categories.exists() else DEFAULT_CATEGORIES
    category_blocks = []
    for category in source_categories:
        category_name = category.name if isinstance(category, Category) else category["name"]
        category_slug = category.slug if isinstance(category, Category) else category["slug"]
        category_description = category.description if isinstance(category, Category) else category["description"]
        category_blocks.append(
            {
                "name": category_name,
                "slug": category_slug,
                "description": category_description,
                "media_types": ["Video", "Photo", "Reel", "Drone Shots"],
            }
        )
    return render(request, "home/homepage.html", {"category_blocks": category_blocks})


def photographer_dashboard(request):
    pending_bookings = Booking.objects.filter(status=Booking.Status.PENDING).select_related("category").order_by("-created_at")[:25]
    category_boxes = list(Category.objects.order_by("name")[:6])
    if not category_boxes:
        category_boxes = [item["name"] for item in DEFAULT_CATEGORIES]
    return render(request, "bookings/photographer_dashboard.html", {"bookings": pending_bookings, "category_boxes": category_boxes})


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
