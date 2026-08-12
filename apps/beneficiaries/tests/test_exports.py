"""Export engine, formula-safety, and scoping tests."""

import csv
from io import StringIO

from django.core.exceptions import PermissionDenied

from apps.beneficiaries.exports import (
    beneficiary_register_csv_response,
    formula_safe_csv_value,
)

from .base import BeneficiaryTestCase


class FormulaSafetyTests(BeneficiaryTestCase):
    def test_formula_safe_csv_value_prefixes_dangerous_leading_chars(self):
        for unsafe in ("=SUM(A1:A9)", "+cmd", "@x", "-x", "\t", "\r"):
            with self.subTest(value=unsafe):
                self.assertTrue(formula_safe_csv_value(unsafe).startswith("'"))

    def test_safe_values_are_returned_unchanged(self):
        self.assertEqual(formula_safe_csv_value("Maria Banda"), "Maria Banda")
        self.assertEqual(formula_safe_csv_value(2026), "2026")


class RegisterExportTests(BeneficiaryTestCase):
    def test_export_requires_export_permission(self):
        self.grant_permissions(self.viewer, "beneficiaries.view")
        with self.assertRaises(PermissionDenied):
            beneficiary_register_csv_response(self.viewer)

    def test_export_includes_scoped_records(self):
        included = self.create_beneficiary(
            first_name="Exported",
            last_name="Row",
            created_by=self.viewer,
            updated_by=self.viewer,
        )
        self.grant_permissions(
            self.viewer, "beneficiaries.view", "beneficiaries.export"
        )
        response = beneficiary_register_csv_response(self.viewer)
        content = response.content.decode()
        reader = csv.reader(StringIO(content))
        rows = list(reader)
        self.assertEqual(rows[0][0], "Beneficiary ID")
        self.assertTrue(any(included.reference_number == row[0] for row in rows[1:]))

    def test_export_neutralizes_formula_injection_in_names(self):
        self.create_beneficiary(
            first_name="=HYPERLINK",
            last_name='"http://evil.example"',
            created_by=self.manager,
            updated_by=self.manager,
        )
        response = beneficiary_register_csv_response(self.manager)
        content = response.content.decode()
        self.assertIn("'=HYPERLINK", content)

    def test_export_never_exposes_out_of_scope_records(self):
        self.create_beneficiary()
        self.grant_permissions(self.viewer, "beneficiaries.export")
        response = beneficiary_register_csv_response(self.viewer)
        content = response.content.decode()
        rows = list(csv.reader(StringIO(content)))
        self.assertEqual(len(rows), 1)
