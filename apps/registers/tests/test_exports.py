"""Export adapters, permission checks, and formula-injection safety."""

import csv
import io
import json

from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.registers.exports import (
    formula_safe_csv_value,
    register_export_response,
    register_register_csv_response,
)

from .base import RegistersTestCase


class ExportPermissionTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.create_register_entry()

    def test_csv_export_includes_entry(self):
        response = register_register_csv_response(self.officer)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        self.assertEqual(rows[0][0], "Reference Number")
        self.assertTrue(any(self.entry.reference_number in row for row in rows))

    def test_export_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            register_register_csv_response(self.viewer)

    def test_confidential_entries_hidden_from_exporter(self):
        self.make_confidential_entry()
        response = register_register_csv_response(self.officer)
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        data_rows = rows[1:]
        self.assertEqual(len(data_rows), 1)

    def test_export_activity_recorded(self):
        register_register_csv_response(self.officer)
        from apps.registers.models import RegisterActivity

        self.assertTrue(RegisterActivity.objects.filter(action="EXPORTED").exists())

    def test_export_view_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:export"))
        self.assertEqual(response.status_code, 403)


class FormatExportTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.create_register_entry()

    def test_json_export(self):
        response = register_export_response(self.officer, fmt="json")
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        payload = json.loads(response.content.decode("utf-8"))
        self.assertTrue(any(row["Title"] == self.entry.title for row in payload))

    def test_xlsx_export(self):
        response = register_export_response(self.officer, fmt="xlsx")
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(response.content[:2], b"PK")

    def test_docx_export(self):
        response = register_export_response(self.officer, fmt="docx")
        self.assertIn("wordprocessingml.document", response["Content-Type"])

    def test_pdf_export(self):
        response = register_export_response(self.officer, fmt="pdf")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF", response.content)

    def test_unknown_format_denied(self):
        with self.assertRaises(PermissionDenied):
            register_export_response(self.officer, fmt="html")

    def test_register_scoped_export(self):
        other_category = self.create_category("Volunteer", "volunteer", "VOL")
        other_register = self.create_register(other_category, self.manager)
        self.create_register_entry(register=other_register)
        response = register_export_response(self.officer, register=self.register)
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        data_rows = rows[1:]
        self.assertEqual(len(data_rows), 1)


class FormulaSafetyTests(RegistersTestCase):
    def test_formula_prefixes_neutralized(self):
        for dangerous in ("=cmd", "+1", "-2", "@import", "\t", "\r"):
            self.assertTrue(formula_safe_csv_value(dangerous).startswith("'"))
        self.assertEqual(formula_safe_csv_value("safe"), "safe")
