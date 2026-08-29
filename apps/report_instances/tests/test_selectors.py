"""Selector tests for the ``report_instances`` app."""

from apps.report_instances.selectors import (
    get_all_reports,
    get_approved_reports,
    get_archived_reports,
    get_draft_reports,
    get_overdue_reports,
    get_reports_by_owner,
    get_reports_by_reviewer,
    get_reports_pending_review,
    get_submitted_reports,
)
from apps.report_instances.services import (
    approve_report,
    archive_report,
    assign_report,
    submit_report,
    validate_report,
)
from apps.reports.constants import ReportStatus

from .base import ReportInstanceBaseTestCase


class ReportSelectorTest(ReportInstanceBaseTestCase):
    """Queryset selectors respect status, owner and reviewer scoping."""

    def _submitted(self, owner=None, assigned=False):
        report = self.make_report(owner=owner)
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        if assigned:
            assign_report(
                report,
                assigned_to=self.reviewer,
                assigned_by=self.owner,
                role="REVIEWER",
            )
        return report

    def test_get_all_reports(self):
        self.make_report(title="One")
        self.make_report(title="Two", owner=self.other)
        self.assertEqual(get_all_reports().count(), 2)

    def test_get_draft_and_submitted(self):
        self.make_report(title="Draft")
        self._submitted()
        self.assertEqual(get_draft_reports().count(), 1)
        self.assertEqual(get_submitted_reports().count(), 1)

    def test_reports_by_owner(self):
        self.make_report(title="Mine")
        self.make_report(title="Theirs", owner=self.other)
        self.assertEqual(get_reports_by_owner(self.owner).count(), 1)
        self.assertEqual(get_reports_by_owner(self.other).count(), 1)

    def test_pending_review_scopes_by_reviewer(self):
        self._submitted(assigned=True)
        self.assertEqual(get_reports_pending_review(self.reviewer).count(), 1)
        self.assertEqual(get_reports_pending_review(self.other).count(), 0)

    def test_approved_and_archived(self):
        report = self._submitted(assigned=True)
        approve_report(report, approved_by=self.reviewer)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.APPROVED)
        self.assertEqual(get_approved_reports().count(), 1)

        archive_report(report, archived_by=self.reviewer)
        report.refresh_from_db()
        self.assertEqual(get_archived_reports().count(), 1)

    def test_get_overdue_reports(self):
        import datetime

        from django.utils import timezone

        report = self.make_report(title="Overdue")
        # Anchor on the same clock the selector uses (UTC when USE_TZ) so
        # local-timezone offsets cannot push this out of the overdue window.
        report.due_date = timezone.now().date() - datetime.timedelta(days=1)
        report.save()
        overdue = get_overdue_reports()
        self.assertIn(report, overdue)

    def test_get_reports_by_reviewer(self):
        report = self._submitted(assigned=True)
        self.assertIn(report, get_reports_by_reviewer(self.reviewer))
