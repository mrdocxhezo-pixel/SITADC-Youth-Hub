"""Form tests for the Calendar & Meetings app."""

from django.utils import timezone

from apps.meetings.constants import (
    CalendarType,
    CalendarVisibility,
    EventStatus,
    EventType,
    MeetingMode,
    MeetingStatus,
    MeetingType,
)
from apps.meetings.forms import (
    AgendaItemForm,
    CalendarEventForm,
    CalendarForm,
    MeetingActionItemForm,
    MeetingAgendaForm,
    MeetingDecisionForm,
    MeetingForm,
    MeetingMinutesForm,
    MeetingParticipantForm,
    MeetingTemplateForm,
    MeetingVenueForm,
)
from apps.meetings.models import Meeting, MeetingTemplate
from apps.meetings.tests.base import MeetingsTestCase


class CalendarFormTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)

    def test_calendar_form_valid(self):
        form = CalendarForm(
            data={
                "name": "Test Calendar",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
                "description": "Test description",
            },
            user=self.manager,
        )
        self.assertTrue(form.is_valid())

    def test_calendar_form_invalid_missing_name(self):
        form = CalendarForm(
            data={
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
            },
            user=self.manager,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_calendar_form_update(self):
        form = CalendarForm(
            data={
                "name": "Updated Calendar",
                "calendar_type": CalendarType.TEAM,
                "visibility": CalendarVisibility.TEAM,
                "description": "Updated",
            },
            instance=self.calendar,
            user=self.manager,
        )
        self.assertTrue(form.is_valid())


class CalendarEventFormTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)

    def test_event_form_valid(self):
        form = CalendarEventForm(
            data={
                "title": "Test Event",
                "event_type": EventType.MEETING,
                "calendar": self.calendar.pk,
                "start_at": (timezone.now() + timezone.timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=1, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
                "status": EventStatus.DRAFT,
            },
            user=self.manager,
        )
        self.assertTrue(form.is_valid())

    def test_event_form_invalid_end_before_start(self):
        form = CalendarEventForm(
            data={
                "title": "Bad Event",
                "event_type": EventType.MEETING,
                "calendar": self.calendar.pk,
                "start_at": (timezone.now() + timezone.timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (timezone.now() + timezone.timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "organizer": self.manager.pk,
                "status": EventStatus.DRAFT,
            },
            user=self.manager,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("end_at", form.errors)


class MeetingFormTests(MeetingsTestCase):
    def test_meeting_form_valid(self):
        form = MeetingForm(
            data={
                "title": "Test Meeting",
                "meeting_type": MeetingType.STAFF,
                "start_at": (timezone.now() + timezone.timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (
                    timezone.now() + timezone.timedelta(days=2, hours=1)
                ).strftime("%Y-%m-%dT%H:%M"),
                "organizer": self.manager.pk,
                "mode": MeetingMode.IN_PERSON,
                "status": MeetingStatus.DRAFT,
            },
            user=self.manager,
        )
        self.assertTrue(form.is_valid())

    def test_meeting_form_invalid_end_before_start(self):
        form = MeetingForm(
            data={
                "title": "Bad Meeting",
                "meeting_type": MeetingType.STAFF,
                "start_at": (timezone.now() + timezone.timedelta(days=2)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "end_at": (timezone.now() + timezone.timedelta(days=1)).strftime(
                    "%Y-%m-%dT%H:%M"
                ),
                "organizer": self.manager.pk,
                "mode": MeetingMode.IN_PERSON,
                "status": MeetingStatus.DRAFT,
            },
            user=self.manager,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("end_at", form.errors)


class MeetingParticipantFormTests(MeetingsTestCase):
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

    def test_participant_form_with_user(self):
        form = MeetingParticipantForm(
            data={
                "user": self.officer.pk,
                "participant_type": "INTERNAL",
                "role_in_meeting": "ATTENDEE",
                "is_required": True,
            },
            meeting=self.meeting,
        )
        self.assertTrue(form.is_valid())

    def test_participant_form_without_user(self):
        form = MeetingParticipantForm(
            data={
                "name_snapshot": "External Person",
                "email_snapshot": "external@example.com",
                "participant_type": "EXTERNAL",
                "role_in_meeting": "PRESENTER",
            },
            meeting=self.meeting,
        )
        self.assertTrue(form.is_valid())

    def test_participant_form_requires_user_or_name(self):
        form = MeetingParticipantForm(
            data={
                "participant_type": "INTERNAL",
                "role_in_meeting": "ATTENDEE",
            },
            meeting=self.meeting,
        )
        self.assertFalse(form.is_valid())


class MeetingAgendaFormTests(MeetingsTestCase):
    def test_agenda_form_valid(self):
        form = MeetingAgendaForm(
            data={
                "title": "Test Agenda",
                "confidentiality_level": "INTERNAL",
            },
        )
        self.assertTrue(form.is_valid())


class AgendaItemFormTests(MeetingsTestCase):
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
        self.agenda = self.meeting.agendas.create(
            title="Test Agenda",
            prepared_by=self.manager,
        )

    def test_agenda_item_form_valid(self):
        form = AgendaItemForm(
            data={
                "item_number": 1,
                "display_order": 1,
                "title": "Test Item",
                "item_type": "DISCUSSION",
                "time_allocation_minutes": 30,
            },
            agenda=self.agenda,
        )
        self.assertTrue(form.is_valid())


class MeetingMinutesFormTests(MeetingsTestCase):
    def test_minutes_form_valid(self):
        form = MeetingMinutesForm(
            data={
                "title": "Test Minutes",
                "summary": "Summary",
                "opening": "Opening remarks",
                "closing": "Closing remarks",
                "confidentiality_level": "INTERNAL",
            },
        )
        self.assertTrue(form.is_valid())


class MeetingActionItemFormTests(MeetingsTestCase):
    def test_action_form_valid(self):
        form = MeetingActionItemForm(
            data={
                "description": "Test action",
                "owner": self.officer.pk,
                "priority": "MEDIUM",
                "due_date": (
                    timezone.now().date() + timezone.timedelta(days=7)
                ).isoformat(),
            },
        )
        self.assertTrue(form.is_valid())


class MeetingDecisionFormTests(MeetingsTestCase):
    def test_decision_form_valid(self):
        form = MeetingDecisionForm(
            data={
                "decision_text": "Test decision",
                "decision_type": "RESOLUTION",
                "proposed_by": self.manager.pk,
            },
        )
        self.assertTrue(form.is_valid())


class MeetingVenueFormTests(MeetingsTestCase):
    def test_venue_form_valid(self):
        form = MeetingVenueForm(
            data={
                "name": "Test Venue",
                "venue_type": "BOARDROOM",
                "capacity": 20,
                "address": "123 Main St",
            },
            user=self.manager,
        )
        self.assertTrue(form.is_valid())


class MeetingTemplateFormTests(MeetingsTestCase):
    def test_template_form_valid(self):
        form = MeetingTemplateForm(
            data={
                "name": "Test Template",
                "code": "TEST",
                "meeting_type": MeetingType.STAFF,
                "standard_duration_minutes": 60,
            },
        )
        self.assertTrue(form.is_valid())

    def test_template_form_unique_code(self):
        MeetingTemplate.objects.create(
            name="Existing",
            code="UNIQUE",
            meeting_type=MeetingType.STAFF,
        )
        form = MeetingTemplateForm(
            data={
                "name": "Duplicate",
                "code": "UNIQUE",
                "meeting_type": MeetingType.STAFF,
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("code", form.errors)
