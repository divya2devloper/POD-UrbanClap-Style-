from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


AHMEDABAD_GANDHINAGAR_AREAS = {
    "satellite": (23.0225, 72.5714),
    "vastrapur": (23.0400, 72.5300),
    "gota": (23.1025, 72.5415),
    "sargasan": (23.1960, 72.6284),
    "bopal": (23.0300, 72.4600),
    "prahladnagar": (23.0129, 72.5105),
    "sg_highway": (23.0800, 72.5240),
    "chandkheda": (23.1090, 72.5860),
    "maninagar": (22.9950, 72.6030),
    "navrangpura": (23.0340, 72.5600),
}


def area_to_coordinates(area_name: str):
    if not area_name:
        return None
    return AHMEDABAD_GANDHINAGAR_AREAS.get(area_name.strip().lower())


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "Pending", "Pending"
        ASSIGNED = "Assigned", "Assigned"
        COMPLETED = "Completed", "Completed"

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bookings",
    )
    customer_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    customer_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    current_ping_radius = models.PositiveSmallIntegerField(
        default=5,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Current expanding search radius in km.",
    )
    assigned_photographer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_jobs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Booking<{self.id}>:{self.status}"
