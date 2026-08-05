"""
Permission helpers and constants for the reference numbering module.

Authorization is always enforced on the server; these helpers centralize the
permission checks used across views, services and templates.
"""

from __future__ import annotations

from apps.rbac.authorization import user_has_permission

REFERENCE_NUMBERS_VIEW = "reference_numbers.view"
REFERENCE_NUMBERS_CREATE = "reference_numbers.create"
REFERENCE_NUMBERS_UPDATE = "reference_numbers.update"
REFERENCE_NUMBERS_ACTIVATE = "reference_numbers.activate"
REFERENCE_NUMBERS_ARCHIVE = "reference_numbers.archive"
REFERENCE_NUMBERS_PREVIEW = "reference_numbers.preview"
REFERENCE_NUMBERS_RESET = "reference_numbers.reset"
REFERENCE_NUMBERS_VIEW_REGISTRY = "reference_numbers.view_registry"
REFERENCE_NUMBERS_CORRECT = "reference_numbers.correct"

VIEW_PERMISSIONS: tuple[str, ...] = (REFERENCE_NUMBERS_VIEW,)
MANAGE_PERMISSIONS: tuple[str, ...] = (
    REFERENCE_NUMBERS_VIEW,
    REFERENCE_NUMBERS_CREATE,
    REFERENCE_NUMBERS_UPDATE,
    REFERENCE_NUMBERS_ACTIVATE,
    REFERENCE_NUMBERS_ARCHIVE,
    REFERENCE_NUMBERS_PREVIEW,
    REFERENCE_NUMBERS_RESET,
    REFERENCE_NUMBERS_VIEW_REGISTRY,
    REFERENCE_NUMBERS_CORRECT,
)


def user_can_view(user) -> bool:
    return user_has_permission(user, REFERENCE_NUMBERS_VIEW)


def user_can_manage(user) -> bool:
    return user_has_permission(user, REFERENCE_NUMBERS_UPDATE)


def user_can_view_registry(user) -> bool:
    return user_has_permission(user, REFERENCE_NUMBERS_VIEW_REGISTRY)
