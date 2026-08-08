from django.apps import AppConfig


class StoresConfig(AppConfig):
    """
    App registration for `stores`.

    Owns exactly one concrete model, `Store` (DDS §4.5) — the public-facing
    storefront profile, 1:1 with `vendors.VendorProfile`.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stores"
    verbose_name = "Stores"
