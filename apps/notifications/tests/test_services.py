"""Service-level tests for the Notifications & Announcements app."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.notifications.constants import (
    AnnouncementAudience,
    DeliveryStatus,
    NotificationCategory,
    NotificationStatus,
    ReadStatus,
)
from apps.notifications.models import (
    AnnouncementDelivery,
    Notification,
    NotificationAuditRecord,
    NotificationDigest,
    NotificationPreference,
)
from apps.notifications.services import (
    AcknowledgeNotificationService,
    AnnouncementService,
    ArchiveNotificationService,
    DigestService,
    MarkAllNotificationsReadService,
    MarkNotificationReadService,
    NotificationEventService,
    NotificationService,
    ProcessExpiredService,
    PublishAnnouncementService,
    RuleService,
    SendNotificationService,
    TemplateService,
    UnpublishAnnouncementService,
)
from apps.notifications.tests.base import NotificationsTestCase


class NotificationServiceTests(NotificationsTestCase):
    def test_create_allocates_reference_and_delivery(self):
        notification = self.create_notification(self.manager)
        self.assertIn("NTF-", notification.reference)
        self.assertEqual(notification.status, NotificationStatus.PENDING)
        self.assertEqual(notification.delivery_attempts.count(), 1)
        self.assertEqual(
            notification.delivery_attempts.get().status, DeliveryStatus.QUEUED
        )

    def test_create_respects_recipient_opt_out(self):
        preference = NotificationPreference.objects.create(user=self.viewer)
        preference.category_preferences = {"GENERAL": {"in_app": False}}
        preference.save()
        notification = self.create_notification(self.manager)
        notification.refresh_from_db()
        self.assertEqual(notification.status, NotificationStatus.CANCELLED)

    def test_create_deduplication(self):
        first = self.create_notification(self.manager, deduplication_key="dedup-key-1")
        second = self.create_notification(self.manager, deduplication_key="dedup-key-1")
        self.assertEqual(first.pk, second.pk)

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            self.create_notification(self.outsider)

    def test_create_from_event_without_rule_returns_none(self):
        result = NotificationService(user=self.manager).create_from_event(
            recipient=self.viewer,
            event_type="unknown.event",
            category=NotificationCategory.GENERAL,
        )
        self.assertIsNone(result)

    def test_create_from_event_with_rule(self):
        self.create_rule(self.officer, event_type="test.event")
        notification = NotificationService(user=self.manager).create_from_event(
            recipient=self.viewer,
            event_type="test.event",
            category=NotificationCategory.GENERAL,
            payload={"title": "Event!"},
        )
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Event!")


class SendNotificationServiceTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.notification = self.create_notification(self.manager)

    def test_send_marks_delivery(self):
        result = SendNotificationService(user=self.viewer).execute(self.notification)
        self.assertEqual(result.status, NotificationStatus.SENT)
        delivery = self.notification.delivery_attempts.get()
        self.assertEqual(delivery.status, DeliveryStatus.DELIVERED)

    def test_send_denied_for_non_recipient_without_permission(self):
        with self.assertRaises(PermissionDenied):
            SendNotificationService(user=self.outsider).execute(self.notification)

    def test_send_recipient_may_send(self):
        result = SendNotificationService(user=self.viewer).execute(self.notification)
        self.assertEqual(result.status, NotificationStatus.SENT)

    def test_send_already_delivered_idempotent(self):
        SendNotificationService(user=self.viewer).execute(self.notification)
        result = SendNotificationService(user=self.viewer).execute(self.notification)
        self.assertEqual(result.status, NotificationStatus.SENT)


class ReadServiceTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.notification = self.create_notification(self.manager)

    def test_mark_read_by_recipient(self):
        MarkNotificationReadService(user=self.viewer).execute(self.notification)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.read_status, ReadStatus.READ)

    def test_mark_read_denied_for_outsider(self):
        with self.assertRaises(PermissionDenied):
            MarkNotificationReadService(user=self.outsider).execute(self.notification)

    def test_mark_all_read(self):
        self.create_notification(self.manager, recipient=self.viewer)
        self.create_notification(self.manager, recipient=self.viewer)
        count = MarkAllNotificationsReadService(user=self.viewer).execute()
        self.assertEqual(count, 3)
        self.assertEqual(Notification.objects.for_user(self.viewer).unread().count(), 0)

    def test_acknowledge(self):
        notification = self.create_notification(
            self.manager, acknowledgement_required=True
        )
        AcknowledgeNotificationService(user=self.viewer).execute(notification)
        notification.refresh_from_db()
        self.assertEqual(notification.read_status, ReadStatus.ACKNOWLEDGED)

    def test_acknowledge_denied_for_outsider(self):
        notification = self.create_notification(
            self.manager, acknowledgement_required=True
        )
        with self.assertRaises(PermissionDenied):
            AcknowledgeNotificationService(user=self.outsider).execute(notification)

    def test_archive(self):
        ArchiveNotificationService(user=self.viewer).execute(self.notification)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_archived)

    def test_audit_records_created(self):
        MarkNotificationReadService(user=self.viewer).execute(self.notification)
        self.assertTrue(NotificationAuditRecord.objects.filter(action="READ").exists())


class NotificationEventServiceTests(NotificationsTestCase):
    def test_event_without_rules_is_processed(self):
        event = NotificationEventService(user=self.manager).execute(
            event_type="no.rules",
            source_app="tests",
        )
        event.refresh_from_db()
        self.assertTrue(event.processed)

    def test_event_creates_notifications_for_rule_recipient(self):
        self.create_rule(
            self.officer, event_type="test.event", recipient_user=self.viewer
        )
        event = NotificationEventService(user=self.manager).execute(
            event_type="test.event",
            source_app="tests",
            payload={"title": "Scheduled"},
        )
        event.refresh_from_db()
        self.assertTrue(event.processed)
        self.assertTrue(
            Notification.objects.for_user(self.viewer).filter(event=event).exists()
        )

    def test_event_deduplication(self):
        first = NotificationEventService(user=self.manager).execute(
            event_type="test.event",
            source_app="tests",
            deduplication_key="event-key",
        )
        second = NotificationEventService(user=self.manager).execute(
            event_type="test.event",
            source_app="tests",
            deduplication_key="event-key",
        )
        self.assertEqual(first.pk, second.pk)


class TemplateServiceTests(NotificationsTestCase):
    def test_create_template_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            TemplateService(user=self.outsider).execute(
                code="blocked",
                name="Blocked",
                title_template="Hi",
                message_template="Bye",
            )

    def test_create_and_update_template(self):
        template = self.create_template(self.officer, code="welcome")
        self.assertEqual(template.version, 1)
        updated = TemplateService(user=self.officer).execute(
            code="welcome",
            name="Welcome v2",
            title_template="Hi {{ user_name }}",
            message_template="Bye",
            instance=template,
        )
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.name, "Welcome v2")


class RuleServiceTests(NotificationsTestCase):
    def test_create_rule_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            RuleService(user=self.outsider).execute(
                name="Blocked", event_type="test.event"
            )

    def test_create_rule(self):
        rule = self.create_rule(self.officer, event_type="test.event")
        self.assertEqual(rule.event_type, "test.event")
        self.assertTrue(rule.is_active)

    def test_duplicate_rule_name_raises(self):
        self.create_rule(self.officer, name="Duplicate", event_type="test.event")
        with self.assertRaises(IntegrityError):
            self.create_rule(self.officer, name="Duplicate", event_type="test.event")


class AnnouncementServiceTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.announcement = self.create_announcement(self.manager)

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            self.create_announcement(self.outsider)

    def test_publish_fan_out(self):
        PublishAnnouncementService(user=self.officer).execute(self.announcement)
        self.announcement.refresh_from_db()
        self.assertTrue(self.announcement.is_published)
        # Everyone audience -> all four test users receive a notification.
        self.assertEqual(
            AnnouncementDelivery.objects.filter(announcement=self.announcement).count(),
            4,
        )

    def test_unpublish(self):
        PublishAnnouncementService(user=self.officer).execute(self.announcement)
        UnpublishAnnouncementService(user=self.officer).execute(self.announcement)
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)

    def test_publish_denied_without_permission(self):
        with self.assertRaises(PermissionDenied):
            PublishAnnouncementService(user=self.viewer).execute(self.announcement)

    def test_update_announcement(self):
        updated = AnnouncementService(user=self.officer).execute(
            title="Updated",
            message="New message",
            audience_type=AnnouncementAudience.EVERYONE,
            instance=self.announcement,
        )
        self.assertEqual(updated.title, "Updated")

    def test_expiry_before_publish_raises(self):
        with self.assertRaises(ValidationError):
            AnnouncementService(user=self.officer).execute(
                title="Bad",
                message="Bad",
                publish_at=timezone.now() + timezone.timedelta(days=1),
                expires_at=timezone.now(),
            )


class ProcessExpiredServiceTests(NotificationsTestCase):
    def test_expired_notification_marked(self):
        notification = self.create_notification(self.manager)
        notification.expiry_at = timezone.now() - timezone.timedelta(days=1)
        notification.save()
        count = ProcessExpiredService(user=self.manager).execute()
        self.assertEqual(count, 1)
        notification.refresh_from_db()
        self.assertEqual(notification.status, NotificationStatus.EXPIRED)


class DigestServiceTests(NotificationsTestCase):
    def test_digest_generated_for_eligible(self):
        NotificationPreference.objects.create(
            user=self.viewer, digest_frequency="WEEKLY"
        )
        self.create_notification(
            self.manager, is_digest_eligible=True, recipient=self.viewer
        )
        digest = DigestService(user=self.manager).execute(user=self.viewer)
        self.assertIsInstance(digest, NotificationDigest)
        self.assertEqual(digest.notification_count, 1)

    def test_no_digest_when_none_eligible(self):
        NotificationPreference.objects.create(
            user=self.viewer, digest_frequency="WEEKLY"
        )
        digest = DigestService(user=self.manager).execute(user=self.viewer)
        self.assertIsNone(digest)

    def test_no_digest_when_preferences_missing(self):
        digest = DigestService(user=self.manager).execute(user=self.viewer)
        self.assertIsNone(digest)
