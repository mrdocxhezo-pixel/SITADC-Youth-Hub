"""Performance app configuration."""

from django.apps import AppConfig


class PerformanceConfig(AppConfig):
    """Configuration for the Performance Optimization app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.performance"
    verbose_name = "Performance Optimization"

    def ready(self) -> None:
        """Import signals when app is ready."""
        import apps.performance.signals  # noqa: F401
