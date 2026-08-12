"""Shared deterministic fixtures for MEAL module tests."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.meal.models import (
    Complaint,
    Feedback,
    Indicator,
    MEALReferenceData,
    MEALReport,
)
from apps.meal.seed_loader import seed_meal_reference_data
from apps.meal.storage import private_meal_storage
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class MEALTestCase(TestCase):
    """Seed MEAL taxonomies, numbering, users, and isolated private storage."""

    password = "TestPassword123!"

    @classmethod
    def setUpTestData(cls):
        seed_meal_reference_data()
        cls.manager = cls.create_test_user("manager")
        cls.officer = cls.create_test_user("officer")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")
        cls.manager.user_permissions.add(Permission.objects.get(codename="meal.manage"))
        cls.officer.user_permissions.add(
            Permission.objects.get(codename="meal.create"),
            Permission.objects.get(codename="meal.update"),
            Permission.objects.get(codename="meal.view"),
        )

    def setUp(self):
        super().setUp()
        self._sequence = 0
        self.private_media = TemporaryDirectory()
        self._original_storage_location = private_meal_storage._location
        private_meal_storage._location = self.private_media.name
        self._clear_storage_cache()
        self.addCleanup(self._restore_private_storage)

    def _clear_storage_cache(self):
        private_meal_storage.__dict__.pop("base_location", None)
        private_meal_storage.__dict__.pop("location", None)

    def _restore_private_storage(self):
        private_meal_storage._location = self._original_storage_location
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

    def taxonomy(self, kind: str, code: str | None = None):
        queryset = MEALReferenceData.objects.filter(kind=kind, active=True)
        if code:
            queryset = queryset.filter(code=code)
        return queryset.order_by("order", "name").first()

    def create_indicator(self, **fields):
        self._sequence += 1
        sequence = self._sequence
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"IND-TEST-{sequence:04d}",
            "code": f"ind_{sequence:04d}",
            "title": f"Indicator {sequence:04d}",
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return Indicator.objects.create(**defaults)

    def create_complaint(self, **fields):
        self._sequence += 1
        sequence = self._sequence
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"CMP-TEST-{sequence:04d}",
            "description": f"Complaint {sequence:04d}",
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return Complaint.objects.create(**defaults)

    def create_feedback(self, **fields):
        self._sequence += 1
        sequence = self._sequence
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"FDB-TEST-{sequence:04d}",
            "description": f"Feedback {sequence:04d}",
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return Feedback.objects.create(**defaults)

    def create_report(self, **fields):
        self._sequence += 1
        sequence = self._sequence
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"MRL-TEST-{sequence:04d}",
            "title": f"MEAL Report {sequence:04d}",
            "report_type": "RESULTS_FRAMEWORK",
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        return MEALReport.objects.create(**defaults)
