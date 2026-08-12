"""Transactional service behaviour and enforcement tests."""

from datetime import date, timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

from apps.beneficiaries.constants import (
    BeneficiaryStatus,
    CaseNoteStatus,
    ConfidentialityLevel,
    ConsentStatus,
    ConsentType,
    GroupStatus,
    GuardianRole,
    HouseholdStatus,
    ReferenceDataKind,
    ReferralStatus,
    SafeguardingStatus,
)
from apps.beneficiaries.models import (
    BeneficiaryHousehold,
    ConsentRecord,
    GuardianRecord,
    HouseholdMember,
)
from apps.beneficiaries.services import (
    BeneficiaryService,
    CaseNoteService,
    ConsentService,
    GroupService,
    GuardianService,
    HouseholdService,
    ReferralService,
    SafeguardingService,
)

from .base import BeneficiaryTestCase


class BeneficiaryServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.caseworker = self.create_user("caseworker")
        self.grant_permissions(
            self.caseworker,
            "beneficiaries.create",
            "beneficiaries.update",
            "beneficiaries.view",
            "beneficiaries.archive",
            "beneficiaries.restore",
            "beneficiaries.manage_consent",
            "beneficiaries.manage_households",
            "beneficiaries.manage_groups",
            "beneficiaries.manage_guardians",
            "beneficiaries.manage_safeguarding",
            "beneficiaries.manage_case_notes",
            "beneficiaries.manage_referrals",
        )

    def create_service_beneficiary(self, **fields):
        fields.setdefault("first_name", "Service")
        fields.setdefault("last_name", "Client")
        fields.setdefault("date_of_birth", date.today() - timedelta(days=365 * 22))
        fields.setdefault("gender", self.taxonomy(ReferenceDataKind.GENDER, "female"))
        fields.setdefault("confidentiality", ConfidentialityLevel.INTERNAL)
        return BeneficiaryService(user=self.caseworker).create(**fields)

    def test_create_assigns_reference_and_initial_status(self):
        beneficiary = self.create_service_beneficiary(last_name="CreateCase")
        self.assertTrue(beneficiary.reference_number.startswith("BEN-"))
        self.assertEqual(beneficiary.status, BeneficiaryStatus.IDENTIFIED)
        self.assertEqual(beneficiary.created_by, self.caseworker)
        self.assertEqual(beneficiary.is_minor, False)

    def test_create_sets_minor_flag_for_children(self):
        beneficiary = self.create_service_beneficiary(
            last_name="MinorCase",
            date_of_birth=date.today() - timedelta(days=365 * 12),
        )
        self.assertTrue(beneficiary.is_minor)

    def test_create_rejects_missing_names(self):
        with self.assertRaises(ValidationError):
            BeneficiaryService(user=self.caseworker).create(last_name="OnlyLast")

    def test_create_rejects_possible_duplicates(self):
        dob = date.today() - timedelta(days=365 * 22)
        self.create_service_beneficiary(
            first_name="DupFirst", last_name="DupLast", date_of_birth=dob
        )
        with self.assertRaises(ValidationError):
            BeneficiaryService(user=self.caseworker).create(
                first_name="DupFirst", last_name="DupLast", date_of_birth=dob
            )

    def test_create_denies_without_permission(self):
        with self.assertRaises(PermissionDenied):
            BeneficiaryService(user=self.outsider).create(
                first_name="No", last_name="Access"
            )

    def test_update_changes_fields_and_tracks_history(self):
        beneficiary = self.create_service_beneficiary()
        updated = BeneficiaryService(user=self.caseworker).update(
            beneficiary, phone_primary="+260977000111"
        )
        updated.refresh_from_db()
        self.assertEqual(updated.phone_primary, "+260977000111")

    def test_change_status_blocks_invalid_transition(self):
        beneficiary = self.create_service_beneficiary()
        with self.assertRaises(ValidationError):
            BeneficiaryService(user=self.caseworker).change_status(
                beneficiary, BeneficiaryStatus.ACTIVE, reason="Skip the pipeline"
            )

    def test_change_status_requires_consent_for_adult(self):
        beneficiary = self.create_service_beneficiary()
        BeneficiaryService(user=self.caseworker).change_status(
            beneficiary, BeneficiaryStatus.REGISTERED, reason="Register"
        )
        with self.assertRaises(ValidationError) as ctx:
            BeneficiaryService(user=self.caseworker).change_status(
                beneficiary, BeneficiaryStatus.VERIFIED, reason="Verification"
            )
        self.assertIn("consent", " ".join(ctx.exception.messages).lower())

    def test_change_status_requires_consent_and_assent_for_minor(self):
        minor = self.create_service_beneficiary(
            last_name="MinorGate", date_of_birth=date.today() - timedelta(days=365 * 12)
        )
        BeneficiaryService(user=self.caseworker).change_status(
            minor, BeneficiaryStatus.REGISTERED, reason="Register"
        )
        with self.assertRaises(ValidationError) as ctx:
            BeneficiaryService(user=self.caseworker).change_status(
                minor, BeneficiaryStatus.VERIFIED, reason="Verification"
            )
        self.assertIn("minor", " ".join(ctx.exception.messages).lower())

    def test_change_status_verified_sets_verification_metadata(self):
        beneficiary = self.create_consenting_adult(
            created_by=self.caseworker, first_name="Vera", last_name="Verified"
        )
        BeneficiaryService(user=self.caseworker).change_status(
            beneficiary, BeneficiaryStatus.REGISTERED, reason="Register"
        )
        result = BeneficiaryService(user=self.caseworker).change_status(
            beneficiary, BeneficiaryStatus.VERIFIED, reason="Documents checked"
        )
        result.refresh_from_db()
        self.assertEqual(result.status, BeneficiaryStatus.VERIFIED)
        self.assertEqual(result.verification_date, timezone.localdate())
        self.assertEqual(result.verified_by, self.caseworker)

    def test_archive_then_restore_round_trip(self):
        beneficiary = self.create_service_beneficiary()
        archived = BeneficiaryService(user=self.caseworker).archive(
            beneficiary, reason="No longer in scope"
        )
        archived.refresh_from_db()
        self.assertTrue(archived.is_archived)
        self.assertEqual(archived.status, BeneficiaryStatus.ARCHIVED)
        restored = BeneficiaryService(user=self.caseworker).restore(
            archived, reason="Re-engaged"
        )
        restored.refresh_from_db()
        self.assertFalse(restored.is_archived)
        self.assertEqual(restored.status, BeneficiaryStatus.REGISTERED)

    def test_update_denied_outside_object_scope(self):
        beneficiary = self.create_beneficiary()
        with self.assertRaises(PermissionDenied):
            BeneficiaryService(user=self.caseworker).update(
                beneficiary, phone_primary="+260977000222"
            )


class ConsentServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.caseworker = self.create_user("consent-officer")
        self.grant_permissions(
            self.caseworker,
            "beneficiaries.create",
            "beneficiaries.update",
            "beneficiaries.view",
            "beneficiaries.manage_consent",
        )

    def test_minor_guardian_consent_requires_relationship(self):
        minor = BeneficiaryService(user=self.caseworker).create(
            first_name="Child",
            last_name="Consent",
            date_of_birth=date.today() - timedelta(days=365 * 12),
        )
        with self.assertRaises(ValidationError):
            ConsentService(user=self.caseworker).record(
                minor,
                consent_type=ConsentType.DATA_PROCESSING,
                provided_by="Guardian",
            )

    def test_assent_then_guardian_consent_enables_minor_status(self):
        minor = BeneficiaryService(user=self.caseworker).create(
            first_name="Child",
            last_name="Assent",
            date_of_birth=date.today() - timedelta(days=365 * 12),
        )
        ConsentService(user=self.caseworker).record(
            minor,
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Child Assent",
            is_assent=True,
            valid_to=timezone.localdate() + timedelta(days=365),
        )
        ConsentService(user=self.caseworker).record(
            minor,
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Guardian",
            relationship=GuardianRole.PARENT,
            valid_to=timezone.localdate() + timedelta(days=365),
        )
        minor.refresh_from_db()
        self.assertEqual(minor.consent_status, ConsentStatus.GRANTED)
        self.assertTrue(minor.assent_recorded)
        BeneficiaryService(user=self.caseworker).change_status(
            minor, BeneficiaryStatus.REGISTERED, reason="Register"
        )
        result = BeneficiaryService(user=self.caseworker).change_status(
            minor, BeneficiaryStatus.VERIFIED, reason="Verified with consent"
        )
        self.assertEqual(result.status, BeneficiaryStatus.VERIFIED)

    def test_adult_consent_enables_status(self):
        adult = BeneficiaryService(user=self.caseworker).create(
            first_name="Adult",
            last_name="Consents",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        ConsentService(user=self.caseworker).record(
            adult,
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Adult Consents",
            valid_to=timezone.localdate() + timedelta(days=365),
        )
        adult.refresh_from_db()
        self.assertEqual(adult.consent_status, ConsentStatus.GRANTED)
        self.assertEqual(
            adult.consent_expiry_date, timezone.localdate() + timedelta(days=365)
        )
        BeneficiaryService(user=self.caseworker).change_status(
            adult, BeneficiaryStatus.REGISTERED, reason="Register"
        )
        result = BeneficiaryService(user=self.caseworker).change_status(
            adult, BeneficiaryStatus.VERIFIED, reason="Adult verified"
        )
        self.assertEqual(result.status, BeneficiaryStatus.VERIFIED)

    def test_withdraw_requires_reason_and_updates_beneficiary(self):
        adult = BeneficiaryService(user=self.caseworker).create(
            first_name="Wendy",
            last_name="Withdraw",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        consent = ConsentService(user=self.caseworker).record(
            adult,
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Wendy Withdraw",
        )
        with self.assertRaises(ValidationError):
            ConsentService(user=self.caseworker).withdraw(consent, reason="")
        withdrawn = ConsentService(user=self.caseworker).withdraw(
            consent, reason="No longer wishes to participate"
        )
        withdrawn.refresh_from_db()
        adult.refresh_from_db()
        self.assertEqual(withdrawn.status, ConsentStatus.WITHDRAWN)
        self.assertEqual(adult.consent_status, ConsentStatus.WITHDRAWN)

    def test_withdraw_denied_without_permission(self):
        adult = self.create_beneficiary()
        consent = ConsentRecord.objects.create(
            beneficiary=adult,
            reference_number="CONS-SEC-0001",
            consent_type=ConsentType.DATA_PROCESSING,
            provided_by="Parent",
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(PermissionDenied):
            ConsentService(user=self.outsider).withdraw(consent, reason="Testing")


class GuardianServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.caseworker = self.create_user("guardian-officer")
        self.grant_permissions(
            self.caseworker,
            "beneficiaries.create",
            "beneficiaries.view",
            "beneficiaries.manage_guardians",
        )

    def test_first_guardian_becomes_primary(self):
        minor = BeneficiaryService(user=self.caseworker).create(
            first_name="Guardian",
            last_name="Ward",
            date_of_birth=date.today() - timedelta(days=365 * 10),
        )
        guardian = GuardianService(user=self.caseworker).create(
            minor,
            full_name="Parent One",
            relationship=GuardianRole.PARENT,
            phone_primary="+260977000333",
        )
        self.assertTrue(guardian.is_primary)

    def test_new_primary_demotes_existing_primary(self):
        minor = BeneficiaryService(user=self.caseworker).create(
            first_name="Guardian",
            last_name="Switch",
            date_of_birth=date.today() - timedelta(days=365 * 10),
        )
        first = GuardianService(user=self.caseworker).create(
            minor,
            full_name="Parent One",
            relationship=GuardianRole.PARENT,
            phone_primary="+260977000333",
        )
        second = GuardianService(user=self.caseworker).create(
            minor,
            full_name="Parent Two",
            relationship=GuardianRole.PARENT,
            phone_primary="+260977000444",
            is_primary=True,
        )
        first.refresh_from_db()
        self.assertFalse(first.is_primary)
        self.assertTrue(second.is_primary)

    def test_deactivate_clears_primary_flag(self):
        minor = self.create_beneficiary(
            created_by=self.caseworker, updated_by=self.caseworker
        )
        guardian = GuardianRecord.objects.create(
            beneficiary=minor,
            full_name="Parent One",
            relationship=GuardianRole.PARENT,
            is_primary=True,
            phone_primary="+260977000333",
            created_by=self.caseworker,
            updated_by=self.caseworker,
        )
        GuardianService(user=self.caseworker).deactivate(guardian)
        guardian.refresh_from_db()
        self.assertFalse(guardian.is_active)
        self.assertFalse(guardian.is_primary)


class HouseholdServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.officer = self.create_user("household-officer")
        self.grant_permissions(
            self.officer,
            "beneficiaries.create",
            "beneficiaries.view",
            "beneficiaries.manage_households",
        )

    def test_create_household_assigns_reference(self):
        household = HouseholdService(user=self.officer).create(
            household_name="Chanda Household",
            household_type=self.taxonomy(ReferenceDataKind.HOUSEHOLD_TYPE),
        )
        self.assertTrue(household.reference_number.startswith("HHL-"))
        self.assertEqual(household.status, HouseholdStatus.PROSPECTIVE)

    def test_add_and_remove_member_recalculates_count(self):
        household = HouseholdService(user=self.officer).create(
            household_name="Counted Household",
            household_type=self.taxonomy(ReferenceDataKind.HOUSEHOLD_TYPE),
        )
        member = BeneficiaryService(user=self.officer).create(
            first_name="Counted",
            last_name="Member",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        membership = HouseholdService(user=self.officer).add_member(
            household, member, is_head=True
        )
        household.refresh_from_db()
        self.assertEqual(household.number_of_members, 1)
        member.refresh_from_db()
        self.assertEqual(member.household, household)
        self.assertTrue(member.is_household_head)

        HouseholdService(user=self.officer).remove_member(membership)
        household.refresh_from_db()
        member.refresh_from_db()
        self.assertEqual(household.number_of_members, 0)
        self.assertIsNone(member.household)
        self.assertFalse(member.is_household_head)

    def test_remove_member_denied_without_permission(self):
        household = BeneficiaryHousehold.objects.create(
            reference_number="HHL-SEC-0001",
            household_name="Secure Household",
            created_by=self.manager,
            updated_by=self.manager,
        )
        member = self.create_beneficiary()
        membership = HouseholdMember.objects.create(
            household=household,
            beneficiary=member,
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(PermissionDenied):
            HouseholdService(user=self.outsider).remove_member(membership)


class GroupServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.officer = self.create_user("group-officer")
        self.grant_permissions(
            self.officer,
            "beneficiaries.create",
            "beneficiaries.view",
            "beneficiaries.manage_groups",
        )

    def test_create_group_assigns_reference(self):
        group = GroupService(user=self.officer).create(
            group_name="Chifundo Youth Group",
            group_type=self.taxonomy(ReferenceDataKind.GROUP_TYPE),
            status=GroupStatus.FORMING,
        )
        self.assertTrue(group.reference_number.startswith("GRP-"))
        self.assertEqual(group.status, GroupStatus.FORMING)

    def test_add_member_recalculates_count(self):
        group = GroupService(user=self.officer).create(
            group_name="Counting Group",
            group_type=self.taxonomy(ReferenceDataKind.GROUP_TYPE),
            status=GroupStatus.ACTIVE,
        )
        member = BeneficiaryService(user=self.officer).create(
            first_name="Group",
            last_name="Member",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        GroupService(user=self.officer).add_member(group, member)
        group.refresh_from_db()
        self.assertEqual(group.member_count, 1)

    def test_disbanded_group_rejects_members(self):
        group = GroupService(user=self.officer).create(
            group_name="Disbanded Group",
            group_type=self.taxonomy(ReferenceDataKind.GROUP_TYPE),
            status=GroupStatus.DISBANDED,
        )
        member = BeneficiaryService(user=self.officer).create(
            first_name="Late",
            last_name="Member",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        with self.assertRaises(ValidationError):
            GroupService(user=self.officer).add_member(group, member)

    def test_duplicate_membership_rejected(self):
        group = GroupService(user=self.officer).create(
            group_name="Unique Group",
            group_type=self.taxonomy(ReferenceDataKind.GROUP_TYPE),
            status=GroupStatus.ACTIVE,
        )
        member = BeneficiaryService(user=self.officer).create(
            first_name="Once",
            last_name="Only",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )
        GroupService(user=self.officer).add_member(group, member)
        with self.assertRaises(ValidationError):
            GroupService(user=self.officer).add_member(group, member)


class RelatedRecordServiceTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.caseworker = self.create_user("record-officer")
        self.grant_permissions(
            self.caseworker,
            "beneficiaries.create",
            "beneficiaries.update",
            "beneficiaries.view",
            "beneficiaries.manage_case_notes",
            "beneficiaries.manage_referrals",
            "beneficiaries.manage_safeguarding",
        )
        self.beneficiary = BeneficiaryService(user=self.caseworker).create(
            first_name="Related",
            last_name="Records",
            date_of_birth=date.today() - timedelta(days=365 * 22),
        )

    def test_case_note_created_finalized(self):
        note = CaseNoteService(user=self.caseworker).create(
            self.beneficiary,
            title="First home visit",
            note_type=self.taxonomy(ReferenceDataKind.CASE_NOTE_TYPE),
            content="Visited and supported the family.",
        )
        self.assertEqual(note.status, CaseNoteStatus.FINALIZED)

    def test_referral_create_and_status_transition(self):
        referral = ReferralService(user=self.caseworker).create(
            self.beneficiary,
            referral_type=self.taxonomy(ReferenceDataKind.REFERRAL_TYPE),
            referred_to="District Social Welfare",
            reason="Needs livelihood support",
        )
        self.assertTrue(referral.reference_number.startswith("RFL-"))
        updated = ReferralService(user=self.caseworker).change_status(
            referral, ReferralStatus.ACCEPTED, response_notes="Accepted by agency"
        )
        self.assertEqual(updated.status, ReferralStatus.ACCEPTED)

    def test_safeguarding_record_marks_beneficiary(self):
        record = SafeguardingService(user=self.caseworker).record(
            self.beneficiary,
            reported_by="Field Officer",
            description="Child reported at risk of exploitation.",
            risk_level=4,
        )
        self.beneficiary.refresh_from_db()
        self.assertTrue(self.beneficiary.safeguarding_concerns)

        resolved = SafeguardingService(user=self.caseworker).change_status(
            record, SafeguardingStatus.RESOLVED, notes="Case closed with family"
        )
        self.assertEqual(resolved.status, SafeguardingStatus.RESOLVED)
        with self.assertRaises(ValidationError):
            SafeguardingService(user=self.caseworker).change_status(
                record, SafeguardingStatus.OPEN, notes="Reopen attempt"
            )
