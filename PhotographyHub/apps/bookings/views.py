import logging
import math
import os
import razorpay
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.signing import Signer, BadSignature
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.bookings.models import Booking, Category
from apps.bookings.tasks import (
    track_booking_ripple, 
    check_upload_deadline, 
    send_whatsapp_notification
)
from apps.accounts.models import PhotographerProfile, PortfolioItem
from apps.bookings.utils import generate_signed_qr_base64

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
    {"name": "Commercial", "slug": "commercial", "description": "Professional commercial and industrial photography."},
    {"name": "Advertisement", "slug": "advertisement", "description": "High-impact advertising and promotional shoots."},
    {"name": "Racing/Sports", "slug": "racing-sports", "description": "High-speed action and sports event coverage."},
    # Service Categories
    {"name": "Photos", "slug": "photos", "description": "Standard high-resolution photography."},
    {"name": "Videos", "slug": "videos", "description": "Professional videography and cinematic coverage."},
    {"name": "Shorts (< 2 min)", "slug": "shorts", "description": "Short-form vertical video content for social media."},
    {"name": "Drone", "slug": "drone", "description": "Aerial photography and videography."},
]



def homepage(request):
    """
    Main portal landing page.
    """
    # Seed categories if missing
    for cat_data in DEFAULT_CATEGORIES:
        Category.objects.get_or_create(
            slug=cat_data["slug"],
            defaults={
                "name": cat_data["name"],
                "description": cat_data["description"]
            }
        )

    # Use database categories
    categories = Category.objects.order_by("name")
    
    # Identify service category IDs for display filtering (if needed)
    service_names = ["Photos", "Videos", "Shorts (< 2 min)", "Drone"]
    
    category_blocks = []
    for c in categories:
        # Skip service categories in the main niche grid
        if c.name in service_names:
            continue
            
        p_url = c.placeholder_url or "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?auto=format&fit=crop&w=400&q=80"
        
        # Simple attribution logic for the new model
        media_types = ["Standard"]
        if "Photo" in c.name: media_types = ["RAW", "JPEG", "Edited"]
        elif "Video" in c.name: media_types = ["4K Cinematic", "Full HD"]
        elif "Short" in c.name: media_types = ["9:16 Vertical", "Social Ready"]
        elif "Drone" in c.name: media_types = ["Aerial 4K", "Top-down"]

        category_blocks.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "placeholder_url": p_url,
            "media_types": media_types,
            "is_corporate": c.is_corporate
        })
        
    # Fetch featured portfolio items for the main gallery
    featured_work = PortfolioItem.objects.filter(is_main_gallery=True).select_related('photographer__user', 'category')[:12]
        
    return render(request, "home/homepage.html", {
        "category_blocks": category_blocks,
        "featured_work": featured_work
    })


