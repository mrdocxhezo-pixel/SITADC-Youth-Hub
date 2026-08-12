"""Model behaviour, validation, and immutability tests."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.registers.constants import (
    ConfidentialityLevel,
    RegisterActivityAction,
    RegisterApprovalStatus,
    RegisterStatus,
    RetentionPolicy,
)
from apps.registers.models import (
    Register,
    RegisterActivity,
    RegisterAttachment,
    RegisterCategory,
    RegisterEntry,
    RegisterVersion,
)

from .base import RegistersTestCase


class RegisterCategoryModelTests(RegistersTestCase):
    def test_default_confidentiality_internal(self):
        self.assertEqual(
            self.category.default_confidentiality, ConfidentialityLevel.INTERNAL
        )

    def test_retention_years_required_for_fixed_term(self):
        category = RegisterCategory(
            name="Fixed",
            code="fixed",
            retention_policy=RetentionPolicy.FIXED_TERM,
            retention_years=None,
        )
        with self.assertRaises(ValidationError):
            category.full_clean()

    def test_duplicate_code_rejected(self):
        with self.assertRaises((IntegrityError, ValidationError)):
            self.create_category("Membership Duplicate", self.category.code, "MEM")


class RegisterModelTests(RegistersTestCase):
    def test_reference_number_assigned(self):
        self.assertTrue(self.register.reference_number.startswith("SITADC/REG/"))
        self.assertIn("MEM", self.register.reference_number)

    def test_default_status_draft(self):
        self.assertEqual(self.register.status, RegisterStatus.DRAFT)

    def test_archive_updates_status(self):
        self.register.archive(archived_by=self.manager)
        self.register.refresh_from_db()
        self.assertEqual(self.register.status, RegisterStatus.ARCHIVED)

    def test_entry_count_properties(self):
        self.create_register_entry()
        self.register.refresh_from_db()
        self.assertEqual(self.register.active_entry_count, 1)

    def test_retention_years_required_for_scheduled_disposal(self):
        register = Register(
            reference_number="REG-TEST-0001",
            name="Disposal",
            code="disposal",
            category=self.category,
            owner=self.manager,
            retention_policy=RetentionPolicy.SCHEDULED_DISPOSAL,
            retention_years=None,
        )
        with self.assertRaises(ValidationError):
            register.full_clean()


class RegisterEntryModelTests(RegistersTestCase):
    def test_reference_number_assigned(self):
        entry = self.create_register_entry()
        self.assertTrue(entry.reference_number.startswith("SITADC/REG/MEM/"))

    def test_unique_reference_number_enforced(self):
        entry = self.create_register_entry()
        duplicate = RegisterEntry(
            reference_number=entry.reference_number,
            register=self.register,
            title="Duplicate reference",
            owner=self.manager,
        )
        with self.assertRaises((IntegrityError, ValidationError)):
            duplicate.full_clean()
            duplicate.save()

    def test_default_approval_status_draft(self):
        entry = self.create_register_entry()
        self.assertEqual(entry.approval_status, RegisterApprovalStatus.DRAFT)

    def test_is_confidential_property(self):
        public = self.create_register_entry()
        self.assertFalse(public.is_confidential)
        entry = self.make_confidential_entry()
        self.assertTrue(entry.is_confidential)

    def test_invalid_reporting_period_rejected(self):
        entry = RegisterEntry(
            reference_number="ENT-TEST-0001",
            register=self.register,
            title="Bad period",
            owner=self.manager,
            reporting_period_start="2026-02-01",
            reporting_period_end="2026-01-01",
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()


class ImmutabilityTests(RegistersTestCase):
    def test_register_version_immutable(self):
        entry = self.create_register_entry()
        version = RegisterVersion.objects.create(
            entry=entry,
            version_number=2,
            author=self.manager,
            data_snapshot={"title": entry.title},
        )
        with self.assertRaises(ValidationError):
            version.delete()

    def test_register_activity_immutable(self):
        entry = self.create_register_entry()
        activity = RegisterActivity.objects.create(
            entry=entry,
            action=RegisterActivityAction.CREATED,
            actor=self.manager,
        )
        with self.assertRaises(ValidationError):
            activity.delete()

    def test_attachment_stores_metadata(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        entry = self.create_register_entry()
        attachment = RegisterAttachment.objects.create(
            entry=entry,
            file=SimpleUploadedFile("note.txt", b"content", content_type="text/plain"),
            original_filename="note.txt",
            content_type="text/plain",
            size=7,
            created_by=self.manager,
            updated_by=self.manager,
        )
        self.assertEqual(attachment.entry, entry)
        self.assertEqual(attachment.size, 7)
        self.assertIn("note.txt", str(attachment))
