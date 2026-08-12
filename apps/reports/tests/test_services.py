"""Service-level integration tests for the Report Builder API."""

from apps.reports.exceptions import InvalidTemplateSchemaError
from apps.reports.models import ReportCategory, ReportTemplateVersion
from apps.reports.services import (
    ReportTemplateService,
    TemplateCloneService,
    TemplateImportService,
    TemplateSchemaService,
    TemplateVersionService,
)
from apps.reports.tests.base import ReportsTestCase


class ReportTemplateServiceTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.svc = ReportTemplateService(user=self.manager)
        self.category = ReportCategory.objects.first()
        self.assertIsNotNone(self.category, "No category to work with")
        self.template = self.svc.create(
            code="svc-temp",
            title="Service Test",
            category=self.category,
        )

    def _simple_schema(self):
        return {
            "template": {
                "code": self.template.code,
                "title": self.template.title,
                "reference_number": self.template.reference_number,
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
                                    "field_type": "INTEGER",
                                    "data_type": "INTEGER",
                                    "required": True,
                                    "is_calculated": False,
                                },
                                {
                                    "code": "field2",
                                    "label": "Field 2",
                                    "field_type": "FORMULA",
                                    "data_type": "INTEGER",
                                    "is_calculated": True,
                                    "formula": "field1 * 2",
                                },
                            ],
                        }
                    ],
                }
            ],
            "conditional_rules": [],
            "components": [],
        }

    def test_save_schema_creates_structure(self):
        schema = self._simple_schema()
        version = TemplateSchemaService(user=self.manager).save_schema(
            self.template, schema
        )
        self.assertIsInstance(version, ReportTemplateVersion)
        # Verify sections/fields persisted
        self.assertTrue(self.template.sections.filter(code="sec1").exists())
        field = (
            self.template.sections.get(code="sec1")
            .groups.get(code="grp1")
            .fields.get(code="field1")
        )
        self.assertEqual(field.field_type, "INTEGER")
        # Calculate field should be stored correctly
        calc = (
            self.template.sections.get(code="sec1")
            .groups.get(code="grp1")
            .fields.get(code="field2")
        )
        self.assertTrue(calc.is_calculated)
        self.assertEqual(calc.formula, "field1 * 2")

    def test_schema_validation_fails_on_invalid_formula(self):
        schema = self._simple_schema()
        # inject invalid formula
        schema["sections"][0]["groups"][0]["fields"][1]["formula"] = "evil()"
        with self.assertRaises(InvalidTemplateSchemaError):
            TemplateSchemaService(user=self.manager).save_schema(self.template, schema)

    def test_version_creation_and_working_version(self):
        version_svc = TemplateVersionService(user=self.manager)
        # initial version already exists; create a major bump
        v1 = version_svc.create_version(
            self.template, change_summary="first bump", bump="major"
        )
        self.assertEqual(v1.version_number, "2.0")
        # working version should be the latest draft
        working = version_svc.working_version(self.template)
        self.assertEqual(working.pk, v1.pk)

    def test_clone_creates_new_template(self):
        # save a valid schema first
        schema = self._simple_schema()
        TemplateSchemaService(user=self.manager).save_schema(self.template, schema)
        clone_svc = TemplateCloneService(user=self.manager)
        clone = clone_svc.clone(
            self.template,
            new_code="clone-temp",
            new_title="Cloned Template",
        )
        self.assertNotEqual(clone.pk, self.template.pk)
        self.assertEqual(clone.title, "Cloned Template")
        # cloned template should have its own draft version
        self.assertTrue(clone.versions.filter(is_current=False).exists())

    def test_import_and_export_roundtrip(self):
        # Build and save schema
        schema = self._simple_schema()
        TemplateSchemaService(user=self.manager).save_schema(self.template, schema)
        # Export
        payload = TemplateSchemaService(user=self.manager).export_json(self.template)
        self.assertIn("schema_version", payload)
        # Import as a new template
        import_svc = TemplateImportService(user=self.manager)
        new_template = import_svc.import_json(
            payload,
            code="imported-temp",
            category=self.category,
            notes="import test",
        )
        self.assertIsNotNone(new_template)
        self.assertNotEqual(new_template.pk, self.template.pk)
        # Imported template should have a working version
        self.assertTrue(new_template.versions.filter(status="DRAFT").exists())
