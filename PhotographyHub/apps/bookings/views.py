import logging
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking, Category
from apps.bookings.tasks import track_booking_ripple

logger = logging.getLogger(__name__)

DEFAULT_CATEGORIES = [
    {"name": "Wedding", "slug": "wedding", "description": "Candid, cinematic, and traditional wedding coverage."},
    {"name": "Pre-Wedding", "slug": "pre-wedding", "description": "Romantic and cinematic pre-wedding storytelling."},
    {"name": "Maternity", "slug": "maternity", "description": "Beautiful maternity and pregnancy portraits."},
    {"name": "Baby/Kids", "slug": "baby-kids", "description": "Cute and playful baby and children photography."},
    {"name": "Fashion", "slug": "fashion", "description": "High-end fashion and editorial photography."},
    {"name": "Food", "slug": "food", "description": "Mouth-watering food and culinary photography."},
    {"name": "Interior", "slug": "interior", "description": "Architectural and interior design photography."},
    {"name": "Product", "slug": "product", "description": "Professional product and e-commerce shoots."},
    {"name": "Branding/Headshots", "slug": "branding-headshots", "description": "Corporate headshots and personal branding."},
    {"name": "Corporate Events", "slug": "corporate-events", "description": "Conferences, seminars, and corporate ceremonies."},
]


def homepage(request):
    """
    Main portal landing page.
    """
    # Use database categories
    categories = list(Category.objects.order_by("name"))
    
    category_blocks = []
    for c in categories:
        # Prioritize the database field, fallback to Unsplash default if empty
        p_url = c.placeholder_url or "https://images.unsplash.com/photo-1542038783-0219c819321e?auto=format&fit=crop&w=800&q=80"
        
        category_blocks.append({
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "placeholder_url": p_url,
            "media_types": ["Video", "Photo", "Reel", "Drone Shots"],
            "is_corporate": "Corporate" in c.name
        })
        
    return render(request, "home/homepage.html", {"category_blocks": category_blocks})


def photographer_dashboard(request):
    """
    Feed for photographers + Financial Stats.
    """
    if not request.user.is_authenticated:
        return render(request, "accounts/login.html")

    # 1. Job Feed
    pending_bookings = Booking.objects.filter(
        status=Booking.Status.PENDING
    ).select_related("category").order_by("-created_at")[:50]
    
    # 2. Financial Stats for CURRENT photographer
    stats = Booking.objects.filter(assigned_photographer=request.user).aggregate(
        total_earned=Sum("total_amount", filter=Q(status=Booking.Status.ASSIGNED)),
        pending_payouts=Sum("total_amount", filter=Q(status=Booking.Status.ASSIGNED, is_payout_completed=False)),
        completed_count=Count("id", filter=Q(status=Booking.Status.ASSIGNED, is_payout_completed=True))
    )
    
    # Financial History
    work_history = Booking.objects.filter(
        assigned_photographer=request.user
    ).select_related("category").order_by("-created_at")[:20]

    category_boxes = Category.objects.order_by("name")
    
    return render(request, "bookings/photographer_dashboard.html", {
        "bookings": pending_bookings,
        "category_boxes": category_boxes,
        "stats": stats,
        "work_history": work_history
    })


@login_required
def admin_dashboard(request):
    """
    Platform-wide analytics for Administrators.
    """
    if not request.user.is_staff:
        return JsonResponse({"detail": "Admin access required."}, status=403)

    platform_stats = Booking.objects.aggregate(
        total_revenue=Sum("total_amount"),
        total_gst=Sum("gst_amount"),
        pending_payouts=Sum("total_amount", filter=Q(is_payout_completed=False)),
        total_bookings=Count("id")
    )
    
    recent_activity = Booking.objects.select_related("customer", "category", "assigned_photographer").order_by("-created_at")[:20]
    
    return render(request, "bookings/admin_dashboard.html", {
        "stats": platform_stats,
        "recent_activity": recent_activity
    })


