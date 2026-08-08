from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.services import _token_generator
from apps.users.models import User


class RegisterViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_creates_user_and_returns_tokens(self):
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "w1@example.com",
                "password": "correct-horse-9",
                "full_name": "W1",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertTrue(User.objects.filter(email="w1@example.com").exists())

    def test_rejects_duplicate_email(self):
        User.objects.create_user(
            email="w2@example.com", password="pass12345", full_name="W2"
        )
        response = self.client.post(
            "/api/v1/auth/register/",
            {
                "email": "w2@example.com",
                "password": "correct-horse-9",
                "full_name": "Dup",
            },
        )
        self.assertEqual(response.status_code, 400)


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="w3@example.com", password="correct-horse-9", full_name="W3"
        )

    def test_valid_credentials_return_tokens(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "w3@example.com", "password": "correct-horse-9"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data["data"])
        self.assertEqual(response.data["data"]["user"]["email"], "w3@example.com")

    def test_invalid_credentials_rejected(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "w3@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 401)

    def test_inactive_user_rejected(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "w3@example.com", "password": "correct-horse-9"},
        )
        self.assertEqual(response.status_code, 401)


class LogoutViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="w4@example.com", password="correct-horse-9", full_name="W4"
        )

    def test_blacklists_refresh_token(self):
        refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/auth/logout/", {"refresh": str(refresh)})
        self.assertEqual(response.status_code, 205)

        # Re-using the same (now blacklisted) refresh token must fail.
        response2 = self.client.post("/api/v1/auth/logout/", {"refresh": str(refresh)})
        self.assertEqual(response2.status_code, 409)

    def test_rejects_token_belonging_to_another_user(self):
        other_user = User.objects.create_user(
            email="w5@example.com", password="correct-horse-9", full_name="W5"
        )
        refresh = RefreshToken.for_user(other_user)
        self.client.force_authenticate(self.user)
        response = self.client.post("/api/v1/auth/logout/", {"refresh": str(refresh)})
        self.assertEqual(response.status_code, 403)

    def test_requires_authentication(self):
        response = self.client.post("/api/v1/auth/logout/", {"refresh": "whatever"})
        self.assertIn(response.status_code, (401, 403))


class PasswordResetViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="w6@example.com", password="oldpass123", full_name="W6"
        )

    def test_request_always_returns_generic_success(self):
        response = self.client.post(
            "/api/v1/auth/password-reset/request/", {"email": "w6@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        response_unknown = self.client.post(
            "/api/v1/auth/password-reset/request/", {"email": "unknown@example.com"}
        )
        self.assertEqual(response_unknown.status_code, 200)

    def test_confirm_updates_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = _token_generator.make_token(self.user)
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "brandnewpass9"},
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandnewpass9"))

    def test_confirm_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            "/api/v1/auth/password-reset/confirm/",
            {"uid": uid, "token": "bad-token", "new_password": "brandnewpass9"},
        )
        self.assertEqual(response.status_code, 409)
