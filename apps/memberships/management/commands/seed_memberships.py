"""
Idempotently seed the default membership configuration data.

Run with::

    python manage.py seed_memberships

The command is safe to run repeatedly; existing configuration rows are
updated in place (identity by ``code``) and missing rows are created.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.memberships.seed_loader import seed_membership_configuration


class Command(BaseCommand):
    help = "Seed the default membership configuration data."

    @transaction.atomic
    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))
        stats = seed_membership_configuration()
        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    "Membership configuration ready: "
                    f"{stats['statuses']} statuses, {stats['categories']} categories, "
                    f"{stats['types']} types, {stats['levels']} levels, "
                    f"{stats['benefits']} benefits."
                )
            )
