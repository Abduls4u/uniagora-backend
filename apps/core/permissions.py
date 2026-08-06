from rest_framework.permissions import BasePermission


class IsAuthenticatedCustomer(BasePermission):
    message = "Authentication is required to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)


class IsVerifiedVendor(BasePermission):
    message = "A verified vendor profile is required to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False
        vendor_profile = getattr(user, "vendor_profile", None)
        if vendor_profile is None:
            return False
        return bool(getattr(vendor_profile, "is_verified", False))


class IsOwnerVendor(BasePermission):
    message = "You do not own this resource."

    def has_object_permission(self, request, view, obj):
        user = getattr(request, "user", None)
        if not (user and user.is_authenticated):
            return False

        requester_vendor_profile = getattr(user, "vendor_profile", None)
        if requester_vendor_profile is None:
            return False

        object_vendor_profile = self._resolve_vendor_profile(obj)
        if object_vendor_profile is None:
            return False
        return object_vendor_profile == requester_vendor_profile

    @staticmethod
    def _resolve_vendor_profile(obj):
        vendor_profile = getattr(obj, "vendor_profile", None)
        if vendor_profile is not None:
            return vendor_profile

        store = getattr(obj, "store", None)
        if store is not None:
            return getattr(store, "vendor_profile", None)

        return None


class IsAdmin(BasePermission):
    message = "Admin privileges are required to perform this action."

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        return bool(
            user and user.is_authenticated and (user.is_staff or user.is_superuser)
        )
