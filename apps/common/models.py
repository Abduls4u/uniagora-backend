"""
Abstract base model shared by every persisted entity in the backend.

Zero domain knowledge lives here (Backend Architecture §1: "common —
Pure generic infra — zero domain knowledge"). Every model in every other
app (`University`, `User`, `VendorProfile`, `Product`, ... ) inherits from
`BaseModel` instead of `models.Model` directly.
"""

import uuid

from django.db import models

from .managers import SoftDeleteManager


class BaseModel(models.Model):
    """
    Supplies the four persistence conventions documented in DDS §4
    (model-spec preamble): UUID primary key, `created_at`/`updated_at`
    timestamps, and the `is_deleted` soft-delete flag. These four fields
    are deliberately "not repeated in the field tables" of any domain
    model in the DDS, because they live here once.

    DDS-mandated fields:
        id: UUIDField, primary_key=True, default=uuid4, editable=False.
        created_at: DateTimeField, auto_now_add=True.
        updated_at: DateTimeField, auto_now=True.
        is_deleted: BooleanField, default=False, indexed.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    # `objects` is unfiltered by default — it returns every row, including
    # soft-deleted ones. Callers exclude soft-deleted rows explicitly via
    # `.alive()` (e.g. `Product.objects.alive().filter(...)`). See
    # managers.py for the full design rationale
    objects = SoftDeleteManager()

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft-deletes by default (DDS §11, Assumption 11: "Soft-delete
        (is_deleted) is the default deletion behavior application-wide").

        Pass `hard=True` only for the specific, individually-justified
        hard-delete paths documented per-relationship in DDS §8 (Cascade
        Rules) — e.g. an admin hard-removing clearly fraudulent data.
        Everyday user-facing "delete" actions must route through the
        default soft-delete behavior via the owning app's service layer.
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)
        self.is_deleted = True
        self.save(update_fields=["is_deleted", "updated_at"])
        return None

    def restore(self) -> None:
        """Reverses a soft-delete."""
        self.is_deleted = False
        self.save(update_fields=["is_deleted", "updated_at"])
