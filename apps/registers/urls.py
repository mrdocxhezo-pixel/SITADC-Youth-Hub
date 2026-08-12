"""URL configuration for the Organizational Registers module."""

from django.urls import path

from . import views

app_name = "registers"

urlpatterns = [
    path("", views.RegisterDashboardView.as_view(), name="dashboard"),
    # Register categories
    path(
        "categories/",
        views.RegisterCategoryListView.as_view(),
        name="category_list",
    ),
    path(
        "categories/new/",
        views.RegisterCategoryCreateView.as_view(),
        name="category_create",
    ),
    path(
        "categories/<uuid:pk>/edit/",
        views.RegisterCategoryUpdateView.as_view(),
        name="category_update",
    ),
    # Registers
    path("registers/", views.RegisterListView.as_view(), name="register_list"),
    path("registers/new/", views.RegisterCreateView.as_view(), name="register_create"),
    path(
        "registers/<uuid:pk>/",
        views.RegisterDetailView.as_view(),
        name="register_detail",
    ),
    path(
        "registers/<uuid:pk>/edit/",
        views.RegisterUpdateView.as_view(),
        name="register_update",
    ),
    path(
        "registers/<uuid:pk>/archive/",
        views.RegisterArchiveView.as_view(),
        name="register_archive",
    ),
    path(
        "registers/<uuid:pk>/restore/",
        views.RegisterRestoreView.as_view(),
        name="register_restore",
    ),
    # Templates
    path("templates/", views.RegisterTemplateListView.as_view(), name="template_list"),
    path(
        "templates/new/",
        views.RegisterTemplateCreateView.as_view(),
        name="template_create",
    ),
    path(
        "templates/<uuid:pk>/edit/",
        views.RegisterTemplateUpdateView.as_view(),
        name="template_update",
    ),
    # Entries
    path("entries/", views.EntryListView.as_view(), name="entry_list"),
    path(
        "registers/<uuid:register_pk>/entries/new/",
        views.EntryCreateView.as_view(),
        name="entry_create",
    ),
    path(
        "entries/<uuid:pk>/",
        views.EntryDetailView.as_view(),
        name="entry_detail",
    ),
    path(
        "entries/<uuid:pk>/edit/",
        views.EntryUpdateView.as_view(),
        name="entry_update",
    ),
    path(
        "entries/<uuid:pk>/submit/",
        views.EntrySubmitView.as_view(),
        name="entry_submit",
    ),
    path(
        "entries/<uuid:pk>/review/",
        views.EntryStartReviewView.as_view(),
        name="entry_start_review",
    ),
    path(
        "entries/<uuid:pk>/approve/",
        views.EntryApproveView.as_view(),
        name="entry_approve",
    ),
    path(
        "entries/<uuid:pk>/return/",
        views.EntryReturnView.as_view(),
        name="entry_return",
    ),
    path(
        "entries/<uuid:pk>/reject/",
        views.EntryRejectView.as_view(),
        name="entry_reject",
    ),
    path(
        "entries/<uuid:pk>/archive/",
        views.EntryArchiveView.as_view(),
        name="entry_archive",
    ),
    path(
        "entries/<uuid:pk>/restore/",
        views.EntryRestoreView.as_view(),
        name="entry_restore",
    ),
    path(
        "entries/<uuid:entry_pk>/attachments/new/",
        views.EntryAttachmentCreateView.as_view(),
        name="attachment_create",
    ),
    # Exports
    path("export/", views.RegisterExportView.as_view(), name="export"),
    path(
        "export/<uuid:pk>/",
        views.RegisterExportView.as_view(),
        name="export_register",
    ),
    path(
        "export/<str:fmt>/",
        views.RegisterExportView.as_view(),
        name="export_format",
    ),
    path(
        "export/<uuid:pk>/<str:fmt>/",
        views.RegisterExportView.as_view(),
        name="export_register_format",
    ),
]
