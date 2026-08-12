"""Shared deterministic fixtures for beneficiary tests."""

from __future__ import annotations

from datetime import date, timedelta
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.utils import timezone

from apps.accounts.constants import AccountStatus
from apps.beneficiaries.constants import (
    BeneficiaryStatus,
    ConfidentialityLevel,
    ConsentStatus,
)
from apps.beneficiaries.models import Beneficiary, BeneficiaryReferenceData
from apps.beneficiaries.seed_loader import seed_beneficiary_reference_data
from apps.beneficiaries.storage import private_beneficiary_storage
from apps.rbac.authorization import clear_permission_cache

User = get_user_model()


class BeneficiaryTestCase(TestCase):
    """Seed taxonomies, numbering, users, and isolated private storage."""

    password = "TestPassword123!"

    @classmethod
    def setUpTestData(cls):
        seed_beneficiary_reference_data()
        cls.manager = cls.create_test_user("manager")
        cls.officer = cls.create_test_user("officer")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="beneficiaries.manage")
        )
        cls.officer.user_permissions.add(
            Permission.objects.get(codename="beneficiaries.create"),
            Permission.objects.get(codename="beneficiaries.update"),
            Permission.objects.get(codename="beneficiaries.view"),
        )

    def setUp(self):
        super().setUp()
        self._beneficiary_sequence = 0
        self._household_sequence = 0
        self._group_sequence = 0
        self.private_media = TemporaryDirectory()
        self._original_storage_location = private_beneficiary_storage._location
        private_beneficiary_storage._location = self.private_media.name
        self._clear_storage_cache()
        self.addCleanup(self._restore_private_storage)

    def _clear_storage_cache(self):
        private_beneficiary_storage.__dict__.pop("base_location", None)
        private_beneficiary_storage.__dict__.pop("location", None)

    def _restore_private_storage(self):
        private_beneficiary_storage._location = self._original_storage_location
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
        queryset = BeneficiaryReferenceData.objects.filter(kind=kind, active=True)
        if code:
            queryset = queryset.filter(code=code)
        return queryset.order_by("order", "name").first()

    def create_beneficiary(self, **fields):
        self._beneficiary_sequence += 1
        sequence = self._beneficiary_sequence
        status = fields.pop("status", BeneficiaryStatus.IDENTIFIED)
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"BEN-TEST-{sequence:04d}",
            "first_name": f"Test{sequence:04d}",
            "last_name": f"Beneficiary{sequence:04d}",
            "status": status,
            "confidentiality": ConfidentialityLevel.INTERNAL,
            "created_by": created_by,
            "updated_by": created_by,
        }
        defaults.update(fields)
        beneficiary = Beneficiary.objects.create(**defaults)
        if "date_of_birth" in defaults:
            from apps.beneficiaries.validators import is_minor

            beneficiary.is_minor = is_minor(defaults["date_of_birth"])
            beneficiary.save(update_fields=["is_minor"])
        return beneficiary

    def create_minor(self, **fields):
        fields.setdefault("date_of_birth", date.today() - timedelta(days=365 * 12))
        return self.create_beneficiary(**fields)

    def create_consenting_adult(self, **fields):
        fields.setdefault("date_of_birth", date.today() - timedelta(days=365 * 22))
        beneficiary = self.create_beneficiary(**fields)
        beneficiary.consent_status = ConsentStatus.GRANTED
        beneficiary.consent_recorded_at = timezone.now()
        beneficiary.consent_expiry_date = timezone.localdate() + timedelta(days=365)
        beneficiary.save(
            update_fields=[
                "consent_status",
                "consent_recorded_at",
                "consent_expiry_date",
            ]
        )
        return beneficiary
