"""Validate stakeholder model and cross-taxonomy invariants without mutation."""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.stakeholders.constants import ReferenceDataKind
from apps.stakeholders.models import Stakeholder


class Command(BaseCommand):
    help = "Validate stakeholder records and their configurable taxonomy links."

    def handle(self, *args, **options):
        checked = 0
        errors = []
        for stakeholder in Stakeholder.all_objects.filter(is_deleted=False).iterator():
            checked += 1
            try:
                stakeholder.full_clean()
                self._validate_taxonomies(stakeholder)
                self._validate_contacts(stakeholder)
            except ValidationError as exc:
                errors.append(f"{stakeholder.pk}: {exc}")
        for error in errors:
            self.stderr.write(error)
        if errors:
            raise CommandError(
                f"Validated {checked} stakeholder records; {len(errors)} were invalid."
            )
        self.stdout.write(
            self.style.SUCCESS(f"Validated {checked} stakeholder records successfully.")
        )

    @staticmethod
    def _validate_taxonomies(stakeholder):
        for field_name, expected_kind in (
            ("categories", ReferenceDataKind.CATEGORY),
            ("sectors", ReferenceDataKind.SECTOR),
            ("focus_areas", ReferenceDataKind.FOCUS_AREA),
            ("sdgs", ReferenceDataKind.SDG),
        ):
            if getattr(stakeholder, field_name).exclude(kind=expected_kind).exists():
                raise ValidationError(
                    {field_name: "One or more linked values have the wrong kind."}
                )

    @staticmethod
    def _validate_contacts(stakeholder):
        primary_count = stakeholder.contacts.filter(
            is_primary=True, is_active=True
        ).count()
        if primary_count > 1:
            raise ValidationError({"contacts": "More than one active primary contact."})
