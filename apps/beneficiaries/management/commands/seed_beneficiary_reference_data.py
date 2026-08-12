"""Seed default beneficiary taxonomies and child number schemes."""

from django.core.management.base import BaseCommand

from apps.beneficiaries.seed_loader import seed_beneficiary_reference_data


class Command(BaseCommand):
    help = "Idempotently seed Phase 17 beneficiary reference data."

    def handle(self, *args, **options):
        stats = seed_beneficiary_reference_data()
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS(
                    "Beneficiary configuration ready: "
                    f"{stats['reference_data']} reference rows and "
                    f"{stats['schemes']} numbering schemes created."
                )
            )
