"""
Transactional business services for the membership management module.

Every state-changing membership operation flows through these services so
that invariants are enforced transactionally:

* reference numbers are issued through the centralized numbering service,
* status transitions are validated,
* immutable status-history and audit records are appended on every change,
* permissions are enforced server-side before any mutation.
"""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import ReferenceNumberService

from .constants import (
    AdjustmentStatus,
    ApplicationStatus,
    CardStatus,
    ExitStatus,
    LeaveStatus,
    MembershipAuditAction,
    ParticipationStatus,
    PaymentStatus,
    RenewalStatus,
    TransferStatus,
    UpgradeStatus,
)
from .exceptions import (
    ApplicationValidationError,
    CardError,
    PaymentError,
    RegistrationError,
    RenewalError,
    StatusTransitionError,
)
from .models import (
    AlumniRecord,
    MemberCommitteeAssignment,
    MemberLeave,
    MemberParticipation,
    MemberProfile,
    MemberRecognition,
    MembershipApplication,
    MembershipAuditRecord,
    MembershipCard,
    MembershipCategory,
    MembershipExit,
    MembershipFeeAdjustment,
    MembershipPayment,
    MembershipRenewal,
    MembershipStatus,
    MembershipStatusHistory,
    MembershipSuspension,
    MembershipTermination,
    MembershipTransfer,
    MembershipUpgrade,
)
from .permissions import (
    MEMBERSHIP_APPROVE,
    MEMBERSHIP_ARCHIVE,
    MEMBERSHIP_ASSIGN,
    MEMBERSHIP_CREATE,
    MEMBERSHIP_ISSUE_CARD,
    MEMBERSHIP_MANAGE,
    MEMBERSHIP_MANAGE_EXIT,
    MEMBERSHIP_MANAGE_LEAVE,
    MEMBERSHIP_MANAGE_PARTICIPATION,
    MEMBERSHIP_RECORD_PAYMENT,
    MEMBERSHIP_REJECT,
    MEMBERSHIP_RENEW,
    MEMBERSHIP_RESTORE,
    MEMBERSHIP_REVIEW,
    MEMBERSHIP_SUBMIT,
    MEMBERSHIP_SUSPEND,
    MEMBERSHIP_TERMINATE,
    MEMBERSHIP_TRANSFER,
    MEMBERSHIP_UPDATE,
    MEMBERSHIP_VERIFY_PAYMENT,
    MEMBERSHIP_WAIVE,
)

logger = logging.getLogger(__name__)

# Default status codes that mirror the seeded configuration.  They are
# referenced by code so configuration changes never require code edits.
STATUS_ACTIVE = "ACTIVE"
STATUS_PENDING = "PENDING"
STATUS_APPROVED = "APPROVED"
STATUS_INACTIVE = "INACTIVE"
STATUS_SUSPENDED = "SUSPENDED"
STATUS_EXPIRED = "EXPIRED"
STATUS_TERMINATED = "TERMINATED"
STATUS_ARCHIVED = "ARCHIVED"

DEFAULT_RENEWAL_PERIOD_MONTHS = 12


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------


def record_membership_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> MembershipAuditRecord:
    """Append an immutable audit record for a membership management event."""
    return MembershipAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, permission_code: str) -> None:
    if not user_has_permission(user, permission_code) and not user_has_permission(
        user, MEMBERSHIP_MANAGE
    ):
        raise PermissionDenied(_("Permission denied for action."))


def _issue_membership_reference(
    user, record_type: str = "member", notes: str = ""
) -> str:
    """Issue a centralized reference number for a membership entity."""
    generated = ReferenceNumberService(user=user).execute(
        module=ReferenceModules.MEMBERSHIPS,
        record_type=record_type,
        notes=notes,
    )
    return generated.reference_number


def _get_status(code: str) -> MembershipStatus:
    try:
        return MembershipStatus.objects.get(code=code)
    except MembershipStatus.DoesNotExist as exc:
        raise RegistrationError(
            _("Membership status %(code)s is not configured.") % {"code": code}
        ) from exc


def _get_category(code: str) -> MembershipCategory:
    try:
        return MembershipCategory.objects.get(code=code, is_active=True)
    except MembershipCategory.DoesNotExist as exc:
        raise RegistrationError(
            _("Membership category %(code)s is not configured or inactive.")
            % {"code": code}
        ) from exc


def _record_status_history(member, to_status, changed_by, reason: str = "") -> None:
    MembershipStatusHistory.objects.create(
        member=member,
        from_status=member.status,
        to_status=to_status,
        changed_by=changed_by,
        reason=reason,
    )


