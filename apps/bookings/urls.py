from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('job-feed/', views.job_feed, name='job_feed'),
    path('accept-job/<int:booking_id>/', views.accept_job, name='accept_job'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('create/', views.create_booking, name='create_booking'),
]
