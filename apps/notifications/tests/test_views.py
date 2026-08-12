"""View-level tests for the Notifications & Announcements app."""

from __future__ import annotations

from django.urls import reverse
from django.utils import timezone

from apps.notifications.constants import (
    AnnouncementAudience,
    AnnouncementType,
    DeliveryChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationStatus,
    NotificationType,
    ReadStatus,
)
from apps.notifications.models import (
    Notification,
    NotificationPreference,
    NotificationRule,
    NotificationTemplate,
    SystemAnnouncement,
)
from apps.notifications.tests.base import NotificationsTestCase


class DashboardViewTests(NotificationsTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("notifications:dashboard"))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_to_authenticated_user(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notifications &amp; Announcements")

    def test_dashboard_shows_recent_notifications(self):
        self.create_notification(self.manager, title="Hello from the dashboard")
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:dashboard"))
        self.assertContains(response, "Hello from the dashboard")


class InboxViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)
        self.notification = self.create_notification(self.manager)

    def test_inbox_lists_own_notifications(self):
        response = self.client.get(reverse("notifications:inbox"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.notification.title)

    def test_inbox_unread_filter(self):
        response = self.client.get(reverse("notifications:inbox") + "?status=unread")
        self.assertContains(response, self.notification.title)

    def test_inbox_archived_filter(self):
        self.notification.archive()
        response = self.client.get(reverse("notifications:inbox") + "?status=archived")
        self.assertContains(response, self.notification.title)

    def test_inbox_excludes_other_users_notifications(self):
        other = self.create_notification(
            self.manager, recipient=self.manager, title="Private to manager"
        )
        response = self.client.get(reverse("notifications:inbox"))
        self.assertNotContains(response, other.title)


class NotificationDetailViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)
        self.notification = self.create_notification(self.manager)

    def test_detail_marks_read(self):
        response = self.client.get(
            reverse("notifications:notification_detail", args=[self.notification.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.read_status, ReadStatus.READ)

    def test_detail_denied_for_outsider(self):
        self.client.logout()
        self.login_as(self.outsider)
        response = self.client.get(
            reverse("notifications:notification_detail", args=[self.notification.pk])
        )
        self.assertEqual(response.status_code, 404)

    def test_open_redirect_resolves(self):
        response = self.client.get(
            reverse("notifications:notification_open", args=[self.notification.pk])
        )
        self.assertEqual(response.status_code, 302)


class NotificationActionViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)
        self.notification = self.create_notification(self.manager)

    def test_mark_read_post(self):
        response = self.client.post(
            reverse("notifications:notification_mark_read", args=[self.notification.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.read_status, ReadStatus.READ)

    def test_acknowledge_post(self):
        notification = self.create_notification(
            self.manager, acknowledgement_required=True
        )
        response = self.client.post(
            reverse("notifications:notification_acknowledge", args=[notification.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)
        notification.refresh_from_db()
        self.assertEqual(notification.read_status, ReadStatus.ACKNOWLEDGED)

    def test_archive_post(self):
        response = self.client.post(
            reverse("notifications:notification_archive", args=[self.notification.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_archived)

    def test_mark_all_read(self):
        self.create_notification(self.manager, recipient=self.viewer)
        self.client.post(reverse("notifications:mark_all_read"))
        self.assertEqual(Notification.objects.for_user(self.viewer).unread().count(), 0)


class PreferenceViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)

    def test_preference_form_get(self):
        response = self.client.get(reverse("notifications:preferences"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Notification preferences")

    def test_preference_form_post(self):
        response = self.client.post(
            reverse("notifications:preferences"),
            {
                "in_app_enabled": "on",
                "digest_frequency": "WEEKLY",
                "digest_timezone": "Africa/Lusaka",
                "quiet_hours_policy": "RESPECT",
                "timezone": "Africa/Lusaka",
                "reminder_frequency": "IMMEDIATE",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            NotificationPreference.objects.filter(user=self.viewer).exists()
        )


class TemplateViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.officer)
        self.template = self.create_template(self.officer, code="existing")

    def test_template_list_requires_permission(self):
        self.client.logout()
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:template_list"))
        self.assertEqual(response.status_code, 403)

    def test_template_list_view(self):
        response = self.client.get(reverse("notifications:template_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.template.name)

    def test_template_create_view(self):
        response = self.client.post(
            reverse("notifications:template_create"),
            {
                "code": "new_template",
                "name": "New Template",
                "category": NotificationCategory.GENERAL,
                "channel": DeliveryChannel.IN_APP,
                "title_template": "Hello {{ user_name }}",
                "message_template": "A message",
                "priority": NotificationPriority.NORMAL,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            NotificationTemplate.objects.filter(code="new_template").exists()
        )

    def test_template_update_view(self):
        response = self.client.post(
            reverse("notifications:template_update", args=[self.template.pk]),
            {
                "code": "existing",
                "name": "Renamed",
                "category": NotificationCategory.GENERAL,
                "channel": DeliveryChannel.IN_APP,
                "title_template": "Hello {{ user_name }}",
                "message_template": "A message",
                "priority": NotificationPriority.NORMAL,
                "is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.template.refresh_from_db()
        self.assertEqual(self.template.name, "Renamed")


class RuleViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.officer)
        self.rule = self.create_rule(self.officer, event_type="test.event")

    def test_rule_list_requires_permission(self):
        self.client.logout()
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:rule_list"))
        self.assertEqual(response.status_code, 403)

    def test_rule_list_view(self):
        response = self.client.get(reverse("notifications:rule_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.rule.name)

    def test_rule_create_view(self):
        response = self.client.post(
            reverse("notifications:rule_create"),
            {
                "name": "New Rule",
                "event_type": "report.submitted",
                "category": NotificationCategory.REPORTS,
                "notification_type": NotificationType.INFORMATION,
                "priority": NotificationPriority.NORMAL,
                "channels": [DeliveryChannel.IN_APP],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            NotificationRule.objects.filter(name="New Rule").exists()
        )

    def test_rule_update_view(self):
        response = self.client.post(
            reverse("notifications:rule_update", args=[self.rule.pk]),
            {
                "name": "Renamed Rule",
                "event_type": "test.event",
                "category": NotificationCategory.GENERAL,
                "notification_type": NotificationType.INFORMATION,
                "priority": NotificationPriority.NORMAL,
                "channels": [DeliveryChannel.IN_APP],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.rule.refresh_from_db()
        self.assertEqual(self.rule.name, "Renamed Rule")


class AnnouncementViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.officer)
        self.announcement = self.create_announcement(self.officer)

    def test_announcement_list_requires_permission(self):
        self.client.logout()
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:announcement_list"))
        self.assertEqual(response.status_code, 403)

    def test_announcement_list_view(self):
        response = self.client.get(reverse("notifications:announcement_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.announcement.title)

    def test_announcement_create_view(self):
        response = self.client.post(
            reverse("notifications:announcement_create"),
            {
                "title": "New Announcement",
                "message": "Big news!",
                "announcement_type": AnnouncementType.ORGANIZATION_WIDE,
                "audience_type": AnnouncementAudience.EVERYONE,
                "priority": NotificationPriority.NORMAL,
                "category": NotificationCategory.ANNOUNCEMENTS,
                "is_dismissible": "on",
                "acknowledgement_required": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SystemAnnouncement.objects.filter(title="New Announcement").exists()
        )

    def test_announcement_update_view(self):
        response = self.client.post(
            reverse("notifications:announcement_update", args=[self.announcement.pk]),
            {
                "title": "Updated Announcement",
                "message": "Updated news!",
                "announcement_type": AnnouncementType.ORGANIZATION_WIDE,
                "audience_type": AnnouncementAudience.EVERYONE,
                "priority": NotificationPriority.NORMAL,
                "category": NotificationCategory.ANNOUNCEMENTS,
                "is_dismissible": "on",
                "acknowledgement_required": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.announcement.refresh_from_db()
        self.assertEqual(self.announcement.title, "Updated Announcement")

    def test_announcement_publish_view(self):
        response = self.client.post(
            reverse(
                "notifications:announcement_publish", args=[self.announcement.pk]
            )
        )
        self.assertEqual(response.status_code, 302)
        self.announcement.refresh_from_db()
        self.assertTrue(self.announcement.is_published)

    def test_announcement_publish_denied_for_viewer(self):
        self.client.logout()
        self.login_as(self.viewer)
        response = self.client.post(
            reverse(
                "notifications:announcement_publish", args=[self.announcement.pk]
            )
        )
        self.assertEqual(response.status_code, 302)
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)

    def test_announcement_unpublish_view(self):
        self.announcement.publish(self.officer)
        self.client.post(
            reverse(
                "notifications:announcement_unpublish", args=[self.announcement.pk]
            )
        )
        self.announcement.refresh_from_db()
        self.assertFalse(self.announcement.is_published)

    def test_announcement_dismiss_ajax(self):
        self.announcement.publish(self.officer)
        self.client.logout()
        self.login_as(self.viewer)
        response = self.client.post(
            reverse(
                "notifications:announcement_dismiss", args=[self.announcement.pk]
            ),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)
        self.assertTrue(
            self.announcement.dismissals.filter(user=self.viewer).exists()
        )


class AdminListViewTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.manager)

    def test_event_list_requires_manage(self):
        self.client.logout()
        self.login_as(self.officer)
        self.assertEqual(
            self.client.get(reverse("notifications:event_list")).status_code, 403
        )

    def test_event_list_view(self):
        response = self.client.get(reverse("notifications:event_list"))
        self.assertEqual(response.status_code, 200)

    def test_audit_list_view(self):
        response = self.client.get(reverse("notifications:audit_list"))
        self.assertEqual(response.status_code, 200)


class JsonEndpointTests(NotificationsTestCase):
    def setUp(self):
        super().setUp()
        self.login_as(self.viewer)
        self.create_notification(self.manager, recipient=self.viewer)

    def test_unread_count_json(self):
        response = self.client.get(reverse("notifications:api_unread_count"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.json()["unread"], 1)

    def test_recent_notifications_json(self):
        response = self.client.get(reverse("notifications:api_recent_notifications"))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()["items"]), 1)

    def test_json_endpoints_require_login(self):
        self.client.logout()
        response = self.client.get(reverse("notifications:api_unread_count"))
        self.assertEqual(response.status_code, 302)
