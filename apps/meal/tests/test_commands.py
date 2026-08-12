"""Management command tests."""

from django.core.management import call_command

from apps.meal.constants import ReferenceDataKind
from apps.meal.models import MEALReferenceData
from apps.meal.seed_data import DEFAULT_REFERENCE_DATA, DEFAULT_REFERENCE_SCHEMES
from apps.references.models import ReferenceNumberScheme

from .base import MEALTestCase


class SeedCommandTests(MEALTestCase):
    def test_seed_command_creates_reference_data(self):
        call_command("seed_meal_reference_data")
        self.assertEqual(MEALReferenceData.objects.count(), len(DEFAULT_REFERENCE_DATA))
        self.assertTrue(
            MEALReferenceData.objects.filter(
                kind=ReferenceDataKind.REPORTING_FREQUENCY, code="monthly"
            ).exists()
        )
        self.assertTrue(
            MEALReferenceData.objects.filter(
                kind=ReferenceDataKind.EVALUATION_TYPE, code="endline"
            ).exists()
        )

    def test_seed_command_is_idempotent(self):
        call_command("seed_meal_reference_data")
        first = list(
            MEALReferenceData.objects.order_by("kind", "code").values_list(
                "pk", flat=True
            )
        )
        call_command("seed_meal_reference_data")
        second = list(
            MEALReferenceData.objects.order_by("kind", "code").values_list(
                "pk", flat=True
            )
        )
        self.assertEqual(first, second)

    def test_seed_creates_numbering_schemes(self):
        call_command("seed_meal_reference_data")
        codes = set(
            ReferenceNumberScheme.objects.filter(module="meal").values_list(
                "code", flat=True
            )
        )
        self.assertIn("indicator", codes)
        self.assertIn("theory_of_change", codes)
        self.assertIn("complaint", codes)
        self.assertIn("meal_report", codes)
        for code, _name, _prefix in DEFAULT_REFERENCE_SCHEMES:
            self.assertIn(code, codes)
