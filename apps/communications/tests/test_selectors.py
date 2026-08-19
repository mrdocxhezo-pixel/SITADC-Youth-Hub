"""Communication selector tests."""

from __future__ import annotations

from django.contrib.auth.models import AnonymousUser

from apps.communications.selectors import (
    can_manage_communications,
    get_accessible_communications,
    get_accessible_media_assets,
    get_dashboard_summary,
    get_recent_communications,
    get_upcoming_event_communications,
)

from .base import CommunicationsTestCase


class SelectorTests(CommunicationsTestCase):
    """Tests for the fail-closed selector layer."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)

    def test_get_accessible_communications_with_permission(self):
        """Test that users with permission see communications."""
        self.create_communication()
        qs = get_accessible_communications(self.user)
        self.assertEqual(qs.count(), 1)

    def test_get_accessible_communications_denied(self):
        """Test that users without permission receive an empty queryset."""
        qs = get_accessible_communications(self.user_without_permissions())
        self.assertEqual(qs.count(), 0)

    def test_get_accessible_media_assets_with_permission(self):
        """Test that media assets are accessible with permission."""
        self.create_media_asset()
        qs = get_accessible_media_assets(self.user)
        self.assertEqual(qs.count(), 1)

    def test_get_dashboard_summary_with_permission(self):
        """Test dashboard summary counts."""
        self.create_communication()
        self.create_announcement()
        summary = get_dashboard_summary(self.user)
        self.assertEqual(summary["communications"], 1)
        self.assertEqual(summary["announcements"], 1)

    def test_get_dashboard_summary_denied(self):
        """Test that denied users receive an empty summary."""
        summary = get_dashboard_summary(self.user_without_permissions())
        self.assertEqual(summary, {})

    def test_get_recent_communications(self):
        """Test recent communications ordering."""
        self.create_communication(title="First")
        self.create_communication(title="Second", reference_number="COM-002")
        qs = get_recent_communications(self.user, limit=5)
        self.assertEqual(qs.count(), 2)
        self.assertEqual(qs[0].title, "Second")

    def test_get_recent_communications_denied(self):
        """Test that denied users receive an empty queryset."""
        qs = get_recent_communications(self.user_without_permissions())
        self.assertEqual(qs.count(), 0)

    def test_get_upcoming_event_communications(self):
        """Test upcoming event communications ordering."""
        from datetime import timedelta

        from django.utils import timezone

        self.create_event_communication(event_date=timezone.now() + timedelta(days=1))
        self.create_event_communication(
            title="Past Event",
            reference_number="EVC-002",
            event_date=timezone.now() - timedelta(days=1),
        )
        qs = get_upcoming_event_communications(self.user, limit=5)
        self.assertEqual(qs.count(), 1)

    def test_can_manage_communications(self):
        """Test manage permission helper."""
        self.assertTrue(can_manage_communications(self.user))
        self.assertFalse(can_manage_communications(self.user_without_permissions()))

    def test_anonymous_user_denied(self):
        """Test that anonymous users are denied."""
        anon = AnonymousUser()
        self.assertEqual(get_accessible_communications(anon).count(), 0)
        self.assertEqual(get_dashboard_summary(anon), {})

    def user_without_permissions(self):
        """Return a user with no communications permissions."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.create_user(
            username="noperms",
            email="noperms@example.com",
            password="testpass123",
        )
