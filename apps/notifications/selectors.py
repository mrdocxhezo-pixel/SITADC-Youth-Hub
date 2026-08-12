"""Read-only retrieval helpers for the Notifications & Announcements module.

Selectors never modify data; they only fetch and shape notification data for
views, services, templates and management commands.
"""

from __future__ import annotations

from django.db.models import Count, QuerySet
from django.utils import timezone

from apps.rbac.authorization import get_active_role_assignments

from .constants import (
    AnnouncementAudience,
    NotificationCategory,
    NotificationStatus,
    ReadStatus,
)
from .models import (
    AnnouncementDismissal,
    Notification,
    NotificationDelivery,
    NotificationDigest,
    NotificationEvent,
    NotificationRule,
    NotificationTemplate,
    NotificationPreference,
    SystemAnnouncement,
)

_BULK_STATUSES = (
    NotificationStatus.PENDING,
    NotificationStatus.QUEUED,
    NotificationStatus.SCHEDULED,
)


def notification_queryset(user, *, include_archived: bool = False) -> QuerySet:
    """Notifications the user may know exist (own inbox)."""
    manager = Notification.all_objects if include_archived else Notification.objects
    return manager.for_user(user)


def active_notifications(user) -> QuerySet:
    """Active, non-expired notifications for the user's inbox."""
    return notification_queryset(user).active().recent_first()


def unread_notifications(user) -> QuerySet:
    """Unread notifications for the user."""
    return notification_queryset(user).filter(
        read_status=ReadStatus.UNREAD, is_archived=False
    ).recent_first()


def action_required_notifications(user) -> QuerySet:
    """Notifications that require the recipient to take action."""
    return notification_queryset(user).action_required().active().recent_first()


def digest_eligible_notifications(user) -> QuerySet:
    """Notifications eligible for the next digest generation."""
    return (
        notification_queryset(user)
        .filter(
            is_digest_eligible=True,
            digest_sent=False,
            status__in=_BULK_STATUSES,
        )
        .recent_first()
    )


def expired_notifications(user=None) -> QuerySet:
    """Notifications whose expiry has passed but were not marked expired."""
    queryset = Notification.objects.filter(expiry_at__lt=timezone.now()).exclude(
        status__in=[NotificationStatus.EXPIRED, NotificationStatus.CANCELLED]
    )
    if user is not None:
        queryset = queryset.filter(recipient=user)
    return queryset


def notification_preference_for(user) -> NotificationPreference | None:
    """Return the user's notification preferences or ``None``."""
    return NotificationPreference.objects.for_user(user)


def template_queryset(user=None) -> QuerySet:
    """Active notification templates."""
    qs: QuerySet = NotificationTemplate.objects.active().order_by("code")
    if user is not None and not user.is_superuser:
        scope_ids = [
            assignment.access_scope_id
            for assignment in get_active_role_assignments(user)
            if assignment.access_scope_id
        ]
        if scope_ids:
            qs = qs.filter(
                organization_unit__access_scope_id__in=scope_ids
            ) | qs.filter(organization_unit__isnull=True)
    return qs


def rule_queryset(user=None) -> QuerySet:
    """Active notification rules."""
    qs: QuerySet = NotificationRule.objects.active().order_by("sort_order", "name")
    if user is not None and not user.is_superuser:
        scope_ids = [
            assignment.access_scope_id
            for assignment in get_active_role_assignments(user)
            if assignment.access_scope_id
        ]
        if scope_ids:
            qs = qs.filter(
                organization_unit__access_scope_id__in=scope_ids
            ) | qs.filter(organization_unit__isnull=True)
    return qs


def event_queryset(user=None, event_type: str | None = None) -> QuerySet:
    """Notification events, optionally filtered by type."""
    qs = NotificationEvent.objects.all()
    if event_type:
        qs = qs.filter(event_type=event_type)
    return qs


def delivery_queryset(notification=None) -> QuerySet:
    """Delivery attempts, optionally scoped to a notification."""
    qs: QuerySet = NotificationDelivery.objects.all()
    if notification is not None:
        qs = qs.filter(notification=notification)
    return qs


def announcement_queryset(user=None) -> QuerySet:
    """Published announcements, respecting expiry."""
    qs = SystemAnnouncement.objects.active()
    if user is not None and not user.is_superuser:
        dismissed = AnnouncementDismissal.objects.filter(user=user).values_list(
            "announcement_id", flat=True
        )
        qs = qs.exclude(id__in=dismissed)
    return qs


def announcements_for_user(user) -> QuerySet:
    """Announcements relevant to the user's role audience."""
    base = announcement_queryset(user)
    if not user or not user.is_authenticated:
        return SystemAnnouncement.objects.none()

    role_ids = [
        assignment.role_id
        for assignment in get_active_role_assignments(user)
        if assignment.role_id
    ]
    from django.db.models import Q

    everyone = Q(audience_type=AnnouncementAudience.EVERYONE)
    by_role = Q(
        audience_type=AnnouncementAudience.SPECIFIC_ROLES,
        audience_roles__id__in=role_ids,
    )
    return base.filter(everyone | by_role).distinct()


def digest_queryset(user=None) -> QuerySet:
    """Generated digests, optionally scoped to a user."""
    qs: QuerySet = NotificationDigest.objects.all()
    if user is not None:
        qs = qs.filter(user=user)
    return qs


def unread_count(user) -> int:
    """Unread notification count for a user."""
    if not user or not user.is_authenticated:
        return 0
    return unread_notifications(user).count()


def action_count(user) -> int:
    """Action-required notification count for a user."""
    if not user or not user.is_authenticated:
        return 0
    return action_required_notifications(user).count()


def category_breakdown(user) -> list[dict]:
    """Unread counts grouped by category for the inbox sidebar."""
    rows = (
        notification_queryset(user)
        .filter(read_status=ReadStatus.UNREAD, is_archived=False)
        .values("category")
        .annotate(total=Count("id"))
        .order_by("category")
    )
    return [
        {
            "code": row["category"],
            "label": NotificationCategory(row["category"]).label
            if row["category"] in NotificationCategory.values
            else row["category"],
            "count": row["total"],
        }
        for row in rows
    ]


def digest_summary_counts(user) -> dict:
    """Summary counts used on the notifications dashboard."""
    inbox = notification_queryset(user)
    return {
        "total": inbox.active().count(),
        "unread": unread_count(user),
        "action_required": action_count(user),
        "delivered": inbox.filter(
            status=NotificationStatus.DELIVERED, is_archived=False
        ).count(),
        "read": inbox.filter(read_status=ReadStatus.READ, is_archived=False).count(),
    }


def announcement_summary_counts() -> dict:
    """Announcement counts for admin dashboards."""
    active = SystemAnnouncement.objects.active()
    return {
        "published": active.count(),
        "drafts": SystemAnnouncement.objects.filter(is_published=False).count(),
        "acknowledgement_required": active.filter(
            acknowledgement_required=True
        ).count(),
    }
