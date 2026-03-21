from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('photographer', 'Photographer'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    phone = models.CharField(max_length=15, blank=True)
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)


class PhotographerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='photographer_profile')
    base_latitude = models.FloatField()
    base_longitude = models.FloatField()
    max_travel_radius = models.FloatField(default=20.0, help_text="Maximum travel radius in km")
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    rating = models.FloatField(default=0.0)
    total_jobs = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    portfolio_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Photographer"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    address = models.TextField(blank=True)
    area = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} - Customer"
