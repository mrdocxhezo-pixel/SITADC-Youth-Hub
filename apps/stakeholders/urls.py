"""URL routes for the stakeholder management module."""

from django.urls import path

from . import views

app_name = "stakeholders"

urlpatterns = [
    path("", views.StakeholderDashboardView.as_view(), name="dashboard"),
    path("dashboard/", views.StakeholderDashboardView.as_view(), name="dashboard_alt"),
    path("directory/", views.StakeholderDirectoryView.as_view(), name="directory"),
    path("directory/partners/", views.PartnerDirectoryView.as_view(), name="partners"),
    path("directory/donors/", views.DonorDirectoryView.as_view(), name="donors"),
    path("directory/sponsors/", views.SponsorDirectoryView.as_view(), name="sponsors"),
    path(
        "directory/government/",
        views.GovernmentDirectoryView.as_view(),
        name="government",
    ),
    path(
        "directory/community/",
        views.CommunityDirectoryView.as_view(),
        name="community",
    ),
    path("mapping/", views.MappingMatrixView.as_view(), name="mapping_matrix"),
    path("create/", views.StakeholderCreateView.as_view(), name="create"),
    path("<uuid:pk>/", views.StakeholderProfileView.as_view(), name="profile"),
    path("<uuid:pk>/edit/", views.StakeholderUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/status/", views.StakeholderStatusView.as_view(), name="status"),
    path("<uuid:pk>/archive/", views.StakeholderArchiveView.as_view(), name="archive"),
    path("<uuid:pk>/restore/", views.StakeholderRestoreView.as_view(), name="restore"),
    path(
        "<uuid:pk>/contacts/", views.StakeholderContactsView.as_view(), name="contacts"
    ),
    path(
        "contacts/<uuid:contact_pk>/primary/",
        views.ContactSetPrimaryView.as_view(),
        name="contact_primary",
    ),
    path(
        "contacts/<uuid:contact_pk>/deactivate/",
        views.ContactDeactivateView.as_view(),
        name="contact_deactivate",
    ),
    path(
        "<uuid:pk>/assessments/",
        views.StakeholderAssessmentsView.as_view(),
        name="assessments",
    ),
    path(
        "<uuid:pk>/engagement-plans/",
        views.StakeholderEngagementPlansView.as_view(),
        name="engagement_plans",
    ),
    path(
        "<uuid:pk>/engagements/",
        views.StakeholderEngagementsView.as_view(),
        name="engagements",
    ),
    path(
        "engagements/<uuid:engagement_pk>/complete/",
        views.EngagementCompleteView.as_view(),
        name="engagement_complete",
    ),
    path(
        "<uuid:pk>/communications/",
        views.StakeholderCommunicationsView.as_view(),
        name="communications",
    ),
    path(
        "<uuid:pk>/commitments/",
        views.StakeholderCommitmentsView.as_view(),
        name="commitments",
    ),
    path(
        "commitments/<uuid:commitment_pk>/progress/",
        views.CommitmentProgressView.as_view(),
        name="commitment_progress",
    ),
    path(
        "<uuid:pk>/contributions/",
        views.StakeholderContributionsView.as_view(),
        name="contributions",
    ),
    path(
        "contributions/<uuid:contribution_pk>/verify/",
        views.ContributionVerifyView.as_view(),
        name="contribution_verify",
    ),
    path(
        "<uuid:pk>/agreements/",
        views.StakeholderAgreementsView.as_view(),
        name="agreements",
    ),
    path(
        "agreements/<uuid:agreement_pk>/transition/",
        views.AgreementTransitionView.as_view(),
        name="agreement_transition",
    ),
    path(
        "agreements/<uuid:agreement_pk>/versions/add/",
        views.AgreementVersionCreateView.as_view(),
        name="agreement_version_add",
    ),
    path(
        "agreement-versions/<uuid:version_pk>/download/",
        views.AgreementVersionDownloadView.as_view(),
        name="agreement_version_download",
    ),
    path(
        "agreements/<uuid:agreement_pk>/renewal/",
        views.AgreementRenewalRequestView.as_view(),
        name="renewal_request",
    ),
    path(
        "renewals/<uuid:renewal_pk>/decision/",
        views.AgreementRenewalDecisionView.as_view(),
        name="renewal_decision",
    ),
    path(
        "<uuid:pk>/due-diligence/",
        views.StakeholderDueDiligenceView.as_view(),
        name="due_diligence",
    ),
    path("<uuid:pk>/risks/", views.StakeholderRiskView.as_view(), name="risks"),
    path(
        "<uuid:pk>/performance/",
        views.StakeholderPerformanceView.as_view(),
        name="performance",
    ),
    path(
        "performance/<uuid:review_pk>/finalize/",
        views.PerformanceFinalizeView.as_view(),
        name="performance_finalize",
    ),
    path("<uuid:pk>/actions/", views.StakeholderActionsView.as_view(), name="actions"),
    path(
        "actions/<uuid:action_pk>/status/",
        views.ActionStatusView.as_view(),
        name="action_status",
    ),
    path("<uuid:pk>/notes/", views.StakeholderNotesView.as_view(), name="notes"),
    path(
        "notes/<uuid:note_pk>/versions/add/",
        views.NoteVersionCreateView.as_view(),
        name="note_version_add",
    ),
    path(
        "notes/<uuid:note_pk>/finalize/",
        views.NoteFinalizeView.as_view(),
        name="note_finalize",
    ),
    path(
        "<uuid:pk>/documents/",
        views.StakeholderDocumentsView.as_view(),
        name="documents",
    ),
    path(
        "documents/<uuid:document_pk>/download/",
        views.StakeholderDocumentDownloadView.as_view(),
        name="document_download",
    ),
    path(
        "documents/<uuid:document_pk>/archive/",
        views.DocumentArchiveView.as_view(),
        name="document_archive",
    ),
    path("reports/summary/", views.StakeholderReportsView.as_view(), name="reports"),
    path(
        "reports/register.csv",
        views.StakeholderRegisterExportView.as_view(),
        name="register_export",
    ),
]
