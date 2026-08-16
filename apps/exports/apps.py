"""Application configuration for the Export Engine.

Phase 27 — the centralized, permission-aware, branded document-generation
service for the SITADC Youth Hub.
"""

from django.apps import AppConfig


class ExportsConfig(AppConfig):
    """Configuration for the Phase 27 Export Engine app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.exports"
    label = "exports"
    verbose_name = "Export Engine"

    def ready(self) -> None:
        """Import provider and renderer registries so they self-register."""
        # Providers and renderers self-register on import.  Importing them
        # here guarantees the registries are populated whenever Django loads.
        from apps.exports import providers  # noqa: F401
        from apps.exports import renderers  # noqa: F401
