from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.qa.services import QualityMetricService

User = get_user_model()


class Command(BaseCommand):
    help = "Calculate quality metrics for a given period"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to calculate metrics for (default: 7)",
        )
        parser.add_argument(
            "--module",
            type=str,
            default="",
            help="Module to calculate metrics for (optional)",
        )
        parser.add_argument(
            "--user", type=str, help="Username to attribute calculations to"
        )

    def handle(self, *args, **options):
        days = options["days"]
        module = options["module"]
        username = options["user"]

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User "{username}" not found.'))
            return

        period_end = timezone.now()
        period_start = period_end - timedelta(days=days)

        self.stdout.write(
            "Calculating quality metrics for "
            f"{period_start.date()} to {period_end.date()}..."
        )

        metrics = QualityMetricService.calculate_metrics(
            user, period_start, period_end, module
        )

        self.stdout.write(
            self.style.SUCCESS(f"Calculated {len(metrics)} quality metrics:")
        )
        for metric in metrics:
            msg = (
                f"  {metric.name}: {metric.value} {metric.unit} "
                f"(target: {metric.target_value})"
            )
            self.stdout.write(msg)
