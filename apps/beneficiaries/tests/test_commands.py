"""Beneficiary seed and validation command tests."""

from io import StringIO

from django.core.management import call_command

from apps.beneficiaries.models import BeneficiaryReferenceData
from apps.references.models import ReferenceNumberScheme

from .base import BeneficiaryTestCase


class BeneficiarySeedCommandTests(BeneficiaryTestCase):
    def test_seed_command_is_idempotent(self):
        initial_counts = (
            BeneficiaryReferenceData.objects.count(),
            ReferenceNumberScheme.objects.filter(module="beneficiaries").count(),
        )
        output = StringIO()
        call_command("seed_beneficiary_reference_data", stdout=output)
        call_command("seed_beneficiary_reference_data", stdout=output)
        self.assertEqual(
            (
                BeneficiaryReferenceData.objects.count(),
                ReferenceNumberScheme.objects.filter(module="beneficiaries").count(),
            ),
            initial_counts,
        )
        self.assertIn("0 reference rows", output.getvalue())

    def test_base_beneficiary_scheme_exists_for_reference_allocation(self):
        self.assertTrue(
            ReferenceNumberScheme.objects.filter(
                code="beneficiary", module="beneficiaries"
            ).exists()
        )
