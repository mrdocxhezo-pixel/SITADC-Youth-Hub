"""Permission-checked transactional services for beneficiary management.

Every write flows through these services so that RBAC checks, object-scope
checks, consent enforcement, lifecycle transitions, reference-number
allocation, and the immutable audit trail are enforced consistently.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import ClassVar

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from .constants import (
    REFERENCE_SCHEME_CODES,
    AssessmentStatus,
    BeneficiaryStatus,
    ConsentStatus,
    DuplicateReviewStatus,
    EnrollmentStatus,
    ExitStatus,
    FollowUpStatus,
    PlanStatus,
    ReferenceDataKind,
    ReferralStatus,
    SafeguardingStatus,
    ServiceDeliveryStatus,
    TransferStatus,
)
from .models import (
    AttendanceRecord,
    Beneficiary,
    BeneficiaryAssessment,
    BeneficiaryAuditRecord,
    BeneficiaryCommunication,
    BeneficiaryDocument,
    BeneficiaryEnrollment,
    BeneficiaryGroup,
    BeneficiaryHousehold,
    BeneficiaryParticipation,
    BeneficiaryStatusHistory,
    CaseNote,
    ConsentRecord,
    DuplicateReviewRecord,
    ExitRecord,
    FeedbackRecord,
    FollowUpVisit,
    GroupMembership,
    GuardianRecord,
    HouseholdMember,
    OutcomeRecord,
    Referral,
    SafeguardingRecord,
    ServiceDeliveryRecord,
    SupportPlan,
    TransferRecord,
)
from .permissions import (
    BENEFICIARIES_APPROVE,
    BENEFICIARIES_ARCHIVE,
    BENEFICIARIES_CREATE,
    BENEFICIARIES_MANAGE,
    BENEFICIARIES_MANAGE_ASSESSMENTS,
    BENEFICIARIES_MANAGE_ATTENDANCE,
    BENEFICIARIES_MANAGE_CASE_NOTES,
    BENEFICIARIES_MANAGE_CONSENT,
    BENEFICIARIES_MANAGE_DOCUMENTS,
    BENEFICIARIES_MANAGE_DUPLICATES,
    BENEFICIARIES_MANAGE_ENROLLMENTS,
    BENEFICIARIES_MANAGE_EXITS,
    BENEFICIARIES_MANAGE_FEEDBACK,
    BENEFICIARIES_MANAGE_FOLLOW_UPS,
    BENEFICIARIES_MANAGE_GROUPS,
    BENEFICIARIES_MANAGE_GUARDIANS,
    BENEFICIARIES_MANAGE_HOUSEHOLDS,
    BENEFICIARIES_MANAGE_OUTCOMES,
    BENEFICIARIES_MANAGE_PARTICIPATION,
    BENEFICIARIES_MANAGE_REFERRALS,
    BENEFICIARIES_MANAGE_SAFEGUARDING,
    BENEFICIARIES_MANAGE_SERVICES,
    BENEFICIARIES_MANAGE_SUPPORT_PLANS,
    BENEFICIARIES_MANAGE_TRANSFERS,
    BENEFICIARIES_RESTORE,
    BENEFICIARIES_SUBMIT,
    BENEFICIARIES_UPDATE,
)
from .selectors import user_can_access_beneficiary

logger = logging.getLogger(__name__)


BENEFICIARY_TRANSITIONS: dict[str, set[str]] = {
    BeneficiaryStatus.IDENTIFIED: {
        BeneficiaryStatus.REGISTERED,
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.REGISTERED: {
        BeneficiaryStatus.VERIFIED,
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.VERIFIED: {
        BeneficiaryStatus.ELIGIBLE,
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.ELIGIBLE: {
        BeneficiaryStatus.ENROLLED,
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.ENROLLED: {
        BeneficiaryStatus.ACTIVE,
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.ACTIVE: {
        BeneficiaryStatus.SUSPENDED,
        BeneficiaryStatus.GRADUATED,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.SUSPENDED: {
        BeneficiaryStatus.REGISTERED,
        BeneficiaryStatus.VERIFIED,
        BeneficiaryStatus.ELIGIBLE,
        BeneficiaryStatus.ENROLLED,
        BeneficiaryStatus.ACTIVE,
        BeneficiaryStatus.EXITED,
    },
    BeneficiaryStatus.GRADUATED: {
        BeneficiaryStatus.EXITED,
        BeneficiaryStatus.ARCHIVED,
    },
    BeneficiaryStatus.EXITED: {BeneficiaryStatus.ARCHIVED},
    BeneficiaryStatus.ARCHIVED: set(),
}


def _require_permission(user, permission_code: str) -> None:
    """Check RBAC for every write, allowing the module-wide manager override."""
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(_("An authenticated actor is required."))
    if not (
        user_has_permission(user, permission_code)
        or user_has_permission(user, BENEFICIARIES_MANAGE)
    ):
        raise PermissionDenied(_("Permission denied for this beneficiary action."))


def _require_record_access(user, beneficiary, *, include_archived=False) -> None:
    if not user_can_access_beneficiary(
        user, beneficiary, include_archived=include_archived
    ):
        raise PermissionDenied(
            _("This beneficiary record is outside your access scope.")
        )


def _log_event(action: str, instance, actor, **details) -> None:
    """Structured Phase 17 audit trail until the central audit app exists."""
    entity_type = type(instance).__name__
    entity_id = str(instance.pk)
    logger.info(
        "beneficiary_domain_event",
        extra={
            "beneficiary_event": {
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "actor_id": str(getattr(actor, "pk", "")),
                **details,
            }
        },
    )
    BeneficiaryAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_by=actor,
        notes=str(details or ""),
        to_data={key: str(value) for key, value in details.items()},
    )


def _reserve_reference(actor, scheme_key: str):
    scheme_code = REFERENCE_SCHEME_CODES[scheme_key]
    return ReferenceNumberService(user=actor).execute(
        module=ReferenceModules.BENEFICIARIES,
        record_type=scheme_code,
        scheme_code=scheme_code,
        notes=f"Phase 17 {scheme_code} reference reservation.",
    )


def _confirm_reference(actor, reference, instance) -> None:
    ConfirmReferenceAssignmentService(user=actor).execute(
        reference=reference,
        record_id=instance.pk,
        notes=f"Assigned to {type(instance).__name__}.",
    )


def _validate_reference_values(values, expected_kind: str, field_name: str) -> list:
    records = list(values or [])
    invalid = [record for record in records if record.kind != expected_kind]
    if invalid:
        raise ValidationError(
            {field_name: _("One or more values have the wrong kind.")}
        )
    return records


def _set_profile_taxonomies(beneficiary: Beneficiary, fields: dict) -> None:
    for field_name, expected_kind in (
        ("vulnerabilities", ReferenceDataKind.VULNERABILITY),
        ("inclusion_barriers", ReferenceDataKind.INCLUSION),
        ("disabilities", ReferenceDataKind.DISABILITY),
        ("skills", ReferenceDataKind.SKILL),
        ("interests", ReferenceDataKind.INTEREST),
        ("needs", ReferenceDataKind.NEED_TYPE),
    ):
        if field_name in fields:
            values = _validate_reference_values(
                fields.pop(field_name), expected_kind, field_name
            )
            getattr(beneficiary, field_name).set(values)


def _ensure_consent_for_status(beneficiary: Beneficiary, new_status: str) -> None:
    """Consent is a hard gate for verified, enrolled, and active statuses."""
    if new_status not in {
        BeneficiaryStatus.VERIFIED,
        BeneficiaryStatus.ELIGIBLE,
        BeneficiaryStatus.ENROLLED,
        BeneficiaryStatus.ACTIVE,
        BeneficiaryStatus.GRADUATED,
    }:
        return
    if beneficiary.is_minor and not (
        beneficiary.consent_status == ConsentStatus.GRANTED
        and beneficiary.assent_recorded
    ):
        raise ValidationError(
            {
                "status": _(
                    "A minor requires recorded guardian consent and assent before "
                    "this status."
                )
            },
            code="minor_consent_required",
        )
    if not beneficiary.is_minor and beneficiary.consent_status != ConsentStatus.GRANTED:
        raise ValidationError(
            {"status": _("Recorded consent is required before this status.")},
            code="consent_required",
        )
    if (
        beneficiary.consent_expiry_date
        and beneficiary.consent_expiry_date < timezone.localdate()
    ):
        raise ValidationError(
            {"status": _("Recorded consent has expired and must be renewed.")},
            code="consent_expired",
        )


class BeneficiaryService(BaseService):
    """Create, update, transition, archive, and restore beneficiary profiles."""

    CREATE_FIELDS: ClassVar[set[str]] = {
        field.name
        for field in Beneficiary._meta.fields
        if field.name
        not in {
            "id",
            "reference_number",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
            "deleted_at",
            "deleted_by",
            "archived_at",
            "archived_by",
            "is_deleted",
            "is_archived",
            "status",
            "is_minor",
            "verified_by",
            "verification_date",
            "enrolled_at",
            "graduated_at",
            "exited_at",
            "consent_status",
            "consent_recorded_at",
            "consent_expiry_date",
            "consent_version",
            "assent_recorded",
            "assent_recorded_at",
            "assent_version",
            "duplicate_of",
            "duplicate_review_status",
        }
    }
    UPDATE_FIELDS: ClassVar[set[str]] = set(CREATE_FIELDS) | {
        "consent_status",
        "consent_expiry_date",
        "consent_version",
        "assent_recorded",
    }

    @transaction.atomic
    def create(self, **fields) -> Beneficiary:
        _require_permission(self.user, BENEFICIARIES_CREATE)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in (
                "vulnerabilities",
                "inclusion_barriers",
                "disabilities",
                "skills",
                "interests",
                "needs",
            )
            if name in fields
        }
        disallowed = set(fields) - self.CREATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported beneficiary fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        first_name = str(fields.get("first_name", "")).strip()
        last_name = str(fields.get("last_name", "")).strip()
        if not (first_name and last_name):
            raise ValidationError(_("First name and last name are required."))
        if Beneficiary.all_objects.filter(
            Q(first_name__iexact=first_name, last_name__iexact=last_name)
            & Q(
                Q(date_of_birth=fields.get("date_of_birth"))
                | Q(date_of_birth__isnull=True)
            )
        ).exists():
            raise ValidationError(
                {"first_name": _("A possible duplicate beneficiary already exists.")},
                code="possible_beneficiary_duplicate",
            )
        reference = _reserve_reference(self.user, "beneficiary")
        beneficiary = Beneficiary(
            reference_number=reference.reference_number,
            status=BeneficiaryStatus.IDENTIFIED,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        if beneficiary.date_of_birth:
            from .validators import is_minor as _is_minor

            beneficiary.is_minor = _is_minor(beneficiary.date_of_birth)
        beneficiary.full_clean()
        beneficiary.save()
        _set_profile_taxonomies(beneficiary, taxonomy_fields)
        _confirm_reference(self.user, reference, beneficiary)
        BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=BeneficiaryStatus.IDENTIFIED,
            to_status=BeneficiaryStatus.IDENTIFIED,
            changed_by=self.user,
            reason="Beneficiary registered.",
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("beneficiary.created", beneficiary, self.user)
        return beneficiary

    @transaction.atomic
    def update(self, beneficiary: Beneficiary, **fields) -> Beneficiary:
        _require_permission(self.user, BENEFICIARIES_UPDATE)
        _require_record_access(self.user, beneficiary)
        beneficiary = Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in (
                "vulnerabilities",
                "inclusion_barriers",
                "disabilities",
                "skills",
                "interests",
                "needs",
            )
            if name in fields
        }
        disallowed = set(fields) - self.UPDATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported beneficiary fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        if fields.get("date_of_birth"):
            from .validators import is_minor as _is_minor

            fields["is_minor"] = _is_minor(fields["date_of_birth"])
        changed = []
        for name, value in fields.items():
            if getattr(beneficiary, name) != value:
                setattr(beneficiary, name, value)
                changed.append(name)
        if changed and "is_minor" not in fields and beneficiary.date_of_birth:
            from .validators import is_minor as _is_minor

            new_minor = _is_minor(beneficiary.date_of_birth)
            if new_minor != beneficiary.is_minor:
                beneficiary.is_minor = new_minor
                changed.append("is_minor")
        beneficiary.updated_by = self.user
        beneficiary.full_clean()
        beneficiary.save()
        _set_profile_taxonomies(beneficiary, taxonomy_fields)
        _log_event("beneficiary.updated", beneficiary, self.user, fields=changed)
        return beneficiary

    @transaction.atomic
    def change_status(
        self, beneficiary: Beneficiary, new_status: str, reason: str
    ) -> Beneficiary:
        _require_permission(self.user, BENEFICIARIES_UPDATE)
        _require_record_access(self.user, beneficiary)
        beneficiary = Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        old_status = beneficiary.status
        if new_status not in BENEFICIARY_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                _("Transition from %(old)s to %(new)s is not allowed.")
                % {"old": old_status, "new": new_status},
                code="invalid_beneficiary_transition",
            )
        if not reason.strip():
            raise ValidationError({"reason": _("A transition reason is required.")})
        if new_status in {
            BeneficiaryStatus.VERIFIED,
            BeneficiaryStatus.ELIGIBLE,
            BeneficiaryStatus.ENROLLED,
            BeneficiaryStatus.ACTIVE,
            BeneficiaryStatus.GRADUATED,
        }:
            _ensure_consent_for_status(beneficiary, new_status)
        if new_status == BeneficiaryStatus.VERIFIED:
            beneficiary.verification_date = timezone.localdate()
            beneficiary.verified_by = self.user
        elif new_status == BeneficiaryStatus.ENROLLED:
            beneficiary.enrolled_at = beneficiary.enrolled_at or timezone.localdate()
        elif new_status == BeneficiaryStatus.GRADUATED:
            beneficiary.graduated_at = timezone.localdate()
        elif new_status == BeneficiaryStatus.EXITED:
            beneficiary.exited_at = timezone.localdate()
        beneficiary.status = new_status
        beneficiary.updated_by = self.user
        beneficiary.full_clean()
        beneficiary.save()
        BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=old_status,
            to_status=new_status,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event(
            "beneficiary.status_changed",
            beneficiary,
            self.user,
            from_status=old_status,
            to_status=new_status,
        )
        return beneficiary

    @transaction.atomic
    def archive(self, beneficiary: Beneficiary, reason: str) -> Beneficiary:
        _require_permission(self.user, BENEFICIARIES_ARCHIVE)
        _require_record_access(self.user, beneficiary)
        beneficiary = Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        if beneficiary.is_archived:
            raise ValidationError(_("Beneficiary is already archived."))
        if not reason.strip():
            raise ValidationError({"reason": _("An archive reason is required.")})
        old_status = beneficiary.status
        beneficiary.status = BeneficiaryStatus.ARCHIVED
        beneficiary.is_archived = True
        beneficiary.archived_at = timezone.now()
        beneficiary.archived_by = self.user
        beneficiary.updated_by = self.user
        beneficiary.save()
        BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=old_status,
            to_status=BeneficiaryStatus.ARCHIVED,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("beneficiary.archived", beneficiary, self.user, reason=reason)
        return beneficiary

    @transaction.atomic
    def restore(self, beneficiary: Beneficiary, reason: str) -> Beneficiary:
        _require_permission(self.user, BENEFICIARIES_RESTORE)
        _require_record_access(self.user, beneficiary, include_archived=True)
        beneficiary = Beneficiary.all_objects.select_for_update().get(pk=beneficiary.pk)
        if not beneficiary.is_archived:
            raise ValidationError(_("Beneficiary is not archived."))
        beneficiary.is_archived = False
        beneficiary.archived_at = None
        beneficiary.archived_by = None
        beneficiary.status = BeneficiaryStatus.REGISTERED
        beneficiary.updated_by = self.user
        beneficiary.save()
        BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=BeneficiaryStatus.ARCHIVED,
            to_status=BeneficiaryStatus.REGISTERED,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("beneficiary.restored", beneficiary, self.user, reason=reason)
        return beneficiary


class GuardianService(BaseService):
    """Maintain guardians while enforcing one active primary guardian."""

    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> GuardianRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GUARDIANS)
        _require_record_access(self.user, beneficiary)
        Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        has_primary = GuardianRecord.objects.filter(
            beneficiary=beneficiary, is_primary=True, is_active=True
        ).exists()
        requested_primary = fields.pop("is_primary", not has_primary)
        if requested_primary:
            GuardianRecord.objects.filter(
                beneficiary=beneficiary, is_primary=True, is_active=True
            ).update(is_primary=False, updated_by=self.user)
        guardian = GuardianRecord(
            beneficiary=beneficiary,
            is_primary=requested_primary,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        guardian.full_clean()
        guardian.save()
        _log_event(
            "guardian.created", guardian, self.user, beneficiary_id=str(beneficiary.pk)
        )
        return guardian

    @transaction.atomic
    def set_primary(self, guardian: GuardianRecord) -> GuardianRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GUARDIANS)
        _require_record_access(self.user, guardian.beneficiary)
        guardian = GuardianRecord.objects.select_for_update().get(pk=guardian.pk)
        if not guardian.is_active:
            raise ValidationError(_("An inactive guardian cannot be primary."))
        GuardianRecord.objects.filter(
            beneficiary=guardian.beneficiary, is_primary=True, is_active=True
        ).exclude(pk=guardian.pk).update(is_primary=False, updated_by=self.user)
        guardian.is_primary = True
        guardian.updated_by = self.user
        guardian.full_clean()
        guardian.save()
        _log_event("guardian.primary_set", guardian, self.user)
        return guardian

    @transaction.atomic
    def deactivate(self, guardian: GuardianRecord) -> GuardianRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GUARDIANS)
        _require_record_access(self.user, guardian.beneficiary)
        guardian = GuardianRecord.objects.select_for_update().get(pk=guardian.pk)
        guardian.is_active = False
        guardian.is_primary = False
        guardian.valid_to = guardian.valid_to or timezone.localdate()
        guardian.updated_by = self.user
        guardian.full_clean()
        guardian.save()
        _log_event("guardian.deactivated", guardian, self.user)
        return guardian


class HouseholdService(BaseService):
    @transaction.atomic
    def create(self, **fields) -> BeneficiaryHousehold:
        _require_permission(self.user, BENEFICIARIES_MANAGE_HOUSEHOLDS)
        reference = _reserve_reference(self.user, "household")
        household = BeneficiaryHousehold(
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        household.full_clean()
        household.save()
        _confirm_reference(self.user, reference, household)
        _log_event("household.created", household, self.user)
        return household

    @transaction.atomic
    def add_member(
        self, household: BeneficiaryHousehold, beneficiary: Beneficiary, **fields
    ) -> HouseholdMember:
        _require_permission(self.user, BENEFICIARIES_MANAGE_HOUSEHOLDS)
        _require_record_access(self.user, beneficiary)
        household = BeneficiaryHousehold.objects.select_for_update().get(
            pk=household.pk
        )
        is_head = fields.pop("is_head", False)
        if is_head:
            HouseholdMember.objects.filter(household=household, is_head=True).update(
                is_head=False, updated_by=self.user
            )
        member = HouseholdMember(
            household=household,
            beneficiary=beneficiary,
            is_head=is_head,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        member.full_clean()
        member.save()
        if is_head:
            Beneficiary.objects.filter(pk=beneficiary.pk).update(
                household=household,
                is_household_head=True,
                updated_by=self.user,
            )
        else:
            Beneficiary.objects.filter(
                pk=beneficiary.pk, household__isnull=True
            ).update(household=household, updated_by=self.user)
        household.recalculate_member_count()
        _log_event("household.member_added", member, self.user)
        return member

    @transaction.atomic
    def remove_member(self, member: HouseholdMember, left_on=None) -> HouseholdMember:
        _require_permission(self.user, BENEFICIARIES_MANAGE_HOUSEHOLDS)
        _require_record_access(self.user, member.beneficiary)
        member = HouseholdMember.objects.select_for_update().get(pk=member.pk)
        member.is_active = False
        member.left_on = left_on or timezone.localdate()
        member.updated_by = self.user
        member.full_clean()
        member.save()
        if member.is_head:
            Beneficiary.objects.filter(pk=member.beneficiary_id).update(
                household=None, is_household_head=False, updated_by=self.user
            )
        member.household.recalculate_member_count()
        _log_event("household.member_removed", member, self.user)
        return member


class GroupService(BaseService):
    @transaction.atomic
    def create(self, **fields) -> BeneficiaryGroup:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GROUPS)
        reference = _reserve_reference(self.user, "group")
        group = BeneficiaryGroup(
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        group.full_clean()
        group.save()
        _confirm_reference(self.user, reference, group)
        _log_event("group.created", group, self.user)
        return group

    @transaction.atomic
    def add_member(
        self, group: BeneficiaryGroup, beneficiary: Beneficiary, **fields
    ) -> GroupMembership:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GROUPS)
        _require_record_access(self.user, beneficiary)
        group = BeneficiaryGroup.objects.select_for_update().get(pk=group.pk)
        if group.status not in {"FORMING", "ACTIVE"}:
            raise ValidationError(_("Only forming or active groups accept members."))
        membership = GroupMembership(
            group=group,
            beneficiary=beneficiary,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        membership.full_clean()
        membership.save()
        group.recalculate_member_count()
        _log_event("group.member_added", membership, self.user)
        return membership

    @transaction.atomic
    def remove_member(
        self, membership: GroupMembership, left_on=None
    ) -> GroupMembership:
        _require_permission(self.user, BENEFICIARIES_MANAGE_GROUPS)
        _require_record_access(self.user, membership.beneficiary)
        membership = GroupMembership.objects.select_for_update().get(pk=membership.pk)
        membership.is_active = False
        membership.left_on = left_on or timezone.localdate()
        membership.updated_by = self.user
        membership.full_clean()
        membership.save()
        membership.group.recalculate_member_count()
        _log_event("group.member_removed", membership, self.user)
        return membership


class EnrollmentService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> BeneficiaryEnrollment:
        _require_permission(self.user, BENEFICIARIES_MANAGE_ENROLLMENTS)
        _require_record_access(self.user, beneficiary)
        _ensure_consent_for_status(beneficiary, BeneficiaryStatus.ENROLLED)
        reference = _reserve_reference(self.user, "enrollment")
        enrollment = BeneficiaryEnrollment(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        enrollment.full_clean()
        enrollment.save()
        _confirm_reference(self.user, reference, enrollment)
        if (
            beneficiary.status
            in {BeneficiaryStatus.ELIGIBLE, BeneficiaryStatus.ENROLLED}
            and not beneficiary.enrolled_at
        ):
            Beneficiary.objects.filter(pk=beneficiary.pk).update(
                enrolled_at=timezone.localdate(), updated_by=self.user
            )
        _log_event("enrollment.created", enrollment, self.user)
        return enrollment

    @transaction.atomic
    def change_status(
        self, enrollment: BeneficiaryEnrollment, status: str, reason: str = ""
    ) -> BeneficiaryEnrollment:
        _require_permission(self.user, BENEFICIARIES_MANAGE_ENROLLMENTS)
        _require_record_access(self.user, enrollment.beneficiary)
        enrollment = BeneficiaryEnrollment.objects.select_for_update().get(
            pk=enrollment.pk
        )
        if status not in EnrollmentStatus.values:
            raise ValidationError(_("Invalid enrollment status."))
        if status in {EnrollmentStatus.COMPLETED, EnrollmentStatus.WITHDRAWN}:
            if not reason.strip():
                raise ValidationError({"reason": _("A reason is required.")})
            enrollment.exit_date = timezone.localdate()
        enrollment.status = status
        enrollment.updated_by = self.user
        enrollment.full_clean()
        enrollment.save()
        _log_event("enrollment.status_changed", enrollment, self.user, status=status)
        return enrollment


class ParticipationService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> BeneficiaryParticipation:
        _require_permission(self.user, BENEFICIARIES_MANAGE_PARTICIPATION)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "participation")
        participation = BeneficiaryParticipation(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        participation.full_clean()
        participation.save()
        _confirm_reference(self.user, reference, participation)
        _log_event("participation.recorded", participation, self.user)
        return participation


class AttendanceService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> AttendanceRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_ATTENDANCE)
        _require_record_access(self.user, beneficiary)
        attendance = AttendanceRecord(
            beneficiary=beneficiary,
            recorded_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        attendance.full_clean()
        attendance.save()
        _log_event("attendance.recorded", attendance, self.user)
        return attendance


class ServiceDeliveryService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> ServiceDeliveryRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SERVICES)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "service")
        service = ServiceDeliveryRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        service.full_clean()
        service.save()
        _confirm_reference(self.user, reference, service)
        _log_event("service_delivery.created", service, self.user)
        return service

    @transaction.atomic
    def mark_delivered(
        self, service: ServiceDeliveryRecord, outcome_notes: str = ""
    ) -> ServiceDeliveryRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SERVICES)
        _require_record_access(self.user, service.beneficiary)
        service = ServiceDeliveryRecord.objects.select_for_update().get(pk=service.pk)
        service.status = ServiceDeliveryStatus.DELIVERED
        service.delivered_at = timezone.now()
        service.delivered_by = self.user
        service.outcome_notes = outcome_notes
        service.updated_by = self.user
        service.full_clean()
        service.save()
        _log_event("service_delivery.delivered", service, self.user)
        return service


class ReferralService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> Referral:
        _require_permission(self.user, BENEFICIARIES_MANAGE_REFERRALS)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "referral")
        referral = Referral(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        referral.full_clean()
        referral.save()
        _confirm_reference(self.user, reference, referral)
        _log_event("referral.created", referral, self.user)
        return referral

    @transaction.atomic
    def change_status(
        self, referral: Referral, status: str, response_notes: str = ""
    ) -> Referral:
        _require_permission(self.user, BENEFICIARIES_MANAGE_REFERRALS)
        _require_record_access(self.user, referral.beneficiary)
        referral = Referral.objects.select_for_update().get(pk=referral.pk)
        if status not in ReferralStatus.values:
            raise ValidationError(_("Invalid referral status."))
        if referral.status in {ReferralStatus.CLOSED, ReferralStatus.CANCELLED}:
            raise ValidationError(_("Final referrals cannot be reopened."))
        referral.status = status
        referral.response_notes = response_notes or referral.response_notes
        if status in {ReferralStatus.COMPLETED, ReferralStatus.CLOSED}:
            referral.response_received = True
            referral.closed_on = timezone.localdate()
        referral.updated_by = self.user
        referral.full_clean()
        referral.save()
        _log_event("referral.status_changed", referral, self.user, status=status)
        return referral


class CaseNoteService(BaseService):
    @transaction.atomic
    def create(
        self, beneficiary: Beneficiary, title: str, content: str, **fields
    ) -> CaseNote:
        _require_permission(self.user, BENEFICIARIES_MANAGE_CASE_NOTES)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "case_note")
        note = CaseNote(
            beneficiary=beneficiary,
            title=title,
            content=content,
            reference_number=reference.reference_number,
            author=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        note.full_clean()
        note.save()
        _confirm_reference(self.user, reference, note)
        _log_event("case_note.created", note, self.user)
        return note


class FollowUpService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> FollowUpVisit:
        _require_permission(self.user, BENEFICIARIES_MANAGE_FOLLOW_UPS)
        _require_record_access(self.user, beneficiary)
        follow_up = FollowUpVisit(
            beneficiary=beneficiary,
            assigned_to=fields.pop("assigned_to", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        follow_up.full_clean()
        follow_up.save()
        _log_event("follow_up.created", follow_up, self.user)
        return follow_up

    @transaction.atomic
    def complete(
        self, follow_up: FollowUpVisit, summary: str = "", **outcomes
    ) -> FollowUpVisit:
        _require_permission(self.user, BENEFICIARIES_MANAGE_FOLLOW_UPS)
        _require_record_access(self.user, follow_up.beneficiary)
        follow_up = FollowUpVisit.objects.select_for_update().get(pk=follow_up.pk)
        if follow_up.status != FollowUpStatus.PLANNED:
            raise ValidationError(_("Only planned follow-ups can be completed."))
        for name in ("findings", "action_items", "next_follow_up_date"):
            if name in outcomes:
                setattr(follow_up, name, outcomes[name])
        follow_up.summary = summary
        follow_up.status = FollowUpStatus.COMPLETED
        follow_up.completed_on = timezone.localdate()
        follow_up.updated_by = self.user
        follow_up.full_clean()
        follow_up.save()
        _log_event("follow_up.completed", follow_up, self.user)
        return follow_up


class AssessmentService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> BeneficiaryAssessment:
        _require_permission(self.user, BENEFICIARIES_MANAGE_ASSESSMENTS)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "assessment")
        assessment = BeneficiaryAssessment(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            assessed_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        assessment.full_clean()
        assessment.save()
        _confirm_reference(self.user, reference, assessment)
        _log_event("assessment.created", assessment, self.user)
        return assessment

    @transaction.atomic
    def submit(self, assessment: BeneficiaryAssessment) -> BeneficiaryAssessment:
        _require_permission(self.user, BENEFICIARIES_SUBMIT)
        _require_record_access(self.user, assessment.beneficiary)
        assessment = BeneficiaryAssessment.objects.select_for_update().get(
            pk=assessment.pk
        )
        if assessment.status != AssessmentStatus.DRAFT:
            raise ValidationError(_("Only draft assessments can be submitted."))
        if not assessment.summary.strip() and not assessment.recommendation.strip():
            raise ValidationError(_("A summary or recommendation is required."))
        assessment.status = AssessmentStatus.SUBMITTED
        assessment.submitted_by = self.user
        assessment.submitted_at = timezone.now()
        assessment.updated_by = self.user
        assessment.save()
        _log_event("assessment.submitted", assessment, self.user)
        return assessment

    @transaction.atomic
    def approve(self, assessment: BeneficiaryAssessment) -> BeneficiaryAssessment:
        _require_permission(self.user, BENEFICIARIES_APPROVE)
        _require_record_access(self.user, assessment.beneficiary)
        assessment = BeneficiaryAssessment.objects.select_for_update().get(
            pk=assessment.pk
        )
        if assessment.status != AssessmentStatus.SUBMITTED:
            raise ValidationError(_("Only submitted assessments can be approved."))
        if assessment.created_by_id == self.user.pk:
            raise ValidationError(
                _("Assessment creators cannot approve their own assessments."),
                code="beneficiary_assessment_self_approval",
            )
        assessment.status = AssessmentStatus.APPROVED
        assessment.approved_by = self.user
        assessment.approved_at = timezone.now()
        assessment.updated_by = self.user
        assessment.save()
        _log_event("assessment.approved", assessment, self.user)
        return assessment


class SupportPlanService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> SupportPlan:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SUPPORT_PLANS)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "support_plan")
        plan = SupportPlan(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            support_coordinator=fields.pop("support_coordinator", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        plan.full_clean()
        plan.save()
        _confirm_reference(self.user, reference, plan)
        _log_event("support_plan.created", plan, self.user)
        return plan

    @transaction.atomic
    def activate(self, plan: SupportPlan) -> SupportPlan:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SUPPORT_PLANS)
        _require_record_access(self.user, plan.beneficiary)
        plan = SupportPlan.objects.select_for_update().get(pk=plan.pk)
        if plan.status != PlanStatus.DRAFT:
            raise ValidationError(_("Only draft plans can be activated."))
        if plan.start_date > timezone.localdate():
            raise ValidationError(_("The plan start date is still in the future."))
        plan.status = PlanStatus.ACTIVE
        plan.updated_by = self.user
        plan.save()
        _log_event("support_plan.activated", plan, self.user)
        return plan


class ConsentService(BaseService):
    @transaction.atomic
    def record(
        self,
        beneficiary: Beneficiary,
        *,
        consent_type: str,
        provided_by: str,
        **fields,
    ) -> ConsentRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_CONSENT)
        _require_record_access(self.user, beneficiary)
        beneficiary = Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        status = fields.pop("status", ConsentStatus.GRANTED)
        is_assent = fields.pop("is_assent", False)
        if beneficiary.is_minor and not is_assent and "relationship" not in fields:
            raise ValidationError(
                {"relationship": _("A guardian relationship is required for minors.")}
            )
        reference = _reserve_reference(self.user, "consent")
        consent = ConsentRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            consent_type=consent_type,
            provided_by=provided_by,
            status=status,
            is_assent=is_assent,
            recorded_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        consent.full_clean()
        consent.save()
        _confirm_reference(self.user, reference, consent)
        beneficiary.consent_status = status
        beneficiary.consent_recorded_at = timezone.now()
        beneficiary.consent_version = consent.form_version
        beneficiary.consent_expiry_date = consent.valid_to
        if is_assent:
            beneficiary.assent_recorded = True
            beneficiary.assent_recorded_at = timezone.now()
            beneficiary.assent_version = consent.form_version
        beneficiary.updated_by = self.user
        beneficiary.full_clean()
        beneficiary.save()
        _log_event(
            "consent.recorded",
            consent,
            self.user,
            status=status,
            is_assent=is_assent,
        )
        return consent

    @transaction.atomic
    def withdraw(self, consent: ConsentRecord, reason: str) -> ConsentRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_CONSENT)
        _require_record_access(self.user, consent.beneficiary)
        consent = ConsentRecord.objects.select_for_update().get(pk=consent.pk)
        if consent.status != ConsentStatus.GRANTED:
            raise ValidationError(_("Only granted consent can be withdrawn."))
        if not reason.strip():
            raise ValidationError({"reason": _("A withdrawal reason is required.")})
        consent.status = ConsentStatus.WITHDRAWN
        consent.withdrawal_reason = reason
        consent.updated_by = self.user
        consent.save(update_fields=["status", "withdrawal_reason", "updated_by"])
        Beneficiary.objects.filter(pk=consent.beneficiary_id).update(
            consent_status=ConsentStatus.WITHDRAWN, updated_by=self.user
        )
        _log_event("consent.withdrawn", consent, self.user, reason=reason)
        return consent


class SafeguardingService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> SafeguardingRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SAFEGUARDING)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "safeguarding")
        record = SafeguardingRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            reviewed_by=fields.pop("reviewed_by", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        record.full_clean()
        record.save()
        _confirm_reference(self.user, reference, record)
        Beneficiary.objects.filter(pk=beneficiary.pk).update(
            safeguarding_concerns=True,
            safeguarding_notes=record.description[:2000],
            updated_by=self.user,
        )
        _log_event("safeguarding.recorded", record, self.user)
        return record

    @transaction.atomic
    def change_status(
        self, record: SafeguardingRecord, status: str, notes: str = ""
    ) -> SafeguardingRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_SAFEGUARDING)
        _require_record_access(self.user, record.beneficiary)
        record = SafeguardingRecord.objects.select_for_update().get(pk=record.pk)
        if status not in SafeguardingStatus.values:
            raise ValidationError(_("Invalid safeguarding status."))
        if record.status in {SafeguardingStatus.RESOLVED, SafeguardingStatus.CLOSED}:
            raise ValidationError(_("Closed safeguarding records are immutable."))
        record.status = status
        record.updated_by = self.user
        update_fields = ["status", "updated_by"]
        if status in {SafeguardingStatus.RESOLVED, SafeguardingStatus.CLOSED}:
            record.resolved_on = timezone.localdate()
            record.outcome = notes or record.outcome
            update_fields.extend(["resolved_on", "outcome"])
        if notes and status == SafeguardingStatus.INVESTIGATING:
            record.investigation_notes = notes
            update_fields.append("investigation_notes")
        record.save(update_fields=update_fields)
        _log_event("safeguarding.status_changed", record, self.user, status=status)
        return record


class OutcomeService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> OutcomeRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_OUTCOMES)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "outcome")
        outcome = OutcomeRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            recorded_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        outcome.full_clean()
        outcome.save()
        _confirm_reference(self.user, reference, outcome)
        _log_event("outcome.recorded", outcome, self.user)
        return outcome


class ExitService(BaseService):
    @transaction.atomic
    def record(
        self,
        beneficiary: Beneficiary,
        *,
        exit_status: str,
        reason: str,
        **fields,
    ) -> ExitRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_EXITS)
        _require_record_access(self.user, beneficiary)
        beneficiary = Beneficiary.objects.select_for_update().get(pk=beneficiary.pk)
        old_status = beneficiary.status
        if old_status in {BeneficiaryStatus.GRADUATED, BeneficiaryStatus.EXITED}:
            raise ValidationError(_("Beneficiary has already exited."))
        reference = _reserve_reference(self.user, "exit")
        exit_record = ExitRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            exit_status=exit_status,
            reason=reason,
            conducted_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        exit_record.full_clean()
        exit_record.save()
        _confirm_reference(self.user, reference, exit_record)
        if (
            old_status == BeneficiaryStatus.ACTIVE
            and exit_status == ExitStatus.GRADUATED
        ):
            beneficiary.status = BeneficiaryStatus.GRADUATED
            beneficiary.graduated_at = exit_record.exit_date
        else:
            beneficiary.status = BeneficiaryStatus.EXITED
            beneficiary.exited_at = exit_record.exit_date
        beneficiary.updated_by = self.user
        beneficiary.full_clean()
        beneficiary.save()
        BeneficiaryStatusHistory.objects.create(
            beneficiary=beneficiary,
            from_status=old_status,
            to_status=beneficiary.status,
            changed_by=self.user,
            reason=f"Exit recorded: {exit_status} - {reason}",
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event(
            "exit.recorded",
            exit_record,
            self.user,
            exit_status=exit_status,
        )
        return exit_record


class DocumentService(BaseService):
    @transaction.atomic
    def upload(
        self, beneficiary: Beneficiary, *, title: str, file, **fields
    ) -> BeneficiaryDocument:
        _require_permission(self.user, BENEFICIARIES_MANAGE_DOCUMENTS)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "document")
        document = BeneficiaryDocument(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            title=title,
            file=file,
            uploaded_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        document.full_clean()
        document.save()
        document.checksum = document.compute_checksum()
        document.save(update_fields=["checksum"])
        _confirm_reference(self.user, reference, document)
        _log_event("document.uploaded", document, self.user)
        return document

    @transaction.atomic
    def archive(self, document: BeneficiaryDocument) -> BeneficiaryDocument:
        _require_permission(self.user, BENEFICIARIES_MANAGE_DOCUMENTS)
        _require_record_access(self.user, document.beneficiary)
        document = BeneficiaryDocument.objects.select_for_update().get(pk=document.pk)
        document.status = "ARCHIVED"
        document.updated_by = self.user
        document.save()
        _log_event("document.archived", document, self.user)
        return document


class CommunicationService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> BeneficiaryCommunication:
        _require_permission(self.user, BENEFICIARIES_MANAGE_CASE_NOTES)
        _require_record_access(self.user, beneficiary)
        communication = BeneficiaryCommunication(
            beneficiary=beneficiary,
            responsible_officer=fields.pop("responsible_officer", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        communication.full_clean()
        communication.save()
        _log_event("communication.recorded", communication, self.user)
        return communication


class TransferService(BaseService):
    @transaction.atomic
    def create(self, beneficiary: Beneficiary, **fields) -> TransferRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_TRANSFERS)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "transfer")
        transfer = TransferRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        transfer.full_clean()
        transfer.save()
        _confirm_reference(self.user, reference, transfer)
        _log_event("transfer.created", transfer, self.user)
        return transfer

    @transaction.atomic
    def complete(
        self, transfer: TransferRecord, handover_notes: str = ""
    ) -> TransferRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_TRANSFERS)
        _require_record_access(self.user, transfer.beneficiary)
        transfer = TransferRecord.objects.select_for_update().get(pk=transfer.pk)
        if transfer.status != TransferStatus.PENDING:
            raise ValidationError(_("Only pending transfers can be completed."))
        transfer.status = TransferStatus.COMPLETED
        transfer.approved_by = self.user
        transfer.approved_at = timezone.now()
        transfer.completed_on = timezone.localdate()
        transfer.handover_notes = handover_notes
        transfer.updated_by = self.user
        transfer.save()
        _log_event("transfer.completed", transfer, self.user)
        return transfer


class FeedbackService(BaseService):
    @transaction.atomic
    def record(self, beneficiary: Beneficiary, **fields) -> FeedbackRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_FEEDBACK)
        _require_record_access(self.user, beneficiary)
        reference = _reserve_reference(self.user, "feedback")
        feedback = FeedbackRecord(
            beneficiary=beneficiary,
            reference_number=reference.reference_number,
            received_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        feedback.full_clean()
        feedback.save()
        _confirm_reference(self.user, reference, feedback)
        _log_event("feedback.recorded", feedback, self.user)
        return feedback

    @transaction.atomic
    def respond(
        self, feedback: FeedbackRecord, response: str, *, close: bool = False
    ) -> FeedbackRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_FEEDBACK)
        _require_record_access(self.user, feedback.beneficiary)
        feedback = FeedbackRecord.objects.select_for_update().get(pk=feedback.pk)
        feedback.response = response
        feedback.status = "CLOSED" if close else "ACTIONED"
        feedback.resolved_on = timezone.localdate() if close else None
        feedback.updated_by = self.user
        feedback.full_clean()
        feedback.save()
        _log_event("feedback.responded", feedback, self.user, close=close)
        return feedback


class DuplicateService(BaseService):
    @transaction.atomic
    def review(
        self,
        beneficiary: Beneficiary,
        candidate: Beneficiary,
        *,
        review_status: str,
        decision_notes: str = "",
        match_score: Decimal = Decimal("0.00"),
        matching_fields: list | None = None,
    ) -> DuplicateReviewRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_DUPLICATES)
        _require_record_access(self.user, beneficiary)
        _require_record_access(self.user, candidate)
        if beneficiary.pk == candidate.pk:
            raise ValidationError(_("A record cannot be its own duplicate."))
        review, created = DuplicateReviewRecord.objects.get_or_create(
            beneficiary=beneficiary,
            duplicate_candidate=candidate,
            defaults={
                "review_status": review_status,
                "decision_notes": decision_notes,
                "match_score": match_score,
                "matching_fields": matching_fields or [],
                "reviewed_by": self.user,
                "reviewed_at": timezone.now(),
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        if not created:
            review.review_status = review_status
            review.decision_notes = decision_notes
            review.match_score = match_score
            review.matching_fields = matching_fields or review.matching_fields
            review.reviewed_by = self.user
            review.reviewed_at = timezone.now()
            review.updated_by = self.user
            review.save()
        _log_event(
            "duplicate.reviewed",
            review,
            self.user,
            review_status=review_status,
        )
        return review

    @transaction.atomic
    def merge(
        self, review: DuplicateReviewRecord, merged_into: Beneficiary
    ) -> DuplicateReviewRecord:
        _require_permission(self.user, BENEFICIARIES_MANAGE_DUPLICATES)
        _require_record_access(self.user, merged_into)
        review = DuplicateReviewRecord.objects.select_for_update().get(pk=review.pk)
        if review.review_status != DuplicateReviewStatus.CONFIRMED_DUPLICATE:
            raise ValidationError(_("Only confirmed duplicates can be merged."))
        duplicate = review.duplicate_candidate
        if merged_into.pk != review.beneficiary.pk and merged_into.pk != duplicate.pk:
            raise ValidationError(
                _("The merge target is not part of this duplicate pair.")
            )
        duplicate.duplicate_of = merged_into
        duplicate.duplicate_review_status = DuplicateReviewStatus.MERGED
        duplicate.updated_by = self.user
        duplicate.save()
        review.review_status = DuplicateReviewStatus.MERGED
        review.merged_into = merged_into
        review.merged_at = timezone.now()
        review.updated_by = self.user
        review.save()
        _log_event(
            "duplicate.merged",
            review,
            self.user,
            merged_into=str(merged_into.pk),
        )
        return review
