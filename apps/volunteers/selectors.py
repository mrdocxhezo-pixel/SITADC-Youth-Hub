"""Permission-aware, optimized selectors for volunteer records."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.rbac.authorization import user_has_permission

from .models import VolunteerProfile
from .permissions import (
    VOLUNTEERS_MANAGE,
    VOLUNTEERS_VIEW,
    VOLUNTEERS_VIEW_CONFIDENTIAL,
)


def visible_volunteer_profiles(user, *, include_archived: bool = False) -> QuerySet:
    """Return profiles visible to the actor, denying broad access by default."""
    queryset = VolunteerProfile.objects.select_related("user", "team", "supervisor")
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if user is None or not getattr(user, "is_authenticated", False):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, VOLUNTEERS_MANAGE):
        return queryset
    if user_has_permission(user, VOLUNTEERS_VIEW):
        return queryset.filter(user=user)
    return queryset.none()


def can_view_confidential_volunteer_data(user) -> bool:
    if user is None or not getattr(user, "is_authenticated", False):
        return False
    return bool(
        user.is_superuser or user_has_permission(user, VOLUNTEERS_VIEW_CONFIDENTIAL)
    )
