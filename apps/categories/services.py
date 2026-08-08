"""
CategoryService — DDS §10: "Tree management (admin-only, most of it
post-MVP per PRD)."

Only the MVP-exposed operations are implemented: create, rename, activate,
deactivate, and guarded soft-delete. Reparenting and sibling reordering are
NOT exposed in MVP — DDS §4.6: "No tree-mutation methods — reparenting/
reordering belongs to a future CategoryService... not MVP-exposed per PRD,
but schema is ready." See ADR-CAT1 in the EDD.
"""

from django.db import transaction

from apps.common.exceptions import ConflictError

from .models import Category

_UNSET = object()


class CategoryService:
    """Static-method service layer for `Category`. No instance state."""

    @staticmethod
    @transaction.atomic
    def create(*, name, parent=None, display_order=0):
        """
        Create a category. `slug` is never accepted as input (AutoSlugMixin
        derives it). `is_active` is never accepted — new categories are
        always created active.
        """
        return Category.objects.create(
            name=name,
            parent=parent,
            display_order=display_order,
        )

    @staticmethod
    @transaction.atomic
    def update(*, category, name=_UNSET):
        """
        Rename a category. `parent`/`display_order` (reparenting/
        reordering) and `is_active` are intentionally excluded — see
        module docstring and ADR-CAT1. Uses the project's `_UNSET`
        sentinel pattern to distinguish "omitted" from "explicitly set."
        """
        if name is not _UNSET:
            category.name = name
            category.save(update_fields=["name", "updated_at"])
        return category

    @staticmethod
    @transaction.atomic
    def activate(*, category):
        if category.is_active:
            raise ConflictError("Category is already active.")
        category.is_active = True
        category.save(update_fields=["is_active", "updated_at"])
        return category

    @staticmethod
    @transaction.atomic
    def deactivate(*, category):
        if not category.is_active:
            raise ConflictError("Category is already inactive.")
        category.is_active = False
        category.save(update_fields=["is_active", "updated_at"])
        return category

    @staticmethod
    @transaction.atomic
    def delete(*, category):
        """
        Soft-delete a category.

        DDS §4.6: deletion "requires children to be reparented or
        deactivated first (service-layer rule)." Since reparenting is not
        exposed in MVP, and `is_active` does not remove a child from the
        tree, the only way to satisfy this precondition is for every child
        to itself be soft-deleted first. Blocks while any alive child
        (active or inactive) still references this category as its parent.
        """
        blocking_children = category.children.alive()
        if blocking_children.exists():
            raise ConflictError(
                "Category has subcategories that must be deleted first."
            )
        category.delete()
        return category
