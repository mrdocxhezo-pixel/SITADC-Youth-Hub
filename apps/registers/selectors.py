"""Fail-closed, permission-aware selectors for Organizational Registers data."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.rbac.authorization import user_has_permission

from .constants import ConfidentialityLevel
from .models import Register, RegisterCategory, RegisterEntry, RegisterTemplate
from .permissions import REGISTER_MANAGE, REGISTER_VIEW, REGISTER_VIEW_CONFIDENTIAL

_SENSITIVE_LEVELS = (
    ConfidentialityLevel.RESTRICTED,
    ConfidentialityLevel.CONFIDENTIAL,
    ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
)

_NON_SENSITIVE_LEVELS = (
    ConfidentialityLevel.PUBLIC,
    ConfidentialityLevel.INTERNAL,
)


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _can_view(user) -> bool:
    return bool(
        user.is_superuser
        or user_has_permission(user, REGISTER_VIEW)
        or user_has_permission(user, REGISTER_MANAGE)
    )


def _can_view_sensitive(user) -> bool:
    return bool(
        user.is_superuser
        or user_has_permission(user, REGISTER_VIEW_CONFIDENTIAL)
        or user_has_permission(user, REGISTER_MANAGE)
    )


def register_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Registers the actor may know exist."""
    manager = Register.all_objects if include_archived else Register.objects
    queryset = manager.all()
    if not _authenticated(user) or not _can_view(user):
        return queryset.none()
    return queryset


def visible_registers(user, *, include_archived: bool = False) -> QuerySet:
    """Registers scoped by confidentiality for the actor."""
    queryset = register_queryset(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not _can_view_sensitive(user):
        queryset = queryset.filter(confidentiality__in=_NON_SENSITIVE_LEVELS)
    return queryset


def entry_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Register entries the actor may know exist."""
    manager = RegisterEntry.all_objects if include_archived else RegisterEntry.objects
    queryset = manager.all()
    if not _authenticated(user) or not _can_view(user):
        return queryset.none()
    return queryset


def visible_entries(user, *, include_archived: bool = False) -> QuerySet:
    """Register entries scoped by entry confidentiality for the actor."""
    queryset = entry_queryset(user, include_archived=include_archived)
    if not _authenticated(user):
        return queryset
    if not _can_view_sensitive(user):
        queryset = queryset.filter(confidentiality__in=_NON_SENSITIVE_LEVELS)
    return queryset


def category_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Register categories the actor may browse."""
    manager = (
        RegisterCategory.all_objects if include_archived else RegisterCategory.objects
    )
    queryset = manager.all()
    if not _authenticated(user) or not _can_view(user):
        return queryset.none()
    return queryset


def template_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Register templates the actor may browse."""
    manager = (
        RegisterTemplate.all_objects if include_archived else RegisterTemplate.objects
    )
    queryset = manager.all()
    if not _authenticated(user) or not _can_view(user):
        return queryset.none()
    return queryset


def user_can_access_register(user, instance, *, include_archived: bool = False) -> bool:
    """Whether the actor may read a specific register."""
    if instance is None:
        return False
    if not _authenticated(user) or not _can_view(user):
        return False
    if (
        instance.is_confidential
        and not _can_view_sensitive(user)
        and not user_has_permission(user, REGISTER_MANAGE)
    ):
        return False
    return (
        register_queryset(user, include_archived=include_archived)
        .filter(pk=instance.pk)
        .exists()
    )


def user_can_access_entry(user, instance, *, include_archived: bool = False) -> bool:
    """Whether the actor may read a specific register entry."""
    if instance is None:
        return False
    if not _authenticated(user) or not _can_view(user):
        return False
    if (
        instance.is_confidential
        and not _can_view_sensitive(user)
        and not user_has_permission(user, REGISTER_MANAGE)
    ):
        return False
    if (
        instance.register.is_confidential
        and not _can_view_sensitive(user)
        and not user_has_permission(user, REGISTER_MANAGE)
    ):
        return False
    return (
        entry_queryset(user, include_archived=include_archived)
        .filter(pk=instance.pk)
        .exists()
    )
