"""Management command to generate performance reports."""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.performance.services import PerformanceReportService


class Command(BaseCommand):
    """Generate performance reports."""

    help = "Generate performance reports for a given period"

    def add_arguments(self, parser):
        parser.add_argument(
            "--period",
            type=str,
            default="daily",
            choices=["hourly", "daily", "weekly", "monthly"],
            help="Report period (default: daily)",
        )
        parser.add_argument(
            "--format",
            type=str,
            default="HTML",
            choices=["HTML", "PDF", "XLSX", "CSV"],
            help="Report format (default: HTML)",
        )
        parser.add_argument(
            "--title",
            type=str,
            default="",
            help="Report title (default: auto-generated)",
        )
        parser.add_argument(
            "--user",
            type=str,
            help="Username to run report as (default: first superuser)",
        )

    def handle(self, *args, **options):
        period = options["period"]
        format_ = options["format"]
        title = options["title"]
        username = options["user"]

        # Determine period
        now = timezone.now()
        if period == "hourly":
            period_start = now - timedelta(hours=1)
            period_name = "Hourly"
        elif period == "daily":
            period_start = now - timedelta(days=1)
            period_name = "Daily"
        elif period == "weekly":
            period_start = now - timedelta(weeks=1)
            period_name = "Weekly"
        elif period == "monthly":
            period_start = now - timedelta(days=30)
            period_name = "Monthly"
        else:
            period_start = now - timedelta(days=1)
            period_name = "Daily"

        # Get user
        if username:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"User '{username}' not found."))
                return
        else:
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(self.style.ERROR("No superuser found to run report."))
                return

        # Generate title
        if not title:
            title = (
                f"{period_name} Performance Report - {now.strftime('%Y-%m-%d %H:%M')}"
            )

        # Generate report
        try:
            service = PerformanceReportService()
            report = service.generate_report(
                actor=user,
                title=title,
                period_start=period_start,
                period_end=now,
                format=format_,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Generated report: {report.title} (ID: {report.pk})"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to generate report: {e}"))
