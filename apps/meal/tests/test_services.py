"""Transactional service behaviour and RBAC enforcement tests."""

from datetime import date

from django.core.exceptions import PermissionDenied

from apps.meal.constants import (
    ComplaintStatus,
    CorrectiveActionStatus,
    FeedbackStatus,
    ReportStatus,
    ScorecardStatus,
    WorkflowStatus,
)
from apps.meal.exceptions import InvalidStatusTransition
from apps.meal.models import (
    Complaint,
    CorrectiveAction,
    Feedback,
    Indicator,
    MEALStatusHistory,
    MonitoringFinding,
    MonitoringVisit,
    PerformanceScorecard,
    TheoryOfChange,
)
from apps.meal.services import (
    AccountabilityService,
    FrameworkService,
    IndicatorService,
    MonitoringService,
    ReportService,
    ScorecardService,
)

from .base import MEALTestCase


class IndicatorServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.meal_officer = self.create_user("meal_officer")
        self.grant_permissions(
            self.meal_officer,
            "meal.create",
            "meal.update",
            "meal.view",
            "meal.submit",
            "meal.approve",
            "meal.manage_indicators",
            "meal.manage_accountability",
            "meal.manage_monitoring",
            "meal.manage_reports",
            "meal.manage_scorecards",
        )

    def test_create_indicator_assigns_reference_and_initial_status(self):
        indicator = IndicatorService(user=self.meal_officer).create(
            fields={
                "code": "ind_a",
                "title": "Youth trained",
                "description": "Count of youth trained.",
            },
            model=Indicator,
        )
        self.assertTrue(indicator.reference_number.startswith("IND-"))
        self.assertEqual(indicator.status, "DRAFT")
        self.assertEqual(indicator.created_by, self.meal_officer)

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            IndicatorService(user=self.viewer).create(
                fields={"code": "ind_b", "title": "No permission"},
                model=Indicator,
            )

    def test_activate_indicator_records_history(self):
        indicator = IndicatorService(user=self.meal_officer).create(
            fields={"code": "ind_c", "title": "Active indicator"},
            model=Indicator,
        )
        IndicatorService(user=self.meal_officer).activate(instance=indicator)
        indicator.refresh_from_db()
        self.assertEqual(indicator.status, "ACTIVE")
        self.assertTrue(
            MEALStatusHistory.objects.filter(
                entity_type="Indicator", entity_id=str(indicator.pk), to_status="ACTIVE"
            ).exists()
        )


class FrameworkServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.meal_officer = self.create_user("meal_officer")
        self.approver = self.create_user("approver")
        self.grant_permissions(
            self.meal_officer,
            "meal.create",
            "meal.update",
            "meal.view",
            "meal.submit",
            "meal.approve",
            "meal.manage_frameworks",
        )
        self.grant_permissions(self.approver, "meal.approve", "meal.view")

    def create_framework(self):
        return FrameworkService(user=self.meal_officer).create(
            fields={
                "title": "Strategic ToC",
                "strategic_goal": "Empowered communities",
            },
            model=TheoryOfChange,
        )

    def test_full_approval_workflow(self):
        toc = self.create_framework()
        self.assertEqual(toc.status, WorkflowStatus.DRAFT)
        FrameworkService(user=self.meal_officer).submit(instance=toc)
        toc.refresh_from_db()
        self.assertEqual(toc.status, WorkflowStatus.SUBMITTED)
        FrameworkService(user=self.approver).approve(instance=toc)
        toc.refresh_from_db()
        self.assertEqual(toc.status, WorkflowStatus.APPROVED)

    def test_invalid_transition_rejected(self):
        toc = self.create_framework()
        with self.assertRaises(InvalidStatusTransition):
            FrameworkService(user=self.meal_officer).approve(instance=toc)


class MonitoringServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.meal_officer = self.create_user("meal_officer")
        self.grant_permissions(
            self.meal_officer,
            "meal.create",
            "meal.view",
            "meal.manage_monitoring",
        )
        self.visit = MonitoringVisit.objects.create(
            reference_number="VIS-SVC-0001",
            visit_date=date(2026, 1, 10),
            created_by=self.meal_officer,
            updated_by=self.meal_officer,
        )

    def test_visit_lifecycle_and_finding(self):
        service = MonitoringService(user=self.meal_officer)
        service.begin_visit(instance=self.visit)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, "IN_PROGRESS")
        finding = service.create_finding(
            visit=self.visit, fields={"description": "Site is active"}
        )
        self.assertIsInstance(finding, MonitoringFinding)
        service.complete_visit(instance=self.visit)
        self.visit.refresh_from_db()
        self.assertEqual(self.visit.status, "COMPLETED")


class AccountabilityServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.officer = self.create_user("accountability_officer")
        self.grant_permissions(
            self.officer,
            "meal.create",
            "meal.update",
            "meal.view",
            "meal.manage_accountability",
        )

    def test_complaint_full_lifecycle(self):
        complaint = AccountabilityService(user=self.officer).create(
            fields={"description": "Missing allowance"},
            model=Complaint,
        )
        self.assertEqual(complaint.status, ComplaintStatus.RECEIVED)
        service = AccountabilityService(user=self.officer)
        service.resolve_complaint(instance=complaint, resolution="Paid the allowance.")
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.RESOLVED)
        self.assertEqual(complaint.resolution, "Paid the allowance.")
        service.close_complaint(instance=complaint)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, ComplaintStatus.CLOSED)

    def test_confidential_complaint_guarded(self):
        complaint = AccountabilityService(user=self.officer).create(
            fields={
                "description": "Confidential misconduct",
                "is_confidential": True,
            },
            model=Complaint,
        )
        restricted = self.create_user("restricted")
        self.grant_permissions(
            restricted,
            "meal.manage_accountability",
            "meal.view",
        )
        with self.assertRaises(PermissionDenied):
            AccountabilityService(user=restricted).update_complaint(
                instance=complaint, fields={"description": "Updated by non-viewer"}
            )

    def test_feedback_response_flow(self):
        feedback = AccountabilityService(user=self.officer).create(
            fields={"description": "Great training"},
            model=Feedback,
        )
        service = AccountabilityService(user=self.officer)
        service.respond_feedback(instance=feedback, response="Thank you!")
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.RESPONDED)
        service.close_feedback(instance=feedback)
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, FeedbackStatus.CLOSED)

    def test_corrective_action_complete_verify(self):
        complaint = AccountabilityService(user=self.officer).create(
            fields={"description": "Source complaint"},
            model=Complaint,
        )
        action = AccountabilityService(user=self.officer).create(
            fields={
                "title": "Fix data gap",
                "description": "Update registers",
                "complaint": complaint,
            },
            model=CorrectiveAction,
        )
        self.assertEqual(action.status, CorrectiveActionStatus.OPEN)
        service = AccountabilityService(user=self.officer)
        service.complete_corrective_action(
            instance=action, resolution="Registers updated."
        )
        action.refresh_from_db()
        self.assertEqual(action.status, CorrectiveActionStatus.COMPLETED)
        service.verify_corrective_action(instance=action)
        action.refresh_from_db()
        self.assertEqual(action.status, CorrectiveActionStatus.VERIFIED)


class ReportServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.prep = self.create_user("prep")
        self.approver = self.create_user("approver")
        self.grant_permissions(
            self.prep, "meal.create", "meal.view", "meal.submit", "meal.manage_reports"
        )
        self.grant_permissions(self.approver, "meal.approve", "meal.view")
        self.report = self.create_report(prepared_by=self.prep)

    def test_submit_and_approve(self):
        ReportService(user=self.prep).submit(instance=self.report)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.SUBMITTED)
        ReportService(user=self.approver).approve(instance=self.report)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.APPROVED)
        self.assertEqual(self.report.approved_by, self.approver)


class ScorecardServiceTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.officer = self.create_user("scorecard_officer")
        self.grant_permissions(
            self.officer, "meal.create", "meal.view", "meal.manage_scorecards"
        )
        self.scorecard = PerformanceScorecard.objects.create(
            reference_number="SCR-SVC-0001",
            title="Annual scorecard",
            period_label="2026",
            created_by=self.officer,
            updated_by=self.officer,
        )

    def test_publish_and_dimension(self):
        service = ScorecardService(user=self.officer)
        service.add_dimension(
            scorecard=self.scorecard,
            dimension="PROGRAM",
            label="Program performance",
            score=80,
        )
        service.publish(instance=self.scorecard)
        self.scorecard.refresh_from_db()
        self.assertEqual(self.scorecard.status, ScorecardStatus.PUBLISHED)
        self.assertEqual(self.scorecard.dimensions.count(), 1)
        self.assertGreaterEqual(self.scorecard.average_score, 80)
