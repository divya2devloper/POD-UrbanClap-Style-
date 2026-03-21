from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import PhotographerProfile
from apps.bookings.models import Booking, Category
from apps.bookings.tasks import expand_ripple_logic


class BookingFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="photo", password="pass12345")
        self.other_user = get_user_model().objects.create_user(username="photo2", password="pass12345")
        self.category = Category.objects.create(name="Wedding", slug="wedding", description="Wedding shoots")
        PhotographerProfile.objects.create(
            user=self.user,
            base_latitude=23.0216,
            base_longitude=72.5316,
            max_travel_radius=30,
            is_available=True,
        )
        PhotographerProfile.objects.create(
            user=self.other_user,
            base_latitude=23.0216,
            base_longitude=72.5316,
            max_travel_radius=30,
            is_available=False,
        )
        self.booking = Booking.objects.create(
            customer_name="Amit",
            customer_address="Satellite",
            customer_latitude=23.0216,
            customer_longitude=72.5316,
            category=self.category,
        )

    def test_accept_job_is_atomic_for_taken_booking(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accept-job", args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.other_user)
        second_response = self.client.post(reverse("accept-job", args=[self.booking.id]))
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(second_response.json()["detail"], "Job already taken")

    def test_expand_ripple_increments_pending_radius(self):
        self.assertEqual(self.booking.current_ping_radius, 5)
        expand_ripple_logic()
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.current_ping_radius, 10)

    def test_homepage_renders_default_category_sections(self):
        self.booking.category = None
        self.booking.save(update_fields=["category"])
        Category.objects.all().delete()
        response = self.client.get(reverse("homepage"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Wedding")
        self.assertContains(response, "Video")
        self.assertContains(response, "Drone Shots")
