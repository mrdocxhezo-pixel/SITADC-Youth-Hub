from django.apps import AppConfig


class ConfigurationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.configuration"
    verbose_name = "System Configuration"

    def ready(self):
        import apps.configuration.signals  # noqa: F401
