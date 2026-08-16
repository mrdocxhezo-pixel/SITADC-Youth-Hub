"""Management command to generate meeting reference numbers for records missing them."""

from django.core.management.base import BaseCommand

from apps.meetings.models import (
    Calendar,
    CalendarEvent,
    Meeting,
    MeetingActionItem,
    MeetingDecision,
    MeetingDocument,
    MeetingMinutes,
)
from apps.references.services import ReferenceNumberService


class Command(BaseCommand):
    help = "Generate reference numbers for meeting records missing them."

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            choices=[
                "all",
                "calendar",
                "event",
                "meeting",
                "minutes",
                "decision",
                "action",
            ],
            default="all",
            help="Which model to process (default: all).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be generated without actually generating.",
        )

    def handle(self, *args, **options):
        model = options["model"]
        dry_run = options["dry_run"]

        self.stdout.write("Generating reference numbers...")

        total_created = 0

        if model in ["all", "calendar"]:
            total_created += self._process_calendars(dry_run)
        if model in ["all", "event"]:
            total_created += self._process_events(dry_run)
        if model in ["all", "meeting"]:
            total_created += self._process_meetings(dry_run)
        if model in ["all", "minutes"]:
            total_created += self._process_minutes(dry_run)
        if model in ["all", "decision"]:
            total_created += self._process_decisions(dry_run)
        if model in ["all", "action"]:
            total_created += self._process_actions(dry_run)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Dry run complete. Would generate "
                    f"{total_created} reference numbers."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Generated {total_created} reference numbers.")
            )

    def _get_service(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.filter(is_active=True).first()
        if not user:
            raise ValueError("No active user found to run reference generation")
        return ReferenceNumberService(user=user)

    def _process_calendars(self, dry_run):
        created = 0
        service = self._get_service()
        for cal in Calendar.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Calendar {cal.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="calendars",
                        record_type="calendar",
                        scheme_code="calendar",
                    )
                    cal.reference = result.reference_number
                    cal.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for calendar {cal.pk}: {e}")
                    )
        return created

    def _process_events(self, dry_run):
        created = 0
        service = self._get_service()
        for evt in CalendarEvent.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Event {evt.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="events",
                        record_type="event",
                        scheme_code="event",
                    )
                    evt.reference = result.reference_number
                    evt.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for event {evt.pk}: {e}")
                    )
        return created

    def _process_meetings(self, dry_run):
        created = 0
        service = self._get_service()
        for mtg in Meeting.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Meeting {mtg.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="meetings",
                        record_type="meeting",
                        scheme_code="meeting",
                    )
                    mtg.reference = result.reference_number
                    mtg.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for meeting {mtg.pk}: {e}")
                    )
        return created

    def _process_minutes(self, dry_run):
        created = 0
        service = self._get_service()
        for minutes in MeetingMinutes.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Minutes {minutes.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="meetings",
                        record_type="minutes",
                        scheme_code="meeting",
                    )
                    minutes.reference = result.reference_number
                    minutes.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for minutes {minutes.pk}: {e}")
                    )
        return created

    def _process_decisions(self, dry_run):
        created = 0
        service = self._get_service()
        for decision in MeetingDecision.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Decision {decision.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="meetings",
                        record_type="decision",
                        scheme_code="meeting",
                    )
                    decision.reference = result.reference_number
                    decision.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for decision {decision.pk}: {e}")
                    )
        return created

    def _process_actions(self, dry_run):
        created = 0
        service = self._get_service()
        for action in MeetingActionItem.objects.filter(reference__in=["", None]):
            if dry_run:
                self.stdout.write(f"  Action {action.pk}: would generate reference")
                created += 1
            else:
                try:
                    result = service.execute(
                        module="meetings",
                        record_type="action",
                        scheme_code="meeting",
                    )
                    action.reference = result.reference_number
                    action.save(update_fields=["reference"])
                    created += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Failed for action {action.pk}: {e}")
                    )
        return created


