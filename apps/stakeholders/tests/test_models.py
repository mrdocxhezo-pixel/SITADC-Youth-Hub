"""Model constraints and immutability tests for stakeholders."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.stakeholders.constants import (
    DueDiligenceStatus,
    ReferenceDataKind,
    StakeholderStatus,
)
from apps.stakeholders.models import (
    Stakeholder,
    StakeholderAgreementVersion,
    StakeholderContact,
    StakeholderDueDiligence,
    StakeholderDuplicateReview,
    StakeholderReferenceData,
    StakeholderStatusHistory,
)

from .base import StakeholderTestCase


class TaxonomyConstraintTests(StakeholderTestCase):
    def test_kind_and_code_are_unique_together(self):
        existing = self.taxonomy(ReferenceDataKind.CATEGORY, "donor")
        with self.assertRaises(IntegrityError), transaction.atomic():
            StakeholderReferenceData.objects.create(
                kind=existing.kind,
                code=existing.code,
                name="Duplicate donor",
            )

    def test_profile_rejects_reference_data_of_wrong_kind(self):
        stakeholder = self.create_stakeholder(
            relationship_type=self.taxonomy(ReferenceDataKind.CATEGORY, "donor")
        )
        with self.assertRaises(ValidationError) as context:
            stakeholder.full_clean()
        self.assertIn("relationship_type", context.exception.message_dict)


class StakeholderProfileValidationTests(StakeholderTestCase):
    def test_relationship_end_cannot_precede_start(self):
        stakeholder = Stakeholder(
            reference_number="STK-DATES",
            legal_name="Invalid Dates",
            relationship_start_date=date(2026, 6, 2),
            relationship_end_date=date(2026, 6, 1),
        )
        with self.assertRaises(ValidationError) as context:
            stakeholder.full_clean()
        self.assertIn("relationship_end_date", context.exception.message_dict)

    def test_established_date_cannot_be_future(self):
        stakeholder = Stakeholder(
            reference_number="STK-FUTURE",
            legal_name="Future Organization",
            date_established=timezone.localdate() + timedelta(days=1),
        )
        with self.assertRaises(ValidationError) as context:
            stakeholder.full_clean()
        self.assertIn("date_established", context.exception.message_dict)

    def test_active_profile_requires_verification_metadata(self):
        stakeholder = Stakeholder(
            reference_number="STK-ACTIVE",
            legal_name="Unverified Active",
            status=StakeholderStatus.ACTIVE,
        )
        with self.assertRaises(ValidationError) as context:
            stakeholder.full_clean()
        self.assertIn("status", context.exception.message_dict)


class ContactConstraintTests(StakeholderTestCase):
    def test_contact_requires_a_channel(self):
        contact = StakeholderContact(
            stakeholder=self.create_stakeholder(), full_name="No Channel"
        )
        with self.assertRaises(ValidationError):
            contact.full_clean()

    def test_only_one_active_primary_contact_is_allowed(self):
        stakeholder = self.create_stakeholder()
        StakeholderContact.objects.create(
            stakeholder=stakeholder,
            full_name="Primary One",
            email="one@example.com",
            is_primary=True,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            StakeholderContact.objects.create(
                stakeholder=stakeholder,
                full_name="Primary Two",
                email="two@example.com",
                is_primary=True,
            )


class AgreementModelTests(StakeholderTestCase):
    def test_agreement_rejects_invalid_dates_and_negative_values(self):
        invalid_dates = self.create_agreement(
            effective_date=date(2026, 8, 2),
            expiry_date=date(2026, 8, 1),
        )
        with self.assertRaises(ValidationError) as context:
            invalid_dates.full_clean()
        self.assertIn("expiry_date", context.exception.message_dict)

        negative_values = self.create_agreement(financial_value=Decimal("-1.00"))
        with self.assertRaises(ValidationError) as context:
            negative_values.full_clean()
        self.assertIn("financial_value", context.exception.message_dict)

        negative_in_kind = self.create_agreement(in_kind_value=Decimal("-2.00"))
        with self.assertRaises(ValidationError) as context:
            negative_in_kind.full_clean()
        self.assertIn("in_kind_value", context.exception.message_dict)

    def test_agreement_version_is_immutable_by_instance_and_queryset(self):
        version = StakeholderAgreementVersion.objects.create(
            agreement=self.create_agreement(),
            version_number=1,
            title="Version one",
        )
        version.title = "Changed"
        with self.assertRaises(ValidationError):
            version.save()
        with self.assertRaises(ValidationError):
            StakeholderAgreementVersion.objects.filter(pk=version.pk).update(
                title="Changed"
            )
        with self.assertRaises(ValidationError):
            version.delete()


class HistoricalAndDuplicateConstraintTests(StakeholderTestCase):
    def test_status_history_is_append_only(self):
        history = StakeholderStatusHistory.objects.create(
            stakeholder=self.create_stakeholder(),
            from_status=StakeholderStatus.PROSPECT,
            to_status=StakeholderStatus.IDENTIFIED,
            changed_by=self.manager,
            reason="Qualified",
        )
        history.reason = "Rewritten"
        with self.assertRaises(ValidationError):
            history.save()
        with self.assertRaises(ValidationError):
            StakeholderStatusHistory.objects.filter(pk=history.pk).delete()

    def test_duplicate_review_rejects_self_reference(self):
        stakeholder = self.create_stakeholder()
        duplicate = StakeholderDuplicateReview(
            stakeholder=stakeholder,
            possible_duplicate=stakeholder,
            match_score=Decimal("100.00"),
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            StakeholderDuplicateReview.objects.create(
                stakeholder=stakeholder,
                possible_duplicate=stakeholder,
                match_score=Decimal("100.00"),
            )

    def test_due_diligence_requires_ordered_dates_and_completion_actor(self):
        invalid_dates = StakeholderDueDiligence(
            stakeholder=self.create_stakeholder(),
            reference_number="SDD-DATES",
            review_date=date(2026, 8, 2),
            expiry_date=date(2026, 8, 1),
        )
        with self.assertRaises(ValidationError) as context:
            invalid_dates.full_clean()
        self.assertIn("expiry_date", context.exception.message_dict)

        missing_actor = StakeholderDueDiligence(
            stakeholder=self.create_stakeholder(),
            reference_number="SDD-ACTOR",
            review_date=date(2026, 8, 1),
            expiry_date=date(2027, 8, 1),
            status=DueDiligenceStatus.PASSED,
        )
        with self.assertRaises(ValidationError) as context:
            missing_actor.full_clean()
        self.assertIn("status", context.exception.message_dict)


class DocumentModelTests(StakeholderTestCase):
    def test_private_document_has_no_public_url(self):
        document = self.create_document()
        with self.assertRaisesRegex(ValueError, "do not expose public URLs"):
            str(document.file.url)

    def test_document_cannot_be_deleted(self):
        document = self.create_document()
        with self.assertRaises(ValidationError) as context:
            document.delete()
        self.assertEqual(
            context.exception.error_list[0].code, "protected_stakeholder_document"
        )


class ModelTestStyleTests(TestCase):
    """Keep this suite explicitly based on Django's unittest integration."""

    def test_suite_uses_django_test_case(self):
        self.assertTrue(issubclass(StakeholderTestCase, TestCase))
