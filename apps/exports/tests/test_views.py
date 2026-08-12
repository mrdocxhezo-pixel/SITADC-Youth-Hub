"""View-level tests for the Export Engine."""

from __future__ import annotations

from django.urls import reverse

from apps.exports.models import ExportRequest, ExportStatus
from apps.exports.services import GenerateExportService, RequestExportService

from .base import ExportsTestCase


class ExportViewAccessTests(ExportsTestCase):
    def test_anonymous_home_denied(self):
        response = self.client.get(reverse("exports:home"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_home_ok(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(reverse("exports:home"))
        self.assertEqual(response.status_code, 200)

    def test_manager_home_ok(self):
        self.assertTrue(self.login_as(self.manager))
        response = self.client.get(reverse("exports:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Export")

    def test_settings_requires_manage(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(reverse("exports:settings"))
        self.assertEqual(response.status_code, 403)

    def test_settings_admin_ok(self):
        self.assertTrue(self.login_as(self.admin))
        response = self.client.get(reverse("exports:settings"))
        self.assertEqual(response.status_code, 200)

    def test_templates_requires_manage(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(reverse("exports:templates"))
        self.assertEqual(response.status_code, 403)

    def test_templates_admin_ok(self):
        self.assertTrue(self.login_as(self.admin))
        response = self.client.get(reverse("exports:templates"))
        self.assertEqual(response.status_code, 200)


class ExportCreateViewTests(ExportsTestCase):
    def _create_payload(self):
        return {
            "source_type": "REPORT",
            "format": "PDF",
            "include_sensitive": "",
            "confirmed": "on",
        }

    def test_viewer_cannot_create(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.post(reverse("exports:create"), self._create_payload())
        self.assertEqual(response.status_code, 403)

    def test_manager_creates_and_redirects_to_detail(self):
        self.assertTrue(self.login_as(self.manager))
        response = self.client.post(reverse("exports:create"), self._create_payload())
        self.assertEqual(response.status_code, 302)
        export = ExportRequest.objects.latest("created_at")
        self.assertIn(str(export.pk), response.url)
        self.assertEqual(export.status, ExportStatus.COMPLETED)

    def test_invalid_source_rejected(self):
        self.assertTrue(self.login_as(self.manager))
        payload = self._create_payload()
        payload["source_type"] = "SEARCH"
        response = self.client.post(reverse("exports:create"), payload)
        self.assertRedirects(response, reverse("exports:home"))


class ExportHistoryViewTests(ExportsTestCase):
    def test_manager_sees_own_history(self):
        RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format="PDF",
            requested_by=self.manager,
        )
        self.assertTrue(self.login_as(self.manager))
        response = self.client.get(reverse("exports:history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SITADC-EXP-")

    def test_viewer_history_does_not_leak_others(self):
        RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format="PDF",
            requested_by=self.manager,
        )
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(reverse("exports:history"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "SITADC-EXP-")


class ExportDetailViewTests(ExportsTestCase):
    def setUp(self):
        self.export = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format="PDF",
            requested_by=self.manager,
        )

    def test_owner_can_view_detail(self):
        self.assertTrue(self.login_as(self.manager))
        response = self.client.get(
            reverse("exports:detail", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.export.reference_number)

    def test_other_user_gets_404(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(
            reverse("exports:detail", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 404)


class ExportDownloadViewTests(ExportsTestCase):
    def setUp(self):
        self.export = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format="PDF",
            requested_by=self.manager,
        )
        GenerateExportService(user=self.manager).execute(self.export)

    def test_owner_downloads_file(self):
        self.assertTrue(self.login_as(self.manager))
        response = self.client.get(
            reverse("exports:download", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            f'attachment; filename="{self.export.filename}"',
        )

    def test_viewer_cannot_download_others(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.get(
            reverse("exports:download", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 404)


class ExportCancelViewTests(ExportsTestCase):
    def setUp(self):
        self.export = RequestExportService(user=self.manager).execute(
            source_type="REPORT",
            format="PDF",
            requested_by=self.manager,
        )

    def test_owner_cancels_pending(self):
        self.assertTrue(self.login_as(self.manager))
        response = self.client.post(
            reverse("exports:cancel", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 302)
        self.export.refresh_from_db()
        self.assertEqual(self.export.status, ExportStatus.CANCELLED)

    def test_viewer_cannot_cancel(self):
        self.assertTrue(self.login_as(self.viewer))
        response = self.client.post(
            reverse("exports:cancel", kwargs={"pk": self.export.pk})
        )
        self.assertEqual(response.status_code, 404)
        self.export.refresh_from_db()
        self.assertEqual(self.export.status, ExportStatus.QUEUED)
