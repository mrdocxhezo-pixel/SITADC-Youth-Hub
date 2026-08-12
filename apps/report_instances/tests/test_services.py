"""Service-layer tests for the ``report_instances`` app."""

from datetime import timedelta

from django.utils import timezone

from apps.report_instances.models import ReportComment, ReportSubmission
from apps.reports.constants import ReportStatus, ReportValidationStatus

from .base import ReportInstanceBaseTestCase


class ReportLifecycleServiceTest(ReportInstanceBaseTestCase):
    """Full lifecycle driven through the service layer."""

    def test_create_rejects_non_published_template(self):
        from apps.report_instances.services import create_report
        from apps.reports.constants import ReportStatus as TemplateStatus

        self.template.status = TemplateStatus.ARCHIVED
        self.template.save()
        with self.assertRaises(ValueError):
            create_report(template=self.template, title="X", owner=self.owner)

    def test_create_report(self):
        report = self.make_report(title="Lifecycle Report")
        self.assertEqual(report.status, ReportStatus.DRAFT)
        self.assertEqual(report.validation_status, ReportValidationStatus.NOT_VALIDATED)
        self.assertEqual(report.version_number, 1)
        self.assertEqual(report.category, self.template.category)
        self.assertIn("RPT", report.reference_number)
        self.assertEqual(report.timeline_events.first().event_type, "REPORT_CREATED")

    def test_update_report_moves_to_in_progress(self):
        from apps.report_instances.services import update_report

        report = self.make_report()
        update_report(report, title="Updated Title", updated_by=self.owner)
        report.refresh_from_db()
        self.assertEqual(report.title, "Updated Title")
        self.assertEqual(report.status, ReportStatus.IN_PROGRESS)

    def test_update_report_rejects_non_editable(self):
        from apps.report_instances.services import (
            submit_report,
            update_report,
            validate_report,
        )

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        with self.assertRaises(ValueError):
            update_report(report, title="Nope", updated_by=self.owner)

    def test_validate_passes_when_complete(self):
        from apps.report_instances.services import validate_report

        report = self.make_report()
        self.fill_report(report)
        result = validate_report(report, validated_by=self.owner)
        report.refresh_from_db()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.failed_rules, 0)
        self.assertEqual(report.status, ReportStatus.READY_FOR_SUBMISSION)
        self.assertEqual(report.validation_status, ReportValidationStatus.PASSED)

    def test_validate_fails_when_required_field_missing(self):
        from apps.report_instances.services import validate_report

        report = self.make_report()
        result = validate_report(report, validated_by=self.owner)
        report.refresh_from_db()
        self.assertFalse(result.is_valid)
        self.assertGreater(result.failed_rules, 0)
        self.assertEqual(report.status, ReportStatus.VALIDATION_FAILED)

    def test_submit_requires_ready_state(self):
        from apps.report_instances.services import submit_report

        report = self.make_report()
        with self.assertRaises(ValueError):
            submit_report(report, submitted_by=self.owner)

    def test_full_lifecycle_to_approval(self):
        from apps.report_instances.services import (
            approve_report,
            archive_report,
            restore_report,
            submit_report,
            validate_report,
            withdraw_report,
        )

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner, notes="First submission")
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        self.assertIsNotNone(report.submitted_at)

        withdraw_report(report, withdrawn_by=self.owner, reason="Not ready")
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.DRAFT)
        self.assertIsNone(report.submitted_at)
        self.assertEqual(report.submissions.filter(status="WITHDRAWN").count(), 1)

        # Re-run the lifecycle to approval.
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        approve_report(report, approved_by=self.reviewer, notes="Looks good")
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.APPROVED)
        self.assertIsNotNone(report.approved_at)

        archive_report(report, archived_by=self.reviewer)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.ARCHIVED)
        self.assertIsNotNone(report.archived_at)

        restore_report(report, restored_by=self.reviewer)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        self.assertIsNone(report.archived_at)

    def test_archive_rejects_draft(self):
        from apps.report_instances.services import archive_report

        report = self.make_report()
        with self.assertRaises(ValueError):
            archive_report(report, archived_by=self.owner)

    def test_restore_rejects_non_archived(self):
        from apps.report_instances.services import restore_report

        report = self.make_report()
        with self.assertRaises(ValueError):
            restore_report(report, restored_by=self.owner)


