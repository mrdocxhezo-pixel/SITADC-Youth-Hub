"""Fail-closed, permission-aware selectors for report builder data.

Views read exclusively through these helpers so that anonymous users and
actors without report permission can never discover the existence of report
templates, categories or audit history.
"""

from __future__ import annotations

from django.db.models import QuerySet

from apps.rbac.authorization import user_has_permission

from .models import ReportCategory, ReportTemplate, ReportTemplateAuditRecord
from .permissions import REPORT_TEMPLATE_MANAGE, REPORT_TEMPLATE_VIEW


def _authenticated(user) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def template_queryset(
    user, *, include_archived: bool = False
) -> QuerySet[ReportTemplate]:
    """Return report templates the actor may know exist."""
    manager = ReportTemplate.all_objects if include_archived else ReportTemplate.objects
    queryset = manager.all()
    if not include_archived:
        queryset = queryset.filter(is_archived=False)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, REPORT_TEMPLATE_MANAGE):
        return queryset
    if user_has_permission(user, REPORT_TEMPLATE_VIEW):
        return queryset
    return queryset.none()


def category_queryset(
    user, *, include_inactive: bool = False
) -> QuerySet[ReportCategory]:
    """Return report categories the actor may read."""
    if not _authenticated(user):
        return ReportCategory.objects.none()
    if user.is_superuser or user_has_permission(user, REPORT_TEMPLATE_MANAGE):
        manager = (
            ReportCategory.all_objects if include_inactive else ReportCategory.objects
        )
        return manager.all()
    if user_has_permission(user, REPORT_TEMPLATE_VIEW):
        return ReportCategory.objects.all()
    return ReportCategory.objects.none()


def visible_audit_records(user, *, entity_type: str | None = None, limit: int = 20):
    """Return the recent report builder audit trail for the actor."""
    queryset = ReportTemplateAuditRecord.objects.all()
    if entity_type:
        queryset = queryset.filter(entity_type=entity_type)
    if not _authenticated(user):
        return queryset.none()
    if user.is_superuser or user_has_permission(user, REPORT_TEMPLATE_MANAGE):
        return queryset.order_by("-created_at")[:limit]
    return queryset.none()


def user_can_access_template(user, instance) -> bool:
    """Check if user can read a specific report template."""
    if instance is None:
        return False
    return (
        template_queryset(user, include_archived=True).filter(pk=instance.pk).exists()
    )


def get_report_template_by_slug(slug: str, user=None):
    """Return a ``ReportTemplate`` by slug.

    If ``user`` is provided, permission checks are applied using
    ``template_queryset``; otherwise the object is returned without checks.
    """
    from .models import ReportTemplate

    qs = ReportTemplate.objects.all()
    if user is not None:
        qs = template_queryset(user, include_archived=True)
    return qs.get(slug=slug)
