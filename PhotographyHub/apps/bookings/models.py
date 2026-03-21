from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ASSIGNED = "Assigned", "Assigned"

    customer_name = models.CharField(max_length=120, blank=True)
    customer_address = models.CharField(max_length=255, blank=True)
    customer_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    customer_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="bookings", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    current_ping_radius = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Current expanding ripple radius in kilometers.",
    )
    assigned_photographer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_bookings",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Booking #{self.pk} - {self.status}"
