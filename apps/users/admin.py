from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from apps.common.admin import SoftDeleteAdminMixin

from .models import User


@admin.register(User)
class UserAdmin(SoftDeleteAdminMixin, DjangoUserAdmin):
    """Extends Django's stock UserAdmin, adapted for an email-based
    USERNAME_FIELD (no `username` column exists on this model), combined
    with `SoftDeleteAdminMixin` for consistency with every other
    BaseModel-derived admin registration in the project.
    """

    model = User
    ordering = ["-created_at"]
    list_display = [
        "email",
        "full_name",
        "is_staff",
        "is_active",
        "active_university",
        "created_at",
    ]
    list_filter = ["is_staff", "is_active", "active_university"]
    search_fields = ["email", "full_name"]
    readonly_fields = ["id", "created_at", "updated_at", "date_joined", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("full_name", "phone_number", "active_university")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2"),
            },
        ),
    )