class ReportReturnReviewTest(ReportInstanceBaseTestCase):
    """Return-for-correction and resubmission flows."""

    def _submitted(self):
        from apps.report_instances.services import submit_report, validate_report

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        return report

    def test_return_then_resubmit(self):
        from apps.report_instances.services import resubmit_report, return_report

        report = self._submitted()
        return_report(report, returned_by=self.reviewer, reason="Fix section 1")
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.RETURNED_FOR_CORRECTION)
        self.assertTrue(report.is_editable)
        self.assertTrue(
            ReportComment.objects.filter(
                report=report, body__startswith="[RETURNED]"
            ).exists()
        )

        resubmit_report(report, resubmitted_by=self.owner)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
        self.assertEqual(report.submissions.count(), 2)

    def test_resubmit_rejects_non_returned(self):
        from apps.report_instances.services import resubmit_report

        report = self._submitted()
        with self.assertRaises(ValueError):
            resubmit_report(report, resubmitted_by=self.owner)

    def test_reject_and_approve_guards(self):
        from apps.report_instances.services import approve_report, reject_report

        report = self.make_report()
        with self.assertRaises(ValueError):
            approve_report(report, approved_by=self.reviewer)
        with self.assertRaises(ValueError):
            reject_report(report, rejected_by=self.reviewer)


class ReportSupportServiceTest(ReportInstanceBaseTestCase):
    """Evidence, attachments, comments, versions, exports, assignment."""

    def test_duplicate_report(self):
        from apps.report_instances.services import duplicate_report

        report = self.make_report(title="Original")
        copy = duplicate_report(report, duplicated_by=self.owner)
        self.assertNotEqual(copy.pk, report.pk)
        self.assertEqual(copy.title, "Copy of Original")
        self.assertEqual(copy.status, ReportStatus.DRAFT)
        self.assertEqual(copy.template, self.template)

    def test_add_evidence_and_attachment(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.report_instances.services import add_attachment, add_evidence

        report = self.make_report()
        file = SimpleUploadedFile("photo.jpg", b"bytes", content_type="image/jpeg")
        evidence = add_evidence(
            report,
            evidence_type="PHOTOGRAPH",
            file=file,
            original_filename="photo.jpg",
            file_size=file.size,
            mime_type=file.content_type or "",
            uploaded_by=self.owner,
        )
        self.assertEqual(evidence.evidence_type, "PHOTOGRAPH")
        self.assertFalse(evidence.is_verified)
        self.assertEqual(report.evidence_items.count(), 1)

        attachment = add_attachment(
            report,
            file=file,
            original_filename="doc.pdf",
            file_size=file.size,
            uploaded_by=self.owner,
        )
        self.assertEqual(attachment.original_filename, "doc.pdf")
        self.assertEqual(report.attachments.count(), 1)

    def test_verify_evidence(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from apps.report_instances.services import add_evidence, verify_evidence

        report = self.make_report()
        file = SimpleUploadedFile("doc.pdf", b"data", content_type="application/pdf")
        evidence = add_evidence(
            report,
            evidence_type="DOCUMENT",
            file=file,
            original_filename="doc.pdf",
            file_size=file.size,
            uploaded_by=self.owner,
        )
        verify_evidence(evidence, verified_by=self.reviewer)
        evidence.refresh_from_db()
        self.assertTrue(evidence.is_verified)
        self.assertEqual(evidence.verified_by, self.reviewer)

    def test_add_comment(self):
        from apps.report_instances.services import add_comment

        report = self.make_report()
        comment = add_comment(
            report, body="Please check", author=self.reviewer, is_internal=True
        )
        self.assertTrue(comment.is_internal)
        self.assertEqual(report.comments.count(), 1)
        self.assertEqual(
            report.timeline_events.filter(event_type="COMMENT_ADDED").count(),
            1,
        )

    def test_record_export(self):
        from apps.report_instances.services import record_export

        report = self.make_report()
        record_export(report, format="CSV", file=None, exported_by=self.owner)
        self.assertEqual(report.exports.count(), 1)
        self.assertEqual(report.exports.first().format, "CSV")

    def test_assign_reviewer(self):
        from apps.report_instances.services import assign_report

        report = self.make_report()
        assign_report(
            report,
            assigned_to=self.reviewer,
            assigned_by=self.owner,
            role="REVIEWER",
        )
        report.refresh_from_db()
        self.assertEqual(report.assigned_reviewer, self.reviewer)
        self.assertEqual(report.assignments.count(), 1)

    def test_schedule_reminder(self):
        from apps.report_instances.services import schedule_reminder

        report = self.make_report()
        reminder = schedule_reminder(
            report,
            reminder_type="DUE_SOON",
            recipient=self.owner,
            scheduled_at=timezone.now() + timedelta(days=1),
        )
        self.assertEqual(report.reminders.count(), 1)
        self.assertEqual(reminder.reminder_type, "DUE_SOON")

    def test_auto_save(self):
        from apps.report_instances.services import auto_save_report

        report = self.make_report()
        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        auto_save_report(
            report,
            section_data={str(section.pk): {str(field.pk): "draft"}},
            field_data={str(field.pk): "draft"},
            saved_by=self.owner,
        )
        self.assertEqual(report.field_responses.count(), 1)
        self.assertEqual(report.section_responses.count(), 1)

    def test_submission_records(self):
        from apps.report_instances.services import submit_report, validate_report

        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        self.assertEqual(ReportSubmission.objects.filter(report=report).count(), 1)
        self.assertEqual(report.submissions.first().submission_number, 1)
