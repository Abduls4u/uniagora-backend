from django.test import TestCase

from apps.authentication.serializers import RegisterSerializer
from apps.users.models import User


class RegisterSerializerTests(TestCase):
    def test_rejects_duplicate_email(self):
        User.objects.create_user(
            email="u1@example.com", password="pass12345", full_name="U1"
        )
        serializer = RegisterSerializer(
            data={
                "email": "u1@example.com",
                "password": "correct-horse-9",
                "full_name": "Dup",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_rejects_duplicate_email_case_insensitively(self):
        User.objects.create_user(
            email="u2@example.com", password="pass12345", full_name="U2"
        )
        serializer = RegisterSerializer(
            data={
                "email": "U2@Example.com",
                "password": "correct-horse-9",
                "full_name": "Dup",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_rejects_weak_password(self):
        serializer = RegisterSerializer(
            data={"email": "u3@example.com", "password": "123", "full_name": "U3"}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_rejects_invalid_phone_number(self):
        serializer = RegisterSerializer(
            data={
                "email": "u4@example.com",
                "password": "correct-horse-9",
                "full_name": "U4",
                "phone_number": "not-a-phone!!",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)

    def test_accepts_valid_payload(self):
        serializer = RegisterSerializer(
            data={
                "email": "u5@example.com",
                "password": "correct-horse-9",
                "full_name": "U5",
            }
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
