"""URL configuration for the Accessibility Review module."""

from django.urls import path

from . import views

app_name = "accessibility"

urlpatterns = [
    # Dashboard
    path("", views.AccessibilityDashboardView.as_view(), name="dashboard"),

    # Standards
    path("standards/", views.StandardListView.as_view(), name="standard_list"),
    path("standards/create/", views.StandardCreateView.as_view(), name="standard_create"),
    path("standards/<uuid:pk>/edit/", views.StandardUpdateView.as_view(), name="standard_update"),

    # Policies
    path("policies/", views.PolicyListView.as_view(), name="policy_list"),
    path("policies/create/", views.PolicyCreateView.as_view(), name="policy_create"),
    path("policies/<uuid:pk>/edit/", views.PolicyUpdateView.as_view(), name="policy_update"),

    # Configuration
    path("configuration/", views.ConfigurationView.as_view(), name="configuration"),

    # User Preferences
    path("preferences/", views.UserPreferenceView.as_view(), name="user_preferences"),

    # WCAG Criteria
    path("criteria/", views.WCAGCriterionListView.as_view(), name="criterion_list"),
    path("criteria/create/", views.WCAGCriterionCreateView.as_view(), name="criterion_create"),

    # Audits
    path("audits/", views.AuditListView.as_view(), name="audit_list"),
    path("audits/create/", views.AuditCreateView.as_view(), name="audit_create"),
    path("audits/<uuid:pk>/", views.AuditDetailView.as_view(), name="audit_detail"),
    path("audits/<uuid:pk>/complete/", views.AuditCompleteView.as_view(), name="audit_complete"),
    path("audits/<uuid:audit_pk>/findings/create/", views.FindingCreateView.as_view(), name="finding_create"),

    # Issues
    path("issues/", views.IssueListView.as_view(), name="issue_list"),
    path("issues/create/", views.IssueCreateView.as_view(), name="issue_create"),
    path("issues/<uuid:pk>/", views.IssueDetailView.as_view(), name="issue_detail"),
    path("issues/<uuid:pk>/resolve/", views.IssueResolveView.as_view(), name="issue_resolve"),

    # Recommendations
    path("recommendations/", views.RecommendationListView.as_view(), name="recommendation_list"),
    path("recommendations/create/", views.RecommendationCreateView.as_view(), name="recommendation_create"),

    # Compliance
    path("compliance/", views.ComplianceRecordListView.as_view(), name="compliance_list"),
    path("compliance/<uuid:pk>/", views.ComplianceRecordDetailView.as_view(), name="compliance_detail"),
    path("exceptions/create/", views.ExceptionCreateView.as_view(), name="exception_create"),

    # Analytics & Reports
    path("analytics/", views.AnalyticsView.as_view(), name="analytics"),
    path("timeline/", views.TimelineView.as_view(), name="timeline"),

    # API Endpoints
    path("api/preferences/", views.UserPreferencesAPIView.as_view(), name="api_preferences"),
    path("api/contrast-check/", views.ContrastCheckAPIView.as_view(), name="api_contrast_check"),
]
