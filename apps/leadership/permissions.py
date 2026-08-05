"""
Permission helpers and constants for the leadership management module.

Authorization is always enforced on the server; these helpers centralize the
permission checks used across views, services and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

LEADERSHIP_VIEW = "leadership.view"
LEADERSHIP_CREATE = "leadership.create"
LEADERSHIP_UPDATE = "leadership.update"
LEADERSHIP_DELETE = "leadership.delete"
LEADERSHIP_ARCHIVE = "leadership.archive"
LEADERSHIP_RESTORE = "leadership.restore"
LEADERSHIP_EXPORT = "leadership.export"
LEADERSHIP_ASSIGN = "leadership.assign"
LEADERSHIP_MANAGE = "leadership.manage"

VIEW_PERMISSIONS: tuple[str, ...] = (LEADERSHIP_VIEW,)
MANAGE_PERMISSIONS: tuple[str, ...] = (
    LEADERSHIP_VIEW,
    LEADERSHIP_CREATE,
    LEADERSHIP_UPDATE,
    LEADERSHIP_DELETE,
    LEADERSHIP_ARCHIVE,
    LEADERSHIP_RESTORE,
    LEADERSHIP_EXPORT,
    LEADERSHIP_ASSIGN,
    LEADERSHIP_MANAGE,
)
ASSIGN_PERMISSIONS: tuple[str, ...] = (LEADERSHIP_VIEW, LEADERSHIP_ASSIGN)


def user_can_view(user) -> bool:
    return user_has_permission(user, LEADERSHIP_VIEW)


def user_can_manage(user) -> bool:
    return user_has_permission(user, LEADERSHIP_MANAGE)


def user_can_assign(user) -> bool:
    return user_has_permission(user, LEADERSHIP_ASSIGN)
