"""Management command to clean up soft-deleted meeting records."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.meetings.models import (
    Calendar,
    CalendarEvent,
    Meeting,
    MeetingActionItem,
    MeetingAgenda,
    MeetingAttendance,
    MeetingDecision,
    MeetingDocument,
    MeetingInvitation,
    MeetingMinutes,
    MeetingParticipant,
    MeetingTemplate,
    MeetingVenue,
)


class Command(BaseCommand):
    help = "Permanently delete soft-deleted meeting records older than specified days."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=90,
            help="Delete records soft-deleted more than this many days ago "
            "(default: 90).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting.",
        )
        parser.add_argument(
            "--model",
            choices=[
                "all",
                "calendar",
                "event",
                "meeting",
                "agenda",
                "minutes",
                "decision",
                "action",
                "document",
                "participant",
                "invitation",
                "attendance",
                "venue",
                "template",
            ],
            default="all",
            help="Which model to process (default: all).",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        model = options["model"]

        cutoff = timezone.now() - timezone.timedelta(days=days)

        self.stdout.write(f"Cleaning up soft-deleted records older than {days} days...")

        total_deleted = 0

        if model in ["all", "calendar"]:
            total_deleted += self._cleanup(Calendar, cutoff, dry_run, "calendar")
        if model in ["all", "event"]:
            total_deleted += self._cleanup(CalendarEvent, cutoff, dry_run, "event")
        if model in ["all", "meeting"]:
            total_deleted += self._cleanup(Meeting, cutoff, dry_run, "meeting")
        if model in ["all", "agenda"]:
            total_deleted += self._cleanup(MeetingAgenda, cutoff, dry_run, "agenda")
        if model in ["all", "minutes"]:
            total_deleted += self._cleanup(MeetingMinutes, cutoff, dry_run, "minutes")
        if model in ["all", "decision"]:
            total_deleted += self._cleanup(MeetingDecision, cutoff, dry_run, "decision")
        if model in ["all", "action"]:
            total_deleted += self._cleanup(MeetingActionItem, cutoff, dry_run, "action")
        if model in ["all", "document"]:
            total_deleted += self._cleanup(MeetingDocument, cutoff, dry_run, "document")
        if model in ["all", "participant"]:
            total_deleted += self._cleanup(
                MeetingParticipant, cutoff, dry_run, "participant"
            )
        if model in ["all", "invitation"]:
            total_deleted += self._cleanup(
                MeetingInvitation, cutoff, dry_run, "invitation"
            )
        if model in ["all", "attendance"]:
            total_deleted += self._cleanup(
                MeetingAttendance, cutoff, dry_run, "attendance"
            )
        if model in ["all", "venue"]:
            total_deleted += self._cleanup(MeetingVenue, cutoff, dry_run, "venue")
        if model in ["all", "template"]:
            total_deleted += self._cleanup(MeetingTemplate, cutoff, dry_run, "template")

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "Dry run complete. Would permanently delete "
                    f"{total_deleted} records."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Permanently deleted {total_deleted} records.")
            )

    def _cleanup(self, model_class, cutoff, dry_run, name):
        if not hasattr(model_class, "all_objects") or not hasattr(
            model_class, "hard_delete"
        ):
            self.stdout.write(
                self.style.WARNING(
                    f"  {name}: model does not support hard delete, skipping"
                )
            )
            return 0

        qs = model_class.all_objects.filter(is_deleted=True, deleted_at__lt=cutoff)
        count = qs.count()

        if count == 0:
            return 0

        if dry_run:
            self.stdout.write(f"  {name}: would delete {count} records")
            return count

        for obj in qs:
            obj.hard_delete()

        self.stdout.write(f"  {name}: deleted {count} records")
        return count
