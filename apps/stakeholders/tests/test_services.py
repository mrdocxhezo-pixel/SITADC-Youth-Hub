"""Transactional stakeholder service and calculation tests."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import ClassVar
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.references.constants import ReferenceNumberStatus
from apps.references.models import GeneratedReferenceNumber
from apps.stakeholders.constants import (
    AgreementStatus,
    CommitmentStatus,
    CommunicationChannel,
    CommunicationDirection,
    ContributionStatus,
    DueDiligenceStatus,
    EngagementStatus,
    EngagementType,
    ReferenceDataKind,
    RenewalStatus,
    StakeholderStatus,
)
from apps.stakeholders.models import Stakeholder, StakeholderAgreementVersion
from apps.stakeholders.services import (
    AGREEMENT_TRANSITIONS,
    STAKEHOLDER_TRANSITIONS,
    StakeholderAgreementService,
    StakeholderAssessmentService,
    StakeholderCommitmentService,
    StakeholderCommunicationService,
    StakeholderContactService,
    StakeholderContributionService,
    StakeholderDueDiligenceService,
    StakeholderEngagementService,
    StakeholderPerformanceService,
    StakeholderRiskService,
    StakeholderService,
    calculate_assessment_matrix,
    calculate_weighted_performance,
)

from .base import StakeholderTestCase


class StakeholderCreationServiceTests(StakeholderTestCase):
    def test_create_reserves_assigns_reference_and_initial_history(self):
        stakeholder = StakeholderService(user=self.manager).create(
            legal_name="Created Through Service"
        )
        generated = GeneratedReferenceNumber.objects.get(
            reference_number=stakeholder.reference_number
        )
        self.assertEqual(generated.status, ReferenceNumberStatus.ASSIGNED)
        self.assertEqual(generated.record_id, stakeholder.pk)
        self.assertEqual(stakeholder.status_history.count(), 1)

    def test_create_rolls_back_profile_and_reference_when_assignment_fails(self):
        before_references = GeneratedReferenceNumber.objects.count()
        with (
            patch(
                "apps.stakeholders.services._confirm_reference",
                side_effect=RuntimeError("assignment failed"),
            ),
            self.assertRaises(RuntimeError),
        ):
            StakeholderService(user=self.manager).create(
                legal_name="Rolled Back Stakeholder"
            )
        self.assertFalse(
            Stakeholder.all_objects.filter(
                legal_name="Rolled Back Stakeholder"
            ).exists()
        )
        self.assertEqual(GeneratedReferenceNumber.objects.count(), before_references)

    def test_duplicate_detection_is_case_insensitive_for_name_and_registration(self):
        self.create_stakeholder(
            legal_name="Known Partner", registration_number="PACRA-100"
        )
        service = StakeholderService(user=self.manager)
        with self.assertRaises(ValidationError):
            service.create(legal_name="known partner")
        with self.assertRaises(ValidationError):
            service.create(legal_name="Different Name", registration_number="pacra-100")


class StakeholderLifecycleServiceTests(StakeholderTestCase):
    expected_transitions: ClassVar[dict[str, set[str]]] = {
        StakeholderStatus.PROSPECT: {
            StakeholderStatus.IDENTIFIED,
            StakeholderStatus.INACTIVE,
        },
        StakeholderStatus.IDENTIFIED: {
            StakeholderStatus.PROSPECT,
            StakeholderStatus.UNDER_ASSESSMENT,
            StakeholderStatus.CONTACTED,
        },
        StakeholderStatus.UNDER_ASSESSMENT: {
            StakeholderStatus.CONTACTED,
            StakeholderStatus.PROSPECT,
            StakeholderStatus.SUSPENDED,
        },
        StakeholderStatus.CONTACTED: {
            StakeholderStatus.ENGAGED,
            StakeholderStatus.DORMANT,
            StakeholderStatus.SUSPENDED,
        },
        StakeholderStatus.ENGAGED: {
            StakeholderStatus.NEGOTIATING,
            StakeholderStatus.ACTIVE,
            StakeholderStatus.DORMANT,
            StakeholderStatus.SUSPENDED,
        },
        StakeholderStatus.NEGOTIATING: {
            StakeholderStatus.PENDING_AGREEMENT,
            StakeholderStatus.ENGAGED,
            StakeholderStatus.CLOSED,
        },
        StakeholderStatus.PENDING_AGREEMENT: {
            StakeholderStatus.ACTIVE,
            StakeholderStatus.NEGOTIATING,
            StakeholderStatus.CLOSED,
        },
        StakeholderStatus.ACTIVE: {
            StakeholderStatus.DORMANT,
            StakeholderStatus.INACTIVE,
            StakeholderStatus.SUSPENDED,
            StakeholderStatus.COMPLETED,
            StakeholderStatus.CLOSED,
        },
        StakeholderStatus.DORMANT: {
            StakeholderStatus.ENGAGED,
            StakeholderStatus.ACTIVE,
            StakeholderStatus.CLOSED,
        },
        StakeholderStatus.INACTIVE: {
            StakeholderStatus.ACTIVE,
            StakeholderStatus.CLOSED,
        },
        StakeholderStatus.SUSPENDED: {
            StakeholderStatus.ACTIVE,
            StakeholderStatus.INACTIVE,
            StakeholderStatus.CLOSED,
            StakeholderStatus.BLACKLISTED,
        },
        StakeholderStatus.COMPLETED: {StakeholderStatus.CLOSED},
        StakeholderStatus.CLOSED: set(),
        StakeholderStatus.BLACKLISTED: set(),
        StakeholderStatus.ARCHIVED: set(),
    }

    def test_transition_map_is_exact(self):
        self.assertEqual(STAKEHOLDER_TRANSITIONS, self.expected_transitions)

    def test_valid_transition_records_exact_history(self):
        stakeholder = self.create_stakeholder(status=StakeholderStatus.ENGAGED)
        updated = StakeholderService(user=self.manager).change_status(
            stakeholder, StakeholderStatus.ACTIVE, "Partnership verified"
        )
        history = updated.status_history.get()
        self.assertEqual(updated.status, StakeholderStatus.ACTIVE)
        self.assertEqual(history.from_status, StakeholderStatus.ENGAGED)
        self.assertEqual(history.to_status, StakeholderStatus.ACTIVE)
        self.assertEqual(history.reason, "Partnership verified")
        self.assertEqual(updated.verified_by, self.manager)

    def test_invalid_transition_and_blank_reason_do_not_mutate(self):
        stakeholder = self.create_stakeholder()
        service = StakeholderService(user=self.manager)
        with self.assertRaises(ValidationError):
            service.change_status(
                stakeholder, StakeholderStatus.ACTIVE, "Skipped steps"
            )
        with self.assertRaises(ValidationError):
            service.change_status(stakeholder, StakeholderStatus.IDENTIFIED, " ")
        stakeholder.refresh_from_db()
        self.assertEqual(stakeholder.status, StakeholderStatus.PROSPECT)
        self.assertFalse(stakeholder.status_history.exists())

    def test_archive_and_restore_preserve_history(self):
        stakeholder = self.create_stakeholder(status=StakeholderStatus.ENGAGED)
        service = StakeholderService(user=self.manager)
        service.archive(stakeholder, "Relationship paused")
        from apps.stakeholders.selectors import visible_stakeholders

        self.assertFalse(
            visible_stakeholders(self.manager).filter(pk=stakeholder.pk).exists()
        )
        archived = Stakeholder.all_objects.get(pk=stakeholder.pk)
        restored = service.restore(archived, "Relationship reopened")
        self.assertFalse(restored.is_archived)
        self.assertEqual(restored.status, StakeholderStatus.INACTIVE)
        self.assertEqual(restored.status_history.count(), 2)


class AssessmentAndPerformanceTests(StakeholderTestCase):
    def test_assessment_formula_classifies_and_averages_five_core_scores(self):
        result = calculate_assessment_matrix(
            influence_score=5,
            interest_score=4,
            power_score=3,
            impact_score=2,
            strategic_importance_score=1,
        )
        self.assertEqual(result["average_score"], Decimal("3.00"))
        self.assertEqual(result["completeness_percentage"], Decimal("100.00"))
        self.assertEqual(result["classification"], "MANAGE_CLOSELY")
        self.assertEqual(result["missing_fields"], [])

    def test_assessment_missing_data_is_listed_and_never_imputed(self):
        result = calculate_assessment_matrix(influence_score=4, power_score=2)
        self.assertEqual(result["average_score"], Decimal("3.00"))
        self.assertEqual(result["completeness_percentage"], Decimal("40.00"))
        self.assertEqual(result["classification"], "INSUFFICIENT_DATA")
        self.assertIn("interest_score", result["missing_fields"])
        self.assertIn("No values were imputed", result["matrix_explanation"])

    def test_assessment_service_assigns_a_reference(self):
        assessment = StakeholderAssessmentService(user=self.manager).record(
            self.create_stakeholder(), influence_score=2, interest_score=4
        )
        self.assertEqual(assessment.classification, "KEEP_INFORMED")
        self.assertTrue(
            GeneratedReferenceNumber.objects.filter(
                reference_number=assessment.reference_number,
                status=ReferenceNumberStatus.ASSIGNED,
            ).exists()
        )

    def test_weighted_performance_uses_present_weights_and_reports_missing(self):
        from apps.stakeholders.models import StakeholderPerformanceDimension

        StakeholderPerformanceDimension.objects.all().delete()
        first = StakeholderPerformanceDimension.objects.create(
            code="quality", name="Quality", weight=Decimal("1"), order=1
        )
        StakeholderPerformanceDimension.objects.create(
            code="delivery", name="Delivery", weight=Decimal("3"), order=2
        )
        dimensions = list(StakeholderPerformanceDimension.objects.all())
        result = calculate_weighted_performance(dimensions, {first.code: 80})
        self.assertEqual(result["weighted_score"], Decimal("80.00"))
        self.assertEqual(result["completeness_percentage"], Decimal("25.00"))
        self.assertEqual(result["missing_dimensions"], ["delivery"])

    def test_performance_service_persists_weight_snapshots(self):
        from apps.stakeholders.models import StakeholderPerformanceDimension

        dimensions = list(StakeholderPerformanceDimension.objects.filter(active=True))
        scores = {dimensions[0].code: Decimal("75")}
        review = StakeholderPerformanceService(user=self.manager).record_review(
            self.create_stakeholder(), "2026 Q3", scores
        )
        score = review.scores.get()
        self.assertEqual(score.weight_snapshot, dimensions[0].weight)
        self.assertEqual(
            review.missing_dimensions, [item.code for item in dimensions[1:]]
        )


class ContactEngagementAndContributionServiceTests(StakeholderTestCase):
    def test_contact_service_rotates_primary_and_deactivates(self):
        stakeholder = self.create_stakeholder()
        service = StakeholderContactService(user=self.manager)
        first = service.create(
            stakeholder, full_name="First", email="first@example.com"
        )
        second = service.create(
            stakeholder,
            full_name="Second",
            email="second@example.com",
            is_primary=True,
        )
        first.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertTrue(second.is_primary)
        service.deactivate(second)
        second.refresh_from_db()
        self.assertFalse(second.is_active)
        self.assertFalse(second.is_primary)
        self.assertIsNotNone(second.valid_to)

    def test_engagement_plan_record_completion_and_communication(self):
        stakeholder = self.create_stakeholder()
        engagement_service = StakeholderEngagementService(user=self.manager)
        plan = engagement_service.create_plan(
            stakeholder,
            title="Quarterly plan",
            objectives="Coordinate delivery",
            engagement_level=self.taxonomy(
                ReferenceDataKind.ENGAGEMENT_LEVEL, "collaborate"
            ),
            start_date=date(2026, 7, 1),
            end_date=date(2026, 12, 31),
        )
        engagement = engagement_service.record(
            stakeholder,
            plan=plan,
            engagement_type=EngagementType.MEETING,
            title="Review meeting",
            scheduled_at=timezone.make_aware(datetime(2026, 8, 2, 10, 0)),
        )
        completed = engagement_service.complete(engagement, outcomes="Plan agreed")
        self.assertEqual(completed.status, EngagementStatus.COMPLETED)
        communication = StakeholderCommunicationService(user=self.manager).record(
            stakeholder,
            engagement=completed,
            channel=CommunicationChannel.EMAIL,
            direction=CommunicationDirection.OUTBOUND,
            subject="Minutes",
            summary="Minutes shared",
        )
        self.assertEqual(communication.engagement, completed)

    def test_commitment_progress_and_contribution_verification(self):
        stakeholder = self.create_stakeholder()
        commitment = StakeholderCommitmentService(user=self.manager).create(
            stakeholder,
            title="Provide venue",
            description="Provide a training venue",
            responsible_party="Partner",
            due_date=date(2026, 9, 1),
        )
        commitment = StakeholderCommitmentService(user=self.manager).update_progress(
            commitment, Decimal("100"), "Delivered", complete=True
        )
        self.assertEqual(commitment.status, CommitmentStatus.COMPLETED)
        contribution = StakeholderContributionService(user=self.manager).record(
            stakeholder,
            contribution_type=self.taxonomy(
                ReferenceDataKind.CONTRIBUTION_TYPE, "financial"
            ),
            description="Training support",
            contribution_date=date(2026, 8, 1),
            amount=Decimal("2500.00"),
            status=ContributionStatus.RECEIVED,
        )
        contribution = StakeholderContributionService(user=self.manager).verify(
            contribution
        )
        self.assertEqual(contribution.status, ContributionStatus.VERIFIED)
        self.assertEqual(contribution.verified_by, self.manager)


class AgreementServiceTests(StakeholderTestCase):
    expected_transitions: ClassVar[dict[str, set[str]]] = {
        AgreementStatus.DRAFT: {AgreementStatus.UNDER_REVIEW, AgreementStatus.ARCHIVED},
        AgreementStatus.UNDER_REVIEW: {
            AgreementStatus.RETURNED,
            AgreementStatus.PENDING_APPROVAL,
        },
        AgreementStatus.RETURNED: {AgreementStatus.DRAFT, AgreementStatus.UNDER_REVIEW},
        AgreementStatus.PENDING_APPROVAL: {
            AgreementStatus.RETURNED,
            AgreementStatus.APPROVED,
        },
        AgreementStatus.APPROVED: {
            AgreementStatus.PENDING_SIGNATURE,
            AgreementStatus.RETURNED,
        },
        AgreementStatus.PENDING_SIGNATURE: {
            AgreementStatus.ACTIVE,
            AgreementStatus.RETURNED,
        },
        AgreementStatus.ACTIVE: {
            AgreementStatus.EXPIRING,
            AgreementStatus.EXPIRED,
            AgreementStatus.COMPLETED,
            AgreementStatus.TERMINATED,
            AgreementStatus.RENEWED,
        },
        AgreementStatus.EXPIRING: {
            AgreementStatus.ACTIVE,
            AgreementStatus.EXPIRED,
            AgreementStatus.RENEWED,
            AgreementStatus.TERMINATED,
        },
        AgreementStatus.EXPIRED: {AgreementStatus.RENEWED, AgreementStatus.ARCHIVED},
        AgreementStatus.TERMINATED: {AgreementStatus.ARCHIVED},
        AgreementStatus.COMPLETED: {AgreementStatus.ARCHIVED, AgreementStatus.RENEWED},
        AgreementStatus.RENEWED: {AgreementStatus.ARCHIVED},
        AgreementStatus.ARCHIVED: set(),
    }

    def test_agreement_transition_map_is_exact(self):
        self.assertEqual(AGREEMENT_TRANSITIONS, self.expected_transitions)

    def test_creator_cannot_approve_own_agreement(self):
        agreement = self.create_agreement(
            status=AgreementStatus.PENDING_APPROVAL,
            created_by=self.manager,
        )
        StakeholderAgreementVersion.objects.create(
            agreement=agreement, version_number=1, title=agreement.title
        )
        with self.assertRaises(ValidationError) as context:
            StakeholderAgreementService(user=self.manager).transition(
                agreement, AgreementStatus.APPROVED
            )
        self.assertEqual(
            context.exception.error_list[0].code, "agreement_self_approval"
        )

    def test_activation_requires_current_successful_due_diligence(self):
        stakeholder = self.create_stakeholder()
        agreement = self.create_agreement(
            stakeholder=stakeholder,
            status=AgreementStatus.PENDING_SIGNATURE,
            effective_date=date(2026, 8, 1),
            approved_by=self.manager,
            approved_at=timezone.now(),
        )
        StakeholderDueDiligenceService(user=self.manager).record(
            stakeholder,
            review_date=date(2026, 1, 1),
            expiry_date=date(2026, 1, 31),
            status=DueDiligenceStatus.PASSED,
        )
        with self.assertRaises(ValidationError):
            StakeholderAgreementService(user=self.manager).transition(
                agreement, AgreementStatus.ACTIVE
            )

    def test_agreement_expiry_and_renewal_create_new_versioned_agreement(self):
        stakeholder = self.create_stakeholder()
        agreement = self.create_agreement(
            stakeholder=stakeholder,
            status=AgreementStatus.ACTIVE,
            effective_date=date(2025, 1, 1),
            expiry_date=timezone.localdate() - timedelta(days=1),
            approved_by=self.manager,
            approved_at=timezone.now(),
        )
        service = StakeholderAgreementService(user=self.manager)
        expired = service.expire(agreement)
        self.assertEqual(expired.status, AgreementStatus.EXPIRED)
        renewal = service.request_renewal(
            expired,
            proposed_effective_date=date(2026, 9, 1),
            proposed_expiry_date=date(2027, 8, 31),
            rationale="Continue collaboration",
        )
        renewal = service.decide_renewal(
            renewal, approve=True, decision_notes="Approved"
        )
        self.assertEqual(renewal.status, RenewalStatus.COMPLETED)
        self.assertNotEqual(renewal.renewed_agreement_id, agreement.pk)
        self.assertEqual(renewal.renewed_agreement.current_version_number, 1)


class DueDiligenceAndRiskServiceTests(StakeholderTestCase):
    def test_due_diligence_service_sets_completion_metadata(self):
        review = StakeholderDueDiligenceService(user=self.manager).record(
            self.create_stakeholder(),
            review_date=date(2026, 8, 1),
            expiry_date=date(2027, 8, 1),
            status=DueDiligenceStatus.CONDITIONAL,
        )
        self.assertEqual(review.reviewed_by, self.manager)
        self.assertIsNotNone(review.completed_at)

    def test_risk_score_is_likelihood_times_impact(self):
        risk = StakeholderRiskService(user=self.manager).record_risk(
            self.create_stakeholder(),
            category=self.taxonomy(ReferenceDataKind.RISK_CATEGORY, "financial"),
            title="Funding concentration",
            description="Single source",
            likelihood=4,
            impact=5,
        )
        self.assertEqual(risk.risk_score, 20)
