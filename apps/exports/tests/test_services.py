"""Service-level tests for the Export Engine."""

from __future__ import annotations

from apps.exports.constants import ExportFormat, ExportStatus
from apps.exports.exceptions import (
    ExportDownloadDenied,
    ExportExpiredError,
    ExportPermissionDenied,
    ExportValidationError,
)
from apps.exports.models import ExportActivity
from apps.exports.services import (
    CancelExportService,
    DownloadExportService,
    GenerateExportService,
    RequestExportService,
)

from .base import ExportsTestCase


class RequestExportServiceTests(ExportsTestCase):
    def test_manager_can_request_report_export(self):
        request = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format=ExportFormat.PDF,
            requested_by=self.manager,
        )
        self.assertIn("SITADC-EXP-", request.reference_number)
        self.assertEqual(request.status, ExportStatus.QUEUED)
        self.assertEqual(request.source_type, "REPORT")
        self.assertEqual(
            ExportActivity.objects.filter(export_request=request).count(), 1
        )

    def test_viewer_without_create_permission_denied(self):
        with self.assertRaises(ExportPermissionDenied):
            RequestExportService(user=self.viewer).execute(
                source_type="REPORT",
                format=ExportFormat.PDF,
                requested_by=self.viewer,
            )

    def test_outsider_cannot_request(self):
        with self.assertRaises(ExportPermissionDenied):
            RequestExportService(user=self.outsider).execute(
                source_type="REPORT",
                format=ExportFormat.PDF,
                requested_by=self.outsider,
            )

    def test_unknown_source_raises_provider_error(self):
        from apps.exports.exceptions import ExportProviderError

        with self.assertRaises(ExportProviderError):
            RequestExportService(user=self.manager).execute(
                source_type="SEARCH",
                format=ExportFormat.PDF,
                requested_by=self.manager,
            )


class GenerateExportServiceTests(ExportsTestCase):
    def setUp(self):
        self.request = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format=ExportFormat.PDF,
            requested_by=self.manager,
        )

    def test_generates_pdf_file(self):
        generated = GenerateExportService(user=self.manager).execute(self.request)
        self.assertEqual(generated.status, ExportStatus.COMPLETED)
        self.assertTrue(generated.storage_path)
        self.assertTrue(generated.file_size > 0)
        self.assertTrue(generated.is_downloadable)

    def test_generation_records_activity(self):
        GenerateExportService(user=self.manager).execute(self.request)
        self.assertIn(
            "GENERATED",
            list(
                ExportActivity.objects.filter(export_request=self.request).values_list(
                    "action", flat=True
                )
            ),
        )


class DownloadExportServiceTests(ExportsTestCase):
    def setUp(self):
        self.request = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format=ExportFormat.PDF,
            requested_by=self.manager,
        )
        GenerateExportService(user=self.manager).execute(self.request)

    def test_owner_can_download(self):
        service = DownloadExportService(user=self.manager)
        service.execute(self.request)
        handle = service.file_handle(self.request)
        self.assertTrue(hasattr(handle, "read"))
        handle.close()

    def test_other_user_without_all_history_denied(self):
        with self.assertRaises(ExportDownloadDenied):
            DownloadExportService(user=self.viewer).execute(self.request)

    def test_superuser_can_download_others(self):
        service = DownloadExportService(user=self.admin)
        service.execute(self.request)
        handle = service.file_handle(self.request)
        handle.close()

    def test_expired_export_raises(self):
        from datetime import timedelta

        from django.utils import timezone

        self.request.expires_at = timezone.now() - timedelta(hours=1)
        self.request.save()
        with self.assertRaises(ExportExpiredError):
            DownloadExportService(user=self.manager).execute(self.request)


class CancelExportServiceTests(ExportsTestCase):
    def setUp(self):
        self.request = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format=ExportFormat.PDF,
            requested_by=self.manager,
        )

    def test_owner_can_cancel_queued(self):
        cancelled = CancelExportService(user=self.manager).execute(self.request)
        self.assertEqual(cancelled.status, ExportStatus.CANCELLED)

    def test_cannot_cancel_finished(self):
        GenerateExportService(user=self.manager).execute(self.request)
        with self.assertRaises(ExportValidationError):
            CancelExportService(user=self.manager).execute(self.request)

    def test_viewer_cannot_cancel(self):
        with self.assertRaises(ExportPermissionDenied):
            CancelExportService(user=self.viewer).execute(self.request)


class SensitiveExportTests(ExportsTestCase):
    def test_beneficiary_export_requires_sensitive_permission(self):
        request = RequestExportService(user=self.manager).execute(
            source_type="BENEFICIARY",
            format=ExportFormat.PDF,
            requested_by=self.manager,
        )
        request.is_sensitive = True
        request.save()
        with self.assertRaises(ExportPermissionDenied):
            GenerateExportService(user=self.manager).execute(request)

    def test_admin_can_generate_sensitive_beneficiary_export(self):
        request = RequestExportService(user=self.admin).execute(
            source_type="BENEFICIARY",
            format=ExportFormat.PDF,
            requested_by=self.admin,
        )
        request.is_sensitive = True
        request.save()
        generated = GenerateExportService(user=self.admin).execute(request)
        self.assertEqual(generated.status, ExportStatus.COMPLETED)
