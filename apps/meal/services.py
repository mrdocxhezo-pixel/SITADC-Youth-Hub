"""Permission-checked transactional services for the MEAL module.

Every write flows through these services so that RBAC checks, workflow
transitions, reference-number allocation, status history, and the immutable
audit trail are enforced consistently.
"""

from __future__ import annotations

import logging
from typing import Any, ClassVar

from django.core.exceptions import PermissionDenied
from django.db import models
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
    BaselineStatus,
    BestPracticeStatus,
    ComplaintStatus,
    CorrectiveActionStatus,
    DataCollectionPlanStatus,
    DataSubmissionStatus,
    DQAStatus,
    EvaluationStatus,
    FeedbackStatus,
    LearningLogStatus,
    LessonStatus,
    MonitoringPlanStatus,
    MonitoringVisitStatus,
    OutcomeHarvestStatus,
    ReportStatus,
    ScorecardStatus,
    TargetStatus,
    WorkflowStatus,
)
from .exceptions import InvalidStatusTransition
from .models import MEALAuditRecord, MEALStatusHistory
from .permissions import (
    MEAL_APPROVE,
    MEAL_ARCHIVE,
    MEAL_CREATE,
    MEAL_EXPORT,
    MEAL_MANAGE,
    MEAL_MANAGE_ACCOUNTABILITY,
    MEAL_MANAGE_DATA_COLLECTION,
    MEAL_MANAGE_DQA,
    MEAL_MANAGE_EVALUATIONS,
    MEAL_MANAGE_INDICATORS,
    MEAL_MANAGE_LEARNING,
    MEAL_MANAGE_MONITORING,
    MEAL_MANAGE_SCORECARDS,
    MEAL_RESTORE,
    MEAL_SUBMIT,
    MEAL_UPDATE,
    MEAL_VIEW_CONFIDENTIAL,
)
from .selectors import user_can_access_meal_record

logger = logging.getLogger(__name__)


MODEL_SCHEME_KEYS: dict[str, str] = {
    "TheoryOfChange": "theory_of_change",
    "ResultsFramework": "results_framework",
    "LogicalFramework": "logframe",
    "Indicator": "indicator",
    "IndicatorBaseline": "indicator_baseline",
    "IndicatorTarget": "indicator_target",
    "DataCollectionPlan": "data_collection_plan",
    "MonitoringPlan": "monitoring_plan",
    "MonitoringVisit": "monitoring_visit",
    "Evaluation": "evaluation",
    "DataQualityAssessment": "dqa",
    "Complaint": "complaint",
    "Feedback": "feedback",
    "CorrectiveAction": "corrective_action",
    "OutcomeHarvest": "outcome_harvest",
    "LearningLog": "learning_log",
    "BestPractice": "best_practice",
    "LessonLearned": "meal_lesson",
    "PerformanceScorecard": "scorecard",
    "MEALReport": "meal_report",
    "OrganizationalKPI": "organizational_kpi",
}


