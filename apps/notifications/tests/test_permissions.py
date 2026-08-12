"""Permission-level tests for the Notifications & Announcements app."""

from __future__ import annotations

from django.urls import reverse

from apps.notifications.permissions import (
    user_can_manage_announcements,
    user_can_manage_notifications,
    user_can_manage_rules,
    user_can_manage_templates,
    user_can_view_notifications,
)
from apps.notifications.tests.base import NotificationsTestCase


class PermissionHelperTests(NotificationsTestCase):
    def test_manager_has_full_control(self):
        self.assertTrue(user_can_manage_notifications(self.manager))
        self.assertTrue(user_can_manage_announcements(self.manager))
        self.assertTrue(user_can_manage_templates(self.manager))
        self.assertTrue(user_can_manage_rules(self.manager))
        self.assertTrue(user_can_view_notifications(self.manager))

    def test_officer_manages_templates_rules_announcements(self):
        self.assertTrue(user_can_manage_templates(self.officer))
        self.assertTrue(user_can_manage_rules(self.officer))
        self.assertTrue(user_can_manage_announcements(self.officer))
        self.assertTrue(user_can_view_notifications(self.officer))

    def test_viewer_can_only_view(self):
        self.assertFalse(user_can_manage_notifications(self.viewer))
        self.assertFalse(user_can_manage_announcements(self.viewer))
        self.assertFalse(user_can_manage_templates(self.viewer))
        self.assertFalse(user_can_manage_rules(self.viewer))
        self.assertTrue(user_can_view_notifications(self.viewer))

    def test_outsider_has_no_permissions(self):
        self.assertFalse(user_can_view_notifications(self.outsider))


class ViewAccessControlTests(NotificationsTestCase):
    def test_inbox_requires_login(self):
        response = self.client.get(reverse("notifications:inbox"))
        self.assertEqual(response.status_code, 302)

    def test_preferences_accessible_to_viewer(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("notifications:preferences"))
        self.assertEqual(response.status_code, 200)

    def test_template_list_denied_to_viewer(self):
        self.login_as(self.viewer)
        self.assertEqual(
            self.client.get(reverse("notifications:template_list")).status_code, 403
        )

    def test_template_list_allowed_to_officer(self):
        self.login_as(self.officer)
        self.assertEqual(
            self.client.get(reverse("notifications:template_list")).status_code, 200
        )

    def test_rule_list_denied_to_viewer(self):
        self.login_as(self.viewer)
        self.assertEqual(
            self.client.get(reverse("notifications:rule_list")).status_code, 403
        )

    def test_announcement_list_denied_to_viewer(self):
        self.login_as(self.viewer)
        self.assertEqual(
            self.client.get(reverse("notifications:announcement_list")).status_code, 403
        )

    def test_event_list_denied_to_officer(self):
        self.login_as(self.officer)
        self.assertEqual(
            self.client.get(reverse("notifications:event_list")).status_code, 403
        )
