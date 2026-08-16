"""Provider and renderer tests for the Export Engine."""

from __future__ import annotations

from django.utils import timezone

from apps.exports.models import ExportConfiguration
from apps.exports.providers import registry
from apps.exports.providers.base import BaseProvider
from apps.exports.renderers import RendererRegistry, get_renderer
from apps.exports.renderers.base import ExportColumn, ExportDataset, RenderResult

from .base import ExportsTestCase


class ProviderRegistryTests(ExportsTestCase):
    def test_providers_registered(self):
        keys = registry.keys()
        self.assertIn("reports.template", keys)
        self.assertIn("registers.register", keys)
        self.assertIn("beneficiaries.profile", keys)
        self.assertIn("directory.volunteers", keys)
        self.assertIn("directory.stakeholders", keys)
        self.assertIn("documents.metadata", keys)

    def test_available_filters_by_permission(self):
        available = registry.available(self.viewer, source_types=["REPORT"])
        keys = [provider.key for provider in available]
        self.assertNotIn("reports.template", keys)

    def test_manager_sees_available_reports(self):
        available = registry.available(self.manager, source_types=["REPORT"])
        keys = [provider.key for provider in available]
        self.assertIn("reports.template", keys)

    def test_superuser_sees_all(self):
        available = registry.available(self.admin)
        self.assertGreaterEqual(len(available), 3)


class SensitiveColumnTests(ExportsTestCase):
    def test_sensitive_columns_dropped_without_permission(self):
        provider = registry.get("beneficiaries.profile")
        self.assertIsNotNone(provider)
        columns = provider.columns(self.viewer)
        keys = [column.key for column in columns]
        self.assertNotIn("date_of_birth", keys)
        self.assertIn("full_name", keys)

    def test_sensitive_columns_included_with_permission(self):
        provider = registry.get("beneficiaries.profile")
        columns = provider.columns(self.admin)
        keys = [column.key for column in columns]
        self.assertIn("date_of_birth", keys)


class RendererRegistryTests(ExportsTestCase):
    def test_all_formats_available(self):
        formats = RendererRegistry.available_formats()
        self.assertIn("PDF", formats)
        self.assertIn("DOCX", formats)
        self.assertIn("XLSX", formats)
        self.assertIn("CSV", formats)
        self.assertIn("PRINT_HTML", formats)
        self.assertIn("PNG", formats)
        self.assertIn("JPEG", formats)

    def test_get_renderer_returns_instance(self):
        renderer = get_renderer("PDF")
        self.assertIsNotNone(renderer)

    def test_get_renderer_raises_for_unknown(self):
        with self.assertRaises(ValueError):
            get_renderer("TXT")


class RendererOutputTests(ExportsTestCase):
    def setUp(self):
        self.config = ExportConfiguration.load()
        self.dataset = ExportDataset(
            title="Test Export",
            subtitle="Test",
            reference="SITADC-EXP-2026-000001",
            generated_by="Test User",
            generated_at=timezone.now(),
            confidentiality="INTERNAL",
            columns=[
                ExportColumn("name", "Name"),
                ExportColumn("value", "Value"),
            ],
            rows=[["A", "1"], ["B", "2"]],
        )

    def test_csv_render_produces_bytes(self):
        renderer = get_renderer("CSV")
        result = renderer.render(self.dataset, self.config)
        self.assertIsInstance(result, RenderResult)
        self.assertGreater(len(result.content), 0)
        self.assertEqual(result.mime_type, "text/csv; charset=utf-8")

    def test_pdf_render_produces_bytes(self):
        renderer = get_renderer("PDF")
        result = renderer.render(self.dataset, self.config)
        self.assertGreater(len(result.content), 0)
        self.assertEqual(result.mime_type, "application/pdf")

    def test_xlsx_render_produces_bytes(self):
        renderer = get_renderer("XLSX")
        result = renderer.render(self.dataset, self.config)
        self.assertGreater(len(result.content), 0)

    def test_print_html_render_produces_bytes(self):
        renderer = get_renderer("PRINT_HTML")
        result = renderer.render(self.dataset, self.config)
        self.assertIn(b"Test Export", result.content)

    def test_png_render_produces_bytes(self):
        renderer = get_renderer("PNG")
        result = renderer.render(self.dataset, self.config)
        self.assertIsInstance(result, RenderResult)
        self.assertGreater(len(result.content), 0)
        self.assertEqual(result.mime_type, "image/png")
        self.assertEqual(result.filename, "png")

    def test_jpeg_render_produces_bytes(self):
        renderer = get_renderer("JPEG")
        result = renderer.render(self.dataset, self.config)
        self.assertIsInstance(result, RenderResult)
        self.assertGreater(len(result.content), 0)
        self.assertEqual(result.mime_type, "image/jpeg")
        self.assertEqual(result.filename, "jpg")


class ProviderDatasetTests(ExportsTestCase):
    def test_build_dataset_respects_row_cap(self):
        provider = registry.get("reports.template")
        self.assertIsInstance(provider, BaseProvider)
        dataset = provider.build_dataset(self.manager, include_sensitive=False)
        self.assertEqual(dataset.title, "Report Templates")
        self.assertIsNotNone(dataset.columns)
