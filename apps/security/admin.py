"""
Admin configuration for the Security Hardening framework.
"""

from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    EnterpriseSecurityPolicy,
    Identity,
    ServiceIdentity,
    OrganizationalIdentity,
    Permission,
    RolePermission,
    IdentityRole,
    LoginAttempt,
    AccessReview,
    AccessReviewItem,
    RoleHierarchy,
    PermissionGrant,
    Session,
    MFAEnrollment,
    MFAVerificationAttempt,
    APICredential,
    APIAccessToken,
    APIRateLimit,
    DatabaseSecurityPolicy,
    DatabaseAccessLog,
    SecureFile,
)


@admin.register(EnterpriseSecurityPolicy)
class EnterpriseSecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "policy_type", "enforcement_level", "is_active", "effective_date", "expiry_date", "created_at")
    list_filter = ("policy_type", "enforcement_level", "is_active", "created_at")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("slug", "created_at", "updated_at", "created_by", "updated_by", "reviewed_by", "reviewed_at", "approved_by", "approved_at")
    ordering = ("policy_type", "name")
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "slug", "policy_type", "description")
        }),
        (_("Policy Rules"), {
            "fields": ("rules", "enforcement_level", "scope", "exceptions")
        }),
        (_("Status"), {
            "fields": ("is_active", "effective_date", "expiry_date")
        }),
        (_("Review & Approval"), {
            "fields": ("reviewed_by", "reviewed_at", "approved_by", "approved_at"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Identity)
class IdentityAdmin(admin.ModelAdmin):
    list_display = ("identifier", "display_name", "identity_type", "status", "confidentiality", "owner", "is_expired", "created_at")
    list_filter = ("identity_type", "status", "confidentiality", "created_at")
    search_fields = ("identifier", "display_name", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "last_used_at")
    ordering = ("identity_type", "identifier")
    autocomplete_fields = ("owner", "managed_by")
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("identity_type", "identifier", "display_name", "description")
        }),
        (_("Status & Security"), {
            "fields": ("status", "confidentiality", "expires_at")
        }),
        (_("Ownership"), {
            "fields": ("owner", "managed_by")
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by", "last_used_at"),
            "classes": ("collapse",)
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = _("Expired")


@admin.register(ServiceIdentity)
class ServiceIdentityAdmin(IdentityAdmin):
    list_display = ("identifier", "display_name", "service_type", "status", "confidentiality", "owner", "is_expired", "created_at")
    list_filter = ("service_type", "status", "confidentiality", "created_at")
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("identity_type", "identifier", "display_name", "description")
        }),
        (_("Service Details"), {
            "fields": ("service_type", "service_account_token", "token_expires_at", "ip_allowlist", "allowed_operations")
        }),
        (_("Status & Security"), {
            "fields": ("status", "confidentiality", "expires_at")
        }),
        (_("Ownership"), {
            "fields": ("owner", "managed_by")
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by", "last_used_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(OrganizationalIdentity)
class OrganizationalIdentityAdmin(IdentityAdmin):
    list_display = ("identifier", "display_name", "org_identity_type", "organization_unit", "status", "confidentiality", "is_expired", "created_at")
    list_filter = ("org_identity_type", "status", "confidentiality", "organization_unit", "created_at")
    autocomplete_fields = ("owner", "managed_by", "parent_organization", "organization_unit", "contact_person")
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("identity_type", "identifier", "display_name", "description")
        }),
        (_("Organizational Details"), {
            "fields": ("org_identity_type", "parent_organization", "organization_unit", "contact_person")
        }),
        (_("Status & Security"), {
            "fields": ("status", "confidentiality", "expires_at")
        }),
        (_("Ownership"), {
            "fields": ("owner", "managed_by")
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by", "last_used_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "name", "module", "resource_type", "action", "is_system", "is_assignable", "requires_approval")
    list_filter = ("module", "resource_type", "is_system", "is_assignable", "requires_approval")
    search_fields = ("name", "slug", "module", "resource_type", "action", "description")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("module", "resource_type", "action", "name")
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "slug", "description")
        }),
        (_("Permission Structure"), {
            "fields": ("module", "resource_type", "action")
        }),
        (_("Properties"), {
            "fields": ("is_system", "is_assignable", "requires_approval", "conditions")
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ("role", "permission", "is_active", "granted_by", "granted_at", "expires_at", "is_expired")
    list_filter = ("is_active", "role", "permission__module", "granted_at")
    search_fields = ("role__name", "permission__name", "permission__module")
    readonly_fields = ("granted_at", "created_at", "updated_at")
    autocomplete_fields = ("role", "permission", "granted_by")
    ordering = ("-granted_at",)
    fieldsets = (
        (_("Assignment"), {
            "fields": ("role", "permission", "granted_by")
        }),
        (_("Validity"), {
            "fields": ("is_active", "expires_at", "conditions")
        }),
        (_("Justification"), {
            "fields": ("justification",)
        }),
        (_("Audit"), {
            "fields": ("granted_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = _("Expired")


@admin.register(IdentityRole)
class IdentityRoleAdmin(admin.ModelAdmin):
    list_display = ("identity", "role", "is_active", "assigned_by", "assigned_at", "expires_at", "is_expired")
    list_filter = ("is_active", "role", "assigned_at")
    search_fields = ("identity__identifier", "identity__display_name", "role__name")
    readonly_fields = ("assigned_at", "created_at", "updated_at")
    autocomplete_fields = ("identity", "role", "assigned_by")
    ordering = ("-assigned_at",)
    fieldsets = (
        (_("Assignment"), {
            "fields": ("identity", "role", "assigned_by")
        }),
        (_("Validity"), {
            "fields": ("is_active", "expires_at", "conditions", "delegation_chain")
        }),
        (_("Justification"), {
            "fields": ("justification",)
        }),
        (_("Audit"), {
            "fields": ("assigned_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = _("Expired")


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("username_attempted", "ip_address", "outcome", "identity", "risk_score", "is_suspicious", "created_at")
    list_filter = ("outcome", "is_suspicious", "created_at")
    search_fields = ("username_attempted", "ip_address", "failure_reason", "identity__identifier")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (_("Attempt Details"), {
            "fields": ("identity", "username_attempted", "ip_address", "user_agent")
        }),
        (_("Outcome"), {
            "fields": ("outcome", "failure_reason")
        }),
        (_("Security Assessment"), {
            "fields": ("risk_score", "is_suspicious", "country_code", "city")
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        return False  # Login attempts are created automatically


@admin.register(AccessReview)
class AccessReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "review_type", "status", "started_at", "due_date", "completed_at", "lead_reviewer", "completion_percentage")
    list_filter = ("review_type", "status", "started_at", "due_date")
    search_fields = ("name", "description")
    readonly_fields = ("started_at", "completed_at", "total_items_reviewed", "items_approved", "items_revoked", "items_modified", "items_escalated", "created_at", "updated_at")
    autocomplete_fields = ("target_identity", "target_role", "target_permission", "reviewers", "lead_reviewer", "created_by")
    ordering = ("-started_at",)
    date_hierarchy = "started_at"
    filter_horizontal = ("reviewers",)
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "description", "review_type")
        }),
        (_("Scope"), {
            "fields": ("target_identity", "target_role", "target_permission")
        }),
        (_("Schedule"), {
            "fields": ("started_at", "due_date", "completed_at")
        }),
        (_("Status & Progress"), {
            "fields": ("status", "total_items_reviewed", "items_approved", "items_revoked", "items_modified", "items_escalated")
        }),
        (_("Configuration"), {
            "fields": ("auto_approve_low_risk", "require_justification_for_changes", "escalate_overdue_reviews")
        }),
        (_("Reviewers"), {
            "fields": ("reviewers", "lead_reviewer")
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )

    def completion_percentage(self, obj):
        return f"{obj.completion_percentage:.1f}%"
    completion_percentage.short_description = _("Completion")


@admin.register(AccessReviewItem)
class AccessReviewItemAdmin(admin.ModelAdmin):
    list_display = ("access_review", "get_target", "decision", "reviewer", "reviewed_at", "risk_level")
    list_filter = ("decision", "risk_level", "access_review__review_type", "reviewed_at")
    search_fields = ("access_review__name", "identity__identifier", "role__name", "permission__name")
    readonly_fields = ("reviewed_at", "created_at", "updated_at")
    autocomplete_fields = ("access_review", "identity", "role", "permission", "identity_role", "reviewer")
    ordering = ("-reviewed_at",)
    fieldsets = (
        (_("Review"), {
            "fields": ("access_review",)
        }),
        (_("Target"), {
            "fields": ("identity", "role", "permission", "identity_role")
        }),
        (_("Decision"), {
            "fields": ("reviewer", "reviewed_at", "decision", "justification", "new_value", "change_reason")
        }),
        (_("Risk Assessment"), {
            "fields": ("risk_level", "risk_factors")
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def get_target(self, obj):
        if obj.identity:
            return f"Identity: {obj.identity.display_name}"
        elif obj.role:
            return f"Role: {obj.role.name}"
        elif obj.permission:
            return f"Permission: {obj.permission.name}"
        return "-"
    get_target.short_description = _("Target")


@admin.register(RoleHierarchy)
class RoleHierarchyAdmin(admin.ModelAdmin):
    list_display = ("parent_role", "child_role", "inherit_permissions", "inherit_role_permissions", "created_by", "created_at")
    list_filter = ("inherit_permissions", "inherit_role_permissions", "created_at")
    search_fields = ("parent_role__name", "child_role__name")
    readonly_fields = ("created_at", "updated_at", "created_by")
    autocomplete_fields = ("parent_role", "child_role", "created_by")
    ordering = ("parent_role__priority", "child_role__priority")
    fieldsets = (
        (_("Hierarchy"), {
            "fields": ("parent_role", "child_role")
        }),
        (_("Inheritance"), {
            "fields": ("inherit_permissions", "inherit_role_permissions")
        }),
        (_("Justification"), {
            "fields": ("justification",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(PermissionGrant)
class PermissionGrantAdmin(admin.ModelAdmin):
    list_display = ("identity", "permission", "is_active", "granted_by", "granted_at", "expires_at", "is_expired")
    list_filter = ("is_active", "permission__module", "granted_at")
    search_fields = ("identity__identifier", "permission__name")
    readonly_fields = ("granted_at", "created_at", "updated_at")
    autocomplete_fields = ("identity", "permission", "granted_by")
    ordering = ("-granted_at",)
    fieldsets = (
        (_("Grant"), {
            "fields": ("identity", "permission", "granted_by")
        }),
        (_("Validity"), {
            "fields": ("is_active", "expires_at", "conditions")
        }),
        (_("Justification"), {
            "fields": ("justification",)
        }),
        (_("Audit"), {
            "fields": ("granted_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_expired(self, obj):
        return obj.is_expired
    is_expired.boolean = True
    is_expired.short_description = _("Expired")


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("identity", "session_key_short", "ip_address", "status", "is_active", "started_at", "last_activity_at", "expires_at")
    list_filter = ("status", "is_secure", "is_mfa_used", "started_at")
    search_fields = ("identity__identifier", "session_key", "ip_address", "device_fingerprint")
    readonly_fields = ("session_key", "started_at", "last_activity_at", "created_at", "updated_at")
    autocomplete_fields = ("identity", "superseded_by", "supersedes")
    ordering = ("-started_at",)
    date_hierarchy = "started_at"
    fieldsets = (
        (_("Session"), {
            "fields": ("identity", "session_key", "ip_address", "user_agent")
        }),
        (_("Status"), {
            "fields": ("status", "started_at", "last_activity_at", "expires_at", "terminated_at")
        }),
        (_("Timeouts"), {
            "fields": ("idle_timeout_minutes", "absolute_timeout_minutes")
        }),
        (_("Security"), {
            "fields": ("is_secure", "is_mfa_used", "mfa_method", "device_fingerprint")
        }),
        (_("Concurrency"), {
            "fields": ("superseded_by", "supersedes"),
            "classes": ("collapse",)
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def session_key_short(self, obj):
        return f"{obj.session_key[:8]}..."
    session_key_short.short_description = _("Session Key")

    def is_active(self, obj):
        return obj.is_active
    is_active.boolean = True
    is_active.short_description = _("Active")

    def has_add_permission(self, request):
        return False  # Sessions are created automatically


@admin.register(MFAEnrollment)
class MFAEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("identity", "method", "is_primary", "is_backup", "is_enabled", "is_trusted", "enrolled_at", "last_used_at")
    list_filter = ("method", "is_primary", "is_backup", "is_enabled", "is_trusted_device", "enrolled_at")
    search_fields = ("identity__identifier", "identity__display_name", "name", "phone_number", "email_address")
    readonly_fields = ("enrolled_at", "created_at", "updated_at", "last_used_at", "usage_count", "failed_attempt_count", "locked_until", "backup_codes_used")
    autocomplete_fields = ("identity", "enrolled_by")
    ordering = ("-is_primary", "-enrolled_at")
    fieldsets = (
        (_("Enrollment"), {
            "fields": ("identity", "method", "enrolled_by")
        }),
        (_("Configuration"), {
            "fields": ("is_primary", "is_backup", "is_enabled", "name")
        }),
        (_("Method-Specific"), {
            "fields": ("secret_key", "phone_number", "email_address")
        }),
        (_("Backup Codes"), {
            "fields": ("backup_codes", "backup_codes_used"),
            "classes": ("collapse",)
        }),
        (_("Trusted Device"), {
            "fields": ("is_trusted_device", "device_name", "device_fingerprint", "trusted_since", "trust_expires_at")
        }),
        (_("Usage Statistics"), {
            "fields": ("last_used_at", "usage_count", "failed_attempt_count", "locked_until"),
            "classes": ("collapse",)
        }),
        (_("Metadata"), {
            "fields": ("attributes",),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("enrolled_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_trusted(self, obj):
        return obj.is_trusted
    is_trusted.boolean = True
    is_trusted.short_description = _("Trusted")


@admin.register(MFAVerificationAttempt)
class MFAVerificationAttemptAdmin(admin.ModelAdmin):
    list_display = ("identity", "enrollment", "outcome", "trusted_device", "backup_code_used", "risk_score", "is_suspicious", "attempted_at")
    list_filter = ("outcome", "trusted_device", "backup_code_used", "is_suspicious", "attempted_at")
    search_fields = ("identity__identifier", "challenge", "response")
    readonly_fields = ("attempted_at", "created_at", "updated_at")
    autocomplete_fields = ("identity", "enrollment")
    ordering = ("-attempted_at",)
    date_hierarchy = "attempted_at"
    fieldsets = (
        (_("Attempt"), {
            "fields": ("identity", "enrollment", "challenge", "response", "ip_address", "user_agent")
        }),
        (_("Outcome"), {
            "fields": ("outcome", "expires_at", "trusted_device", "backup_code_used")
        }),
        (_("Risk Assessment"), {
            "fields": ("risk_score", "is_suspicious", "country_code", "city")
        }),
        (_("Audit"), {
            "fields": ("attempted_at", "created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        return False  # Verification attempts are created automatically


@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ("name", "credential_type", "service_name", "identity", "is_active", "is_valid", "last_used_at", "usage_count", "created_at")
    list_filter = ("credential_type", "is_active", "is_compromised", "created_at")
    search_fields = ("name", "slug", "service_name", "credential_key", "identity__identifier")
    readonly_fields = ("slug", "created_at", "updated_at", "last_used_at", "usage_count", "compromised_at")
    autocomplete_fields = ("identity",)
    ordering = ("-created_at",)
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "slug", "description", "credential_type")
        }),
        (_("Credential"), {
            "fields": ("credential_key", "credential_secret")
        }),
        (_("Service"), {
            "fields": ("service_name", "service_url")
        }),
        (_("Restrictions"), {
            "fields": ("ip_allowlist", "allowed_endpoints", "allowed_methods")
        }),
        (_("Rate Limiting"), {
            "fields": ("rate_limit_per_hour", "rate_limit_per_day")
        }),
        (_("Status"), {
            "fields": ("is_active", "expires_at", "is_compromised", "compromised_at", "compromised_reason")
        }),
        (_("Usage"), {
            "fields": ("last_used_at", "usage_count"),
            "classes": ("collapse",)
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )

    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = _("Valid")


@admin.register(APIAccessToken)
class APIAccessTokenAdmin(admin.ModelAdmin):
    list_display = ("credential", "token_short", "token_type", "identity", "is_valid", "issued_at", "expires_at", "last_used_at", "usage_count")
    list_filter = ("is_revoked", "issued_at", "expires_at")
    search_fields = ("token", "credential__name", "identity__identifier")
    readonly_fields = ("issued_at", "created_at", "updated_at", "last_used_at", "usage_count", "revoked_at")
    autocomplete_fields = ("credential", "identity")
    ordering = ("-issued_at",)
    fieldsets = (
        (_("Token"), {
            "fields": ("credential", "token", "token_type", "identity")
        }),
        (_("Scopes & Permissions"), {
            "fields": ("scopes", "permissions")
        }),
        (_("Validity"), {
            "fields": ("issued_at", "expires_at", "not_before")
        }),
        (_("Status"), {
            "fields": ("is_revoked", "revoked_at", "revoked_reason")
        }),
        (_("Usage"), {
            "fields": ("last_used_at", "usage_count"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def token_short(self, obj):
        return f"{obj.token[:20]}..."
    token_short.short_description = _("Token")

    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True
    is_valid.short_description = _("Valid")

    def has_add_permission(self, request):
        return False  # Tokens are created automatically


@admin.register(APIRateLimit)
class APIRateLimitAdmin(admin.ModelAdmin):
    list_display = ("credential", "identity", "window_start", "window_end", "request_count", "blocked_count", "endpoint", "method", "is_exceeded")
    list_filter = ("window_start", "endpoint", "method")
    search_fields = ("credential__name", "identity__identifier", "endpoint")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("credential", "identity")
    ordering = ("-window_start",)
    date_hierarchy = "window_start"
    fieldsets = (
        (_("Rate Limit"), {
            "fields": ("credential", "identity", "window_start", "window_end")
        }),
        (_("Counts"), {
            "fields": ("request_count", "blocked_count")
        }),
        (_("Details"), {
            "fields": ("endpoint", "method", "status_code", "ip_address")
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def is_exceeded(self, obj):
        return obj.is_exceeded
    is_exceeded.boolean = True
    is_exceeded.short_description = _("Exceeded")

    def has_add_permission(self, request):
        return False  # Rate limits are created automatically


@admin.register(DatabaseSecurityPolicy)
class DatabaseSecurityPolicyAdmin(admin.ModelAdmin):
    list_display = ("name", "database_type", "database_identifier", "host", "port", "require_ssl", "encryption_at_rest", "is_active", "validation_status", "created_at")
    list_filter = ("database_type", "require_ssl", "encryption_at_rest", "is_active", "validation_status", "created_at")
    search_fields = ("name", "slug", "database_identifier", "host", "database_name")
    readonly_fields = ("slug", "last_validated_at", "validation_status", "created_at", "updated_at")
    autocomplete_fields = ()
    ordering = ("name",)
    fieldsets = (
        (_("Basic Information"), {
            "fields": ("name", "slug", "description")
        }),
        (_("Database"), {
            "fields": ("database_identifier", "database_type", "host", "port", "database_name")
        }),
        (_("Security"), {
            "fields": ("require_ssl", "ssl_cert_path", "ssl_key_path", "auth_method")
        }),
        (_("Connection Pooling"), {
            "fields": ("use_connection_pooling", "max_connections")
        }),
        (_("Timeouts"), {
            "fields": ("statement_timeout_ms", "lock_timeout_ms")
        }),
        (_("Audit"), {
            "fields": ("audit_connections", "audit_statements", "audit_statement_level")
        }),
        (_("Encryption"), {
            "fields": ("encryption_at_rest", "encryption_key_identifier")
        }),
        (_("Access Control"), {
            "fields": ("allow_public_access", "allowed_networks")
        }),
        (_("Status"), {
            "fields": ("is_active", "last_validated_at", "validation_status")
        }),
        (_("Metadata"), {
            "fields": ("tags", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by"),
            "classes": ("collapse",)
        }),
    )


@admin.register(DatabaseAccessLog)
class DatabaseAccessLogAdmin(admin.ModelAdmin):
    list_display = ("database_policy", "username", "client_ip", "connection_status", "statement_type", "success", "connection_started")
    list_filter = ("database_policy", "connection_status", "success", "statement_type", "connection_started")
    search_fields = ("username", "client_ip", "client_hostname", "statement", "error_message")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("database_policy",)
    ordering = ("-connection_started",)
    date_hierarchy = "connection_started"
    fieldsets = (
        (_("Connection"), {
            "fields": ("database_policy", "session_id", "username", "client_ip", "client_hostname")
        }),
        (_("Timing"), {
            "fields": ("connection_started", "connection_ended", "statement_timestamp")
        }),
        (_("Status"), {
            "fields": ("connection_status", "success", "error_message", "error_code")
        }),
        (_("Statement"), {
            "fields": ("statement_type", "statement", "statement_duration_ms", "rows_affected")
        }),
        (_("Metadata"), {
            "fields": ("attributes",),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )

    def has_add_permission(self, request):
        return False  # Access logs are created automatically


@admin.register(SecureFile)
class SecureFileAdmin(admin.ModelAdmin):
    list_display = ("filename", "version", "owner", "uploaded_by", "file_size_human", "confidentiality", "is_encrypted", "virus_scan_status", "is_latest_version", "is_active", "created_at")
    list_filter = ("confidentiality", "is_encrypted", "virus_scan_status", "is_latest_version", "is_active", "is_deleted", "created_at")
    search_fields = ("filename", "original_filename", "owner__identifier", "uploaded_by__identifier", "storage_path")
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("owner", "uploaded_by", "allowed_identities", "allowed_roles", "replaced_by")
    filter_horizontal = ("allowed_identities", "allowed_roles")
    ordering = ("-created_at",)
    fieldsets = (
        (_("File Information"), {
            "fields": ("filename", "original_filename", "file_size", "content_type")
        }),
        (_("Storage"), {
            "fields": ("storage_path", "storage_bucket", "storage_region")
        }),
        (_("Ownership"), {
            "fields": ("owner", "uploaded_by")
        }),
        (_("Access Control"), {
            "fields": ("is_public", "allowed_identities", "allowed_roles")
        }),
        (_("Security Classification"), {
            "fields": ("confidentiality",)
        }),
        (_("Integrity"), {
            "fields": ("checksum_algorithm", "checksum_value", "previous_checksum")
        }),
        (_("Virus Scan"), {
            "fields": ("virus_scan_status", "virus_scan_at", "virus_scan_details")
        }),
        (_("Encryption"), {
            "fields": ("is_encrypted", "encryption_algorithm", "encryption_key_identifier")
        }),
        (_("Versioning"), {
            "fields": ("version", "is_latest_version", "replaced_by")
        }),
        (_("Retention"), {
            "fields": ("retention_date", "retention_policy", "legal_hold")
        }),
        (_("Status"), {
            "fields": ("is_active", "is_deleted", "deleted_at")
        }),
        (_("Metadata"), {
            "fields": ("upload_metadata", "attributes"),
            "classes": ("collapse",)
        }),
        (_("Audit"), {
            "fields": ("created_at", "updated_at", "created_by", "updated_by"),
            "classes": ("collapse",)
        }),
    )

    def file_size_human(self, obj):
        size = obj.file_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    file_size_human.short_description = _("Size")