class MEALService(BaseService):
    """Base service enforcing RBAC, transitions, references, and audit."""

    model: ClassVar[type[models.Model] | None] = None
    scheme_key: ClassVar[str | None] = None
    transitions: ClassVar[dict[str, set[str]]] = {}

    def __init__(self, user=None):
        super().__init__(user)
        self.actor = user

    # -- guards ---------------------------------------------------------
    def _require_permission(self, permission_code: str) -> None:
        if not self.actor or not getattr(self.actor, "is_authenticated", False):
            raise PermissionDenied(_("An authenticated actor is required."))
        if not (
            user_has_permission(self.actor, permission_code)
            or user_has_permission(self.actor, MEAL_MANAGE)
        ):
            raise PermissionDenied(_("Permission denied for this MEAL action."))

    def _require_record_access(
        self, instance, *, include_archived: bool = False
    ) -> None:
        if not user_can_access_meal_record(
            self.actor, instance, include_archived=include_archived
        ):
            raise PermissionDenied(_("This MEAL record is outside your access scope."))

    # -- audit helpers ---------------------------------------------------
    def _log(self, action: str, instance, **details) -> None:
        entity_type = type(instance).__name__
        entity_id = str(instance.pk)
        logger.info(
            "meal_domain_event",
            extra={
                "meal_event": {
                    "action": action,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "actor_id": str(getattr(self.actor, "pk", "")),
                    **details,
                }
            },
        )
        MEALAuditRecord.objects.create(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            created_by=self.actor,
            notes=str(details or ""),
            to_data={key: str(value) for key, value in details.items()},
        )

    def _history(
        self,
        instance,
        action: str,
        from_status: str | None,
        to_status: str,
        notes: str = "",
    ) -> None:
        MEALStatusHistory.objects.create(
            entity_type=type(instance).__name__,
            entity_id=str(instance.pk),
            action=action,
            from_status=from_status or "",
            to_status=to_status,
            notes=notes,
            created_by=self.actor,
        )

    # -- reference allocation ----------------------------------------------
    def _reserve_reference(self, instance):
        """Reserve a centralized reference number for an unsaved entity."""
        scheme_key = MODEL_SCHEME_KEYS.get(type(instance).__name__) or self.scheme_key
        if not scheme_key:
            return None
        scheme_code = REFERENCE_SCHEME_CODES[scheme_key]
        return ReferenceNumberService(user=self.actor).execute(
            module=ReferenceModules.MEAL,
            record_type=scheme_code,
            scheme_code=scheme_code,
            notes=f"Phase 18 {scheme_code} reference reservation.",
        )

    def _confirm_reference(self, reference, instance) -> None:
        if reference is None:
            return
        ConfirmReferenceAssignmentService(user=self.actor).execute(
            reference=reference,
            record_id=instance.pk,
            notes=f"Assigned to {type(instance).__name__}.",
        )

    def _allocate_reference(self, instance) -> None:
        """Assign a reference number to an already persisted instance."""
        reference = self._reserve_reference(instance)
        if reference is not None:
            instance.reference_number = reference.reference_number
            instance.save(update_fields=["reference_number", "updated_at"])
            self._confirm_reference(reference, instance)

    def _apply_reference(self, instance, reference) -> None:
        """Bind a reserved reference before validation and persist it."""
        if reference is not None:
            instance.reference_number = reference.reference_number

    # -- generic CRUD --------------------------------------------------------
    def create(
        self,
        *,
        fields: dict | None = None,
        model: type[models.Model] | None = None,
        **extra,
    ) -> Any:
        entity = model or self.model
        if entity is None:
            raise NotImplementedError("create requires a model.")
        self._require_permission(MEAL_CREATE)
        data = dict(fields or {})
        data.update(extra)
        data["created_by"] = self.actor
        data["updated_by"] = self.actor
        m2m_fields = {field.name for field in entity._meta.local_many_to_many}
        m2m_data = {key: data.pop(key) for key in list(data) if key in m2m_fields}
        instance = entity(**data)
        reference = self._reserve_reference(instance)
        self._apply_reference(instance, reference)
        instance.full_clean()
        instance.save()
        for key, value in m2m_data.items():
            getattr(instance, key).set(value)
        self._confirm_reference(reference, instance)
        self._log(
            "create",
            instance,
            **{key: str(value) for key, value in data.items() if value is not None},
        )
        self._history(instance, "CREATE", None, str(getattr(instance, "status", "")))
        return instance

    def update(self, *, instance, fields: dict | None = None, **extra) -> Any:
        self._require_permission(MEAL_UPDATE)
        self._require_record_access(instance)
        data = dict(fields or {})
        data.update(extra)
        changed: list[str] = []
        for key, value in data.items():
            if hasattr(instance, key) and getattr(instance, key) != value:
                setattr(instance, key, value)
                changed.append(key)
        if changed:
            instance.updated_by = self.actor
            instance.full_clean()
            instance.save()
            snapshot = {key: str(getattr(instance, key)) for key in changed}
            self._log("update", instance, changed_fields=changed, **snapshot)
        return instance

    def archive(self, *, instance) -> Any:
        self._require_permission(MEAL_ARCHIVE)
        self._require_record_access(instance)
        instance.archive(archived_by=self.actor)
        self._history(instance, "ARCHIVE", instance.status, instance.status)
        self._log("archive", instance)
        return instance

    def restore(self, *, instance) -> Any:
        self._require_permission(MEAL_RESTORE)
        self._require_record_access(instance, include_archived=True)
        instance.unarchive()
        self._history(instance, "RESTORE", instance.status, instance.status)
        self._log("restore", instance)
        return instance

    # -- workflow transition ------------------------------------------------
    def transition(
        self,
        *,
        instance,
        to_status: str,
        permission_code: str,
        notes: str = "",
    ) -> Any:
        self._require_permission(permission_code)
        self._require_record_access(instance)
        allowed = self.transitions.get(instance.status, set())
        if to_status not in allowed:
            raise InvalidStatusTransition(
                _("Cannot move %(record)s from %(current)s to %(target)s.")
                % {
                    "record": type(instance).__name__,
                    "current": instance.get_status_display(),
                    "target": dict(instance._meta.get_field("status").flatchoices).get(
                        to_status, to_status
                    ),
                }
            )
        from_status = instance.status
        instance.status = to_status
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, to_status, from_status, to_status, notes)
        self._log("transition", instance, from_status=from_status, to_status=to_status)
        return instance

    def _set_fields(
        self, instance, *, fields: dict | None, permission: str = "update"
    ) -> None:
        self._require_permission(permission)
        self._require_record_access(instance)
        changed: list[str] = []
        for key, value in (fields or {}).items():
            if hasattr(instance, key) and getattr(instance, key) != value:
                setattr(instance, key, value)
                changed.append(key)
        if changed:
            instance.updated_by = self.actor
            instance.full_clean()
            instance.save()
            self._log("update", instance, changed_fields=changed)


