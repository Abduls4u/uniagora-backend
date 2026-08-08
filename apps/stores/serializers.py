from rest_framework import serializers

from apps.common.validators import validate_phone_number

from .models import Store


class StoreSerializer(serializers.ModelSerializer):
    """
    Read-only representation used for every response body: public detail,
    the vendor's own `/stores/me/`, and the echoed object after
    create/update.

    Exposes the public storefront surface (DDS §4.5) plus a minimal
    "verification badge" derived from the related `VendorProfile`
    (PRD §9: "Store contains: ... Verification Badge ..."). Deliberately
    does **not** expose `VendorProfile`'s sensitive verification/document
    fields (`matric_number`, `business_address`, `VendorDocument`, etc.) —
    only the two attributes needed to render a public badge.
    """

    vendor_type = serializers.CharField(
        source="vendor_profile.vendor_type", read_only=True
    )
    is_verified = serializers.BooleanField(
        source="vendor_profile.is_verified", read_only=True
    )

    class Meta:
        model = Store
        fields = [
            "id",
            "display_name",
            "slug",
            "description",
            "contact_phone",
            "is_active",
            "vendor_type",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class StoreWriteSerializer(serializers.ModelSerializer):
    """
    The only serializer that ever accepts client input — used identically
    for store creation (`POST /stores/`) and editing
    (`PATCH /stores/me/`, called with `partial=True`).

    `vendor_profile`, `slug`, and `is_active` are deliberately absent from
    `Meta.fields` entirely, not merely marked read-only, so there is no
    field on this serializer a client could ever populate for them.
    """

    contact_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_null=True,
        allow_blank=True,
        validators=[validate_phone_number],
    )

    class Meta:
        model = Store
        fields = ["display_name", "description", "contact_phone"]
        extra_kwargs = {
            "display_name": {"required": False},
            "description": {"required": False, "allow_null": True, "allow_blank": True},
        }
