"""Form tests for the ``report_instances`` app."""

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


class ReportCreateFormTest(ReportInstanceBaseTestCase):
    """The create form only offers published templates."""

    def test_template_queryset_is_published(self):
        form = ReportCreateForm()
        queryset = form.fields["template"].queryset
        self.assertIn(self.template, queryset)
        self.assertTrue(all(t.status == "PUBLISHED" for t in queryset))
