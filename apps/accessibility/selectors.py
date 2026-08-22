"""Fail-closed selectors for the Accessibility Review module."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.accessibility.permissions import (
    ACCESSIBILITY_MANAGE,
    ACCESSIBILITY_VIEW,
)
from apps.rbac.authorization import user_has_permission

from .models import (
    AccessibilityAnalytics,
    AccessibilityAudit,
    AccessibilityComplianceRecord,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityNotification,
    AccessibilityPolicy,
    AccessibilityRecommendation,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
    WCAGCriterion,
)


def _has_perm(user, *codes: str) -> bool:
    if user is None or not user.is_authenticated:
        return False
    if user_has_permission(user, ACCESSIBILITY_MANAGE):
        return True
    return any(user_has_permission(user, code) for code in codes)


def standard_queryset(user, *, include_inactive: bool = False) -> QuerySet:
    """Return accessible accessibility standards."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityStandardRecord.objects.none()
    qs = AccessibilityStandardRecord.objects.all()
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


def policy_queryset(user, *, include_inactive: bool = False) -> QuerySet:
    """Return accessible accessibility policies."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityPolicy.objects.none()
    qs = AccessibilityPolicy.objects.select_related("standard")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


def criterion_queryset(user, *, include_inactive: bool = False) -> QuerySet:
    """Return accessible WCAG criteria."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return WCAGCriterion.objects.none()
    qs = WCAGCriterion.objects.select_related("standard")
    if not include_inactive:
        qs = qs.filter(is_active=True)
    return qs


def audit_queryset(user) -> QuerySet:
    """Return accessible audits."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityAudit.objects.none()
    return AccessibilityAudit.objects.select_related("standard", "auditor")


def finding_queryset(user) -> QuerySet:
    """Return accessible findings."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityFinding.objects.none()
    return AccessibilityFinding.objects.select_related("audit", "criterion", "assigned_to")


def issue_queryset(user) -> QuerySet:
    """Return accessible issues."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityIssue.objects.none()
    return AccessibilityIssue.objects.select_related("reporter", "assigned_to", "criterion")


def recommendation_queryset(user) -> QuerySet:
    """Return accessible recommendations."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityRecommendation.objects.none()
    return AccessibilityRecommendation.objects.prefetch_related("related_criteria")


def compliance_queryset(user) -> QuerySet:
    """Return accessible compliance records."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityComplianceRecord.objects.none()
    return AccessibilityComplianceRecord.objects.select_related("standard", "last_audit")


def notification_queryset(user) -> QuerySet:
    """Return notifications for the current user."""
    if user is None or not user.is_authenticated:
        return AccessibilityNotification.objects.none()
    return AccessibilityNotification.objects.filter(recipient=user).select_related(
        "related_audit", "related_finding", "related_issue"
    )


def unread_notification_count(user) -> int:
    """Count unread notifications for the current user."""
    if user is None or not user.is_authenticated:
        return 0
    return AccessibilityNotification.objects.filter(recipient=user, is_read=False).count()


def analytics_queryset(user, module: str = "") -> QuerySet:
    """Return analytics snapshots."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityAnalytics.objects.none()
    qs = AccessibilityAnalytics.objects.all()
    if module:
        qs = qs.filter(module=module)
    return qs


def timeline_queryset(user, module: str = "", event_type: str = "") -> QuerySet:
    """Return accessibility timeline events."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return AccessibilityTimeline.objects.none()
    qs = AccessibilityTimeline.objects.select_related("performed_by")
    if module:
        qs = qs.filter(module=module)
    if event_type:
        qs = qs.filter(event_type=event_type)
    return qs


def get_user_preferences(user) -> AccessibilityStandardRecord | None:
    """Get or create user accessibility preferences."""
    from .models import AccessibilityPreference
    if user is None or not user.is_authenticated:
        return None
    return AccessibilityPreference.objects.get_or_create(user=user)[0]


def get_configuration() -> AccessibilityStandardRecord:
    """Get the singleton accessibility configuration."""
    from .models import AccessibilityConfiguration
    return AccessibilityConfiguration.load()


def get_latest_analytics(module: str = "") -> AccessibilityAnalytics | None:
    """Get the most recent analytics snapshot."""
    qs = AccessibilityAnalytics.objects.all()
    if module:
        qs = qs.filter(module=module)
    return qs.order_by("-snapshot_date").first()


def get_open_findings_count(user, module: str = "") -> int:
    """Count open findings for a module."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return 0
    qs = AccessibilityFinding.objects.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"])
    if module:
        qs = qs.filter(audit__module=module)
    return qs.count()


def get_open_issues_count(user, module: str = "") -> int:
    """Count open issues for a module."""
    if not _has_perm(user, ACCESSIBILITY_VIEW):
        return 0
    qs = AccessibilityIssue.objects.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"])
    if module:
        qs = qs.filter(module=module)
    return qs.count()
