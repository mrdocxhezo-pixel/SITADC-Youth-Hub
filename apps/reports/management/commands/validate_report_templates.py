"""Validate every report template schema and report blockers."""

from django.core.management.base import BaseCommand, CommandError

from apps.reports.models import ReportTemplate
from apps.reports.services import (
    TemplatePublicationService,
    TemplateSchemaService,
)


class Command(BaseCommand):
    help = "Validate the schema and publish-readiness of all report templates."

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish-check",
            action="store_true",
            help="Also run the full publish-readiness validation.",
        )

    def handle(self, *args, **options):
        schema_service = TemplateSchemaService(user=None)
        publish_service = TemplatePublicationService(user=None)
        problems = 0
        checked = 0
        for template in ReportTemplate.all_objects.all():
            schema = schema_service.build_schema(template)
            schema_errors = schema_service.validate_schema(template, schema)
            try:
                schema_service.validate_formula_graph(template, schema)
            except Exception as exc:  # - report every formula issue
                schema_errors.append(str(exc))
            try:
                schema_service.validate_condition_graph(template, schema)
            except Exception as exc:  # - report every condition issue
                schema_errors.append(str(exc))
            checked += 1
            if schema_errors:
                problems += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"{template.reference_number} ({template.code}):"
                    )
                )
                for error in schema_errors:
                    self.stdout.write(self.style.ERROR(f"  - {error}"))
            if options["publish_check"]:
                blockers = publish_service.validate_ready(template)
                if blockers:
                    problems += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"{template.reference_number} ({template.code}) "
                            "is not publish-ready:"
                        )
                    )
                    for blocker in blockers:
                        self.stdout.write(self.style.WARNING(f"  - {blocker}"))
        self.stdout.write(
            self.style.SUCCESS(
                f"Validated {checked} template(s); "
                f"{problems} template(s) with issues."
            )
        )
        if problems:
            raise CommandError(f"{problems} template(s) have validation issues.")