class FrameworkService(MEALService):
    """Theory of Change, Results Framework, and Logframe workflows."""

    transitions: ClassVar[dict[str, set[str]]] = {
        WorkflowStatus.DRAFT: {
            WorkflowStatus.SUBMITTED,
            WorkflowStatus.ARCHIVED,
        },
        WorkflowStatus.SUBMITTED: {
            WorkflowStatus.APPROVED,
            WorkflowStatus.REJECTED,
            WorkflowStatus.DRAFT,
        },
        WorkflowStatus.APPROVED: {WorkflowStatus.ARCHIVED},
        WorkflowStatus.REJECTED: {WorkflowStatus.DRAFT, WorkflowStatus.ARCHIVED},
        WorkflowStatus.ARCHIVED: set(),
    }

    def submit(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=WorkflowStatus.SUBMITTED,
            permission_code=MEAL_SUBMIT,
            notes=notes,
        )

    def approve(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=WorkflowStatus.APPROVED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def reject(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=WorkflowStatus.REJECTED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def return_to_draft(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=WorkflowStatus.DRAFT,
            permission_code=MEAL_SUBMIT,
            notes=notes,
        )


class IndicatorService(MEALService):
    """Indicator registry, baseline, target, and result workflows."""

    model = None
    scheme_key = "indicator"
    transitions: ClassVar[dict[str, set[str]]] = {
        "DRAFT": {"ACTIVE", "ARCHIVED"},
        "ACTIVE": {"ARCHIVED"},
        "ARCHIVED": set(),
    }

    def activate(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status="ACTIVE",
            permission_code=MEAL_MANAGE_INDICATORS,
            notes=notes,
        )

    def archive_indicator(self, *, instance) -> Any:
        return self.transition(
            instance=instance,
            to_status="ARCHIVED",
            permission_code=MEAL_ARCHIVE,
        )

    def create_baseline(self, *, indicator, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_INDICATORS)
        from .models import IndicatorBaseline

        instance = IndicatorBaseline(
            indicator=indicator,
            status=BaselineStatus.PENDING_APPROVAL,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        reference = self._reserve_reference(instance)
        self._apply_reference(instance, reference)
        instance.full_clean()
        instance.save()
        self._confirm_reference(reference, instance)
        self._log("create", instance, indicator=str(indicator.pk))
        return instance

    def approve_baseline(self, *, instance, notes: str = "") -> Any:
        if instance.status not in {
            BaselineStatus.PENDING_APPROVAL,
            BaselineStatus.REVISED,
        }:
            raise InvalidStatusTransition(
                _("Only pending or revised baselines can be approved.")
            )
        self._require_permission(MEAL_MANAGE_INDICATORS)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = BaselineStatus.APPROVED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, "APPROVE", from_status, BaselineStatus.APPROVED, notes)
        self._log("approve", instance, baseline_id=str(instance.pk))
        return instance

    def revise_baseline(self, *, instance, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_INDICATORS)
        self._require_record_access(instance)
        from .models import IndicatorBaseline

        revision = IndicatorBaseline(
            indicator=instance.indicator,
            status=BaselineStatus.PENDING_APPROVAL,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        reference = self._reserve_reference(revision)
        self._apply_reference(revision, reference)
        revision.full_clean()
        revision.save()
        self._confirm_reference(reference, revision)
        instance.status = BaselineStatus.REVISED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, "REVISE", "APPROVED", BaselineStatus.REVISED)
        self._log("revise", instance, revision_id=str(revision.pk))
        return revision

    def create_target(self, *, indicator, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_INDICATORS)
        from .models import IndicatorTarget

        instance = IndicatorTarget(
            indicator=indicator,
            status=TargetStatus.PENDING_APPROVAL,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        reference = self._reserve_reference(instance)
        self._apply_reference(instance, reference)
        instance.full_clean()
        instance.save()
        self._confirm_reference(reference, instance)
        self._log("create", instance, indicator=str(indicator.pk))
        return instance

    def approve_target(self, *, instance, notes: str = "") -> Any:
        if instance.status != TargetStatus.PENDING_APPROVAL:
            raise InvalidStatusTransition(_("Only pending targets can be approved."))
        self._require_permission(MEAL_MANAGE_INDICATORS)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = TargetStatus.APPROVED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, "APPROVE", from_status, TargetStatus.APPROVED, notes)
        self._log("approve", instance, target_id=str(instance.pk))
        return instance

    def revise_target(self, *, instance, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_INDICATORS)
        self._require_record_access(instance)
        from .models import IndicatorTarget

        revision = IndicatorTarget(
            indicator=instance.indicator,
            status=TargetStatus.PENDING_APPROVAL,
            revised_from=instance,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        reference = self._reserve_reference(revision)
        self._apply_reference(revision, reference)
        revision.full_clean()
        revision.save()
        self._confirm_reference(reference, revision)
        instance.status = TargetStatus.REVISED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, "REVISE", "APPROVED", TargetStatus.REVISED)
        self._log("revise", instance, revision_id=str(revision.pk))
        return revision

    def record_result(self, *, indicator, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        from .models import IndicatorResult

        instance = IndicatorResult(
            indicator=indicator,
            status=DataSubmissionStatus.DRAFT,
            submitted_by=self.actor,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        instance.full_clean()
        instance.save()
        self._log("create", instance, indicator=str(indicator.pk))
        return instance

    def validate_result(self, *, instance, notes: str = "") -> Any:
        if instance.status not in {
            DataSubmissionStatus.SUBMITTED,
            DataSubmissionStatus.REJECTED,
        }:
            raise InvalidStatusTransition(
                _("Result can only be validated after submission.")
            )
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.VALIDATED
        instance.validated_by = self.actor
        instance.validated_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "validated_by",
                "validated_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(
            instance, "VALIDATE", from_status, DataSubmissionStatus.VALIDATED, notes
        )
        self._log("validate", instance)
        return instance

    def approve_result(self, *, instance, notes: str = "") -> Any:
        if instance.status != DataSubmissionStatus.VALIDATED:
            raise InvalidStatusTransition(_("Only validated results can be approved."))
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.APPROVED
        instance.approved_by = self.actor
        instance.approved_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(
            instance, "APPROVE", from_status, DataSubmissionStatus.APPROVED, notes
        )
        self._log("approve", instance, indicator=str(instance.indicator_id))
        return instance

    def reject_result(self, *, instance, notes: str = "") -> Any:
        if instance.status not in {
            DataSubmissionStatus.SUBMITTED,
            DataSubmissionStatus.VALIDATED,
        }:
            raise InvalidStatusTransition(
                _("Only submitted or validated results can be rejected.")
            )
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.REJECTED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(
            instance, "REJECT", from_status, DataSubmissionStatus.REJECTED, notes
        )
        self._log("reject", instance)
        return instance


class DataCollectionService(MEALService):
    """Data collection plan and submission workflows."""

    model = None
    scheme_key = "data_collection_plan"
    transitions: ClassVar[dict[str, set[str]]] = {
        DataCollectionPlanStatus.DRAFT: {
            DataCollectionPlanStatus.ACTIVE,
            DataCollectionPlanStatus.CANCELLED,
        },
        DataCollectionPlanStatus.ACTIVE: {
            DataCollectionPlanStatus.COMPLETED,
            DataCollectionPlanStatus.CANCELLED,
        },
        DataCollectionPlanStatus.COMPLETED: {DataCollectionPlanStatus.ARCHIVED},
        DataCollectionPlanStatus.CANCELLED: {DataCollectionPlanStatus.ARCHIVED},
        DataCollectionPlanStatus.ARCHIVED: set(),
    }

    SUBMISSION_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        DataSubmissionStatus.DRAFT: {DataSubmissionStatus.SUBMITTED},
        DataSubmissionStatus.SUBMITTED: {
            DataSubmissionStatus.VALIDATED,
            DataSubmissionStatus.REJECTED,
        },
        DataSubmissionStatus.VALIDATED: {
            DataSubmissionStatus.APPROVED,
            DataSubmissionStatus.REJECTED,
        },
        DataSubmissionStatus.REJECTED: {DataSubmissionStatus.SUBMITTED},
        DataSubmissionStatus.APPROVED: set(),
    }

    def start_plan(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=DataCollectionPlanStatus.ACTIVE,
            permission_code=MEAL_MANAGE_DATA_COLLECTION,
            notes=notes,
        )

    def complete_plan(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=DataCollectionPlanStatus.COMPLETED,
            permission_code=MEAL_MANAGE_DATA_COLLECTION,
            notes=notes,
        )

    def create_submission(self, *, plan, indicator, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        from .models import DataSubmission

        instance = DataSubmission(
            plan=plan,
            indicator=indicator,
            status=DataSubmissionStatus.DRAFT,
            enumerator=self.actor,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        instance.full_clean()
        instance.save()
        self._log("create", instance, plan=str(plan.pk))
        return instance

    def submit_submission(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=DataSubmissionStatus.SUBMITTED,
            permission_code=MEAL_MANAGE_DATA_COLLECTION,
            notes=notes,
        )

    def validate_submission(self, *, instance, notes: str = "") -> Any:
        if instance.status not in {
            DataSubmissionStatus.SUBMITTED,
            DataSubmissionStatus.REJECTED,
        }:
            raise InvalidStatusTransition(
                _("Only submitted or rejected submissions can be validated.")
            )
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.VALIDATED
        instance.validated_by = self.actor
        instance.validated_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "validated_by",
                "validated_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(
            instance, "VALIDATE", from_status, DataSubmissionStatus.VALIDATED, notes
        )
        self._log("validate", instance)
        return instance

    def approve_submission(self, *, instance, notes: str = "") -> Any:
        if instance.status != DataSubmissionStatus.VALIDATED:
            raise InvalidStatusTransition(
                _("Only validated submissions can be approved.")
            )
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.APPROVED
        instance.approved_by = self.actor
        instance.approved_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(
            instance, "APPROVE", from_status, DataSubmissionStatus.APPROVED, notes
        )
        self._log("approve", instance)
        return instance

    def reject_submission(self, *, instance, notes: str = "") -> Any:
        if instance.status not in {
            DataSubmissionStatus.SUBMITTED,
            DataSubmissionStatus.VALIDATED,
        }:
            raise InvalidStatusTransition(
                _("Only submitted or validated submissions can be rejected.")
            )
        self._require_permission(MEAL_MANAGE_DATA_COLLECTION)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = DataSubmissionStatus.REJECTED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(
            instance, "REJECT", from_status, DataSubmissionStatus.REJECTED, notes
        )
        self._log("reject", instance)
        return instance


class MonitoringService(MEALService):
    """Monitoring plan, visit, and finding workflows."""

    model = None
    scheme_key = "monitoring_visit"
    transitions: ClassVar[dict[str, set[str]]] = {
        MonitoringVisitStatus.PLANNED: {
            MonitoringVisitStatus.IN_PROGRESS,
            MonitoringVisitStatus.CANCELLED,
        },
        MonitoringVisitStatus.IN_PROGRESS: {
            MonitoringVisitStatus.COMPLETED,
            MonitoringVisitStatus.FOLLOW_UP_REQUIRED,
            MonitoringVisitStatus.CANCELLED,
        },
        MonitoringVisitStatus.COMPLETED: {MonitoringVisitStatus.FOLLOW_UP_REQUIRED},
        MonitoringVisitStatus.FOLLOW_UP_REQUIRED: {MonitoringVisitStatus.COMPLETED},
        MonitoringVisitStatus.CANCELLED: set(),
    }

    PLAN_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        MonitoringPlanStatus.ACTIVE: {
            MonitoringPlanStatus.PAUSED,
            MonitoringPlanStatus.COMPLETED,
        },
        MonitoringPlanStatus.PAUSED: {MonitoringPlanStatus.ACTIVE},
        MonitoringPlanStatus.COMPLETED: {MonitoringPlanStatus.ARCHIVED},
        MonitoringPlanStatus.ARCHIVED: set(),
    }

    def begin_visit(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=MonitoringVisitStatus.IN_PROGRESS,
            permission_code=MEAL_MANAGE_MONITORING,
            notes=notes,
        )

    def complete_visit(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=MonitoringVisitStatus.COMPLETED,
            permission_code=MEAL_MANAGE_MONITORING,
            notes=notes,
        )

    def require_follow_up(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=MonitoringVisitStatus.FOLLOW_UP_REQUIRED,
            permission_code=MEAL_MANAGE_MONITORING,
            notes=notes,
        )

    def create_finding(self, *, visit, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_MONITORING)
        from .models import MonitoringFinding

        instance = MonitoringFinding(
            visit=visit,
            created_by=self.actor,
            updated_by=self.actor,
            **(fields or {}),
        )
        instance.full_clean()
        instance.save()
        self._log("create", instance, visit=str(visit.pk))
        return instance


class EvaluationService(MEALService):
    """Evaluation lifecycle including report submission and approval."""

    model = None
    scheme_key = "evaluation"
    transitions: ClassVar[dict[str, set[str]]] = {
        EvaluationStatus.PLANNED: {EvaluationStatus.IN_PROGRESS},
        EvaluationStatus.IN_PROGRESS: {EvaluationStatus.REPORT_DRAFT},
        EvaluationStatus.REPORT_DRAFT: {
            EvaluationStatus.SUBMITTED,
            EvaluationStatus.ARCHIVED,
        },
        EvaluationStatus.SUBMITTED: {
            EvaluationStatus.APPROVED,
            EvaluationStatus.REJECTED,
        },
        EvaluationStatus.APPROVED: {
            EvaluationStatus.PUBLISHED,
            EvaluationStatus.ARCHIVED,
        },
        EvaluationStatus.PUBLISHED: {EvaluationStatus.ARCHIVED},
        EvaluationStatus.REJECTED: {EvaluationStatus.REPORT_DRAFT},
        EvaluationStatus.ARCHIVED: set(),
    }

    def start(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=EvaluationStatus.IN_PROGRESS,
            permission_code=MEAL_MANAGE_EVALUATIONS,
            notes=notes,
        )

    def submit_report(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=EvaluationStatus.SUBMITTED,
            permission_code=MEAL_MANAGE_EVALUATIONS,
            notes=notes,
        )

    def approve(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=EvaluationStatus.APPROVED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def reject(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=EvaluationStatus.REJECTED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def publish(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=EvaluationStatus.PUBLISHED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )


class DQAService(MEALService):
    """Data Quality Assessment lifecycle and dimension scores."""

    model = None
    scheme_key = "dqa"
    transitions: ClassVar[dict[str, set[str]]] = {
        DQAStatus.PLANNED: {DQAStatus.IN_PROGRESS},
        DQAStatus.IN_PROGRESS: {DQAStatus.COMPLETED},
        DQAStatus.COMPLETED: {DQAStatus.ARCHIVED},
        DQAStatus.ARCHIVED: set(),
    }

    def start(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=DQAStatus.IN_PROGRESS,
            permission_code=MEAL_MANAGE_DQA,
            notes=notes,
        )

    def complete(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=DQAStatus.COMPLETED,
            permission_code=MEAL_MANAGE_DQA,
            notes=notes,
        )

    def record_dimension_score(
        self, *, dqa, dimension: str, score: int, findings: str = ""
    ) -> Any:
        self._require_permission(MEAL_MANAGE_DQA)
        from .models import DQADimensionScore

        instance, _ = DQADimensionScore.objects.update_or_create(
            dqa=dqa,
            dimension=dimension,
            defaults={
                "score": score,
                "findings": findings,
                "updated_by": self.actor,
            },
        )
        self._log("update", instance, dqa=str(dqa.pk), dimension=dimension)
        return instance


class AccountabilityService(MEALService):
    """Complaint, feedback, and corrective action workflows."""

    model = None
    scheme_key = "complaint"
    transitions: ClassVar[dict[str, set[str]]] = {
        ComplaintStatus.RECEIVED: {
            ComplaintStatus.ASSIGNED,
            ComplaintStatus.RESOLVED,
            ComplaintStatus.WITHDRAWN,
        },
        ComplaintStatus.ASSIGNED: {
            ComplaintStatus.UNDER_INVESTIGATION,
            ComplaintStatus.RESOLVED,
            ComplaintStatus.WITHDRAWN,
        },
        ComplaintStatus.UNDER_INVESTIGATION: {
            ComplaintStatus.RESOLVED,
            ComplaintStatus.WITHDRAWN,
        },
        ComplaintStatus.RESOLVED: {ComplaintStatus.CLOSED},
        ComplaintStatus.WITHDRAWN: set(),
        ComplaintStatus.CLOSED: set(),
    }

    FEEDBACK_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        FeedbackStatus.RECEIVED: {FeedbackStatus.REVIEWED},
        FeedbackStatus.REVIEWED: {FeedbackStatus.RESPONDED},
        FeedbackStatus.RESPONDED: {FeedbackStatus.CLOSED},
        FeedbackStatus.CLOSED: set(),
    }

    CORRECTIVE_ACTION_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        CorrectiveActionStatus.OPEN: {
            CorrectiveActionStatus.IN_PROGRESS,
            CorrectiveActionStatus.CANCELLED,
        },
        CorrectiveActionStatus.IN_PROGRESS: {
            CorrectiveActionStatus.COMPLETED,
            CorrectiveActionStatus.CANCELLED,
        },
        CorrectiveActionStatus.COMPLETED: {CorrectiveActionStatus.VERIFIED},
        CorrectiveActionStatus.VERIFIED: {CorrectiveActionStatus.CLOSED},
        CorrectiveActionStatus.CANCELLED: set(),
        CorrectiveActionStatus.CLOSED: set(),
    }

    def _guard_confidential(self, instance) -> None:
        if getattr(instance, "is_confidential", False) and not (
            user_has_permission(self.actor, MEAL_VIEW_CONFIDENTIAL)
            or user_has_permission(self.actor, MEAL_MANAGE)
        ):
            raise PermissionDenied(
                _("This confidential record is restricted to authorized personnel.")
            )

    def update_complaint(self, *, instance, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        changed: list[str] = []
        for key, value in (fields or {}).items():
            if hasattr(instance, key) and getattr(instance, key) != value:
                setattr(instance, key, value)
                changed.append(key)
        if changed:
            instance.updated_by = self.actor
            instance.full_clean()
            instance.save()
            self._log("update", instance, changed_fields=changed)
        return instance

    def update_feedback(self, *, instance, fields: dict | None = None) -> Any:
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        changed: list[str] = []
        for key, value in (fields or {}).items():
            if hasattr(instance, key) and getattr(instance, key) != value:
                setattr(instance, key, value)
                changed.append(key)
        if changed:
            instance.updated_by = self.actor
            instance.full_clean()
            instance.save()
            self._log("update", instance, changed_fields=changed)
        return instance

    def assign_complaint(self, *, instance, assigned_officer, notes: str = "") -> Any:
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        instance.assigned_officer = assigned_officer
        if instance.status == ComplaintStatus.RECEIVED:
            instance.status = ComplaintStatus.ASSIGNED
        instance.updated_by = self.actor
        instance.save(
            update_fields=["assigned_officer", "status", "updated_by", "updated_at"]
        )
        self._history(instance, "ASSIGN", instance.status, instance.status, notes)
        self._log("assign", instance, officer=str(getattr(assigned_officer, "pk", "")))
        return instance

    def resolve_complaint(self, *, instance, resolution: str, notes: str = "") -> Any:
        if instance.status not in {
            ComplaintStatus.RECEIVED,
            ComplaintStatus.ASSIGNED,
            ComplaintStatus.UNDER_INVESTIGATION,
        }:
            raise InvalidStatusTransition(
                _("Complaint cannot be resolved in its current state.")
            )
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        from_status = instance.status
        instance.resolution = resolution
        instance.status = ComplaintStatus.RESOLVED
        instance.response_date = timezone.localdate()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "resolution",
                "status",
                "response_date",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(instance, "RESOLVE", from_status, ComplaintStatus.RESOLVED, notes)
        self._log("resolve", instance, complaint_id=str(instance.pk))
        return instance

    def close_complaint(self, *, instance, notes: str = "") -> Any:
        if instance.status != ComplaintStatus.RESOLVED:
            raise InvalidStatusTransition(_("Only resolved complaints can be closed."))
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        from_status = instance.status
        instance.status = ComplaintStatus.CLOSED
        instance.closed_by = self.actor
        instance.closed_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "closed_by",
                "closed_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(instance, "CLOSE", from_status, ComplaintStatus.CLOSED, notes)
        self._log("close", instance)
        return instance

    def respond_feedback(self, *, instance, response: str, notes: str = "") -> Any:
        if instance.status not in {FeedbackStatus.RECEIVED, FeedbackStatus.REVIEWED}:
            raise InvalidStatusTransition(
                _("Feedback cannot be responded to in its current state.")
            )
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        from_status = instance.status
        instance.response = response
        instance.response_date = timezone.localdate()
        instance.status = FeedbackStatus.RESPONDED
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "response",
                "response_date",
                "status",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(instance, "RESPOND", from_status, FeedbackStatus.RESPONDED, notes)
        self._log("respond", instance, feedback_id=str(instance.pk))
        return instance

    def close_feedback(self, *, instance, notes: str = "") -> Any:
        if instance.status != FeedbackStatus.RESPONDED:
            raise InvalidStatusTransition(_("Only responded feedback can be closed."))
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        self._guard_confidential(instance)
        from_status = instance.status
        instance.status = FeedbackStatus.CLOSED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(instance, "CLOSE", from_status, FeedbackStatus.CLOSED, notes)
        self._log("close", instance)
        return instance

    def complete_corrective_action(
        self, *, instance, resolution: str, notes: str = ""
    ) -> Any:
        if instance.status not in {
            CorrectiveActionStatus.OPEN,
            CorrectiveActionStatus.IN_PROGRESS,
        }:
            raise InvalidStatusTransition(
                _("Corrective action cannot be completed in its current state.")
            )
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        from_status = instance.status
        instance.resolution = resolution
        instance.status = CorrectiveActionStatus.COMPLETED
        instance.updated_by = self.actor
        instance.save(
            update_fields=["resolution", "status", "updated_by", "updated_at"]
        )
        self._history(
            instance, "COMPLETE", from_status, CorrectiveActionStatus.COMPLETED, notes
        )
        self._log("complete", instance)
        return instance

    def verify_corrective_action(self, *, instance, notes: str = "") -> Any:
        if instance.status != CorrectiveActionStatus.COMPLETED:
            raise InvalidStatusTransition(
                _("Only completed corrective actions can be verified.")
            )
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = CorrectiveActionStatus.VERIFIED
        instance.updated_by = self.actor
        instance.save(update_fields=["status", "updated_by", "updated_at"])
        self._history(
            instance, "VERIFY", from_status, CorrectiveActionStatus.VERIFIED, notes
        )
        self._log("verify", instance)
        return instance

    def close_corrective_action(self, *, instance, notes: str = "") -> Any:
        if instance.status != CorrectiveActionStatus.VERIFIED:
            raise InvalidStatusTransition(
                _("Only verified corrective actions can be closed.")
            )
        self._require_permission(MEAL_MANAGE_ACCOUNTABILITY)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = CorrectiveActionStatus.CLOSED
        instance.closed_by = self.actor
        instance.closed_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "closed_by",
                "closed_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(
            instance, "CLOSE", from_status, CorrectiveActionStatus.CLOSED, notes
        )
        self._log("close", instance)
        return instance


class LearningService(MEALService):
    """Outcome harvesting, learning logs, best practices, and lessons."""

    model = None
    scheme_key = "outcome_harvest"
    transitions: ClassVar[dict[str, set[str]]] = {
        OutcomeHarvestStatus.DRAFT: {OutcomeHarvestStatus.VALIDATED},
        OutcomeHarvestStatus.VALIDATED: {OutcomeHarvestStatus.APPROVED},
        OutcomeHarvestStatus.APPROVED: {OutcomeHarvestStatus.ARCHIVED},
        OutcomeHarvestStatus.ARCHIVED: set(),
    }

    LOG_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        LearningLogStatus.OPEN: {LearningLogStatus.IN_PROGRESS},
        LearningLogStatus.IN_PROGRESS: {LearningLogStatus.IMPLEMENTED},
        LearningLogStatus.IMPLEMENTED: {LearningLogStatus.CLOSED},
        LearningLogStatus.CLOSED: set(),
    }

    BEST_PRACTICE_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        BestPracticeStatus.DRAFT: {
            BestPracticeStatus.SUBMITTED,
            BestPracticeStatus.ARCHIVED,
        },
        BestPracticeStatus.SUBMITTED: {
            BestPracticeStatus.APPROVED,
            BestPracticeStatus.REJECTED,
        },
        BestPracticeStatus.APPROVED: {
            BestPracticeStatus.PUBLISHED,
            BestPracticeStatus.ARCHIVED,
        },
        BestPracticeStatus.REJECTED: {BestPracticeStatus.DRAFT},
        BestPracticeStatus.PUBLISHED: {BestPracticeStatus.ARCHIVED},
        BestPracticeStatus.ARCHIVED: set(),
    }

    LESSON_TRANSITIONS: ClassVar[dict[str, set[str]]] = {
        LessonStatus.DRAFT: {LessonStatus.REVIEWED, LessonStatus.ARCHIVED},
        LessonStatus.REVIEWED: {LessonStatus.APPROVED},
        LessonStatus.APPROVED: {LessonStatus.SHARED, LessonStatus.ARCHIVED},
        LessonStatus.SHARED: {LessonStatus.ARCHIVED},
        LessonStatus.ARCHIVED: set(),
    }

    def validate_harvest(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=OutcomeHarvestStatus.VALIDATED,
            permission_code=MEAL_MANAGE_LEARNING,
            notes=notes,
        )

    def approve_harvest(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=OutcomeHarvestStatus.APPROVED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def submit_best_practice(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=BestPracticeStatus.SUBMITTED,
            permission_code=MEAL_MANAGE_LEARNING,
            notes=notes,
        )

    def approve_best_practice(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=BestPracticeStatus.APPROVED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def reject_best_practice(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=BestPracticeStatus.REJECTED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def publish_best_practice(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=BestPracticeStatus.PUBLISHED,
            permission_code=MEAL_MANAGE_LEARNING,
            notes=notes,
        )

    def review_lesson(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=LessonStatus.REVIEWED,
            permission_code=MEAL_MANAGE_LEARNING,
            notes=notes,
        )

    def approve_lesson(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=LessonStatus.APPROVED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )

    def share_lesson(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=LessonStatus.SHARED,
            permission_code=MEAL_MANAGE_LEARNING,
            notes=notes,
        )


class ScorecardService(MEALService):
    """Organizational performance scorecards."""

    model = None
    scheme_key = "scorecard"
    transitions: ClassVar[dict[str, set[str]]] = {
        ScorecardStatus.DRAFT: {ScorecardStatus.PUBLISHED, ScorecardStatus.ARCHIVED},
        ScorecardStatus.PUBLISHED: {ScorecardStatus.ARCHIVED},
        ScorecardStatus.ARCHIVED: set(),
    }

    def publish(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=ScorecardStatus.PUBLISHED,
            permission_code=MEAL_MANAGE_SCORECARDS,
            notes=notes,
        )

    def add_dimension(self, *, scorecard, dimension: str, label: str, **fields) -> Any:
        self._require_permission(MEAL_MANAGE_SCORECARDS)
        from .models import ScorecardDimension

        instance = ScorecardDimension(
            scorecard=scorecard,
            dimension=dimension,
            label=label,
            created_by=self.actor,
            updated_by=self.actor,
            **fields,
        )
        instance.full_clean()
        instance.save()
        self._log("create", instance, scorecard=str(scorecard.pk))
        return instance


class ReportService(MEALService):
    """MEAL report approval workflow."""

    model = None
    scheme_key = "meal_report"
    transitions: ClassVar[dict[str, set[str]]] = {
        ReportStatus.DRAFT: {ReportStatus.SUBMITTED, ReportStatus.ARCHIVED},
        ReportStatus.SUBMITTED: {
            ReportStatus.APPROVED,
            ReportStatus.RETURNED,
        },
        ReportStatus.RETURNED: {ReportStatus.DRAFT},
        ReportStatus.APPROVED: {ReportStatus.ARCHIVED},
        ReportStatus.ARCHIVED: set(),
    }

    def submit(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=ReportStatus.SUBMITTED,
            permission_code=MEAL_SUBMIT,
            notes=notes,
        )

    def approve(self, *, instance, notes: str = "") -> Any:
        if instance.status != ReportStatus.SUBMITTED:
            raise InvalidStatusTransition(_("Only submitted reports can be approved."))
        self._require_permission(MEAL_APPROVE)
        self._require_record_access(instance)
        from_status = instance.status
        instance.status = ReportStatus.APPROVED
        instance.approved_by = self.actor
        instance.approved_at = timezone.now()
        instance.updated_by = self.actor
        instance.save(
            update_fields=[
                "status",
                "approved_by",
                "approved_at",
                "updated_by",
                "updated_at",
            ]
        )
        self._history(instance, "APPROVE", from_status, ReportStatus.APPROVED, notes)
        self._log("approve", instance, report_id=str(instance.pk))
        return instance

    def return_for_revision(self, *, instance, notes: str = "") -> Any:
        return self.transition(
            instance=instance,
            to_status=ReportStatus.RETURNED,
            permission_code=MEAL_APPROVE,
            notes=notes,
        )


def validate_export_permission(user) -> None:
    """Raise when the actor may not export MEAL registers."""
    if not user_has_permission(user, MEAL_EXPORT) and not user_has_permission(
        user, MEAL_MANAGE
    ):
        raise PermissionDenied(_("Permission denied for MEAL exports."))
