from django.contrib import admin

from apps.common.admin import SoftDeleteAdminMixin

from .models import Store


@admin.register(Store)
class StoreAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "display_name",
        "vendor_profile",
        "slug",
        "is_active",
        "is_deleted",
        "created_at",
    )
    list_filter = ("is_active", "is_deleted")
    search_fields = ("display_name", "slug", "vendor_profile__store_name")
    readonly_fields = ("slug", "created_at", "updated_at")
    autocomplete_fields = ("vendor_profile",)