def _set_status(member, to_status, changed_by, reason: str = "") -> None:
    """Transition a member's status and record history + audit immutably."""
    from_status = member.status
    if from_status is not None and from_status == to_status:
        return
    member.status = to_status
    member.save(update_fields=["status", "updated_at"])
    _record_status_history(member, to_status, changed_by, reason)
    record_membership_audit(
        entity_type="MemberProfile",
        entity_id=member.id,
        action=MembershipAuditAction.STATUS_CHANGED,
        changed_by=changed_by,
        from_data={"status": from_status.code if from_status else None},
        to_data={"status": to_status.code},
        notes=reason or "Membership status updated.",
    )


# ---------------------------------------------------------------------------
# Application & Registration Services
# ---------------------------------------------------------------------------


class MembershipApplicationService(BaseService):
    """Service for the membership application workflow."""

    @transaction.atomic
    def submit_application(
        self,
        applicant,
        first_name: str,
        last_name: str,
        email: str,
        category,
        membership_type,
        level,
        phone: str = "",
        gender: str = "",
        date_of_birth=None,
        nationality: str = "",
        national_id: str = "",
        occupation: str = "",
        education_level: str = "",
        province: str = "",
        district: str = "",
        community: str = "",
        skills: str = "",
        interests: str = "",
        referral_source: str = "",
        declaration_agreed: bool = True,
        responsibilities_acknowledged: bool = True,
        **kwargs,
    ) -> MembershipApplication:
        """Create and submit a new membership application."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_SUBMIT)

        if not declaration_agreed:
            raise ApplicationValidationError(
                _("The application declaration must be agreed before submission.")
            )

        existing = MembershipApplication.objects.filter(
            applicant=applicant,
            status__in=[ApplicationStatus.DRAFT, ApplicationStatus.SUBMITTED],
        ).exists()
        if existing:
            raise ApplicationValidationError(
                _("An application for this applicant is already pending.")
            )

        reference_number = _issue_membership_reference(
            self.user, record_type="application", notes="Membership application"
        )
        application = MembershipApplication.objects.create(
            reference_number=reference_number,
            applicant=applicant,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            gender=gender,
            date_of_birth=date_of_birth,
            nationality=nationality,
            national_id=national_id,
            occupation=occupation,
            education_level=education_level,
            province=province,
            district=district,
            community=community,
            category=category,
            membership_type=membership_type,
            level=level,
            skills=skills,
            interests=interests,
            referral_source=referral_source,
            declaration_agreed=declaration_agreed,
            responsibilities_acknowledged=responsibilities_acknowledged,
            status=ApplicationStatus.SUBMITTED,
            submitted_at=timezone.now(),
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        record_membership_audit(
            entity_type="MembershipApplication",
            entity_id=application.id,
            action=MembershipAuditAction.SUBMITTED,
            changed_by=self.user,
            to_data={"reference_number": application.reference_number},
            notes="Membership application submitted.",
        )
        logger.info(
            "Membership application %s submitted.", application.reference_number
        )
        return application

    @transaction.atomic
    def start_review(self, application: MembershipApplication) -> MembershipApplication:
        """Move an application into review."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_REVIEW)
        if application.status not in (
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.RETURNED,
        ):
            raise ApplicationValidationError(
                _("Only submitted or returned applications can be reviewed.")
            )
        application.status = ApplicationStatus.UNDER_REVIEW
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.save()
        return application

    @transaction.atomic
    def approve_application(
        self,
        application: MembershipApplication,
        decision_notes: str = "",
        **registration,
    ) -> MemberProfile:
        """Approve an application and register the member in one transaction."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_APPROVE)

        if application.status != ApplicationStatus.UNDER_REVIEW:
            raise ApplicationValidationError(
                _("Application must be under review before approval.")
            )

        member = MemberRegistrationService(user=self.user).register_member(
            application=application,
            decision_notes=decision_notes,
            **registration,
        )
        return member

    @transaction.atomic
    def return_application(
        self, application: MembershipApplication, decision_notes: str = ""
    ) -> MembershipApplication:
        """Return an application for correction."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_REVIEW)
        if application.status != ApplicationStatus.UNDER_REVIEW:
            raise ApplicationValidationError(
                _("Only applications under review can be returned.")
            )
        application.status = ApplicationStatus.RETURNED
        application.decision_notes = decision_notes
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.save()
        record_membership_audit(
            entity_type="MembershipApplication",
            entity_id=application.id,
            action=MembershipAuditAction.RETURNED,
            changed_by=self.user,
            to_data={"status": ApplicationStatus.RETURNED},
            notes=decision_notes or "Application returned for correction.",
        )
        return application

    @transaction.atomic
    def reject_application(
        self, application: MembershipApplication, decision_notes: str = ""
    ) -> MembershipApplication:
        """Reject an application."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_REJECT)
        if application.status not in (
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.SUBMITTED,
        ):
            raise ApplicationValidationError(
                _("Application cannot be rejected from its current state.")
            )
        application.status = ApplicationStatus.REJECTED
        application.decision_notes = decision_notes
        application.reviewed_by = self.user
        application.reviewed_at = timezone.now()
        application.save()
        record_membership_audit(
            entity_type="MembershipApplication",
            entity_id=application.id,
            action=MembershipAuditAction.REJECTED,
            changed_by=self.user,
            to_data={"status": ApplicationStatus.REJECTED},
            notes=decision_notes or "Application rejected.",
        )
        return application

    @transaction.atomic
    def resubmit_application(
        self, application: MembershipApplication, **updates
    ) -> MembershipApplication:
        """Resubmit a returned application after correction."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_SUBMIT)
        if application.status != ApplicationStatus.RETURNED:
            raise ApplicationValidationError(
                _("Only returned applications can be resubmitted.")
            )
        for field, value in updates.items():
            setattr(application, field, value)
        application.status = ApplicationStatus.SUBMITTED
        application.decision_notes = ""
        application.submitted_at = timezone.now()
        application.save()
        record_membership_audit(
            entity_type="MembershipApplication",
            entity_id=application.id,
            action=MembershipAuditAction.SUBMITTED,
            changed_by=self.user,
            to_data={"status": ApplicationStatus.SUBMITTED},
            notes="Application resubmitted after correction.",
        )
        return application


