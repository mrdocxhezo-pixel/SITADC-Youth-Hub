"""Permission constants and helpers for the Accessibility Review module."""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

# ──────────────────────────────────────────────────────────────────────────────
# Permission Codenames
# ──────────────────────────────────────────────────────────────────────────────

ACCESSIBILITY_VIEW = "accessibility.view"
ACCESSIBILITY_CREATE = "accessibility.create"
ACCESSIBILITY_UPDATE = "accessibility.update"
ACCESSIBILITY_DELETE = "accessibility.delete"
ACCESSIBILITY_CONFIGURE = "accessibility.configure"
ACCESSIBILITY_AUDIT = "accessibility.audit"
ACCESSIBILITY_TEST = "accessibility.test"
ACCESSIBILITY_REPORT = "accessibility.report"
ACCESSIBILITY_MANAGE = "accessibility.manage"
ACCESSIBILITY_APPROVE = "accessibility.approve"

# ──────────────────────────────────────────────────────────────────────────────
# Role-based Permission Groups
# ──────────────────────────────────────────────────────────────────────────────

ACCESSIBILITY_ADMIN_PERMS = (
    ACCESSIBILITY_VIEW,
    ACCESSIBILITY_CREATE,
    ACCESSIBILITY_UPDATE,
    ACCESSIBILITY_DELETE,
    ACCESSIBILITY_CONFIGURE,
    ACCESSIBILITY_AUDIT,
    ACCESSIBILITY_TEST,
    ACCESSIBILITY_REPORT,
    ACCESSIBILITY_MANAGE,
    ACCESSIBILITY_APPROVE,
)

ACCESSIBILITY_AUDITOR_PERMS = (
    ACCESSIBILITY_VIEW,
    ACCESSIBILITY_AUDIT,
    ACCESSIBILITY_TEST,
    ACCESSIBILITY_REPORT,
)

ACCESSIBILITY_DEVELOPER_PERMS = (
    ACCESSIBILITY_VIEW,
    ACCESSIBILITY_CREATE,
    ACCESSIBILITY_UPDATE,
    ACCESSIBILITY_TEST,
    ACCESSIBILITY_REPORT,
)

ACCESSIBILITY_USER_PERMS = (
    ACCESSIBILITY_VIEW,
    ACCESSIBILITY_TEST,  # Can run automated scans on their own content
)

# ──────────────────────────────────────────────────────────────────────────────
# Permission Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def can_view_accessibility(user) -> bool:
    """Check if user can view accessibility records."""
    return user_has_permission(user, ACCESSIBILITY_VIEW) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_create_accessibility(user) -> bool:
    """Check if user can create accessibility records."""
    return user_has_permission(user, ACCESSIBILITY_CREATE) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_update_accessibility(user) -> bool:
    """Check if user can update accessibility records."""
    return user_has_permission(user, ACCESSIBILITY_UPDATE) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_delete_accessibility(user) -> bool:
    """Check if user can delete accessibility records."""
    return user_has_permission(user, ACCESSIBILITY_DELETE) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_configure_accessibility(user) -> bool:
    """Check if user can configure accessibility settings."""
    return user_has_permission(user, ACCESSIBILITY_CONFIGURE) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_audit_accessibility(user) -> bool:
    """Check if user can perform accessibility audits."""
    return user_has_permission(user, ACCESSIBILITY_AUDIT) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_test_accessibility(user) -> bool:
    """Check if user can run accessibility tests."""
    return user_has_permission(user, ACCESSIBILITY_TEST) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_report_accessibility(user) -> bool:
    """Check if user can generate accessibility reports."""
    return user_has_permission(user, ACCESSIBILITY_REPORT) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_manage_accessibility(user) -> bool:
    """Check if user has full accessibility management permissions."""
    return user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_approve_accessibility(user) -> bool:
    """Check if user can approve accessibility changes."""
    return user_has_permission(user, ACCESSIBILITY_APPROVE) or user_has_permission(user, ACCESSIBILITY_MANAGE)


def can_view_own_preferences(user) -> bool:
    """Check if user can view their own accessibility preferences."""
    return user.is_authenticated


def can_update_own_preferences(user) -> bool:
    """Check if user can update their own accessibility preferences."""
    return user.is_authenticated
