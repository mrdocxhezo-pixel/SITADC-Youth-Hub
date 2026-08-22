"""
URL configuration for the Security Hardening framework.
"""

from django.urls import path

from . import views

app_name = "security"

urlpatterns = [
    # Dashboard
    path("", views.security_dashboard_view, name="dashboard"),
    path("dashboard/api/", views.security_dashboard_api, name="dashboard_api"),

    # Access denied
    path("access-denied/", views.security_access_denied_view, name="access_denied"),

    # Security Policies
    path("policies/", views.security_policy_list_view, name="policy_list"),
    path("policies/create/", views.security_policy_create_view, name="policy_create"),
    path("policies/<slug:slug>/", views.security_policy_detail_view, name="policy_detail"),
    path("policies/<slug:slug>/update/", views.security_policy_update_view, name="policy_update"),

    # Identities
    path("identities/", views.identity_list_view, name="identity_list"),
    path("identities/create/", views.identity_create_view, name="identity_create"),
    path("identities/<int:pk>/", views.identity_detail_view, name="identity_detail"),
    path("identities/<int:pk>/update/", views.identity_update_view, name="identity_update"),

    # Permissions
    path("permissions/", views.permission_list_view, name="permission_list"),
    path("permissions/create/", views.permission_create_view, name="permission_create"),

    # Role Permissions
    path("roles/<slug:role_slug>/permissions/", views.role_permission_list_view, name="role_permissions"),
    path("roles/<slug:role_slug>/permissions/grant/", views.role_permission_grant_view, name="role_permission_grant"),
    path("roles/<slug:role_slug>/permissions/<int:permission_id>/revoke/", views.role_permission_revoke_view, name="role_permission_revoke"),

    # Identity Roles
    path("identities/<int:identity_pk>/roles/", views.identity_role_list_view, name="identity_roles"),
    path("identities/<int:identity_pk>/roles/assign/", views.identity_role_assign_view, name="identity_role_assign"),
    path("identities/<int:identity_pk>/roles/<slug:role_slug>/revoke/", views.identity_role_revoke_view, name="identity_role_revoke"),

    # Permission Grants
    path("identities/<int:identity_pk>/permission-grants/", views.permission_grant_list_view, name="permission_grants"),
    path("identities/<int:identity_pk>/permission-grants/create/", views.permission_grant_create_view, name="permission_grant_create"),
    path("identities/<int:identity_pk>/permission-grants/<int:permission_id>/revoke/", views.permission_grant_revoke_view, name="permission_grant_revoke"),

    # Role Hierarchy
    path("role-hierarchies/", views.role_hierarchy_list_view, name="role_hierarchy_list"),
    path("role-hierarchies/create/", views.role_hierarchy_create_view, name="role_hierarchy_create"),

    # Login Attempts
    path("login-attempts/", views.login_attempt_list_view, name="login_attempt_list"),
    path("login-attempts/<int:pk>/", views.login_attempt_detail_view, name="login_attempt_detail"),

    # Access Reviews
    path("access-reviews/", views.access_review_list_view, name="access_review_list"),
    path("access-reviews/create/", views.access_review_create_view, name="access_review_create"),
    path("access-reviews/<int:pk>/", views.access_review_detail_view, name="access_review_detail"),
    path("access-reviews/<int:pk>/start/", views.access_review_start_view, name="access_review_start"),
    path("access-reviews/<int:pk>/complete/", views.access_review_complete_view, name="access_review_complete"),
    path("access-review-items/<int:item_pk>/", views.access_review_item_view, name="access_review_item"),

    # Sessions
    path("sessions/", views.session_list_view, name="session_list"),
    path("sessions/<int:pk>/", views.session_detail_view, name="session_detail"),
    path("sessions/<int:pk>/terminate/", views.session_terminate_view, name="session_terminate"),
    path("sessions/<int:pk>/extend/", views.session_extend_view, name="session_extend"),

    # MFA
    path("identities/<int:identity_pk>/mfa/", views.mfa_enrollment_list_view, name="mfa_enrollments"),
    path("identities/<int:identity_pk>/mfa/create/", views.mfa_enrollment_create_view, name="mfa_enrollment_create"),
    path("mfa/verify/", views.mfa_verification_view, name="mfa_verify"),

    # API Credentials
    path("identities/<int:identity_pk>/api-credentials/", views.api_credential_list_view, name="api_credentials"),
    path("identities/<int:identity_pk>/api-credentials/create/", views.api_credential_create_view, name="api_credential_create"),
    path("identities/<int:identity_pk>/api-credentials/<int:credential_pk>/rotate/", views.api_credential_rotate_view, name="api_credential_rotate"),
    path("identities/<int:identity_pk>/api-credentials/<int:credential_pk>/revoke/", views.api_credential_revoke_view, name="api_credential_revoke"),

    # Database Security
    path("database-policies/", views.database_policy_list_view, name="database_policies"),
    path("database-policies/create/", views.database_policy_create_view, name="database_policy_create"),
    path("database-policies/<int:policy_pk>/logs/", views.database_access_log_view, name="database_access_logs"),

    # Secure Files
    path("secure-files/", views.secure_file_list_view, name="secure_file_list"),
    path("secure-files/create/", views.secure_file_create_view, name="secure_file_create"),
    path("secure-files/<int:pk>/", views.secure_file_detail_view, name="secure_file_detail"),
]