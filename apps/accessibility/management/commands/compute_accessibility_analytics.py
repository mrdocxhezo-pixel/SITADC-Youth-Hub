"""Management command to compute accessibility analytics."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Compute accessibility analytics snapshots for all modules."

    def add_arguments(self, parser):
        parser.add_argument(
            '--module',
            type=str,
            help='Compute analytics for a specific module only',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Number of days back to compute historical analytics',
        )

    def handle(self, *args, **options):
        module = options.get('module')
        days_back = options.get('days_back')

        self.stdout.write(
            self.style.NOTICE(
                f"Computing accessibility analytics"
                f"{f' for module: {module}' if module else ''}"
            )
        )

        # If days_back is specified, compute historical snapshots
        if days_back:
            from datetime import timedelta

            from apps.accessibility.models import AccessibilityAnalytics
            from apps.accessibility.services import AccessibilityAnalyticsService

            today = timezone.localdate()
            for i in range(days_back):
                snapshot_date = today - timedelta(days=i)
                # Skip if already exists
                if AccessibilityAnalytics.objects.filter(
                    snapshot_date=snapshot_date,
                    module=module or ''
                ).exists():
                    continue

                try:
                    AccessibilityAnalyticsService().generate_snapshot(module=module or '')
                    self.stdout.write(f"  Generated snapshot for {snapshot_date}")
                except Exception as e:
                    self.stderr.write(f"  Error generating snapshot for {snapshot_date}: {e}")
        else:
            # Just generate current snapshot
            try:
                snapshot = AccessibilityAnalyticsService().generate_snapshot(module=module or '')
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Generated analytics snapshot: {snapshot.snapshot_date} "
                        f"({snapshot.module or 'Global'}) - Score: {snapshot.overall_compliance_score}%"
                    )
                )
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error generating analytics: {e}"))

        self.stdout.write(self.style.SUCCESS("Done."))
