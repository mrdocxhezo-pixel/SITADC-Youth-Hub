"""Management command to process the export queue."""

from django.core.management.base import BaseCommand

from apps.exports.services import ProcessExportQueueService


class Command(BaseCommand):
    """Process pending export queue entries."""

    help = "Process pending export queue entries for batch/async generation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum number of queue entries to process (default: 50)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be processed without actually processing",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]

        if dry_run:
            from django.db import models
            from django.utils import timezone

            from apps.exports.models import ExportQueue, ExportQueueStatus

            now = timezone.now()
            pending = (
                ExportQueue.objects.filter(
                    status__in=[
                        ExportQueueStatus.PENDING,
                        ExportQueueStatus.PROCESSING,
                    ],
                    attempts__lt=models.F("max_attempts"),
                )
                .filter(
                    models.Q(scheduled_for__isnull=True)
                    | models.Q(scheduled_for__lte=now)
                )
                .order_by("-priority", "scheduled_for", "created_at")[:limit]
            )

            self.stdout.write(f"Would process {pending.count()} queue entries:")
            for entry in pending:
                self.stdout.write(
                    f"  - {entry.export_request.reference_number} "
                    f"({entry.get_status_display()}, priority={entry.priority}, "
                    f"attempts={entry.attempts}/{entry.max_attempts})"
                )
            return

        self.stdout.write(f"Processing export queue (limit={limit})...")
        result = ProcessExportQueueService(user=None).execute(limit=limit)

        self.stdout.write(
            self.style.SUCCESS(
                f"Processed: {result['processed']}, "
                f"Succeeded: {result['succeeded']}, "
                f"Failed: {result['failed']}"
            )
        )
        if result["failed"] > 0:
            msg = f"{result['failed']} exports failed; check logs for details"
            self.stdout.write(self.style.WARNING(msg))
