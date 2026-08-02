"""
Generic validators reused by more than one domain app.

Only validators with a genuine cross-app audience belong here — validation
specific to a single app's fields (e.g. `Review.rating` 1–5) stays in that
app per DDS §7.2/§7.1. `phone_number` appears on both `User` (DDS §4.2:
"validated at serializer level") and `VendorProfile`/`Store`, so it is
implemented once here instead of independently in each app's serializers.
"""

import re

from django.core.exceptions import ValidationError

# Loose E.164-style pattern: optional leading '+', 7-15 digits total.
PHONE_NUMBER_REGEX = re.compile(r"^\+?[0-9]{7,15}$")


def validate_phone_number(value: str) -> None:
    if not PHONE_NUMBER_REGEX.match(value):
        raise ValidationError(
            "Enter a valid phone number (7-15 digits, optional leading '+')."
        )
