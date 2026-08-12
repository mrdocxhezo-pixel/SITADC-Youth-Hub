"""Fail-closed, permission-aware selectors for MEAL data."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.rbac.authorization import user_has_permission

from .models import Complaint, Feedback, MEALReferenceData
from .permissions import MEAL_MANAGE, MEAL_VIEW, MEAL_VIEW_CONFIDENTIAL


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def meal_queryset(user, model, *, include_archived: bool = False) -> QuerySet:
    """Return MEAL rows of ``model`` that the actor may know exist."""
    manager = model.all_objects if include_archived else model.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, MEAL_MANAGE):
        return queryset
    if user_has_permission(user, MEAL_VIEW):
        return queryset
    return queryset.none()


def visible_complaints(user, *, include_archived: bool = False) -> QuerySet:
    """Complaints scoped by confidentiality for the actor."""
    queryset = meal_queryset(user, Complaint, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not (user.is_superuser or user_has_permission(user, MEAL_MANAGE)) and not (
        user_has_permission(user, MEAL_VIEW_CONFIDENTIAL)
    ):
        queryset = queryset.filter(is_confidential=False)
    return queryset


def visible_feedback(user, *, include_archived: bool = False) -> QuerySet:
    """Feedback scoped by confidentiality for the actor."""
    queryset = meal_queryset(user, Feedback, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not (user.is_superuser or user_has_permission(user, MEAL_MANAGE)) and not (
        user_has_permission(user, MEAL_VIEW_CONFIDENTIAL)
    ):
        queryset = queryset.filter(is_confidential=False)
    return queryset


def user_can_access_meal_record(
    user, instance, *, include_archived: bool = False
) -> bool:
    """Whether the actor may read a specific MEAL record."""
    if instance is None:
        return False
    if (
        isinstance(instance, Complaint | Feedback)
        and instance.is_confidential
        and not (
            user_has_permission(user, MEAL_VIEW_CONFIDENTIAL)
            or user_has_permission(user, MEAL_MANAGE)
        )
    ):
        return False
    return (
        meal_queryset(user, type(instance), include_archived=include_archived)
        .filter(pk=instance.pk)
        .exists()
    )


def active_reference_data(kind: str) -> QuerySet:
    """Active configurable MEAL reference rows for a given kind."""
    return MEALReferenceData.objects.filter(kind=kind, active=True)
