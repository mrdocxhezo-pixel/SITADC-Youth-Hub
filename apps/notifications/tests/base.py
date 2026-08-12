"""Shared fixtures for Notifications & Announcements tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.notifications.constants import (
    AnnouncementAudience,
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationType,
)
from apps.rbac.authorization import clear_permission_cache
from apps.rbac.models import Role

User = get_user_model()


class NotificationsTestCase(TestCase):
    """Set up default users and permissions for notifications tests."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        # Ensure permissions exist even if running with --nomigrations.
        from django.apps import apps
        from django.contrib.auth.management import create_permissions
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)

        # Ensure reference numbering schemes exist.
        from apps.references.constants import ReferenceModules, SequenceResetPeriod
        from apps.references.models import ReferenceNumberScheme
        ReferenceNumberScheme.objects.update_or_create(
            code="notification",
            defaults={
                "name": "Notification Reference",
                "module": ReferenceModules.NOTIFICATIONS,
                "record_type": "notification",
                "prefix": "NTF",
                "sequence_length": 6,
                "reset_period": SequenceResetPeriod.ANNUALLY,
                "is_active": True,
            },
        )
        ReferenceNumberScheme.objects.update_or_create(
            code="announcement",
            defaults={
                "name": "Announcement Reference",
                "module": ReferenceModules.ANNOUNCEMENTS,
                "record_type": "announcement",
                "prefix": "ANN",
                "sequence_length": 6,
                "reset_period": SequenceResetPeriod.ANNUALLY,
                "is_active": True,
            },
        )

        # Create test users.
        cls.manager = cls.create_test_user("manager")
        cls.officer = cls.create_test_user("officer")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")

        # Module permissions are attached to the Role content type (matching
        # the RBAC seed migrations) so authorization via codename works.
        ct = ContentType.objects.get_for_model(Role)
        codes = {
            "notifications.view": "Can view notifications",
            "notifications.create": "Can create notifications",
            "notifications.send": "Can send notifications",
            "notifications.manage_templates": "Can manage notification templates",
            "notifications.manage_rules": "Can manage notification rules",
            "notifications.manage": "Can manage notifications",
            "announcements.view": "Can view announcements",
            "announcements.create": "Can create announcements",
            "announcements.update": "Can update announcements",
            "announcements.publish": "Can publish announcements",
            "announcements.manage": "Can manage announcements",
            "preferences.view": "Can view preferences",
            "preferences.update": "Can update preferences",
            "preferences.manage": "Can manage preferences",
        }
        cls.permissions = {}
        for codename, name in codes.items():
            perm, _ = Permission.objects.get_or_create(
                codename=codename,
                content_type=ct,
                defaults={"name": name},
            )
            cls.permissions[codename] = perm

        # Manager has full module control.
        cls.manager.user_permissions.add(
            cls.permissions["notifications.manage"],
            cls.permissions["announcements.manage"],
            cls.permissions["preferences.manage"],
        )
        # Officer administers templates/rules/announcements.
        cls.officer.user_permissions.add(
            cls.permissions["notifications.view"],
            cls.permissions["notifications.create"],
            cls.permissions["notifications.send"],
            cls.permissions["notifications.manage_templates"],
            cls.permissions["notifications.manage_rules"],
            cls.permissions["announcements.view"],
            cls.permissions["announcements.create"],
            cls.permissions["announcements.update"],
            cls.permissions["announcements.publish"],
        )
        # Viewer can browse and manage their own preferences.
        cls.viewer.user_permissions.add(
            cls.permissions["notifications.view"],
            cls.permissions["announcements.view"],
            cls.permissions["preferences.view"],
            cls.permissions["preferences.update"],
        )
        for user in (cls.manager, cls.officer, cls.viewer):
            clear_permission_cache(user)

    @classmethod
    def create_test_user(cls, stem: str):
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=f"{stem}@example.com",
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
            password=cls.password,
        )

    def login_as(self, user):
        """Authenticate the test client as the given user."""
        return self.client.login(email=user.email, password=self.password)

    def grant_permissions(self, user, *codenames: str):
        perms = [self.permissions[code] for code in codenames]
        user.user_permissions.add(*perms)
        clear_permission_cache(user)

    def create_template(self, user, **kwargs):
        from apps.notifications.services import TemplateService
        defaults = {
            "code": kwargs.pop("code", "test_template"),
            "name": "Test Template",
            "title_template": "Hello {{ user_name }}",
            "message_template": "Message for {{ user_name }}",
            "category": NotificationCategory.GENERAL,
            "channel": DeliveryChannel.IN_APP,
            "event_type": "test.event",
        }
        defaults.update(kwargs)
        return TemplateService(user=user).execute(**defaults)

    def create_rule(self, user, **kwargs):
        from apps.notifications.services import RuleService
        defaults = {
            "name": "Test Rule",
            "event_type": "test.event",
            "category": NotificationCategory.GENERAL,
            "notification_type": NotificationType.INFORMATION,
            "priority": NotificationPriority.NORMAL,
            "channels": [DeliveryChannel.IN_APP],
            "recipient_user": kwargs.pop("recipient_user", None),
        }
        defaults.update(kwargs)
        return RuleService(user=user).execute(**defaults)

    def create_notification(self, user, **kwargs):
        from apps.notifications.services import NotificationService
        defaults = {
            "recipient": kwargs.pop("recipient", self.viewer),
            "title": "Test Notification",
            "message": "A test notification message.",
            "notification_type": NotificationType.INFORMATION,
            "category": NotificationCategory.GENERAL,
            "priority": NotificationPriority.NORMAL,
            "source_app": "tests",
            "channels": [DeliveryChannel.IN_APP],
            "actor": user,
        }
        defaults.update(kwargs)
        return NotificationService(user=user).execute(**defaults)

    def create_announcement(self, user, **kwargs):
        from apps.notifications.services import AnnouncementService
        defaults = {
            "title": "Test Announcement",
            "message": "A test announcement message.",
            "audience_type": AnnouncementAudience.EVERYONE,
            "publish_now": False,
        }
        defaults.update(kwargs)
        return AnnouncementService(user=user).execute(**defaults)
