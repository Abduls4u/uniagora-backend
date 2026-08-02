"""
Generic, domain-agnostic model mixins. Configured by the consuming model
via class attributes rather than hardcoding any field name, so this file
carries no domain knowledge of its own.
"""

from django.utils.text import slugify


class AutoSlugMixin:
    """
    Populates a slug field from a configurable source field the first time
    a row is saved, uniquifying on collision by appending a numeric suffix.

    The DDS specifies an auto-derived slug for four separate models:
    `University.slug` (from `name`), `Store.slug` (from `display_name`),
    `Category.slug` (from `name`), and `Product.slug` (from `name`, plus a
    short suffix). Rather than reimplementing the same slugify-and-dedupe
    logic four times across four domain apps, it is implemented once here.

    Usage:
        class Store(AutoSlugMixin, BaseModel):
            slug_source_field = "display_name"
            slug = models.SlugField(max_length=170, unique=True, blank=True)
            ...

    Requires the consuming model to use `common.models.BaseModel` (`objects`
    is unfiltered — see managers.py — so the uniqueness check below
    correctly considers soft-deleted rows too; a slug must never be
    reissued to a live row just because its previous owner was
    soft-deleted) and to declare a `SlugField`/`CharField` named per
    `slug_field_name`.
    """

    slug_source_field: str = "name"
    slug_field_name: str = "slug"
    slug_max_length: int = 255

    def _generate_unique_slug(self) -> str:
        source_value = getattr(self, self.slug_source_field)
        base_slug = slugify(source_value)[: self.slug_max_length]
        model_class = self.__class__

        slug = base_slug
        counter = 1
        while (
            model_class.objects.filter(**{self.slug_field_name: slug})
            .exclude(pk=self.pk)
            .exists()
        ):
            suffix = f"-{counter}"
            slug = f"{base_slug[: self.slug_max_length - len(suffix)]}{suffix}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if not getattr(self, self.slug_field_name):
            setattr(self, self.slug_field_name, self._generate_unique_slug())
        super().save(*args, **kwargs)
