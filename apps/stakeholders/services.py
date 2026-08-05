"""Permission-checked transactional services for stakeholder management."""

from __future__ import annotations

import hashlib
import logging
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import ClassVar

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
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
    ASSESSMENT_FORMULA_VERSION,
    ASSESSMENT_HIGH_THRESHOLD,
    REFERENCE_SCHEME_CODES,
    ActionStatus,
    AgreementStatus,
    AssessmentClassification,
    CommitmentStatus,
    ContributionStatus,
    DocumentStatus,
    DueDiligenceStatus,
    EngagementStatus,
    NoteStatus,
    ReferenceDataKind,
    RenewalStatus,
    ReviewStatus,
    RiskStatus,
    StakeholderStatus,
)
from .models import (
    Stakeholder,
    StakeholderAccessGrant,
    StakeholderActionItem,
    StakeholderAgreement,
    StakeholderAgreementRenewal,
    StakeholderAgreementVersion,
    StakeholderAssessment,
    StakeholderCommitment,
    StakeholderCommunication,
    StakeholderConflictOfInterest,
    StakeholderContact,
    StakeholderContribution,
    StakeholderDocument,
    StakeholderDueDiligence,
    StakeholderEngagement,
    StakeholderEngagementPlan,
    StakeholderNote,
    StakeholderNoteVersion,
    StakeholderPerformanceDimension,
    StakeholderPerformanceReview,
    StakeholderPerformanceScore,
    StakeholderReferenceData,
    StakeholderRisk,
    StakeholderStatusHistory,
)
from .permissions import (
    PARTNERS_ANALYTICS,
    PARTNERS_APPROVE_AGREEMENTS,
    PARTNERS_ARCHIVE,
    PARTNERS_ASSESS,
    PARTNERS_CREATE,
    PARTNERS_MANAGE,
    PARTNERS_MANAGE_ACCESS,
    PARTNERS_MANAGE_ACTIONS,
    PARTNERS_MANAGE_AGREEMENTS,
    PARTNERS_MANAGE_COMMITMENTS,
    PARTNERS_MANAGE_COMMUNICATIONS,
    PARTNERS_MANAGE_CONTACTS,
    PARTNERS_MANAGE_CONTRIBUTIONS,
    PARTNERS_MANAGE_DOCUMENTS,
    PARTNERS_MANAGE_DUE_DILIGENCE,
    PARTNERS_MANAGE_ENGAGEMENTS,
    PARTNERS_MANAGE_NOTES,
    PARTNERS_MANAGE_PERFORMANCE,
    PARTNERS_MANAGE_RISK,
    PARTNERS_RESTORE,
    PARTNERS_REVIEW_AGREEMENTS,
    PARTNERS_UPDATE,
)
from .selectors import user_can_access_stakeholder, visible_stakeholders

logger = logging.getLogger(__name__)
TWO_PLACES = Decimal("0.01")


STAKEHOLDER_TRANSITIONS: dict[str, set[str]] = {
    StakeholderStatus.PROSPECT: {
        StakeholderStatus.IDENTIFIED,
        StakeholderStatus.INACTIVE,
    },
    StakeholderStatus.IDENTIFIED: {
        StakeholderStatus.PROSPECT,
        StakeholderStatus.UNDER_ASSESSMENT,
        StakeholderStatus.CONTACTED,
    },
    StakeholderStatus.UNDER_ASSESSMENT: {
        StakeholderStatus.CONTACTED,
        StakeholderStatus.PROSPECT,
        StakeholderStatus.SUSPENDED,
    },
    StakeholderStatus.CONTACTED: {
        StakeholderStatus.ENGAGED,
        StakeholderStatus.DORMANT,
        StakeholderStatus.SUSPENDED,
    },
    StakeholderStatus.ENGAGED: {
        StakeholderStatus.NEGOTIATING,
        StakeholderStatus.ACTIVE,
        StakeholderStatus.DORMANT,
        StakeholderStatus.SUSPENDED,
    },
    StakeholderStatus.NEGOTIATING: {
        StakeholderStatus.PENDING_AGREEMENT,
        StakeholderStatus.ENGAGED,
        StakeholderStatus.CLOSED,
    },
    StakeholderStatus.PENDING_AGREEMENT: {
        StakeholderStatus.ACTIVE,
        StakeholderStatus.NEGOTIATING,
        StakeholderStatus.CLOSED,
    },
    StakeholderStatus.ACTIVE: {
        StakeholderStatus.DORMANT,
        StakeholderStatus.INACTIVE,
        StakeholderStatus.SUSPENDED,
        StakeholderStatus.COMPLETED,
        StakeholderStatus.CLOSED,
    },
    StakeholderStatus.DORMANT: {
        StakeholderStatus.ENGAGED,
        StakeholderStatus.ACTIVE,
        StakeholderStatus.CLOSED,
    },
    StakeholderStatus.INACTIVE: {
        StakeholderStatus.ACTIVE,
        StakeholderStatus.CLOSED,
    },
    StakeholderStatus.SUSPENDED: {
        StakeholderStatus.ACTIVE,
        StakeholderStatus.INACTIVE,
        StakeholderStatus.CLOSED,
        StakeholderStatus.BLACKLISTED,
    },
    StakeholderStatus.COMPLETED: {StakeholderStatus.CLOSED},
    StakeholderStatus.CLOSED: set(),
    StakeholderStatus.BLACKLISTED: set(),
    StakeholderStatus.ARCHIVED: set(),
}

