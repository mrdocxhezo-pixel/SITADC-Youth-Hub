"""Permission constants and helpers for the ``notifications`` namespace.

Authorization is enforced on the server.  These helpers centralize the checks
used across views, services, selectors and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

# Module permission categories.
_NOTIFICATIONS = "notifications"
_ANNOUNCEMENTS = "announcements"
_PREFERENCES = "preferences"

# Notification permissions.
NOTIFICATION_VIEW = f"{_NOTIFICATIONS}.view"
NOTIFICATION_CREATE = f"{_NOTIFICATIONS}.create"
NOTIFICATION_UPDATE = f"{_NOTIFICATIONS}.update"
NOTIFICATION_DELETE = f"{_NOTIFICATIONS}.delete"
NOTIFICATION_SEND = f"{_NOTIFICATIONS}.send"
NOTIFICATION_MANAGE_TEMPLATES = f"{_NOTIFICATIONS}.manage_templates"
NOTIFICATION_MANAGE_RULES = f"{_NOTIFICATIONS}.manage_rules"
NOTIFICATION_CONFIGURE = f"{_NOTIFICATIONS}.configure"
NOTIFICATION_MANAGE = f"{_NOTIFICATIONS}.manage"

# Announcement permissions.
ANNOUNCEMENT_VIEW = f"{_ANNOUNCEMENTS}.view"
ANNOUNCEMENT_CREATE = f"{_ANNOUNCEMENTS}.create"
ANNOUNCEMENT_UPDATE = f"{_ANNOUNCEMENTS}.update"
ANNOUNCEMENT_DELETE = f"{_ANNOUNCEMENTS}.delete"
ANNOUNCEMENT_PUBLISH = f"{_ANNOUNCEMENTS}.publish"
ANNOUNCEMENT_MANAGE = f"{_ANNOUNCEMENTS}.manage"

# Preference permissions.
PREFERENCE_VIEW = f"{_PREFERENCES}.view"
PREFERENCE_UPDATE = f"{_PREFERENCES}.update"
PREFERENCE_MANAGE = f"{_PREFERENCES}.manage"

_VIEW_CODES = (
    NOTIFICATION_VIEW,
    ANNOUNCEMENT_VIEW,
    NOTIFICATION_MANAGE,
    ANNOUNCEMENT_MANAGE,
)


def _has(user, *codes: str) -> bool:
    return any(user_has_permission(user, code) for code in codes)


def user_can_view_notifications(user) -> bool:
    """Whether the user may browse notifications in this module."""
    return _has(user, *_VIEW_CODES)


def user_can_manage_notifications(user) -> bool:
    """Whether the user may administer notifications/announcements."""
    return _has(user, NOTIFICATION_MANAGE, ANNOUNCEMENT_MANAGE)


def user_can_manage_templates(user) -> bool:
    """Whether the user may manage notification templates."""
    return _has(user, NOTIFICATION_MANAGE_TEMPLATES, NOTIFICATION_MANAGE)


def user_can_manage_rules(user) -> bool:
    """Whether the user may manage notification rules."""
    return _has(user, NOTIFICATION_MANAGE_RULES, NOTIFICATION_MANAGE)


def user_can_configure(user) -> bool:
    """Whether the user may configure notification infrastructure."""
    return _has(user, NOTIFICATION_CONFIGURE, NOTIFICATION_MANAGE)


def user_can_send(user) -> bool:
    """Whether the user may trigger or dispatch notifications."""
    return _has(user, NOTIFICATION_SEND, NOTIFICATION_MANAGE)


def user_can_publish_announcements(user) -> bool:
    """Whether the user may publish announcements."""
    return _has(user, ANNOUNCEMENT_PUBLISH, ANNOUNCEMENT_MANAGE)


def user_can_manage_announcements(user) -> bool:
    """Whether the user may create and edit announcements."""
    return _has(user, ANNOUNCEMENT_CREATE, ANNOUNCEMENT_UPDATE, ANNOUNCEMENT_MANAGE)


def user_can_update_preferences(user) -> bool:
    """Whether the user may update their own notification preferences."""
    return _has(user, PREFERENCE_UPDATE, PREFERENCE_MANAGE)


def is_recipient(user, notification) -> bool:
    """Whether the user is the intended recipient of the notification."""
    return bool(user and user.is_authenticated and notification.recipient_id == user.pk)


def is_announcement_author(user, announcement) -> bool:
    """Whether the user created the announcement."""
    return bool(
        user and user.is_authenticated and announcement.created_by_id == user.pk
    )
