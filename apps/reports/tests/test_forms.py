"""Unit tests for Phase 19 Report Builder forms."""
from __future__ import annotations

import json

from django.test import TestCase

from apps.reports.forms import (
    ReportCategoryForm,
    SchemaEditorForm,
    TemplateCloneForm,
    TemplateImportForm,
    TemplatePublishForm,
)
from apps.reports.models import ReportCategory
from apps.reports.tests.base import ReportsTestCase

# ── SchemaEditorForm ───────────────────────────────────────────────────────

class SchemaEditorFormTests(TestCase):
    def _valid(self):
        return json.dumps({"sections": []})

    def test_valid_schema_passes(self):
        form = SchemaEditorForm(data={"schema": self._valid(), "change_summary": ""})
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_sections_key_fails(self):
        form = SchemaEditorForm(data={"schema": json.dumps({"no_sections": []}), "change_summary": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_invalid_json_fails(self):
        form = SchemaEditorForm(data={"schema": "{bad json", "change_summary": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_array_root_fails(self):
        form = SchemaEditorForm(data={"schema": json.dumps([{"sections": []}]), "change_summary": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("schema", form.errors)

    def test_cleaned_data_is_dict_with_sections(self):
        schema = {"sections": [{"code": "s1", "name": "S1", "groups": []}]}
        form = SchemaEditorForm(data={"schema": json.dumps(schema), "change_summary": "test"})
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data["schema"], dict)
        self.assertIn("sections", form.cleaned_data["schema"])


# ── TemplateImportForm ─────────────────────────────────────────────────────

class TemplateImportFormTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.category = ReportCategory.objects.first()

    def _form(self, payload, **extra):
        data = {
            "category": str(self.category.pk),
            "payload": json.dumps(payload),
            "dry_run": False,
        }
        data.update(extra)
        return TemplateImportForm(data=data)

    def test_valid_payload_passes(self):
        form = self._form({"code": "imported", "sections": []})
        self.assertTrue(form.is_valid(), form.errors)

    def test_non_dict_payload_fails(self):
        form = TemplateImportForm(data={
            "category": str(self.category.pk),
            "payload": json.dumps([1, 2, 3]),
            "dry_run": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("payload", form.errors)

    def test_invalid_json_payload_fails(self):
        form = TemplateImportForm(data={
            "category": str(self.category.pk),
            "payload": "not-json",
            "dry_run": False,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("payload", form.errors)

    def test_cleaned_payload_is_dict(self):
        form = self._form({"code": "test-imp", "sections": []})
        self.assertTrue(form.is_valid())
        self.assertIsInstance(form.cleaned_data["payload"], dict)

    def test_dry_run_is_optional(self):
        form = self._form({"sections": []})
        self.assertTrue(form.is_valid(), form.errors)


# ── TemplateCloneForm ──────────────────────────────────────────────────────

class TemplateCloneFormTests(TestCase):
    def test_valid_clone_form(self):
        form = TemplateCloneForm(data={"new_code": "my-clone", "new_title": "Cloned", "notes": ""})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_slug_fails(self):
        form = TemplateCloneForm(data={"new_code": "invalid slug!", "new_title": "", "notes": ""})
        self.assertFalse(form.is_valid())
        self.assertIn("new_code", form.errors)

    def test_title_is_optional(self):
        form = TemplateCloneForm(data={"new_code": "valid-slug"})
        self.assertTrue(form.is_valid(), form.errors)


# ── ReportCategoryForm ─────────────────────────────────────────────────────

class ReportCategoryFormTests(TestCase):
    def test_valid_category_form(self):
        form = ReportCategoryForm(data={
            "code": "cat-001", "name": "Category One",
            "description": "A test", "color": "#00ff00",
            "icon": "bi-star", "sort_order": 10,
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_code_is_required(self):
        form = ReportCategoryForm(data={"name": "No Code"})
        self.assertFalse(form.is_valid())
        self.assertIn("code", form.errors)

    def test_name_is_required(self):
        form = ReportCategoryForm(data={"code": "cat-002"})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_description_is_optional(self):
        form = ReportCategoryForm(data={"code": "cat-003", "name": "No Desc", "sort_order": 10})
        self.assertTrue(form.is_valid(), form.errors)


# ── TemplatePublishForm ────────────────────────────────────────────────────

class TemplatePublishFormTests(TestCase):
    def test_empty_notes_is_valid(self):
        form = TemplatePublishForm(data={"notes": ""})
        self.assertTrue(form.is_valid(), form.errors)

    def test_notes_with_content_is_valid(self):
        form = TemplatePublishForm(data={"notes": "Publishing for Q3 reporting."})
        self.assertTrue(form.is_valid(), form.errors)
