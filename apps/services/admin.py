from django.contrib import admin
from .models import ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_price')
    search_fields = ('name',)
