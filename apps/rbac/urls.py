from django.urls import path

from . import views

app_name = "rbac"

urlpatterns = [
    path("", views.rbac_index_view, name="rbac_index"),
    path("access-denied/", views.access_denied_view, name="access_denied"),
    path("roles/", views.role_list_view, name="role_list"),
    path("roles/new/", views.role_create_view, name="role_create"),
    path("roles/<slug:slug>/", views.role_detail_view, name="role_detail"),
    path("roles/<slug:slug>/update/", views.role_update_view, name="role_update"),
    path(
        "roles/<slug:slug>/permissions/",
        views.role_permissions_view,
        name="role_permissions",
    ),
    path("roles/<slug:slug>/archive/", views.role_archive_view, name="role_archive"),
    path("roles/<slug:slug>/restore/", views.role_restore_view, name="role_restore"),
    path("roles/<slug:slug>/activate/", views.role_activate_view, name="role_activate"),
    path(
        "roles/<slug:slug>/deactivate/",
        views.role_deactivate_view,
        name="role_deactivate",
    ),
    path("roles/<slug:slug>/clone/", views.role_clone_view, name="role_clone"),
    path("roles/<slug:slug>/delete/", views.role_delete_view, name="role_delete"),
    path(
        "roles/<slug:slug>/assignments/",
        views.role_assignments_view,
        name="role_assignments",
    ),
    path(
        "roles/<slug:slug>/assignments/create/",
        views.role_assignment_create_view,
        name="role_assignment_create",
    ),
    path(
        "roles/<slug:slug>/history/",
        views.role_history_view,
        name="role_history",
    ),
    path(
        "assignments/<uuid:assignment_id>/revoke/",
        views.role_assignment_revoke_view,
        name="role_assignment_revoke",
    ),
    path("permissions/", views.permission_list_view, name="permission_list"),
    path("permissions/matrix/", views.permission_matrix_view, name="permission_matrix"),
    path("scopes/", views.access_scope_list_view, name="access_scope_list"),
]
