from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhotographerProfile, CustomerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'user_type', 'phone', 'is_active')
    list_filter = ('user_type', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone', 'profile_photo')}),
    )


@admin.register(PhotographerProfile)
class PhotographerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'base_latitude', 'base_longitude', 'max_travel_radius', 'rating', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('user__username', 'user__email')


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'area', 'created_at')
    search_fields = ('user__username', 'area')
