"""Dispatch queued notification deliveries and process expiries.

Intended to be run on a schedule (cron / task queue).  Example:

    python manage.py process_notifications --deliver --expire --dry-run
"""

from django.core.management.base import BaseCommand

from apps.notifications.constants import DeliveryStatus
from apps.notifications.models import NotificationDelivery
from apps.notifications.services import ProcessDeliveriesService, ProcessExpiredService


class Command(BaseCommand):
    help = "Dispatch queued notifications and expire stale ones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deliver",
            action="store_true",
            help="Process queued delivery attempts.",
        )
        parser.add_argument(
            "--expire",
            action="store_true",
            help="Mark expired notifications as EXPIRED.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=200,
            help="Maximum delivery attempts to process per run.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be processed without changing data.",
        )

    def handle(self, *args, **options):
        deliver = options["deliver"]
        expire = options["expire"]
        dry_run = options["dry_run"]
        limit = options["limit"]

        if not deliver and not expire:
            deliver = True
            expire = True

        if deliver:
            if dry_run:
                pending = NotificationDelivery.objects.filter(
                    status=DeliveryStatus.QUEUED
                ).count()
                self.stdout.write(
                    f"[dry-run] {pending} queued delivery attempt(s) would "
                    "be processed."
                )
            else:
                result = ProcessDeliveriesService(user=None).execute(limit=limit)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deliveries processed: {result['processed']} "
                        f"(delivered={result['delivered']}, failed={result['failed']})"
                    )
                )

        if expire:
            if dry_run:
                from apps.notifications.selectors import expired_notifications

                count = expired_notifications().count()
                self.stdout.write(
                    f"[dry-run] {count} notification(s) would be expired."
                )
            else:
                count = ProcessExpiredService(user=None).execute()
                self.stdout.write(
                    self.style.SUCCESS(f"Expired {count} notification(s).")
                )
