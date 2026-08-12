"""Export adapters, permission checks, and formula-injection safety."""

import csv
import io

from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.meal.exports import (
    complaint_register_csv_response,
    formula_safe_csv_value,
    indicator_register_csv_response,
    meal_report_export_response,
)

from .base import MEALTestCase


class ExportPermissionTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.exporter = self.create_user("exporter")
        self.grant_permissions(self.exporter, "meal.view", "meal.export")
        self.indicator = self.create_indicator()

    def test_indicator_register_csv(self):
        response = indicator_register_csv_response(self.exporter)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        self.assertEqual(rows[0][0], "Indicator ID")
        self.assertTrue(any(self.indicator.reference_number in row for row in rows))

    def test_export_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            indicator_register_csv_response(self.viewer)

    def test_complaint_register_hides_confidential_rows(self):
        self.create_complaint(is_confidential=False)
        self.create_complaint(is_confidential=True)
        response = complaint_register_csv_response(self.exporter)
        rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
        data_rows = rows[1:]
        self.assertEqual(len(data_rows), 1)
        self.assertEqual(data_rows[0][-1], "No")

    def test_export_view_endpoint_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("meal:indicator_register_export"))
        self.assertEqual(response.status_code, 403)


class ReportExportTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.exporter = self.create_user("exporter")
        self.grant_permissions(self.exporter, "meal.view", "meal.export")
        self.report = self.create_report(content="Quarterly performance summary.")

    def test_pdf_export(self):
        response = meal_report_export_response(self.exporter, self.report, "pdf")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF", response.content)

    def test_xlsx_export(self):
        response = meal_report_export_response(self.exporter, self.report, "xlsx")
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertEqual(response.content[:2], b"PK")

    def test_docx_export(self):
        response = meal_report_export_response(self.exporter, self.report, "docx")
        self.assertIn("wordprocessingml.document", response["Content-Type"])

    def test_unknown_format_denied(self):
        with self.assertRaises(PermissionDenied):
            meal_report_export_response(self.exporter, self.report, "html")

    def test_export_view_for_authorized_user(self):
        self.client.force_login(self.exporter)
        response = self.client.get(
            reverse(
                "meal:meal_report_export",
                kwargs={"pk": self.report.pk, "fmt": "pdf"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")


class FormulaSafetyTests(MEALTestCase):
    def test_formula_prefixes_neutralized(self):
        for dangerous in ("=cmd", "+1", "-2", "@import", "\t", "\r"):
            self.assertTrue(formula_safe_csv_value(dangerous).startswith("'"))
        self.assertEqual(formula_safe_csv_value("safe"), "safe")
