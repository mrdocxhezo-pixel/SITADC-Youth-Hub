"""Service tests for the ``reviews`` app (Phase 21)."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.reports.constants import ReportStatus
from apps.reviews import services
from apps.reviews.models import (
    CommentType,
    EscalationTrigger,
    ReviewDecisionType,
    ReviewerRole,
    ReviewStatus,
)

from .base import ReviewBaseTestCase


class CreateReviewServiceTests(ReviewBaseTestCase):
    def test_create_review_rejects_draft_report(self):
        report = self.make_report()
        with self.assertRaises(ValidationError):
            services.create_review(report, created_by=self.admin)

    def test_create_review_accepts_submitted_report(self):
        report = self.submit_report(self.make_report())
        review = services.create_review(report=report, created_by=self.admin)
        self.assertEqual(review.status, ReviewStatus.PENDING_ASSIGNMENT)
        self.assertEqual(review.report, report)

    def test_create_review_sets_report_under_review(self):
        report = self.submit_report(self.make_report())
        services.create_review(report, created_by=self.admin)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.UNDER_REVIEW)

    def test_create_review_with_primary_reviewer_sets_assigned(self):
        report = self.submit_report(self.make_report())
        review = services.create_review(
            report=report,
            primary_reviewer=self.reviewer,
            created_by=self.admin,
        )
        review.refresh_from_db()
        self.assertEqual(review.status, ReviewStatus.ASSIGNED)
        self.assertEqual(review.primary_reviewer, self.reviewer)
        self.assertTrue(
            review.assignments.filter(
                assigned_to=self.reviewer, role=ReviewerRole.PRIMARY
            ).exists()
        )

    def test_create_review_populates_checklist_responses(self):
        review = self.make_review(checklist=self.checklist)
        self.assertEqual(review.checklist_responses.count(), 2)

    def test_review_number_increments_per_report(self):
        report = self.submit_report(self.make_report())
        first = services.create_review(report, created_by=self.admin)
        self.assertEqual(first.review_number, 1)
        report.status = ReportStatus.SUBMITTED
        report.save(update_fields=["status"])
        second = services.create_review(report, created_by=self.admin)
        self.assertEqual(second.review_number, 2)


class AssignmentServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_review(primary_reviewer=self.reviewer)

    def test_assign_reviewer_adds_assignment(self):
        assignment = services.assign_reviewer(
            self.review,
            self.secondary,
            role=ReviewerRole.SECONDARY,
            assigned_by=self.admin,
        )
        self.assertEqual(assignment.role, ReviewerRole.SECONDARY)
        self.assertEqual(
            self.review.assignments.filter(assigned_to=self.secondary).count(), 1
        )

    def test_assign_primary_updates_primary_reviewer_and_status(self):
        self.review.primary_reviewer = None
        self.review.status = ReviewStatus.PENDING_ASSIGNMENT
        self.review.save(update_fields=["primary_reviewer", "status"])
        services.assign_reviewer(self.review, self.secondary, assigned_by=self.admin)
        self.review.refresh_from_db()
        self.assertEqual(self.review.primary_reviewer, self.secondary)
        self.assertEqual(self.review.status, ReviewStatus.ASSIGNED)

    def test_accept_review_requires_assignment(self):
        with self.assertRaises(ValidationError):
            services.accept_review(self.review, self.other)

    def test_accept_review_sets_accepted(self):
        services.accept_review(self.review, self.reviewer)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ACCEPTED)
        assignment = self.review.assignments.get(assigned_to=self.reviewer)
        self.assertIsNotNone(assignment.accepted_at)

    def test_start_review_sets_under_review_and_started_at(self):
        before = timezone.now() - timedelta(minutes=1)
        services.start_review(self.review, self.reviewer)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.UNDER_REVIEW)
        self.assertIsNotNone(self.review.started_at)
        self.assertGreater(self.review.started_at, before)


class CommentServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_add_general_comment(self):
        comment = services.add_review_comment(self.review, self.reviewer, "Looks good.")
        self.assertEqual(comment.comment_type, CommentType.GENERAL)
        self.assertFalse(comment.is_internal)

    def test_add_internal_comment(self):
        comment = services.add_review_comment(
            self.review,
            self.reviewer,
            "Internal note",
            is_internal=True,
        )
        self.assertTrue(comment.is_internal)

    def test_resolve_comment_records_resolver(self):
        comment = services.add_review_comment(self.review, self.reviewer, "Fix this.")
        services.resolve_comment(comment, self.secondary)
        comment.refresh_from_db()
        self.assertTrue(comment.is_resolved)
        self.assertEqual(comment.resolved_by, self.secondary)


class ChecklistServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_review(checklist=self.checklist)

    def test_complete_checklist_item(self):
        response = self.review.checklist_responses.first()
        services.complete_checklist_item(
            response, self.reviewer, is_completed=True, score=4, notes="ok"
        )
        response.refresh_from_db()
        self.assertTrue(response.is_completed)
        self.assertEqual(response.score, 4)
        self.assertEqual(response.reviewed_by, self.reviewer)

    def test_complete_checklist_requires_all_items(self):
        first = self.review.checklist_responses.first()
        services.complete_checklist_item(first, self.reviewer, is_completed=True)
        with self.assertRaises(ValidationError):
            services.complete_checklist(self.review, self.reviewer)

    def test_complete_checklist_when_all_done(self):
        for response in self.review.checklist_responses.all():
            services.complete_checklist_item(response, self.reviewer, is_completed=True)
        services.complete_checklist(self.review, self.reviewer)
        self.review.refresh_from_db()
        self.assertTrue(self.review.checklist_completed)

    def test_complete_checklist_rejects_empty(self):
        review = self.make_assigned_review()
        with self.assertRaises(ValidationError):
            services.complete_checklist(review, self.reviewer)


class DecisionServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_approve_sets_review_and_report_approved(self):
        services.approve_report(self.review, self.reviewer, "All good.")
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.APPROVED)
        self.assertEqual(self.review.decision, ReviewDecisionType.APPROVED)
        report = self.review.report
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.APPROVED)
        self.assertIsNotNone(report.approved_at)

    def test_approve_with_signature_creates_signed_decision(self):
        services.approve_report(
            self.review,
            self.reviewer,
            "Approved with typed signature.",
            signature_data="Jane Reviewer",
        )
        decision = self.review.decisions.first()
        self.assertTrue(decision.signatures.exists())
        signature = decision.signatures.first()
        self.assertEqual(signature.signer, self.reviewer)

    def test_reject_requires_reason(self):
        with self.assertRaises(ValidationError):
            services.reject_report(self.review, self.reviewer, "")

    def test_reject_sets_review_and_report_rejected(self):
        services.reject_report(self.review, self.reviewer, "Insufficient detail.")
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.REJECTED)
        report = self.review.report
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.REJECTED)

    def test_return_for_correction_requires_reason(self):
        with self.assertRaises(ValidationError):
            services.return_for_correction(self.review, self.reviewer, "")

    def test_return_for_correction_updates_report(self):
        services.return_for_correction(
            self.review, self.reviewer, "Please add more evidence."
        )
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.RETURNED_FOR_CORRECTION)
        report = self.review.report
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.RETURNED_FOR_CORRECTION)

    def test_make_decision_records_conditions(self):
        services.make_decision(
            self.review,
            self.reviewer,
            ReviewDecisionType.APPROVED_WITH_CONDITIONS,
            "Approved with conditions.",
            conditions="Submit final figures.",
        )
        decision = self.review.decisions.first()
        self.assertEqual(decision.decision, ReviewDecisionType.APPROVED_WITH_CONDITIONS)
        self.assertEqual(decision.conditions, "Submit final figures.")
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.CONDITIONALLY_APPROVED)

    def test_decisions_are_immutable_history(self):
        services.approve_report(self.review, self.reviewer, "Ok.")
        self.assertEqual(self.review.decisions.count(), 1)


class EscalationServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_escalate_sets_status_and_event(self):
        escalation = services.escalate_review(
            self.review,
            self.reviewer,
            "Needs executive input.",
            trigger=EscalationTrigger.GOVERNANCE,
        )
        self.assertEqual(escalation.trigger, EscalationTrigger.GOVERNANCE)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.ESCALATED)
        self.assertTrue(self.review.sla_events.filter(event_type="ESCALATED").exists())


class DelegationServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_delegate_creates_assignment_and_status(self):
        delegation = services.delegate_review(
            self.review,
            self.reviewer,
            self.secondary,
            "Out of office.",
        )
        self.assertEqual(delegation.delegated_to, self.secondary)
        self.review.refresh_from_db()
        self.assertEqual(self.review.status, ReviewStatus.DELEGATED)
        self.assertTrue(
            self.review.assignments.filter(
                assigned_to=self.secondary,
                role=ReviewerRole.SECONDARY,
            ).exists()
        )


class SLAServiceTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_check_sla_compliance_overdue_creates_event(self):
        self.review.due_date = timezone.now().date() - timedelta(days=2)
        self.review.save(update_fields=["due_date"])
        result = services.check_sla_compliance(self.review)
        self.assertTrue(result["is_overdue"])
        self.assertTrue(self.review.sla_events.filter(event_type="OVERDUE").exists())

    def test_check_sla_compliance_not_overdue(self):
        self.review.due_date = timezone.now().date() + timedelta(days=5)
        self.review.save(update_fields=["due_date"])
        result = services.check_sla_compliance(self.review)
        self.assertFalse(result["is_overdue"])
        self.assertFalse(self.review.sla_events.filter(event_type="OVERDUE").exists())

    def test_send_sla_reminders_targets_due_today(self):
        target = timezone.now().date() + timedelta(days=2)
        self.review.due_date = target
        self.review.save(update_fields=["due_date"])
        count = services.send_sla_reminders()
        self.assertGreaterEqual(count, 1)
        self.assertTrue(
            self.review.sla_events.filter(event_type="REMINDER_SENT").exists()
        )

    def test_send_sla_reminders_skips_completed(self):
        target = timezone.now().date() + timedelta(days=2)
        self.review.due_date = target
        self.review.status = ReviewStatus.APPROVED
        self.review.save(update_fields=["due_date", "status"])
        count = services.send_sla_reminders()
        self.assertEqual(count, 0)


class ReviewerStatsServiceTests(ReviewBaseTestCase):
    def test_get_reviewer_stats_counts_assignments(self):
        self.make_assigned_review(reviewer=self.reviewer)
        self.make_assigned_review(reviewer=self.reviewer)
        stats = services.get_reviewer_stats(self.reviewer)
        self.assertEqual(stats["total_assigned"], 2)

    def test_get_review_dashboard_stats(self):
        self.make_assigned_review()
        self.make_assigned_review()
        stats = services.get_review_dashboard_stats()
        self.assertGreaterEqual(stats["total_reviews"], 2)
        self.assertGreaterEqual(stats["in_progress"], 0)
