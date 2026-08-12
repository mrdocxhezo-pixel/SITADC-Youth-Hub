"""Model-level tests for the Export Engine."""

from __future__ import annotations

from datetime import timedelta

from django.utils import timezone

from apps.exports.models import (
    CONFIGURATION_SINGLETON_KEY,
    ExportActivity,
    ExportConfiguration,
    ExportRequest,
    ExportStatus,
)

from .base import ExportsTestCase


class ExportConfigurationTests(ExportsTestCase):
    def test_load_creates_singleton_with_defaults(self):
        config = ExportConfiguration.load()
        self.assertEqual(config.singleton_key, CONFIGURATION_SINGLETON_KEY)
        self.assertGreater(config.max_sync_rows, 0)
        self.assertGreater(config.download_expiry_hours, 0)

    def test_load_returns_same_row(self):
        ExportConfiguration.load()
        ExportConfiguration.load()
        self.assertEqual(
            ExportConfiguration.objects.filter(
                singleton_key=CONFIGURATION_SINGLETON_KEY
            ).count(),
            1,
        )

    def test_save_forces_singleton_key(self):
        config = ExportConfiguration.load()
        config.singleton_key = "tampered"
        config.save()
        config.refresh_from_db()
        self.assertEqual(config.singleton_key, CONFIGURATION_SINGLETON_KEY)


class ExportRequestModelTests(ExportsTestCase):
    def setUp(self):
        self.config = ExportConfiguration.load()
        self.export = ExportRequest.objects.create(
            reference_number="SITADC-EXP-2026-000001",
            requested_by=self.viewer,
            source_type="REPORT",
            format="PDF",
            status=ExportStatus.COMPLETED,
            storage_path="exports/test/file.pdf",
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_is_downloadable_requires_completed_and_path(self):
        self.assertTrue(self.export.is_downloadable)

    def test_is_downloadable_false_when_expired(self):
        self.export.expires_at = timezone.now() - timedelta(hours=1)
        self.export.save()
        self.assertFalse(self.export.is_downloadable)

    def test_is_finished_true_for_terminal_states(self):
        self.assertTrue(self.export.is_finished)

    def test_mark_expired_transitions_and_clears_metadata(self):
        from unittest.mock import patch

        with patch(
            "apps.exports.services.ExportFileService.delete_export_file"
        ) as deleter:
            self.export.mark_expired()
        deleter.assert_called_once()
        self.export.refresh_from_db()
        self.assertEqual(self.export.status, ExportStatus.EXPIRED)
        self.assertEqual(self.export.filename, "")


class ExportActivityImmutabilityTests(ExportsTestCase):
    def setUp(self):
        self.export = ExportRequest.objects.create(
            reference_number="SITADC-EXP-2026-000002",
            requested_by=self.viewer,
            source_type="REPORT",
            format="PDF",
            status=ExportStatus.QUEUED,
        )
        self.activity = ExportActivity.record(
            request=self.export,
            action="REQUESTED",
            actor=self.viewer,
            details={"source": "REPORT"},
        )

    def test_record_creates_timeline(self):
        self.assertEqual(self.export.activity.count(), 1)
        self.assertEqual(self.activity.action, "REQUESTED")

    def test_cannot_update_activity(self):
        from django.core.exceptions import ValidationError

        self.activity.details = {"tampered": True}
        with self.assertRaises(ValidationError):
            self.activity.save()

    def test_cannot_delete_activity(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            self.activity.delete()
