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
    customer_whatsapp = models.CharField(max_length=15, blank=True, help_text="WhatsApp number with country code e.g. +919876543210")
    customer_address = models.CharField(max_length=255, blank=True)
    event_purpose = models.CharField(max_length=255, blank=True, help_text="Purpose / description of the event")
    event_location = models.CharField(max_length=500, blank=True, help_text="Full venue / address of the event")
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    
    # Event Classification
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    
    # Service Selection
    has_photo = models.BooleanField(default=False)
    has_video = models.BooleanField(default=False)
    has_shorts = models.BooleanField(default=False)
    has_drone = models.BooleanField(default=False)

    # Duration Logic
    duration_hours = models.IntegerField(default=4)
    
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
    subtotal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Total before discounts")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Duration discount amount")
    first_order_discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="First order 5% discount")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Price after all discounts but before GST")
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="10% Non-refundable")
    is_deposit_paid = models.BooleanField(default=False)
    
    # QR Tracking & Time Management
    scheduled_time = models.DateTimeField(null=True, blank=True)
    start_qr_scanned_at = models.DateTimeField(null=True, blank=True)
    end_qr_scanned_at = models.DateTimeField(null=True, blank=True)
    
    # Penalties & Overtime
    arrival_penalty_applied = models.BooleanField(default=False)
    upload_penalty_applied = models.BooleanField(default=False)
    overtime_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Post-Shoot
    gallery_link1 = models.URLField(blank=True, null=True)
    gallery_link2 = models.URLField(blank=True, null=True)
    gallery_link3 = models.URLField(blank=True, null=True)
    
    # Payout to Photographer
    payout_ready_at = models.DateTimeField(null=True, blank=True, help_text="Scheduled payout date (7 days after work)")
    payout_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
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

    def calculate_payout(self):
        """
        Final Payout: Calculate Base Fee - Arrival Penalty (10%) - Upload Penalty (20%) + Overtime Charges (Client).
        Note: The penalty is calculated on the Base Fee.
        """
        payout = self.base_price
        
        if self.arrival_penalty_applied:
            payout -= self.base_price * Decimal('0.10')
            
        if self.upload_penalty_applied:
            payout -= self.base_price * Decimal('0.20')
            
        # Overtime charges are added to the payout (paid by client, passed to photographer? 
        # Requirement says: Calculate Base Fee - Arrival Penalty (10%) - Upload Penalty (20%) + Overtime Charges (Client).
        payout += self.overtime_charges
        
        return max(payout, Decimal('0.00'))

    def save(self, *args, **kwargs):
        # Auto-calculate GST and Total if not set
        # We assume base_price is set before saving by the view calculations
        if self.base_price > 0:
            self.gst_amount = self.base_price * Decimal('0.18')
            self.total_amount = self.base_price + self.gst_amount
            self.deposit_amount = self.total_amount * Decimal('0.10')
            
        # Update payout amount
        self.payout_amount = self.calculate_payout()
        
        super().save(*args, **kwargs)

    def get_services_str(self):
        services = []
        if self.has_photo: services.append("Photo")
        if self.has_video: services.append("Video")
        if self.has_shorts: services.append("Shorts")
        if self.has_drone: services.append("Drone")
        return ", ".join(services) or "Photography"

    def __str__(self) -> str:
        return f"Booking #{self.pk} - {self.status}"
