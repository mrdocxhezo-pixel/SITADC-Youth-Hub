"""Shared fixtures for Report Builder tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class ReportsTestCase(TestCase):
    """Set up default users and permissions for report builder tests."""

    password = "TestPass123!"

    @classmethod
    def setUpTestData(cls):
        # Seed default report categories and settings required for tests
        from apps.reports.seed_loader import seed_report_builder_defaults

        seed_report_builder_defaults()

        # Ensure permissions exist even if running with --nomigrations
        from django.apps import apps
        from django.contrib.auth.management import create_permissions

        for app_config in apps.get_app_configs():
            app_config.models_module = True  # force it to process
            create_permissions(app_config, verbosity=0)

        # Ensure reference numbering scheme exists
        from apps.references.constants import ReferenceModules, SequenceResetPeriod
        from apps.references.models import ReferenceNumberScheme

        ReferenceNumberScheme.objects.get_or_create(
            code="report_template",
            defaults={
                "name": "Report Template Reference",
                "module": ReferenceModules.REPORTS,
                "record_type": "report_template",
                "prefix": "RT",
                "sequence_length": 4,
                "reset_period": SequenceResetPeriod.NEVER,
                "is_active": True,
            },
        )

        # Create test users
        cls.manager = cls.create_test_user("manager")
        cls.officer = cls.create_test_user("officer")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")

        # Assign permissions using RBAC helper (handles caching)
        from django.contrib.contenttypes.models import ContentType

        ct, _ = ContentType.objects.get_or_create(
            app_label="reports", model="reporttemplate"
        )
        p_manage, _ = Permission.objects.get_or_create(
            codename="report_templates.manage",
            content_type=ct,
            defaults={"name": "Manage templates"},
        )
        p_create, _ = Permission.objects.get_or_create(
            codename="report_templates.create",
            content_type=ct,
            defaults={"name": "Create templates"},
        )
        p_update, _ = Permission.objects.get_or_create(
            codename="report_templates.update",
            content_type=ct,
            defaults={"name": "Update templates"},
        )
        p_view, _ = Permission.objects.get_or_create(
            codename="report_templates.view",
            content_type=ct,
            defaults={"name": "View templates"},
        )

        # Manager gets full control
        cls.manager.user_permissions.add(p_manage)
        # Officer can create / update / view
        cls.officer.user_permissions.add(p_create, p_update, p_view)
        # Viewer can only view
        cls.viewer.user_permissions.add(p_view)
        # Clear permission cache after assignment
        clear_permission_cache(cls.manager)
        clear_permission_cache(cls.officer)
        clear_permission_cache(cls.viewer)

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

    def login_as(self, user):
        """Helper to authenticate a test user using the custom User model (email)."""
        return self.client.login(email=user.email, password=self.password)

    def grant_permissions(self, user, *codenames: str):
        perms = [Permission.objects.get(codename=code) for code in codenames]
        user.user_permissions.add(*perms)
        clear_permission_cache(user)
