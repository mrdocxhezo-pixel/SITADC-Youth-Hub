"""Management command to expire stale exports."""

from django.core.management.base import BaseCommand

from apps.exports.services import ExpireStaleExportsService


class Command(BaseCommand):
    """Mark completed exports past their download expiry as expired."""

    help = "Expire completed exports that have passed their download expiry window."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit",
            type=int,
            default=500,
            help="Maximum number of exports to expire per run (default: 500)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be expired without actually expiring",
        )

    def handle(self, *args, **options):
        limit = options["limit"]
        dry_run = options["dry_run"]

        if dry_run:
            from django.utils import timezone

            from apps.exports.models import ExportRequest, ExportStatus

            now = timezone.now()
            stale = ExportRequest.objects.filter(
                status=ExportStatus.COMPLETED,
                expires_at__isnull=False,
                expires_at__lte=now,
            )[:limit]

            self.stdout.write(f"Would expire {stale.count()} exports:")
            for req in stale:
                self.stdout.write(
                    f"  - {req.reference_number} (expired {req.expires_at})"
                )
            return

        self.stdout.write(f"Expiring stale exports (limit={limit})...")
        expired = ExpireStaleExportsService(user=None).execute(limit=limit)

        self.stdout.write(self.style.SUCCESS(f"Expired {expired} export(s)"))
