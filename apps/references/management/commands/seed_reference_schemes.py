"""
Idempotently seed the default reference number schemes.

Run with::

    python manage.py seed_reference_schemes

The command is safe to run repeatedly; existing schemes are updated in place
(identity by ``(module, record_type, prefix)``) and missing schemes are
created.  Seeded schemes are created active.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.references.constants import SchemeStatus
from apps.references.models import ReferenceNumberScheme
from apps.references.seed_data import DEFAULT_SCHEMES


class Command(BaseCommand):
    help = "Seed the default reference number schemes."

    @transaction.atomic
    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))

        created = 0
        for seed in DEFAULT_SCHEMES:
            _, was_created = ReferenceNumberScheme.objects.update_or_create(
                module=seed.module,
                record_type=seed.record_type,
                prefix=seed.prefix,
                defaults={
                    "name": seed.name,
                    "code": seed.code,
                    "description": seed.description,
                    "organization_code": seed.organization_code,
                    "pattern": seed.pattern,
                    "sequence_length": seed.sequence_length,
                    "reset_period": seed.reset_period,
                    "is_default_for_module": seed.is_default_for_module,
                    "is_default_for_record_type": seed.is_default_for_record_type,
                    "is_fallback": seed.is_fallback,
                    "status": SchemeStatus.ACTIVE,
                    "is_active": True,
                },
            )
            if was_created:
                created += 1

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Reference number schemes ready: {created} created, "
                    f"{len(DEFAULT_SCHEMES) - created} already present."
                )
            )
