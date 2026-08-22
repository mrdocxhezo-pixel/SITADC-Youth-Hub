from django.apps import AppConfig


class AccessibilityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accessibility"
    verbose_name = "Accessibility Review"

    def ready(self) -> None:
        import apps.accessibility.signals  # noqa: F401
