"""Shared deterministic fixtures for Organizational Registers tests."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache
from apps.registers.constants import RegisterApprovalStatus
from apps.registers.models import RegisterEntry
from apps.registers.selectors import category_queryset, register_queryset
from apps.registers.services import (
    RegisterCategoryService,
    RegisterEntryService,
    RegisterService,
)
from apps.registers.storage import private_register_storage

User = get_user_model()


class RegistersTestCase(TestCase):
    """Seed users, permissions, and isolated private storage for tests."""

    password = "TestPassword123!"

    @classmethod
    def setUpTestData(cls):
        cls._sequence = 0
        cls.manager = cls.create_test_user("regmanager")
        cls.officer = cls.create_test_user("regofficer")
        cls.viewer = cls.create_test_user("regviewer")
        cls.outsider = cls.create_test_user("regoutsider")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="registers.manage")
        )
        cls.officer.user_permissions.add(
            Permission.objects.get(codename="registers.create"),
            Permission.objects.get(codename="registers.update"),
            Permission.objects.get(codename="registers.submit"),
            Permission.objects.get(codename="registers.review"),
            Permission.objects.get(codename="registers.approve"),
            Permission.objects.get(codename="registers.archive"),
            Permission.objects.get(codename="registers.restore"),
            Permission.objects.get(codename="registers.export"),
            Permission.objects.get(codename="registers.view"),
        )
        cls.viewer.user_permissions.add(
            Permission.objects.get(codename="registers.view")
        )
        cls.category = cls.create_category("Membership", "membership", "MEM")
        cls.register = cls.create_register(cls.category, cls.manager)

    def setUp(self):
        super().setUp()
        self.private_media = TemporaryDirectory()
        self._original_storage_location = private_register_storage._location
        private_register_storage._location = self.private_media.name
        self._clear_storage_cache()
        self.addCleanup(self._restore_private_storage)

    def _clear_storage_cache(self):
        private_register_storage.__dict__.pop("base_location", None)
        private_register_storage.__dict__.pop("location", None)

    def _restore_private_storage(self):
        private_register_storage._location = self._original_storage_location
        self._clear_storage_cache()
        self.private_media.cleanup()

    @classmethod
    def create_test_user(cls, stem: str):
        return User.objects.create_user(
            email=f"{stem}@example.com",
            username=stem,
            first_name=stem.title(),
            last_name="Tester",
            status=AccountStatus.ACTIVE,
        )

    def create_user(self, stem: str):
        return self.create_test_user(stem)

    def grant_permissions(self, user, *codes: str):
        permissions = [Permission.objects.get(codename=code) for code in codes]
        user.user_permissions.add(*permissions)
        clear_permission_cache(user)

    @classmethod
    def create_category(cls, name, code, prefix):
        return RegisterCategoryService(user=cls.manager).execute(
            name=name,
            code=code,
            number_prefix=prefix,
        )

    @classmethod
    def create_register(cls, category, owner=None):
        cls._sequence += 1
        sequence = cls._sequence
        if owner is None:
            owner = cls.manager
        return RegisterService(user=cls.manager).execute(
            name=f"{category.name} Register {sequence}",
            code=f"{category.code}_register_{sequence}",
            category=category,
            owner=owner,
        )

    @classmethod
    def create_register_entry(cls, **fields):
        cls._sequence += 1
        sequence = cls._sequence
        register = fields.pop("register", cls.register)
        created_by = fields.pop("created_by", cls.officer)
        return RegisterEntryService(user=created_by).execute(
            register=register,
            title=fields.pop("title", f"Entry {sequence}"),
            description=fields.pop("description", "A register entry."),
            owner=fields.pop("owner", created_by),
            **fields,
        )

    def categories_for(self, user):
        return list(category_queryset(user))

    def registers_for(self, user):
        return list(register_queryset(user))

    def make_confidential_entry(self, **fields):
        entry = self.create_register_entry(**fields)
        entry.confidentiality = "CONFIDENTIAL"
        entry.save(update_fields=["confidentiality"])
        return entry

    @staticmethod
    def entry_status(entry: RegisterEntry) -> str:
        return entry.approval_status

    def approve_through_workflow(self, entry: RegisterEntry) -> RegisterEntry:
        RegisterEntryService(user=self.officer).submit(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.SUBMITTED)
        RegisterEntryService(user=self.officer).start_review(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.PENDING_REVIEW)
        RegisterEntryService(user=self.officer).approve(instance=entry)
        entry.refresh_from_db()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.APPROVED)
        return entry
