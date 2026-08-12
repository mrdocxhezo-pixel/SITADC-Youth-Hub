"""Application configuration for the Enterprise Search module."""

from django.apps import AppConfig


class SearchConfig(AppConfig):
    """Configuration for the Phase 26 Enterprise Search app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.search"
    label = "search"
    verbose_name = "Enterprise Search"
