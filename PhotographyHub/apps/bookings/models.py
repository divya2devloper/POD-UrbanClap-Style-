from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    placeholder_url = models.URLField(blank=True, null=True)
    is_corporate = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name


class CategoryMedia(models.Model):
    class MediaType(models.TextChoices):
        PHOTO = "Photo", "Photo"
        VIDEO = "Video", "Video"
        REEL = "Reel", "Reel"
        DRONE = "Drone", "Drone"

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="media")
    media_type = models.CharField(max_length=20, choices=MediaType.choices)
    file = models.FileField(upload_to="category_media/")
    thumbnail = models.ImageField(upload_to="category_media/thumbnails/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.category.name} - {self.media_type}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ASSIGNED = "Assigned", "Assigned"
        PAID = "Paid", "Paid"
        COMPLETED = "Completed", "Completed"
        CANCELLED = "Cancelled", "Cancelled"

    class Duration(models.IntegerChoices):
        FOUR_HOURS = 4, "4 Hours"
        SIX_HOURS = 6, "6 Hours"
        EIGHT_HOURS = 8, "8 Hours"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
        null=True,
        blank=True
    )
    customer_name = models.CharField(max_length=120, blank=True)
    customer_address = models.CharField(max_length=255, blank=True)
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True)
    
    # Duration Logic
    duration_hours = models.IntegerField(choices=Duration.choices, default=Duration.FOUR_HOURS)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    current_ping_radius = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Current expanding ripple radius in kilometers.",
    )
    notified_photographer_ids = models.JSONField(default=list, blank=True)
    assigned_photographer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_bookings",
    )
    
    # Financials
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="10% Non-refundable")
    is_deposit_paid = models.BooleanField(default=False)
    
    # Payout to Photographer
    payout_ready_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled payout date (7 days after work)")
    is_payout_completed = models.BooleanField(default=False)

    # Search Logic Extras
    is_saved_by_photographer = models.BooleanField(default=False, help_text="Expands expiry if saved")
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Corporate requirements
    same_day_delivery = models.BooleanField(default=False)
    
    # Payment Gateway IDs
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    order_id = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Auto-calculate GST and Total if not set
        if self.base_price > 0:
            self.gst_amount = self.base_price * Decimal('0.18')
            self.total_amount = self.base_price + self.gst_amount
            self.deposit_amount = self.total_amount * Decimal('0.10')
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Booking #{self.pk} - {self.status}"
