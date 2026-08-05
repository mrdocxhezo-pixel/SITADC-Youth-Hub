"""
Permission helpers and constants for the organizational structure module.

Authorization is always enforced on the server; these helpers centralize the
permission checks used across views, services and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

ORGANIZATIONS_VIEW = "organizations.view"
ORGANIZATIONS_CREATE = "organizations.create"
ORGANIZATIONS_UPDATE = "organizations.update"
ORGANIZATIONS_DELETE = "organizations.delete"
ORGANIZATIONS_ARCHIVE = "organizations.archive"
ORGANIZATIONS_RESTORE = "organizations.restore"
ORGANIZATIONS_EXPORT = "organizations.export"
ORGANIZATIONS_ASSIGN = "organizations.assign"
ORGANIZATIONS_MANAGE = "organizations.manage"

VIEW_PERMISSIONS: tuple[str, ...] = (ORGANIZATIONS_VIEW,)
MANAGE_PERMISSIONS: tuple[str, ...] = (
    ORGANIZATIONS_VIEW,
    ORGANIZATIONS_CREATE,
    ORGANIZATIONS_UPDATE,
    ORGANIZATIONS_DELETE,
    ORGANIZATIONS_ARCHIVE,
    ORGANIZATIONS_RESTORE,
    ORGANIZATIONS_EXPORT,
    ORGANIZATIONS_ASSIGN,
    ORGANIZATIONS_MANAGE,
)
ASSIGN_PERMISSIONS: tuple[str, ...] = (ORGANIZATIONS_VIEW, ORGANIZATIONS_ASSIGN)


def user_can_view(user) -> bool:
    return user_has_permission(user, ORGANIZATIONS_VIEW)


def user_can_manage(user) -> bool:
    return user_has_permission(user, ORGANIZATIONS_MANAGE)


def user_can_assign(user) -> bool:
    return user_has_permission(user, ORGANIZATIONS_ASSIGN)
