from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from apps.common.validators import validate_phone_number


class PhoneNumberValidatorTests(SimpleTestCase):
    def test_accepts_valid_numbers(self):
        for value in ["+2348012345678", "08012345678", "12345678901"]:
            validate_phone_number(value)  # should not raise

    def test_rejects_too_short(self):
        with self.assertRaises(ValidationError):
            validate_phone_number("12345")

    def test_rejects_non_numeric(self):
        with self.assertRaises(ValidationError):
            validate_phone_number("phone-number")
