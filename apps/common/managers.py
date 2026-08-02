"""
Generic, domain-agnostic queryset/manager encoding soft-delete semantics.

Belongs in `common` because it carries zero domain knowledge — it is a pure
persistence-layer concern reused identically by every model that inherits
`common.models.BaseModel` (DDS §1.4: "Soft deletion by default").


`objects` is deliberately UNFILTERED by default. `Model.objects.all()`
returns every row, including soft-deleted ones. Exclusion is an explicit,
visible opt-in via `.alive()`:

    Product.objects.alive().filter(university=u, status=ACTIVE)

This was changed from an earlier design where the default manager silently
excluded soft-deleted rows. That design broke down for aggregations,
reporting/analytics, and admin (`Model.objects.count()` would silently
undercount against what an engineer querying the database directly would
see, with no visual signal in the calling code that filtering happened).
Reserving the *implicit* convenience for genuinely safety-critical,
easy-to-forget invariants (see AutoSlugMixin) and using explicit chaining
here matches the project's own "Explicit is better than implicit"
principle, and matches the documented convention in Backend Architecture
§6 ("Product.objects.visible()" as an explicit, named, chained method
rather than a silent default).
"""

from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """Queryset supporting explicit soft-delete-aware filtering and a genuine hard-delete escape hatch."""

    def alive(self) -> "SoftDeleteQuerySet":
        """Rows not soft-deleted. Call explicitly wherever soft-deleted rows must be excluded."""
        return self.filter(is_deleted=False)

    def dead(self) -> "SoftDeleteQuerySet":
        """Only soft-deleted rows (e.g. admin "recently removed" views, audit queries)."""
        return self.filter(is_deleted=True)

    def delete(self):
        """
        Bulk queryset `.delete()` soft-deletes by default, mirroring
        `BaseModel.delete()`'s single-instance behavior (DDS §11,
        Assumption 11 — this is about *deletion behavior*, independent of
        the default-read-filtering question discussed above).
        """
        return self.update(is_deleted=True)

    def hard_delete(self):
        """
        Explicit, unambiguous bulk hard-delete for the rare, individually
        justified paths described in DDS §8 (Cascade Rules) — never the
        default action.
        """
        return super().delete()


class SoftDeleteManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """
    Default manager for `BaseModel`. Proxies `SoftDeleteQuerySet`'s methods
    directly onto the manager (`Model.objects.alive()`,
    `Model.objects.dead()`), while `Model.objects.all()` / `.filter(...)`
    remain unfiltered — see the module-level design note above.
    """

    pass
