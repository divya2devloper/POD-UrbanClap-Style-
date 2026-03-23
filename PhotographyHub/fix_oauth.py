import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

client_id = os.getenv("SOCIAL_AUTH_GOOGLE_CLIENT_ID")
secret = os.getenv("SOCIAL_AUTH_GOOGLE_SECRET")

if not client_id or not secret:
    print("Error: SOCIAL_AUTH_GOOGLE_CLIENT_ID or SOCIAL_AUTH_GOOGLE_SECRET missing from .env")
    exit(1)

# Update Site
site, created = Site.objects.get_or_create(id=1)
site.domain = "localhost:8000"
site.name = "PhotographyHub"
site.save()
print(f"Site updated: {site.domain}")

# Update SocialApp
app = SocialApp.objects.filter(provider='google').first()
if not app:
    app = SocialApp.objects.create(provider='google', name='Google Login')

app.client_id = client_id
app.secret = secret
app.name = "PhotographyHub"
app.sites.set([site])
app.save()

print(f"SocialApp updated with Client ID: {client_id}")
