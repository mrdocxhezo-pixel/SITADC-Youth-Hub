"""Permission tests for the Calendar & Meetings app."""

from django.urls import reverse
from django.utils import timezone

from apps.meetings.constants import (
    CalendarType,
    CalendarVisibility,
    EventStatus,
    EventType,
    MeetingStatus,
    MeetingType,
)
from apps.meetings.models import CalendarEvent, Meeting
from apps.meetings.tests.base import MeetingsTestCase


class CalendarPermissionTests(MeetingsTestCase):
    def test_manager_can_create_calendar(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:calendar_create"),
            {
                "name": "New Calendar",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_create_calendar(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("meetings:calendar_create"))
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_access_calendar(self):
        self.login_as(self.outsider)
        cal = self.create_calendar(self.manager)
        response = self.client.get(reverse("meetings:calendar_detail", args=[cal.pk]))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_update_own_calendar(self):
        self.login_as(self.manager)
        cal = self.create_calendar(self.manager)
        response = self.client.post(
            reverse("meetings:calendar_update", args=[cal.pk]),
            {
                "name": "Updated",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_officer_cannot_update_others_calendar(self):
        self.login_as(self.officer)
        cal = self.create_calendar(self.manager)
        response = self.client.post(
            reverse("meetings:calendar_update", args=[cal.pk]),
            {
                "name": "Hacked",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_calendar_share_permission(self):
        self.login_as(self.manager)
        cal = self.create_calendar(self.manager)
        response = self.client.post(
            reverse("meetings:calendar_share_create", args=[cal.pk]),
            {
                "user": self.officer.pk,
                "permission_level": "VIEW",
            },
        )
        self.assertEqual(response.status_code, 302)


class EventPermissionTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)
        self.event = CalendarEvent.objects.create(
            title="Test Event",
            calendar=self.calendar,
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            organizer=self.manager,
            status=EventStatus.DRAFT,
        )

    def test_manager_can_create_event(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:event_create", args=[self.calendar.pk]),
            {
                "title": "New Event",
                "event_type": EventType.MEETING,
                "start_at": (timezone.now() + timezone.timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=2, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_create_event(self):
        self.login_as(self.viewer)
        response = self.client.get(
            reverse("meetings:event_create", args=[self.calendar.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_view_event(self):
        self.login_as(self.outsider)
        response = self.client.get(
            reverse("meetings:event_detail", args=[self.event.pk])
        )
        self.assertEqual(response.status_code, 403)


class MeetingPermissionTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = Meeting.objects.create(
            title="Test Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            status=MeetingStatus.DRAFT,
        )

    def test_manager_can_create_meeting(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:meeting_create"),
            {
                "title": "New Meeting",
                "meeting_type": MeetingType.STAFF,
                "start_at": (timezone.now() + timezone.timedelta(days=3)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=3, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_viewer_cannot_create_meeting(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("meetings:meeting_create"))
        self.assertEqual(response.status_code, 403)

    def test_outsider_cannot_view_meeting(self):
        self.login_as(self.outsider)
        response = self.client.get(
            reverse("meetings:meeting_detail", args=[self.meeting.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_update_own_meeting(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:meeting_update", args=[self.meeting.pk]),
            {
                "title": "Updated Meeting",
                "meeting_type": MeetingType.STAFF,
                "start_at": (timezone.now() + timezone.timedelta(days=3)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=3, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_officer_cannot_update_others_meeting(self):
        self.login_as(self.officer)
        response = self.client.post(
            reverse("meetings:meeting_update", args=[self.meeting.pk]),
            {
                "title": "Hacked",
                "meeting_type": MeetingType.STAFF,
                "start_at": (timezone.now() + timezone.timedelta(days=3)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=3, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
            },
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_can_transition_meeting_status(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:meeting_transition", args=[self.meeting.pk, "confirm"])
        )
        self.assertEqual(response.status_code, 302)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, "CONFIRMED")

    def test_viewer_cannot_transition_meeting(self):
        self.login_as(self.viewer)
        response = self.client.post(
            reverse("meetings:meeting_transition", args=[self.meeting.pk, "confirm"])
        )
        self.assertEqual(response.status_code, 403)

    def test_participant_permissions(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("meetings:participant_create", args=[self.meeting.pk]),
            {
                "user": self.officer.pk,
                "participant_type": "INTERNAL",
                "role_in_meeting": "ATTENDEE",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_agenda_permissions(self):
        self.login_as(self.manager)
        agenda = self.meeting.agendas.create(
            title="Test Agenda",
            prepared_by=self.manager,
        )
        response = self.client.post(
            reverse("meetings:agenda_update", args=[self.meeting.pk, agenda.pk]),
            {
                "title": "Updated Agenda",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_minutes_permissions(self):
        self.login_as(self.manager)
        minutes = self.meeting.minutes.create(
            title="Test Minutes",
            prepared_by=self.manager,
        )
        response = self.client.post(
            reverse("meetings:minutes_update", args=[self.meeting.pk, minutes.pk]),
            {
                "title": "Updated Minutes",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_action_permissions(self):
        self.login_as(self.manager)
        action = self.meeting.actions.create(
            description="Test Action",
            owner=self.officer,
            due_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        response = self.client.post(
            reverse("meetings:action_update", args=[self.meeting.pk, action.pk]),
            {
                "description": "Updated Action",
            },
        )
        self.assertEqual(response.status_code, 302)
