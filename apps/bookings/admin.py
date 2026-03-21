from django.contrib import admin
from .models import Booking, BookingPing


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'service_name', 'customer', 'photographer', 'status', 'current_ping_radius', 'scheduled_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('service_name', 'customer__username', 'customer_address')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(BookingPing)
class BookingPingAdmin(admin.ModelAdmin):
    list_display = ('booking', 'photographer', 'pinged_at', 'was_accepted')
    list_filter = ('was_accepted',)
