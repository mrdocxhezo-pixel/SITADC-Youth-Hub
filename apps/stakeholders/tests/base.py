"""Shared deterministic fixtures for stakeholder tests."""

from __future__ import annotations

from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.accounts.constants import AccountStatus
from apps.rbac.authorization import clear_permission_cache
from apps.stakeholders.constants import (
    AgreementStatus,
    ConfidentialityLevel,
    ReferenceDataKind,
    StakeholderStatus,
)
from apps.stakeholders.models import (
    Stakeholder,
    StakeholderAgreement,
    StakeholderDocument,
    StakeholderReferenceData,
)
from apps.stakeholders.seed_loader import seed_stakeholder_reference_data
from apps.stakeholders.storage import private_stakeholder_storage

User = get_user_model()


class StakeholderTestCase(TestCase):
    """Seed taxonomies, numbering, users, and isolated private storage."""

    password = "TestPassword123!"

    @classmethod
    def setUpTestData(cls):
        seed_stakeholder_reference_data()
        cls.manager = cls.create_test_user("manager")
        cls.owner = cls.create_test_user("owner")
        cls.viewer = cls.create_test_user("viewer")
        cls.outsider = cls.create_test_user("outsider")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="partners.manage")
        )

    def setUp(self):
        super().setUp()
        self._stakeholder_sequence = 0
        self._agreement_sequence = 0
        self._document_sequence = 0
        self.private_media = TemporaryDirectory()
        self._original_storage_location = private_stakeholder_storage._location
        private_stakeholder_storage._location = self.private_media.name
        self._clear_storage_cache()
        self.addCleanup(self._restore_private_storage)

    def _clear_storage_cache(self):
        private_stakeholder_storage.__dict__.pop("base_location", None)
        private_stakeholder_storage.__dict__.pop("location", None)

    def _restore_private_storage(self):
        private_stakeholder_storage._location = self._original_storage_location
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
        queryset = StakeholderReferenceData.objects.filter(kind=kind, active=True)
        if code:
            queryset = queryset.filter(code=code)
        return queryset.order_by("order", "name").first()

    def create_stakeholder(self, **fields):
        self._stakeholder_sequence += 1
        sequence = self._stakeholder_sequence
        status = fields.pop("status", StakeholderStatus.PROSPECT)
        created_by = fields.pop("created_by", self.manager)
        defaults = {
            "reference_number": f"STK-TEST-{sequence:04d}",
            "legal_name": f"Stakeholder {sequence:04d}",
            "status": status,
            "confidentiality": ConfidentialityLevel.INTERNAL,
            "created_by": created_by,
            "updated_by": created_by,
        }
        if status == StakeholderStatus.ACTIVE:
            from django.utils import timezone

            defaults.update(verified_at=timezone.now(), verified_by=created_by)
        defaults.update(fields)
        return Stakeholder.objects.create(**defaults)

    def create_agreement(self, stakeholder=None, **fields):
        self._agreement_sequence += 1
        sequence = self._agreement_sequence
        stakeholder = stakeholder or self.create_stakeholder()
        defaults = {
            "stakeholder": stakeholder,
            "reference_number": f"SAG-TEST-{sequence:04d}",
            "agreement_type": self.taxonomy(ReferenceDataKind.AGREEMENT_TYPE, "mou"),
            "title": f"Agreement {sequence:04d}",
            "status": AgreementStatus.DRAFT,
            "created_by": self.manager,
            "updated_by": self.manager,
        }
        defaults.update(fields)
        return StakeholderAgreement.objects.create(**defaults)

    def create_document(self, stakeholder=None, **fields):
        self._document_sequence += 1
        sequence = self._document_sequence
        stakeholder = stakeholder or self.create_stakeholder()
        defaults = {
            "stakeholder": stakeholder,
            "document_key": f"document-{sequence}",
            "version_number": 1,
            "title": f"Document {sequence}",
            "document_type": "Evidence",
            "file": f"stakeholders/documents/document-{sequence}.pdf",
            "original_filename": f"document-{sequence}.pdf",
            "file_size": 20,
            "created_by": self.manager,
            "updated_by": self.manager,
        }
        defaults.update(fields)
        return StakeholderDocument.objects.create(**defaults)

    @staticmethod
    def pdf_upload(name="evidence.pdf"):
        return SimpleUploadedFile(
            name, b"%PDF-1.4\n% test document\n", "application/pdf"
        )