@require_POST
def accept_job(request, booking_id: int):
    """
    Atomic job selection using select_for_update to prevent double assignment.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"detail": "Authentication required"}, status=401)
        
    try:
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(pk=booking_id)
            
            if booking.status != Booking.Status.PENDING:
                return JsonResponse({"detail": "Job already taken or invalid state."}, status=409)

            booking.assigned_photographer = request.user
            booking.status = Booking.Status.ASSIGNED
            booking.payout_ready_at = timezone.now() + timedelta(days=7)
            booking.save(update_fields=["status", "assigned_photographer", "payout_ready_at"])

        # Simulated Notifications
        logger.info(f"NOTIF: Confirmation sent to customer {booking.customer.email if booking.customer else 'N/A'}")
        logger.info(f"NOTIF: Project Start alert sent to customer and photographer.")

        return JsonResponse({
            "detail": "Booking assigned successfully. Payout scheduled for 7 days.",
            "booking_id": booking.id,
            "status": "success"
        })
        
    except Booking.DoesNotExist:
        return JsonResponse({"detail": "Booking not found."}, status=404)
    except Exception as e:
        logger.exception(f"Error accepting job {booking_id}: {str(e)}")
        return JsonResponse({"detail": str(e)}, status=500)


@login_required
def customer_dashboard(request):
    """
    Personal dashboard for users to manage their bookings and profile.
    """
    bookings = Booking.objects.filter(customer=request.user).select_related("category", "assigned_photographer").order_by("-created_at")
    
    stats = {
        "total_spent": bookings.aggregate(Sum("total_amount"))["total_amount__sum"] or 0,
        "total_shoots": bookings.count(),
        "active_bookings": bookings.filter(status=Booking.Status.PENDING).count()
    }
    
    return render(request, "bookings/customer_dashboard.html", {
        "bookings": bookings,
        "stats": stats
    })


@require_POST
@login_required
def update_profile(request):
    """
    CRUD control for personal user data.
    """
    user = request.user
    user.username = request.POST.get("username", user.username)
    # Note: email is managed by allauth, we don't allow casual updates here for security
    user.save()
    
    return JsonResponse({"status": "success", "detail": "Profile updated successfully."})


@require_POST
@login_required
def save_booking(request, booking_id):
    """
    Allows a photographer to 'save' a booking, which expands the radar expiry to 4 hours.
    """
    booking = get_object_or_404(Booking, pk=booking_id)
    if not booking.is_saved_by_photographer:
        booking.is_saved_by_photographer = True
        booking.expires_at = booking.created_at + timedelta(hours=4)
        booking.save(update_fields=["is_saved_by_photographer", "expires_at"])
        return JsonResponse({"detail": "Booking saved. Radar expanded to 4 hours."})
    return JsonResponse({"detail": "Booking already saved."})


@require_POST
@login_required
def create_booking(request):
    """
    Create a new booking and trigger the ripple search engine.
    """
    category_id = request.POST.get("category_id")
    if not category_id:
        return JsonResponse({"detail": "Category ID is required."}, status=400)
        
    category = get_object_or_404(Category, pk=category_id)
    
    # Create booking with default Ahmedabad coords for now
    duration_hours = int(request.POST.get("duration_hours", 4))
    
    # Matches base.html logic (Extended for 1,2,3h)
    # Wedding, Pre-Wedding, and Maternity are the SAME premium tier
    is_premium = any(x in category.name for x in ['Wedding', 'Pre-Wedding', 'Maternity'])
    
    priceMap = {
        "Premium": {1: 3000, 2: 5000, 3: 6500, 4: 8000, 6: 12000, 8: 16000},
        "Normal": {1: 1500, 2: 2500, 3: 3500, 4: 4000, 6: 6000, 8: 8000}
    }
    
    profile = "Premium" if is_premium else "Normal"
    base_price = priceMap[profile].get(duration_hours) or (1500 * duration_hours)

    booking = Booking.objects.create(
        customer=request.user,
        category=category,
        customer_latitude=23.0225,
        customer_longitude=72.5714,
        duration_hours=duration_hours,
        base_price=base_price,
        status=Booking.Status.PENDING,
        expires_at=timezone.now() + timedelta(hours=2)
    )
    
    # Trigger the independent ripple search for THIS specific booking
    track_booking_ripple.delay(booking.id)
    
    return JsonResponse({
        "status": "success",
        "booking_id": booking.id,
        "detail": f"Booking created for {duration_hours}h. Total: ₹{booking.total_amount}. Non-refundable deposit: ₹{booking.deposit_amount}. Expansion engine active."
    })


@login_required
def generate_invoice(request, booking_id):
    """
    View to display a premium GST-compliant bill for the customer.
    """
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    
    return render(request, "bookings/invoice.html", {
        "booking": booking,
        "gst_rate": "18%",
        "deposit_rate": "10%"
    })
