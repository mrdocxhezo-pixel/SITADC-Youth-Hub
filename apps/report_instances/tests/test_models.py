"""Model tests for the ``report_instances`` app."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.reports.constants import ReportStatus

from .base import ReportInstanceBaseTestCase


class ReportModelTest(ReportInstanceBaseTestCase):
    """Tests for the ``Report`` model state helpers and immutability."""

    def test_is_draft(self):
        report = self.make_report()
        self.assertEqual(report.status, ReportStatus.DRAFT)
        self.assertTrue(report.is_draft)
        self.assertTrue(report.is_editable)
        self.assertFalse(report.is_submitted)
        self.assertFalse(report.is_approved)

    def test_editable_states(self):
        from apps.report_instances.services import validate_report

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.READY_FOR_SUBMISSION)
        self.assertFalse(report.is_editable)

    def test_reference_number_uniqueness(self):
        from apps.report_instances.models import Report

        report = self.make_report(title="First")
        with self.assertRaises(IntegrityError):
            Report.objects.create(
                reference_number=report.reference_number,
                title="Duplicate",
                template=self.template,
                owner=self.owner,
            )

    def test_str(self):
        report = self.make_report(title="Model Title")
        self.assertIn(report.reference_number, str(report))
        self.assertIn("Model Title", str(report))


class ImmutableHistoryTest(ReportInstanceBaseTestCase):
    """Status history and timeline entries must be immutable."""

    def test_status_history_immutable(self):
        from apps.report_instances.models import ReportStatusHistory

        report = self.make_report()
        record = ReportStatusHistory.objects.create(
            report=report,
            from_status=ReportStatus.DRAFT,
            to_status=ReportStatus.IN_PROGRESS,
            action="UPDATED",
            performed_by=self.owner,
        )
        with self.assertRaises(ValidationError):
            record.save()
        with self.assertRaises(ValidationError):
            record.delete()

    def test_timeline_event_immutable(self):
        from apps.report_instances.models import ReportTimelineEvent

        report = self.make_report()
        event = ReportTimelineEvent.objects.create(
            report=report,
            event_type="REPORT_CREATED",
            description="Created",
            actor=self.owner,
        )
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()


class ReportVersionTest(ReportInstanceBaseTestCase):
    """Version snapshots are created on submission."""

    def test_submission_creates_version(self):
        from apps.report_instances.services import submit_report, validate_report

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        report.refresh_from_db()

        self.assertEqual(report.versions.count(), 1)
        version = report.versions.first()
        self.assertEqual(version.version_number, 1)
        self.assertEqual(version.status_at_version, ReportStatus.SUBMITTED)
        self.assertIn("field_data", version.snapshot)