AGREEMENT_TRANSITIONS: dict[str, set[str]] = {
    AgreementStatus.DRAFT: {AgreementStatus.UNDER_REVIEW, AgreementStatus.ARCHIVED},
    AgreementStatus.UNDER_REVIEW: {
        AgreementStatus.RETURNED,
        AgreementStatus.PENDING_APPROVAL,
    },
    AgreementStatus.RETURNED: {
        AgreementStatus.DRAFT,
        AgreementStatus.UNDER_REVIEW,
    },
    AgreementStatus.PENDING_APPROVAL: {
        AgreementStatus.RETURNED,
        AgreementStatus.APPROVED,
    },
    AgreementStatus.APPROVED: {
        AgreementStatus.PENDING_SIGNATURE,
        AgreementStatus.RETURNED,
    },
    AgreementStatus.PENDING_SIGNATURE: {
        AgreementStatus.ACTIVE,
        AgreementStatus.RETURNED,
    },
    AgreementStatus.ACTIVE: {
        AgreementStatus.EXPIRING,
        AgreementStatus.EXPIRED,
        AgreementStatus.COMPLETED,
        AgreementStatus.TERMINATED,
        AgreementStatus.RENEWED,
    },
    AgreementStatus.EXPIRING: {
        AgreementStatus.ACTIVE,
        AgreementStatus.EXPIRED,
        AgreementStatus.RENEWED,
        AgreementStatus.TERMINATED,
    },
    AgreementStatus.EXPIRED: {
        AgreementStatus.RENEWED,
        AgreementStatus.ARCHIVED,
    },
    AgreementStatus.TERMINATED: {AgreementStatus.ARCHIVED},
    AgreementStatus.COMPLETED: {AgreementStatus.ARCHIVED, AgreementStatus.RENEWED},
    AgreementStatus.RENEWED: {AgreementStatus.ARCHIVED},
    AgreementStatus.ARCHIVED: set(),
}


def _require_permission(user, permission_code: str) -> None:
    """Check RBAC for every write, allowing the module-wide manager override."""
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(_("An authenticated actor is required."))
    if not (
        user_has_permission(user, permission_code)
        or user_has_permission(user, PARTNERS_MANAGE)
    ):
        raise PermissionDenied(_("Permission denied for this stakeholder action."))


def _require_record_access(user, stakeholder, *, include_archived=False) -> None:
    if not user_can_access_stakeholder(
        user, stakeholder, include_archived=include_archived
    ):
        raise PermissionDenied(
            _("This stakeholder record is outside your access scope.")
        )


def _log_event(action: str, instance, actor, **details) -> None:
    """Temporary structured Phase 10 adapter until the central audit app exists."""
    logger.info(
        "stakeholder_domain_event",
        extra={
            "stakeholder_event": {
                "action": action,
                "entity_type": type(instance).__name__,
                "entity_id": str(instance.pk),
                "actor_id": str(getattr(actor, "pk", "")),
                **details,
            }
        },
    )


