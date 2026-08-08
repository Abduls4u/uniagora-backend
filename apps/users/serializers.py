from rest_framework import serializers

from apps.universities.models import University
from apps.universities.serializers import UniversitySerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only representation of a user's own profile. Used for every
    response body that echoes a User: register, login, /users/me/, and
    the active-university change endpoint.
    """

    active_university = UniversitySerializer(read_only=True)
    is_vendor = serializers.BooleanField(read_only=True)
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "phone_number",
            "active_university",
            "is_vendor",
            "is_admin",
            "is_active",
            "date_joined",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """The only serializer that accepts client input against `User`
    itself. Deliberately excludes:
      - `email` — identity; no dedicated change-email flow is specified in
        any frozen document, so none is invented here.
      - `active_university` — carries its own business rule (must be
        active), handled by `SetActiveUniversitySerializer` below.
    """

    class Meta:
        model = User
        fields = ["full_name", "phone_number"]
        extra_kwargs = {
            "full_name": {"required": False},
            "phone_number": {"required": False},
        }


class SetActiveUniversitySerializer(serializers.Serializer):
    """Validates and resolves a `university_slug` into an active
    `University` instance. Rejecting inactive universities at selection
    time is an Engineering Implementation Decision — see EDD §10,
    assumption 2.
    """

    university_slug = serializers.SlugField()

    def validate_university_slug(self, value):
        try:
            return University.objects.active().get(slug=value)
        except University.DoesNotExist:
            raise serializers.ValidationError(
                "University not found or is not currently active."
            ) from None
