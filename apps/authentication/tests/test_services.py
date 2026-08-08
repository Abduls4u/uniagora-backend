from django.core import mail
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.authentication.services import AuthService, _token_generator
from apps.common.exceptions import ConflictError, NotFoundError
from apps.users.models import User


class AuthServiceRegisterTests(TestCase):
    def test_register_creates_active_user(self):
        user = AuthService.register(
            email="v1@example.com", password="pass12345", full_name="V1"
        )
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password("pass12345"))

    def test_register_persists_optional_phone_number(self):
        user = AuthService.register(
            email="v2@example.com",
            password="pass12345",
            full_name="V2",
            phone_number="+2348012345678",
        )
        self.assertEqual(user.phone_number, "+2348012345678")


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="v3@example.com", password="oldpass123", full_name="V3"
        )

    def test_initiate_password_reset_sends_email_for_known_active_user(self):
        AuthService.initiate_password_reset(email="v3@example.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_initiate_password_reset_silent_for_unknown_email(self):
        AuthService.initiate_password_reset(email="unknown@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_initiate_password_reset_silent_for_inactive_user(self):
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        AuthService.initiate_password_reset(email="v3@example.com")
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_password_reset_changes_password(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = _token_generator.make_token(self.user)
        AuthService.confirm_password_reset(
            uidb64=uid, token=token, new_password="newpass123"
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    def test_confirm_password_reset_rejects_invalid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        with self.assertRaises(ConflictError):
            AuthService.confirm_password_reset(
                uidb64=uid, token="bad-token", new_password="newpass123"
            )

    def test_confirm_password_reset_rejects_invalid_uid(self):
        with self.assertRaises(NotFoundError):
            AuthService.confirm_password_reset(
                uidb64="not-base64!!", token="whatever", new_password="newpass123"
            )
