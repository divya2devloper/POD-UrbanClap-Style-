from django.db import models
from apps.accounts.models import User, PhotographerProfile


class Booking(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Assigned', 'Assigned'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_as_customer')
    photographer = models.ForeignKey(
        PhotographerProfile, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_bookings'
    )
    service_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    customer_latitude = models.FloatField()
    customer_longitude = models.FloatField()
    customer_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    current_ping_radius = models.FloatField(default=5.0, help_text="Current ping radius in km")
    scheduled_at = models.DateTimeField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.service_name} ({self.status})"


class BookingPing(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='pings')
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE)
    pinged_at = models.DateTimeField(auto_now_add=True)
    was_accepted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('booking', 'photographer')
