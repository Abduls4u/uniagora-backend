from django.test import TestCase
from rest_framework.test import APIClient

from apps.universities.models import University
from apps.users.models import User


class MeViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="s@example.com", password="pass12345", full_name="S"
        )

    def test_requires_authentication(self):
        response = self.client.get("/api/v1/users/me/")
        self.assertIn(response.status_code, (401, 403))

    def test_get_returns_own_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.get("/api/v1/users/me/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["email"], "s@example.com")

    def test_patch_updates_profile(self):
        self.client.force_authenticate(self.user)
        response = self.client.patch("/api/v1/users/me/", {"full_name": "Renamed"})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Renamed")


class SetActiveUniversityViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="t@example.com", password="pass12345", full_name="T"
        )
        self.client.force_authenticate(self.user)

    def test_success(self):
        university = University.objects.create(name="Uni C", short_name="UC")
        response = self.client.patch(
            "/api/v1/users/me/active-university/", {"university_slug": university.slug}
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.active_university, university)

    def test_rejects_inactive_university(self):
        university = University.objects.create(
            name="Uni D", short_name="UD", is_active=False
        )
        response = self.client.patch(
            "/api/v1/users/me/active-university/", {"university_slug": university.slug}
        )
        self.assertEqual(response.status_code, 400)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        response = self.client.post(
            "/api/v1/users/me/active-university/", {"university_slug": "whatever"}
        )
        self.assertIn(response.status_code, (401, 403))