class MemberRegistrationService(BaseService):
    """Service for registering a member profile after approval."""

    @transaction.atomic
    def register_member(
        self,
        application: MembershipApplication | None = None,
        user_account=None,
        decision_notes: str = "",
        category=None,
        membership_type=None,
        level=None,
        date_joined=None,
        expiry_date=None,
        renewal_period_months: int = DEFAULT_RENEWAL_PERIOD_MONTHS,
        **profile_fields,
    ) -> MemberProfile:
        """Register a member profile from an approved application."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_CREATE)

        if application is not None:
            user_account = user_account or application.applicant
            category = category or application.category
            membership_type = membership_type or application.membership_type
            level = level or application.level

        if user_account is None:
            raise RegistrationError(_("A user account is required for registration."))
        if category is None or membership_type is None or level is None:
            raise RegistrationError(
                _("Category, type and level are required for registration.")
            )

        if hasattr(user_account, "member_profile"):
            raise RegistrationError(
                _("This user account is already linked to a membership profile.")
            )

        membership_id = _issue_membership_reference(
            self.user, record_type="member", notes="Member registration"
        )
        today = date_joined or timezone.now().date()
        new_expiry = expiry_date or today + timedelta(days=renewal_period_months * 30)

        defaults = {}
        if application is not None:
            defaults = {
                "gender": application.gender,
                "date_of_birth": application.date_of_birth,
                "nationality": application.nationality,
                "national_id": application.national_id,
                "occupation": application.occupation,
                "education_level": application.education_level,
                "province": application.province,
                "district": application.district,
                "community": application.community,
                "phone_primary": application.phone,
                "email_personal": application.email,
                "skills_summary": application.skills,
                "interests_summary": application.interests,
            }
        defaults.update(profile_fields)

        member = MemberProfile.objects.create(
            user=user_account,
            membership_id=membership_id,
            category=category,
            membership_type=membership_type,
            level=level,
            status=_get_status(STATUS_ACTIVE),
            date_joined=today,
            expiry_date=new_expiry,
            responsibilities_acknowledged=True,
            created_by=self.user,
            updated_by=self.user,
            **defaults,
        )

        if application is not None:
            application.member_profile = member
            application.status = ApplicationStatus.APPROVED
            application.approved_by = self.user
            application.approved_at = timezone.now()
            application.decision_notes = decision_notes or application.decision_notes
            application.save()

        _record_status_history(member, member.status, self.user, "Member registered.")
        record_membership_audit(
            entity_type="MemberProfile",
            entity_id=member.id,
            action=MembershipAuditAction.CREATED,
            changed_by=self.user,
            to_data={
                "membership_id": membership_id,
                "user_id": str(user_account.id),
            },
            notes=decision_notes or "Member registered after approval.",
        )
        logger.info("Member %s registered by %s.", membership_id, self.user)
        return member

    @transaction.atomic
    def create_member_direct(
        self,
        user_account,
        category,
        membership_type,
        level,
        date_joined=None,
        **profile_fields,
    ) -> MemberProfile:
        """Directly register a member without an application (staff action)."""
        return self.register_member(
            application=None,
            user_account=user_account,
            category=category,
            membership_type=membership_type,
            level=level,
            date_joined=date_joined,
            **profile_fields,
        )


# ---------------------------------------------------------------------------
# Status & Lifecycle Services
# ---------------------------------------------------------------------------


class MembershipStatusService(BaseService):
    """Service for controlled membership status transitions."""

    @transaction.atomic
    def update_status(
        self,
        member: MemberProfile,
        new_status_code: str,
        reason: str = "",
        validate: bool = True,
    ) -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_UPDATE)
        new_status = _get_status(new_status_code)
        _set_status(member, new_status, self.user, str(reason or _("Status updated.")))
        return member

    @transaction.atomic
    def activate(self, member: MemberProfile, reason: str = "") -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_UPDATE)
        _set_status(member, _get_status(STATUS_ACTIVE), self.user, reason)
        return member

    @transaction.atomic
    def deactivate(self, member: MemberProfile, reason: str = "") -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_UPDATE)
        _set_status(member, _get_status(STATUS_INACTIVE), self.user, reason)
        return member

    @transaction.atomic
    def suspend(
        self, member: MemberProfile, reason: str, effective_date
    ) -> MembershipSuspension:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_SUSPEND)
        suspension, _ = MembershipSuspension.objects.update_or_create(
            member=member,
            is_active=True,
            defaults={
                "reason": reason,
                "effective_date": effective_date,
                "authorized_by": self.user,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        _set_status(member, _get_status(STATUS_SUSPENDED), self.user, reason)
        return suspension

    @transaction.atomic
    def lift_suspension(self, suspension: MembershipSuspension) -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_SUSPEND)
        suspension.is_active = False
        suspension.lifted_at = timezone.now()
        suspension.lifted_by = self.user
        suspension.save()
        member = suspension.member
        _set_status(member, _get_status(STATUS_ACTIVE), self.user, "Suspension lifted.")
        return member

    @transaction.atomic
    def terminate(
        self,
        member: MemberProfile,
        reason: str,
        reason_detail: str = "",
        effective_date=None,
    ) -> MembershipTermination:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_TERMINATE)
        if member.is_terminated:
            raise StatusTransitionError(_("Membership is already terminated."))
        termination = MembershipTermination.objects.create(
            member=member,
            reason=reason,
            reason_detail=reason_detail,
            effective_date=effective_date or timezone.now().date(),
            authorized_by=self.user,
            created_by=self.user,
        )
        _set_status(member, _get_status(STATUS_TERMINATED), self.user, reason_detail)
        record_membership_audit(
            entity_type="MembershipTermination",
            entity_id=termination.id,
            action=MembershipAuditAction.TERMINATED,
            changed_by=self.user,
            to_data={"member_id": str(member.id), "reason": reason},
            notes=reason_detail,
        )
        return termination

    @transaction.atomic
    def archive(self, member: MemberProfile, reason: str = "") -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_ARCHIVE)
        member.archive()
        _set_status(
            member,
            _get_status(STATUS_ARCHIVED),
            self.user,
            str(reason or _("Archived.")),
        )
        return member

    @transaction.atomic
    def restore(self, member: MemberProfile, reason: str = "") -> MemberProfile:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_RESTORE)
        member.unarchive()
        _set_status(
            member, _get_status(STATUS_ACTIVE), self.user, str(reason or _("Restored."))
        )
        return member


# ---------------------------------------------------------------------------
# Renewal, Upgrade, Transfer Services
# ---------------------------------------------------------------------------


class MembershipRenewalService(BaseService):
    """Service for the membership renewal workflow."""

    @transaction.atomic
    def request_renewal(
        self,
        member: MemberProfile,
        renewal_period_months: int = DEFAULT_RENEWAL_PERIOD_MONTHS,
        policy_accepted: bool = True,
        profile_details_confirmed: bool = True,
        notes: str = "",
    ) -> MembershipRenewal:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_RENEW)
        if not member.is_active:
            raise RenewalError(_("Only active members can renew their membership."))
        if not policy_accepted:
            raise RenewalError(_("Organizational policies must be accepted to renew."))

        category = member.category
        fee_amount = (
            category.renewal_fee_amount
            if category and category.renewal_fee_amount
            else None
        )

        renewal = MembershipRenewal.objects.create(
            member=member,
            previous_expiry=member.expiry_date or timezone.now().date(),
            renewal_period_months=renewal_period_months,
            fee_amount=fee_amount,
            policy_accepted=policy_accepted,
            profile_details_confirmed=profile_details_confirmed,
            status=RenewalStatus.PENDING,
            created_by=self.user,
            updated_by=self.user,
            notes=notes,
        )
        record_membership_audit(
            entity_type="MembershipRenewal",
            entity_id=renewal.id,
            action=MembershipAuditAction.RENEWED,
            changed_by=self.user,
            to_data={
                "member_id": str(member.id),
                "period_months": renewal_period_months,
            },
            notes="Renewal request initiated.",
        )
        return renewal

    @transaction.atomic
    def approve_renewal(
        self, renewal: MembershipRenewal, approve: bool = True, notes: str = ""
    ) -> MembershipRenewal:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_RENEW)
        if renewal.status != RenewalStatus.PENDING:
            raise RenewalError(_("Only pending renewals can be processed."))

        member = renewal.member
        if approve:
            if renewal.payment_status not in (PaymentStatus.PAID, PaymentStatus.WAIVED):
                raise RenewalError(
                    _("Renewal payment must be recorded before approval.")
                )
            today = timezone.now().date()
            previous_expiry = member.expiry_date or today
            base = max(previous_expiry, today)
            new_expiry = base + timedelta(days=renewal.renewal_period_months * 30)
            renewal.new_expiry = new_expiry
            renewal.status = RenewalStatus.APPROVED
            renewal.approved_by = self.user
            renewal.approved_at = timezone.now()
            renewal.save()

            member.expiry_date = new_expiry
            member.save(update_fields=["expiry_date", "updated_at"])
            _set_status(
                member, _get_status(STATUS_ACTIVE), self.user, "Membership renewed."
            )
        else:
            renewal.status = RenewalStatus.REJECTED
            renewal.approved_by = self.user
            renewal.approved_at = timezone.now()
            renewal.notes = notes or renewal.notes
            renewal.save()

        record_membership_audit(
            entity_type="MembershipRenewal",
            entity_id=renewal.id,
            action=MembershipAuditAction.RENEWED,
            changed_by=self.user,
            from_data={"status": RenewalStatus.PENDING},
            to_data={
                "status": renewal.status,
                "new_expiry": str(renewal.new_expiry or ""),
            },
            notes=notes or "Renewal decision recorded.",
        )
        return renewal

    @transaction.atomic
    def auto_expire_lapsed(self, days_without_renewal: int = 30) -> int:
        """Expire members whose membership lapsed beyond the configured window."""
        if self.user:
            _require_permission(self.user, MEMBERSHIP_RENEW)
        cutoff = timezone.now().date() - timedelta(days=days_without_renewal)
        expired_status = _get_status(STATUS_EXPIRED)
        qs = MemberProfile.objects.filter(
            status__code=STATUS_ACTIVE,
            expiry_date__lt=cutoff,
            is_deleted=False,
            is_archived=False,
        )
        count = 0
        for member in qs:
            _set_status(member, expired_status, self.user, "Auto-expired after lapse.")
            count += 1
        return count


class MembershipUpgradeService(BaseService):
    """Service for membership upgrades between categories."""

    @transaction.atomic
    def request_upgrade(
        self,
        member: MemberProfile,
        to_category,
        reason: str = "",
        effective_date=None,
    ) -> MembershipUpgrade:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_TRANSFER)
        if member.category is None:
            raise StatusTransitionError(_("Member has no current category."))
        if member.category == to_category:
            raise StatusTransitionError(
                _("Target category must differ from the current category.")
            )
        upgrade = MembershipUpgrade.objects.create(
            member=member,
            from_category=member.category,
            to_category=to_category,
            effective_date=effective_date or timezone.now().date(),
            reason=reason,
            status=UpgradeStatus.PENDING,
            approved_by=None,
            created_by=self.user,
            updated_by=self.user,
        )
        return upgrade

    @transaction.atomic
    def approve_upgrade(
        self, upgrade: MembershipUpgrade, approve: bool = True
    ) -> MembershipUpgrade:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_TRANSFER)
        if upgrade.status != UpgradeStatus.PENDING:
            raise StatusTransitionError(_("Only pending upgrades can be processed."))
        if approve:
            upgrade.member.category = upgrade.to_category
            upgrade.member.save(update_fields=["category", "updated_at"])
            upgrade.status = UpgradeStatus.APPROVED
            upgrade.approved_by = self.user
            upgrade.save()
            record_membership_audit(
                entity_type="MembershipUpgrade",
                entity_id=upgrade.id,
                action=MembershipAuditAction.UPGRADED,
                changed_by=self.user,
                from_data={"category": upgrade.from_category.code},
                to_data={"category": upgrade.to_category.code},
                notes="Membership upgraded.",
            )
        else:
            upgrade.status = UpgradeStatus.REJECTED
            upgrade.approved_by = self.user
            upgrade.save()
        return upgrade


class MembershipTransferService(BaseService):
    """Service for administrative membership transfers."""

    @transaction.atomic
    def request_transfer(
        self,
        member: MemberProfile,
        to_province: str,
        to_district: str,
        to_community: str = "",
        reason: str = "",
        effective_date=None,
    ) -> MembershipTransfer:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_TRANSFER)
        transfer = MembershipTransfer.objects.create(
            member=member,
            from_province=member.province,
            from_district=member.district,
            from_community=member.community,
            to_province=to_province,
            to_district=to_district,
            to_community=to_community,
            effective_date=effective_date or timezone.now().date(),
            reason=reason,
            status=TransferStatus.PENDING,
            created_by=self.user,
            updated_by=self.user,
        )
        return transfer

    @transaction.atomic
    def approve_transfer(
        self, transfer: MembershipTransfer, approve: bool = True
    ) -> MembershipTransfer:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_TRANSFER)
        if transfer.status != TransferStatus.PENDING:
            raise StatusTransitionError(_("Only pending transfers can be processed."))
        if approve:
            member = transfer.member
            member.province = transfer.to_province
            member.district = transfer.to_district
            member.community = transfer.to_community
            member.save(
                update_fields=["province", "district", "community", "updated_at"]
            )
            transfer.status = TransferStatus.APPROVED
            transfer.authorized_by = self.user
            transfer.save()
            record_membership_audit(
                entity_type="MembershipTransfer",
                entity_id=transfer.id,
                action=MembershipAuditAction.TRANSFERRED,
                changed_by=self.user,
                from_data={"district": transfer.from_district},
                to_data={"district": transfer.to_district},
                notes="Membership transfer approved.",
            )
        else:
            transfer.status = TransferStatus.REJECTED
            transfer.authorized_by = self.user
            transfer.save()
        return transfer


# ---------------------------------------------------------------------------
# Fees, Payments & Adjustments
# ---------------------------------------------------------------------------


class MembershipPaymentService(BaseService):
    """Service for membership fee payments."""

    @transaction.atomic
    def record_payment(
        self,
        member: MemberProfile,
        amount,
        payment_method: str,
        payment_date=None,
        fee=None,
        currency: str = "ZMW",
        transaction_reference: str = "",
        period_from=None,
        period_to=None,
        receipt_file=None,
        **kwargs,
    ) -> MembershipPayment:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_RECORD_PAYMENT)
        if amount <= 0:
            raise PaymentError(_("Payment amount must be greater than zero."))

        receipt_number = _issue_membership_reference(
            self.user, record_type="receipt", notes="Membership payment receipt"
        )
        payment = MembershipPayment.objects.create(
            member=member,
            fee=fee,
            receipt_number=receipt_number,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            payment_date=payment_date or timezone.now().date(),
            status=PaymentStatus.PAID,
            transaction_reference=transaction_reference,
            period_from=period_from,
            period_to=period_to,
            receipt_file=receipt_file,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        record_membership_audit(
            entity_type="MembershipPayment",
            entity_id=payment.id,
            action=MembershipAuditAction.PAYMENT_RECORDED,
            changed_by=self.user,
            to_data={
                "receipt_number": receipt_number,
                "amount": str(amount),
                "method": payment_method,
            },
            notes="Membership payment recorded.",
        )
        return payment

    @transaction.atomic
    def verify_payment(self, payment: MembershipPayment) -> MembershipPayment:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_VERIFY_PAYMENT)
        payment.status = PaymentStatus.PAID
        payment.verified_by = self.user
        payment.verified_at = timezone.now()
        payment.save()
        record_membership_audit(
            entity_type="MembershipPayment",
            entity_id=payment.id,
            action=MembershipAuditAction.PAYMENT_RECORDED,
            changed_by=self.user,
            to_data={"status": PaymentStatus.PAID},
            notes="Payment verified.",
        )
        return payment


class MembershipFeeAdjustmentService(BaseService):
    """Service for fee discounts and waivers."""

    @transaction.atomic
    def request_adjustment(
        self,
        member: MemberProfile,
        adjustment_type: str,
        reason: str,
        amount=None,
        percentage=None,
        effective_from=None,
        effective_to=None,
    ) -> MembershipFeeAdjustment:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_WAIVE)
        if amount is None and percentage is None:
            raise PaymentError(
                _("Either an amount or a percentage is required for an adjustment.")
            )
        adjustment = MembershipFeeAdjustment.objects.create(
            member=member,
            adjustment_type=adjustment_type,
            amount=amount,
            percentage=percentage,
            reason=reason,
            effective_from=effective_from or timezone.now().date(),
            effective_to=effective_to,
            status=AdjustmentStatus.PENDING,
            created_by=self.user,
            updated_by=self.user,
        )
        return adjustment

    @transaction.atomic
    def approve_adjustment(
        self, adjustment: MembershipFeeAdjustment, approve: bool = True
    ) -> MembershipFeeAdjustment:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_WAIVE)
        adjustment.status = (
            AdjustmentStatus.APPROVED if approve else AdjustmentStatus.REJECTED
        )
        adjustment.approved_by = self.user
        adjustment.save()
        return adjustment


# ---------------------------------------------------------------------------
# Membership Cards
# ---------------------------------------------------------------------------


class MembershipCardService(BaseService):
    """Service for issuing and managing digital membership cards."""

    @transaction.atomic
    def issue_card(
        self,
        member: MemberProfile,
        expiry_months: int = 12,
        notes: str = "",
    ) -> MembershipCard:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_ISSUE_CARD)
        if not member.membership_id:
            raise CardError(_("Member has no membership ID yet."))

        existing = MembershipCard.objects.filter(member=member).first()
        if existing and existing.status in (CardStatus.ACTIVE, CardStatus.ISSUED):
            raise CardError(
                _("An active membership card already exists for this member.")
            )

        card_number = _issue_membership_reference(
            self.user, record_type="card", notes="Membership card"
        )
        verification_code = secrets.token_hex(8).upper()
        card = MembershipCard.objects.create(
            member=member,
            card_number=card_number,
            verification_code=verification_code,
            issue_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timedelta(days=expiry_months * 30),
            status=CardStatus.ACTIVE,
            issued_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            notes=notes,
        )
        record_membership_audit(
            entity_type="MembershipCard",
            entity_id=card.id,
            action=MembershipAuditAction.CARD_ISSUED,
            changed_by=self.user,
            to_data={"card_number": card_number, "member_id": str(member.id)},
            notes="Membership card issued.",
        )
        return card

    @transaction.atomic
    def revoke_card(self, card: MembershipCard, reason: str = "") -> MembershipCard:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_ISSUE_CARD)
        card.status = CardStatus.REVOKED
        card.revoked_reason = reason
        card.save()
        record_membership_audit(
            entity_type="MembershipCard",
            entity_id=card.id,
            action=MembershipAuditAction.REVOKED,
            changed_by=self.user,
            to_data={"status": CardStatus.REVOKED},
            notes=reason or "Membership card revoked.",
        )
        return card

    def verify_card(self, verification_code: str) -> MembershipCard | None:
        """Verify a card by its verification code (public minimal check)."""
        try:
            card = MembershipCard.objects.get(
                verification_code=verification_code, status=CardStatus.ACTIVE
            )
        except MembershipCard.DoesNotExist:
            return None
        return card


# ---------------------------------------------------------------------------
# Participation, Committees, Recognition, Leave, Exit
# ---------------------------------------------------------------------------


class MemberParticipationService(BaseService):
    """Service for recording member participation."""

    @transaction.atomic
    def record_participation(
        self,
        member: MemberProfile,
        participation_type: str,
        activity_name: str,
        start_date,
        role: str = "",
        end_date=None,
        outcomes: str = "",
        **kwargs,
    ) -> MemberParticipation:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_MANAGE_PARTICIPATION)
        participation = MemberParticipation.objects.create(
            member=member,
            participation_type=participation_type,
            activity_name=activity_name,
            role=role,
            start_date=start_date,
            end_date=end_date,
            outcomes=outcomes,
            status=ParticipationStatus.ENROLLED,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        return participation


class MemberCommitteeService(BaseService):
    """Service for committee assignments."""

    @transaction.atomic
    def assign_member(
        self,
        member: MemberProfile,
        committee,
        appointment_date=None,
        position: str = "",
        end_date=None,
        responsibilities: str = "",
    ) -> MemberCommitteeAssignment:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_ASSIGN)
        assignment = MemberCommitteeAssignment.objects.create(
            member=member,
            committee=committee,
            position=position,
            appointment_date=appointment_date or timezone.now().date(),
            end_date=end_date,
            responsibilities=responsibilities,
            status=ParticipationStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user,
        )
        return assignment


class MemberRecognitionService(BaseService):
    """Service for recording member recognition."""

    @transaction.atomic
    def record_recognition(
        self,
        member: MemberProfile,
        recognition_type: str,
        title: str,
        award_date=None,
        description: str = "",
        issuing_authority: str = "",
        **kwargs,
    ) -> MemberRecognition:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_APPROVE)
        recognition = MemberRecognition.objects.create(
            member=member,
            recognition_type=recognition_type,
            title=title,
            description=description,
            award_date=award_date or timezone.now().date(),
            issuing_authority=issuing_authority,
            created_by=self.user,
            updated_by=self.user,
            **kwargs,
        )
        return recognition


class MemberLeaveService(BaseService):
    """Service for member leave management."""

    @transaction.atomic
    def apply_leave(
        self,
        member: MemberProfile,
        leave_type: str,
        start_date,
        end_date,
        reason: str = "",
    ) -> MemberLeave:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_MANAGE_LEAVE)
        if start_date > end_date:
            raise ValidationError(_("Leave end date cannot precede start date."))
        leave = MemberLeave.objects.create(
            member=member,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=LeaveStatus.SUBMITTED,
            created_by=self.user,
            updated_by=self.user,
        )
        return leave

    @transaction.atomic
    def approve_leave(
        self, leave: MemberLeave, approve: bool = True, notes: str = ""
    ) -> MemberLeave:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_MANAGE_LEAVE)
        leave.status = LeaveStatus.APPROVED if approve else LeaveStatus.REJECTED
        leave.approved_by = self.user
        leave.approval_notes = notes
        leave.save()
        return leave


class MembershipExitService(BaseService):
    """Service for the membership exit and alumni transition workflow."""

    @transaction.atomic
    def initiate_exit(
        self,
        member: MemberProfile,
        exit_type: str,
        effective_date=None,
        reason: str = "",
        transition_to_alumni: bool = True,
        **kwargs,
    ) -> MembershipExit:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_MANAGE_EXIT)
        exit_rec, _ = MembershipExit.objects.update_or_create(
            member=member,
            status=ExitStatus.INITIATED,
            defaults={
                "exit_type": exit_type,
                "reason": reason,
                "effective_date": effective_date or timezone.now().date(),
                "status": ExitStatus.INITIATED,
                "transition_to_alumni": transition_to_alumni,
                "created_by": self.user,
                "updated_by": self.user,
                **kwargs,
            },
        )
        return exit_rec

    @transaction.atomic
    def complete_exit(
        self,
        exit_rec: MembershipExit,
        exit_interview_notes: str = "",
        assets_returned: bool = True,
        documents_returned: bool = True,
    ) -> MembershipExit:
        if self.user:
            _require_permission(self.user, MEMBERSHIP_MANAGE_EXIT)
        member = exit_rec.member
        if exit_rec.transition_to_alumni:
            exit_rec.status = ExitStatus.ALUMNI
            _set_status(
                member,
                _get_status(STATUS_TERMINATED),
                self.user,
                f"Exit ({exit_rec.exit_type}): transitioned to alumni.",
            )
            AlumniRecord.objects.update_or_create(
                member=member,
                defaults={
                    "alumni_since": exit_rec.effective_date,
                    "previous_category": member.category,
                    "previous_level": member.level.name if member.level else "",
                    "previous_district": member.district,
                    "communication_consent": member.consent_to_communications,
                    "exit_record": exit_rec,
                    "created_by": self.user,
                },
            )
        else:
            exit_rec.status = ExitStatus.EXITED
            _set_status(
                member,
                _get_status(STATUS_TERMINATED),
                self.user,
                f"Exit ({exit_rec.exit_type}).",
            )
        exit_rec.exit_interview_notes = exit_interview_notes
        exit_rec.assets_returned = assets_returned
        exit_rec.documents_returned = documents_returned
        exit_rec.clearances_completed = True
        exit_rec.approved_by = self.user
        exit_rec.save()

        MembershipCard.objects.filter(member=member, status=CardStatus.ACTIVE).update(
            status=CardStatus.REVOKED,
            revoked_reason="Membership exit completed.",
        )

        record_membership_audit(
            entity_type="MembershipExit",
            entity_id=exit_rec.id,
            action=MembershipAuditAction.TERMINATED,
            changed_by=self.user,
            to_data={"status": exit_rec.status, "member_id": str(member.id)},
            notes=exit_rec.reason,
        )
        return exit_rec


# ---------------------------------------------------------------------------
# Analytics & Dashboard
# ---------------------------------------------------------------------------


class MembershipAnalyticsService(BaseService):
    """Service for dashboard summaries and analytical insights."""

    def _base_profiles(self):
        return MemberProfile.objects.filter(is_deleted=False, is_archived=False)

    def dashboard_summary(self) -> dict:
        profiles = self._base_profiles()
        today = timezone.now().date()

        status_counts = dict(
            profiles.values_list("status__code").annotate(count=Count("id"))
        )
        expiring_within_30 = profiles.filter(
            expiry_date__range=(today, today + timedelta(days=30)),
            status__code=STATUS_ACTIVE,
        ).count()

        summary = {
            "total_members": profiles.count(),
            "active_members": status_counts.get(STATUS_ACTIVE, 0),
            "pending": status_counts.get(STATUS_PENDING, 0),
            "suspended": status_counts.get(STATUS_SUSPENDED, 0),
            "expired": status_counts.get(STATUS_EXPIRED, 0),
            "terminated": status_counts.get(STATUS_TERMINATED, 0),
            "pending_applications": MembershipApplication.objects.filter(
                status__in=[ApplicationStatus.SUBMITTED, ApplicationStatus.UNDER_REVIEW]
            ).count(),
            "renewals_due": expiring_within_30,
            "category_distribution": list(
                profiles.exclude(category__isnull=True)
                .values("category__name")
                .annotate(count=Count("id"))
                .order_by("-count")
            ),
            "district_distribution": list(
                profiles.exclude(district="")
                .values("district")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            ),
            "gender_distribution": list(
                profiles.exclude(gender="").values("gender").annotate(count=Count("id"))
            ),
            "recent_members": list(
                profiles.order_by("-created_at")[:5].values(
                    "id",
                    "membership_id",
                    "user__first_name",
                    "user__last_name",
                    "status__name",
                    "created_at",
                )
            ),
        }
        return summary

    def fee_collection_summary(self) -> dict:
        paid = MembershipPayment.objects.filter(status=PaymentStatus.PAID).aggregate(
            total=Sum("amount")
        )
        pending_payments = MembershipPayment.objects.filter(
            status=PaymentStatus.PENDING
        ).count()
        return {
            "total_collected": paid["total"] or Decimal("0.00"),
            "pending_payments": pending_payments,
            "payment_count": MembershipPayment.objects.filter(
                status=PaymentStatus.PAID
            ).count(),
        }

    def growth_trends(self, months: int = 12) -> list[dict]:
        cutoff = timezone.now() - timedelta(days=months * 30)
        rows = (
            MemberProfile.objects.filter(created_at__gte=cutoff)
            .extra(select={"month": "strftime('%Y-%m', created_at)"})
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        return list(rows)
