"""Management command to run scheduled exports."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.exports.models import ScheduledExport, ScheduledExportFrequency
from apps.exports.services import (
    ExportNotificationService,
    QueueExportService,
    RequestExportService,
)


class Command(BaseCommand):
    """Run due scheduled exports."""

    help = "Execute scheduled exports that are due to run."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would run without actually running",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        due = ScheduledExport.objects.filter(
            is_active=True,
            next_run_at__lte=now,
        )

        if not due.exists():
            self.stdout.write("No scheduled exports due to run.")
            return

        self.stdout.write(f"Found {due.count()} scheduled export(s) due to run:")
        for scheduled in due:
            freq = scheduled.get_frequency_display()
            self.stdout.write(f"  - {scheduled.name} ({freq})")

        if dry_run:
            return

        for scheduled in due:
            try:
                # Create the export request
                request = RequestExportService(user=scheduled.created_by).execute(
                    source_type=scheduled.source_type,
                    format=scheduled.format,
                    filters=scheduled.filters,
                    selected_columns=scheduled.selected_columns,
                    requested_by=scheduled.created_by,
                    request_obj=None,
                )

                # Queue it for processing
                QueueExportService(user=scheduled.created_by).execute(
                    request, request_obj=None
                )

                # Update next run time
                self._update_next_run(scheduled, now)
                scheduled.last_run_at = now
                fields = ["last_run_at", "next_run_at", "updated_at"]
                scheduled.save(update_fields=fields)

                # Send notification
                if scheduled.notify_on_completion:
                    ExportNotificationService.notify_scheduled_run(scheduled, request)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Queued: {request.reference_number} for {scheduled.name}"
                    )
                )
            except Exception as exc:
                self.stdout.write(
                    self.style.ERROR(f"  Failed to queue {scheduled.name}: {exc}")
                )
                if scheduled.notify_on_failure:
                    msg = f'Scheduled export "{scheduled.name}" failed to queue: {exc}'
                    ExportNotificationService._send_notification(
                        user=scheduled.created_by,
                        event_type="export.scheduled_failed",
                        title="Scheduled Export Failed",
                        message=msg,
                        scheduled_export=scheduled,
                        priority="high",
                    )
                # Still update next run time so it doesn't keep retrying the same slot
                self._update_next_run(scheduled, now)
                scheduled.save(update_fields=["next_run_at", "updated_at"])

    def _update_next_run(self, scheduled: ScheduledExport, base_time) -> None:
        """Calculate and set the next run time based on frequency."""
        from datetime import timedelta

        if scheduled.frequency == ScheduledExportFrequency.DAILY:
            next_run = base_time + timedelta(days=1)
        elif scheduled.frequency == ScheduledExportFrequency.WEEKLY:
            next_run = base_time + timedelta(weeks=1)
        elif scheduled.frequency == ScheduledExportFrequency.MONTHLY:
            # Approximate month
            next_run = base_time + timedelta(days=30)
        elif scheduled.frequency == ScheduledExportFrequency.QUARTERLY:
            next_run = base_time + timedelta(days=90)
        elif scheduled.frequency == ScheduledExportFrequency.ANNUALLY:
            next_run = base_time + timedelta(days=365)
        else:
            # Custom/cron - would need a cron parser; for now skip
            next_run = None

        if next_run:
            # Set the time component
            next_run = next_run.replace(
                hour=scheduled.run_at_time.hour,
                minute=scheduled.run_at_time.minute,
                second=0,
                microsecond=0,
            )
            scheduled.next_run_at = next_run
