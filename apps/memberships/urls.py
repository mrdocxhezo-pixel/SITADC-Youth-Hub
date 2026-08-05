"""
URL routing for the membership management module.
"""

from django.urls import path

from . import views

app_name = "memberships"

urlpatterns = [
    path("dashboard/", views.MembershipDashboardView.as_view(), name="dashboard"),
    path("directory/", views.MembershipDirectoryView.as_view(), name="directory"),
    path("member/create/", views.MemberCreateView.as_view(), name="member_create"),
    path("member/<uuid:pk>/", views.MemberDetailView.as_view(), name="detail"),
    path("member/<uuid:pk>/edit/", views.MemberUpdateView.as_view(), name="update"),
    path(
        "member/<uuid:pk>/status/",
        views.MemberStatusActionView.as_view(),
        name="status_action",
    ),
    path("member/<uuid:pk>/id-card/", views.MemberIdCardView.as_view(), name="id_card"),
    path(
        "member/<uuid:pk>/card/issue/", views.CardIssueView.as_view(), name="card_issue"
    ),
    path(
        "member/<uuid:pk>/participation/add/",
        views.ParticipationCreateView.as_view(),
        name="participation_add",
    ),
    path(
        "member/<uuid:pk>/committee/assign/",
        views.CommitteeAssignView.as_view(),
        name="committee_assign",
    ),
    path(
        "member/<uuid:pk>/recognition/add/",
        views.RecognitionCreateView.as_view(),
        name="recognition_add",
    ),
    # Applications
    path("applications/", views.ApplicationListView.as_view(), name="application_list"),
    path("apply/", views.ApplicationCreateView.as_view(), name="apply"),
    path(
        "apply/success/",
        views.ApplicationSuccessView.as_view(),
        name="application_success",
    ),
    path(
        "application/<uuid:pk>/",
        views.ApplicationDetailView.as_view(),
        name="application_detail",
    ),
    path(
        "application/<uuid:pk>/review/",
        views.ApplicationReviewView.as_view(),
        name="application_review",
    ),
    # Renewals
    path("renewals/", views.RenewalListView.as_view(), name="renewal_list"),
    path(
        "renewal/<uuid:pk>/decide/",
        views.RenewalApproveView.as_view(),
        name="renewal_decide",
    ),
    # Transfers & Upgrades
    path("transfers/", views.TransferListView.as_view(), name="transfer_list"),
    path(
        "transfers/request/", views.TransferCreateView.as_view(), name="transfer_create"
    ),
    path(
        "transfer/<uuid:pk>/decide/",
        views.TransferApproveView.as_view(),
        name="transfer_decide",
    ),
    path("upgrades/request/", views.UpgradeCreateView.as_view(), name="upgrade_create"),
    # Payments & Cards
    path("payments/", views.PaymentListView.as_view(), name="payment_list"),
    path("payments/record/", views.PaymentCreateView.as_view(), name="payment_create"),
    path(
        "payment/<uuid:pk>/verify/",
        views.PaymentVerifyView.as_view(),
        name="payment_verify",
    ),
    path("cards/", views.CardListView.as_view(), name="card_list"),
    path("card/<uuid:pk>/revoke/", views.CardRevokeView.as_view(), name="card_revoke"),
    # Participation, Committees, Recognition, Leave
    path("leaves/", views.LeaveListView.as_view(), name="leave_list"),
    path("leaves/apply/", views.LeaveCreateView.as_view(), name="leave_create"),
    path(
        "leave/<uuid:pk>/decide/", views.LeaveApproveView.as_view(), name="leave_decide"
    ),
    # Exit & Alumni
    path("exits/", views.ExitListView.as_view(), name="exit_list"),
    path("exits/initiate/", views.ExitCreateView.as_view(), name="exit_create"),
    path(
        "exit/<uuid:pk>/complete/",
        views.ExitCompleteView.as_view(),
        name="exit_complete",
    ),
    # Reports & Exports
    path("reports/", views.MemberReportsView.as_view(), name="reports"),
]
