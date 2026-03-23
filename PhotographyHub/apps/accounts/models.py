from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class PhotographerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="photographer_profile")
    base_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    base_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_available = models.BooleanField(default=True)
    max_travel_radius = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Maximum travel distance in kilometers from photographer home base.",
    )
    categories = models.ManyToManyField("bookings.Category", related_name="photographers", blank=True)
    
    # Premium status
    is_premium_partner = models.BooleanField(default=False, help_text="Entitles photographer to early notifications (5 min priority)")
    premium_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user} ({self.max_travel_radius} km)"
