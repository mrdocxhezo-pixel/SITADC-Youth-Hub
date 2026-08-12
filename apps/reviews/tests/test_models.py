"""Model tests for the ``reviews`` app (Phase 21)."""

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.reviews.models import (
    DelegationRecord,
    DigitalSignature,
    Review,
    ReviewChecklistResponse,
    ReviewConfiguration,
    ReviewDecision,
    ReviewDecisionType,
    ReviewStatus,
)

from .base import ReviewBaseTestCase


class ReviewModelTests(ReviewBaseTestCase):
    def test_str_review_number_and_report(self):
        review = self.make_assigned_review()
        self.assertIn(str(review.review_number), str(review))
        self.assertIn(review.report.reference_number, str(review))

    def test_default_status_pending_assignment(self):
        report = self.submit_report(self.make_report())
        review = Review.objects.create(
            report=report,
            created_by=self.admin,
        )
        self.assertEqual(review.status, ReviewStatus.PENDING_ASSIGNMENT)

    def test_review_number_sequence_per_report(self):
        report = self.submit_report(self.make_report())
        review = Review.objects.create(report=report, created_by=self.admin)
        self.assertEqual(review.review_number, 1)

    def test_is_overdue_true_after_due_date(self):
        review = self.make_assigned_review()
        review.due_date = timezone.now().date() - timedelta(days=1)
        self.assertTrue(review.is_overdue)

    def test_is_overdue_false_before_due_date(self):
        review = self.make_assigned_review()
        review.due_date = timezone.now().date() + timedelta(days=5)
        self.assertFalse(review.is_overdue)

    def test_is_overdue_false_when_completed(self):
        review = self.make_assigned_review()
        review.due_date = timezone.now().date() - timedelta(days=1)
        review.status = ReviewStatus.APPROVED
        self.assertFalse(review.is_overdue)

    def test_is_overdue_false_without_due_date(self):
        review = self.make_assigned_review()
        review.due_date = None
        self.assertFalse(review.is_overdue)

    def test_duration_days_none_before_start(self):
        review = self.make_assigned_review()
        self.assertIsNone(review.duration_days)

    def test_duration_days_computed_after_start(self):
        review = self.make_assigned_review()
        start = timezone.now() - timedelta(days=2)
        review.started_at = start
        review.save(update_fields=["started_at"])
        self.assertGreaterEqual(review.duration_days, 2)


class ReviewDecisionModelTests(ReviewBaseTestCase):
    def setUp(self):
        super().setUp()
        self.review = self.make_assigned_review()
        self.decision = ReviewDecision.objects.create(
            review=self.review,
            decision=ReviewDecisionType.APPROVED,
            reason="Approved",
            reviewer=self.reviewer,
            created_by=self.reviewer,
        )

    def test_decision_immutable_on_update(self):
        with self.assertRaises(ValidationError):
            self.decision.reason = "Changed"
            self.decision.save()

    def test_decision_immutable_on_delete(self):
        with self.assertRaises(ValidationError):
            self.decision.delete()

    def test_digital_signature_immutable(self):
        signature = DigitalSignature.objects.create(
            decision=self.decision,
            signer=self.reviewer,
            signature_type="TYPED",
            signature_data="Jane Reviewer",
            created_by=self.reviewer,
        )
        with self.assertRaises(ValidationError):
            signature.signature_data = "Mutated"
            signature.save()
        with self.assertRaises(ValidationError):
            signature.delete()

    def test_signature_str(self):
        signature = DigitalSignature.objects.create(
            decision=self.decision,
            signer=self.reviewer,
            signature_type="TYPED",
            signature_data="Jane Reviewer",
            created_by=self.reviewer,
        )
        self.assertIn(str(signature.signer), str(signature))


class ReviewChecklistResponseModelTests(ReviewBaseTestCase):
    def test_unique_review_item_constraint(self):
        from django.db import IntegrityError

        report = self.submit_report(self.make_report())
        review = Review.objects.create(report=report, created_by=self.admin)
        item = self.checklist.items.first()
        ReviewChecklistResponse.objects.create(
            review=review,
            item=item,
            created_by=self.reviewer,
        )
        with self.assertRaises(IntegrityError):
            ReviewChecklistResponse.objects.create(
                review=review,
                item=item,
                created_by=self.reviewer,
            )


class DelegationRecordModelTests(ReviewBaseTestCase):
    def test_is_expired_true_after_expiry(self):
        review = self.make_assigned_review()
        delegation = DelegationRecord.objects.create(
            review=review,
            delegated_by=self.admin,
            delegated_to=self.secondary,
            reason="Out of office",
            expires_at=timezone.now() - timedelta(days=1),
            created_by=self.admin,
        )
        self.assertTrue(delegation.is_expired)

    def test_is_expired_false_within_window(self):
        review = self.make_assigned_review()
        delegation = DelegationRecord.objects.create(
            review=review,
            delegated_by=self.admin,
            delegated_to=self.secondary,
            reason="Out of office",
            expires_at=timezone.now() + timedelta(days=5),
            created_by=self.admin,
        )
        self.assertFalse(delegation.is_expired)

    def test_is_expired_false_without_expiry(self):
        review = self.make_assigned_review()
        delegation = DelegationRecord.objects.create(
            review=review,
            delegated_by=self.admin,
            delegated_to=self.secondary,
            reason="Out of office",
            created_by=self.admin,
        )
        self.assertFalse(delegation.is_expired)


class ReviewConfigurationModelTests(ReviewBaseTestCase):
    def test_get_value_returns_default_when_missing(self):
        self.assertEqual(
            ReviewConfiguration.get_value("does-not-exist", "fallback"), "fallback"
        )

    def test_set_and_get_value(self):
        ReviewConfiguration.set_value("reminder_days_before", 3, "Reminder lead time")
        self.assertEqual(ReviewConfiguration.get_value("reminder_days_before"), 3)

    def test_set_value_updates_existing(self):
        ReviewConfiguration.set_value("max_extensions", 2)
        ReviewConfiguration.set_value("max_extensions", 4)
        self.assertEqual(ReviewConfiguration.get_value("max_extensions"), 4)
