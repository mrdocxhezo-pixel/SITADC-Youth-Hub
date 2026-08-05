"""
Management command to seed initial volunteer management reference schemes and data.
"""

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Seeds initial volunteer management data and configuration."

    def handle(self, *args, **options):
        call_command("seed_reference_schemes", verbosity=0)
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS("Volunteer reference schemes verified successfully.")
            )
