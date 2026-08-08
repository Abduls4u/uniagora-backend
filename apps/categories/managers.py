"""
Category managers/querysets. No DDS-named query shape beyond `.alive()`/
`.dead()` (inherited) except `.visible()` — the "alive AND active" shape
implied by DDS §7.3 ("Inactive categories hidden from browse/filter") and
the tree-rendering query pattern documented in DDS §11.
"""

from django.db import models

from apps.common.managers import SoftDeleteQuerySet


class CategoryQuerySet(SoftDeleteQuerySet):
    def visible(self):
        """Alive, active categories — the customer-facing browse/filter shape."""
        return self.alive().filter(is_active=True)


class CategoryManager(models.Manager.from_queryset(CategoryQuerySet)):
    """Built via the same `Manager.from_queryset()` mechanism `common`
    itself uses (common app EDD §22.1)."""

    pass
