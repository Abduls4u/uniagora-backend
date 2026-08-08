from django.contrib import admin

from apps.common.admin import SoftDeleteAdminMixin

from .models import Category


@admin.register(Category)
class CategoryAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "parent",
        "display_order",
        "is_active",
        "is_deleted",
    )
    list_filter = ("is_active", "is_deleted")
    search_fields = ("name", "slug")
    autocomplete_fields = ("parent",)
    readonly_fields = ("slug",)
