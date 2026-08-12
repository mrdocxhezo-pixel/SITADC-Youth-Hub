"""Application configuration for the Calendar & Meetings module."""

from django.apps import AppConfig


class MeetingsConfig(AppConfig):
    """Configuration for the Phase 24 Calendar & Meetings app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.meetings"
    label = "meetings"
    verbose_name = "Calendar and Meetings"
