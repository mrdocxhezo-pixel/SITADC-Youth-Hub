"""Selector tests for the Calendar & Meetings app."""

from django.utils import timezone

from apps.meetings.constants import (
    CalendarType,
    CalendarVisibility,
    EventStatus,
    EventType,
    MeetingStatus,
    MeetingType,
)
from apps.meetings.models import Calendar, CalendarEvent, Meeting
from apps.meetings.selectors import (
    Q_calendar_visible_to,
    calendar_queryset,
    event_queryset,
    meeting_queryset,
    upcoming_events,
    upcoming_meetings,
    visible_calendars,
    visible_events,
    visible_meetings,
)
from apps.meetings.tests.base import MeetingsTestCase


class CalendarSelectorTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar1 = self.create_calendar(self.manager, name="Manager Calendar")
        self.calendar2 = Calendar.objects.create(
            name="Officer Calendar",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.officer,
        )
        self.calendar3 = Calendar.objects.create(
            name="Private Calendar",
            calendar_type=CalendarType.PERSONAL,
            visibility=CalendarVisibility.PRIVATE,
            owner=self.outsider,
        )

    def test_visible_calendars_for_manager(self):
        calendars = visible_calendars(self.manager)
        self.assertIn(self.calendar1, calendars)
        self.assertIn(self.calendar2, calendars)

    def test_visible_calendars_for_officer(self):
        calendars = visible_calendars(self.officer)
        self.assertIn(self.calendar2, calendars)
        # Officer may not see manager's calendar unless shared

    def test_calendar_queryset_includes_soft_deleted_when_requested(self):
        self.calendar1.delete()
        qs = calendar_queryset(self.manager, include_archived=True)
        self.assertIn(self.calendar1, qs)
        qs_default = calendar_queryset(self.manager)
        self.assertNotIn(self.calendar1, qs_default)

    def test_Q_calendar_visible_to(self):
        scope_ids = []
        q = Q_calendar_visible_to(self.manager, scope_ids)
        # Should not error


class EventSelectorTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)
        self.event1 = CalendarEvent.objects.create(
            title="Manager Event",
            calendar=self.calendar,
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            organizer=self.manager,
            status=EventStatus.DRAFT,
        )
        self.event2 = CalendarEvent.objects.create(
            title="Officer Event",
            calendar=self.calendar,
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            organizer=self.officer,
            status=EventStatus.DRAFT,
        )
        self.event3 = CalendarEvent.objects.create(
            title="Cancelled Event",
            calendar=self.calendar,
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=3),
            end_at=timezone.now() + timezone.timedelta(days=3, hours=1),
            organizer=self.manager,
            status=EventStatus.CANCELLED,
        )

    def test_visible_events_for_manager(self):
        events = visible_events(self.manager)
        self.assertIn(self.event1, events)
        self.assertIn(self.event2, events)
        self.assertNotIn(self.event3, events)  # Cancelled not visible

    def test_upcoming_events(self):
        events = upcoming_events(self.manager, limit=5)
        self.assertIn(self.event1, events)
        self.assertIn(self.event2, events)

    def test_event_queryset_select_related(self):
        qs = event_queryset(self.manager)
        # Should not error and should use select_related


class MeetingSelectorTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting1 = Meeting.objects.create(
            title="Manager Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            status=MeetingStatus.DRAFT,
        )
        self.meeting2 = Meeting.objects.create(
            title="Officer Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.officer,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            status=MeetingStatus.DRAFT,
        )
        self.meeting3 = Meeting.objects.create(
            title="Completed Meeting",
            meeting_type=MeetingType.STAFF,
            organizer=self.manager,
            start_at=timezone.now() - timezone.timedelta(days=10),
            end_at=timezone.now() - timezone.timedelta(days=10, hours=1),
            status=MeetingStatus.COMPLETED,
        )

    def test_visible_meetings_for_manager(self):
        meetings = visible_meetings(self.manager)
        self.assertIn(self.meeting1, meetings)
        self.assertIn(self.meeting2, meetings)
        self.assertNotIn(self.meeting3, meetings)  # Completed meetings may not be "visible" in some contexts

    def test_upcoming_meetings(self):
        meetings = upcoming_meetings(self.manager, limit=5)
        self.assertIn(self.meeting1, meetings)
        self.assertIn(self.meeting2, meetings)
        self.assertNotIn(self.meeting3, meetings)

    def test_meeting_queryset(self):
        qs = meeting_queryset(self.manager)
        self.assertIn(self.meeting1, qs)
