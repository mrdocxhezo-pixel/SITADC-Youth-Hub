"""Permission constants and helpers for the ``meal`` namespace."""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

from .constants import MEAL_ACTION_PERMISSIONS

MEAL_VIEW = MEAL_ACTION_PERMISSIONS["view"]
MEAL_CREATE = MEAL_ACTION_PERMISSIONS["create"]
MEAL_UPDATE = MEAL_ACTION_PERMISSIONS["update"]
MEAL_DELETE = MEAL_ACTION_PERMISSIONS["delete"]
MEAL_SUBMIT = MEAL_ACTION_PERMISSIONS["submit"]
MEAL_APPROVE = MEAL_ACTION_PERMISSIONS["approve"]
MEAL_ARCHIVE = MEAL_ACTION_PERMISSIONS["archive"]
MEAL_RESTORE = MEAL_ACTION_PERMISSIONS["restore"]
MEAL_EXPORT = MEAL_ACTION_PERMISSIONS["export"]
MEAL_VIEW_CONFIDENTIAL = MEAL_ACTION_PERMISSIONS["view_confidential"]
MEAL_MANAGE_FRAMEWORKS = MEAL_ACTION_PERMISSIONS["manage_frameworks"]
MEAL_MANAGE_INDICATORS = MEAL_ACTION_PERMISSIONS["manage_indicators"]
MEAL_MANAGE_DATA_COLLECTION = MEAL_ACTION_PERMISSIONS["manage_data_collection"]
MEAL_MANAGE_MONITORING = MEAL_ACTION_PERMISSIONS["manage_monitoring"]
MEAL_MANAGE_EVALUATIONS = MEAL_ACTION_PERMISSIONS["manage_evaluations"]
MEAL_MANAGE_DQA = MEAL_ACTION_PERMISSIONS["manage_dqa"]
MEAL_MANAGE_ACCOUNTABILITY = MEAL_ACTION_PERMISSIONS["manage_accountability"]
MEAL_MANAGE_LEARNING = MEAL_ACTION_PERMISSIONS["manage_learning"]
MEAL_MANAGE_SCORECARDS = MEAL_ACTION_PERMISSIONS["manage_scorecards"]
MEAL_MANAGE_REPORTS = MEAL_ACTION_PERMISSIONS["manage_reports"]
MEAL_CONFIGURE = MEAL_ACTION_PERMISSIONS["configure"]
MEAL_MANAGE = MEAL_ACTION_PERMISSIONS["manage"]


def user_can_view_meal(user) -> bool:
    return user_has_permission(user, MEAL_VIEW) or user_has_permission(
        user, MEAL_MANAGE
    )


def user_can_manage_meal(user) -> bool:
    return user_has_permission(user, MEAL_MANAGE)


def user_can_view_confidential(user) -> bool:
    return user_has_permission(user, MEAL_VIEW_CONFIDENTIAL) or user_has_permission(
        user, MEAL_MANAGE
    )
