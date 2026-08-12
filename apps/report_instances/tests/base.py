"""Shared test scaffolding for the ``report_instances`` app.

The published-template setup mirrors the production workflow: seed report
builder defaults, register the reference-numbering scheme, build a template
schema and publish it.  ``setUpTestData`` runs once per test class to keep
the suite fast.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.reports.models import ReportCategory
from apps.reports.seed_loader import seed_report_builder_defaults
from apps.reports.services import (
    ReportTemplateService,
    TemplatePublicationService,
    TemplateSchemaService,
)

User = get_user_model()


class ReportInstanceBaseTestCase(TestCase):
    """Base case providing a published template and actor users."""

    password = "TestPass123!"
    template_code = "rpt-inst-base"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
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

        cls.admin = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password=cls.password,
        )
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            username="owner",
            password=cls.password,
        )
        cls.reviewer = User.objects.create_user(
            email="reviewer@example.com",
            username="reviewer",
            password=cls.password,
        )
        cls.other = User.objects.create_user(
            email="other@example.com",
            username="other",
            password=cls.password,
        )

        cls.category = ReportCategory.objects.first()
        cls.assertIsNotNone(
            cls.category, "Report categories must be seeded by report defaults"
        )
        cls.template = cls._build_published_template(cls.template_code)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _build_published_template(cls, code: str):
        svc = ReportTemplateService(user=cls.admin)
        template = svc.create(
            code=code,
            title=f"Template {code}",
            category=cls.category,
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
        TemplateSchemaService(user=cls.admin).save_schema(template, schema)
        TemplatePublicationService(user=cls.admin).publish(template)
        return template

    @classmethod
    def assign_role(cls, user, role_slug: str) -> None:
        """Assign an active RBAC role (seeded by the baseline migration)."""
        from apps.rbac.models import Role, UserRoleAssignment

        role = Role.objects.get(slug=role_slug)
        UserRoleAssignment.objects.create(
            user=user,
            role=role,
            status="ACTIVE",
        )

    def make_report(self, owner=None, title="Test Report"):
        """Create a draft report owned by ``owner`` (or the base owner)."""
        from apps.report_instances.services import create_report

        return create_report(
            template=self.template,
            title=title,
            owner=owner or self.owner,
        )

    def fill_report(self, report, user=None):
        """Save the required field + section response for the sample template."""
        from apps.report_instances.services import (
            save_field_response,
            save_section_response,
        )

        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        actor = user or self.owner
        save_field_response(report, field.id, "value", updated_by=actor)
        save_section_response(
            report, section.id, {str(field.pk): "value"}, updated_by=actor
        )
        return field, section
