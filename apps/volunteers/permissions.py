"""
Permission constants and helper functions for the volunteer management module.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

VOLUNTEERS_VIEW = "volunteers.view"
VOLUNTEERS_CREATE = "volunteers.create"
VOLUNTEERS_UPDATE = "volunteers.update"
VOLUNTEERS_DELETE = "volunteers.delete"
VOLUNTEERS_ARCHIVE = "volunteers.archive"
VOLUNTEERS_RESTORE = "volunteers.restore"
VOLUNTEERS_EXPORT = "volunteers.export"
VOLUNTEERS_ASSIGN = "volunteers.assign"
VOLUNTEERS_MANAGE_ATTENDANCE = "volunteers.manage_attendance"
VOLUNTEERS_MANAGE_TRAINING = "volunteers.manage_training"
VOLUNTEERS_MANAGE_PERFORMANCE = "volunteers.manage_performance"
VOLUNTEERS_MANAGE_LEAVE = "volunteers.manage_leave"
VOLUNTEERS_MANAGE_EXIT = "volunteers.manage_exit"
VOLUNTEERS_MANAGE_ACTIVITY = "volunteers.manage_activity"
VOLUNTEERS_MANAGE_DISCIPLINARY = "volunteers.manage_disciplinary"
VOLUNTEERS_MANAGE_COMMUNICATIONS = "volunteers.manage_communications"
VOLUNTEERS_MANAGE_DOCUMENTS = "volunteers.manage_documents"
VOLUNTEERS_CONFIGURE = "volunteers.configure"
VOLUNTEERS_VIEW_CONFIDENTIAL = "volunteers.view_confidential"
VOLUNTEERS_MANAGE = "volunteers.manage"

VIEW_PERMISSIONS: tuple[str, ...] = (VOLUNTEERS_VIEW,)
MANAGE_PERMISSIONS: tuple[str, ...] = (
    VOLUNTEERS_VIEW,
    VOLUNTEERS_CREATE,
    VOLUNTEERS_UPDATE,
    VOLUNTEERS_DELETE,
    VOLUNTEERS_ARCHIVE,
    VOLUNTEERS_RESTORE,
    VOLUNTEERS_EXPORT,
    VOLUNTEERS_ASSIGN,
    VOLUNTEERS_MANAGE_ATTENDANCE,
    VOLUNTEERS_MANAGE_TRAINING,
    VOLUNTEERS_MANAGE_PERFORMANCE,
    VOLUNTEERS_MANAGE_LEAVE,
    VOLUNTEERS_MANAGE_EXIT,
    VOLUNTEERS_MANAGE_ACTIVITY,
    VOLUNTEERS_MANAGE_DISCIPLINARY,
    VOLUNTEERS_MANAGE_COMMUNICATIONS,
    VOLUNTEERS_MANAGE_DOCUMENTS,
    VOLUNTEERS_CONFIGURE,
    VOLUNTEERS_MANAGE,
)


def user_can_view_volunteers(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_VIEW) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_create_volunteers(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_CREATE) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_update_volunteers(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_UPDATE) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_assign_volunteers(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_ASSIGN) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_manage_attendance(user) -> bool:
    return user_has_permission(
        user, VOLUNTEERS_MANAGE_ATTENDANCE
    ) or user_has_permission(user, VOLUNTEERS_MANAGE)


def user_can_manage_training(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_MANAGE_TRAINING) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_manage_performance(user) -> bool:
    return user_has_permission(
        user, VOLUNTEERS_MANAGE_PERFORMANCE
    ) or user_has_permission(user, VOLUNTEERS_MANAGE)


def user_can_manage_leave(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_MANAGE_LEAVE) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_manage_exit(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_MANAGE_EXIT) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_view_confidential(user) -> bool:
    return bool(
        getattr(user, "is_superuser", False)
        or user_has_permission(user, VOLUNTEERS_VIEW_CONFIDENTIAL)
    )


def user_can_manage_activity(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_MANAGE_ACTIVITY) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )


def user_can_manage_disciplinary(user) -> bool:
    return user_has_permission(
        user, VOLUNTEERS_MANAGE_DISCIPLINARY
    ) or user_has_permission(user, VOLUNTEERS_MANAGE)


def user_can_manage_communications(user) -> bool:
    return user_has_permission(
        user, VOLUNTEERS_MANAGE_COMMUNICATIONS
    ) or user_has_permission(user, VOLUNTEERS_MANAGE)


def user_can_manage_documents(user) -> bool:
    return user_has_permission(
        user, VOLUNTEERS_MANAGE_DOCUMENTS
    ) or user_has_permission(user, VOLUNTEERS_MANAGE)


def user_can_configure_volunteers(user) -> bool:
    return user_has_permission(user, VOLUNTEERS_CONFIGURE) or user_has_permission(
        user, VOLUNTEERS_MANAGE
    )
