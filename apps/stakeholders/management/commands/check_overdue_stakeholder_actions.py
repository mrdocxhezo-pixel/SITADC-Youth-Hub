"""Report overdue actions and optionally apply the overdue status via services."""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.stakeholders.constants import ActionStatus
from apps.stakeholders.models import StakeholderActionItem
from apps.stakeholders.services import StakeholderActionService


class Command(BaseCommand):
    help = "Check open stakeholder action items whose due date has passed."

    def add_arguments(self, parser):
        parser.add_argument("--mark-overdue", action="store_true")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report only, even when --mark-overdue is supplied.",
        )
        parser.add_argument("--actor-email")

    def handle(self, *args, **options):
        overdue = StakeholderActionItem.objects.filter(
            due_date__lt=timezone.localdate(),
            status__in=[
                ActionStatus.OPEN,
                ActionStatus.IN_PROGRESS,
                ActionStatus.BLOCKED,
            ],
        ).select_related("stakeholder")
        self.stdout.write(f"Overdue stakeholder actions: {overdue.count()}")
        if not options["mark_overdue"] or options["dry_run"]:
            return
        actor_email = options.get("actor_email")
        if not actor_email:
            raise CommandError("--actor-email is required with --mark-overdue.")
        try:
            actor = get_user_model().objects.get(
                email__iexact=actor_email, is_active=True
            )
        except get_user_model().DoesNotExist as exc:
            raise CommandError("Active actor account was not found.") from exc
        updated = 0
        for action in overdue:
            StakeholderActionService(user=actor).change_status(
                action,
                ActionStatus.OVERDUE,
                "Automatically marked overdue after the due date elapsed.",
            )
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Marked {updated} actions overdue."))
