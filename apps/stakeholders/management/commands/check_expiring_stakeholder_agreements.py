"""Report expiring agreements and optionally expire elapsed active records."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.stakeholders.constants import AgreementStatus
from apps.stakeholders.models import StakeholderAgreement
from apps.stakeholders.services import StakeholderAgreementService


class Command(BaseCommand):
    help = "Check active stakeholder agreements approaching or past expiry."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=60)
        parser.add_argument("--mark-expired", action="store_true")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report only, even when --mark-expired is supplied.",
        )
        parser.add_argument("--actor-email")

    def handle(self, *args, **options):
        days = options["days"]
        if days < 0:
            raise CommandError("--days must be zero or greater.")
        today = timezone.localdate()
        active = StakeholderAgreement.objects.filter(
            status=AgreementStatus.ACTIVE, expiry_date__isnull=False
        ).select_related("stakeholder")
        expired = active.filter(expiry_date__lt=today)
        expiring = active.filter(
            expiry_date__gte=today,
            expiry_date__lte=today + timedelta(days=days),
        )
        self.stdout.write(f"Expired active agreements: {expired.count()}")
        self.stdout.write(f"Expiring within {days} days: {expiring.count()}")
        if not options["mark_expired"] or options["dry_run"]:
            return
        actor_email = options.get("actor_email")
        if not actor_email:
            raise CommandError("--actor-email is required with --mark-expired.")
        try:
            actor = get_user_model().objects.get(
                email__iexact=actor_email, is_active=True
            )
        except get_user_model().DoesNotExist as exc:
            raise CommandError("Active actor account was not found.") from exc
        updated = 0
        for agreement in expired:
            StakeholderAgreementService(user=actor).expire(agreement)
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Marked {updated} agreements expired."))
