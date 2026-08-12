"""Selector tests for the Notifications & Announcements app."""

from __future__ import annotations

from django.utils import timezone

from apps.notifications.constants import (
    NotificationCategory,
    NotificationType,
)
from apps.notifications.selectors import (
    action_required_notifications,
    active_notifications,
    announcement_queryset,
    announcement_summary_counts,
    category_breakdown,
    digest_summary_counts,
    expired_notifications,
    notification_preference_for,
    unread_count,
)
from apps.notifications.tests.base import NotificationsTestCase


class NotificationSelectorTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.notification = self.create_notification(self.manager)

    def test_active_notifications_for_user(self):
        notifications = active_notifications(self.viewer)
        self.assertIn(self.notification, notifications)

    def test_unread_count(self):
        self.assertEqual(unread_count(self.viewer), 1)

    def test_unread_count_after_read(self):
        self.notification.mark_read()
        self.assertEqual(unread_count(self.viewer), 0)

    def test_action_required_notifications(self):
        action = self.create_notification(
            self.manager,
            notification_type=NotificationType.ACTION_REQUIRED,
        )
        results = action_required_notifications(self.viewer)
        self.assertIn(action, results)

    def test_archived_notifications_hidden(self):
        self.notification.archive()
        self.assertNotIn(self.notification, active_notifications(self.viewer))

    def test_category_breakdown(self):
        rows = category_breakdown(self.viewer)
        self.assertEqual(rows[0]["code"], NotificationCategory.GENERAL)
        self.assertEqual(rows[0]["count"], 1)

    def test_digest_summary_counts(self):
        summary = digest_summary_counts(self.viewer)
        self.assertEqual(summary["unread"], 1)
        self.assertEqual(summary["total"], 1)

    def test_expired_notifications(self):
        self.notification.expiry_at = timezone.now() - timezone.timedelta(days=1)
        self.notification.save()
        self.assertIn(self.notification, expired_notifications(self.viewer))


class AnnouncementSelectorTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.announcement = self.create_announcement(self.manager, publish_now=True)

    def test_announcement_queryset_returns_published(self):
        results = announcement_queryset(self.viewer)
        self.assertIn(self.announcement, results)

    def test_dismissed_announcement_hidden(self):
        self.announcement.dismissals.create(user=self.viewer)
        self.assertNotIn(self.announcement, announcement_queryset(self.viewer))

    def test_announcement_summary_counts(self):
        counts = announcement_summary_counts()
        self.assertGreaterEqual(counts["published"], 1)


class PreferenceSelectorTests(NotificationsTestCase):
    def test_notification_preference_for(self):
        self.assertIsNone(notification_preference_for(self.viewer))
        from apps.notifications.models import NotificationPreference

        NotificationPreference.objects.create(user=self.viewer)
        self.assertIsNotNone(notification_preference_for(self.viewer))
