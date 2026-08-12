"""Export tests for the ``report_instances`` app."""

from apps.report_instances.exports import export_csv, export_html, export_json

from .base import ReportInstanceBaseTestCase


class ReportExportTest(ReportInstanceBaseTestCase):
    """Exports return the expected content type and payload."""

    def _populated(self):
        report = self.make_report()
        self.fill_report(report)
        return report

    def test_export_json(self):
        report = self._populated()
        response = export_json(report)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertIn("attachment", response["Content-Disposition"])
        content = response.content.decode()
        self.assertIn(report.reference_number, content)
        self.assertIn(report.title, content)

    def test_export_csv(self):
        report = self._populated()
        response = export_csv(report)
        self.assertEqual(response["Content-Type"], "text/csv")
        content = response.content.decode()
        self.assertIn(report.reference_number, content)
        self.assertIn(report.title, content)

    def test_export_html(self):
        report = self._populated()
        response = export_html(report)
        self.assertEqual(response["Content-Type"], "text/html")
        content = response.content.decode()
        self.assertIn(f"<h1>{report.title}</h1>", content)
        self.assertIn(report.reference_number, content)
