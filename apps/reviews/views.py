"""Views for Review and Approval module (Phase 21).

Provides the reviewer inbox, review detail, decision forms,
escalation, delegation, and SLA monitoring views.
"""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from . import services
from .forms import (
    ChecklistResponseForm,
    ReviewAssignForm,
    ReviewCommentForm,
    ReviewDecisionForm,
    ReviewDelegationForm,
    ReviewEscalationForm,
    ReviewFilterForm,
)
from .models import (
    Review,
    ReviewChecklistResponse,
    ReviewComment,
    ReviewStatus,
    SLAConfiguration,
)
from .permissions import (
    can_accept_review,
    can_add_comment,
    can_assign_reviewer,
    can_delegate_review,
    can_escalate_review,
    can_make_decision,
    can_resolve_comment,
    can_start_review,
    can_update_checklist,
    can_view_reviews,
)
from .selectors import (
    get_checklist_progress,
    get_checklist_responses,
    get_comments_for_review,
    get_decisions_for_review,
    get_delegations_for_review,
    get_escalations_for_review,
    get_overdue_reviews,
    get_review_or_404,
    get_sla_events_for_review,
)

# ---------------------------------------------------------------------------
# Reviewer Inbox Dashboard
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewerDashboardView(View):
    """Main reviewer inbox dashboard."""

    def get(self, request):
        if not can_view_reviews(request.user):
            messages.error(request, "You do not have permission to view reviews.")
            return redirect("core:home")

        stats = services.get_reviewer_stats(request.user)
        pending = services.get_pending_reviews(request.user)[:10]
        overdue = (
            get_overdue_reviews()
            .filter(
                assignments__assigned_to=request.user,
                assignments__is_active=True,
            )
            .distinct()[:5]
        )
        recent_completed = (
            Review.objects.filter(
                assignments__assigned_to=request.user,
                assignments__is_active=True,
                status__in=[
                    ReviewStatus.APPROVED,
                    ReviewStatus.REJECTED,
                    ReviewStatus.CLOSED,
                ],
            )
            .select_related("report")
            .order_by("-completed_at")[:5]
        )

        return render(
            request,
            "reviews/dashboard.html",
            {
                "stats": stats,
                "pending_reviews": pending,
                "overdue_reviews": overdue,
                "recent_completed": recent_completed,
                "filter_form": ReviewFilterForm(),
            },
        )


# ---------------------------------------------------------------------------
# Review List Views
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewListView(View):
    """List all reviews visible to the current user."""

    def get(self, request):
        if not can_view_reviews(request.user):
            messages.error(request, "You do not have permission to view reviews.")
            return redirect("core:home")

        filter_form = ReviewFilterForm(request.GET)
        status_filter = request.GET.get("status", "")
        search_query = request.GET.get("q", "")

        qs = services.get_reviews_for_user(request.user)

        if status_filter:
            qs = qs.filter(status=status_filter)
        if search_query:
            qs = qs.filter(
                report__reference_number__icontains=search_query
            ) | qs.filter(report__title__icontains=search_query)

        context = {
            "reviews": qs[:50],
            "filter_form": filter_form,
            "total_count": qs.count(),
        }
        return render(request, "reviews/review_list.html", context)


