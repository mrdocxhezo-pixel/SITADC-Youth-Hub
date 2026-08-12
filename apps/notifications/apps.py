"""Application configuration for the Notifications & Announcements module."""

from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    """Configuration for the Phase 25 Notifications & Announcements app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.notifications"
    label = "notifications"
    verbose_name = "Notifications and Announcements"
