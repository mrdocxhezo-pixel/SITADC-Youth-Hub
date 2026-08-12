"""Security invariants: audit immutability and safe-upload validation."""

from datetime import date

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.meal.models import (
    MEALAuditRecord,
    MEALReport,
    MEALStatusHistory,
    MonitoringVisit,
)

from .base import MEALTestCase

MAX_UPLOAD_BYTES = 20 * 1024 * 1024


class AuditImmutabilityTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.visit = self.monitoring_visit()

    def monitoring_visit(self):
        visit = MonitoringVisit.objects.create(
            reference_number="MV-SEC-0001",
            visit_date=date(2025, 6, 1),
            created_by=self.manager,
            updated_by=self.manager,
        )
        MEALStatusHistory.objects.create(
            entity_type="MonitoringVisit",
            entity_id=str(visit.pk),
            action="CREATE",
            from_status="-",
            to_status="DRAFT",
            notes="created",
            created_by=self.manager,
        )
        MEALAuditRecord.objects.create(
            action="CREATE",
            entity_type="MonitoringVisit",
            entity_id=str(visit.pk),
            notes="created",
            created_by=self.manager,
        )
        return visit

    def test_status_history_is_immutable(self):
        record = MEALStatusHistory.objects.get(entity_id=str(self.visit.pk))
        with self.assertRaises(ValidationError):
            record.action = "UPDATE"
            record.save()

    def test_audit_record_is_immutable(self):
        record = MEALAuditRecord.objects.get(entity_id=str(self.visit.pk))
        with self.assertRaises(ValidationError):
            record.notes = "tampered"
            record.save()

    def test_delete_blocked(self):
        record = MEALStatusHistory.objects.get(entity_id=str(self.visit.pk))
        with self.assertRaises(ValidationError):
            record.delete()


class SafeUploadTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.viewer_uploader = self.create_user("uploader")
        self.grant_permissions(self.viewer_uploader, "meal.view", "meal.create")

    def _upload_report(self, content, filename, content_type):
        return MEALReport(
            reference_number="MRL-UPLOAD-0001",
            title="Uploaded report",
            report_type="BASELINE",
            content="Body",
            file=SimpleUploadedFile(filename, content, content_type),
            created_by=self.manager,
            updated_by=self.manager,
        )

    def test_oversized_file_rejected(self):
        report = self._upload_report(
            b"x" * (MAX_UPLOAD_BYTES + 1), "big.pdf", "application/pdf"
        )
        with self.assertRaises(ValidationError):
            report.full_clean()

    def test_disallowed_extension_rejected(self):
        report = self._upload_report(
            b"<script>alert(1)</script>", "evil.html", "text/html"
        )
        with self.assertRaises(ValidationError):
            report.full_clean()

    def test_allowed_extension_passes(self):
        report = self._upload_report(
            b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF",
            "report.pdf",
            "application/pdf",
        )
        report.full_clean()

    def test_upload_view_rejects_disallowed_type(self):
        self.client.force_login(self.viewer_uploader)
        response = self.client.post(
            reverse("meal:meal_report_create"),
            {
                "title": "Unsafe upload",
                "report_type": "BASELINE",
                "content": "Body",
                "file": SimpleUploadedFile(
                    "evil.html", b"<script>alert(1)</script>", "text/html"
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(MEALReport.objects.filter(title="Unsafe upload").exists())
