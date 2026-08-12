"""URL configuration for Review and Approval module (Phase 21).

All routes are namespaced under ``reviews``.
"""

from django.urls import path

from . import views

app_name = "reviews"

urlpatterns = [
    # Dashboard
    path("", views.ReviewerDashboardView.as_view(), name="dashboard"),
    path("list/", views.ReviewListView.as_view(), name="list"),
    # Review Detail
    path("<uuid:pk>/", views.ReviewDetailView.as_view(), name="detail"),
    # Review Actions
    path("<uuid:pk>/start/", views.ReviewStartView.as_view(), name="start"),
    path("<uuid:pk>/assign/", views.ReviewAssignView.as_view(), name="assign"),
    path("<uuid:pk>/accept/", views.ReviewAcceptView.as_view(), name="accept"),
    # Comments
    path("<uuid:pk>/comment/", views.ReviewCommentView.as_view(), name="comment"),
    path(
        "<uuid:pk>/comment/<uuid:comment_pk>/resolve/",
        views.ReviewCommentResolveView.as_view(),
        name="comment_resolve",
    ),
    # Decisions
    path("<uuid:pk>/decision/", views.ReviewDecisionView.as_view(), name="decision"),
    # Escalation
    path("<uuid:pk>/escalate/", views.ReviewEscalateView.as_view(), name="escalate"),
    # Delegation
    path("<uuid:pk>/delegate/", views.ReviewDelegateView.as_view(), name="delegate"),
    # Checklist
    path(
        "<uuid:pk>/checklist/",
        views.ReviewChecklistUpdateView.as_view(),
        name="checklist_update",
    ),
    # SLA
    path("sla/", views.SLADashboardView.as_view(), name="sla_dashboard"),
]
