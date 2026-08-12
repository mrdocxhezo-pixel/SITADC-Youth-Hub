"""URL routes for the Dynamic Report Builder module."""

from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.ReportBuilderDashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/", views.ReportBuilderDashboardView.as_view(), name="dashboard_alt"
    ),
    path("templates/", views.TemplateDirectoryView.as_view(), name="template_list"),
    path("templates/new/", views.TemplateCreateView.as_view(), name="template_create"),
    path(
        "templates/import/", views.TemplateImportView.as_view(), name="template_import"
    ),
    path(
        "templates/<uuid:pk>/",
        views.TemplateDetailView.as_view(),
        name="template_detail",
    ),
    path(
        "templates/<uuid:pk>/edit/",
        views.TemplateUpdateView.as_view(),
        name="template_update",
    ),
    path(
        "templates/<uuid:pk>/schema/",
        views.SchemaDesignerView.as_view(),
        name="template_schema",
    ),
    path(
        "templates/<uuid:pk>/preview/",
        views.TemplatePreviewView.as_view(),
        name="template_preview",
    ),
    path(
        "templates/<uuid:pk>/publish/",
        views.TemplatePublishView.as_view(),
        name="template_publish",
    ),
    path(
        "templates/<uuid:pk>/unpublish/",
        views.TemplateUnpublishView.as_view(),
        name="template_unpublish",
    ),
    path(
        "templates/<uuid:pk>/archive/",
        views.TemplateArchiveView.as_view(),
        name="template_archive",
    ),
    path(
        "templates/<uuid:pk>/restore/",
        views.TemplateRestoreView.as_view(),
        name="template_restore",
    ),
    path(
        "templates/<uuid:pk>/delete/",
        views.TemplateDeleteView.as_view(),
        name="template_delete",
    ),
    path(
        "templates/<uuid:pk>/clone/",
        views.TemplateCloneView.as_view(),
        name="template_clone",
    ),
    path(
        "templates/<uuid:pk>/export/",
        views.TemplateExportView.as_view(),
        name="template_export",
    ),
    path(
        "templates/<uuid:pk>/versions/",
        views.TemplateVersionListView.as_view(),
        name="template_version_list",
    ),
    path(
        "templates/<uuid:pk>/versions/<uuid:version_pk>/restore/",
        views.TemplateVersionRestoreView.as_view(),
        name="template_version_restore",
    ),
    path(
        "templates/<uuid:pk>/versions/<uuid:left_pk>/compare/<uuid:right_pk>/",
        views.TemplateVersionCompareView.as_view(),
        name="template_version_compare",
    ),
    path("categories/", views.CategoryDirectoryView.as_view(), name="category_list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path(
        "categories/<uuid:pk>/edit/",
        views.CategoryUpdateView.as_view(),
        name="category_update",
    ),
    path(
        "categories/<uuid:pk>/toggle/",
        views.CategoryToggleView.as_view(),
        name="category_toggle",
    ),
    path("settings/", views.ReportBuilderSettingsView.as_view(), name="settings"),
    path("browse/", views.CategoryBrowseView.as_view(), name="category_browse"),
    path(
        "browse/<uuid:pk>/",
        views.CategoryTemplateListView.as_view(),
        name="category_templates",
    ),
]
