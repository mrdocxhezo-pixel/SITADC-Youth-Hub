"""
Service tests for the membership management business logic.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.memberships.constants import (
    ApplicationStatus,
    CardStatus,
    PaymentMethod,
    PaymentStatus,
)
from apps.memberships.exceptions import (
    ApplicationValidationError,
    CardError,
    PaymentError,
    RenewalError,
)
from apps.memberships.models import (
    AlumniRecord,
    MembershipPayment,
    MembershipStatus,
    MembershipTermination,
)
from apps.memberships.services import (
    MemberLeaveService,
    MemberParticipationService,
    MemberRecognitionService,
    MembershipAnalyticsService,
    MembershipApplicationService,
    MembershipCardService,
    MembershipExitService,
    MembershipPaymentService,
    MembershipRenewalService,
    MembershipStatusService,
    MembershipTransferService,
    MembershipUpgradeService,
)
from apps.memberships.tests.base import MembershipTestCase

User = get_user_model()


class MembershipApplicationServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.app_service = MembershipApplicationService(user=self.admin)

    def test_submit_application(self):
        application = self.app_service.submit_application(
            applicant=self.user,
            first_name="Member",
            last_name="User",
            email="member@example.com",
            category=self._category("ordinary"),
            membership_type=self._type("individual"),
            level=self._level("national"),
        )
        self.assertTrue(application.reference_number.startswith("APL-"))
        self.assertEqual(application.status, ApplicationStatus.SUBMITTED)
        self.assertIsNotNone(application.submitted_at)

    def test_submit_requires_declaration(self):
        with self.assertRaises(ApplicationValidationError):
            self.app_service.submit_application(
                applicant=self.user,
                first_name="Member",
                last_name="User",
                email="member@example.com",
                category=self._category("ordinary"),
                membership_type=self._type("individual"),
                level=self._level("national"),
                declaration_agreed=False,
            )

    def test_duplicate_pending_application_rejected(self):
        self.app_service.submit_application(
            applicant=self.user,
            first_name="Member",
            last_name="User",
            email="member@example.com",
            category=self._category("ordinary"),
            membership_type=self._type("individual"),
            level=self._level("national"),
        )
        with self.assertRaises(ApplicationValidationError):
            self.app_service.submit_application(
                applicant=self.user,
                first_name="Member",
                last_name="User",
                email="member@example.com",
                category=self._category("ordinary"),
                membership_type=self._type("individual"),
                level=self._level("national"),
            )

    def test_approve_application_registers_member(self):
        application = self.app_service.submit_application(
            applicant=self.user,
            first_name="Member",
            last_name="User",
            email="member@example.com",
            category=self._category("ordinary"),
            membership_type=self._type("individual"),
            level=self._level("national"),
        )
        self.app_service.start_review(application)
        member = self.app_service.approve_application(application)
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.APPROVED)
        self.assertIsNotNone(member.membership_id)
        self.assertTrue(member.membership_id.startswith("MEM-"))
        self.assertEqual(member.user, self.user)
        self.assertTrue(member.is_active)

    def test_approve_requires_under_review(self):
        application = self.app_service.submit_application(
            applicant=self.user,
            first_name="Member",
            last_name="User",
            email="member@example.com",
            category=self._category("ordinary"),
            membership_type=self._type("individual"),
            level=self._level("national"),
        )
        with self.assertRaises(ApplicationValidationError):
            self.app_service.approve_application(application)

    def test_reject_application(self):
        application = self.app_service.submit_application(
            applicant=self.user,
            first_name="Member",
            last_name="User",
            email="member@example.com",
            category=self._category("ordinary"),
            membership_type=self._type("individual"),
            level=self._level("national"),
        )
        self.app_service.start_review(application)
        self.app_service.reject_application(application, decision_notes="Not eligible")
        application.refresh_from_db()
        self.assertEqual(application.status, ApplicationStatus.REJECTED)
        self.assertEqual(application.decision_notes, "Not eligible")

    def _category(self, code):
        from apps.memberships.models import MembershipCategory

        return MembershipCategory.objects.get(code=code)

    def _type(self, code):
        from apps.memberships.models import MembershipType

        return MembershipType.objects.get(code=code)

    def _level(self, code):
        from apps.memberships.models import MembershipLevel

        return MembershipLevel.objects.get(code=code)


class MembershipStatusServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()
        self.status_service = MembershipStatusService(user=self.admin)

    def test_suspend_and_lift(self):
        suspension = self.status_service.suspend(
            self.member, reason="Misconduct", effective_date=timezone.now().date()
        )
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_suspended)
        self.status_service.lift_suspension(suspension)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_active)

    def test_terminate(self):
        self.status_service.terminate(
            self.member, reason="RESIGNED", reason_detail="Personal reasons"
        )
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_terminated)
        self.assertEqual(
            MembershipTermination.objects.filter(member=self.member).count(), 1
        )

    def test_archive_and_restore(self):
        self.status_service.archive(self.member, reason="Records cleanup")
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_archived)
        self.status_service.restore(self.member)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_archived)
        self.assertTrue(self.member.is_active)

    def test_status_history_recorded(self):
        self.status_service.suspend(
            self.member, reason="Test", effective_date=timezone.now().date()
        )
        self.assertGreaterEqual(self.member.status_history.count(), 1)

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000001",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            created_by=self.admin,
        )


class MembershipPaymentServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()

    def test_record_payment(self):
        service = MembershipPaymentService(user=self.admin)
        payment = service.record_payment(
            member=self.member,
            amount=100,
            payment_method=PaymentMethod.MOBILE_MONEY,
        )
        self.assertTrue(payment.receipt_number.startswith("RCT-"))
        self.assertEqual(payment.status, PaymentStatus.PAID)

    def test_record_payment_rejects_zero(self):
        service = MembershipPaymentService(user=self.admin)
        with self.assertRaises(PaymentError):
            service.record_payment(
                member=self.member,
                amount=0,
                payment_method=PaymentMethod.CASH,
            )

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000002",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            created_by=self.admin,
        )


class MembershipCardServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()
        self.card_service = MembershipCardService(user=self.admin)

    def test_issue_card(self):
        card = self.card_service.issue_card(self.member)
        self.assertTrue(card.card_number.startswith("CRD-"))
        self.assertEqual(len(card.verification_code), 16)
        self.assertEqual(card.status, CardStatus.ACTIVE)

    def test_duplicate_card_rejected(self):
        self.card_service.issue_card(self.member)
        with self.assertRaises(CardError):
            self.card_service.issue_card(self.member)

    def test_verify_card(self):
        card = self.card_service.issue_card(self.member)
        verified = self.card_service.verify_card(card.verification_code)
        self.assertEqual(verified.id, card.id)

    def test_revoke_card(self):
        card = self.card_service.issue_card(self.member)
        self.card_service.revoke_card(card, reason="Lost card")
        card.refresh_from_db()
        self.assertEqual(card.status, CardStatus.REVOKED)

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000003",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            created_by=self.admin,
        )


class MembershipRenewalServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()
        self.renewal_service = MembershipRenewalService(user=self.admin)

    def test_request_and_approve_renewal(self):
        renewal = self.renewal_service.request_renewal(self.member)
        # mark payment as paid so approval passes
        MembershipPayment.objects.create(
            member=self.member,
            receipt_number="RCT-SITADC-2026-000001",
            amount=100,
            payment_method=PaymentMethod.CASH,
            payment_date=timezone.now().date(),
            status=PaymentStatus.PAID,
            created_by=self.admin,
        )
        renewal.payment_status = PaymentStatus.PAID
        renewal.save()
        self.renewal_service.approve_renewal(renewal, approve=True)
        renewal.refresh_from_db()
        self.member.refresh_from_db()
        self.assertEqual(renewal.status, "APPROVED")
        self.assertIsNotNone(self.member.expiry_date)

    def test_approve_requires_payment(self):
        renewal = self.renewal_service.request_renewal(self.member)
        with self.assertRaises(RenewalError):
            self.renewal_service.approve_renewal(renewal, approve=True)

    def test_renewal_rejected_when_not_paid_and_approve_false(self):
        renewal = self.renewal_service.request_renewal(self.member)
        self.renewal_service.approve_renewal(renewal, approve=False)
        renewal.refresh_from_db()
        self.assertEqual(renewal.status, "REJECTED")

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000004",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            expiry_date=timezone.now().date() + timezone.timedelta(days=30),
            created_by=self.admin,
        )


class MembershipTransferServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()
        self.transfer_service = MembershipTransferService(user=self.admin)

    def test_request_and_approve_transfer(self):
        transfer = self.transfer_service.request_transfer(
            self.member, to_province="Copperbelt", to_district="Kitwe"
        )
        self.assertEqual(transfer.status, "PENDING")
        self.transfer_service.approve_transfer(transfer, approve=True)
        self.member.refresh_from_db()
        self.assertEqual(self.member.district, "Kitwe")
        self.assertEqual(self.member.province, "Copperbelt")

    def test_upgrade_service(self):
        from apps.memberships.models import MembershipCategory

        upgrade_service = MembershipUpgradeService(user=self.admin)
        upgrade = upgrade_service.request_upgrade(
            self.member, to_category=MembershipCategory.objects.get(code="founding")
        )
        self.assertEqual(upgrade.status, "PENDING")
        upgrade_service.approve_upgrade(upgrade, approve=True)
        self.member.refresh_from_db()
        self.assertEqual(self.member.category.code, "founding")

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000005",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            province="Lusaka",
            district="Lusaka",
            created_by=self.admin,
        )


class MembershipExitServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()
        self.exit_service = MembershipExitService(user=self.admin)

    def test_initiate_and_complete_exit_with_alumni(self):
        exit_rec = self.exit_service.initiate_exit(
            self.member,
            exit_type="RESIGNATION",
            effective_date=timezone.now().date(),
            transition_to_alumni=True,
        )
        self.exit_service.complete_exit(exit_rec)
        exit_rec.refresh_from_db()
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_terminated)
        self.assertEqual(AlumniRecord.objects.filter(member=self.member).count(), 1)

    def test_complete_exit_without_alumni(self):
        exit_rec = self.exit_service.initiate_exit(
            self.member,
            exit_type="RESIGNATION",
            effective_date=timezone.now().date(),
            transition_to_alumni=False,
        )
        self.exit_service.complete_exit(exit_rec)
        self.member.refresh_from_db()
        self.assertTrue(self.member.is_terminated)
        self.assertEqual(AlumniRecord.objects.filter(member=self.member).count(), 0)

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000006",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            created_by=self.admin,
        )


class MemberEngagementServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.member = self._register_member()

    def test_participation_service(self):
        service = MemberParticipationService(user=self.admin)
        participation = service.record_participation(
            member=self.member,
            participation_type="PROGRAM",
            activity_name="Youth Leadership Program",
            start_date="2026-02-01",
        )
        self.assertEqual(participation.activity_name, "Youth Leadership Program")

    def test_recognition_service(self):
        service = MemberRecognitionService(user=self.admin)
        recognition = service.record_recognition(
            member=self.member,
            recognition_type="OUTSTANDING_CONTRIBUTION",
            title="Volunteer of the Year",
        )
        self.assertEqual(recognition.title, "Volunteer of the Year")

    def test_leave_service(self):
        service = MemberLeaveService(user=self.admin)
        leave = service.apply_leave(
            member=self.member,
            leave_type="ANNUAL",
            start_date="2026-03-01",
            end_date="2026-03-05",
            reason="Vacation",
        )
        self.assertEqual(leave.status, "SUBMITTED")
        service.approve_leave(leave, approve=True)
        leave.refresh_from_db()
        self.assertEqual(leave.status, "APPROVED")

    def _register_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000007",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
            created_by=self.admin,
        )


class MembershipAnalyticsServiceTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.service = MembershipAnalyticsService(user=self.admin)

    def test_dashboard_summary_shape(self):
        summary = self.service.dashboard_summary()
        self.assertIn("total_members", summary)
        self.assertIn("active_members", summary)
        self.assertIn("pending_applications", summary)
        self.assertIn("renewals_due", summary)
        self.assertEqual(summary["total_members"], 0)

    def test_fee_collection_summary(self):
        summary = self.service.fee_collection_summary()
        self.assertIn("total_collected", summary)
        self.assertEqual(int(summary["total_collected"]), 0)
