"""Seed default program taxonomies and child number schemes."""

from django.core.management.base import BaseCommand

from apps.programs.seed_loader import seed_program_reference_data


class Command(BaseCommand):
    help = "Idempotently seed Phase 15 program reference data."

    def handle(self, *args, **options):
        stats = seed_program_reference_data()
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS(
                    "Program configuration ready: "
                    f"{stats['reference_data']} reference rows and "
                    f"{stats['schemes']} numbering schemes created."
                )
            )
