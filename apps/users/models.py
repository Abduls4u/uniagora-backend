"""User model — apps.users.

Reproduces DDS §4.2 field-for-field. See EDD §5 for the full rationale
behind each design choice (multiple inheritance, computed role properties,
case-insensitive email uniqueness).
"""

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel
from apps.common.validators import validate_phone_number
from apps.universities.models import University

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """The single identity record for every account (DDS §4.2).

    Customer is the default, implicit role for every row in this table
    (PRD §4) — there is no separate Customer model. Vendor and Admin are
    role *extensions*, never separate rows:
      - Vendor: `hasattr(self, "vendor_profile")` (see `is_vendor`).
      - Admin: `is_staff` / `is_superuser` (see `is_admin`), per
        Architecture §8's "never a redundant/denormalized flag" rule.

    Class-base ordering (`AbstractBaseUser, PermissionsMixin, BaseModel`)
    mirrors the mixin-before-BaseModel MRO convention documented in the
    common app EDD §22.3 — `BaseModel` defines no conflicting methods
    today, but listing it last keeps the ordering forward-safe.
    """

    email = models.EmailField(unique=True, db_index=True)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(
        max_length=20, blank=True, validators=[validate_phone_number]
    )
    active_university = models.ForeignKey(
        University,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
        help_text="Nullable until onboarding completes; changeable anytime (PRD §3).",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        # Multiple abstract bases (AbstractBaseUser, BaseModel) each carry
        # their own Meta; Django does not merge them automatically, so
        # BaseModel's ["-created_at"] default is restated explicitly here
        # rather than silently relied upon.
        ordering = ["-created_at"]
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Case-insensitive uniqueness via lowercase normalization
        # (DDS §13, Assumption 3) rather than a CITEXT extension dependency.
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    @property
    def is_vendor(self):
        """Computed, not stored (Architecture §8). Safe to call before the
        `vendors` app exists in the build order — simply always False
        until then, since no `vendor_profile` reverse accessor can exist
        yet (DDS §4.2: `is_vendor = hasattr(self, "vendor_profile")`).
        """
        return hasattr(self, "vendor_profile")

    @property
    def is_admin(self):
        """Computed from `is_staff` / `is_superuser` (Architecture §8).
        DDS §4.2 distinguishes this platform role from Django's own
        `is_staff` admin-site flag, but the platform role reuses the same
        underlying fields rather than introducing a redundant, driftable
        role column.
        """
        return self.is_staff or self.is_superuser
