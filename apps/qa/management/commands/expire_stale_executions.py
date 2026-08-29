from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.qa.constants import TestExecutionStatus
from apps.qa.models import QANotification, TestExecution


class Command(BaseCommand):
    help = "Expire stale test executions and notify about stuck executions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--hours",
            type=int,
            default=24,
            help=(
                "Hours after which a running execution is "
                "considered stale (default: 24)"
            ),
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        hours = options["hours"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(hours=hours)

        stale_executions = TestExecution.objects.filter(
            status=TestExecutionStatus.RUNNING, started_at__lt=cutoff
        )

        count = stale_executions.count()
        if count == 0:
            self.stdout.write(self.style.SUCCESS("No stale executions found."))
            return

        self.stdout.write(f"Found {count} stale execution(s) older than {hours} hours.")

        if not dry_run:
            for execution in stale_executions:
                execution.status = TestExecutionStatus.ERROR
                execution.error_message = f"Execution timed out after {hours} hours"
                execution.completed_at = timezone.now()
                execution.duration_seconds = int(
                    (timezone.now() - execution.started_at).total_seconds()
                )
                execution.save()

                # Create notification
                QANotification.objects.create(
                    notification_type="TEST_FAILURE",
                    title=f"Stale Execution Timed Out: {execution.test_case.test_id}",
                    message=(
                        f'Test execution for "{execution.test_case.title}" '
                        f"was running for more than {hours} hours "
                        f"and has been marked as error."
                    ),
                    recipient=execution.executed_by,
                    related_object_type="TestExecution",
                    related_object_id=str(execution.pk),
                    priority="HIGH",
                )

            self.stdout.write(
                self.style.SUCCESS(f"Marked {count} execution(s) as error.")
            )
        else:
            for execution in stale_executions:
                msg = (
                    f"  Would mark as error: {execution.test_case.test_id} "
                    f"(started: {execution.started_at})"
                )
                self.stdout.write(msg)
