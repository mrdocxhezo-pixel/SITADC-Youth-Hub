"""Seed default stakeholder taxonomies, score dimensions, and number schemes."""

from django.core.management.base import BaseCommand

from apps.stakeholders.seed_loader import seed_stakeholder_reference_data


class Command(BaseCommand):
    help = "Idempotently seed Phase 14 stakeholder reference data."

    def handle(self, *args, **options):
        stats = seed_stakeholder_reference_data()
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS(
                    "Stakeholder configuration ready: "
                    f"{stats['reference_data']} reference rows, "
                    f"{stats['dimensions']} score dimensions, and "
                    f"{stats['schemes']} numbering schemes created."
                )
            )
