"""Management command to compute export analytics."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.exports.services import (
    ExportAnalyticsService,
    ExportTemplateAnalyticsService,
    ExportUserAnalyticsService,
)


class Command(BaseCommand):
    """Compute export analytics for dashboard and reporting."""

    help = "Compute export analytics snapshots for daily, weekly, monthly periods."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days back to compute daily analytics (default: 30)",
        )
        parser.add_argument(
            "--weeks",
            type=int,
            default=12,
            help="Number of weeks back to compute weekly analytics (default: 12)",
        )
        parser.add_argument(
            "--months",
            type=int,
            default=12,
            help="Number of months back to compute monthly analytics (default: 12)",
        )
        parser.add_argument(
            "--templates-only",
            action="store_true",
            help="Only compute template analytics",
        )
        parser.add_argument(
            "--users-only",
            action="store_true",
            help="Only compute user analytics",
        )

    def handle(self, *args, **options):
        days = options["days"]
        weeks = options["weeks"]
        months = options["months"]
        templates_only = options["templates_only"]
        users_only = options["users_only"]

        now = timezone.now()

        if not templates_only and not users_only:
            self.stdout.write("Computing general export analytics...")
            service = ExportAnalyticsService()

            # Daily
            self.stdout.write(f"  Computing daily analytics for last {days} days...")
            for i in range(days):
                period_start = (now - timedelta(days=i)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                period_end = period_start + timedelta(days=1)
                service.execute(
                    period="DAILY", period_start=period_start, period_end=period_end
                )

            # Weekly
            self.stdout.write(f"  Computing weekly analytics for last {weeks} weeks...")
            for i in range(weeks):
                period_start = (
                    now - timedelta(weeks=i + 1)
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                period_start = period_start - timedelta(days=period_start.weekday())
                period_end = period_start + timedelta(weeks=1)
                service.execute(
                    period="WEEKLY", period_start=period_start, period_end=period_end
                )

            # Monthly
            self.stdout.write(f"  Computing monthly analytics for last {months} months...")
            for i in range(months):
                month = (now.month - i - 1) % 12 + 1
                year = now.year - ((now.month - i - 1) // 12)
                period_start = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
                next_month = month % 12 + 1
                next_year = year + (month == 12)
                period_end = timezone.datetime(next_year, next_month, 1, tzinfo=timezone.utc)
                service.execute(
                    period="MONTHLY", period_start=period_start, period_end=period_end
                )

            self.stdout.write(self.style.SUCCESS("General analytics computed."))

        if not users_only:
            self.stdout.write("Computing template analytics...")
            tmpl_service = ExportTemplateAnalyticsService()

            # Daily
            for i in range(days):
                period_start = (now - timedelta(days=i)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                period_end = period_start + timedelta(days=1)
                tmpl_service.compute(
                    period="DAILY", period_start=period_start, period_end=period_end
                )

            # Weekly
            for i in range(weeks):
                period_start = (
                    now - timedelta(weeks=i + 1)
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                period_start = period_start - timedelta(days=period_start.weekday())
                period_end = period_start + timedelta(weeks=1)
                tmpl_service.compute(
                    period="WEEKLY", period_start=period_start, period_end=period_end
                )

            # Monthly
            for i in range(months):
                month = (now.month - i - 1) % 12 + 1
                year = now.year - ((now.month - i - 1) // 12)
                period_start = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
                next_month = month % 12 + 1
                next_year = year + (month == 12)
                period_end = timezone.datetime(next_year, next_month, 1, tzinfo=timezone.utc)
                tmpl_service.compute(
                    period="MONTHLY", period_start=period_start, period_end=period_end
                )

            self.stdout.write(self.style.SUCCESS("Template analytics computed."))

        if not templates_only:
            self.stdout.write("Computing user analytics...")
            user_service = ExportUserAnalyticsService()

            # Daily
            for i in range(days):
                period_start = (now - timedelta(days=i)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                period_end = period_start + timedelta(days=1)
                user_service.compute(
                    period="DAILY", period_start=period_start, period_end=period_end
                )

            # Weekly
            for i in range(weeks):
                period_start = (
                    now - timedelta(weeks=i + 1)
                ).replace(hour=0, minute=0, second=0, microsecond=0)
                period_start = period_start - timedelta(days=period_start.weekday())
                period_end = period_start + timedelta(weeks=1)
                user_service.compute(
                    period="WEEKLY", period_start=period_start, period_end=period_end
                )

            # Monthly
            for i in range(months):
                month = (now.month - i - 1) % 12 + 1
                year = now.year - ((now.month - i - 1) // 12)
                period_start = timezone.datetime(year, month, 1, tzinfo=timezone.utc)
                next_month = month % 12 + 1
                next_year = year + (month == 12)
                period_end = timezone.datetime(next_year, next_month, 1, tzinfo=timezone.utc)
                user_service.compute(
                    period="MONTHLY", period_start=period_start, period_end=period_end
                )

            self.stdout.write(self.style.SUCCESS("User analytics computed."))

        self.stdout.write(self.style.SUCCESS("All analytics computation complete."))
