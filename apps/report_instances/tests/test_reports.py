"""Tests for the report_instances app (Phase 20 — Report Management)."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.reports.constants import ReportStatus
from apps.reports.models import ReportCategory
from apps.reports.seed_loader import seed_report_builder_defaults
from apps.reports.services import (
    ReportTemplateService,
    TemplatePublicationService,
    TemplateSchemaService,
)

User = get_user_model()


class ReportWorkflowTest(TestCase):
    """End-to-end report lifecycle driven through the service layer."""

    password = "TestPass123!"

    def setUp(self):
        seed_report_builder_defaults()

        from apps.references.constants import ReferenceModules, SequenceResetPeriod
        from apps.references.models import ReferenceNumberScheme

        ReferenceNumberScheme.objects.get_or_create(
            code="report_template",
            defaults={
                "name": "Report Template Reference",
                "module": ReferenceModules.REPORTS,
                "record_type": "report_template",
                "prefix": "RT",
                "sequence_length": 4,
                "reset_period": SequenceResetPeriod.NEVER,
                "is_active": True,
            },
        )

        self.user = User.objects.create_user(
            email="tester@example.com",
            password=self.password,
        )
        self.user.is_superuser = True
        self.user.save()
        self.category = ReportCategory.objects.first()
        self.assertTrue(self.category, "Report categories must be seeded")
        self.template = self._build_published_template()

    def _build_published_template(self):
        svc = ReportTemplateService(user=self.user)
        template = svc.create(
            code="rpt-inst",
            title="Instance Template",
            category=self.category,
        )
        schema = {
            "template": {
                "code": template.code,
                "title": template.title,
                "reference_number": template.reference_number,
            },
            "sections": [
                {
                    "code": "sec1",
                    "name": "Section 1",
                    "sort_order": 1,
                    "groups": [
                        {
                            "code": "grp1",
                            "name": "Group 1",
                            "sort_order": 1,
                            "fields": [
                                {
                                    "code": "field1",
                                    "label": "Field 1",
                                    "field_type": "TEXT",
                                    "data_type": "STRING",
                                    "required": True,
                                    "is_calculated": False,
                                }
                            ],
                        }
                    ],
                }
            ],
            "conditional_rules": [],
            "components": [],
        }
        TemplateSchemaService(user=self.user).save_schema(template, schema)
        TemplatePublicationService(user=self.user).publish(template)
        return template

    def test_create_and_submit_report(self):
        from apps.report_instances.services import (
            create_report,
            save_field_response,
            save_section_response,
            submit_report,
            validate_report,
        )

        report = create_report(
            template=self.template,
            title="Test Report",
            owner=self.user,
        )
        self.assertEqual(report.status, ReportStatus.DRAFT)

        field = (
            self.template.sections.get(code="sec1")
            .groups.get(code="grp1")
            .fields.get(code="field1")
        )
        section = self.template.sections.get(code="sec1")

        save_field_response(report, field.id, "value", updated_by=self.user)
        save_section_response(
            report, section.id, {"field1": "value"}, updated_by=self.user
        )

        result = validate_report(report, validated_by=self.user)
        self.assertTrue(result.is_valid)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.READY_FOR_SUBMISSION)

        submit_report(report, submitted_by=self.user)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)

        self.assertEqual(report.versions.count(), 1)
        version = report.versions.first()
        self.assertEqual(version.version_number, 1)