def photographer_dashboard(request):
    """
    Feed for photographers + Financial Stats.
    """
    if not request.user.is_authenticated:
        return render(request, "accounts/login.html")

    # 1. Job Feed
    pending_bookings = Booking.objects.filter(
        status=Booking.Status.PENDING
    ).order_by("-created_at")[:50]
    
    # 2. Financial Stats for CURRENT photographer
    stats = Booking.objects.filter(assigned_photographer=request.user).aggregate(
        total_earned=Sum("total_amount", filter=Q(status=Booking.Status.ASSIGNED)),
        pending_payouts=Sum("total_amount", filter=Q(status=Booking.Status.ASSIGNED, is_payout_completed=False)),
        completed_count=Count("id", filter=Q(status=Booking.Status.ASSIGNED, is_payout_completed=True))
    )
    
    # Financial History
    work_history = Booking.objects.filter(
        assigned_photographer=request.user
    ).order_by("-created_at")[:20]

    category_boxes = Category.objects.order_by("name")
    
    return render(request, "bookings/photographer_dashboard.html", {
        "bookings": pending_bookings,
        "category_boxes": category_boxes,
        "stats": stats,
        "work_history": work_history,
        "profile": getattr(request.user, "photographer_profile", None)
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
    
    recent_activity = Booking.objects.select_related("customer", "assigned_photographer").order_by("-created_at")[:20]
    
    return render(request, "bookings/admin_dashboard.html", {
        "stats": platform_stats,
        "recent_activity": recent_activity
    })


@login_required
def admin_portfolio_review(request):
    """
    Interface for admins to approve/reject photographer portfolio items.
    """
    if not request.user.is_staff:
        return JsonResponse({"detail": "Admin access required."}, status=403)

    if request.method == "POST":
        item_id = request.POST.get("item_id")
        action = request.POST.get("action")
        item = get_object_or_404(PortfolioItem, id=item_id)

        if action == "approve":
            item.is_approved = True
            item.save()
            messages.success(request, f"Approved item from {item.photographer}")
        elif action == "feature":
            item.is_approved = True
            item.is_main_gallery = True
            item.save()
            messages.success(request, f"Featured item from {item.photographer} in Main Gallery")
        elif action == "reject":
            item.delete()
            messages.warning(request, "Rejected and deleted portfolio item.")
        
        return redirect("admin-portfolio-review")

    pending_items = PortfolioItem.objects.filter(is_approved=False).select_related('photographer__user', 'category')
    approved_items = PortfolioItem.objects.filter(is_approved=True).select_related('photographer__user', 'category')[:50]

    return render(request, "bookings/admin_portfolio_review.html", {
        "pending_items": pending_items,
        "approved_items": approved_items
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

        # WhatsApp Notification
        send_whatsapp_notification(booking, "confirm")
        
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
    bookings = Booking.objects.filter(customer=request.user).select_related("assigned_photographer").order_by("-created_at")
    
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
    user.save()

    # Update UserProfile WhatsApp
    whatsapp = request.POST.get("whatsapp_number")
    if whatsapp:
        profile = user.profile
        profile.whatsapp_number = whatsapp
        profile.save()
    
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
@require_POST
@login_required
def create_booking(request):
    """
    Create a new booking and trigger the ripple search engine.
    Mandatory fields: whatsapp_number, event_purpose, event_date, event_time, event_location.
    Services: has_photo, has_video, has_shorts, has_drone (checkboxes).
    """
    whatsapp_number = request.POST.get("whatsapp_number", "").strip()
    event_purpose = request.POST.get("event_purpose", "").strip()
    event_date = request.POST.get("event_date", "").strip()
    event_time = request.POST.get("event_time", "").strip()
    event_location = request.POST.get("event_location", "").strip()
    category_id = request.POST.get("category_id")
    
    # Service checkboxes (sent as 'true'/'false' or presence)
    has_photo = request.POST.get("has_photo") == "true"
    has_video = request.POST.get("has_video") == "true"
    has_shorts = request.POST.get("has_shorts") == "true"
    has_drone = request.POST.get("has_drone") == "true"

    # ── Mandatory field validation ──────────────────────────────────────
    missing = []
    if not whatsapp_number:
        missing.append("WhatsApp number")
    if not event_purpose:
        missing.append("Purpose of event")
    if not event_date:
        missing.append("Event date")
    if not event_time:
        missing.append("Event time")
    if not event_location:
        missing.append("Event location")
    
    if not any([has_photo, has_video, has_shorts, has_drone]):
        return JsonResponse({"detail": "Please select at least one service (Photo, Video, Shorts, or Drone)."}, status=400)

    if missing:
        return JsonResponse({"detail": f"Required fields missing: {', '.join(missing)}."}, status=400)

    # Basic WhatsApp number format check
    import re
    if not re.match(r'^\+?\d{10,15}$', whatsapp_number):
        return JsonResponse({"detail": "Invalid WhatsApp number. Use format: +919876543210"}, status=400)

    # Build scheduled_time from date + time inputs
    try:
        scheduled_time_str = f"{event_date}T{event_time}"
        scheduled_time = timezone.datetime.fromisoformat(scheduled_time_str)
        if timezone.is_naive(scheduled_time):
            scheduled_time = timezone.make_aware(scheduled_time)
    except (ValueError, TypeError):
        return JsonResponse({"detail": "Invalid date or time format."}, status=400)

    duration_hours = int(request.POST.get("duration_hours", 4))

    # --- Pricing Logic ---
    rates = {
        "photo": 1500,
        "video": 2500,
        "shorts": 1000,
        "drone": 3000
    }
    
    hourly_rate = 0
    if has_photo: hourly_rate += rates["photo"]
    if has_video: hourly_rate += rates["video"]
    if has_shorts: hourly_rate += rates["shorts"]
    if has_drone: hourly_rate += rates["drone"]
    
    subtotal = Decimal(hourly_rate * duration_hours)
    
    # 1. Duration Discount (4+ hours -> 10%)
    discount_amount = Decimal('0.00')
    discount_percentage = Decimal('0.00')
    if duration_hours >= 4:
        discount_percentage = Decimal('10.00')
        discount_amount = subtotal * Decimal('0.10')
    
    running_total = subtotal - discount_amount
    
    # 2. First Order Discount (Additional 5%)
    first_order_discount = Decimal('0.00')
    # Check if user has any existing successful or pending bookings
    has_previous = Booking.objects.filter(customer=request.user).exclude(status=Booking.Status.CANCELLED).exists()
    if not has_previous:
        first_order_discount = running_total * Decimal('0.05')
        discount_percentage += Decimal('5.00')
    
    base_price = running_total - first_order_discount

    booking = Booking.objects.create(
        customer=request.user,
        customer_whatsapp=whatsapp_number,
        event_purpose=event_purpose,
        event_location=event_location,
        customer_latitude=23.0225,
        customer_longitude=72.5714,
        category_id=category_id,
        duration_hours=duration_hours,
        has_photo=has_photo,
        has_video=has_video,
        has_shorts=has_shorts,
        has_drone=has_drone,
        subtotal_amount=subtotal,
        discount_amount=discount_amount,
        first_order_discount_amount=first_order_discount,
        discount_percentage=discount_percentage,
        base_price=base_price,
        status=Booking.Status.PENDING,
        scheduled_time=scheduled_time,
        expires_at=timezone.now() + timedelta(hours=2)
    )

    # Trigger the independent ripple search for THIS specific booking
    track_booking_ripple.delay(booking.id)

    return JsonResponse({
        "status": "success",
        "booking_id": booking.id,
        "detail": f"Booking created! Subtotal: ₹{subtotal}. Total Discount: {discount_percentage}%. Final: ₹{booking.total_amount}. Non-refundable deposit: ₹{booking.deposit_amount}."
    })


signer = Signer()

def arrival_qr_scan(request, booking_id):
    """
    Client scans photographer's QR to 'Start' the job.
    """
    token = request.GET.get("token")
    if not token:
        return JsonResponse({"detail": "Missing token."}, status=400)
    
    try:
        unsigned_value = signer.unsign(token)
        if unsigned_value != f"{booking_id}:arrival":
            return JsonResponse({"detail": "Invalid token for this booking."}, status=400)
    except BadSignature:
        return JsonResponse({"detail": "Signature invalid."}, status=400)

    booking = get_object_or_404(Booking, pk=booking_id)
    
    if booking.start_qr_scanned_at:
        return JsonResponse({"detail": "Job already started."}, status=400)

    now = timezone.now()
    booking.start_qr_scanned_at = now
    
    # 15-minute buffer logic
    if booking.scheduled_time and now > (booking.scheduled_time + timedelta(minutes=15)):
        booking.arrival_penalty_applied = True
        logger.info(f"Arrival Penalty (10%) flagged for Booking {booking_id}.")
    
    booking.save()
    
    return render(request, "bookings/job_started.html", {"booking": booking})


def completion_qr_scan(request, booking_id):
    """
    Client scans second QR to 'End' the job and check for overtime.
    """
    token = request.GET.get("token")
    if not token:
        return JsonResponse({"detail": "Missing token."}, status=400)
    
    try:
        unsigned_value = signer.unsign(token)
        if unsigned_value != f"{booking_id}:completion":
            return JsonResponse({"detail": "Invalid token for this booking."}, status=400)
    except BadSignature:
        return JsonResponse({"detail": "Signature invalid."}, status=400)

    booking = get_object_or_404(Booking, pk=booking_id)
    
    if booking.end_qr_scanned_at:
        return JsonResponse({"detail": "Job already ended."}, status=400)

    now = timezone.now()
    booking.end_qr_scanned_at = now
    
    # Overtime Logic: If End > Start + Duration + 15m buffer
    start_time = booking.start_qr_scanned_at or booking.scheduled_time or booking.created_at
    contracted_end_time = start_time + timedelta(hours=booking.duration_hours)
    buffer_end_time = contracted_end_time + timedelta(minutes=15)
    
    if now > buffer_end_time:
        diff = now - contracted_end_time
        hours_over = math.ceil(diff.total_seconds() / 3600)
        # 10% of total booking fee per hour
        booking.overtime_charges = (booking.total_amount * Decimal('0.10')) * hours_over
        logger.info(f"Overtime detected: {hours_over} hours. Charge: ₹{booking.overtime_charges}")

    booking.status = Booking.Status.COMPLETED
    booking.save()

    # Schedule 48-hour upload check
    check_upload_deadline.apply_async((booking.id,), countdown=48*3600)

    # Razorpay Payment Link for Overtime if any
    razorpay_link = None
    if booking.overtime_charges > 0:
        # Placeholder for Razorpay integration
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        payment_link = client.payment_link.create({
            "amount": int(booking.overtime_charges * 100),
            "currency": "INR",
            "description": f"Overtime charges for Booking #{booking.id}",
            "customer": {
                "name": booking.customer_name or "Client",
                "email": booking.customer.email if booking.customer else "client@example.com",
            },
            "callback_url": f"{settings.SITE_DOMAIN}/bookings/{booking.id}/payout-callback/",
            "callback_method": "get"
        })
        razorpay_link = payment_link.get("short_url")

    return render(request, "bookings/job_completed.html", {
        "booking": booking,
        "overtime_charges": booking.overtime_charges,
        "razorpay_link": razorpay_link
    })


@login_required
def upload_gallery(request, booking_id):
    """
    Photographer uploads 3 gallery links.
    """
    booking = get_object_or_404(Booking, pk=booking_id, assigned_photographer=request.user)
    
    if request.method == "POST":
        booking.gallery_link1 = request.POST.get("link1")
        booking.gallery_link2 = request.POST.get("link2")
        booking.gallery_link3 = request.POST.get("link3")
        booking.save()
        return JsonResponse({"status": "success", "detail": "Gallery links updated."})
    
    return render(request, "bookings/upload_gallery.html", {"booking": booking})


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Handle incoming Razorpay payment events."""
    logger.info("Razorpay Webhook Triggered")
    return JsonResponse({"status": "received"})

@csrf_exempt
def whatsapp_webhook(request):
    """Handle incoming WhatsApp messages or status updates."""
    if request.method == "GET":
        mode = request.GET.get("hub.mode")
        token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")
        if mode == "subscribe" and token == os.getenv("WHATSAPP_VERIFY_TOKEN", "Jini0123"):
            return HttpResponse(challenge)
    logger.info("WhatsApp Webhook Triggered")
    return JsonResponse({"status": "received"})

@login_required
def generate_invoice(request, booking_id):
    """
    View to display a premium GST-compliant bill for the customer.
    """
    booking = get_object_or_404(Booking, pk=booking_id, customer=request.user)
    
    # Identify which services were selected
    selected_services = []
    if booking.has_photo: selected_services.append("Professional Photography")
    if booking.has_video: selected_services.append("Cinematic Videography")
    if booking.has_shorts: selected_services.append("Short-form Content / Reels")
    if booking.has_drone: selected_services.append("Drone / Aerial Imagery")

    return render(request, "bookings/invoice.html", {
        "booking": booking,
        "selected_services": selected_services,
        "subtotal": booking.subtotal_amount,
        "discount_val": booking.discount_amount + booking.first_order_discount_amount,
        "discount_pct": booking.discount_percentage,
        "base_amount": booking.base_price,
        "gst_amount": booking.gst_amount,
        "overtime_amount": booking.overtime_charges,
        "total_amount": booking.total_amount,
        "gst_rate": "18%",
        "deposit_rate": "10%"
    })
