"""Communication and Media permissions.

The ``communications.*`` catalogue supplements Django model-level permissions.
Every communications view must satisfy the relevant communications permission
before data is exposed, and confidential records additionally require the
``communications.view_confidential`` permission.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model

from apps.rbac.authorization import user_has_permission

User = get_user_model()

COMMUNICATIONS_VIEW = "communications.view"
COMMUNICATIONS_VIEW_CONFIDENTIAL = "communications.view_confidential"
COMMUNICATIONS_CREATE = "communications.create"
COMMUNICATIONS_UPDATE = "communications.update"
COMMUNICATIONS_DELETE = "communications.delete"
COMMUNICATIONS_APPROVE = "communications.approve"
COMMUNICATIONS_PUBLISH = "communications.publish"
COMMUNICATIONS_ARCHIVE = "communications.archive"
COMMUNICATIONS_RESTORE = "communications.restore"
COMMUNICATIONS_EXPORT = "communications.export"
COMMUNICATIONS_MANAGE = "communications.manage"


def _has(user: Any, *codes: str) -> bool:
    """Fail-closed check for any of the given permission codes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in codes)


def user_can_access_communications(user) -> bool:
    """Whether the actor may open the communications workspace."""
    return _has(user, COMMUNICATIONS_VIEW, COMMUNICATIONS_MANAGE)


def user_can_manage_communications(user) -> bool:
    """Whether the actor holds the master communications-management permission."""
    return _has(user, COMMUNICATIONS_MANAGE)


def user_can_view_confidential_communications(user) -> bool:
    """Whether the actor may view confidential communication records."""
    return _has(user, COMMUNICATIONS_VIEW_CONFIDENTIAL, COMMUNICATIONS_MANAGE)


def user_can_create_communications(user) -> bool:
    """Whether the actor may create communication records."""
    return _has(user, COMMUNICATIONS_CREATE, COMMUNICATIONS_MANAGE)


def user_can_update_communications(user) -> bool:
    """Whether the actor may update communication records."""
    return _has(user, COMMUNICATIONS_UPDATE, COMMUNICATIONS_MANAGE)


def user_can_delete_communications(user) -> bool:
    """Whether the actor may delete communication records."""
    return _has(user, COMMUNICATIONS_DELETE, COMMUNICATIONS_MANAGE)


def user_can_approve_communications(user) -> bool:
    """Whether the actor may approve communication records."""
    return _has(user, COMMUNICATIONS_APPROVE, COMMUNICATIONS_MANAGE)


def user_can_publish_communications(user) -> bool:
    """Whether the actor may publish communication records."""
    return _has(user, COMMUNICATIONS_PUBLISH, COMMUNICATIONS_MANAGE)


def user_can_archive_communications(user) -> bool:
    """Whether the actor may archive communication records."""
    return _has(user, COMMUNICATIONS_ARCHIVE, COMMUNICATIONS_MANAGE)


def user_can_restore_communications(user) -> bool:
    """Whether the actor may restore archived communication records."""
    return _has(user, COMMUNICATIONS_RESTORE, COMMUNICATIONS_MANAGE)


def user_can_export_communications(user) -> bool:
    """Whether the actor may export communication records."""
    return _has(user, COMMUNICATIONS_EXPORT, COMMUNICATIONS_MANAGE)


def user_can_view_communications(user) -> bool:
    """Whether the actor may view ordinary communication records."""
    return _has(user, COMMUNICATIONS_VIEW, COMMUNICATIONS_MANAGE)
