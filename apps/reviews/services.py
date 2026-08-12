"""Service layer for Review and Approval module (Phase 21).

All business logic for reviews, assignments, decisions, escalations,
delegations, and SLA management lives here. Views call these functions
rather than manipulating models directly.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.report_instances.models import Report
from apps.reports.constants import ReportStatus

from .models import (
    CommentType,
    DelegationRecord,
    DigitalSignature,
    EscalationRecord,
    EscalationTrigger,
    Review,
    ReviewAssignment,
    ReviewChecklist,
    ReviewChecklistResponse,
    ReviewComment,
    ReviewConfiguration,
    ReviewDecision,
    ReviewDecisionType,
    ReviewerRole,
    ReviewStatus,
    SLAEvent,
)

# ---------------------------------------------------------------------------
# Review CRUD
# ---------------------------------------------------------------------------


@transaction.atomic
def create_review(
    report: Report,
    *,
    primary_reviewer=None,
    due_date=None,
    checklist: ReviewChecklist | None = None,
    created_by=None,
) -> Review:
    """Create a new review for a submitted report."""
    if report.status not in (
        ReportStatus.SUBMITTED,
        ReportStatus.RESUBMITTED,
    ):
        raise ValidationError(
            "Only submitted or resubmitted reports can be reviewed.",
            code="invalid_report_status",
        )

    review_number = Review.objects.filter(report=report).count() + 1
    review = Review.objects.create(
        report=report,
        review_number=review_number,
        status=ReviewStatus.PENDING_ASSIGNMENT,
        primary_reviewer=primary_reviewer,
        due_date=due_date,
        created_by=created_by,
    )

    if primary_reviewer:
        ReviewAssignment.objects.create(
            review=review,
            assigned_to=primary_reviewer,
            assigned_by=created_by,
            role=ReviewerRole.PRIMARY,
            created_by=created_by,
        )
        review.status = ReviewStatus.ASSIGNED
        review.save(update_fields=["status"])

    report.status = ReportStatus.UNDER_REVIEW
    report.save(update_fields=["status"])

    if checklist:
        _populate_checklist_responses(review, checklist, created_by)

    return review


def _populate_checklist_responses(
    review: Review, checklist: ReviewChecklist, created_by=None
) -> None:
    """Populate checklist responses for a review."""
    items = checklist.items.all()
    for item in items:
        ReviewChecklistResponse.objects.create(
            review=review,
            item=item,
            created_by=created_by,
        )


def get_review_or_404(review_id: str) -> Review:
    """Get a review by ID or raise Http404."""
    from django.shortcuts import get_object_or_404

    return get_object_or_404(Review, pk=review_id)


def get_reviews_for_user(user, status_filter=None):
    """Get reviews assigned to a specific user."""
    qs = Review.objects.filter(
        assignments__assigned_to=user,
        assignments__is_active=True,
    ).select_related("report", "primary_reviewer")

    if status_filter:
        qs = qs.filter(status=status_filter)

    return qs.distinct()


def get_pending_reviews(user=None):
    """Get reviews pending assignment or review."""
    qs = Review.objects.filter(
        status__in=[
            ReviewStatus.PENDING_ASSIGNMENT,
            ReviewStatus.ASSIGNED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.UNDER_REVIEW,
        ]
    ).select_related("report", "primary_reviewer")

    if user:
        qs = qs.filter(
            assignments__assigned_to=user,
            assignments__is_active=True,
        ).distinct()

    return qs


def get_overdue_reviews():
    """Get reviews that are overdue."""
    today = timezone.now().date()
    return Review.objects.filter(
        due_date__lt=today,
        status__in=[
            ReviewStatus.ASSIGNED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.UNDER_REVIEW,
        ],
    ).select_related("report", "primary_reviewer")


# ---------------------------------------------------------------------------
# Review Assignment
# ---------------------------------------------------------------------------


@transaction.atomic
def assign_reviewer(
    review: Review,
    user,
    *,
    role: str = ReviewerRole.PRIMARY,
    assigned_by=None,
    notes: str = "",
) -> ReviewAssignment:
    """Assign a reviewer to a review."""
    assignment = ReviewAssignment.objects.create(
        review=review,
        assigned_to=user,
        assigned_by=assigned_by,
        role=role,
        notes=notes,
        created_by=assigned_by,
    )

    if role == ReviewerRole.PRIMARY:
        review.primary_reviewer = user
        review.status = ReviewStatus.ASSIGNED
        review.save(update_fields=["primary_reviewer", "status"])

    return assignment


@transaction.atomic
def accept_review(review: Review, user) -> Review:
    """Accept a review assignment."""
    assignment = review.assignments.filter(assigned_to=user, is_active=True).first()

    if not assignment:
        raise ValidationError(
            "You are not assigned to this review.",
            code="not_assigned",
        )

    assignment.accepted_at = timezone.now()
    assignment.save(update_fields=["accepted_at"])

    review.status = ReviewStatus.ACCEPTED
    review.save(update_fields=["status"])

    return review


@transaction.atomic
def start_review(review: Review, user) -> Review:
    """Start the review process."""
    review.status = ReviewStatus.UNDER_REVIEW
    review.started_at = timezone.now()
    review.save(update_fields=["status", "started_at"])
    return review


# ---------------------------------------------------------------------------
# Review Comments
# ---------------------------------------------------------------------------


@transaction.atomic
def add_review_comment(
    review: Review,
    author,
    body: str,
    *,
    comment_type: str = CommentType.GENERAL,
    section=None,
    field=None,
    parent=None,
    is_internal: bool = False,
) -> ReviewComment:
    """Add a comment to a review."""
    comment = ReviewComment.objects.create(
        review=review,
        comment_type=comment_type,
        section=section,
        field=field,
        parent=parent,
        body=body,
        author=author,
        is_internal=is_internal,
        created_by=author,
    )
    return comment


@transaction.atomic
def resolve_comment(comment: ReviewComment, user) -> ReviewComment:
    """Resolve a review comment."""
    comment.is_resolved = True
    comment.resolved_by = user
    comment.resolved_at = timezone.now()
    comment.save(update_fields=["is_resolved", "resolved_by", "resolved_at"])
    return comment


# ---------------------------------------------------------------------------
# Review Decisions
# ---------------------------------------------------------------------------


@transaction.atomic
def make_decision(
    review: Review,
    reviewer,
    decision: str,
    reason: str,
    *,
    conditions: str = "",
    signature_data: str = "",
    signature_type: str = "",
) -> ReviewDecision:
    """Record a formal review decision."""
    decision_record = ReviewDecision.objects.create(
        review=review,
        decision=decision,
        reason=reason,
        conditions=conditions,
        reviewer=reviewer,
        created_by=reviewer,
    )

    if signature_data:
        DigitalSignature.objects.create(
            decision=decision_record,
            signer=reviewer,
            signature_type=signature_type or "TYPED",
            signature_data=signature_data,
            created_by=reviewer,
        )

    review.decision = decision
    review.decision_at = timezone.now()
    review.decision_notes = reason
    review.completed_at = timezone.now()

    status_map = {
        ReviewDecisionType.APPROVED: ReviewStatus.APPROVED,
        ReviewDecisionType.APPROVED_WITH_CONDITIONS: (
            ReviewStatus.CONDITIONALLY_APPROVED
        ),
        ReviewDecisionType.RETURNED_FOR_CORRECTION: (
            ReviewStatus.RETURNED_FOR_CORRECTION
        ),
        ReviewDecisionType.REJECTED: ReviewStatus.REJECTED,
        ReviewDecisionType.ESCALATED: ReviewStatus.ESCALATED,
        ReviewDecisionType.DELEGATED: ReviewStatus.DELEGATED,
    }

    review.status = status_map.get(decision, review.status)
    review.save(
        update_fields=[
            "decision",
            "decision_at",
            "decision_notes",
            "completed_at",
            "status",
        ]
    )

    report = review.report
    report_status_map = {
        ReviewDecisionType.APPROVED: ReportStatus.APPROVED,
        ReviewDecisionType.APPROVED_WITH_CONDITIONS: ReportStatus.APPROVED,
        ReviewDecisionType.RETURNED_FOR_CORRECTION: (
            ReportStatus.RETURNED_FOR_CORRECTION
        ),
        ReviewDecisionType.REJECTED: ReportStatus.REJECTED,
    }
    if decision in report_status_map:
        report.status = report_status_map[decision]
        if decision in (
            ReviewDecisionType.APPROVED,
            ReviewDecisionType.APPROVED_WITH_CONDITIONS,
        ):
            report.approved_at = timezone.now()
        report.save(update_fields=["status", "approved_at"])

    return decision_record


@transaction.atomic
def approve_report(
    review: Review,
    reviewer,
    reason: str = "",
    *,
    signature_data: str = "",
) -> ReviewDecision:
    """Approve a report through review."""
    return make_decision(
        review,
        reviewer,
        ReviewDecisionType.APPROVED,
        reason or "Report approved.",
        signature_data=signature_data,
    )


@transaction.atomic
def reject_report(
    review: Review,
    reviewer,
    reason: str,
) -> ReviewDecision:
    """Reject a report through review."""
    if not reason:
        raise ValidationError(
            "Rejection reason is required.",
            code="rejection_reason_required",
        )
    return make_decision(
        review,
        reviewer,
        ReviewDecisionType.REJECTED,
        reason,
    )


@transaction.atomic
def return_for_correction(
    review: Review,
    reviewer,
    reason: str,
) -> ReviewDecision:
    """Return a report for correction."""
    if not reason:
        raise ValidationError(
            "Return reason is required.",
            code="return_reason_required",
        )
    return make_decision(
        review,
        reviewer,
        ReviewDecisionType.RETURNED_FOR_CORRECTION,
        reason,
    )


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------


@transaction.atomic
def escalate_review(
    review: Review,
    escalated_by,
    reason: str,
    *,
    trigger: str = EscalationTrigger.CUSTOM,
    escalated_to=None,
) -> EscalationRecord:
    """Escalate a review to higher authority."""
    escalation = EscalationRecord.objects.create(
        review=review,
        trigger=trigger,
        reason=reason,
        escalated_by=escalated_by,
        escalated_to=escalated_to,
        created_by=escalated_by,
    )

    review.status = ReviewStatus.ESCALATED
    review.save(update_fields=["status"])

    SLAEvent.objects.create(
        review=review,
        event_type="ESCALATED",
        notes=reason,
        created_by=escalated_by,
    )

    return escalation


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


@transaction.atomic
def delegate_review(
    review: Review,
    delegated_by,
    delegated_to,
    reason: str,
    *,
    expires_at=None,
    notes: str = "",
) -> DelegationRecord:
    """Delegate review authority to another reviewer."""
    delegation = DelegationRecord.objects.create(
        review=review,
        delegated_by=delegated_by,
        delegated_to=delegated_to,
        reason=reason,
        expires_at=expires_at,
        notes=notes,
        created_by=delegated_by,
    )

    ReviewAssignment.objects.create(
        review=review,
        assigned_to=delegated_to,
        assigned_by=delegated_by,
        role=ReviewerRole.SECONDARY,
        notes=f"Delegated by {delegated_by.get_full_name()}: {reason}",
        created_by=delegated_by,
    )

    review.status = ReviewStatus.DELEGATED
    review.save(update_fields=["status"])

    return delegation


# ---------------------------------------------------------------------------
# Checklist Management
# ---------------------------------------------------------------------------


@transaction.atomic
def complete_checklist_item(
    response: ReviewChecklistResponse,
    user,
    *,
    is_completed: bool = True,
    score=None,
    notes: str = "",
) -> ReviewChecklistResponse:
    """Complete a checklist item."""
    response.is_completed = is_completed
    response.score = score
    response.notes = notes
    response.reviewed_by = user
    response.save(update_fields=["is_completed", "score", "notes", "reviewed_by"])
    return response


@transaction.atomic
def complete_checklist(review: Review, user) -> Review:
    """Mark checklist as completed for a review."""
    responses = review.checklist_responses.all()
    if not responses.exists():
        raise ValidationError(
            "No checklist items to complete.",
            code="no_checklist_items",
        )

    all_completed = all(r.is_completed for r in responses)
    if not all_completed:
        raise ValidationError(
            "Not all checklist items are completed.",
            code="checklist_incomplete",
        )

    review.checklist_completed = True
    review.save(update_fields=["checklist_completed"])
    return review


# ---------------------------------------------------------------------------
# SLA Management
# ---------------------------------------------------------------------------


@transaction.atomic
def check_sla_compliance(review: Review) -> dict:
    """Check SLA compliance for a review."""
    result = {
        "is_overdue": review.is_overdue,
        "duration_days": review.duration_days,
        "due_date": review.due_date,
        "status": review.status,
    }

    if review.is_overdue:
        SLAEvent.objects.get_or_create(
            review=review,
            event_type="OVERDUE",
            defaults={"notes": "Review is overdue"},
        )

    return result


@transaction.atomic
def send_sla_reminders() -> int:
    """Send SLA reminders for reviews approaching deadline."""
    reminder_days = ReviewConfiguration.get_value("reminder_days_before", 2)
    target_date = timezone.now().date() + timedelta(days=reminder_days)

    reviews = Review.objects.filter(
        due_date=target_date,
        status__in=[
            ReviewStatus.ASSIGNED,
            ReviewStatus.ACCEPTED,
            ReviewStatus.UNDER_REVIEW,
        ],
    )

    count = 0
    for review in reviews:
        SLAEvent.objects.get_or_create(
            review=review,
            event_type="REMINDER_SENT",
            defaults={"notes": f"Reminder: due on {review.due_date}"},
        )
        count += 1

    return count


# ---------------------------------------------------------------------------
# Reviewer Inbox Stats
# ---------------------------------------------------------------------------


def get_reviewer_stats(user) -> dict:
    """Get review statistics for a specific reviewer."""
    assigned = Review.objects.filter(
        assignments__assigned_to=user,
        assignments__is_active=True,
    )

    return {
        "total_assigned": assigned.count(),
        "pending": assigned.filter(
            status__in=[ReviewStatus.ASSIGNED, ReviewStatus.ACCEPTED]
        ).count(),
        "in_progress": assigned.filter(status=ReviewStatus.UNDER_REVIEW).count(),
        "completed": assigned.filter(
            status__in=[
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED,
                ReviewStatus.CLOSED,
            ]
        ).count(),
        "overdue": get_overdue_reviews()
        .filter(
            assignments__assigned_to=user,
            assignments__is_active=True,
        )
        .distinct()
        .count(),
    }


def get_review_dashboard_stats() -> dict:
    """Get overall review dashboard statistics."""
    return {
        "total_reviews": Review.objects.count(),
        "pending_assignment": Review.objects.filter(
            status=ReviewStatus.PENDING_ASSIGNMENT
        ).count(),
        "in_progress": Review.objects.filter(
            status__in=[
                ReviewStatus.ASSIGNED,
                ReviewStatus.ACCEPTED,
                ReviewStatus.UNDER_REVIEW,
            ]
        ).count(),
        "completed": Review.objects.filter(
            status__in=[
                ReviewStatus.APPROVED,
                ReviewStatus.REJECTED,
                ReviewStatus.CLOSED,
            ]
        ).count(),
        "overdue": get_overdue_reviews().count(),
        "escalated": Review.objects.filter(status=ReviewStatus.ESCALATED).count(),
    }
