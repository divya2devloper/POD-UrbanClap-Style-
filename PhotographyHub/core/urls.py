from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import login_view, photographer_join
from apps.bookings.views import (
    homepage,
    photographer_dashboard,
    admin_dashboard,
    customer_dashboard,
    update_profile,
    create_booking,
    accept_job,
    save_booking,
    generate_invoice
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", homepage, name="homepage"),
    path("login/", login_view, name="login"),
    path("accounts/", include("allauth.urls")),
    path("photographer/join/", photographer_join, name="photographer-join"),
    path("photographer/dashboard/", photographer_dashboard, name="photographer-dashboard"),
    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
    path('customer/dashboard/', customer_dashboard, name='customer-dashboard'),
    path('customer/update-profile/', update_profile, name='update-profile'),
    path("bookings/create/", create_booking, name="create-booking"),
    path("bookings/<int:booking_id>/accept/", accept_job, name="accept-job"),
    path('bookings/<int:booking_id>/save/', save_booking, name='save-job'),
    path('bookings/<int:booking_id>/invoice/', generate_invoice, name='generate-invoice'),
]
