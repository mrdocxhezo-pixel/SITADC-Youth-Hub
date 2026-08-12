"""Selectors for Review and Approval module (Phase 21).

Read-only query functions used by views and services.
"""

from __future__ import annotations

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from .models import (
    DelegationRecord,
    DigitalSignature,
    EscalationRecord,
    Review,
    ReviewAssignment,
    ReviewChecklist,
    ReviewChecklistResponse,
    ReviewComment,
    ReviewConfiguration,
    ReviewDecision,
    ReviewStatus,
    SLAConfiguration,
    SLAEvent,
)

# ---------------------------------------------------------------------------
# Review Selectors
# ---------------------------------------------------------------------------


def get_review_or_404(review_id: str) -> Review:
    """Get a review by ID or raise Http404."""
    return get_object_or_404(
        Review.objects.select_related("report", "primary_reviewer"),
        pk=review_id,
    )


def get_all_reviews() -> QuerySet[Review]:
    """Get all reviews with related objects."""
    return Review.objects.select_related("report", "primary_reviewer").prefetch_related(
        "assignments", "comments", "decisions"
    )


def get_reviews_by_status(status: str) -> QuerySet[Review]:
    """Get reviews filtered by status."""
    return get_all_reviews().filter(status=status)


def get_reviews_for_user(user) -> QuerySet[Review]:
    """Get reviews assigned to a specific user."""
    return (
        get_all_reviews()
        .filter(
            assignments__assigned_to=user,
            assignments__is_active=True,
        )
        .distinct()
    )


def get_pending_reviews() -> QuerySet[Review]:
    """Get reviews pending assignment or review."""
    return get_all_reviews().filter(
        status__in=[
            ReviewStatus.PENDING_ASSIGNMENT,
            ReviewStatus.ASSIGNED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.UNDER_REVIEW,
        ]
    )


def get_overdue_reviews() -> QuerySet[Review]:
    """Get reviews that are overdue."""
    from django.utils import timezone

    today = timezone.now().date()
    return get_all_reviews().filter(
        due_date__lt=today,
        status__in=[
            ReviewStatus.ASSIGNED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.UNDER_REVIEW,
        ],
    )


def get_completed_reviews() -> QuerySet[Review]:
    """Get completed reviews."""
    return get_all_reviews().filter(
        status__in=[
            ReviewStatus.APPROVED,
            ReviewStatus.REJECTED,
            ReviewStatus.CLOSED,
        ]
    )


# ---------------------------------------------------------------------------
# Assignment Selectors
# ---------------------------------------------------------------------------


def get_assignments_for_review(review: Review) -> QuerySet[ReviewAssignment]:
    """Get all assignments for a review."""
    return review.assignments.select_related("assigned_to", "assigned_by")


def get_active_assignments_for_review(review: Review) -> QuerySet[ReviewAssignment]:
    """Get active assignments for a review."""
    return review.assignments.filter(is_active=True).select_related("assigned_to")


# ---------------------------------------------------------------------------
# Comment Selectors
# ---------------------------------------------------------------------------


def get_comments_for_review(review: Review) -> QuerySet[ReviewComment]:
    """Get all comments for a review."""
    return review.comments.select_related(
        "author", "section", "field", "parent"
    ).order_by("created_at")


def get_internal_comments(review: Review) -> QuerySet[ReviewComment]:
    """Get internal comments for a review."""
    return get_comments_for_review(review).filter(is_internal=True)


def get_unresolved_comments(review: Review) -> QuerySet[ReviewComment]:
    """Get unresolved comments for a review."""
    return get_comments_for_review(review).filter(is_resolved=False)


# ---------------------------------------------------------------------------
# Decision Selectors
# ---------------------------------------------------------------------------


def get_decisions_for_review(review: Review) -> QuerySet[ReviewDecision]:
    """Get all decisions for a review."""
    return review.decisions.select_related("reviewer").order_by("-decided_at")


def get_latest_decision(review: Review) -> ReviewDecision | None:
    """Get the latest decision for a review."""
    return review.decisions.select_related("reviewer").first()


# ---------------------------------------------------------------------------
# Checklist Selectors
# ---------------------------------------------------------------------------


def get_checklist_responses(review: Review) -> QuerySet[ReviewChecklistResponse]:
    """Get checklist responses for a review."""
    return review.checklist_responses.select_related("item", "reviewed_by").order_by(
        "item__sort_order"
    )


def get_checklist_progress(review: Review) -> dict:
    """Get checklist completion progress."""
    responses = review.checklist_responses.all()
    total = responses.count()
    completed = responses.filter(is_completed=True).count()
    return {
        "total": total,
        "completed": completed,
        "percentage": (completed / total * 100) if total > 0 else 0,
    }


def get_available_checklists(category=None) -> QuerySet[ReviewChecklist]:
    """Get available checklists, optionally filtered by category."""
    qs = ReviewChecklist.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)
    return qs


# ---------------------------------------------------------------------------
# Escalation Selectors
# ---------------------------------------------------------------------------


def get_escalations_for_review(review: Review) -> QuerySet[EscalationRecord]:
    """Get escalations for a review."""
    return review.escalations.select_related("escalated_by", "escalated_to").order_by(
        "-escalated_at"
    )


def get_unresolved_escalations() -> QuerySet[EscalationRecord]:
    """Get unresolved escalations."""
    return EscalationRecord.objects.filter(is_resolved=False).select_related(
        "review", "escalated_by", "escalated_to"
    )


# ---------------------------------------------------------------------------
# Delegation Selectors
# ---------------------------------------------------------------------------


def get_delegations_for_review(review: Review) -> QuerySet[DelegationRecord]:
    """Get delegations for a review."""
    return review.delegations.select_related("delegated_by", "delegated_to").order_by(
        "-delegated_at"
    )


def get_active_delegations(user) -> QuerySet[DelegationRecord]:
    """Get active delegations for a user."""
    from django.utils import timezone

    return DelegationRecord.objects.filter(
        delegated_to=user,
        is_active=True,
        expires_at__gt=timezone.now(),
    ).select_related("review", "delegated_by")


# ---------------------------------------------------------------------------
# SLA Selectors
# ---------------------------------------------------------------------------


def get_sla_events_for_review(review: Review) -> QuerySet[SLAEvent]:
    """Get SLA events for a review."""
    return review.sla_events.order_by("-event_date")


def get_sla_configurations(category=None) -> QuerySet[SLAConfiguration]:
    """Get SLA configurations."""
    qs = SLAConfiguration.objects.filter(is_active=True)
    if category:
        qs = qs.filter(category=category)
    return qs


# ---------------------------------------------------------------------------
# Digital Signature Selectors
# ---------------------------------------------------------------------------


def get_signatures_for_decision(decision: ReviewDecision) -> QuerySet[DigitalSignature]:
    """Get signatures for a decision."""
    return decision.signatures.select_related("signer").order_by("-signed_at")


# ---------------------------------------------------------------------------
# Configuration Selectors
# ---------------------------------------------------------------------------


def get_review_configurations() -> QuerySet[ReviewConfiguration]:
    """Get all review configurations."""
    return ReviewConfiguration.objects.all()


def get_configuration_value(key: str, default=None):
    """Get a configuration value."""
    return ReviewConfiguration.get_value(key, default)
