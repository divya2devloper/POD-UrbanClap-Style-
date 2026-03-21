from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class PhotographerProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="photographer_profile",
    )
    base_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    base_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    max_travel_radius = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(1), MaxValueValidator(60)],
        help_text="Maximum distance the photographer is willing to travel in km.",
    )

    def __str__(self) -> str:
        return f"PhotographerProfile<{self.user_id}>"
