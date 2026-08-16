from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("", views.organizations_index_view, name="organizations_index"),
    path("units/", views.unit_list_view, name="unit_list"),
    path("units/new/", views.unit_create_view, name="unit_create"),
    path("units/<uuid:unit_id>/", views.unit_detail_view, name="unit_detail"),
    path("units/<uuid:unit_id>/update/", views.unit_update_view, name="unit_update"),
    path("units/<uuid:unit_id>/archive/", views.unit_archive_view, name="unit_archive"),
    path("units/<uuid:unit_id>/restore/", views.unit_restore_view, name="unit_restore"),
    path("units/<uuid:unit_id>/status/", views.unit_status_view, name="unit_status"),
    path("units/<uuid:unit_id>/parent/", views.unit_parent_view, name="unit_parent"),
    path("positions/", views.position_list_view, name="position_list"),
    path("positions/new/", views.position_create_view, name="position_create"),
    path("positions/<slug:slug>/", views.position_detail_view, name="position_detail"),
    path(
        "positions/<slug:slug>/update/",
        views.position_update_view,
        name="position_update",
    ),
    path(
        "positions/<slug:slug>/archive/",
        views.position_archive_view,
        name="position_archive",
    ),
    path(
        "positions/<slug:slug>/restore/",
        views.position_restore_view,
        name="position_restore",
    ),
    path(
        "positions/<slug:slug>/status/",
        views.position_status_view,
        name="position_status",
    ),
    path(
        "positions/<slug:slug>/reporting/",
        views.position_reporting_view,
        name="position_reporting",
    ),
    path(
        "positions/<slug:slug>/assign/",
        views.position_assign_view,
        name="position_assign",
    ),
    path(
        "positions/<slug:slug>/acting/new/",
        views.acting_create_view,
        name="acting_create",
    ),
    path(
        "assignments/<uuid:assignment_id>/end/",
        views.assignment_end_view,
        name="assignment_end",
    ),
    path(
        "assignments/<uuid:assignment_id>/revoke/",
        views.assignment_revoke_view,
        name="assignment_revoke",
    ),
    path(
        "acting/<uuid:acting_id>/end/",
        views.acting_end_view,
        name="acting_end",
    ),
    path(
        "acting/<uuid:acting_id>/revoke/",
        views.acting_revoke_view,
        name="acting_revoke",
    ),
    path("vacancies/", views.vacancy_list_view, name="vacancy_list"),
    path("vacancies/new/", views.vacancy_create_view, name="vacancy_create"),
    path(
        "vacancies/<uuid:vacancy_id>/status/",
        views.vacancy_status_view,
        name="vacancy_status",
    ),
    path("transfers/", views.transfer_list_view, name="transfer_list"),
    path("transfers/new/", views.transfer_create_view, name="transfer_create"),
    path(
        "transfers/<uuid:transfer_id>/approve/",
        views.transfer_approve_view,
        name="transfer_approve",
    ),
    path(
        "transfers/<uuid:transfer_id>/complete/",
        views.transfer_complete_view,
        name="transfer_complete",
    ),
    path("audit/", views.audit_list_view, name="organization_audit"),
    path("catalogues/", views.catalogue_list_view, name="catalogue_list"),
    path("catalogues/levels/new/", views.level_create_view, name="level_create"),
    path(
        "catalogues/classifications/new/",
        views.classification_create_view,
        name="classification_create",
    ),
]
