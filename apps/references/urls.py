"""URL routing for the reference numbering module."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.references_index_view, name="references_index"),
    path("schemes/", views.scheme_list_view, name="scheme_list"),
    path("schemes/new/", views.scheme_create_view, name="scheme_create"),
    path("schemes/<uuid:scheme_id>/", views.scheme_detail_view, name="scheme_detail"),
    path(
        "schemes/<uuid:scheme_id>/edit/",
        views.scheme_update_view,
        name="scheme_edit",
    ),
    path(
        "schemes/<uuid:scheme_id>/activate/",
        views.scheme_activate_view,
        name="scheme_activate",
    ),
    path(
        "schemes/<uuid:scheme_id>/deactivate/",
        views.scheme_deactivate_view,
        name="scheme_deactivate",
    ),
    path(
        "schemes/<uuid:scheme_id>/archive/",
        views.scheme_archive_view,
        name="scheme_archive",
    ),
    path(
        "schemes/<uuid:scheme_id>/restore/",
        views.scheme_restore_view,
        name="scheme_restore",
    ),
    path(
        "schemes/<uuid:scheme_id>/reset/",
        views.scheme_reset_view,
        name="scheme_reset",
    ),
    path("preview/", views.scheme_preview_view, name="scheme_preview"),
    path("registry/", views.registry_view, name="reference_registry"),
    path("sequences/", views.sequence_list_view, name="sequence_list"),
    path("audit/", views.audit_list_view, name="audit_list"),
    path(
        "registry/<uuid:generated_id>/correct/",
        views.correct_reference_view,
        name="reference_correct",
    ),
]
