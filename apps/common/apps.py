from django.apps import AppConfig


class CommonConfig(AppConfig):
    """
    App configuration for the `common` app.

    `common` owns zero domain models (DDS §3: "*(none — abstract only)*").
    `default_auto_field` is declared for Django 5 convention compliance even
    though no concrete model is defined directly in this app.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Common"
