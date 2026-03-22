from django.contrib import admin
from django.urls import path

from apps.bookings.views import accept_job, homepage, photographer_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", homepage, name="homepage"),
    path("photographer/dashboard/", photographer_dashboard, name="photographer-dashboard"),
    path("bookings/<int:booking_id>/accept/", accept_job, name="accept-job"),
]
