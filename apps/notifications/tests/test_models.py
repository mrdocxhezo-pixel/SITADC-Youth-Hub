"""Model-level tests for the Notifications & Announcements app."""

from __future__ import annotations

from django.db import IntegrityError
from django.utils import timezone

from apps.notifications.constants import (
    DeliveryStatus,
    NotificationPriority,
    NotificationType,
    ReadStatus,
)
from apps.notifications.models import (
    AnnouncementDelivery,
    Notification,
    NotificationEvent,
    NotificationPreference,
    SystemAnnouncement,
)
from apps.notifications.tests.base import NotificationsTestCase


class NotificationModelTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.notification = self.create_notification(self.manager)

    def test_reference_allocated_on_create(self):
        self.assertIn("NTF-", self.notification.reference)

    def test_default_expiry_is_set(self):
        self.assertIsNotNone(self.notification.expiry_at)

    def test_mark_read(self):
        self.notification.mark_read()
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.read_status, ReadStatus.READ)
        self.assertIsNotNone(self.notification.read_at)

    def test_acknowledge_requires_flag(self):
        self.notification.acknowledge(self.viewer)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.read_status, ReadStatus.UNREAD)

    def test_acknowledge_when_required(self):
        notification = self.create_notification(
            self.manager, acknowledgement_required=True
        )
        notification.acknowledge(self.viewer)
        notification.refresh_from_db()
        self.assertEqual(notification.read_status, ReadStatus.ACKNOWLEDGED)
        self.assertEqual(notification.acknowledged_by, self.viewer)

    def test_icon_mapping(self):
        notification = self.create_notification(
            self.manager, notification_type=NotificationType.WARNING
        )
        self.assertEqual(notification.icon, "bi-exclamation-triangle")

    def test_badge_color_mapping(self):
        notification = self.create_notification(
            self.manager, priority=NotificationPriority.URGENT
        )
        self.assertEqual(notification.badge_color, "text-bg-danger")

    def test_is_expired(self):
        self.notification.expiry_at = timezone.now() - timezone.timedelta(days=1)
        self.notification.save()
        self.assertTrue(self.notification.is_expired())

    def test_queryset_filters(self):
        notification = self.create_notification(self.manager, recipient=self.viewer)
        self.assertTrue(
            Notification.objects.for_user(self.viewer)
            .filter(pk=notification.pk)
            .exists()
        )
        self.assertEqual(
            Notification.objects.unread().filter(pk=notification.pk).count(), 1
        )


class NotificationDeliveryModelTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.notification = self.create_notification(self.manager)
        self.delivery = self.notification.delivery_attempts.get()

    def test_mark_delivered(self):
        self.delivery.mark_delivered()
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, DeliveryStatus.DELIVERED)
        self.assertIsNotNone(self.delivery.delivered_at)

    def test_mark_failed_schedules_retry(self):
        self.delivery.mark_failed(
            category="provider_error", summary="Provider unavailable", retryable=True
        )
        self.delivery.refresh_from_db()
        self.assertEqual(self.delivery.status, DeliveryStatus.FAILED)
        self.assertEqual(self.delivery.retry_count, 1)
        self.assertIsNotNone(self.delivery.next_retry_at)


class NotificationPreferenceModelTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.preference = NotificationPreference.objects.create(user=self.viewer)

    def test_category_allowed_default(self):
        self.assertTrue(self.preference.category_allowed("GENERAL"))

    def test_category_allowed_muted(self):
        self.preference.category_preferences = {"GENERAL": {"in_app": False}}
        self.preference.save()
        self.assertFalse(self.preference.category_allowed("GENERAL"))

    def test_mandatory_category_cannot_be_muted(self):
        self.preference.mandatory_categories = ["SECURITY"]
        self.preference.category_preferences = {"SECURITY": {"in_app": False}}
        self.preference.save()
        self.assertTrue(self.preference.category_allowed("SECURITY"))

    def test_channel_enabled(self):
        self.assertTrue(self.preference.channel_enabled("IN_APP"))
        self.preference.email_enabled = True
        self.preference.save()
        self.assertTrue(self.preference.channel_enabled("EMAIL", "GENERAL"))

    def test_quiet_hours(self):
        self.preference.quiet_hours_enabled = True
        self.preference.quiet_hours_start = "22:00"
        self.preference.quiet_hours_end = "07:00"
        self.preference.save()
        when = timezone.now().replace(hour=23, minute=30, second=0, microsecond=0)
        self.assertTrue(self.preference.in_quiet_hours(when))
        when = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)
        self.assertFalse(self.preference.in_quiet_hours(when))


class NotificationEventModelTests(NotificationsTestCase):
    def test_event_created_with_payload(self):
        event = NotificationEvent.objects.create(
            event_type="report.submitted",
            source_app="reports",
            payload={"title": "Q1 Report"},
            created_by=self.manager,
            actor=self.manager,
        )
        self.assertEqual(event.event_type, "report.submitted")
        self.assertFalse(event.processed)

    def test_event_deduplication_key_indexed(self):
        NotificationEvent.objects.create(
            event_type="meeting.scheduled",
            source_app="meetings",
            deduplication_key="abc-123",
            created_by=self.manager,
            actor=self.manager,
        )
        self.assertEqual(
            NotificationEvent.objects.filter(deduplication_key="abc-123").count(), 1
        )


class SystemAnnouncementModelTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.announcement = self.create_announcement(self.manager)

    def test_reference_allocated_on_create(self):
        self.assertIn("ANN-", self.announcement.reference)

    def test_default_expiry_set(self):
        self.assertIsNotNone(self.announcement.expires_at)

    def test_publish_and_unpublish(self):
        self.announcement.publish(self.manager)
        self.announcement.refresh_from_db()
        self.assertTrue(self.announcement.is_published)
        self.announcement.unpublish(self.manager)
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)

    def test_audience_recipients_everyone(self):
        self.announcement.publish(self.manager)
        recipients = self.announcement.audience_recipients()
        self.assertIn(self.viewer, recipients)
        self.assertIn(self.manager, recipients)

    def test_announcement_delivery_unique_per_recipient(self):
        AnnouncementDelivery.objects.create(
            announcement=self.announcement, recipient=self.viewer
        )
        with self.assertRaises(IntegrityError):
            AnnouncementDelivery.objects.create(
                announcement=self.announcement, recipient=self.viewer
            )


class SystemAnnouncementStatusTests(NotificationsTestCase):
    def test_active_queryset(self):
        announcement = self.create_announcement(self.manager, publish_now=True)
        announcement.publish_at = timezone.now() - timezone.timedelta(hours=1)
        announcement.expires_at = timezone.now() + timezone.timedelta(days=1)
        announcement.save()
        self.assertTrue(
            SystemAnnouncement.objects.active().filter(pk=announcement.pk).exists()
        )

    def test_expired_excluded_from_active(self):
        announcement = self.create_announcement(self.manager, publish_now=True)
        announcement.expires_at = timezone.now() - timezone.timedelta(hours=1)
        announcement.save()
        self.assertFalse(
            SystemAnnouncement.objects.active().filter(pk=announcement.pk).exists()
        )
