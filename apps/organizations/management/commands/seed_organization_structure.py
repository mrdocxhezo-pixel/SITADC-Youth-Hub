"""
Idempotently seed the organizational catalogues: levels and classifications.

Run with::

    python manage.py seed_organization_structure

The command is safe to run repeatedly; existing records are updated in place
and missing records are created.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.organizations.models import OrganizationLevel, PositionClassification
from apps.organizations.seed_data import DEFAULT_CLASSIFICATIONS, DEFAULT_LEVELS


class Command(BaseCommand):
    help = "Seed organizational levels and position classifications."

    @transaction.atomic
    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))

        created_levels = 0
        for level_seed in DEFAULT_LEVELS:
            created_level, level_created = OrganizationLevel.objects.update_or_create(
                code=level_seed.code,
                defaults={
                    "name": level_seed.name,
                    "sort_order": level_seed.sort_order,
                    "description": level_seed.description,
                    "is_active": True,
                },
            )
            if level_created:
                created_levels += 1

        created_classifications = 0
        for classification_seed in DEFAULT_CLASSIFICATIONS:
            created_classification, classification_created = (
                PositionClassification.objects.update_or_create(
                    code=classification_seed.code,
                    defaults={
                        "name": classification_seed.name,
                        "sort_order": classification_seed.sort_order,
                        "description": classification_seed.description,
                        "is_active": True,
                    },
                )
            )
            if classification_created:
                created_classifications += 1

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    "Organizational structure catalogues ready: "
                    f"{created_levels} levels and "
                    f"{created_classifications} classifications created."
                )
            )
