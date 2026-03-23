from django.contrib import admin
from django.urls import include, path

from apps.accounts.views import login_view, photographer_join, whatsapp_setup, photographer_profile_edit, upgrade_to_premium
from apps.bookings.views import (
    homepage,
    photographer_dashboard,
    admin_dashboard,
    admin_portfolio_review,
    customer_dashboard,
    update_profile,
    create_booking,
    accept_job,
    save_booking,
    generate_invoice,
    arrival_qr_scan,
    completion_qr_scan,
    upload_gallery,
    razorpay_webhook,
    whatsapp_webhook
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", homepage, name="homepage"),
    path("login/", login_view, name="login"),
    path("accounts/whatsapp-setup/", whatsapp_setup, name="whatsapp-setup"),
    path("accounts/", include("allauth.urls")),
    path("photographer/join/", photographer_join, name="photographer-join"),
    path("photographer/profile/edit/", photographer_profile_edit, name="photographer-profile-edit"),
    path("photographer/upgrade-premium/", upgrade_to_premium, name="upgrade-to-premium"),
    path("photographer/dashboard/", photographer_dashboard, name="photographer-dashboard"),
    path('admin/dashboard/', admin_dashboard, name='admin-dashboard'),
    path('admin/portfolio/review/', admin_portfolio_review, name='admin-portfolio-review'),
    path('customer/dashboard/', customer_dashboard, name='customer-dashboard'),
    path('customer/update-profile/', update_profile, name='update-profile'),
    path("bookings/create/", create_booking, name="create-booking"),
    path("bookings/<int:booking_id>/accept/", accept_job, name="accept-job"),
    path('bookings/<int:booking_id>/save/', save_booking, name='save-job'),
    path('bookings/<int:booking_id>/invoice/', generate_invoice, name='generate-invoice'),
    path("bookings/<int:booking_id>/arrival-scan/", arrival_qr_scan, name="arrival_qr_scan"),
    path("bookings/<int:booking_id>/completion-scan/", completion_qr_scan, name="completion_qr_scan"),
    path("bookings/<int:booking_id>/upload-gallery/", upload_gallery, name="upload-gallery"),
    path("api/razorpay/webhook/", razorpay_webhook, name="razorpay-webhook"),
    path("api/whatsapp/webhook/", whatsapp_webhook, name="whatsapp-webhook"),
]
