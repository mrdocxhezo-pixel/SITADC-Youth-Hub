"""Program seed and reference configuration command tests."""

from io import StringIO

from django.core.management import call_command

from apps.programs.models import ProgramReferenceData

from .base import ProgramTestCase


class ProgramSeedCommandTests(ProgramTestCase):
    def test_seed_command_is_idempotent(self):
        initial_count = ProgramReferenceData.objects.count()
        output = StringIO()
        call_command("seed_program_reference_data", stdout=output)
        call_command("seed_program_reference_data", stdout=output)
        self.assertEqual(ProgramReferenceData.objects.count(), initial_count)
        self.assertIn("reference rows and 0 numbering schemes", output.getvalue())

    def test_seed_command_installs_expected_taxonomies(self):
        call_command("seed_program_reference_data", stdout=StringIO())
        for kind in (
            "CATEGORY",
            "PROJECT_CATEGORY",
            "PILLAR",
            "SDG",
            "FUNDING_SOURCE",
            "RISK_CATEGORY",
        ):
            self.assertTrue(
                ProgramReferenceData.objects.filter(kind=kind, active=True).exists(),
                f"Missing seeded {kind} reference data",
            )
