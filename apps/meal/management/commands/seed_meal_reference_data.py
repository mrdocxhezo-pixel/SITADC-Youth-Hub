"""Seed default MEAL taxonomies and numbering schemes."""

from django.core.management.base import BaseCommand

from apps.meal.seed_loader import seed_meal_reference_data


class Command(BaseCommand):
    help = "Idempotently seed Phase 18 MEAL reference data and schemes."

    def handle(self, *args, **options):
        stats = seed_meal_reference_data()
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS(
                    "MEAL configuration ready: "
                    f"{stats['reference_data']} reference rows and "
                    f"{stats['schemes']} numbering schemes created."
                )
            )
