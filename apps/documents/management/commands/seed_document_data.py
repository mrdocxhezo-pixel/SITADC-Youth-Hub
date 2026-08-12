"""Management command to seed document reference data."""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.documents.seed_data import seed_all


class Command(BaseCommand):
    help = "Seed default document management reference data (categories, types, retention, settings)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding document management reference data...")

        results = seed_all()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created: {results['categories']} categories, "
                f"{results['types']} document types, "
                f"{results['retention']} retention categories. "
                f"Settings created: {results['settings']}"
            )
        )
