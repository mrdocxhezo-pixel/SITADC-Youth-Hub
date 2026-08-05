"""Permission constants and helpers for the ``programmes``/``projects`` namespaces."""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

from .constants import PROGRAM_ACTION_PERMISSIONS, PROJECT_ACTION_PERMISSIONS

PROGRAMMES_VIEW = PROGRAM_ACTION_PERMISSIONS["view"]
PROGRAMMES_CREATE = PROGRAM_ACTION_PERMISSIONS["create"]
PROGRAMMES_UPDATE = PROGRAM_ACTION_PERMISSIONS["update"]
PROGRAMMES_DELETE = PROGRAM_ACTION_PERMISSIONS["delete"]
PROGRAMMES_SUBMIT = PROGRAM_ACTION_PERMISSIONS["submit"]
PROGRAMMES_ARCHIVE = PROGRAM_ACTION_PERMISSIONS["archive"]
PROGRAMMES_RESTORE = PROGRAM_ACTION_PERMISSIONS["restore"]
PROGRAMMES_EXPORT = PROGRAM_ACTION_PERMISSIONS["export"]
PROGRAMMES_ASSIGN = PROGRAM_ACTION_PERMISSIONS["assign"]
PROGRAMMES_MANAGE = PROGRAM_ACTION_PERMISSIONS["manage"]

PROJECTS_VIEW = PROJECT_ACTION_PERMISSIONS["view"]
PROJECTS_CREATE = PROJECT_ACTION_PERMISSIONS["create"]
PROJECTS_UPDATE = PROJECT_ACTION_PERMISSIONS["update"]
PROJECTS_DELETE = PROJECT_ACTION_PERMISSIONS["delete"]
PROJECTS_SUBMIT = PROJECT_ACTION_PERMISSIONS["submit"]
PROJECTS_ARCHIVE = PROJECT_ACTION_PERMISSIONS["archive"]
PROJECTS_RESTORE = PROJECT_ACTION_PERMISSIONS["restore"]
PROJECTS_EXPORT = PROJECT_ACTION_PERMISSIONS["export"]
PROJECTS_ASSIGN = PROJECT_ACTION_PERMISSIONS["assign"]
PROJECTS_MANAGE = PROJECT_ACTION_PERMISSIONS["manage"]


def user_can_view_programs(user) -> bool:
    return user_has_permission(user, PROGRAMMES_VIEW) or user_has_permission(
        user, PROGRAMMES_MANAGE
    )


def user_can_manage_programs(user) -> bool:
    return user_has_permission(user, PROGRAMMES_MANAGE)


def user_can_view_projects(user) -> bool:
    return user_has_permission(user, PROJECTS_VIEW) or user_has_permission(
        user, PROJECTS_MANAGE
    )


def user_can_manage_projects(user) -> bool:
    return user_has_permission(user, PROJECTS_MANAGE)
