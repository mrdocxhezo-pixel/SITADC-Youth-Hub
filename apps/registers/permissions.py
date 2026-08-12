"""Permission constants and helpers for the ``registers`` namespace.

Authorization is always enforced on the server.  These helpers centralize the
permission checks used across views, services, selectors and templates so the
same rules apply everywhere.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

from .constants import REGISTER_ACTION_PERMISSIONS

REGISTER_VIEW = REGISTER_ACTION_PERMISSIONS["view"]
REGISTER_CREATE = REGISTER_ACTION_PERMISSIONS["create"]
REGISTER_UPDATE = REGISTER_ACTION_PERMISSIONS["update"]
REGISTER_DELETE = REGISTER_ACTION_PERMISSIONS["delete"]
REGISTER_EXPORT = REGISTER_ACTION_PERMISSIONS["export"]
REGISTER_SUBMIT = REGISTER_ACTION_PERMISSIONS["submit"]
REGISTER_REVIEW = REGISTER_ACTION_PERMISSIONS["review"]
REGISTER_APPROVE = REGISTER_ACTION_PERMISSIONS["approve"]
REGISTER_ARCHIVE = REGISTER_ACTION_PERMISSIONS["archive"]
REGISTER_RESTORE = REGISTER_ACTION_PERMISSIONS["restore"]
REGISTER_VIEW_CONFIDENTIAL = REGISTER_ACTION_PERMISSIONS["view_confidential"]
REGISTER_MANAGE = REGISTER_ACTION_PERMISSIONS["manage"]


def _has(user, *codes: str) -> bool:
    return any(user_has_permission(user, code) for code in codes)


def user_can_view_registers(user) -> bool:
    """Whether the user may browse registers and register entries."""
    return _has(user, REGISTER_VIEW, REGISTER_MANAGE)


def user_can_manage_registers(user) -> bool:
    """Whether the user may administer registers and configuration."""
    return user_has_permission(user, REGISTER_MANAGE)


def user_can_view_confidential(user) -> bool:
    """Whether the user may see restricted and confidential entries."""
    return _has(user, REGISTER_VIEW_CONFIDENTIAL, REGISTER_MANAGE)


def user_can_export(user) -> bool:
    """Whether the user may export register data."""
    return _has(user, REGISTER_EXPORT, REGISTER_MANAGE)


def user_can_act_on_entries(user) -> bool:
    """Whether the user may create, edit or submit register entries."""
    return _has(
        user, REGISTER_CREATE, REGISTER_UPDATE, REGISTER_SUBMIT, REGISTER_MANAGE
    )
