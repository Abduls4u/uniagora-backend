"""Custom manager/queryset for the User model.

Combines Django's BaseUserManager (create_user/create_superuser semantics)
with common.managers.SoftDeleteQuerySet (.alive()/.dead()), matching the
unfiltered-by-default convention established in common app EDD ADR-001.
"""

from django.contrib.auth.base_user import BaseUserManager

from apps.common.managers import SoftDeleteQuerySet


class UserQuerySet(SoftDeleteQuerySet):
    """Adds no domain-specific query shapes beyond what SoftDeleteQuerySet
    already provides (.alive() / .dead() / .hard_delete()). User
    deactivation in MVP is handled via `is_active`, not `is_deleted`
    (DDS §9.1 — "No hard delete in MVP; deactivation via is_active=False"),
    so no deletion-workflow-specific query shape is needed yet. `.alive()`/
    `.dead()` remain available for forward-compatibility and consistency
    with every other BaseModel-derived model.
    """


class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    """Built the same way `common.managers.SoftDeleteManager` is built
    (`Manager.from_queryset()`, common app EDD §22.1) — except starting
    from `BaseUserManager` instead of the plain `models.Manager`, so the
    resulting manager gets both Django's custom-user-model contract
    (`create_user`/`create_superuser`/`normalize_email`) AND
    `UserQuerySet`'s `.alive()`/`.dead()` methods copied onto it.

    Unfiltered by default (common EDD ADR-001) — `.alive()`/`.dead()` are
    explicit, visible opt-ins; `objects.all()` returns every row including
    soft-deleted ones.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        # Email is always stored lowercased (User.save()); comparing
        # against a lowercased input keeps this an index-friendly equality
        # lookup rather than a case-insensitive pattern match, per DDS §13
        # Assumption 3's "normalized-lowercase" approach (no CITEXT).
        return self.get(email=email.lower())
