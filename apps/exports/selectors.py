"""Fail-closed selectors for the Export Engine.

Every query is permission-scaled: users only see their own exports unless
they hold the operational-history permission, and templates are only listed
when the actor may use the engine.
"""

from __future__ import annotations

from typing import Any

from django.db.models import Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.rbac.authorization import user_has_permission

from .constants import ExportStatus
from .models import ExportConfiguration, ExportRequest, ExportTemplate
from .permissions import EXPORTS_MANAGE, EXPORTS_VIEW_ALL_HISTORY, user_can_view_exports


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def _not_expired() -> Q:
    """Q expression: expires_at is null OR expires_at is in the future."""
    now = timezone.now()
    return Q(expires_at__isnull=True) | Q(expires_at__gt=now)


def active_export_configuration() -> ExportConfiguration:
    """Return the singleton export configuration."""
    return ExportConfiguration.load()


def export_request_queryset(
    user, *, include_all: bool = False
) -> QuerySet[ExportRequest]:
    """Export requests visible to the actor.

    Default: the actor's own requests.  ``include_all`` (superusers and
    holders of the operational-history permission) returns every request.
    """
    queryset = ExportRequest.objects.all()
    if not _authenticated(user):
        return queryset.none()
    if (
        user.is_superuser
        or include_all
        or user_has_permission(user, EXPORTS_VIEW_ALL_HISTORY)
    ):
        return queryset
    return queryset.filter(requested_by=user)


def export_requests_for_user(
    user, *, status: str | None = None
) -> QuerySet[ExportRequest]:
    """The actor's own export requests (optionally filtered by status)."""
    queryset = export_request_queryset(user)
    if status:
        queryset = queryset.filter(status=status)
    return queryset


def get_export_request_for_user(request_id: Any, user) -> ExportRequest:
    """Fetch an export request honoring ownership; raises 404 otherwise."""
    queryset = export_request_queryset(user)
    return get_object_or_404(queryset, pk=request_id)


def visible_export_templates(
    user, *, source_type: str | None = None
) -> QuerySet[ExportTemplate]:
    """Active export templates the actor may use."""
    if not _authenticated(user) or not user_can_view_exports(user):
        return ExportTemplate.objects.none()
    queryset = ExportTemplate.objects.filter(is_active=True)
    if source_type:
        queryset = queryset.filter(source_type=source_type)
    return queryset


def export_templates(user) -> QuerySet[ExportTemplate]:
    """All export templates (admin management view)."""
    if not _authenticated(user):
        return ExportTemplate.objects.none()
    if user.is_superuser or user_has_permission(user, EXPORTS_MANAGE):
        return ExportTemplate.objects.all()
    return ExportTemplate.objects.none()


def downloadable_exports(user) -> QuerySet[ExportRequest]:
    """Completed, not-yet-expired exports the actor may download."""
    return (
        export_request_queryset(user)
        .filter(
            status=ExportStatus.COMPLETED,
        )
        .filter(_not_expired())
    )
