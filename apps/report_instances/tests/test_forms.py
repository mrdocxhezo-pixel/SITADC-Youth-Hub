"""Form tests for the ``report_instances`` app."""

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.report_instances.forms import DynamicReportForm
from apps.report_instances.views import ReportCreateForm

from .base import ReportInstanceBaseTestCase


class DynamicReportFormTest(ReportInstanceBaseTestCase):
    """The dynamic form renders a field per template schema field."""

    def test_form_builds_dynamic_fields(self):
        form = DynamicReportForm(template_id=self.template.pk)
        self.assertEqual(len(form.fields), 1)

        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        expected = f"section_{section.pk}_field_{field.pk}"
        self.assertIn(expected, form.fields)

    def test_form_is_valid_and_extracts_section_data(self):
        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        name = f"section_{section.pk}_field_{field.pk}"

        form = DynamicReportForm(
            {name: "hello"},
            template_id=self.template.pk,
        )
        self.assertTrue(form.is_valid())
        section_data = form.section_data(str(section.pk))
        self.assertEqual(section_data[str(field.pk)], "hello")
        self.assertEqual(
            form.all_section_data(),
            {str(section.pk): {str(field.pk): "hello"}},
        )

    def test_required_field_validation(self):
        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        name = f"section_{section.pk}_field_{field.pk}"

        form = DynamicReportForm({name: ""}, template_id=self.template.pk)
        self.assertFalse(form.is_valid())


class DynamicReportFormJsonSafetyTest(ReportInstanceBaseTestCase):
    """Section data must be JSON-safe before persistence."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        from apps.reports.services import (
            TemplatePublicationService,
            TemplateSchemaService,
        )

        svc_args = {"user": cls.admin}
        # Build a dedicated mixed-type template.
        from apps.reports.services import ReportTemplateService

        template_service = ReportTemplateService(**svc_args)
        cls.mixed_template = template_service.create(
            code="rpt-mixed-json",
            title="Mixed JSON Template",
            category=cls.category,
        )
        schema = {
            "template": {
                "code": cls.mixed_template.code,
                "title": cls.mixed_template.title,
                "reference_number": cls.mixed_template.reference_number,
            },
            "sections": [
                {
                    "code": "msec",
                    "name": "Mixed Section",
                    "sort_order": 1,
                    "groups": [
                        {
                            "code": "mgrp",
                            "name": "Mixed Group",
                            "sort_order": 1,
                            "fields": [
                                {
                                    "code": "mtext",
                                    "label": "Full Name",
                                    "field_type": "TEXT",
                                    "data_type": "STRING",
                                    "required": True,
                                },
                                {
                                    "code": "mdate",
                                    "label": "Date of Birth",
                                    "field_type": "DATE",
                                    "data_type": "DATE",
                                    "required": False,
                                },
                                {
                                    "code": "mamount",
                                    "label": "Amount",
                                    "field_type": "DECIMAL",
                                    "data_type": "DECIMAL",
                                    "required": False,
                                },
                                {
                                    "code": "mdoc",
                                    "label": "Evidence",
                                    "field_type": "DOCUMENT",
                                    "data_type": "STRING",
                                    "required": False,
                                },
                            ],
                        }
                    ],
                }
            ],
            "conditional_rules": [],
            "components": [],
        }
        TemplateSchemaService(**svc_args).save_schema(cls.mixed_template, schema)
        TemplatePublicationService(**svc_args).publish(cls.mixed_template)

    def _mixed_names(self):
        section = self.mixed_template.sections.get(code="msec")
        group = section.groups.get(code="mgrp")
        names = {
            code: f"section_{section.pk}_field_{group.fields.get(code=code).pk}"
            for code in ("mtext", "mdate", "mamount", "mdoc")
        }
        return section, group, names

    def test_section_data_serializes_dates_and_decimals(self):
        section, group, names = self._mixed_names()

        form = DynamicReportForm(
            {
                names["mtext"]: "Doris Kipume",
                names["mdate"]: "1999-11-18",
                names["mamount"]: "1234.50",
            },
            {
                names["mdoc"]: SimpleUploadedFile(
                    "evidence.jpg", b"bytes", content_type="image/jpeg"
                )
            },
            template_id=self.mixed_template.pk,
        )
        self.assertTrue(form.is_valid(), form.errors)

        section_data = form.section_data(str(section.pk))
        self.assertEqual(
            section_data[str(group.fields.get(code="mdate").pk)], "1999-11-18"
        )
        self.assertEqual(
            section_data[str(group.fields.get(code="mamount").pk)], "1234.50"
        )
        self.assertNotIn(str(group.fields.get(code="mdoc").pk), section_data)

        # Everything left must survive a JSON round-trip untouched.
        import json

        json.dumps(section_data)

    def test_date_cleaned_value_is_iso_string(self):
        """The raw cleaned value stays a date; extraction converts it."""
        import datetime

        section, _, names = self._mixed_names()
        form = DynamicReportForm(
            {
                names["mtext"]: "x",
                names["mdate"]: "1999-11-18",
            },
            template_id=self.mixed_template.pk,
        )
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data[names["mdate"]], datetime.date)
        self.assertEqual(
            form.section_data(str(section.pk))[
                names["mdate"].split("_field_")[1]
            ],
            "1999-11-18",
        )


class ReportCreateFormTest(ReportInstanceBaseTestCase):
    """The create form only offers published templates."""

    def test_template_queryset_is_published(self):
        form = ReportCreateForm()
        queryset = form.fields["template"].queryset
        self.assertIn(self.template, queryset)
        self.assertTrue(all(t.status == "PUBLISHED" for t in queryset))
