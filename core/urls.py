from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('bookings/', include('apps.bookings.urls', namespace='bookings')),
    path('services/', include('apps.services.urls', namespace='services')),
    path('', lambda request: redirect('bookings:job_feed'), name='home'),
]
