"""Fail-closed, permission-aware selectors for stakeholder data."""

from __future__ import annotations

from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.rbac.authorization import user_has_permission

from .constants import ConfidentialityLevel
from .models import Stakeholder, StakeholderContact, StakeholderDocument
from .permissions import (
    PARTNERS_MANAGE,
    PARTNERS_MANAGE_DOCUMENTS,
    PARTNERS_VIEW,
    PARTNERS_VIEW_DIRECTORY,
    PARTNERS_VIEW_PRIVATE_CONTACTS,
)


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _active_grant_filter(user) -> Q:
    now = timezone.now()
    return Q(
        access_grants__user=user,
        access_grants__is_active=True,
        access_grants__starts_at__lte=now,
    ) & (
        Q(access_grants__expires_at__isnull=True) | Q(access_grants__expires_at__gt=now)
    )


def visible_stakeholders(user, *, include_archived: bool = False) -> QuerySet:
    """Return only records the actor may know exist."""
    queryset = Stakeholder.all_objects.filter(is_deleted=False).select_related(
        "relationship_type",
        "classification",
        "organization_unit",
        "primary_responsible_officer",
        "responsible_leadership__user",
    )
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, PARTNERS_MANAGE):
        return queryset.distinct()

    access_filter = Q()
    has_access_rule = False
    if user_has_permission(user, PARTNERS_VIEW):
        access_filter |= (
            Q(created_by=user)
            | Q(primary_responsible_officer=user)
            | Q(responsible_leadership__user=user)
            | _active_grant_filter(user)
        )
        has_access_rule = True
    if user_has_permission(user, PARTNERS_VIEW_DIRECTORY):
        access_filter |= Q(
            confidentiality__in=[
                ConfidentialityLevel.DIRECTORY,
                ConfidentialityLevel.INTERNAL,
            ]
        )
        has_access_rule = True
    if not has_access_rule:
        return queryset.none()
    return queryset.filter(access_filter).distinct()


def visible_stakeholder_contacts(user, stakeholder=None) -> QuerySet:
    """Private contact details require a separate permission."""
    queryset = StakeholderContact.objects.select_related("stakeholder")
    if stakeholder is not None:
        queryset = queryset.filter(stakeholder=stakeholder)
    if not _authenticated(user):
        return queryset.none()
    if not (
        user.is_superuser
        or user_has_permission(user, PARTNERS_MANAGE)
        or user_has_permission(user, PARTNERS_VIEW_PRIVATE_CONTACTS)
    ):
        return queryset.none()
    return queryset.filter(
        stakeholder__in=visible_stakeholders(user, include_archived=True)
    )


def visible_stakeholder_documents(user, stakeholder=None) -> QuerySet:
    """Documents fail closed independently of profile visibility."""
    queryset = StakeholderDocument.objects.select_related("stakeholder")
    if stakeholder is not None:
        queryset = queryset.filter(stakeholder=stakeholder)
    if not _authenticated(user):
        return queryset.none()
    if not (
        user.is_superuser
        or user_has_permission(user, PARTNERS_MANAGE)
        or user_has_permission(user, PARTNERS_MANAGE_DOCUMENTS)
    ):
        return queryset.none()
    return queryset.filter(
        stakeholder__in=visible_stakeholders(user, include_archived=True)
    )


def user_can_access_stakeholder(user, stakeholder, *, include_archived=False) -> bool:
    """Object authorization helper used by transactional services."""
    if stakeholder is None:
        return False
    return (
        visible_stakeholders(user, include_archived=include_archived)
        .filter(pk=stakeholder.pk)
        .exists()
    )
