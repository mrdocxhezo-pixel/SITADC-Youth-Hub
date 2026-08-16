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
        from django.contrib.auth.models import Permission

        # Get permissions created by RBAC migration (they use Role content type)
        # Meeting permissions
        p_meeting_manage = Permission.objects.get(codename="meetings.manage")
        p_meeting_create = Permission.objects.get(codename="meetings.create")
        p_meeting_update = Permission.objects.get(codename="meetings.update")
        p_meeting_view = Permission.objects.get(codename="meetings.view")
        p_meeting_manage_agendas = Permission.objects.get(codename="meetings.manage_agendas")
        p_meeting_approve_agendas = Permission.objects.get(codename="meetings.approve_agendas")
        p_meeting_manage_participants = Permission.objects.get(codename="meetings.manage_participants")
        p_meeting_send_invitations = Permission.objects.get(codename="meetings.send_invitations")
        p_meeting_record_attendance = Permission.objects.get(codename="meetings.record_attendance")
        p_meeting_verify_attendance = Permission.objects.get(codename="meetings.verify_attendance")
        p_meeting_check_in = Permission.objects.get(codename="meetings.check_in")
        p_meeting_check_out = Permission.objects.get(codename="meetings.check_out")
        p_meeting_manage_quorum = Permission.objects.get(codename="meetings.manage_quorum")
        p_meeting_draft_minutes = Permission.objects.get(codename="meetings.draft_minutes")
        p_meeting_submit_minutes = Permission.objects.get(codename="meetings.submit_minutes")
        p_meeting_review_minutes = Permission.objects.get(codename="meetings.review_minutes")
        p_meeting_approve_minutes = Permission.objects.get(codename="meetings.approve_minutes")
        p_meeting_record_decisions = Permission.objects.get(codename="meetings.record_decisions")
        p_meeting_manage_actions = Permission.objects.get(codename="meetings.manage_actions")
        p_meeting_verify_actions = Permission.objects.get(codename="meetings.verify_actions")
        p_meeting_escalate = Permission.objects.get(codename="meetings.escalate")
        p_meeting_manage_templates = Permission.objects.get(codename="meetings.manage_templates")
        p_meeting_manage_venues = Permission.objects.get(codename="meetings.manage_venues")
        p_meeting_configure = Permission.objects.get(codename="meetings.configure")
        p_meeting_view_confidential = Permission.objects.get(codename="meetings.view_confidential")

        # Calendar permissions
        p_calendar_manage = Permission.objects.get(codename="calendars.manage")
        p_calendar_create = Permission.objects.get(codename="calendars.create")
        p_calendar_update = Permission.objects.get(codename="calendars.update")
        p_calendar_view = Permission.objects.get(codename="calendars.view")
        p_calendar_share = Permission.objects.get(codename="calendars.share")
        p_calendar_archive = Permission.objects.get(codename="calendars.archive")
        p_calendar_restore = Permission.objects.get(codename="calendars.restore")
        p_calendar_export = Permission.objects.get(codename="calendars.export")
        p_calendar_view_confidential = Permission.objects.get(codename="calendars.view_confidential")

        # Event permissions
        p_event_manage = Permission.objects.get(codename="events.manage")
        p_event_create = Permission.objects.get(codename="events.create")
        p_event_update = Permission.objects.get(codename="events.update")
        p_event_view = Permission.objects.get(codename="events.view")
        p_event_schedule = Permission.objects.get(codename="events.schedule")
        p_event_confirm = Permission.objects.get(codename="events.confirm")
        p_event_complete = Permission.objects.get(codename="events.complete")
        p_event_cancel = Permission.objects.get(codename="events.cancel")
        p_event_archive = Permission.objects.get(codename="events.archive")
        p_event_restore = Permission.objects.get(codename="events.restore")
        p_event_export = Permission.objects.get(codename="events.export")
        p_event_manage_reminders = Permission.objects.get(codename="events.manage_reminders")
        p_event_view_confidential = Permission.objects.get(codename="events.view_confidential")

        # Manager gets full control over all three
        cls.manager.user_permissions.add(
            p_meeting_manage,
            p_meeting_create,
            p_meeting_update,
            p_meeting_view,
            p_meeting_manage_agendas,
            p_meeting_approve_agendas,
            p_meeting_manage_participants,
            p_meeting_send_invitations,
            p_meeting_record_attendance,
            p_meeting_verify_attendance,
            p_meeting_check_in,
            p_meeting_check_out,
            p_meeting_manage_quorum,
            p_meeting_draft_minutes,
            p_meeting_submit_minutes,
            p_meeting_review_minutes,
            p_meeting_approve_minutes,
            p_meeting_record_decisions,
            p_meeting_manage_actions,
            p_meeting_verify_actions,
            p_meeting_escalate,
            p_meeting_manage_templates,
            p_meeting_manage_venues,
            p_meeting_configure,
            p_meeting_view_confidential,
            p_calendar_manage,
            p_calendar_create,
            p_calendar_update,
            p_calendar_view,
            p_calendar_share,
            p_calendar_archive,
            p_calendar_restore,
            p_calendar_export,
            p_calendar_view_confidential,
            p_event_manage,
            p_event_create,
            p_event_update,
            p_event_view,
            p_event_schedule,
            p_event_confirm,
            p_event_complete,
            p_event_cancel,
            p_event_archive,
            p_event_restore,
            p_event_export,
            p_event_manage_reminders,
            p_event_view_confidential,
        )

        # Officer can create/update/view all three
        cls.officer.user_permissions.add(
            p_meeting_create,
            p_meeting_update,
            p_meeting_view,
            p_meeting_manage_agendas,
            p_meeting_manage_participants,
            p_meeting_send_invitations,
            p_meeting_record_attendance,
            p_meeting_verify_attendance,
            p_meeting_check_in,
            p_meeting_check_out,
            p_meeting_manage_quorum,
            p_meeting_draft_minutes,
            p_meeting_submit_minutes,
            p_meeting_review_minutes,
            p_meeting_manage_actions,
            p_meeting_verify_actions,
            p_calendar_create,
            p_calendar_update,
            p_calendar_view,
            p_calendar_share,
            p_calendar_export,
            p_event_create,
            p_event_update,
            p_event_view,
            p_event_schedule,
            p_event_confirm,
            p_event_complete,
            p_event_cancel,
            p_event_archive,
            p_event_export,
            p_event_manage_reminders,
        )

        # Viewer can only view all three
        cls.viewer.user_permissions.add(
            p_meeting_view,
            p_calendar_view,
            p_event_view,
            p_calendar_view_confidential,
            p_event_view_confidential,
        )

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
        """Helper to authenticate a test user using the custom User model (email)."""
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