from django.test import TestCase

from apps.common.exceptions import ConflictError
from apps.universities.models import University
from apps.users.models import User
from apps.users.services import UserService


class UserServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="r@example.com", password="pass12345", full_name="R"
        )

    def test_update_profile_updates_only_provided_fields(self):
        original_phone = self.user.phone_number
        UserService.update_profile(user=self.user, full_name="Updated Name")
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, "Updated Name")
        self.assertEqual(self.user.phone_number, original_phone)

    def test_update_profile_no_op_when_nothing_provided(self):
        original_updated_at = self.user.updated_at
        UserService.update_profile(user=self.user)
        self.user.refresh_from_db()
        self.assertEqual(self.user.updated_at, original_updated_at)

    def test_set_active_university_success(self):
        university = University.objects.create(name="Uni A", short_name="UA")
        UserService.set_active_university(user=self.user, university=university)
        self.user.refresh_from_db()
        self.assertEqual(self.user.active_university, university)

    def test_set_active_university_rejects_inactive(self):
        university = University.objects.create(
            name="Uni B", short_name="UB", is_active=False
        )
        with self.assertRaises(ConflictError):
            UserService.set_active_university(user=self.user, university=university)
