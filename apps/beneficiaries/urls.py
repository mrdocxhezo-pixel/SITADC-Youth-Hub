"""URL routes for the beneficiary management module."""

from django.urls import path

from . import views

app_name = "beneficiaries"

urlpatterns = [
    path("", views.BeneficiaryDashboardView.as_view(), name="dashboard"),
    path("dashboard/", views.BeneficiaryDashboardView.as_view(), name="dashboard_alt"),
    path("directory/", views.BeneficiaryDirectoryView.as_view(), name="directory"),
    path("create/", views.BeneficiaryCreateView.as_view(), name="create"),
    path(
        "autocomplete/",
        views.BeneficiaryAutocompleteView.as_view(),
        name="autocomplete",
    ),
    path("households/", views.HouseholdListView.as_view(), name="households"),
    path(
        "households/<uuid:pk>/",
        views.HouseholdDetailView.as_view(),
        name="household_detail",
    ),
    path(
        "household-members/<uuid:member_pk>/remove/",
        views.HouseholdMemberRemoveView.as_view(),
        name="household_member_remove",
    ),
    path("groups/", views.GroupListView.as_view(), name="groups"),
    path("groups/<uuid:pk>/", views.GroupDetailView.as_view(), name="group_detail"),
    path(
        "group-members/<uuid:membership_pk>/remove/",
        views.GroupMemberRemoveView.as_view(),
        name="group_member_remove",
    ),
    path(
        "reports/register.csv",
        views.BeneficiaryRegisterExportView.as_view(),
        name="register_export",
    ),
    path(
        "reports/register.xlsx",
        views.BeneficiaryRegisterXlsxExportView.as_view(),
        name="register_xlsx",
    ),
    path(
        "reports/register.docx",
        views.BeneficiaryRegisterDocxExportView.as_view(),
        name="register_docx",
    ),
    path(
        "reports/register.pdf",
        views.BeneficiaryRegisterPdfExportView.as_view(),
        name="register_pdf",
    ),
    path("<uuid:pk>/", views.BeneficiaryProfileView.as_view(), name="profile"),
    path("<uuid:pk>/edit/", views.BeneficiaryUpdateView.as_view(), name="edit"),
    path("<uuid:pk>/status/", views.BeneficiaryStatusView.as_view(), name="status"),
    path("<uuid:pk>/archive/", views.BeneficiaryArchiveView.as_view(), name="archive"),
    path("<uuid:pk>/restore/", views.BeneficiaryRestoreView.as_view(), name="restore"),
    path(
        "<uuid:pk>/profile.docx",
        views.BeneficiaryProfileDocxExportView.as_view(),
        name="profile_docx",
    ),
    path("<uuid:pk>/guardians/", views.GuardiansView.as_view(), name="guardians"),
    path(
        "guardians/<uuid:guardian_pk>/primary/",
        views.GuardianPrimaryView.as_view(),
        name="guardian_primary",
    ),
    path(
        "guardians/<uuid:guardian_pk>/deactivate/",
        views.GuardianDeactivateView.as_view(),
        name="guardian_deactivate",
    ),
    path("<uuid:pk>/enrollments/", views.EnrollmentsView.as_view(), name="enrollments"),
    path(
        "enrollments/<uuid:enrollment_pk>/status/",
        views.EnrollmentStatusView.as_view(),
        name="enrollment_status",
    ),
    path(
        "<uuid:pk>/participation/",
        views.ParticipationView.as_view(),
        name="participation",
    ),
    path("<uuid:pk>/attendance/", views.AttendanceView.as_view(), name="attendance"),
    path("<uuid:pk>/services/", views.ServicesView.as_view(), name="services"),
    path(
        "services/<uuid:service_pk>/deliver/",
        views.ServiceDeliverView.as_view(),
        name="service_deliver",
    ),
    path("<uuid:pk>/referrals/", views.ReferralsView.as_view(), name="referrals"),
    path(
        "referrals/<uuid:referral_pk>/status/",
        views.ReferralStatusView.as_view(),
        name="referral_status",
    ),
    path("<uuid:pk>/case-notes/", views.CaseNotesView.as_view(), name="case_notes"),
    path("<uuid:pk>/follow-ups/", views.FollowUpsView.as_view(), name="follow_ups"),
    path(
        "follow-ups/<uuid:follow_up_pk>/complete/",
        views.FollowUpCompleteView.as_view(),
        name="follow_up_complete",
    ),
    path("<uuid:pk>/assessments/", views.AssessmentsView.as_view(), name="assessments"),
    path(
        "assessments/<uuid:assessment_pk>/submit/",
        views.AssessmentSubmitView.as_view(),
        name="assessment_submit",
    ),
    path(
        "assessments/<uuid:assessment_pk>/approve/",
        views.AssessmentApproveView.as_view(),
        name="assessment_approve",
    ),
    path(
        "<uuid:pk>/support-plans/",
        views.SupportPlansView.as_view(),
        name="support_plans",
    ),
    path(
        "support-plans/<uuid:plan_pk>/activate/",
        views.SupportPlanActivateView.as_view(),
        name="support_plan_activate",
    ),
    path("<uuid:pk>/consent/", views.ConsentView.as_view(), name="consent"),
    path(
        "consent/<uuid:consent_pk>/withdraw/",
        views.ConsentWithdrawView.as_view(),
        name="consent_withdraw",
    ),
    path(
        "<uuid:pk>/safeguarding/",
        views.SafeguardingView.as_view(),
        name="safeguarding",
    ),
    path(
        "safeguarding/<uuid:record_pk>/status/",
        views.SafeguardingStatusView.as_view(),
        name="safeguarding_status",
    ),
    path("<uuid:pk>/outcomes/", views.OutcomesView.as_view(), name="outcomes"),
    path("<uuid:pk>/exits/", views.ExitsView.as_view(), name="exits"),
    path("<uuid:pk>/documents/", views.DocumentsView.as_view(), name="documents"),
    path(
        "documents/<uuid:document_pk>/download/",
        views.DocumentDownloadView.as_view(),
        name="document_download",
    ),
    path(
        "documents/<uuid:document_pk>/archive/",
        views.DocumentArchiveView.as_view(),
        name="document_archive",
    ),
    path(
        "<uuid:pk>/communications/",
        views.CommunicationsView.as_view(),
        name="communications",
    ),
    path("<uuid:pk>/feedback/", views.FeedbackView.as_view(), name="feedback"),
    path(
        "feedback/<uuid:feedback_pk>/respond/",
        views.FeedbackRespondView.as_view(),
        name="feedback_respond",
    ),
    path("<uuid:pk>/transfers/", views.TransfersView.as_view(), name="transfers"),
    path(
        "transfers/<uuid:transfer_pk>/complete/",
        views.TransferCompleteView.as_view(),
        name="transfer_complete",
    ),
    path("<uuid:pk>/duplicates/", views.DuplicatesView.as_view(), name="duplicates"),
    path(
        "duplicates/<uuid:review_pk>/merge/",
        views.DuplicateMergeView.as_view(),
        name="duplicate_merge",
    ),
]
