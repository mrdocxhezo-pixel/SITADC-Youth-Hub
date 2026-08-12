"""Tests for the Enterprise Search permission helpers."""

from __future__ import annotations

from apps.search.permissions import user_can_export, user_can_manage, user_can_search
from apps.search.tests.base import SearchTestCase


class PermissionHelperTests(SearchTestCase):
    """user_can_* helpers must be fail-closed and additive."""

    def test_superuser_can_search(self):
        self.assertTrue(user_can_search(self.admin))

    def test_viewer_with_view_can_search(self):
        self.assertTrue(user_can_search(self.viewer))

    def test_outsider_cannot_search(self):
        self.assertFalse(user_can_search(self.outsider))

    def test_anonymous_cannot_search(self):
        self.assertFalse(user_can_search(None))

    def test_export_requires_export_permission(self):
        self.assertTrue(user_can_export(self.manager))
        self.assertFalse(user_can_export(self.viewer))

    def test_manage_requires_manage_permission(self):
        self.assertTrue(user_can_manage(self.admin))
        self.assertFalse(user_can_manage(self.manager))
