"""Management command to validate meeting data integrity."""

from django.core.management.base import BaseCommand
from django.db.models import Q

from apps.meetings.models import (
    Calendar,
    CalendarEvent,
    Meeting,
    MeetingActionItem,
    MeetingAgenda,
    MeetingAttendance,
    MeetingMinutes,
    MeetingParticipant,
)


class Command(BaseCommand):
    help = "Validate meeting data integrity and report issues."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Attempt to fix automatically fixable issues.",
        )
        parser.add_argument(
            "--calendar",
            type=str,
            help="Validate only a specific calendar (by reference or UUID).",
        )

    def handle(self, *args, **options):
        fix = options["fix"]
        calendar_ref = options["calendar"]

        self.stdout.write("Validating meeting data integrity...")
        issues = 0

        issues += self._validate_calendars(calendar_ref, fix)
        issues += self._validate_events(fix)
        issues += self._validate_meetings(fix)
        issues += self._validate_agendas(fix)
        issues += self._validate_minutes(fix)
        issues += self._validate_actions(fix)
        issues += self._validate_participants(fix)
        issues += self._validate_attendance(fix)

        if issues == 0:
            self.stdout.write(self.style.SUCCESS("No issues found."))
        else:
            self.stdout.write(self.style.WARNING(f"Total issues found: {issues}"))

    def _validate_calendars(self, calendar_ref, fix):
        issues = 0
        qs = Calendar.objects.all()
        if calendar_ref:
            qs = qs.filter(Q(reference=calendar_ref) | Q(pk=calendar_ref))

        for cal in qs:
            # Calendar without owner
            if not cal.owner_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Calendar {cal.reference} has no owner")
                )
            # Calendar with invalid reference format
            if not cal.reference or not cal.reference.startswith("SITADC-"):
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Calendar {cal.pk} has invalid reference: {cal.reference}"
                    )
                )
        return issues

    def _validate_events(self, fix):
        issues = 0
        for evt in CalendarEvent.objects.all():
            # Event without calendar
            if not evt.calendar_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Event {evt.reference} has no calendar")
                )
            # Event with end before start
            if evt.end_at <= evt.start_at:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Event {evt.reference} has end_at <= start_at")
                )
            # Event without organizer
            if not evt.organizer_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Event {evt.reference} has no organizer")
                )
        return issues

    def _validate_meetings(self, fix):
        issues = 0
        for mtg in Meeting.objects.all():
            # Meeting without organizer
            if not mtg.organizer_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Meeting {mtg.reference} has no organizer")
                )
            # Meeting with end before start
            if mtg.end_at <= mtg.start_at:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Meeting {mtg.reference} has end_at <= start_at"
                    )
                )
            # Meeting with invalid status transition
            from apps.meetings.constants import MeetingStatus

            valid_statuses = [s[0] for s in MeetingStatus.choices]
            if mtg.status not in valid_statuses:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Meeting {mtg.reference} has invalid status: {mtg.status}"
                    )
                )
        return issues

    def _validate_agendas(self, fix):
        issues = 0
        for agenda in MeetingAgenda.objects.all():
            # Agenda without meeting
            if not agenda.meeting_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Agenda {agenda.pk} has no meeting")
                )
            # Agenda with no items
            if not agenda.items.exists():
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        "Agenda "
                        f"{agenda.pk} for meeting "
                        f"{agenda.meeting.reference} has no items"
                    )
                )
        return issues

    def _validate_minutes(self, fix):
        issues = 0
        for minutes in MeetingMinutes.objects.all():
            # Minutes without meeting
            if not minutes.meeting_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Minutes {minutes.pk} has no meeting")
                )
            # Minutes without prepared_by
            if not minutes.prepared_by_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Minutes {minutes.pk} has no prepared_by")
                )
        return issues

    def _validate_actions(self, fix):
        issues = 0
        for action in MeetingActionItem.objects.all():
            # Action without meeting
            if not action.meeting_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Action {action.reference} has no meeting")
                )
            # Action without owner
            if not action.owner_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Action {action.reference} has no owner")
                )
            # Action past due date but not completed
            from django.utils import timezone

            if (
                action.due_date
                and action.due_date < timezone.now().date()
                and action.status not in ["COMPLETED", "CANCELLED"]
            ):
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        "Action "
                        f"{action.reference} is overdue (due: {action.due_date})"
                    )
                )
        return issues

    def _validate_participants(self, fix):
        issues = 0
        for participant in MeetingParticipant.objects.all():
            # Participant without meeting
            if not participant.meeting_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Participant {participant.pk} has no meeting")
                )
            # Participant without user and without name snapshot
            if not participant.user_id and not participant.name_snapshot:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"Participant {participant.pk} has no user and no name snapshot"
                    )
                )
        return issues

    def _validate_attendance(self, fix):
        issues = 0
        for attendance in MeetingAttendance.objects.all():
            # Attendance without meeting
            if not attendance.meeting_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Attendance {attendance.pk} has no meeting")
                )
            # Attendance without participant
            if not attendance.participant_id:
                issues += 1
                self.stdout.write(
                    self.style.WARNING(f"Attendance {attendance.pk} has no participant")
                )
        return issues
