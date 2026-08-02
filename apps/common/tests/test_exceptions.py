from django.test import SimpleTestCase
from rest_framework import exceptions as drf_exceptions
from rest_framework import status as http_status
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.common.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    custom_exception_handler,
)


def _context():
    request = APIRequestFactory().get("/")
    return {"view": APIView(), "args": (), "kwargs": {}, "request": request}


class ApplicationErrorDefaultsTests:
    """Not a TestCase itself — shared assertions used by subclasses below."""

    error_class = None
    expected_status = None

    def test_uses_default_message_when_none_given(self):
        error = self.error_class()
        self.assertEqual(error.status_code, self.expected_status)
        self.assertTrue(error.message)

    def test_accepts_custom_message_and_errors(self):
        error = self.error_class(message="Custom.", errors={"field": ["bad"]})
        self.assertEqual(error.message, "Custom.")
        self.assertEqual(error.errors, {"field": ["bad"]})


class NotFoundErrorTests(ApplicationErrorDefaultsTests, SimpleTestCase):
    error_class = NotFoundError
    expected_status = http_status.HTTP_404_NOT_FOUND


class PermissionDeniedErrorTests(ApplicationErrorDefaultsTests, SimpleTestCase):
    error_class = PermissionDeniedError
    expected_status = http_status.HTTP_403_FORBIDDEN


class ConflictErrorTests(ApplicationErrorDefaultsTests, SimpleTestCase):
    error_class = ConflictError
    expected_status = http_status.HTTP_409_CONFLICT


class CustomExceptionHandlerTests(SimpleTestCase):
    def test_wraps_application_error_in_failure_envelope(self):
        exc = ConflictError(message="Cannot renew a suspended listing.")
        response = custom_exception_handler(exc, _context())

        self.assertEqual(response.status_code, http_status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["success"], False)
        self.assertEqual(response.data["message"], "Cannot renew a suspended listing.")

    def test_wraps_drf_validation_error(self):
        exc = drf_exceptions.ValidationError({"email": ["This field is required."]})
        response = custom_exception_handler(exc, _context())

        self.assertEqual(response.status_code, http_status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data["success"])
        self.assertEqual(
            response.data["errors"], {"email": ["This field is required."]}
        )

    def test_wraps_drf_not_found(self):
        exc = drf_exceptions.NotFound()
        response = custom_exception_handler(exc, _context())

        self.assertEqual(response.status_code, http_status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["success"])

    def test_returns_none_for_unhandled_exception_types(self):
        # A plain, non-DRF exception must propagate untouched (never
        # silently reshaped into a 500 envelope by this handler).
        response = custom_exception_handler(ValueError("boom"), _context())
        self.assertIsNone(response)
