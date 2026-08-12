"""Shared fixtures for Export Engine tests.

All tests talk to the real DB test mirror (SQLite) and exercise the actual
provider/renderer registries so permission scoping is verified end to end.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class ExportsTestCase(TestCase):
    """Base test case exposing permissioned users for exports."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        from django.apps import apps
        from django.contrib.auth.management import create_permissions

        for app_config in apps.get_app_configs():
            app_config.models_module = True
            create_permissions(app_config, verbosity=0)

        cls.admin = cls.create_test_user("admin", is_superuser=True)
        cls.manager = cls.create_test_user("manager")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")

        cls.grant_perms(
            cls.admin,
            "exports.view",
            "exports.create",
            "exports.download",
            "exports.manage",
            "exports.export_sensitive",
            "exports.export_reports",
            "exports.export_registers",
            "exports.export_directories",
            "exports.export_pdf",
            "exports.export_xlsx",
            "exports.export_csv",
            "exports.export_docx",
            "exports.print",
            "exports.view_all_history",
            "exports.cancel",
            "exports.regenerate",
            "report_templates.view",
            "beneficiaries.view",
        )
        cls.grant_perms(
            cls.manager,
            "exports.view",
            "exports.create",
            "exports.download",
            "exports.export_reports",
            "exports.export_beneficiaries",
            "exports.export_directories",
            "exports.export_pdf",
            "exports.export_xlsx",
            "exports.export_csv",
            "exports.print",
            "exports.cancel",
            "report_templates.view",
            "beneficiaries.view",
        )
        cls.grant_perms(cls.viewer, "exports.view", "exports.download")
        cls.grant_perms(cls.outsider, "exports.view")

    @classmethod
    def create_test_user(cls, stem: str, *, is_superuser: bool = False):
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=f"{stem}@example.com",
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
            is_superuser=is_superuser,
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
