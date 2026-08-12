"""Model constraints, lifecycle guards, and validation tests."""

from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from apps.beneficiaries.constants import (
    BeneficiaryStatus,
    ConsentStatus,
    ConsentType,
    GuardianRole,
    HouseholdStatus,
    ReferenceDataKind,
)
from apps.beneficiaries.models import (
    BeneficiaryHousehold,
    BeneficiaryStatusHistory,
    ConsentRecord,
    GuardianRecord,
    HouseholdMember,
)
from apps.beneficiaries.validators import (
    is_minor,
    validate_date_range,
    validate_phone_number,
)

from .base import BeneficiaryTestCase


class BeneficiaryModelTests(BeneficiaryTestCase):
    def test_full_name_joins_available_parts(self):
        beneficiary = self.create_beneficiary(
            first_name="Alice", middle_name="Mary", last_name="Banda"
        )
        self.assertEqual(beneficiary.full_name, "Alice Mary Banda")
        self.assertIn(beneficiary.reference_number, str(beneficiary))

    def test_minor_flag_computed_from_date_of_birth(self):
        today = date.today()
        self.assertEqual(is_minor(date(today.year - 17, today.month, today.day)), True)
        self.assertEqual(is_minor(date(today.year - 18, today.month, today.day)), False)

    def test_clean_rejects_future_registration(self):
        beneficiary = self.create_beneficiary(
            registration_date=timezone.localdate() + timedelta(days=1)
        )
        with self.assertRaises(ValidationError):
            beneficiary.full_clean()

    def test_clean_rejects_verification_before_registration(self):
        beneficiary = self.create_beneficiary()
        beneficiary.verification_date = beneficiary.registration_date - timedelta(
            days=1
        )
        with self.assertRaises(ValidationError):
            beneficiary.full_clean()

    def test_clean_rejects_consenting_minor_without_assent(self):
        minor = self.create_minor(consent_status=ConsentStatus.GRANTED)
        with self.assertRaises(ValidationError):
            minor.full_clean()

    def test_clean_accepts_consenting_minor_with_assent(self):
        minor = self.create_minor(consent_status=ConsentStatus.GRANTED)
        minor.assent_recorded = True
        minor.full_clean()

    def test_clean_rejects_wrong_reference_data_kind(self):
        beneficiary = self.create_beneficiary(
            gender=self.taxonomy(ReferenceDataKind.MARITAL_STATUS)
        )
        with self.assertRaises(ValidationError):
            beneficiary.full_clean()

    def test_verified_status_requires_verification_metadata(self):
        beneficiary = self.create_beneficiary(status=BeneficiaryStatus.VERIFIED)
        with self.assertRaises(ValidationError):
            beneficiary.full_clean()


class ImmutableHistoryTests(BeneficiaryTestCase):
    def test_status_history_rows_are_immutable(self):
        beneficiary = self.create_beneficiary()
        history = BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=BeneficiaryStatus.IDENTIFIED,
            to_status=BeneficiaryStatus.REGISTERED,
            changed_by=self.manager,
            reason="Transition",
            created_by=self.manager,
            updated_by=self.manager,
        )
        history.reason = "edited"
        with self.assertRaises(ValidationError):
            history.save()
        with self.assertRaises(ValidationError):
            history.delete()

    def test_consent_record_allows_only_whitelisted_updates(self):
        beneficiary = self.create_beneficiary()
        consent = ConsentRecord.objects.create(
            beneficiary=beneficiary,
            reference_number="CONS-TEST-0001",
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Parent",
            created_by=self.manager,
            updated_by=self.manager,
        )
        consent.status = ConsentStatus.WITHDRAWN
        consent.withdrawal_reason = "Changed mind"
        consent.updated_by = self.manager
        consent.save(update_fields=["status", "withdrawal_reason", "updated_by"])
        consent.refresh_from_db()
        self.assertEqual(consent.status, ConsentStatus.WITHDRAWN)
        consent.consent_type = ConsentType.COMMUNICATION
        with self.assertRaises(ValidationError):
            consent.save(update_fields=["consent_type"])

    def test_consent_clean_rejects_reversed_dates(self):
        beneficiary = self.create_beneficiary()
        consent = ConsentRecord(
            beneficiary=beneficiary,
            reference_number="CONS-TEST-0002",
            consent_type=ConsentType.SERVICE_PROVISION,
            provided_by="Parent",
            valid_from=date(2026, 8, 2),
            valid_to=date(2026, 8, 1),
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(ValidationError):
            consent.full_clean()


class HouseholdModelTests(BeneficiaryTestCase):
    def test_recalculate_member_count_tracks_active_members(self):
        household = BeneficiaryHousehold.objects.create(
            reference_number="HHL-TEST-0001",
            household_name="Banda Household",
            household_type=self.taxonomy(ReferenceDataKind.HOUSEHOLD_TYPE),
            status=HouseholdStatus.ACTIVE,
            created_by=self.manager,
            updated_by=self.manager,
        )
        member = self.create_beneficiary()
        HouseholdMember.objects.create(
            household=household,
            beneficiary=member,
            created_by=self.manager,
            updated_by=self.manager,
        )
        household.recalculate_member_count()
        household.refresh_from_db()
        self.assertEqual(household.number_of_members, 1)

    def test_member_household_beneficiary_is_unique(self):
        household = BeneficiaryHousehold.objects.create(
            reference_number="HHL-TEST-0002",
            household_name="Unique Household",
            created_by=self.manager,
            updated_by=self.manager,
        )
        member = self.create_beneficiary()
        HouseholdMember.objects.create(
            household=household,
            beneficiary=member,
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(IntegrityError):
            HouseholdMember.objects.create(
                household=household,
                beneficiary=member,
                created_by=self.manager,
                updated_by=self.manager,
            )

    def test_only_one_active_primary_guardian_per_beneficiary(self):
        beneficiary = self.create_beneficiary()
        GuardianRecord.objects.create(
            beneficiary=beneficiary,
            full_name="First Parent",
            is_primary=True,
            relationship=GuardianRole.PARENT,
            phone_primary="+260977000000",
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(IntegrityError):
            GuardianRecord.objects.create(
                beneficiary=beneficiary,
                full_name="Second Parent",
                is_primary=True,
                relationship=GuardianRole.PARENT,
                phone_primary="+260977000001",
                created_by=self.manager,
                updated_by=self.manager,
            )


class ValidatorTests(BeneficiaryTestCase):
    def test_phone_validator_rejects_unformatted_numbers(self):
        with self.assertRaises(ValidationError):
            validate_phone_number("1234")

    def test_date_range_accepts_null_end(self):
        validate_date_range(date(2026, 1, 1), None, end_field="valid_to")

    def test_date_range_rejects_reversed_dates(self):
        with self.assertRaises(ValidationError):
            validate_date_range(
                date(2026, 8, 2), date(2026, 8, 1), end_field="valid_to"
            )


class SoftDeleteModelTests(BeneficiaryTestCase):
    def test_beneficiary_supports_soft_delete_flag(self):
        beneficiary = self.create_beneficiary()
        beneficiary.is_deleted = True
        beneficiary.deleted_by = self.manager
        beneficiary.save(update_fields=["is_deleted", "deleted_by"])
        beneficiary.refresh_from_db()
        self.assertTrue(beneficiary.is_deleted)
