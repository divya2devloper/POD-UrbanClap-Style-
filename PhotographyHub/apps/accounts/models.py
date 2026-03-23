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
    
    # Bio & Expertise
    bio = models.TextField(blank=True, help_text="Tell clients about yourself.")
    experience_years = models.PositiveIntegerField(default=0)
    specialties = models.CharField(
        max_length=500, 
        blank=True, 
        help_text="Comma-separated expertise (e.g. Panorama, Fish-eye)"
    )
    
    def items_per_category(self, category):
        return self.portfolio_items.filter(category=category).count()
        
    def can_add_to_category(self, category):
        return self.items_per_category(category) < 10

    profile_picture = models.ImageField(upload_to="photographer_profiles/", null=True, blank=True)
    
    # Premium status
    is_premium_partner = models.BooleanField(default=False, help_text="Entitles photographer to early notifications (10 min priority)")
    premium_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user} ({self.max_travel_radius} km)"


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_verified = models.BooleanField(default=False)

    def __cln_whatsapp__(self):
        if self.whatsapp_number:
            return self.whatsapp_number.replace(" ", "").replace("-", "")
        return ""

    def __str__(self) -> str:
        return f"Profile of {self.user.username}"

class PortfolioItem(models.Model):
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name="portfolio_items")
    category = models.ForeignKey('bookings.Category', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="portfolios/")
    is_approved = models.BooleanField(default=False)
    is_main_gallery = models.BooleanField(default=False, help_text="Show on the public homepage gallery")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Work by {self.photographer} - {self.category}"
