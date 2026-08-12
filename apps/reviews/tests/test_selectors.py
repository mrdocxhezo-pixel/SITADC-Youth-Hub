"""Selector tests for the ``reviews`` app (Phase 21)."""

from datetime import timedelta

from django.utils import timezone

from apps.reviews import selectors, services
from apps.reviews.models import ReviewStatus

from .base import ReviewBaseTestCase


class ReviewSelectorTests(ReviewBaseTestCase):
    def test_get_reviews_for_user_scoped_to_assignments(self):
        self.make_assigned_review(reviewer=self.reviewer)
        self.make_assigned_review(reviewer=self.secondary)
        qs = selectors.get_reviews_for_user(self.reviewer)
        self.assertEqual(qs.count(), 1)

    def test_get_pending_reviews_includes_active_statuses(self):
        self.make_review(primary_reviewer=self.reviewer)
        self.make_assigned_review()
        qs = selectors.get_pending_reviews()
        self.assertGreaterEqual(qs.count(), 2)

    def test_get_overdue_reviews_filters_by_due_date(self):
        overdue = self.make_assigned_review()
        overdue.due_date = timezone.now().date() - timedelta(days=3)
        overdue.save(update_fields=["due_date"])
        on_time = self.make_assigned_review()
        on_time.due_date = timezone.now().date() + timedelta(days=3)
        on_time.save(update_fields=["due_date"])
        qs = selectors.get_overdue_reviews()
        self.assertTrue(qs.filter(pk=overdue.pk).exists())
        self.assertFalse(qs.filter(pk=on_time.pk).exists())

    def test_get_completed_reviews(self):
        completed = self.make_assigned_review()
        services.approve_report(completed, self.reviewer, "Ok.")
        active = self.make_assigned_review()
        qs = selectors.get_completed_reviews()
        self.assertTrue(qs.filter(pk=completed.pk).exists())
        self.assertFalse(qs.filter(pk=active.pk).exists())

    def test_get_reviews_by_status(self):
        review = self.make_assigned_review()
        self.assertEqual(
            selectors.get_reviews_by_status(ReviewStatus.ASSIGNED).count(), 1
        )
        self.assertFalse(
            selectors.get_reviews_by_status(ReviewStatus.APPROVED)
            .filter(pk=review.pk)
            .exists()
        )


class CommentSelectorTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()

    def test_get_unresolved_comments_excludes_resolved(self):
        services.add_review_comment(self.review, self.reviewer, "Open comment")
        resolved = services.add_review_comment(
            self.review, self.reviewer, "Resolved comment"
        )
        services.resolve_comment(resolved, self.reviewer)
        qs = selectors.get_unresolved_comments(self.review)
        self.assertEqual(qs.count(), 1)
        self.assertFalse(qs.filter(pk=resolved.pk).exists())


class ChecklistSelectorTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_review(checklist=self.checklist)

    def test_get_checklist_progress_counts(self):
        response = self.review.checklist_responses.first()
        services.complete_checklist_item(response, self.reviewer, is_completed=True)
        progress = selectors.get_checklist_progress(self.review)
        self.assertEqual(progress["total"], 2)
        self.assertEqual(progress["completed"], 1)
        self.assertEqual(progress["percentage"], 50)

    def test_get_available_checklists_filters_by_category(self):
        qs = selectors.get_available_checklists(self.category)
        self.assertTrue(qs.filter(pk=self.checklist.pk).exists())


class EscalationSelectorTests(ReviewBaseTestCase):
    def test_get_unresolved_escalations(self):
        review = self.make_assigned_review()
        services.escalate_review(review, self.reviewer, "Needs attention.")
        qs = selectors.get_unresolved_escalations()
        self.assertTrue(qs.filter(review=review).exists())


class DelegationSelectorTests(ReviewBaseTestCase):
    def test_get_active_delegations_for_user(self):
        review = self.make_assigned_review()
        services.delegate_review(
            review,
            self.reviewer,
            self.secondary,
            "Handover",
            expires_at=timezone.now() + timedelta(days=3),
        )
        qs = selectors.get_active_delegations(self.secondary)
        self.assertEqual(qs.count(), 1)


class ConfigurationSelectorTests(ReviewBaseTestCase):
    def test_get_configuration_value(self):
        services.ReviewConfiguration.set_value("test_key", 42)
        self.assertEqual(selectors.get_configuration_value("test_key"), 42)
        self.assertEqual(
            selectors.get_configuration_value("missing", "default"), "default"
        )
