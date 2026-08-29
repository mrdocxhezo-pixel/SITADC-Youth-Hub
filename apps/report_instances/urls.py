"""URL configuration for the ``report_instances`` app (Phase 20).

All routes are namespaced under ``report_instances``.
"""

from django.urls import path

from . import views

app_name = "report_instances"

urlpatterns = [
    # Dashboard
    path("", views.ReportDashboardView.as_view(), name="dashboard"),
    path("list/", views.ReportListView.as_view(), name="list"),
    # CRUD
    path("create/", views.ReportCreateView.as_view(), name="create"),
    path(
        "create-from-template/<uuid:template_id>/",
        views.ReportCreateFromTemplateView.as_view(),
        name="create_from_template",
    ),
    path("<uuid:pk>/", views.ReportDetailView.as_view(), name="detail"),
    path("<uuid:pk>/edit/", views.ReportEditView.as_view(), name="edit"),
    path("<uuid:pk>/duplicate/", views.ReportDuplicateView.as_view(), name="duplicate"),
    # Data Entry
    path(
        "<uuid:pk>/enter-data/", views.ReportDataEntryView.as_view(), name="enter_data"
    ),
    # Lifecycle
    path("<uuid:pk>/submit/", views.ReportSubmitView.as_view(), name="submit"),
    path("<uuid:pk>/withdraw/", views.ReportWithdrawView.as_view(), name="withdraw"),
    path("<uuid:pk>/resubmit/", views.ReportResubmitView.as_view(), name="resubmit"),
    path("<uuid:pk>/validate/", views.ReportValidateView.as_view(), name="validate"),
    path("<uuid:pk>/archive/", views.ReportArchiveView.as_view(), name="archive"),
    path("<uuid:pk>/restore/", views.ReportRestoreView.as_view(), name="restore"),
    # Review Actions
    path("<uuid:pk>/review/", views.ReportReviewView.as_view(), name="review"),
    path(
        "<uuid:pk>/start-review/",
        views.ReportStartReviewView.as_view(),
        name="start_review",
    ),
    # Comments
    path("<uuid:pk>/comment/", views.ReportCommentView.as_view(), name="comment"),
    # Evidence & Attachments
    path("<uuid:pk>/evidence/", views.ReportEvidenceView.as_view(), name="evidence"),
    path(
        "<uuid:pk>/video-link/", views.ReportVideoLinkView.as_view(), name="video_link"
    ),
    path(
        "<uuid:pk>/attachment/", views.ReportAttachmentView.as_view(), name="attachment"
    ),
    # Version History
    path("<uuid:pk>/versions/", views.ReportVersionsView.as_view(), name="versions"),
    path(
        "<uuid:pk>/versions/<int:version_number>/",
        views.ReportVersionDetailView.as_view(),
        name="version_detail",
    ),
    # Export & Preview
    path("<uuid:pk>/export/", views.ReportExportView.as_view(), name="export"),
    path("<uuid:pk>/preview/", views.ReportPreviewView.as_view(), name="preview"),
    path("<uuid:pk>/presubmit-review/", views.ReportPreSubmitReviewView.as_view(), name="presubmit_review"),
    # Assignment
    path("<uuid:pk>/assign/", views.ReportAssignView.as_view(), name="assign"),
    # API
    path("<uuid:pk>/autosave/", views.ReportAutoSaveView.as_view(), name="autosave"),
    path(
        "api/template/<uuid:template_id>/fields/",
        views.ReportTemplateFieldsView.as_view(),
        name="template_fields",
    ),
    # Delete (drafts only)
    path("<uuid:pk>/delete/", views.ReportDeleteView.as_view(), name="delete"),
]