# ---------------------------------------------------------------------------
# Review Detail
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewDetailView(View):
    """View review details with all related data."""

    def get(self, request, pk):
        if not can_view_reviews(request.user):
            messages.error(request, "You do not have permission to view this review.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        assignments = review.assignments.select_related("assigned_to", "assigned_by")
        comments = get_comments_for_review(review)
        decisions = get_decisions_for_review(review)
        escalations = get_escalations_for_review(review)
        delegations = get_delegations_for_review(review)
        sla_events = get_sla_events_for_review(review)
        checklist_progress = get_checklist_progress(review)
        checklist_responses = get_checklist_responses(review)

        return render(
            request,
            "reviews/review_detail.html",
            {
                "review": review,
                "report": review.report,
                "assignments": assignments,
                "comments": comments,
                "decisions": decisions,
                "escalations": escalations,
                "delegations": delegations,
                "sla_events": sla_events,
                "checklist_progress": checklist_progress,
                "checklist_responses": checklist_responses,
                "comment_form": ReviewCommentForm(),
                "decision_form": ReviewDecisionForm(),
                "assign_form": ReviewAssignForm(),
                "escalation_form": ReviewEscalationForm(),
                "delegation_form": ReviewDelegationForm(),
                "checklist_form": ChecklistResponseForm(),
            },
        )


# ---------------------------------------------------------------------------
# Review Actions
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewStartView(View):
    """Start the review process."""

    def post(self, request, pk):
        if not can_start_review(request.user):
            messages.error(request, "You do not have permission to start reviews.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        try:
            services.start_review(review, request.user)
            messages.success(request, "Review started successfully.")
        except Exception as e:
            messages.error(request, f"Error starting review: {e}")

        return redirect("reviews:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReviewAssignView(View):
    """Assign a reviewer to a review."""

    def post(self, request, pk):
        if not can_assign_reviewer(request.user):
            messages.error(request, "You do not have permission to assign reviewers.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ReviewAssignForm(request.POST)

        if form.is_valid():
            try:
                reviewer = get_user_model().objects.get(
                    pk=form.cleaned_data["reviewer"]
                )
                services.assign_reviewer(
                    review,
                    reviewer,
                    role=form.cleaned_data["role"],
                    assigned_by=request.user,
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(
                    request, f"Reviewer {reviewer.email} assigned successfully."
                )
            except Exception as e:
                messages.error(request, f"Error assigning reviewer: {e}")

        return redirect("reviews:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReviewAcceptView(View):
    """Accept a review assignment."""

    def post(self, request, pk):
        if not can_accept_review(request.user):
            messages.error(request, "You do not have permission to accept reviews.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        try:
            services.accept_review(review, request.user)
            messages.success(request, "Review accepted successfully.")
        except Exception as e:
            messages.error(request, f"Error accepting review: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewCommentView(View):
    """Add a comment to a review."""

    def post(self, request, pk):
        if not can_add_comment(request.user):
            messages.error(request, "You do not have permission to add comments.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ReviewCommentForm(request.POST)

        if form.is_valid():
            try:
                services.add_review_comment(
                    review,
                    request.user,
                    form.cleaned_data["body"],
                    comment_type=form.cleaned_data["comment_type"],
                    is_internal=form.cleaned_data.get("is_internal", False),
                )
                messages.success(request, "Comment added successfully.")
            except Exception as e:
                messages.error(request, f"Error adding comment: {e}")

        return redirect("reviews:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReviewCommentResolveView(View):
    """Resolve a review comment."""

    def post(self, request, pk, comment_pk):
        if not can_resolve_comment(request.user):
            messages.error(request, "You do not have permission to resolve comments.")
            return redirect("reviews:dashboard")

        comment = get_object_or_404(ReviewComment, pk=comment_pk)
        try:
            services.resolve_comment(comment, request.user)
            messages.success(request, "Comment resolved successfully.")
        except Exception as e:
            messages.error(request, f"Error resolving comment: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# Decisions
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewDecisionView(View):
    """Make a review decision."""

    def post(self, request, pk):
        if not can_make_decision(request.user):
            messages.error(request, "You do not have permission to make decisions.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ReviewDecisionForm(request.POST)

        if form.is_valid():
            try:
                services.make_decision(
                    review,
                    request.user,
                    form.cleaned_data["decision"],
                    form.cleaned_data["reason"],
                    conditions=form.cleaned_data.get("conditions", ""),
                    signature_data=form.cleaned_data.get("signature_data", ""),
                )
                messages.success(request, "Decision recorded successfully.")
            except Exception as e:
                messages.error(request, f"Error recording decision: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewEscalateView(View):
    """Escalate a review."""

    def post(self, request, pk):
        if not can_escalate_review(request.user):
            messages.error(request, "You do not have permission to escalate reviews.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ReviewEscalationForm(request.POST)

        if form.is_valid():
            try:
                escalated_to = None
                if form.cleaned_data.get("escalated_to"):
                    escalated_to = get_user_model().objects.get(
                        pk=form.cleaned_data["escalated_to"]
                    )
                services.escalate_review(
                    review,
                    request.user,
                    form.cleaned_data["reason"],
                    trigger=form.cleaned_data["trigger"],
                    escalated_to=escalated_to,
                )
                messages.success(request, "Review escalated successfully.")
            except Exception as e:
                messages.error(request, f"Error escalating review: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewDelegateView(View):
    """Delegate a review."""

    def post(self, request, pk):
        if not can_delegate_review(request.user):
            messages.error(request, "You do not have permission to delegate reviews.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ReviewDelegationForm(request.POST)

        if form.is_valid():
            try:
                delegated_to = get_user_model().objects.get(
                    pk=form.cleaned_data["delegated_to"]
                )
                services.delegate_review(
                    review,
                    request.user,
                    delegated_to,
                    form.cleaned_data["reason"],
                    expires_at=form.cleaned_data.get("expires_at"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, f"Review delegated to {delegated_to.email}.")
            except Exception as e:
                messages.error(request, f"Error delegating review: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReviewChecklistUpdateView(View):
    """Update a checklist response."""

    def post(self, request, pk):
        if not can_update_checklist(request.user):
            messages.error(request, "You do not have permission to update checklists.")
            return redirect("reviews:dashboard")

        review = get_review_or_404(pk)
        form = ChecklistResponseForm(request.POST)

        if form.is_valid():
            try:
                response = get_object_or_404(
                    ReviewChecklistResponse,
                    pk=form.cleaned_data["response_id"],
                    review=review,
                )
                services.complete_checklist_item(
                    response,
                    request.user,
                    is_completed=form.cleaned_data.get("is_completed", False),
                    score=form.cleaned_data.get("score"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Checklist item updated.")
            except Exception as e:
                messages.error(request, f"Error updating checklist: {e}")

        return redirect("reviews:detail", pk=pk)


# ---------------------------------------------------------------------------
# SLA Monitoring
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class SLADashboardView(View):
    """SLA monitoring dashboard."""

    def get(self, request):
        if not can_view_reviews(request.user):
            messages.error(request, "You do not have permission to view SLA data.")
            return redirect("core:home")

        overdue_reviews = get_overdue_reviews()[:20]
        sla_configs = SLAConfiguration.objects.filter(is_active=True)

        return render(
            request,
            "reviews/sla_dashboard.html",
            {
                "overdue_reviews": overdue_reviews,
                "sla_configs": sla_configs,
            },
        )
