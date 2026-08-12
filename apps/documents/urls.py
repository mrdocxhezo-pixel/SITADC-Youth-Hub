"""URL routes for the Document Management module."""

from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    # ── Dashboard ─────────────────────────────────────────────────────
    path("", views.DocumentDashboardView.as_view(), name="dashboard"),
    path("dashboard/", views.DocumentDashboardView.as_view(), name="dashboard_alt"),
    # ── Document Directory ───────────────────────────────────────────
    path("list/", views.DocumentListView.as_view(), name="list"),
    path("my-documents/", views.MyDocumentsView.as_view(), name="my_documents"),
    # ── Upload ────────────────────────────────────────────────────────
    path("upload/", views.DocumentCreateView.as_view(), name="upload"),
    # ── Detail ────────────────────────────────────────────────────────
    path("<uuid:pk>/", views.DocumentDetailView.as_view(), name="detail"),
    # ── Metadata Update ──────────────────────────────────────────────
    path("<uuid:pk>/edit/", views.DocumentMetadataUpdateView.as_view(), name="edit"),
    # ── File Operations ──────────────────────────────────────────────
    path("<uuid:pk>/preview/", views.DocumentPreviewView.as_view(), name="preview"),
    path("<uuid:pk>/download/", views.DocumentDownloadView.as_view(), name="download"),
    # ── Versioning ────────────────────────────────────────────────────
    path(
        "<uuid:pk>/versions/",
        views.DocumentVersionHistoryView.as_view(),
        name="version_history",
    ),
    path(
        "<uuid:pk>/versions/upload/",
        views.DocumentVersionUploadView.as_view(),
        name="version_upload",
    ),
    # ── Checkout / Checkin ───────────────────────────────────────────
    path("<uuid:pk>/checkout/", views.DocumentCheckoutView.as_view(), name="checkout"),
    path("<uuid:pk>/checkin/", views.DocumentCheckinView.as_view(), name="checkin"),
    path(
        "<uuid:pk>/checkout/cancel/",
        views.DocumentCancelCheckoutView.as_view(),
        name="checkout_cancel",
    ),
    # ── Workflow ──────────────────────────────────────────────────────
    path(
        "<uuid:pk>/workflow/",
        views.DocumentWorkflowActionView.as_view(),
        name="workflow_action",
    ),
    path(
        "<uuid:pk>/submit/",
        views.DocumentSubmitReviewView.as_view(),
        name="submit",
    ),
    path(
        "<uuid:pk>/review/",
        views.DocumentReviewView.as_view(),
        name="review",
    ),
    path(
        "<uuid:pk>/approve/",
        views.DocumentApproveView.as_view(),
        name="approve",
    ),
    path(
        "<uuid:pk>/publish/",
        views.DocumentPublishView.as_view(),
        name="publish",
    ),
    path(
        "<uuid:pk>/unpublish/",
        views.DocumentUnpublishView.as_view(),
        name="unpublish",
    ),
    # ── Archive / Restore ────────────────────────────────────────────
    path(
        "<uuid:pk>/archive/",
        views.DocumentArchiveView.as_view(),
        name="archive",
    ),
    path(
        "<uuid:pk>/restore/",
        views.DocumentRestoreView.as_view(),
        name="restore",
    ),
    # ── Sharing ───────────────────────────────────────────────────────
    path(
        "<uuid:pk>/share/",
        views.DocumentShareCreateView.as_view(),
        name="share",
    ),
    path(
        "shares/<uuid:share_pk>/revoke/",
        views.DocumentShareRevokeView.as_view(),
        name="share_revoke",
    ),
    # ── Holds ─────────────────────────────────────────────────────────
    path(
        "<uuid:pk>/hold/",
        views.DocumentHoldCreateView.as_view(),
        name="hold",
    ),
    path(
        "holds/<uuid:hold_pk>/release/",
        views.DocumentHoldReleaseView.as_view(),
        name="hold_release",
    ),
    # ── Disposal ──────────────────────────────────────────────────────
    path(
        "<uuid:pk>/disposal/",
        views.DocumentDisposalRequestView.as_view(),
        name="disposal",
    ),
    # ── Delete ────────────────────────────────────────────────────────
    path("<uuid:pk>/delete/", views.DocumentDeleteView.as_view(), name="delete"),
    # ── Folders ───────────────────────────────────────────────────────
    path("folders/", views.DocumentFolderListView.as_view(), name="folder_list"),
    path(
        "folders/new/",
        views.DocumentFolderCreateView.as_view(),
        name="folder_create",
    ),
    path(
        "folders/<uuid:pk>/",
        views.DocumentFolderView.as_view(),
        name="folder_detail",
    ),
    # ── Categories ────────────────────────────────────────────────────
    path(
        "categories/",
        views.DocumentCategoryListView.as_view(),
        name="category_list",
    ),
    path(
        "categories/<uuid:pk>/",
        views.DocumentCategoryDetailView.as_view(),
        name="category_detail",
    ),
    # ── Audit ─────────────────────────────────────────────────────────
    path(
        "<uuid:pk>/audit/",
        views.DocumentAuditLogView.as_view(),
        name="audit_log",
    ),
    path(
        "audit/",
        views.DocumentAuditLogListView.as_view(),
        name="audit_log_list",
    ),
]