def _reserve_reference(actor, scheme_key: str):
    scheme_code = REFERENCE_SCHEME_CODES[scheme_key]
    return ReferenceNumberService(user=actor).execute(
        module=ReferenceModules.PARTNERS,
        record_type=scheme_code,
        scheme_code=scheme_code,
        notes=f"Phase 14 {scheme_code} reference reservation.",
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


def _set_profile_taxonomies(stakeholder: Stakeholder, fields: dict) -> None:
    for field_name, expected_kind in (
        ("categories", ReferenceDataKind.CATEGORY),
        ("sectors", ReferenceDataKind.SECTOR),
        ("focus_areas", ReferenceDataKind.FOCUS_AREA),
        ("sdgs", ReferenceDataKind.SDG),
    ):
        if field_name in fields:
            values = _validate_reference_values(
                fields.pop(field_name), expected_kind, field_name
            )
            getattr(stakeholder, field_name).set(values)


class StakeholderService(BaseService):
    """Create, update, transition, archive, and restore stakeholder profiles."""

    CREATE_FIELDS: ClassVar[set[str]] = {
        field.name
        for field in Stakeholder._meta.fields
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
            "verified_at",
            "verified_by",
        }
    }
    UPDATE_FIELDS: ClassVar[set[str]] = set(CREATE_FIELDS)

    @transaction.atomic
    def create(self, **fields) -> Stakeholder:
        _require_permission(self.user, PARTNERS_CREATE)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in ("categories", "sectors", "focus_areas", "sdgs")
            if name in fields
        }
        disallowed = set(fields) - self.CREATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported stakeholder fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        legal_name = str(fields.get("legal_name", "")).strip()
        registration_number = str(fields.get("registration_number", "")).strip()
        duplicate_filter = Q(legal_name__iexact=legal_name)
        if registration_number:
            duplicate_filter |= Q(registration_number__iexact=registration_number)
        if legal_name and Stakeholder.all_objects.filter(duplicate_filter).exists():
            raise ValidationError(
                {"legal_name": _("A possible duplicate stakeholder already exists.")},
                code="possible_stakeholder_duplicate",
            )
        reference = _reserve_reference(self.user, "stakeholder")
        stakeholder = Stakeholder(
            reference_number=reference.reference_number,
            status=StakeholderStatus.PROSPECT,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        stakeholder.full_clean()
        stakeholder.save()
        _set_profile_taxonomies(stakeholder, taxonomy_fields)
        _confirm_reference(self.user, reference, stakeholder)
        StakeholderStatusHistory.objects.create(
            stakeholder=stakeholder,
            from_status=StakeholderStatus.PROSPECT,
            to_status=StakeholderStatus.PROSPECT,
            changed_by=self.user,
            reason="Stakeholder registered.",
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("stakeholder.created", stakeholder, self.user)
        return stakeholder

    @transaction.atomic
    def update(self, stakeholder: Stakeholder, **fields) -> Stakeholder:
        _require_permission(self.user, PARTNERS_UPDATE)
        _require_record_access(self.user, stakeholder)
        stakeholder = Stakeholder.objects.select_for_update().get(pk=stakeholder.pk)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in ("categories", "sectors", "focus_areas", "sdgs")
            if name in fields
        }
        disallowed = set(fields) - self.UPDATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported stakeholder fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        changed = []
        for name, value in fields.items():
            if getattr(stakeholder, name) != value:
                setattr(stakeholder, name, value)
                changed.append(name)
        stakeholder.updated_by = self.user
        stakeholder.full_clean()
        stakeholder.save()
        _set_profile_taxonomies(stakeholder, taxonomy_fields)
        _log_event("stakeholder.updated", stakeholder, self.user, fields=changed)
        return stakeholder

    @transaction.atomic
    def change_status(
        self, stakeholder: Stakeholder, new_status: str, reason: str
    ) -> Stakeholder:
        _require_permission(self.user, PARTNERS_UPDATE)
        _require_record_access(self.user, stakeholder)
        stakeholder = Stakeholder.objects.select_for_update().get(pk=stakeholder.pk)
        old_status = stakeholder.status
        if new_status not in STAKEHOLDER_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                _("Transition from %(old)s to %(new)s is not allowed.")
                % {"old": old_status, "new": new_status},
                code="invalid_stakeholder_transition",
            )
        if not reason.strip():
            raise ValidationError({"reason": _("A transition reason is required.")})
        if new_status == StakeholderStatus.ACTIVE:
            stakeholder.verified_at = stakeholder.verified_at or timezone.now()
            stakeholder.verified_by = stakeholder.verified_by or self.user
        stakeholder.status = new_status
        stakeholder.updated_by = self.user
        stakeholder.full_clean()
        stakeholder.save()
        StakeholderStatusHistory.objects.create(
            stakeholder=stakeholder,
            from_status=old_status,
            to_status=new_status,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event(
            "stakeholder.status_changed",
            stakeholder,
            self.user,
            from_status=old_status,
            to_status=new_status,
        )
        return stakeholder

    @transaction.atomic
    def archive(self, stakeholder: Stakeholder, reason: str) -> Stakeholder:
        _require_permission(self.user, PARTNERS_ARCHIVE)
        _require_record_access(self.user, stakeholder)
        stakeholder = Stakeholder.objects.select_for_update().get(pk=stakeholder.pk)
        if stakeholder.is_archived:
            raise ValidationError(_("Stakeholder is already archived."))
        if not reason.strip():
            raise ValidationError({"reason": _("An archive reason is required.")})
        old_status = stakeholder.status
        stakeholder.status = StakeholderStatus.ARCHIVED
        stakeholder.is_archived = True
        stakeholder.archived_at = timezone.now()
        stakeholder.archived_by = self.user
        stakeholder.updated_by = self.user
        stakeholder.save()
        StakeholderStatusHistory.objects.create(
            stakeholder=stakeholder,
            from_status=old_status,
            to_status=StakeholderStatus.ARCHIVED,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("stakeholder.archived", stakeholder, self.user, reason=reason)
        return stakeholder

    @transaction.atomic
    def restore(self, stakeholder: Stakeholder, reason: str) -> Stakeholder:
        _require_permission(self.user, PARTNERS_RESTORE)
        _require_record_access(self.user, stakeholder, include_archived=True)
        stakeholder = Stakeholder.all_objects.select_for_update().get(pk=stakeholder.pk)
        if not stakeholder.is_archived:
            raise ValidationError(_("Stakeholder is not archived."))
        stakeholder.is_archived = False
        stakeholder.archived_at = None
        stakeholder.archived_by = None
        stakeholder.status = StakeholderStatus.INACTIVE
        stakeholder.updated_by = self.user
        stakeholder.save()
        StakeholderStatusHistory.objects.create(
            stakeholder=stakeholder,
            from_status=StakeholderStatus.ARCHIVED,
            to_status=StakeholderStatus.INACTIVE,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("stakeholder.restored", stakeholder, self.user, reason=reason)
        return stakeholder


class StakeholderContactService(BaseService):
    """Maintain private contacts while enforcing one active primary contact."""

    @transaction.atomic
    def create(self, stakeholder: Stakeholder, **fields) -> StakeholderContact:
        _require_permission(self.user, PARTNERS_MANAGE_CONTACTS)
        _require_record_access(self.user, stakeholder)
        Stakeholder.objects.select_for_update().get(pk=stakeholder.pk)
        has_primary = StakeholderContact.objects.filter(
            stakeholder=stakeholder, is_primary=True, is_active=True
        ).exists()
        requested_primary = fields.pop("is_primary", not has_primary)
        if requested_primary:
            StakeholderContact.objects.filter(
                stakeholder=stakeholder, is_primary=True, is_active=True
            ).update(is_primary=False, updated_by=self.user)
        contact = StakeholderContact(
            stakeholder=stakeholder,
            is_primary=requested_primary,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        contact.full_clean()
        contact.save()
        _log_event(
            "contact.created", contact, self.user, stakeholder_id=str(stakeholder.pk)
        )
        return contact

    @transaction.atomic
    def set_primary(self, contact: StakeholderContact) -> StakeholderContact:
        _require_permission(self.user, PARTNERS_MANAGE_CONTACTS)
        _require_record_access(self.user, contact.stakeholder)
        contact = StakeholderContact.objects.select_for_update().get(pk=contact.pk)
        if not contact.is_active:
            raise ValidationError(_("An inactive contact cannot be primary."))
        StakeholderContact.objects.filter(
            stakeholder=contact.stakeholder, is_primary=True, is_active=True
        ).exclude(pk=contact.pk).update(is_primary=False, updated_by=self.user)
        contact.is_primary = True
        contact.updated_by = self.user
        contact.full_clean()
        contact.save()
        _log_event("contact.primary_set", contact, self.user)
        return contact

    @transaction.atomic
    def deactivate(self, contact: StakeholderContact) -> StakeholderContact:
        _require_permission(self.user, PARTNERS_MANAGE_CONTACTS)
        _require_record_access(self.user, contact.stakeholder)
        contact = StakeholderContact.objects.select_for_update().get(pk=contact.pk)
        contact.is_active = False
        contact.is_primary = False
        contact.valid_to = contact.valid_to or timezone.localdate()
        contact.updated_by = self.user
        contact.full_clean()
        contact.save()
        _log_event("contact.deactivated", contact, self.user)
        return contact


def calculate_assessment_matrix(**scores) -> dict:
    """Return transparent matrix classification without imputing missing values."""
    score_names = (
        "influence_score",
        "interest_score",
        "power_score",
        "impact_score",
        "strategic_importance_score",
    )
    values = {name: scores.get(name) for name in score_names}
    missing = [name for name, value in values.items() if value is None]
    present: list[Decimal] = [
        Decimal(str(value)) for value in values.values() if value is not None
    ]
    average = (
        (sum(present, Decimal("0")) / len(present)).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        if present
        else None
    )
    completeness = Decimal(100 * len(present) / len(score_names)).quantize(
        TWO_PLACES, rounding=ROUND_HALF_UP
    )
    influence = values["influence_score"]
    interest = values["interest_score"]
    if influence is None or interest is None:
        classification = AssessmentClassification.INSUFFICIENT_DATA
        explanation = (
            "Classification requires influence_score and interest_score; missing "
            + ", ".join(
                name
                for name in ("influence_score", "interest_score")
                if values[name] is None
            )
            + ". No values were imputed."
        )
    elif (
        influence >= ASSESSMENT_HIGH_THRESHOLD and interest >= ASSESSMENT_HIGH_THRESHOLD
    ):
        classification = AssessmentClassification.MANAGE_CLOSELY
        explanation = "Influence and interest meet the high threshold; manage closely."
    elif influence >= ASSESSMENT_HIGH_THRESHOLD:
        classification = AssessmentClassification.KEEP_SATISFIED
        explanation = "Influence is high and interest is low; keep satisfied."
    elif interest >= ASSESSMENT_HIGH_THRESHOLD:
        classification = AssessmentClassification.KEEP_INFORMED
        explanation = "Influence is low and interest is high; keep informed."
    else:
        classification = AssessmentClassification.MONITOR
        explanation = "Influence and interest are below the high threshold; monitor."
    return {
        "average_score": average,
        "completeness_percentage": completeness,
        "classification": classification,
        "missing_fields": missing,
        "matrix_explanation": (
            f"{explanation} High means >= {ASSESSMENT_HIGH_THRESHOLD}; "
            "average uses only supplied scores."
        ),
        "formula_version": ASSESSMENT_FORMULA_VERSION,
    }


class StakeholderAssessmentService(BaseService):
    @transaction.atomic
    def record(self, stakeholder: Stakeholder, **scores) -> StakeholderAssessment:
        _require_permission(self.user, PARTNERS_ASSESS)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "assessment")
        calculated = calculate_assessment_matrix(**scores)
        assessment = StakeholderAssessment(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            assessed_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **scores,
            **calculated,
        )
        assessment.full_clean()
        assessment.save()
        _confirm_reference(self.user, reference, assessment)
        _log_event(
            "assessment.recorded",
            assessment,
            self.user,
            classification=assessment.classification,
            missing_fields=assessment.missing_fields,
        )
        return assessment


class StakeholderEngagementService(BaseService):
    @transaction.atomic
    def create_plan(
        self, stakeholder: Stakeholder, **fields
    ) -> StakeholderEngagementPlan:
        _require_permission(self.user, PARTNERS_MANAGE_ENGAGEMENTS)
        _require_record_access(self.user, stakeholder)
        plan = StakeholderEngagementPlan(
            stakeholder=stakeholder,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        plan.full_clean()
        plan.save()
        _log_event("engagement_plan.created", plan, self.user)
        return plan

    @transaction.atomic
    def record(self, stakeholder: Stakeholder, **fields) -> StakeholderEngagement:
        _require_permission(self.user, PARTNERS_MANAGE_ENGAGEMENTS)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "engagement")
        engagement = StakeholderEngagement(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        engagement.full_clean()
        engagement.save()
        _confirm_reference(self.user, reference, engagement)
        _log_event("engagement.recorded", engagement, self.user)
        return engagement

    @transaction.atomic
    def complete(
        self, engagement: StakeholderEngagement, **outcomes
    ) -> StakeholderEngagement:
        _require_permission(self.user, PARTNERS_MANAGE_ENGAGEMENTS)
        _require_record_access(self.user, engagement.stakeholder)
        engagement = StakeholderEngagement.objects.select_for_update().get(
            pk=engagement.pk
        )
        if engagement.status != EngagementStatus.PLANNED:
            raise ValidationError(_("Only planned engagements can be completed."))
        for name in ("minutes", "decisions", "outcomes", "follow_up_date"):
            if name in outcomes:
                setattr(engagement, name, outcomes[name])
        engagement.status = EngagementStatus.COMPLETED
        engagement.completed_at = timezone.now()
        engagement.updated_by = self.user
        engagement.full_clean()
        engagement.save()
        _log_event("engagement.completed", engagement, self.user)
        return engagement


class StakeholderCommunicationService(BaseService):
    @transaction.atomic
    def record(self, stakeholder: Stakeholder, **fields) -> StakeholderCommunication:
        _require_permission(self.user, PARTNERS_MANAGE_COMMUNICATIONS)
        _require_record_access(self.user, stakeholder)
        communication = StakeholderCommunication(
            stakeholder=stakeholder,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        communication.full_clean()
        communication.save()
        _log_event("communication.recorded", communication, self.user)
        return communication


class StakeholderCommitmentService(BaseService):
    @transaction.atomic
    def create(self, stakeholder: Stakeholder, **fields) -> StakeholderCommitment:
        _require_permission(self.user, PARTNERS_MANAGE_COMMITMENTS)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "commitment")
        commitment = StakeholderCommitment(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        commitment.full_clean()
        commitment.save()
        _confirm_reference(self.user, reference, commitment)
        _log_event("commitment.created", commitment, self.user)
        return commitment

    @transaction.atomic
    def update_progress(
        self,
        commitment: StakeholderCommitment,
        progress_percentage,
        notes: str,
        *,
        complete: bool = False,
    ) -> StakeholderCommitment:
        _require_permission(self.user, PARTNERS_MANAGE_COMMITMENTS)
        _require_record_access(self.user, commitment.stakeholder)
        commitment = StakeholderCommitment.objects.select_for_update().get(
            pk=commitment.pk
        )
        if commitment.status == CommitmentStatus.CANCELLED:
            raise ValidationError(_("Cancelled commitments cannot be updated."))
        commitment.progress_percentage = progress_percentage
        commitment.progress_notes = notes
        commitment.status = (
            CommitmentStatus.COMPLETED if complete else CommitmentStatus.IN_PROGRESS
        )
        commitment.completion_date = timezone.localdate() if complete else None
        commitment.updated_by = self.user
        commitment.full_clean()
        commitment.save()
        _log_event("commitment.progress_updated", commitment, self.user)
        return commitment


class StakeholderContributionService(BaseService):
    @transaction.atomic
    def record(self, stakeholder: Stakeholder, **fields) -> StakeholderContribution:
        _require_permission(self.user, PARTNERS_MANAGE_CONTRIBUTIONS)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "contribution")
        contribution = StakeholderContribution(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        contribution.full_clean()
        contribution.save()
        _confirm_reference(self.user, reference, contribution)
        _log_event("contribution.recorded", contribution, self.user)
        return contribution

    @transaction.atomic
    def verify(self, contribution: StakeholderContribution) -> StakeholderContribution:
        _require_permission(self.user, PARTNERS_MANAGE_CONTRIBUTIONS)
        _require_record_access(self.user, contribution.stakeholder)
        contribution = StakeholderContribution.objects.select_for_update().get(
            pk=contribution.pk
        )
        if contribution.status not in {
            ContributionStatus.PLEDGED,
            ContributionStatus.RECEIVED,
        }:
            raise ValidationError(_("This contribution cannot be verified."))
        contribution.status = ContributionStatus.VERIFIED
        contribution.verified_by = self.user
        contribution.verified_at = timezone.now()
        contribution.updated_by = self.user
        contribution.full_clean()
        contribution.save()
        _log_event("contribution.verified", contribution, self.user)
        return contribution


class StakeholderAgreementService(BaseService):
    """Agreement content, lifecycle, expiry, and renewal operations."""

    @transaction.atomic
    def create(self, stakeholder: Stakeholder, **fields) -> StakeholderAgreement:
        _require_permission(self.user, PARTNERS_MANAGE_AGREEMENTS)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "agreement")
        version_file = fields.pop("file", None)
        change_summary = fields.pop("change_summary", "Initial agreement version.")
        agreement = StakeholderAgreement(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            relationship_owner=fields.pop("relationship_owner", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        agreement.full_clean()
        agreement.save()
        self._append_version(agreement, version_file, change_summary)
        _confirm_reference(self.user, reference, agreement)
        _log_event("agreement.created", agreement, self.user)
        return agreement

    def _append_version(self, agreement, version_file=None, change_summary=""):
        next_version = agreement.current_version_number + 1
        version = StakeholderAgreementVersion(
            agreement=agreement,
            version_number=next_version,
            title=agreement.title,
            purpose=agreement.purpose,
            responsibilities=agreement.responsibilities,
            deliverables=agreement.deliverables,
            effective_date=agreement.effective_date,
            expiry_date=agreement.expiry_date,
            file=version_file,
            file_name=getattr(version_file, "name", "") if version_file else "",
            file_size=getattr(version_file, "size", None) if version_file else None,
            change_summary=change_summary,
            created_by=self.user,
            updated_by=self.user,
        )
        version.full_clean()
        version.save()
        StakeholderAgreement.objects.filter(pk=agreement.pk).update(
            current_version_number=next_version,
            updated_by=self.user,
            updated_at=timezone.now(),
        )
        agreement.current_version_number = next_version
        return version

    @transaction.atomic
    def add_version(
        self, agreement: StakeholderAgreement, change_summary: str, **changes
    ) -> StakeholderAgreementVersion:
        _require_permission(self.user, PARTNERS_MANAGE_AGREEMENTS)
        _require_record_access(self.user, agreement.stakeholder)
        agreement = StakeholderAgreement.objects.select_for_update().get(
            pk=agreement.pk
        )
        if agreement.status not in {
            AgreementStatus.DRAFT,
            AgreementStatus.UNDER_REVIEW,
        }:
            raise ValidationError(
                _("Only draft or review agreements can receive versions.")
            )
        version_file = changes.pop("file", None)
        allowed = {
            "title",
            "purpose",
            "responsibilities",
            "deliverables",
            "effective_date",
            "expiry_date",
            "program_references",
            "project_references",
        }
        for name, value in changes.items():
            if name not in allowed:
                raise ValidationError(
                    _("Unsupported agreement field: %(field)s") % {"field": name}
                )
            setattr(agreement, name, value)
        agreement.updated_by = self.user
        agreement.full_clean()
        agreement.save()
        version = self._append_version(agreement, version_file, change_summary)
        _log_event("agreement.version_added", version, self.user)
        return version

    @transaction.atomic
    def transition(
        self, agreement: StakeholderAgreement, new_status: str, reason: str = ""
    ) -> StakeholderAgreement:
        permission = PARTNERS_MANAGE_AGREEMENTS
        if new_status in {
            AgreementStatus.UNDER_REVIEW,
            AgreementStatus.RETURNED,
            AgreementStatus.PENDING_APPROVAL,
        }:
            permission = PARTNERS_REVIEW_AGREEMENTS
        elif new_status in {
            AgreementStatus.APPROVED,
            AgreementStatus.PENDING_SIGNATURE,
            AgreementStatus.ACTIVE,
        }:
            permission = PARTNERS_APPROVE_AGREEMENTS
        _require_permission(self.user, permission)
        _require_record_access(self.user, agreement.stakeholder)
        agreement = StakeholderAgreement.objects.select_for_update().get(
            pk=agreement.pk
        )
        old_status = agreement.status
        if new_status not in AGREEMENT_TRANSITIONS.get(old_status, set()):
            raise ValidationError(_("Agreement transition is not allowed."))
        now = timezone.now()
        if new_status == AgreementStatus.APPROVED:
            if agreement.created_by_id == self.user.pk:
                raise ValidationError(
                    _("Agreement creators cannot approve their own agreements."),
                    code="agreement_self_approval",
                )
            if not agreement.versions.exists():
                raise ValidationError(
                    _("An agreement version is required before approval.")
                )
            agreement.approved_by = self.user
            agreement.approved_at = now
        elif new_status == AgreementStatus.ACTIVE:
            if agreement.expiry_date and agreement.expiry_date < timezone.localdate():
                raise ValidationError(_("An expired agreement cannot be activated."))
            latest_due_diligence = agreement.stakeholder.due_diligence_reviews.order_by(
                "-review_date"
            ).first()
            if (
                not latest_due_diligence
                or latest_due_diligence.status
                not in {
                    DueDiligenceStatus.PASSED,
                    DueDiligenceStatus.CONDITIONAL,
                }
                or (
                    latest_due_diligence.expiry_date
                    and latest_due_diligence.expiry_date < timezone.localdate()
                )
            ):
                raise ValidationError(
                    _("Current successful due diligence is required.")
                )
            agreement.activated_at = now
        elif new_status == AgreementStatus.TERMINATED:
            if not reason.strip():
                raise ValidationError(
                    {"reason": _("A termination reason is required.")}
                )
            agreement.terminated_at = now
            agreement.termination_reason = reason
        elif new_status == AgreementStatus.ARCHIVED:
            agreement.is_archived = True
            agreement.archived_at = now
            agreement.archived_by = self.user
        agreement.status = new_status
        agreement.updated_by = self.user
        agreement.full_clean()
        agreement.save()
        _log_event(
            "agreement.status_changed",
            agreement,
            self.user,
            from_status=old_status,
            to_status=new_status,
            reason=reason,
        )
        return agreement

    @transaction.atomic
    def expire(self, agreement: StakeholderAgreement) -> StakeholderAgreement:
        _require_permission(self.user, PARTNERS_MANAGE_AGREEMENTS)
        if agreement.status != AgreementStatus.ACTIVE or not agreement.is_expired:
            raise ValidationError(_("Only elapsed active agreements can expire."))
        return self.transition(
            agreement, AgreementStatus.EXPIRED, "Expiry date elapsed."
        )

    @transaction.atomic
    def request_renewal(
        self, agreement: StakeholderAgreement, **fields
    ) -> StakeholderAgreementRenewal:
        _require_permission(self.user, PARTNERS_MANAGE_AGREEMENTS)
        _require_record_access(self.user, agreement.stakeholder)
        if agreement.status not in {AgreementStatus.ACTIVE, AgreementStatus.EXPIRED}:
            raise ValidationError(_("Agreement is not eligible for renewal."))
        renewal = StakeholderAgreementRenewal(
            agreement=agreement,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        renewal.full_clean()
        renewal.save()
        _log_event("agreement.renewal_requested", renewal, self.user)
        return renewal

    @transaction.atomic
    def decide_renewal(
        self,
        renewal: StakeholderAgreementRenewal,
        *,
        approve: bool,
        decision_notes: str,
    ) -> StakeholderAgreementRenewal:
        _require_permission(self.user, PARTNERS_MANAGE_AGREEMENTS)
        renewal = (
            StakeholderAgreementRenewal.objects.select_for_update()
            .select_related("agreement__stakeholder", "agreement__agreement_type")
            .get(pk=renewal.pk)
        )
        _require_record_access(self.user, renewal.agreement.stakeholder)
        if renewal.status != RenewalStatus.PENDING:
            raise ValidationError(_("Renewal has already been decided."))
        renewal.decided_by = self.user
        renewal.decided_at = timezone.now()
        renewal.decision_notes = decision_notes
        if not approve:
            renewal.status = RenewalStatus.REJECTED
            renewal.updated_by = self.user
            renewal.save()
            _log_event("agreement.renewal_rejected", renewal, self.user)
            return renewal
        old = renewal.agreement
        renewed = self.create(
            stakeholder=old.stakeholder,
            agreement_type=old.agreement_type,
            title=old.title,
            purpose=old.purpose,
            responsibilities=old.responsibilities,
            deliverables=old.deliverables,
            program_references=old.program_references,
            project_references=old.project_references,
            effective_date=renewal.proposed_effective_date,
            expiry_date=renewal.proposed_expiry_date,
            notice_period_days=old.notice_period_days,
            relationship_owner=old.relationship_owner,
            change_summary=f"Renewal of {old.reference_number}.",
        )
        old.status = AgreementStatus.RENEWED
        old.updated_by = self.user
        old.save()
        renewal.status = RenewalStatus.COMPLETED
        renewal.renewed_agreement = renewed
        renewal.updated_by = self.user
        renewal.save()
        _log_event("agreement.renewed", renewal, self.user, renewed_id=str(renewed.pk))
        return renewal


class StakeholderDueDiligenceService(BaseService):
    @transaction.atomic
    def record(self, stakeholder: Stakeholder, **fields) -> StakeholderDueDiligence:
        _require_permission(self.user, PARTNERS_MANAGE_DUE_DILIGENCE)
        _require_record_access(self.user, stakeholder)
        reference = _reserve_reference(self.user, "due_diligence")
        review = StakeholderDueDiligence(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            reviewed_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        if review.status in {
            DueDiligenceStatus.PASSED,
            DueDiligenceStatus.CONDITIONAL,
            DueDiligenceStatus.FAILED,
        }:
            review.completed_at = review.completed_at or timezone.now()
        review.full_clean()
        review.save()
        _confirm_reference(self.user, reference, review)
        _log_event("due_diligence.recorded", review, self.user, status=review.status)
        return review


class StakeholderRiskService(BaseService):
    @transaction.atomic
    def record_risk(self, stakeholder: Stakeholder, **fields) -> StakeholderRisk:
        _require_permission(self.user, PARTNERS_MANAGE_RISK)
        _require_record_access(self.user, stakeholder)
        risk = StakeholderRisk(
            stakeholder=stakeholder,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        risk.full_clean()
        risk.save()
        _log_event("risk.recorded", risk, self.user, risk_score=risk.risk_score)
        return risk

    @transaction.atomic
    def declare_conflict(
        self, stakeholder: Stakeholder, **fields
    ) -> StakeholderConflictOfInterest:
        _require_permission(self.user, PARTNERS_MANAGE_RISK)
        _require_record_access(self.user, stakeholder)
        conflict = StakeholderConflictOfInterest(
            stakeholder=stakeholder,
            declared_by=fields.pop("declared_by", self.user),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        conflict.full_clean()
        conflict.save()
        _log_event("conflict.declared", conflict, self.user)
        return conflict


def calculate_weighted_performance(dimensions, supplied_scores: dict) -> dict:
    """Normalize and weight supplied dimensions; missing values are not imputed."""
    dimensions = list(dimensions)
    total_weight = sum((dimension.weight for dimension in dimensions), Decimal("0"))
    present_weight = Decimal("0")
    weighted_total = Decimal("0")
    normalized: dict[str, Decimal] = {}
    missing: list[str] = []
    for dimension in dimensions:
        raw = supplied_scores.get(
            str(dimension.pk), supplied_scores.get(dimension.code)
        )
        if raw is None:
            missing.append(dimension.code)
            continue
        raw_decimal = Decimal(str(raw))
        if not dimension.minimum_score <= raw_decimal <= dimension.maximum_score:
            raise ValidationError(
                {dimension.code: _("Score is outside its configured range.")}
            )
        span = dimension.maximum_score - dimension.minimum_score
        normalized_score = (
            (raw_decimal - dimension.minimum_score) / span * Decimal("100")
        ).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        normalized[str(dimension.pk)] = normalized_score
        present_weight += dimension.weight
        weighted_total += normalized_score * dimension.weight
    weighted_score = (
        (weighted_total / present_weight).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if present_weight
        else None
    )
    completeness = (
        (present_weight / total_weight * Decimal("100")).quantize(
            TWO_PLACES, rounding=ROUND_HALF_UP
        )
        if total_weight
        else Decimal("0.00")
    )
    return {
        "weighted_score": weighted_score,
        "completeness_percentage": completeness,
        "missing_dimensions": missing,
        "normalized": normalized,
        "formula_explanation": (
            "Each score is normalized to 0-100 from its configured range, then "
            "averaged using weight snapshots for supplied dimensions only. Missing "
            "dimensions are listed and never imputed."
        ),
    }


class StakeholderPerformanceService(BaseService):
    @transaction.atomic
    def record_review(
        self,
        stakeholder: Stakeholder,
        review_period: str,
        scores: dict,
        **fields,
    ) -> StakeholderPerformanceReview:
        _require_permission(self.user, PARTNERS_MANAGE_PERFORMANCE)
        _require_record_access(self.user, stakeholder)
        dimensions = list(StakeholderPerformanceDimension.objects.filter(active=True))
        if not dimensions:
            raise ValidationError(_("No active performance dimensions are configured."))
        calculated = calculate_weighted_performance(dimensions, scores)
        reference = _reserve_reference(self.user, "performance")
        review = StakeholderPerformanceReview(
            stakeholder=stakeholder,
            reference_number=reference.reference_number,
            review_period=review_period,
            reviewer=self.user,
            weighted_score=calculated["weighted_score"],
            completeness_percentage=calculated["completeness_percentage"],
            missing_dimensions=calculated["missing_dimensions"],
            formula_explanation=calculated["formula_explanation"],
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        review.full_clean()
        review.save()
        for dimension in dimensions:
            raw = scores.get(str(dimension.pk), scores.get(dimension.code))
            if raw is None:
                continue
            score = StakeholderPerformanceScore(
                review=review,
                dimension=dimension,
                score=Decimal(str(raw)),
                weight_snapshot=dimension.weight,
                normalized_score=calculated["normalized"][str(dimension.pk)],
                created_by=self.user,
                updated_by=self.user,
            )
            score.full_clean()
            score.save()
        _confirm_reference(self.user, reference, review)
        _log_event(
            "performance.recorded",
            review,
            self.user,
            weighted_score=str(review.weighted_score),
            completeness=str(review.completeness_percentage),
        )
        return review

    @transaction.atomic
    def finalize(
        self, review: StakeholderPerformanceReview
    ) -> StakeholderPerformanceReview:
        _require_permission(self.user, PARTNERS_MANAGE_PERFORMANCE)
        _require_record_access(self.user, review.stakeholder)
        review = StakeholderPerformanceReview.objects.select_for_update().get(
            pk=review.pk
        )
        if review.status != ReviewStatus.DRAFT:
            raise ValidationError(_("Only draft reviews can be finalized."))
        if review.weighted_score is None:
            raise ValidationError(_("At least one dimension score is required."))
        review.status = ReviewStatus.FINALIZED
        review.finalized_at = timezone.now()
        review.updated_by = self.user
        review.save()
        _log_event("performance.finalized", review, self.user)
        return review


class StakeholderActionService(BaseService):
    @transaction.atomic
    def create(self, stakeholder: Stakeholder, **fields) -> StakeholderActionItem:
        _require_permission(self.user, PARTNERS_MANAGE_ACTIONS)
        _require_record_access(self.user, stakeholder)
        action = StakeholderActionItem(
            stakeholder=stakeholder,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        action.full_clean()
        action.save()
        _log_event("action.created", action, self.user)
        return action

    @transaction.atomic
    def change_status(
        self, action: StakeholderActionItem, status: str, progress_notes: str = ""
    ) -> StakeholderActionItem:
        _require_permission(self.user, PARTNERS_MANAGE_ACTIONS)
        _require_record_access(self.user, action.stakeholder)
        action = StakeholderActionItem.objects.select_for_update().get(pk=action.pk)
        if status not in ActionStatus.values:
            raise ValidationError(_("Invalid action status."))
        if action.status in {ActionStatus.COMPLETED, ActionStatus.CANCELLED}:
            raise ValidationError(
                _("Final actions cannot be reopened through this service.")
            )
        action.status = status
        action.progress_notes = progress_notes
        action.completed_at = (
            timezone.now() if status == ActionStatus.COMPLETED else None
        )
        action.updated_by = self.user
        action.full_clean()
        action.save()
        _log_event("action.status_changed", action, self.user, status=status)
        return action


class StakeholderNoteService(BaseService):
    @transaction.atomic
    def create(
        self, stakeholder: Stakeholder, title: str, content: str, **fields
    ) -> StakeholderNote:
        _require_permission(self.user, PARTNERS_MANAGE_NOTES)
        _require_record_access(self.user, stakeholder)
        note = StakeholderNote(
            stakeholder=stakeholder,
            title=title,
            current_version_number=1,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        note.full_clean()
        note.save()
        version = StakeholderNoteVersion(
            note=note,
            version_number=1,
            content=content,
            created_by=self.user,
            updated_by=self.user,
        )
        version.full_clean()
        version.save()
        _log_event("note.created", note, self.user)
        return note

    @transaction.atomic
    def add_version(
        self, note: StakeholderNote, content: str, change_summary: str = ""
    ) -> StakeholderNoteVersion:
        _require_permission(self.user, PARTNERS_MANAGE_NOTES)
        _require_record_access(self.user, note.stakeholder)
        note = StakeholderNote.objects.select_for_update().get(pk=note.pk)
        if note.status != NoteStatus.DRAFT:
            raise ValidationError(_("Only draft notes can receive new versions."))
        next_version = note.current_version_number + 1
        version = StakeholderNoteVersion(
            note=note,
            version_number=next_version,
            content=content,
            change_summary=change_summary,
            created_by=self.user,
            updated_by=self.user,
        )
        version.full_clean()
        version.save()
        note.current_version_number = next_version
        note.updated_by = self.user
        note.save()
        _log_event("note.version_added", version, self.user)
        return version

    @transaction.atomic
    def finalize(self, note: StakeholderNote) -> StakeholderNote:
        _require_permission(self.user, PARTNERS_MANAGE_NOTES)
        _require_record_access(self.user, note.stakeholder)
        note = StakeholderNote.objects.select_for_update().get(pk=note.pk)
        if note.status != NoteStatus.DRAFT:
            raise ValidationError(_("Only draft notes can be finalized."))
        version = note.versions.select_for_update().get(
            version_number=note.current_version_number
        )
        now = timezone.now()
        version.is_finalized = True
        version.finalized_at = now
        version.finalized_by = self.user
        version.updated_by = self.user
        version.full_clean()
        version.save()
        note.status = NoteStatus.FINALIZED
        note.finalized_at = now
        note.finalized_by = self.user
        note.updated_by = self.user
        note.save()
        _log_event("note.finalized", note, self.user)
        return note


def _file_checksum(upload) -> str:
    position = upload.tell() if hasattr(upload, "tell") else None
    digest = hashlib.sha256()
    for chunk in (
        upload.chunks()
        if hasattr(upload, "chunks")
        else iter(lambda: upload.read(65536), b"")
    ):
        digest.update(chunk)
    if position is not None and hasattr(upload, "seek"):
        upload.seek(position)
    return digest.hexdigest()


class StakeholderDocumentService(BaseService):
    @transaction.atomic
    def add_version(
        self,
        stakeholder: Stakeholder,
        *,
        document_key: str,
        title: str,
        document_type: str,
        file,
        **fields,
    ) -> StakeholderDocument:
        _require_permission(self.user, PARTNERS_MANAGE_DOCUMENTS)
        _require_record_access(self.user, stakeholder, include_archived=True)
        latest = (
            StakeholderDocument.objects.select_for_update()
            .filter(stakeholder=stakeholder, document_key=document_key)
            .order_by("-version_number")
            .first()
        )
        version_number = latest.version_number + 1 if latest else 1
        if latest and latest.status == DocumentStatus.CURRENT:
            StakeholderDocument.objects.filter(pk=latest.pk).update(
                status=DocumentStatus.SUPERSEDED,
                updated_by=self.user,
                updated_at=timezone.now(),
            )
        document = StakeholderDocument(
            stakeholder=stakeholder,
            document_key=document_key,
            version_number=version_number,
            previous_version=latest,
            title=title,
            document_type=document_type,
            file=file,
            original_filename=str(file.name),
            file_size=file.size,
            checksum=_file_checksum(file),
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        document.full_clean()
        document.save()
        _log_event("document.version_added", document, self.user)
        return document

    @transaction.atomic
    def archive(self, document: StakeholderDocument) -> StakeholderDocument:
        _require_permission(self.user, PARTNERS_MANAGE_DOCUMENTS)
        _require_record_access(self.user, document.stakeholder, include_archived=True)
        document = StakeholderDocument.objects.select_for_update().get(pk=document.pk)
        if document.legal_hold:
            raise ValidationError(_("A document on legal hold cannot be archived."))
        document.status = DocumentStatus.ARCHIVED
        document.updated_by = self.user
        document.save()
        _log_event("document.archived", document, self.user)
        return document


class StakeholderAccessService(BaseService):
    @transaction.atomic
    def grant(
        self, stakeholder: Stakeholder, user, reason: str, **fields
    ) -> StakeholderAccessGrant:
        _require_permission(self.user, PARTNERS_MANAGE_ACCESS)
        _require_record_access(self.user, stakeholder, include_archived=True)
        if not reason.strip():
            raise ValidationError({"reason": _("An access reason is required.")})
        existing = (
            StakeholderAccessGrant.objects.select_for_update()
            .filter(stakeholder=stakeholder, user=user, is_active=True)
            .first()
        )
        if existing:
            raise ValidationError(_("This user already has an active grant."))
        grant = StakeholderAccessGrant(
            stakeholder=stakeholder,
            user=user,
            reason=reason,
            granted_by=self.user,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        grant.full_clean()
        grant.save()
        _log_event("access.granted", grant, self.user, grantee_id=str(user.pk))
        return grant

    @transaction.atomic
    def revoke(self, grant: StakeholderAccessGrant) -> StakeholderAccessGrant:
        _require_permission(self.user, PARTNERS_MANAGE_ACCESS)
        _require_record_access(self.user, grant.stakeholder, include_archived=True)
        grant = StakeholderAccessGrant.objects.select_for_update().get(pk=grant.pk)
        if not grant.is_active:
            raise ValidationError(_("Access grant is already inactive."))
        grant.is_active = False
        grant.revoked_at = timezone.now()
        grant.revoked_by = self.user
        grant.updated_by = self.user
        grant.full_clean()
        grant.save()
        _log_event("access.revoked", grant, self.user)
        return grant


class StakeholderAnalyticsService(BaseService):
    """Permission-scoped aggregates for dashboards and reporting adapters."""

    def summary(self) -> dict:
        _require_permission(self.user, PARTNERS_ANALYTICS)
        queryset = visible_stakeholders(self.user)
        today = timezone.localdate()
        contribution_total = StakeholderContribution.objects.filter(
            stakeholder__in=queryset,
            status=ContributionStatus.VERIFIED,
            amount__isnull=False,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        return {
            "total": queryset.count(),
            "by_status": list(
                queryset.values("status").annotate(total=Count("id")).order_by("status")
            ),
            "by_region": list(
                queryset.exclude(province_or_region="")
                .values("province_or_region")
                .annotate(total=Count("id"))
                .order_by("province_or_region")
            ),
            "by_category": list(
                StakeholderReferenceData.objects.filter(
                    kind=ReferenceDataKind.CATEGORY,
                    category_stakeholders__in=queryset,
                )
                .values("code", "name")
                .annotate(total=Count("category_stakeholders", distinct=True))
                .order_by("name")
            ),
            "verified_contribution_total": contribution_total,
            "expiring_agreements": StakeholderAgreement.objects.filter(
                stakeholder__in=queryset,
                status=AgreementStatus.ACTIVE,
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=60),
            ).count(),
            "overdue_actions": StakeholderActionItem.objects.filter(
                stakeholder__in=queryset,
                due_date__lt=today,
                status__in=[
                    ActionStatus.OPEN,
                    ActionStatus.IN_PROGRESS,
                    ActionStatus.BLOCKED,
                    ActionStatus.OVERDUE,
                ],
            ).count(),
            "open_risks": StakeholderRisk.objects.filter(
                stakeholder__in=queryset,
                status__in=[RiskStatus.OPEN, RiskStatus.MONITORING],
            ).count(),
        }
