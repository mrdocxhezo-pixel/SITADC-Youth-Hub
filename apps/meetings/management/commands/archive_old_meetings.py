"""Management command to archive old completed meetings."""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.meetings.models import CalendarEvent, Meeting


class Command(BaseCommand):
    help = "Archive old completed meetings and events."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="Archive meetings older than this many days (default: 365).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without actually archiving.",
        )
        parser.add_argument(
            "--include-cancelled",
            action="store_true",
            help="Also archive cancelled meetings.",
        )

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]
        include_cancelled = options["include_cancelled"]

        cutoff = timezone.now() - timezone.timedelta(days=days)

        self.stdout.write(f"Archiving meetings older than {days} days...")

        statuses = ["COMPLETED", "CLOSED"]
        if include_cancelled:
            statuses.append("CANCELLED")

        meetings_qs = Meeting.objects.filter(
            status__in=statuses,
            end_at__lt=cutoff,
            is_archived=False,
        )

        events_qs = CalendarEvent.objects.filter(
            status__in=["COMPLETED", "CANCELLED"],
            end_at__lt=cutoff,
            is_archived=False,
        )

        meeting_count = meetings_qs.count()
        event_count = events_qs.count()

        if dry_run:
            self.stdout.write(
                "Dry run: Would archive "
                f"{meeting_count} meetings and {event_count} events."
            )
            for mtg in meetings_qs[:10]:
                self.stdout.write(
                    f"  Meeting {mtg.pk}: {mtg.reference} - {mtg.title} "
                    f"(ended {mtg.end_at})"
                )
            for evt in events_qs[:10]:
                self.stdout.write(
                    f"  Event {evt.pk}: {evt.reference} - {evt.title} "
                    f"(ended {evt.end_at})"
                )
            return

        with transaction.atomic():
            for mtg in meetings_qs:
                mtg.is_archived = True
                mtg.archived_at = timezone.now()
                mtg.save(update_fields=["is_archived", "archived_at"])

            for evt in events_qs:
                evt.is_archived = True
                evt.archived_at = timezone.now()
                evt.save(update_fields=["is_archived", "archived_at"])

        self.stdout.write(
            self.style.SUCCESS(
                "Archived " f"{meeting_count} meetings and {event_count} events."
            )
        )
