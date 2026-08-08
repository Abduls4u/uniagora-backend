from django.db import transaction

from apps.common.exceptions import ConflictError

from .models import Store

# Sentinel distinguishing "field omitted from this call" from "field
# explicitly supplied as None/blank" in update operations — the same
# pattern already established in the project (see EDD_users_authentication
# ADR-U5). A plain `None` default cannot make this distinction for
# nullable fields like `description`/`contact_phone` without also
# discarding a legitimate "clear this field" request.
_UNSET = object()


class StoreService:
    """
    Mutating business operations for `Store` (DDS §4.5, Architecture §2/§7).

    Views call this service; this service never imports views or
    serializers. Every method is the transaction boundary for its own
    write, per Architecture §7, even where a single row is touched —
    consistent with the majority convention already set by
    `UniversityService`/`VendorApplicationService`/`VendorSuspensionService`.
    """

    @staticmethod
    @transaction.atomic
    def create(
        *, vendor_profile, display_name=None, description=None, contact_phone=None
    ):
        """
        Creates the single `Store` owned by `vendor_profile`.

        - `display_name` defaults to `vendor_profile.store_name` when omitted.
        - `contact_phone` defaults to `vendor_profile.phone_number` when omitted.
        - `is_active` is never accepted here; always the model default (`True`).
        - `slug` is never accepted here; derived by `AutoSlugMixin` from
          `display_name` on first save.

        Raises `ConflictError` (409) if `vendor_profile` already has a store —
        a friendly, service-layer duplicate check ahead of the DB-level
        OneToOneField constraint (DDS §7.2's "friendly error before it would
        ever hit the DB" pattern).
        """
        if hasattr(vendor_profile, "store"):
            raise ConflictError("This vendor already has a store.")

        store = Store.objects.create(
            vendor_profile=vendor_profile,
            display_name=display_name
            if display_name is not None
            else vendor_profile.store_name,
            description=description,
            contact_phone=(
                contact_phone
                if contact_phone is not None
                else vendor_profile.phone_number
            ),
        )
        return store

    @staticmethod
    @transaction.atomic
    def update(*, store, display_name=_UNSET, description=_UNSET, contact_phone=_UNSET):
        """
        Updates only explicitly-provided storefront fields (`display_name`,
        `description`, `contact_phone`). Never touches `vendor_profile`,
        `slug`, or `is_active` — those are not parameters of this method at
        all, so there is no code path by which this service could mutate
        them, regardless of what a caller passes through from a serializer.
        """
        update_fields = []

        if display_name is not _UNSET:
            store.display_name = display_name
            update_fields.append("display_name")
        if description is not _UNSET:
            store.description = description
            update_fields.append("description")
        if contact_phone is not _UNSET:
            store.contact_phone = contact_phone
            update_fields.append("contact_phone")

        if update_fields:
            update_fields.append("updated_at")
            store.save(update_fields=update_fields)
        return store

    @staticmethod
    @transaction.atomic
    def delete(*, store):
        """
        Soft-deletes the store via `BaseModel`'s default `.delete()`
        behavior (common app EDD §5) — no `hard=True`, consistent with the
        project's soft-delete-by-default convention (DDS §11 Assumption 11).
        """
        store.delete()
        return store

    @staticmethod
    @transaction.atomic
    def set_active_state(*, store, is_active):
        """
        Toggles `Store.is_active`.

        Intended to be called exclusively by
        `vendors.services.VendorSuspensionService.suspend()`/`reinstate()`
        as the store-side half of the DDS §9.2 cascade — never reachable
        from any endpoint in this app, since `is_active` is deliberately
        absent from every store-facing serializer. Idempotent: a no-op
        save is skipped if the value is already correct.
        """
        if store.is_active != is_active:
            store.is_active = is_active
            store.save(update_fields=["is_active", "updated_at"])
        return store
