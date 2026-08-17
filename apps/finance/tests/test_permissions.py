"""Finance Engine permission tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finance.permissions import (
    FinancePermissionMixin,
    user_can_access_finance,
    user_can_manage_finance,
    user_can_view_budgets,
    user_can_view_financial_reports,
    user_can_view_transactions,
)

User = get_user_model()


class FinancePermissionTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="perm-admin", email="perm@test.local", password="pw"
        )
        self.plain = User.objects.create_user(
            username="perm-plain", email="plain@test.local", password="pw"
        )
        self.anonymous = User(username="anon", password="pw")

    def test_superuser_has_all_access(self):
        self.assertTrue(user_can_access_finance(self.superuser))
        self.assertTrue(user_can_manage_finance(self.superuser))
        self.assertTrue(user_can_view_financial_reports(self.superuser))
        self.assertTrue(user_can_view_budgets(self.superuser))
        self.assertTrue(user_can_view_transactions(self.superuser))

    def test_plain_user_denied_by_default(self):
        self.assertFalse(user_can_access_finance(self.plain))
        self.assertFalse(user_can_manage_finance(self.plain))
        self.assertFalse(user_can_view_financial_reports(self.plain))

    def test_anonymous_denied(self):
        self.assertFalse(user_can_access_finance(self.anonymous))
        self.assertFalse(user_can_view_budgets(self.anonymous))

    def test_none_user_denied(self):
        self.assertFalse(user_can_access_finance(None))

    def test_permission_mixin_denies_plain_user(self):
        mixin = FinancePermissionMixin()
        request = type("Request", (), {"user": self.plain})()
        from django.core.exceptions import PermissionDenied

        with self.assertRaises(PermissionDenied):
            mixin.dispatch(request)
