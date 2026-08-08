from django.contrib import admin

from apps.common.admin import SoftDeleteAdminMixin

from .models import VendorDocument, VendorProfile


class VendorDocumentInline(admin.TabularInline):
    model = VendorDocument
    extra = 0
    readonly_fields = ("uploaded_at", "reviewed_at")


@admin.register(VendorProfile)
class VendorProfileAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("store_name", "vendor_type", "university", "status", "submitted_at")
    list_filter = ("vendor_type", "status", "university")
    search_fields = ("store_name", "matric_number", "business_name", "user__email")
    inlines = [VendorDocumentInline]


@admin.register(VendorDocument)
class VendorDocumentAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("vendor_profile", "document_type", "status", "uploaded_at")
    list_filter = ("document_type", "status")
