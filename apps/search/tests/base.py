"""Shared fixtures for Enterprise Search tests.

All tests talk to the real DB test mirror (SQLite) and exercise the actual
provider registry so permission scoping is verified end to end.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class SearchTestCase(TestCase):
    """Base test case exposing permissioned users for search."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        from django.apps import apps
        from django.contrib.auth.management import create_permissions

        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)

        cls.admin = cls.create_test_user("admin")
        cls.manager = cls.create_test_user("manager")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")

        cls.grant_perms(cls.admin, "search.manage", "search.view", "search.export")
        cls.grant_perms(cls.manager, "search.view", "search.export")
        cls.grant_perms(cls.viewer, "search.view")

    @classmethod
    def create_test_user(cls, stem: str):
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=f"{stem}@example.com",
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
            password=cls.password,
        )

    @classmethod
    def grant_perms(cls, user, *codenames: str):
        from django.contrib.auth.models import Permission

        perms = [Permission.objects.get(codename=code) for code in codenames]
        user.user_permissions.add(*perms)
        clear_permission_cache(user)

    def login_as(self, user):
        return self.client.login(email=user.email, password=self.password)
