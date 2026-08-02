"""
Shared exception types and the global DRF exception handler.

Backend Architecture §7 (Service Layer Conventions):
    "Services raise domain-specific exceptions (e.g. VendorNotVerifiedError,
    ReviewNotEligibleError), caught once by the shared common/exceptions.py
    handler and translated into the standard error envelope — views never
    need their own try/except blocks for expected business-rule failures."

This module defines the *base* exception vocabulary only. Domain apps
(`vendors`, `reviews`, `chat`, ...) subclass `ApplicationError` for their
own business-rule failures; `common` has no knowledge of what those
specific failures are.
"""

from rest_framework import status as http_status
from rest_framework.views import exception_handler as drf_default_exception_handler

from .response import error_response


class ApplicationError(Exception):
    """
    Base class for every service-layer business-rule exception in the
    system. Domain apps subclass this instead of raising bare exceptions
    or DRF exceptions directly from services, keeping the service layer
    decoupled from DRF (Backend Architecture §7: "services never import
    from views.py or serializers.py").
    """

    default_message = "A business rule prevented this action."
    default_status_code = http_status.HTTP_400_BAD_REQUEST

    def __init__(
        self,
        message: str | None = None,
        errors: dict | None = None,
        status_code: int | None = None,
    ):
        self.message = message or self.default_message
        self.errors = errors or {}
        self.status_code = status_code or self.default_status_code
        super().__init__(self.message)


class NotFoundError(ApplicationError):
    """Raised by a service when a referenced domain object does not exist or isn't visible to the caller."""

    default_message = "The requested resource was not found."
    default_status_code = http_status.HTTP_404_NOT_FOUND


class PermissionDeniedError(ApplicationError):
    """Raised by a service for authorization failures that depend on business context, not just object ownership."""

    default_message = "You do not have permission to perform this action."
    default_status_code = http_status.HTTP_403_FORBIDDEN


class ConflictError(ApplicationError):
    """
    Raised for invalid state transitions, e.g. attempting to renew a
    product that is `HIDDEN_BY_SUSPENSION` rather than `EXPIRED`
    (DDS §7.3 lifecycle rules).
    """

    default_message = "This action conflicts with the current state of the resource."
    default_status_code = http_status.HTTP_409_CONFLICT


def custom_exception_handler(exc, context):
    """
    Global DRF exception handler, wired via
    `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Normalizes every error source
    into the PRD §17 failure envelope:

    1. `ApplicationError` (and subclasses) raised anywhere in a service layer.
    2. Standard DRF exceptions (`ValidationError`, `NotFound`,
       `PermissionDenied`, `AuthenticationFailed`, throttling, etc).

    Anything neither DRF nor this handler recognizes is left to propagate
    so an unexpected 500 is never silently reshaped or swallowed.
    """
    if isinstance(exc, ApplicationError):
        return error_response(
            message=exc.message,
            errors=exc.errors,
            status=exc.status_code,
        )

    response = drf_default_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data

    if isinstance(detail, dict) and set(detail.keys()) == {"detail"}:
        message = str(detail["detail"])
        errors = {}
    else:
        message = (
            "Validation failed."
            if response.status_code == http_status.HTTP_400_BAD_REQUEST
            else str(exc)
        )
        errors = detail if isinstance(detail, dict | list) else {"detail": detail}

    return error_response(message=message, errors=errors, status=response.status_code)
