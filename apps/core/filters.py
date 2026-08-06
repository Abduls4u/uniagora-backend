from rest_framework.filters import BaseFilterBackend


class ActiveUniversityFilterBackend(BaseFilterBackend):
    university_lookup_field = "university"

    def filter_queryset(self, request, queryset, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return queryset.none()

        active_university = getattr(user, "active_university", None)
        if active_university is None:
            return queryset.none()

        lookup_field = getattr(
            view, "university_lookup_field", self.university_lookup_field
        )
        return queryset.filter(**{lookup_field: active_university})
