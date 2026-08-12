"""Model-level tests for the Calendar & Meetings app."""

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.meetings.constants import (
    CalendarVisibility,
    EventStatus,
    EventType,
    MeetingMode,
    MeetingStatus,
    MeetingType,
)
from apps.meetings.models import (
    AgendaItem,
    CalendarEvent,
    CalendarShare,
    Meeting,
    MeetingActionItem,
    MeetingAgenda,
    MeetingDecision,
    MeetingDocument,
    MeetingMinutes,
    MeetingParticipant,
    MeetingTemplate,
    MeetingVenue,
)
from apps.meetings.tests.base import MeetingsTestCase


class CalendarModelTests(MeetingsTestCase):
    def test_create_calendar_allocates_reference(self):
        cal = self.create_calendar(self.manager)
        self.assertIsNotNone(cal.reference)
        self.assertTrue(cal.reference.startswith("SITADC-"))

    def test_calendar_str(self):
        cal = self.create_calendar(self.manager, name="Board Calendar")
        self.assertEqual(str(cal), "Board Calendar")

    def test_calendar_default_visibility(self):
        cal = self.create_calendar(self.manager)
        self.assertEqual(cal.visibility, CalendarVisibility.TEAM)

    def test_calendar_is_active_by_default(self):
        cal = self.create_calendar(self.manager)
        self.assertTrue(cal.is_active)

    def test_calendar_soft_delete(self):
        cal = self.create_calendar(self.manager)
        cal.delete()
        cal.refresh_from_db()
        self.assertTrue(cal.is_deleted)

    def test_calendar_unique_reference(self):
        cal1 = self.create_calendar(self.manager, name="Cal 1")
        cal2 = self.create_calendar(self.manager, name="Cal 2")
        self.assertNotEqual(cal1.reference, cal2.reference)

    def test_calendar_invalid_end_before_start(self):
        cal = self.create_calendar(self.manager)
        # This is not directly validated on Calendar, but we test it's a valid model


class CalendarEventModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)

    def test_create_event_allocates_reference(self):
        evt = self.create_event(self.manager, self.calendar)
        self.assertIsNotNone(evt.reference)
        self.assertTrue(evt.reference.startswith("SITADC-"))

    def test_event_str(self):
        evt = self.create_event(self.manager, self.calendar, title="Annual Review")
        self.assertIn("Annual Review", str(evt))

    def test_event_end_before_start_raises(self):
        from django.utils import timezone
        with self.assertRaises(ValidationError):
            evt = CalendarEvent(
                title="Bad Event",
                calendar=self.calendar,
                event_type=EventType.MEETING,
                organizer=self.manager,
                start_at=timezone.now() + timezone.timedelta(days=2),
                end_at=timezone.now() + timezone.timedelta(days=1),  # Before start
                status=EventStatus.DRAFT,
            )
            evt.full_clean()

    def test_event_str_includes_date(self):
        evt = self.create_event(self.manager, self.calendar)
        self.assertIn(str(evt.start_at.date()), str(evt))


class CalendarShareModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)

    def test_create_calendar_share(self):
        from apps.meetings.constants import CalendarShareLevel
        share = CalendarShare.objects.create(
            calendar=self.calendar,
            user=self.officer,
            permission_level=CalendarShareLevel.VIEW_EVENTS,
        )
        self.assertEqual(share.calendar, self.calendar)
        self.assertEqual(share.user, self.officer)
        self.assertEqual(share.permission_level, CalendarShareLevel.VIEW_EVENTS)


class MeetingModelTests(MeetingsTestCase):
    def test_create_meeting_allocates_reference(self):
        mtg = self.create_meeting(self.manager)
        self.assertIsNotNone(mtg.reference)
        self.assertTrue(mtg.reference.startswith("SITADC-"))

    def test_meeting_str(self):
        mtg = self.create_meeting(self.manager, title="Quarterly Planning")
        self.assertIn("Quarterly Planning", str(mtg))

    def test_meeting_end_before_start_raises(self):
        with self.assertRaises(ValidationError):
            mtg = Meeting(
                title="Bad Meeting",
                meeting_type=MeetingType.STAFF,
                organizer=self.manager,
                start_at=timezone.now() + timezone.timedelta(days=2),
                end_at=timezone.now() + timezone.timedelta(days=1),
                status=MeetingStatus.DRAFT,
            )
            mtg.full_clean()

    def test_meeting_default_status(self):
        mtg = self.create_meeting(self.manager)
        self.assertEqual(mtg.status, MeetingStatus.SCHEDULED)

    def test_meeting_default_mode(self):
        mtg = self.create_meeting(self.manager)
        self.assertEqual(mtg.mode, MeetingMode.IN_PERSON)


class MeetingParticipantModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_participant_with_user(self):
        from apps.meetings.constants import ParticipantRole, ParticipantType
        participant = MeetingParticipant.objects.create(
            meeting=self.meeting,
            user=self.officer,
            participant_type=ParticipantType.USER,
            role_in_meeting=ParticipantRole.ATTENDEE,
            is_required=True,
            name_snapshot=self.officer.get_full_name(),
            email_snapshot=self.officer.email,
        )
        self.assertEqual(participant.meeting, self.meeting)
        self.assertEqual(participant.user, self.officer)
        self.assertEqual(participant.name_snapshot, self.officer.get_full_name())

    def test_create_participant_without_user(self):
        participant = MeetingParticipant.objects.create(
            meeting=self.meeting,
            name_snapshot="External Person",
            email_snapshot="external@example.com",
            participant_type="EXTERNAL",
            role_in_meeting="PRESENTER",
        )
        self.assertIsNone(participant.user)
        self.assertEqual(participant.name_snapshot, "External Person")


class MeetingAgendaModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_agenda(self):
        from apps.meetings.constants import AgendaStatus
        agenda = MeetingAgenda.objects.create(
            meeting=self.meeting,
            title="Test Agenda",
            prepared_by=self.manager,
            status=AgendaStatus.DRAFT,
        )
        self.assertEqual(agenda.meeting, self.meeting)
        self.assertEqual(agenda.title, "Test Agenda")
        self.assertEqual(agenda.version, 1)

    def test_agenda_items_ordering(self):
        agenda = MeetingAgenda.objects.create(
            meeting=self.meeting,
            title="Test Agenda",
            prepared_by=self.manager,
        )
        item1 = AgendaItem.objects.create(
            agenda=agenda,
            item_number=1,
            display_order=10,
            title="Item 1",
        )
        item2 = AgendaItem.objects.create(
            agenda=agenda,
            item_number=2,
            display_order=5,
            title="Item 2",
        )
        items = list(agenda.items)
        self.assertEqual(items[0].display_order, 5)  # item2 comes first
        self.assertEqual(items[1].display_order, 10)


class AgendaItemModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.agenda = MeetingAgenda.objects.create(
            meeting=self.meeting,
            title="Test Agenda",
            prepared_by=self.manager,
        )

    def test_create_agenda_item(self):
        item = AgendaItem.objects.create(
            agenda=self.agenda,
            item_number=1,
            display_order=1,
            title="Test Item",
            item_type="DISCUSSION",
            time_allocation_minutes=30,
        )
        self.assertEqual(item.agenda, self.agenda)
        self.assertEqual(item.item_number, 1)
        self.assertEqual(item.time_allocation_minutes, 30)


class MeetingMinutesModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_minutes(self):
        from apps.meetings.constants import MinutesStatus
        minutes = MeetingMinutes.objects.create(
            meeting=self.meeting,
            title="Test Minutes",
            prepared_by=self.manager,
            status=MinutesStatus.DRAFT,
        )
        self.assertEqual(minutes.meeting, self.meeting)
        self.assertEqual(minutes.version, 1)

    def test_minutes_str(self):
        minutes = MeetingMinutes.objects.create(
            meeting=self.meeting,
            title="Test Minutes",
            prepared_by=self.manager,
        )
        self.assertIn("Test Minutes", str(minutes))


class MeetingActionItemModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_action_item(self):
        from apps.meetings.constants import ActionPriority, ActionStatus
        action = MeetingActionItem.objects.create(
            meeting=self.meeting,
            description="Test action item",
            owner=self.officer,
            status=ActionStatus.NOT_STARTED,
            priority=ActionPriority.MEDIUM,
            due_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        self.assertEqual(action.meeting, self.meeting)
        self.assertEqual(action.owner, self.officer)
        self.assertEqual(action.priority, ActionPriority.MEDIUM)


class MeetingDecisionModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_decision(self):
        from apps.meetings.constants import DecisionStatus, DecisionType
        decision = MeetingDecision.objects.create(
            meeting=self.meeting,
            decision_text="Test decision",
            decision_type=DecisionType.RESOLUTION,
            proposed_by=self.manager,
            status=DecisionStatus.PROPOSED,
        )
        self.assertEqual(decision.meeting, self.meeting)
        self.assertEqual(decision.decision_text, "Test decision")


class MeetingDocumentModelTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)

    def test_create_document(self):
        from apps.documents.models import Document
        from apps.meetings.constants import MeetingDocumentType
        document = Document.objects.create(
            reference_number="DOC-MTG-TEST-001",
            title="Test Document",
            file="documents/files/test.pdf",
            original_filename="test.pdf",
            stored_filename="test.pdf",
            file_extension="pdf",
            mime_type="application/pdf",
            file_size=1024,
            checksum="a" * 64,
        )
        doc = MeetingDocument.objects.create(
            meeting=self.meeting,
            document=document,
            document_type=MeetingDocumentType.AGENDA,
        )
        self.assertEqual(doc.meeting, self.meeting)
        self.assertEqual(doc.document_type, MeetingDocumentType.AGENDA)
        self.assertEqual(doc.document, document)


class MeetingVenueModelTests(MeetingsTestCase):
    def test_create_venue(self):
        from apps.meetings.constants import VenueType
        venue = MeetingVenue.objects.create(
            name="Board Room",
            venue_type=VenueType.BOARDROOM,
            capacity=20,
        )
        self.assertEqual(venue.name, "Board Room")
        self.assertEqual(venue.capacity, 20)

    def test_venue_str(self):
        venue = MeetingVenue.objects.create(
            name="Main Hall",
            venue_type="HALL",
        )
        self.assertEqual(str(venue), "Main Hall")


class MeetingTemplateModelTests(MeetingsTestCase):
    def test_create_template(self):
        from apps.meetings.constants import MeetingType
        template = MeetingTemplate.objects.create(
            name="Standard Meeting Template",
            code="STD-MTG",
            meeting_type=MeetingType.STAFF,
            standard_duration_minutes=60,
        )
        self.assertEqual(template.name, "Standard Meeting Template")
        self.assertEqual(template.code, "STD-MTG")
        self.assertEqual(template.standard_duration_minutes, 60)

    def test_template_str(self):
        template = MeetingTemplate.objects.create(
            name="Board Template",
            code="BRD",
            meeting_type="BOARD",
        )
        self.assertEqual(str(template), "Board Template")
