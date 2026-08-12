"""Seed default report builder categories, settings, and all report templates."""

from django.core.management.base import BaseCommand

from apps.reports.seed_loader import seed_report_builder_defaults


class Command(BaseCommand):
    help = (
        "Idempotently seed Phase 19 report builder data: categories, "
        "templates, schemas."
    )

    def handle(self, *args, **options):
        stats = seed_report_builder_defaults()
        if int(options.get("verbosity", 1)):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Report builder configuration ready:\n"
                    f"  Categories: {stats['categories']}\n"
                    f"  Settings:   {stats['settings']}\n"
                    f"  Templates:  {stats['templates']}\n"
                    f"  Sections:   {stats['sections']}\n"
                    f"  Groups:     {stats['groups']}\n"
                    f"  Fields:     {stats['fields']}\n"
                    f"  Options:    {stats['options']}"
                )
            )
