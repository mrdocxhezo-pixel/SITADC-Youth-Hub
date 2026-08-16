"""View-level tests for the Calendar & Meetings app."""

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
from apps.meetings.models import (
    Calendar,
    CalendarEvent,
    Meeting,
    MeetingTemplate,
    MeetingVenue,
)
from apps.meetings.tests.base import MeetingsTestCase


class DashboardViewTests(MeetingsTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("meetings:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_accessible_to_manager(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("meetings:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Calendar & Meetings")

    def test_dashboard_shows_upcoming_meetings(self):
        self.login_as(self.manager)
        Meeting.objects.create(
            title="Upcoming Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            status=MeetingStatus.CONFIRMED,
        )
        response = self.client.get(reverse("meetings:dashboard"))
        self.assertContains(response, "Upcoming Meeting")


class CalendarListViewTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)
        self.calendar = self.create_calendar(self.manager)

    def test_calendar_list_view(self):
        response = self.client.get(reverse("meetings:calendar_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.calendar.name)

    def test_calendar_list_search(self):
        Calendar.objects.create(
            name="Searchable Calendar",
            calendar_type=CalendarType.TEAM,
            owner=self.manager,
        )
        response = self.client.get(reverse("meetings:calendar_list") + "?q=Searchable")
        self.assertContains(response, "Searchable Calendar")

    def test_calendar_create_view_get(self):
        response = self.client.get(reverse("meetings:calendar_create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "New Calendar")

    def test_calendar_create_view_post(self):
        response = self.client.post(
            reverse("meetings:calendar_create"),
            {
                "name": "New Calendar",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after create
        self.assertTrue(Calendar.objects.filter(name="New Calendar").exists())

    def test_calendar_detail_view(self):
        response = self.client.get(
            reverse("meetings:calendar_detail", args=[self.calendar.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.calendar.name)

    def test_calendar_update_view_get(self):
        response = self.client.get(
            reverse("meetings:calendar_update", args=[self.calendar.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Calendar")

    def test_calendar_update_view_post(self):
        response = self.client.post(
            reverse("meetings:calendar_update", args=[self.calendar.pk]),
            {
                "name": "Updated Calendar",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.calendar.refresh_from_db()
        self.assertEqual(self.calendar.name, "Updated Calendar")

    def test_calendar_archive_view(self):
        response = self.client.post(
            reverse("meetings:calendar_archive", args=[self.calendar.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.calendar.refresh_from_db()
        self.assertTrue(self.calendar.is_archived)


class CalendarEventViewTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)
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

    def test_event_list_view(self):
        response = self.client.get(reverse("meetings:event_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_event_detail_view(self):
        response = self.client.get(
            reverse("meetings:event_detail", args=[self.event.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.event.title)

    def test_event_create_view_get(self):
        response = self.client.get(
            reverse("meetings:event_create", args=[self.calendar.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_event_create_view_post(self):
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
        self.assertTrue(CalendarEvent.objects.filter(title="New Event").exists())

    def test_event_update_view(self):
        response = self.client.post(
            reverse("meetings:event_update", args=[self.event.pk]),
            {
                "title": "Updated Event",
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
        self.event.refresh_from_db()
        self.assertEqual(self.event.title, "Updated Event")

    def test_event_transition_to_cancelled(self):
        response = self.client.post(
            reverse("meetings:event_transition", args=[self.event.pk, "cancelled"])
        )
        self.assertEqual(response.status_code, 302)
        self.event.refresh_from_db()
        self.assertEqual(self.event.status, EventStatus.CANCELLED)


class MeetingViewTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)
        self.meeting = Meeting.objects.create(
            title="Test Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            status=MeetingStatus.DRAFT,
        )

    def test_meeting_list_view(self):
        response = self.client.get(reverse("meetings:meeting_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.meeting.title)

    def test_meeting_detail_view(self):
        response = self.client.get(
            reverse("meetings:meeting_detail", args=[self.meeting.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.meeting.title)

    def test_meeting_create_view_get(self):
        response = self.client.get(reverse("meetings:meeting_create"))
        self.assertEqual(response.status_code, 200)

    def test_meeting_create_view_post(self):
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
        self.assertTrue(Meeting.objects.filter(title="New Meeting").exists())

    def test_meeting_reschedule_view(self):
        response = self.client.post(
            reverse("meetings:meeting_reschedule", args=[self.meeting.pk]),
            {
                "start_at": (timezone.now() + timezone.timedelta(days=5)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=5, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "reason": "Rescheduling for availability",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.RESCHEDULED)

    def test_meeting_status_transitions(self):
        # Confirm
        response = self.client.post(
            reverse("meetings:meeting_transition", args=[self.meeting.pk, "confirm"])
        )
        self.assertEqual(response.status_code, 302)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.CONFIRMED)

        # Complete
        response = self.client.post(
            reverse("meetings:meeting_transition", args=[self.meeting.pk, "complete"])
        )
        self.assertEqual(response.status_code, 302)
        self.meeting.refresh_from_db()
        self.assertEqual(self.meeting.status, MeetingStatus.COMPLETED)

    def test_participant_create_view(self):
        response = self.client.post(
            reverse("meetings:participant_create", args=[self.meeting.pk]),
            {
                "user": self.officer.pk,
                "participant_type": "INTERNAL",
                "role_in_meeting": "ATTENDEE",
                "is_required": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.meeting.participants.filter(user=self.officer).exists())


class TemplateViewTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)
        self.template = MeetingTemplate.objects.create(
            name="Test Template",
            code="TEST",
            meeting_type=MeetingType.STAFF,
        )

    def test_template_list_view(self):
        response = self.client.get(reverse("meetings:template_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.template.name)

    def test_template_create_view(self):
        response = self.client.post(
            reverse("meetings:template_create"),
            {
                "name": "New Template",
                "code": "NEW",
                "meeting_type": MeetingType.STAFF,
                "standard_duration_minutes": 60,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MeetingTemplate.objects.filter(name="New Template").exists())

    def test_template_update_view(self):
        response = self.client.post(
            reverse("meetings:template_update", args=[self.template.pk]),
            {
                "name": "Updated Template",
                "code": "UPD",
                "meeting_type": MeetingType.STAFF,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, "Updated Template")


class VenueViewTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)
        self.venue = MeetingVenue.objects.create(
            name="Test Venue",
            venue_type="BOARDROOM",
            capacity=10,
        )

    def test_venue_list_view(self):
        response = self.client.get(reverse("meetings:venue_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.venue.name)

    def test_venue_create_view(self):
        response = self.client.post(
            reverse("meetings:venue_create"),
            {
                "name": "New Venue",
                "venue_type": "COMMUNITY_HALL",
                "capacity": 50,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MeetingVenue.objects.filter(name="New Venue").exists())

    def test_venue_update_view(self):
        response = self.client.post(
            reverse("meetings:venue_update", args=[self.venue.pk]),
            {
                "name": "Updated Venue",
                "venue_type": "COMMUNITY_HALL",
                "capacity": 20,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.venue.refresh_from_db()
        self.assertEqual(self.venue.name, "Updated Venue")
