from django.test import TestCase

from apps.universities.models import University
from apps.users.models import User


def make_university(**kwargs):
    defaults = {"name": "University of Ibadan", "short_name": "UI"}
    defaults.update(kwargs)
    return University.objects.create(**defaults)


class UserModelTests(TestCase):
    def test_str_returns_email(self):
        user = User.objects.create_user(
            email="Test@Example.com", password="pass12345", full_name="Test User"
        )
        self.assertEqual(str(user), "test@example.com")

    def test_email_is_lowercased_on_save(self):
        user = User.objects.create_user(
            email="MixedCase@Example.com", password="pass12345", full_name="X"
        )
        self.assertEqual(user.email, "mixedcase@example.com")

    def test_uuid_primary_key(self):
        user = User.objects.create_user(
            email="a@example.com", password="pass12345", full_name="A"
        )
        self.assertEqual(len(str(user.pk)), 36)

    def test_is_vendor_false_without_profile(self):
        user = User.objects.create_user(
            email="b@example.com", password="pass12345", full_name="B"
        )
        self.assertFalse(user.is_vendor)

    def test_is_admin_true_for_staff(self):
        user = User.objects.create_user(
            email="c@example.com", password="pass12345", full_name="C", is_staff=True
        )
        self.assertTrue(user.is_admin)

    def test_is_admin_true_for_superuser(self):
        user = User.objects.create_superuser(
            email="d@example.com", password="pass12345", full_name="D"
        )
        self.assertTrue(user.is_admin)

    def test_is_admin_false_for_regular_customer(self):
        user = User.objects.create_user(
            email="e@example.com", password="pass12345", full_name="E"
        )
        self.assertFalse(user.is_admin)

    def test_active_university_nullable(self):
        user = User.objects.create_user(
            email="f@example.com", password="pass12345", full_name="F"
        )
        self.assertIsNone(user.active_university)

    def test_active_university_can_be_set(self):
        university = make_university()
        user = User.objects.create_user(
            email="g@example.com",
            password="pass12345",
            full_name="G",
            active_university=university,
        )
        self.assertEqual(user.active_university, university)

    def test_unfiltered_default_manager_includes_soft_deleted(self):
        user = User.objects.create_user(
            email="h@example.com", password="pass12345", full_name="H"
        )
        user.delete()  # soft-delete, per common.BaseModel
        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(User.objects.alive().filter(pk=user.pk).exists())
        self.assertTrue(User.objects.dead().filter(pk=user.pk).exists())

    def test_default_ordering_is_newest_first(self):
        first = User.objects.create_user(
            email="i@example.com", password="pass12345", full_name="I"
        )
        second = User.objects.create_user(
            email="j@example.com", password="pass12345", full_name="J"
        )
        ordered = list(User.objects.filter(pk__in=[first.pk, second.pk]))
        self.assertEqual(ordered, [second, first])
