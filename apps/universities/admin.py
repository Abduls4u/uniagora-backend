from django.contrib import admin

from apps.common.admin import SoftDeleteAdminMixin

from .models import University


@admin.register(University)
class UniversityAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("short_name", "name", "is_active", "is_deleted", "created_at")
    list_filter = ("is_active", "is_deleted")
    search_fields = ("name", "short_name", "slug")
    readonly_fields = ("id", "slug", "created_at", "updated_at")
    ordering = ("name",)
