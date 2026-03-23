import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.bookings.models import Category

# Clear existing categories
Category.objects.all().delete()

# Create new categories as requested
categories = [
    {
        "name": "Photos",
        "slug": "photos",
        "description": "Professional photography for events, portraits, and more.",
        "placeholder_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Videos",
        "slug": "videos",
        "description": "Cinematic video coverage with professional editing.",
        "placeholder_url": "https://images.unsplash.com/photo-1492724441997-5dc865305da7?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Shorts (< 2 min)",
        "slug": "shorts",
        "description": "Vertical high-impact content for Reels and TikTok.",
        "placeholder_url": "https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7?auto=format&fit=crop&w=800&q=80"
    },
    {
        "name": "Drone",
        "slug": "drone",
        "description": "Breathtaking aerial views and dynamic 4K footage.",
        "placeholder_url": "https://images.unsplash.com/photo-1473960104502-6abe9c247ad9?auto=format&fit=crop&w=800&q=80"
    }
]

for cat_data in categories:
    Category.objects.create(**cat_data)

print("Categories updated successfully.")
