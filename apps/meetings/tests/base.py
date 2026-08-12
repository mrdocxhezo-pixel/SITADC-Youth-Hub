"""Shared fixtures for Calendar & Meetings tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.meetings.constants import (
    CalendarType,
    CalendarVisibility,
    EventStatus,
    EventType,
    MeetingMode,
    MeetingType,
)
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class MeetingsTestCase(TestCase):
    """Set up default users and permissions for meetings tests."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        # Ensure permissions exist even if running with --nomigrations
        from django.apps import apps
        from django.contrib.auth.management import create_permissions
        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)

        # Ensure reference numbering scheme exists
        from apps.references.constants import ReferenceModules, SequenceResetPeriod
        from apps.references.models import ReferenceNumberScheme
        for scheme in (
            {
                "code": "calendar",
                "name": "Calendar Reference",
                "module": ReferenceModules.CALENDARS,
                "record_type": "calendar",
                "prefix": "CAL",
            },
            {
                "code": "event",
                "name": "Event Reference",
                "module": ReferenceModules.EVENTS,
                "record_type": "event",
                "prefix": "EVT",
            },
            {
                "code": "meeting",
                "name": "Meeting Reference",
                "module": ReferenceModules.MEETINGS,
                "record_type": "meeting",
                "prefix": "MTG",
            },
        ):
            ReferenceNumberScheme.objects.get_or_create(
                code=scheme["code"],
                defaults={
                    "name": scheme["name"],
                    "module": scheme["module"],
                    "record_type": scheme["record_type"],
                    "prefix": scheme["prefix"],
                    "sequence_length": 6,
                    "reset_period": SequenceResetPeriod.NEVER,
                    "is_active": True,
                },
            )

        # Create test users
        cls.manager = cls.create_test_user("manager")
        cls.officer = cls.create_test_user("officer")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")

        # Assign permissions using RBAC helper (handles caching)
        from django.contrib.contenttypes.models import ContentType
        ct, _ = ContentType.objects.get_or_create(
            app_label="meetings", model="meeting"
        )
        p_manage, _ = Permission.objects.get_or_create(
            codename="meetings.manage", content_type=ct, defaults={"name": "Manage meetings"}
        )
        p_create, _ = Permission.objects.get_or_create(
            codename="meetings.create", content_type=ct, defaults={"name": "Create meetings"}
        )
        p_update, _ = Permission.objects.get_or_create(
            codename="meetings.update", content_type=ct, defaults={"name": "Update meetings"}
        )
        p_view, _ = Permission.objects.get_or_create(
            codename="meetings.view", content_type=ct, defaults={"name": "View meetings"}
        )

        # Manager gets full control
        cls.manager.user_permissions.add(p_manage)
        # Officer can create / update / view
        cls.officer.user_permissions.add(p_create, p_update, p_view)
        # Viewer can only view
        cls.viewer.user_permissions.add(p_view)
        # Clear permission cache after assignment
        clear_permission_cache(cls.manager)
        clear_permission_cache(cls.officer)
        clear_permission_cache(cls.viewer)

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
        """Helper to properly authenticate a test user using the custom User model (email)."""
        return self.client.login(email=user.email, password=self.password)

    def grant_permissions(self, user, *codenames: str):
        perms = [Permission.objects.get(codename=code) for code in codenames]
        user.user_permissions.add(*perms)
        clear_permission_cache(user)

    def create_calendar(self, user, **kwargs):
        from apps.meetings.services import CalendarService
        defaults = {
            "name": "Test Calendar",
            "calendar_type": CalendarType.TEAM,
            "visibility": CalendarVisibility.TEAM,
            "owner": user,
        }
        defaults.update(kwargs)
        service = CalendarService(user=user)
        return service.execute(**defaults)

    def create_event(self, user, calendar, **kwargs):
        from apps.meetings.services import CalendarEventService
        defaults = {
            "title": "Test Event",
            "event_type": EventType.MEETING,
            "calendar": calendar,
            "organizer": user,
            "start_at": timezone.now() + timezone.timedelta(days=1),
            "end_at": timezone.now() + timezone.timedelta(days=1, hours=1),
            "status": EventStatus.DRAFT,
        }
        defaults.update(kwargs)
        service = CalendarEventService(user=user)
        return service.execute(**defaults)

    def create_meeting(self, user, **kwargs):
        from apps.meetings.services import MeetingService
        defaults = {
            "title": "Test Meeting",
            "meeting_type": MeetingType.STAFF,
            "organizer": user,
            "start_at": timezone.now() + timezone.timedelta(days=2),
            "end_at": timezone.now() + timezone.timedelta(days=2, hours=1),
            "mode": MeetingMode.IN_PERSON,
        }
        defaults.update(kwargs)
        service = MeetingService(user=user)
        return service.execute(**defaults)
