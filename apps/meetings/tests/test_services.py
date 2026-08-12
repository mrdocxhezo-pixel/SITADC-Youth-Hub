"""Service-level tests for the Calendar & Meetings app."""

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.meetings.constants import (
    ActionPriority,
    ActionStatus,
    AgendaStatus,
    CalendarType,
    CalendarVisibility,
    DecisionType,
    EventType,
    MeetingStatus,
    MeetingType,
    MinutesStatus,
    ParticipantStatus,
    ParticipantType,
    VenueType,
)
from apps.meetings.services import (
    ActionItemService,
    AgendaService,
    CalendarEventService,
    CalendarService,
    DecisionService,
    MeetingService,
    MinutesService,
    ParticipantService,
    TemplateService,
    VenueService,
)
from apps.meetings.tests.base import MeetingsTestCase


class CalendarServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.service = CalendarService(user=self.manager)

    def test_create_calendar(self):
        cal = self.service.create(
            name="Service Calendar",
            calendar_type=CalendarType.TEAM,
            visibility=CalendarVisibility.TEAM,
            owner=self.manager,
        )
        self.assertIsNotNone(cal.reference)
        self.assertEqual(cal.name, "Service Calendar")
        self.assertEqual(cal.owner, self.manager)

    def test_update_calendar(self):
        cal = self.service.create(
            name="Original",
            calendar_type=CalendarType.TEAM,
            owner=self.manager,
        )
        updated = self.service.update(cal, name="Updated")
        self.assertEqual(updated.name, "Updated")

    def test_soft_delete_calendar(self):
        cal = self.service.create(
            name="To Delete",
            calendar_type=CalendarType.TEAM,
            owner=self.manager,
        )
        self.service.soft_delete(cal, notes="test delete")
        cal.refresh_from_db()
        self.assertTrue(cal.is_deleted)

    def test_archive_calendar(self):
        cal = self.service.create(
            name="To Archive",
            calendar_type=CalendarType.TEAM,
            owner=self.manager,
        )
        self.service.archive(cal, notes="test archive")
        cal.refresh_from_db()
        self.assertTrue(cal.is_archived)

    def test_create_calendar_without_owner_uses_user(self):
        cal = self.service.create(
            name="No Owner",
            calendar_type=CalendarType.TEAM,
        )
        self.assertEqual(cal.owner, self.manager)


class CalendarEventServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.calendar = self.create_calendar(self.manager)
        self.service = CalendarEventService(user=self.manager)

    def test_create_event(self):
        evt = self.service.create(
            calendar=self.calendar,
            title="Service Event",
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            organizer=self.manager,
        )
        self.assertIsNotNone(evt.reference)
        self.assertEqual(evt.title, "Service Event")
        self.assertEqual(evt.calendar, self.calendar)

    def test_update_event(self):
        evt = self.service.create(
            calendar=self.calendar,
            title="Original",
            event_type=EventType.MEETING,
            start_at=timezone.now() + timezone.timedelta(days=1),
            end_at=timezone.now() + timezone.timedelta(days=1, hours=1),
            organizer=self.manager,
        )
        updated = self.service.update(evt, title="Updated")
        self.assertEqual(updated.title, "Updated")

    def test_event_end_before_start_raises(self):
        with self.assertRaises(ValidationError):
            self.service.create(
                calendar=self.calendar,
                title="Bad Event",
                event_type=EventType.MEETING,
                start_at=timezone.now() + timezone.timedelta(days=2),
                end_at=timezone.now() + timezone.timedelta(days=1),
                organizer=self.manager,
            )


class MeetingServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.service = MeetingService(user=self.manager)

    def test_create_meeting(self):
        mtg = self.service.create(
            title="Service Meeting",
            meeting_type=MeetingType.STAFF,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            organizer=self.manager,
        )
        self.assertIsNotNone(mtg.reference)
        self.assertEqual(mtg.title, "Service Meeting")

    def test_update_meeting(self):
        mtg = self.service.create(
            title="Original",
            meeting_type=MeetingType.STAFF,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            organizer=self.manager,
        )
        updated = self.service.update(mtg, title="Updated")
        self.assertEqual(updated.title, "Updated")

    def test_meeting_status_transitions(self):
        mtg = self.service.create(
            title="Draft Meeting",
            meeting_type=MeetingType.STAFF,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            organizer=self.manager,
        )
        self.assertEqual(mtg.status, MeetingStatus.DRAFT)

        # Confirm
        confirmed = self.service.confirm(mtg)
        self.assertEqual(confirmed.status, MeetingStatus.CONFIRMED)

        # Complete
        completed = self.service.complete(mtg)
        self.assertEqual(completed.status, MeetingStatus.COMPLETED)

    def test_cancel_meeting(self):
        mtg = self.service.create(
            title="To Cancel",
            meeting_type=MeetingType.STAFF,
            start_at=timezone.now() + timezone.timedelta(days=2),
            end_at=timezone.now() + timezone.timedelta(days=2, hours=1),
            organizer=self.manager,
        )
        cancelled = self.service.cancel(mtg, reason="No longer needed")
        self.assertEqual(cancelled.status, MeetingStatus.CANCELLED)


class ParticipantServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.service = ParticipantService(user=self.manager)

    def test_add_participant_user(self):
        participant = self.service.add_participant(
            meeting=self.meeting,
            user=self.officer,
            participant_type=ParticipantType.INTERNAL,
            role_in_meeting="ATTENDEE",
            is_required=True,
        )
        self.assertEqual(participant.meeting, self.meeting)
        self.assertEqual(participant.user, self.officer)
        self.assertEqual(participant.participant_type, ParticipantType.INTERNAL)
        self.assertTrue(participant.is_required)

    def test_add_participant_external(self):
        participant = self.service.add_participant(
            meeting=self.meeting,
            name="External Person",
            email="external@example.com",
            participant_type=ParticipantType.EXTERNAL,
            role_in_meeting="PRESENTER",
        )
        self.assertIsNone(participant.user)
        self.assertEqual(participant.name_snapshot, "External Person")
        self.assertEqual(participant.email_snapshot, "external@example.com")

    def test_update_participant_status(self):
        participant = self.service.add_participant(
            meeting=self.meeting,
            user=self.officer,
            participant_type=ParticipantType.INTERNAL,
        )
        updated = self.service.update_status(
            participant,
            participant_status=ParticipantStatus.CONFIRMED,
            rsvp_status="ACCEPTED",
        )
        self.assertEqual(updated.participant_status, ParticipantStatus.CONFIRMED)


class AgendaServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.service = AgendaService(user=self.manager)

    def test_create_agenda(self):
        agenda = self.service.create(
            meeting=self.meeting,
            title="Service Agenda",
            prepared_by=self.manager,
        )
        self.assertEqual(agenda.meeting, self.meeting)
        self.assertEqual(agenda.title, "Service Agenda")
        self.assertEqual(agenda.version, 1)

    def test_add_agenda_item(self):
        agenda = self.service.create(
            meeting=self.meeting,
            title="Test Agenda",
            prepared_by=self.manager,
        )
        item = self.service.add_item(
            agenda=agenda,
            item_number=1,
            title="First Item",
            item_type="DISCUSSION",
            time_allocation_minutes=30,
        )
        self.assertEqual(item.agenda, agenda)
        self.assertEqual(item.item_number, 1)

    def test_approve_agenda(self):
        agenda = self.service.create(
            meeting=self.meeting,
            title="Test Agenda",
            prepared_by=self.manager,
        )
        approved = self.service.approve(agenda, approved_by=self.manager)
        self.assertEqual(approved.status, AgendaStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.manager)


class MinutesServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.service = MinutesService(user=self.manager)

    def test_create_minutes(self):
        minutes = self.service.create(
            meeting=self.meeting,
            title="Service Minutes",
            prepared_by=self.manager,
        )
        self.assertEqual(minutes.meeting, self.meeting)
        self.assertEqual(minutes.title, "Service Minutes")
        self.assertEqual(minutes.version, 1)

    def test_submit_minutes(self):
        minutes = self.service.create(
            meeting=self.meeting,
            title="Draft Minutes",
            prepared_by=self.manager,
        )
        submitted = self.service.submit(minutes)
        self.assertEqual(submitted.status, MinutesStatus.SUBMITTED)


class DecisionServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.service = DecisionService(user=self.manager)

    def test_create_decision(self):
        decision = self.service.create(
            meeting=self.meeting,
            decision_text="Service Decision",
            decision_type=DecisionType.RESOLUTION,
            proposed_by=self.manager,
        )
        self.assertEqual(decision.meeting, self.meeting)
        self.assertEqual(decision.decision_text, "Service Decision")

    def test_record_vote(self):
        decision = self.service.create(
            meeting=self.meeting,
            decision_text="Vote Test",
            decision_type=DecisionType.RESOLUTION,
            proposed_by=self.manager,
        )
        self.service.record_vote(
            decision=decision,
            participant=self.officer,
            vote_type="FOR",
        )
        self.assertEqual(decision.votes_for, 1)


class ActionItemServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.meeting = self.create_meeting(self.manager)
        self.service = ActionItemService(user=self.manager)

    def test_create_action(self):
        action = self.service.create(
            meeting=self.meeting,
            description="Service Action",
            owner=self.officer,
            priority=ActionPriority.HIGH,
            due_date=timezone.now().date() + timezone.timedelta(days=7),
        )
        self.assertEqual(action.meeting, self.meeting)
        self.assertEqual(action.owner, self.officer)
        self.assertEqual(action.priority, ActionPriority.HIGH)

    def test_update_progress(self):
        action = self.service.create(
            meeting=self.meeting,
            description="Progress Test",
            owner=self.officer,
        )
        updated = self.service.update_progress(action, progress_percentage=50)
        self.assertEqual(updated.progress_percentage, 50)

    def test_complete_action(self):
        action = self.service.create(
            meeting=self.meeting,
            description="Complete Test",
            owner=self.officer,
        )
        completed = self.service.complete(action, evidence="Done")
        self.assertEqual(completed.status, ActionStatus.COMPLETED)
        self.assertIsNotNone(completed.completion_date)


class VenueServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.service = VenueService(user=self.manager)

    def test_create_venue(self):
        venue = self.service.create(
            name="Service Venue",
            venue_type=VenueType.BOARDROOM,
            capacity=15,
        )
        self.assertEqual(venue.name, "Service Venue")
        self.assertEqual(venue.capacity, 15)

    def test_update_venue(self):
        venue = self.service.create(
            name="Original",
            venue_type=VenueType.BOARDROOM,
        )
        updated = self.service.update(venue, capacity=25)
        self.assertEqual(updated.capacity, 25)

    def test_archive_venue(self):
        venue = self.service.create(
            name="To Archive",
            venue_type=VenueType.HALL,
        )
        archived = self.service.archive(venue)
        self.assertTrue(archived.is_archived)


class TemplateServiceTests(MeetingsTestCase):
    def setUp(self):
        super().setUp()
        self.service = TemplateService(user=self.manager)

    def test_create_template(self):
        template = self.service.create(
            name="Service Template",
            code="SVC",
            meeting_type=MeetingType.STAFF,
            standard_duration_minutes=90,
        )
        self.assertEqual(template.name, "Service Template")
        self.assertEqual(template.code, "SVC")
        self.assertEqual(template.standard_duration_minutes, 90)

    def test_update_template(self):
        template = self.service.create(
            name="Original",
            code="ORG",
            meeting_type=MeetingType.STAFF,
        )
        updated = self.service.update(template, standard_duration_minutes=120)
        self.assertEqual(updated.standard_duration_minutes, 120)

    def test_activate_deactivate_template(self):
        template = self.service.create(
            name="Active Template",
            code="ACT",
            meeting_type=MeetingType.STAFF,
        )
        self.assertTrue(template.is_active)
        deactivated = self.service.deactivate(template)
        self.assertFalse(deactivated.is_active)
        activated = self.service.activate(deactivated)
        self.assertTrue(activated.is_active)
