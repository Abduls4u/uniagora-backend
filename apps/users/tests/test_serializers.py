from django.test import TestCase

from apps.universities.models import University
from apps.users.models import User
from apps.users.serializers import (
    SetActiveUniversitySerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class UserSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="p@example.com", password="pass12345", full_name="P"
        )

    def test_read_serializer_exposes_computed_flags(self):
        data = UserSerializer(self.user).data
        self.assertIn("is_vendor", data)
        self.assertIn("is_admin", data)
        self.assertFalse(data["is_vendor"])

    def test_read_serializer_all_fields_read_only(self):
        serializer = UserSerializer(
            self.user, data={"email": "hacked@example.com"}, partial=True
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "p@example.com")


class UserUpdateSerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="q@example.com", password="pass12345", full_name="Q"
        )

    def test_accepts_full_name_and_phone_number(self):
        serializer = UserUpdateSerializer(
            self.user,
            data={"full_name": "New Name", "phone_number": "+2348012345678"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_rejects_invalid_phone_number(self):
        serializer = UserUpdateSerializer(
            self.user, data={"phone_number": "not-a-phone!!"}, partial=True
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone_number", serializer.errors)


class SetActiveUniversitySerializerTests(TestCase):
    def test_resolves_active_university_by_slug(self):
        university = University.objects.create(name="Test Uni", short_name="TU")
        serializer = SetActiveUniversitySerializer(
            data={"university_slug": university.slug}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["university_slug"], university)

    def test_rejects_inactive_university(self):
        university = University.objects.create(
            name="Inactive Uni", short_name="IU", is_active=False
        )
        serializer = SetActiveUniversitySerializer(
            data={"university_slug": university.slug}
        )
        self.assertFalse(serializer.is_valid())

    def test_rejects_unknown_slug(self):
        serializer = SetActiveUniversitySerializer(
            data={"university_slug": "does-not-exist"}
        )
        self.assertFalse(serializer.is_valid())
