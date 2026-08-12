"""Permission enforcement tests for the Report Builder services."""

from django.core.exceptions import PermissionDenied

from apps.reports.services import ReportTemplateService
from apps.reports.tests.base import ReportsTestCase


class ReportTemplatePermissionTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        # manager already has manage permission; outsider has none
        from apps.reports.models import ReportCategory

        self.category = ReportCategory.objects.first()
        self.assertIsNotNone(self.category, "No ReportCategory for tests")
        self.manager_service = ReportTemplateService(user=self.manager)
        self.officer_service = ReportTemplateService(user=self.officer)
        self.viewer_service = ReportTemplateService(user=self.viewer)
        self.outsider_service = ReportTemplateService(user=self.outsider)

    def test_manager_can_create(self):
        # manager has manage, should succeed
        tmpl = self.manager_service.create(
            code="perm-temp", title="Perm Test", category=self.category
        )
        self.assertIsNotNone(tmpl.pk)

    def test_officer_can_create(self):
        # officer has report_templates.create, so create succeeds
        tmpl = self.officer_service.create(
            code="off-temp", title="Off Test", category=self.category
        )
        self.assertIsNotNone(tmpl.pk)

    def test_viewer_cannot_create(self):
        # viewer only has view, so create is denied
        with self.assertRaises(PermissionDenied):
            self.viewer_service.create(
                code="view-temp", title="View Test", category=self.category
            )

    def test_viewer_cannot_update(self):
        tmpl = self.manager_service.create(
            code="view-temp", title="View Test", category=self.category
        )
        with self.assertRaises(PermissionDenied):
            self.viewer_service.update(tmpl, title="Malicious Update")

    def test_outsider_cannot_view(self):
        tmpl = self.manager_service.create(
            code="outs-temp", title="Outs Test", category=self.category
        )
        with self.assertRaises(PermissionDenied):
            self.outsider_service.update(tmpl, title="Should Fail")
