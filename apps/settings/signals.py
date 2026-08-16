"""Signals for the Settings app."""

import logging
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_settings(sender, instance, created, **kwargs):
    """Create UserSettings when a new user is created."""
    if created:
        from apps.settings.models import UserSettings, UserSettingsDefault
        defaults = UserSettingsDefault.load()
        UserSettings.objects.get_or_create(
            user=instance,
            defaults={
                "theme": defaults.default_theme,
                "density": defaults.default_density,
                "dashboard_layout": defaults.default_dashboard_layout,
                "animations_enabled": defaults.default_animations,
                "email_notifications": defaults.default_email_notifications,
                "in_app_notifications": defaults.default_in_app_notifications,
                "browser_notifications": defaults.default_browser_notifications,
                "profile_visibility": defaults.default_profile_visibility,
                "language": defaults.default_language,
                "country": defaults.default_country,
                "timezone": defaults.default_timezone,
            },
        )


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def sync_user_settings(sender, instance, **kwargs):
    """Sync user profile with settings on save."""
    # This can be expanded to sync settings with user profile fields
    pass