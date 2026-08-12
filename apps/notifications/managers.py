"""Managers and querysets for the Notifications module."""

from __future__ import annotations

from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.managers import BaseManager, SoftDeleteManager

from .constants import (
    DeliveryStatus,
    NotificationStatus,
    NotificationType,
    ReadStatus,
)


class NotificationQuerySet(models.QuerySet):
    """Custom queryset for the ``Notification`` model."""

    def for_user(self, user):
        """Filter notifications addressed to a user."""
        return self.filter(recipient=user)

    def unread(self):
        """Filter unread notifications."""
        return self.filter(read_status=ReadStatus.UNREAD)

    def read(self):
        """Filter notifications that have been read."""
        return self.filter(read_status=ReadStatus.READ)

    def acknowledged(self):
        """Filter notifications that required and received acknowledgement."""
        return self.filter(read_status=ReadStatus.ACKNOWLEDGED)

    def action_required(self):
        """Filter notifications that ask the recipient to take action."""
        return self.filter(
            Q(notification_type=NotificationType.ACTION_REQUIRED)
            | Q(notification_type=NotificationType.APPROVAL_REQUIRED)
            | Q(notification_type=NotificationType.REVIEW_REQUIRED)
            | Q(acknowledgement_required=True)
        )

    def by_priority(self, *priorities):
        """Filter by one or more priority levels."""
        return self.filter(priority__in=priorities)

    def by_category(self, *categories):
        """Filter by one or more categories."""
        return self.filter(category__in=categories)

    def by_status(self, *statuses):
        """Filter by one or more lifecycle statuses."""
        return self.filter(status__in=statuses)

    def active(self):
        """Filter notifications that are current, not archived/expired/cancelled."""
        now = timezone.now()
        return self.exclude(
            Q(status=NotificationStatus.CANCELLED)
            | Q(status=NotificationStatus.EXPIRED)
            | Q(expiry_at__lt=now)
        ).filter(is_archived=False)

    def scheduled(self):
        """Filter scheduled notifications."""
        return self.filter(status=NotificationStatus.SCHEDULED)

    def pending_delivery(self):
        """Filter notifications awaiting delivery dispatch."""
        return self.filter(
            status__in=[
                NotificationStatus.PENDING,
                NotificationStatus.SCHEDULED,
                NotificationStatus.QUEUED,
            ]
        )

    def with_delivery_tracking(self):
        """Prefetch delivery attempts for the queryset."""
        return self.prefetch_related("delivery_attempts")

    def recent_first(self):
        """Order by most recently created first."""
        return self.order_by("-created_at")

    def unread_count_for(self, user):
        """Return the number of unread notifications for a user."""
        return self.for_user(user).unread().count()


class NotificationManager(BaseManager, SoftDeleteManager):
    """Manager for the ``Notification`` model."""

    def get_queryset(self):
        return NotificationQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def unread(self):
        return self.get_queryset().unread()

    def action_required(self):
        return self.get_queryset().action_required()


class NotificationTemplateQuerySet(models.QuerySet):
    """Custom queryset for the ``NotificationTemplate`` model."""

    def active(self):
        return self.filter(is_active=True)

    def by_category(self, category):
        return self.filter(category=category)

    def by_channel(self, channel):
        return self.filter(channel=channel)

    def by_event_type(self, event_type):
        return self.filter(event_type=event_type)

    def for_code(self, code):
        return self.filter(code=code)


class NotificationTemplateManager(BaseManager):
    """Manager for the ``NotificationTemplate`` model."""

    def get_queryset(self):
        return NotificationTemplateQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class NotificationRuleQuerySet(models.QuerySet):
    """Custom queryset for the ``NotificationRule`` model."""

    def active(self):
        return self.filter(is_active=True)

    def for_event(self, event_type):
        return self.filter(event_type=event_type)

    def for_category(self, category):
        return self.filter(category=category)


class NotificationRuleManager(BaseManager):
    """Manager for the ``NotificationRule`` model."""

    def get_queryset(self):
        return NotificationRuleQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class NotificationPreferenceQuerySet(models.QuerySet):
    """Custom queryset for the ``NotificationPreference`` model."""

    def for_user(self, user):
        return self.filter(user=user).first()


class NotificationPreferenceManager(BaseManager):
    """Manager for the ``NotificationPreference`` model."""

    def get_queryset(self):
        return NotificationPreferenceQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def get_or_create_for_user(self, user):
        obj, created = self.get_queryset().get_or_create(user=user)
        return obj, created


class NotificationDeliveryQuerySet(models.QuerySet):
    """Custom queryset for the ``NotificationDelivery`` model."""

    def pending_retry(self):
        now = timezone.now()
        return self.filter(
            status__in=[DeliveryStatus.QUEUED, DeliveryStatus.FAILED],
            next_retry_at__lte=now,
            retry_count__lt=3,
        )

    def queued(self):
        return self.filter(status=DeliveryStatus.QUEUED)

    def failed(self):
        return self.filter(status=DeliveryStatus.FAILED)

    def by_channel(self, channel):
        return self.filter(channel=channel)


class NotificationDeliveryManager(BaseManager):
    """Manager for the ``NotificationDelivery`` model."""

    def get_queryset(self):
        return NotificationDeliveryQuerySet(self.model, using=self._db)

    def pending_retry(self):
        return self.get_queryset().pending_retry()


class AnnouncementQuerySet(models.QuerySet):
    """Custom queryset for announcements (deprecated ``Announcement``)."""

    def published(self):
        return self.filter(is_published=True, publish_at__lte=timezone.now())


class AnnouncementManager(BaseManager):
    """Manager for announcements."""

    def get_queryset(self):
        return AnnouncementQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()


class SystemAnnouncementQuerySet(models.QuerySet):
    """Custom queryset for the ``SystemAnnouncement`` model."""

    def active(self):
        now = timezone.now()
        return self.filter(is_published=True, publish_at__lte=now).exclude(
            expires_at__lt=now
        )

    def dismissible(self):
        return self.filter(is_dismissible=True)

    def requires_acknowledgement(self):
        return self.filter(acknowledgement_required=True)

    def for_recipient(self, user):
        """Announcements relevant to a recipient (published + not dismissed)."""
        from .models import AnnouncementDismissal

        dismissed_ids = AnnouncementDismissal.objects.filter(user=user).values_list(
            "announcement_id", flat=True
        )
        return self.active().exclude(id__in=dismissed_ids)


class SystemAnnouncementManager(BaseManager):
    """Manager for the ``SystemAnnouncement`` model."""

    def get_queryset(self):
        return SystemAnnouncementQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()
