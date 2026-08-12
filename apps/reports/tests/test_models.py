"""Model-level tests for the Report Builder app."""

from django.core.exceptions import PermissionDenied

from apps.reports.exceptions import TemplatePublishError
from apps.reports.models import ReportTemplateAuditRecord
from apps.reports.services import ReportTemplateService, TemplatePublicationService
from apps.reports.tests.base import ReportsTestCase


class ReportTemplateModelTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.service = ReportTemplateService(user=self.manager)
        # create a simple category for the template
        self.category = None
        # Use the existing categories seeded by the seed command
        from apps.reports.models import ReportCategory

        self.category = ReportCategory.objects.first()
        self.assertIsNotNone(self.category, "No ReportCategory available for tests")

    def test_create_template_allocates_reference_and_audit(self):
        tmpl = self.service.create(
            code="test-template",
            title="Test Template",
            category=self.category,
        )
        self.assertIsNotNone(tmpl.reference_number)
        # audit record should exist
        audit = ReportTemplateAuditRecord.objects.filter(
            entity_type="ReportTemplate", entity_id=str(tmpl.pk)
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action, "CREATED")

    def test_update_permission(self):
        tmpl = self.service.create(
            code="upd-temp",
            title="Update Me",
            category=self.category,
        )
        # officer can update
        srv_officer = ReportTemplateService(user=self.officer)
        updated = srv_officer.update(tmpl, title="Updated Title")
        self.assertEqual(updated.title, "Updated Title")
        # outsider should be denied
        srv_out = ReportTemplateService(user=self.outsider)
        with self.assertRaises(PermissionDenied):
            srv_out.update(tmpl, title="Hacker")

    def test_soft_delete_and_restore(self):
        tmpl = self.service.create(
            code="del-temp",
            title="To Delete",
            category=self.category,
        )
        # delete
        self.service.soft_delete(tmpl, notes="test delete")
        tmpl.refresh_from_db()
        self.assertTrue(tmpl.is_deleted)
        # restore
        restored = self.service.restore(tmpl, notes="test restore")
        self.assertFalse(restored.is_deleted)
        self.assertEqual(restored.status, "DRAFT")

    def test_publish_validation_errors(self):
        tmpl = self.service.create(
            code="pub-temp",
            title="Publish Fail",
            category=self.category,
        )
        # No working schema/version ready - publish should raise
        pub_srv = TemplatePublicationService(user=self.manager)
        with self.assertRaises(TemplatePublishError):
            pub_srv.publish(tmpl)
