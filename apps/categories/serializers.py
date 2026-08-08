"""
Category serializers.
"""

from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    """Read-only representation used for every response body."""

    parent = serializers.SlugRelatedField(slug_field="slug", read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "parent",
            "display_order",
            "is_active",
            "created_at",
            "updated_at",
        ]
        # "parent" is excluded here — it's already explicitly declared
        # read_only=True above; DRF disallows listing an explicitly
        # declared field in read_only_fields as well.
        read_only_fields = [f for f in fields if f != "parent"]


class CategoryCreateSerializer(serializers.ModelSerializer):
    """
    The only serializer that accepts `parent`/`display_order` as input —
    both are set once, at creation. Post-creation, neither is writable
    (see `CategoryService.update` / ADR-CAT1).
    """

    parent = serializers.SlugRelatedField(
        slug_field="slug",
        queryset=Category.objects.alive(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Category
        fields = ["name", "parent", "display_order"]

    def validate(self, attrs):
        """
        Friendly, pre-DB duplicate-sibling-name check (DDS §7.2 pattern).
        NOTE: for root categories (parent=None) this check is the *only*
        enforcement — see ADR-CAT2 in the EDD re: NULL-distinct composite
        unique constraint behavior in PostgreSQL.
        """
        parent = attrs.get("parent")
        name = attrs.get("name")
        if Category.objects.alive().filter(parent=parent, name=name).exists():
            raise serializers.ValidationError(
                {
                    "name": "A category with this name already exists under the selected parent."
                }
            )
        return attrs


class CategoryUpdateSerializer(serializers.ModelSerializer):
    """Only `name` is writable post-creation."""

    class Meta:
        model = Category
        fields = ["name"]

    def validate_name(self, value):
        instance = self.instance
        parent = instance.parent if instance else None
        queryset = Category.objects.alive().filter(parent=parent, name=value)
        if instance is not None:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "A category with this name already exists under the selected parent."
            )
        return value
