"""Permission-checked transactional services for program and project management."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import ClassVar

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
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
    BeneficiaryStatus,
    ChangeStatus,
    DeliverableStatus,
    MilestoneApprovalStatus,
    MilestoneStatus,
    ProgramStatus,
    ProjectClosureStatus,
    ProjectReportStatus,
    ProjectStatus,
    WBSNodeStatus,
    WBSNodeType,
)
from .models import (
    Activity,
    BeneficiaryParticipation,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    EvidenceRecord,
    EvidenceVersion,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    Program,
    ProgramDocument,
    ProgramStatusHistory,
    Project,
    ProjectClosure,
    ProjectReport,
    ProjectResult,
    ProjectStatusHistory,
    ProjectTimeline,
    ResourceAllocation,
    Task,
    WBSNode,
    WorkPlan,
)
from .permissions import (
    PROGRAMMES_ARCHIVE,
    PROGRAMMES_CREATE,
    PROGRAMMES_DELETE,
    PROGRAMMES_MANAGE,
    PROGRAMMES_RESTORE,
    PROGRAMMES_UPDATE,
    PROJECTS_ARCHIVE,
    PROJECTS_CREATE,
    PROJECTS_DELETE,
    PROJECTS_MANAGE,
    PROJECTS_RESTORE,
    PROJECTS_UPDATE,
)
from .selectors import user_can_access_program, user_can_access_project

logger = logging.getLogger(__name__)

PROGRAM_TRANSITIONS: dict[str, set[str]] = {
    ProgramStatus.DRAFT: {
        ProgramStatus.PROPOSED,
        ProgramStatus.CANCELLED,
    },
    ProgramStatus.PROPOSED: {
        ProgramStatus.DRAFT,
        ProgramStatus.PENDING_APPROVAL,
        ProgramStatus.CANCELLED,
    },
    ProgramStatus.PENDING_APPROVAL: {
        ProgramStatus.PROPOSED,
        ProgramStatus.APPROVED,
        ProgramStatus.CANCELLED,
    },
    ProgramStatus.APPROVED: {
        ProgramStatus.ACTIVE,
        ProgramStatus.ON_HOLD,
        ProgramStatus.CANCELLED,
    },
    ProgramStatus.ACTIVE: {
        ProgramStatus.ON_HOLD,
        ProgramStatus.DELAYED,
        ProgramStatus.SUSPENDED,
        ProgramStatus.COMPLETED,
    },
    ProgramStatus.ON_HOLD: {
        ProgramStatus.ACTIVE,
        ProgramStatus.DELAYED,
        ProgramStatus.SUSPENDED,
        ProgramStatus.CLOSED,
    },
    ProgramStatus.DELAYED: {
        ProgramStatus.ACTIVE,
        ProgramStatus.ON_HOLD,
        ProgramStatus.SUSPENDED,
    },
    ProgramStatus.SUSPENDED: {
        ProgramStatus.ACTIVE,
        ProgramStatus.ON_HOLD,
        ProgramStatus.CLOSED,
        ProgramStatus.CANCELLED,
    },
    ProgramStatus.COMPLETED: {ProgramStatus.CLOSED},
    ProgramStatus.CLOSED: set(),
    ProgramStatus.ARCHIVED: set(),
    ProgramStatus.CANCELLED: set(),
}

PROJECT_TRANSITIONS: dict[str, set[str]] = {
    ProjectStatus.CONCEPT: {
        ProjectStatus.PROPOSAL,
        ProjectStatus.PLANNING,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.PROPOSAL: {
        ProjectStatus.CONCEPT,
        ProjectStatus.PLANNING,
        ProjectStatus.APPROVAL,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.PLANNING: {
        ProjectStatus.PROPOSAL,
        ProjectStatus.APPROVAL,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.APPROVAL: {
        ProjectStatus.PLANNING,
        ProjectStatus.INITIATION,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.INITIATION: {
        ProjectStatus.EXECUTION,
        ProjectStatus.MONITORING,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.EXECUTION: {
        ProjectStatus.MONITORING,
        ProjectStatus.COMPLETION,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.MONITORING: {
        ProjectStatus.EXECUTION,
        ProjectStatus.COMPLETION,
        ProjectStatus.ARCHIVED,
    },
    ProjectStatus.COMPLETION: {ProjectStatus.CLOSURE},
    ProjectStatus.CLOSURE: {ProjectStatus.ARCHIVED},
    ProjectStatus.ARCHIVED: set(),
}

PROGRAM_APPROVAL_STATUSES = (ProgramStatus.APPROVED,)
PROJECT_APPROVAL_STATUSES = (ProjectStatus.APPROVAL,)


def _require_permission(user, permission_code: str, manage_code: str) -> None:
    if not user or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(_("An authenticated actor is required."))
    if not (
        user_has_permission(user, permission_code)
        or user_has_permission(user, manage_code)
    ):
        raise PermissionDenied(_("Permission denied for this program action."))


def _log_event(action: str, instance, actor, **details) -> None:
    logger.info(
        "programs_domain_event",
        extra={
            "programs_event": {
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
        module=ReferenceModules.PROGRAMS,
        record_type=scheme_code,
        scheme_code=scheme_code,
        notes=f"Phase 15 {scheme_code} reference reservation.",
    )


def _confirm_reference(actor, reference, instance) -> None:
    ConfirmReferenceAssignmentService(user=actor).execute(
        reference=reference,
        record_id=instance.pk,
        notes=f"Assigned to {type(instance).__name__}.",
    )


class ProgramService(BaseService):
    """Create, update, transition, archive, and restore program profiles."""

    CREATE_FIELDS: ClassVar[set[str]] = {
        field.name
        for field in Program._meta.fields
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
            "approved_by",
            "approved_at",
        }
    }
    UPDATE_FIELDS: ClassVar[set[str]] = set(CREATE_FIELDS)

    @transaction.atomic
    def create(self, **fields) -> Program:
        _require_permission(self.user, PROGRAMMES_CREATE, PROGRAMMES_MANAGE)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in ("pillars", "sdgs", "funding_sources")
            if name in fields
        }
        disallowed = set(fields) - self.CREATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported program fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        reference = _reserve_reference(self.user, "program")
        program = Program(
            reference_number=reference.reference_number,
            status=ProgramStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        program.full_clean()
        program.save()
        for name, values in taxonomy_fields.items():
            if values:
                getattr(program, name).set(values)
        _confirm_reference(self.user, reference, program)
        ProgramStatusHistory.objects.create(
            program=program,
            from_status=ProgramStatus.DRAFT,
            to_status=ProgramStatus.DRAFT,
            changed_by=self.user,
            reason="Program registered.",
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("program.created", program, self.user)
        return program

    @transaction.atomic
    def update(self, program: Program, **fields) -> Program:
        _require_permission(self.user, PROGRAMMES_UPDATE, PROGRAMMES_MANAGE)
        if not user_can_access_program(self.user, program):
            raise PermissionDenied(
                _("This program record is outside your access scope.")
            )
        program = Program.objects.select_for_update().get(pk=program.pk)
        taxonomy_fields = {
            name: fields.pop(name)
            for name in ("pillars", "sdgs", "funding_sources")
            if name in fields
        }
        disallowed = set(fields) - self.UPDATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported program fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        changed = []
        for name, value in fields.items():
            if getattr(program, name) != value:
                setattr(program, name, value)
                changed.append(name)
        program.updated_by = self.user
        program.full_clean()
        program.save()
        for name, values in taxonomy_fields.items():
            getattr(program, name).set(values)
        _log_event("program.updated", program, self.user, fields=changed)
        return program

    @transaction.atomic
    def change_status(self, program: Program, new_status: str, reason: str) -> Program:
        _require_permission(self.user, PROGRAMMES_UPDATE, PROGRAMMES_MANAGE)
        if not user_can_access_program(self.user, program):
            raise PermissionDenied(
                _("This program record is outside your access scope.")
            )
        program = Program.objects.select_for_update().get(pk=program.pk)
        old_status = program.status
        if new_status not in PROGRAM_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                _("Transition from %(old)s to %(new)s is not allowed.")
                % {"old": old_status, "new": new_status},
                code="invalid_program_transition",
            )
        if not reason.strip():
            raise ValidationError({"reason": _("A transition reason is required.")})
        if new_status in PROGRAM_APPROVAL_STATUSES:
            if program.created_by_id == self.user.pk:
                raise ValidationError(
                    _("Program creators cannot approve their own programs."),
                    code="program_self_approval",
                )
            program.approved_by = self.user
            program.approved_at = timezone.now()
        program.status = new_status
        program.updated_by = self.user
        program.full_clean()
        program.save()
        ProgramStatusHistory.objects.create(
            program=program,
            from_status=old_status,
            to_status=new_status,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event(
            "program.status_changed",
            program,
            self.user,
            from_status=old_status,
            to_status=new_status,
        )
        return program

    @transaction.atomic
    def archive(self, program: Program, reason: str) -> Program:
        _require_permission(self.user, PROGRAMMES_ARCHIVE, PROGRAMMES_MANAGE)
        if not user_can_access_program(self.user, program):
            raise PermissionDenied(
                _("This program record is outside your access scope.")
            )
        program = Program.objects.select_for_update().get(pk=program.pk)
        if program.is_archived:
            raise ValidationError(_("Program is already archived."))
        if not reason.strip():
            raise ValidationError({"reason": _("An archive reason is required.")})
        old_status = program.status
        program.status = ProgramStatus.ARCHIVED
        program.is_archived = True
        program.archived_at = timezone.now()
        program.archived_by = self.user
        program.updated_by = self.user
        program.save()
        ProgramStatusHistory.objects.create(
            program=program,
            from_status=old_status,
            to_status=ProgramStatus.ARCHIVED,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("program.archived", program, self.user, reason=reason)
        return program

    @transaction.atomic
    def restore(self, program: Program, reason: str) -> Program:
        _require_permission(self.user, PROGRAMMES_RESTORE, PROGRAMMES_MANAGE)
        if not user_can_access_program(self.user, program, include_archived=True):
            raise PermissionDenied(
                _("This program record is outside your access scope.")
            )
        program = Program.all_objects.select_for_update().get(pk=program.pk)
        if not program.is_archived:
            raise ValidationError(_("Program is not archived."))
        program.is_archived = False
        program.archived_at = None
        program.archived_by = None
        program.status = ProgramStatus.DRAFT
        program.updated_by = self.user
        program.save()
        ProgramStatusHistory.objects.create(
            program=program,
            from_status=ProgramStatus.ARCHIVED,
            to_status=ProgramStatus.DRAFT,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("program.restored", program, self.user, reason=reason)
        return program

    @transaction.atomic
    def soft_delete(self, program: Program, deleted_by=None) -> Program:
        _require_permission(self.user, PROGRAMMES_DELETE, PROGRAMMES_MANAGE)
        program = Program.objects.select_for_update().get(pk=program.pk)
        program.delete(deleted_by=self.user)
        _log_event("program.soft_deleted", program, self.user)
        return program


class ProjectService(BaseService):
    """Create, update, transition, archive, and restore project profiles."""

    CREATE_FIELDS: ClassVar[set[str]] = {
        field.name
        for field in Project._meta.fields
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
            "approved_by",
            "approved_at",
        }
    } | {field.name for field in Project._meta.get_fields() if field.many_to_many}
    UPDATE_FIELDS: ClassVar[set[str]] = set(CREATE_FIELDS)

    _M2M_FIELDS: ClassVar[frozenset[str]] = frozenset(
        field.name for field in Project._meta.get_fields() if field.many_to_many
    )

    @transaction.atomic
    def create(self, program: Program, **fields) -> Project:
        _require_permission(self.user, PROJECTS_CREATE, PROJECTS_MANAGE)
        if not user_can_access_program(self.user, program):
            raise PermissionDenied(
                _("This program record is outside your access scope.")
            )
        if program.status not in {
            ProgramStatus.ACTIVE,
            ProgramStatus.ON_HOLD,
            ProgramStatus.APPROVED,
            ProgramStatus.DELAYED,
        }:
            raise ValidationError(
                _("Projects can only be registered under active programs.")
            )
        disallowed = set(fields) - self.CREATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported project fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        reference = _reserve_reference(self.user, "project")
        m2m_fields = {
            name: fields.pop(name) for name in list(fields) if name in self._M2M_FIELDS
        }
        project = Project(
            program=program,
            reference_number=reference.reference_number,
            status=ProjectStatus.CONCEPT,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        project.full_clean()
        project.save()
        for name, values in m2m_fields.items():
            getattr(project, name).set(values)
        _confirm_reference(self.user, reference, project)
        ProjectStatusHistory.objects.create(
            project=project,
            from_status=ProjectStatus.CONCEPT,
            to_status=ProjectStatus.CONCEPT,
            changed_by=self.user,
            reason="Project registered.",
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("project.created", project, self.user)
        return project

    @transaction.atomic
    def update(self, project: Project, **fields) -> Project:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(
                _("This project record is outside your access scope.")
            )
        project = Project.objects.select_for_update().get(pk=project.pk)
        disallowed = set(fields) - self.UPDATE_FIELDS
        if disallowed:
            raise ValidationError(
                _("Unsupported project fields: %(fields)s")
                % {"fields": ", ".join(sorted(disallowed))}
            )
        changed = []
        m2m_fields = {
            name: fields.pop(name) for name in list(fields) if name in self._M2M_FIELDS
        }
        for name, value in fields.items():
            if getattr(project, name) != value:
                setattr(project, name, value)
                changed.append(name)
        project.updated_by = self.user
        project.full_clean()
        project.save()
        for name, values in m2m_fields.items():
            if set(getattr(project, name).values_list("pk", flat=True)) != set(values):
                getattr(project, name).set(values)
                changed.append(name)
        _log_event("project.updated", project, self.user, fields=changed)
        return project

    @transaction.atomic
    def change_status(self, project: Project, new_status: str, reason: str) -> Project:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(
                _("This project record is outside your access scope.")
            )
        project = Project.objects.select_for_update().get(pk=project.pk)
        old_status = project.status
        if new_status not in PROJECT_TRANSITIONS.get(old_status, set()):
            raise ValidationError(
                _("Transition from %(old)s to %(new)s is not allowed.")
                % {"old": old_status, "new": new_status},
                code="invalid_project_transition",
            )
        if not reason.strip():
            raise ValidationError({"reason": _("A transition reason is required.")})
        if new_status in PROJECT_APPROVAL_STATUSES:
            if project.created_by_id == self.user.pk:
                raise ValidationError(
                    _("Project creators cannot approve their own projects."),
                    code="project_self_approval",
                )
            project.approved_by = self.user
            project.approved_at = timezone.now()
        project.status = new_status
        project.updated_by = self.user
        project.full_clean()
        project.save()
        ProjectStatusHistory.objects.create(
            project=project,
            from_status=old_status,
            to_status=new_status,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event(
            "project.status_changed",
            project,
            self.user,
            from_status=old_status,
            to_status=new_status,
        )
        return project

    @transaction.atomic
    def archive(self, project: Project, reason: str) -> Project:
        _require_permission(self.user, PROJECTS_ARCHIVE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(
                _("This project record is outside your access scope.")
            )
        project = Project.objects.select_for_update().get(pk=project.pk)
        if project.is_archived:
            raise ValidationError(_("Project is already archived."))
        if not reason.strip():
            raise ValidationError({"reason": _("An archive reason is required.")})
        old_status = project.status
        project.status = ProjectStatus.ARCHIVED
        project.is_archived = True
        project.archived_at = timezone.now()
        project.archived_by = self.user
        project.updated_by = self.user
        project.save()
        ProjectStatusHistory.objects.create(
            project=project,
            from_status=old_status,
            to_status=ProjectStatus.ARCHIVED,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("project.archived", project, self.user, reason=reason)
        return project

    @transaction.atomic
    def restore(self, project: Project, reason: str) -> Project:
        _require_permission(self.user, PROJECTS_RESTORE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project, include_archived=True):
            raise PermissionDenied(
                _("This project record is outside your access scope.")
            )
        project = Project.all_objects.select_for_update().get(pk=project.pk)
        if not project.is_archived:
            raise ValidationError(_("Project is not archived."))
        project.is_archived = False
        project.archived_at = None
        project.archived_by = None
        project.status = ProjectStatus.CONCEPT
        project.updated_by = self.user
        project.save()
        ProjectStatusHistory.objects.create(
            project=project,
            from_status=ProjectStatus.ARCHIVED,
            to_status=ProjectStatus.CONCEPT,
            changed_by=self.user,
            reason=reason,
            created_by=self.user,
            updated_by=self.user,
        )
        _log_event("project.restored", project, self.user, reason=reason)
        return project

    @transaction.atomic
    def soft_delete(self, project: Project, deleted_by=None) -> Project:
        _require_permission(self.user, PROJECTS_DELETE, PROJECTS_MANAGE)
        project = Project.objects.select_for_update().get(pk=project.pk)
        project.delete(deleted_by=self.user)
        _log_event("project.soft_deleted", project, self.user)
        return project


class ProgramDocumentService(BaseService):
    """Upload and archive protected program and project documents."""

    @transaction.atomic
    def upload(
        self,
        program: Program | None,
        project: Project | None,
        title: str,
        file,
        document_type=None,
        description: str = "",
    ) -> ProgramDocument:
        if program is None and project is None:
            raise ValidationError(_("A document requires a program or a project."))
        if program is not None:
            _require_permission(self.user, PROGRAMMES_UPDATE, PROGRAMMES_MANAGE)
            if not user_can_access_program(self.user, program):
                raise PermissionDenied(
                    _("This program record is outside your access scope.")
                )
        if project is not None:
            _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
            if not user_can_access_project(self.user, project):
                raise PermissionDenied(
                    _("This project record is outside your access scope.")
                )
        document = ProgramDocument(
            program=program,
            project=project,
            title=title,
            file=file,
            original_filename=getattr(file, "name", ""),
            file_size=getattr(file, "size", None),
            document_type=document_type,
            description=description,
            created_by=self.user,
            updated_by=self.user,
        )
        document.full_clean()
        document.save()
        _log_event(
            "document.uploaded",
            document,
            self.user,
            program_id=str(getattr(program, "pk", "")),
            project_id=str(getattr(project, "pk", "")),
        )
        return document

    @transaction.atomic
    def archive(self, document: ProgramDocument, reason: str = "") -> ProgramDocument:
        if document.program_id is not None:
            _require_permission(self.user, PROGRAMMES_UPDATE, PROGRAMMES_MANAGE)
            if not user_can_access_program(self.user, document.program):
                raise PermissionDenied(
                    _("This program record is outside your access scope.")
                )
        if document.project_id is not None:
            _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
            if not user_can_access_project(self.user, document.project):
                raise PermissionDenied(
                    _("This project record is outside your access scope.")
                )
        document = ProgramDocument.objects.select_for_update().get(pk=document.pk)
        document.status = "ARCHIVED"
        document.updated_by = self.user
        document.save()
        _log_event("document.archived", document, self.user, reason=reason)
        return document


class ProgramChildRecordService(BaseService):
    """Create and manage child records scoped to a program or project.

    The service resolves the owning record, enforces the scoped write
    permission, allocates a reference number for models that carry one, and
    persists the record transactionally.  ``reference_scheme_key`` must be a
    key present in :data:`REFERENCE_SCHEME_CODES` when the target model has a
    ``reference_number`` field.
    """

    REFERENCE_FIELDS: ClassVar[dict[type, str]] = {
        cls: "reference_number"
        for cls in (
            WorkPlan,
            Activity,
            Task,
            Deliverable,
            Issue,
            ChangeRequest,
            EvidenceRecord,
            BeneficiaryRecord,
            ResourceAllocation,
            ProcurementRequest,
            LessonsLearned,
            WBSNode,
        )
    }

    def __init__(self, user=None):
        super().__init__(user=user)
        self._reserved_references: list = []

    @transaction.atomic
    def create(
        self,
        model_cls,
        *,
        program: Program | None = None,
        project: Project | None = None,
        fields: dict | None = None,
    ) -> object:
        fields = dict(fields or {})
        if program is None and project is None:
            raise ValidationError(_("A parent program or project is required."))
        if program is not None:
            _require_permission(self.user, PROGRAMMES_UPDATE, PROGRAMMES_MANAGE)
            if not user_can_access_program(self.user, program):
                raise PermissionDenied(
                    _("This program record is outside your access scope.")
                )
            if _model_has_field(model_cls, "program"):
                fields["program"] = program
        if project is not None:
            _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
            if not user_can_access_project(self.user, project):
                raise PermissionDenied(
                    _("This project record is outside your access scope.")
                )
            if _model_has_field(model_cls, "project"):
                fields["project"] = project
        self._populate_reference(model_cls, fields)
        fields.setdefault("created_by", self.user)
        fields.setdefault("updated_by", self.user)
        instance = model_cls(**fields)
        instance.full_clean()
        instance.save()
        self._confirm_references(instance)
        _log_event(
            "child_record.created",
            instance,
            self.user,
            model=model_cls.__name__,
            program_id=str(getattr(program, "pk", "")),
            project_id=str(getattr(project, "pk", "")),
        )
        return instance

    @transaction.atomic
    def update(self, instance, fields: dict | None = None) -> object:
        fields = dict(fields or {})
        parent = getattr(instance, "program", None) or getattr(
            instance, "project", None
        )
        if parent is None:
            raise ValidationError(_("The child record has no parent scope."))
        _require_permission(self.user, PROGRAMMES_UPDATE, PROJECTS_UPDATE)
        if isinstance(parent, Project):
            _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
            if not user_can_access_project(self.user, parent):
                raise PermissionDenied(
                    _("This project record is outside your access scope.")
                )
        else:
            if not user_can_access_program(self.user, parent):
                raise PermissionDenied(
                    _("This program record is outside your access scope.")
                )
        fields.setdefault("updated_by", self.user)
        for name, value in fields.items():
            setattr(instance, name, value)
        instance.full_clean()
        instance.save()
        _log_event(
            "child_record.updated",
            instance,
            self.user,
            model=type(instance).__name__,
        )
        return instance

    def _populate_reference(self, model_cls, fields: dict) -> None:
        if model_cls not in self.REFERENCE_FIELDS:
            return
        field_name = self.REFERENCE_FIELDS[model_cls]
        scheme_key = _reference_scheme_key_for_model(model_cls)
        if scheme_key is None:
            return
        reference = _reserve_reference(self.user, scheme_key)
        fields[field_name] = reference.reference_number
        self._reserved_references.append((reference, model_cls))

    def _confirm_references(self, instance) -> None:
        for reference, model_cls in self._reserved_references:
            if type(instance) is model_cls:
                _confirm_reference(self.user, reference, instance)
        self._reserved_references.clear()


def _reference_scheme_key_for_model(model_cls) -> str | None:
    mapping = {
        WorkPlan: "work_plan",
        Activity: "activity",
        Task: "task",
        Milestone: "milestone",
        Deliverable: "deliverable",
        Issue: "issue",
        ChangeRequest: "change",
        EvidenceRecord: "evidence",
        BeneficiaryRecord: "program_beneficiary",
        ResourceAllocation: "resource",
        ProcurementRequest: "procurement",
        LessonsLearned: "lesson",
        WBSNode: "wbs",
    }
    return mapping.get(model_cls)


def _model_has_field(model_cls, field_name: str) -> bool:
    return field_name in {field.name for field in model_cls._meta.fields}


class WbsService(BaseService):
    """Manage Work Breakdown Structure trees with progress roll-up."""

    @transaction.atomic
    def create_node(
        self, project: Project, *, parent: WBSNode | None = None, **fields
    ) -> WBSNode:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(_("This project is outside your access scope."))
        if parent is not None and parent.project_id != project.pk:
            raise ValidationError(_("The parent node must belong to the same project."))
        if parent is not None and parent.node_type == WBSNodeType.TASK:
            raise ValidationError(
                _("Tasks may not have child WBS nodes below sub-task level.")
            )
        reference = _reserve_reference(self.user, "wbs")
        instance = WBSNode(
            project=project,
            parent=parent,
            reference_number=reference.reference_number,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        instance.full_clean()
        instance.save()
        _confirm_reference(self.user, reference, instance)
        if parent is not None:
            self._rollup(parent)
        _log_event(
            "wbs.node_created",
            instance,
            self.user,
            project_id=str(project.pk),
            parent_id=str(getattr(parent, "pk", "")),
        )
        return instance

    @transaction.atomic
    def update_node(self, node: WBSNode, **fields) -> WBSNode:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, node.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        node = WBSNode.objects.select_for_update().get(pk=node.pk)
        old_parent_id = node.parent_id
        for name, value in fields.items():
            setattr(node, name, value)
        node.updated_by = self.user
        node.full_clean()
        node.save()
        self._rollup(node)
        if node.parent_id != old_parent_id and old_parent_id is not None:
            old_parent = WBSNode.objects.filter(pk=old_parent_id).first()
            if old_parent:
                self._rollup(old_parent)
        _log_event(
            "wbs.node_updated",
            node,
            self.user,
            project_id=str(node.project_id),
        )
        return node

    @transaction.atomic
    def delete_node(self, node: WBSNode) -> None:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, node.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        node = WBSNode.objects.select_for_update().get(pk=node.pk)
        parent_id = node.parent_id
        node.delete()
        if parent_id:
            parent = WBSNode.objects.filter(pk=parent_id).first()
            if parent:
                self._rollup(parent)
        _log_event(
            "wbs.node_deleted",
            node,
            self.user,
            project_id=str(node.project_id),
        )

    def _rollup(self, node: WBSNode) -> None:
        """Recalculate a node's completion and effort from its children."""
        children = list(node.children.all())
        if not children:
            return
        avg = sum(float(child.completion_percentage) for child in children) / len(
            children
        )
        node.completion_percentage = Decimal(str(round(avg, 2)))
        node.actual_effort_hours = (
            sum((child.actual_effort_hours or Decimal("0")) for child in children)
            if all(child.actual_effort_hours is not None for child in children)
            else None
        )
        if all(child.status == WBSNodeStatus.COMPLETED for child in children):
            node.status = WBSNodeStatus.COMPLETED
        elif any(child.status == WBSNodeStatus.IN_PROGRESS for child in children):
            node.status = WBSNodeStatus.IN_PROGRESS
        elif any(child.status == WBSNodeStatus.DELAYED for child in children):
            node.status = WBSNodeStatus.DELAYED
        node.save(
            update_fields=["completion_percentage", "actual_effort_hours", "status"]
        )
        if node.parent is not None:
            self._rollup(node.parent)


def _recalculate_project_progress(project: Project) -> None:
    """Derive project completion from WBS leaves, tasks, and milestones."""
    nodes = WBSNode.objects.filter(project=project)
    completed_nodes = nodes.filter(status=WBSNodeStatus.COMPLETED).count()
    total_nodes = nodes.count()
    components = []
    if total_nodes:
        components.append(completed_nodes / total_nodes)
    tasks = Task.objects.filter(activity__work_plan__project=project)
    total_tasks = tasks.count()
    if total_tasks:
        completed_tasks = tasks.filter(status="COMPLETED").count()
        components.append(completed_tasks / total_tasks)
    milestones = Milestone.objects.filter(project=project)
    total_milestones = milestones.count()
    if total_milestones:
        completed_milestones = milestones.filter(
            status=MilestoneStatus.ACHIEVED
        ).count()
        components.append(completed_milestones / total_milestones)
    if not components:
        return
    average = round((sum(components) / len(components)) * 100, 2)
    project.completion_percentage = Decimal(str(average))
    project.save(update_fields=["completion_percentage", "updated_at"])


class ProjectApprovalService(BaseService):
    """Submit, approve, and reject milestones and deliverables."""

    @transaction.atomic
    def submit_milestone(self, milestone: Milestone, notes: str = "") -> Milestone:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, milestone.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        milestone = Milestone.objects.select_for_update().get(pk=milestone.pk)
        if milestone.approval_status != MilestoneApprovalStatus.PENDING:
            raise ValidationError(
                _("Only pending milestones can be submitted for approval.")
            )
        milestone.approval_status = MilestoneApprovalStatus.SUBMITTED
        milestone.submitted_by = self.user
        milestone.submitted_at = timezone.now()
        milestone.approval_notes = notes
        milestone.updated_by = self.user
        milestone.save()
        _log_event("milestone.submitted", milestone, self.user)
        return milestone

    @transaction.atomic
    def approve_milestone(self, milestone: Milestone, notes: str = "") -> Milestone:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, milestone.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        milestone = Milestone.objects.select_for_update().get(pk=milestone.pk)
        if milestone.approval_status != MilestoneApprovalStatus.SUBMITTED:
            raise ValidationError(_("Only submitted milestones can be approved."))
        if milestone.submitted_by_id == self.user.pk:
            raise ValidationError(
                _("Milestones cannot be approved by their submitter."),
                code="milestone_self_approval",
            )
        milestone.approval_status = MilestoneApprovalStatus.APPROVED
        milestone.approved_by = self.user
        milestone.approved_at = timezone.now()
        milestone.approval_notes = notes
        milestone.updated_by = self.user
        milestone.save()
        if milestone.status in {MilestoneStatus.PLANNED, MilestoneStatus.IN_PROGRESS}:
            milestone.status = MilestoneStatus.ACHIEVED
            milestone.completion_date = timezone.localdate()
            milestone.save(update_fields=["status", "completion_date"])
            _recalculate_project_progress(milestone.project)
        _log_event("milestone.approved", milestone, self.user)
        return milestone

    @transaction.atomic
    def reject_milestone(self, milestone: Milestone, notes: str) -> Milestone:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, milestone.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        if not notes.strip():
            raise ValidationError({"notes": _("A rejection reason is required.")})
        milestone = Milestone.objects.select_for_update().get(pk=milestone.pk)
        if milestone.approval_status != MilestoneApprovalStatus.SUBMITTED:
            raise ValidationError(_("Only submitted milestones can be rejected."))
        milestone.approval_status = MilestoneApprovalStatus.REJECTED
        milestone.approval_notes = notes
        milestone.updated_by = self.user
        milestone.save()
        _log_event("milestone.rejected", milestone, self.user)
        return milestone

    @transaction.atomic
    def submit_deliverable(
        self, deliverable: Deliverable, notes: str = ""
    ) -> Deliverable:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, deliverable.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        deliverable = Deliverable.objects.select_for_update().get(pk=deliverable.pk)
        if deliverable.status not in {
            DeliverableStatus.PENDING,
            DeliverableStatus.IN_PROGRESS,
        }:
            raise ValidationError(_("Only active deliverables can be submitted."))
        deliverable.status = DeliverableStatus.SUBMITTED
        deliverable.submitted_by = self.user
        deliverable.submitted_at = timezone.now()
        deliverable.approval_notes = notes
        deliverable.updated_by = self.user
        deliverable.save()
        _log_event("deliverable.submitted", deliverable, self.user)
        return deliverable

    @transaction.atomic
    def approve_deliverable(
        self, deliverable: Deliverable, notes: str = ""
    ) -> Deliverable:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, deliverable.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        deliverable = Deliverable.objects.select_for_update().get(pk=deliverable.pk)
        if deliverable.status != DeliverableStatus.SUBMITTED:
            raise ValidationError(_("Only submitted deliverables can be approved."))
        if deliverable.submitted_by_id == self.user.pk:
            raise ValidationError(
                _("Deliverables cannot be approved by their submitter."),
                code="deliverable_self_approval",
            )
        deliverable.status = DeliverableStatus.APPROVED
        deliverable.approved_by = self.user
        deliverable.approved_at = timezone.now()
        deliverable.approval_notes = notes
        deliverable.updated_by = self.user
        deliverable.save()
        _log_event("deliverable.approved", deliverable, self.user)
        return deliverable

    @transaction.atomic
    def reject_deliverable(self, deliverable: Deliverable, notes: str) -> Deliverable:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, deliverable.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        if not notes.strip():
            raise ValidationError({"notes": _("A rejection reason is required.")})
        deliverable = Deliverable.objects.select_for_update().get(pk=deliverable.pk)
        if deliverable.status != DeliverableStatus.SUBMITTED:
            raise ValidationError(_("Only submitted deliverables can be rejected."))
        deliverable.status = DeliverableStatus.REJECTED
        deliverable.approval_notes = notes
        deliverable.updated_by = self.user
        deliverable.save()
        _log_event("deliverable.rejected", deliverable, self.user)
        return deliverable


class ChangeRequestService(BaseService):
    """Decide change requests and auto-apply approved scope changes."""

    @transaction.atomic
    def decide(
        self,
        change: ChangeRequest,
        decision: str,
        reviewer_notes: str = "",
    ) -> ChangeRequest:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, change.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        change = ChangeRequest.objects.select_for_update().get(pk=change.pk)
        if change.status not in {
            ChangeStatus.DRAFT,
            ChangeStatus.SUBMITTED,
            ChangeStatus.PENDING_APPROVAL,
        }:
            raise ValidationError(_("Only pending change requests can be decided."))
        if change.created_by_id == self.user.pk:
            raise ValidationError(
                _("Change requests cannot be decided by their creator."),
                code="change_self_review",
            )
        if decision not in {"APPROVED", "REJECTED"}:
            raise ValidationError(_("Decision must be APPROVED or REJECTED."))
        change.status = decision
        change.reviewer = self.user
        change.reviewer_notes = reviewer_notes
        change.reviewed_at = timezone.now()
        change.decision_notes = reviewer_notes
        change.decided_by = self.user
        change.decided_at = timezone.now()
        change.updated_by = self.user
        change.save()
        if decision == "APPROVED":
            self._apply_approved_change(change)
        _log_event("change_request.decided", change, self.user, decision=decision)
        return change

    def _apply_approved_change(self, change: ChangeRequest) -> None:
        target = change.target_model or ""
        key = (target.lower(), (change.target_field or "").lower())
        field = change.target_field
        value = change.proposed_value
        if key == ("project", "end_date"):
            Project.objects.filter(pk=change.project_id).update(end_date=value)
        elif key == ("project", "budget"):
            Project.objects.filter(pk=change.project_id).update(total_budget=value)
        elif key == ("project", "description"):
            Project.objects.filter(pk=change.project_id).update(description=value)
        elif target and field and value is not None:
            model = _resolve_change_target_model(target)
            if model is not None:
                model.objects.filter(pk=change.target_record_id).update(
                    **{field: value}
                )
        if field:
            _log_event(
                "change_request.applied",
                change,
                self.user,
                target_model=target,
                target_field=field,
            )


def _resolve_change_target_model(target: str):
    from .models import Activity, Deliverable, Issue, Milestone, Project, Task

    mapping = {
        "activity": Activity,
        "task": Task,
        "milestone": Milestone,
        "deliverable": Deliverable,
        "issue": Issue,
        "project": Project,
    }
    return mapping.get(target.lower())


class ProjectClosureService(BaseService):
    """Manage structured project closure records."""

    @transaction.atomic
    def create(self, project: Project, **fields) -> ProjectClosure:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(_("This project is outside your access scope."))
        if ProjectClosure.objects.filter(project=project).exists():
            raise ValidationError(_("This project already has a closure record."))
        if project.status != ProjectStatus.COMPLETION:
            raise ValidationError(
                _("Closure records require a project in Completion status.")
            )
        closure = ProjectClosure(
            project=project,
            status=ProjectClosureStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        closure.full_clean()
        closure.save()
        _log_event("closure.created", closure, self.user)
        return closure

    @transaction.atomic
    def verify(self, closure: ProjectClosure, notes: str = "") -> ProjectClosure:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, closure.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        closure = ProjectClosure.objects.select_for_update().get(pk=closure.pk)
        if closure.status != ProjectClosureStatus.DRAFT:
            raise ValidationError(_("Only draft closures can be verified."))
        closure.status = ProjectClosureStatus.VERIFIED
        closure.closed_by = self.user
        closure.closure_date = closure.closure_date or timezone.localdate()
        closure.closure_notes = notes or closure.closure_notes
        closure.updated_by = self.user
        closure.save()
        _log_event("closure.verified", closure, self.user)
        return closure

    @transaction.atomic
    def approve(self, closure: ProjectClosure, notes: str = "") -> ProjectClosure:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, closure.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        closure = ProjectClosure.objects.select_for_update().get(pk=closure.pk)
        if closure.status != ProjectClosureStatus.VERIFIED:
            raise ValidationError(_("Only verified closures can be approved."))
        if closure.closed_by_id == self.user.pk:
            raise ValidationError(
                _("Closures cannot be approved by their verifier."),
                code="closure_self_approval",
            )
        closure.status = ProjectClosureStatus.APPROVED
        closure.approved_by = self.user
        closure.approved_at = timezone.now()
        closure.closure_notes = notes or closure.closure_notes
        closure.updated_by = self.user
        closure.save()
        project = closure.project
        if project.status != ProjectStatus.CLOSURE:
            project.status = ProjectStatus.CLOSURE
            project.updated_by = self.user
            project.save(update_fields=["status", "updated_by", "updated_at"])
            ProjectStatusHistory.objects.create(
                project=project,
                from_status=ProjectStatus.COMPLETION,
                to_status=ProjectStatus.CLOSURE,
                changed_by=self.user,
                reason="Project closure approved.",
                created_by=self.user,
                updated_by=self.user,
            )
        _log_event("closure.approved", closure, self.user)
        return closure


class ProjectResultService(BaseService):
    """Record structured outputs, outcomes, and impacts."""

    @transaction.atomic
    def create_result(self, project: Project, **fields) -> ProjectResult:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(_("This project is outside your access scope."))
        instance = ProjectResult(
            project=project,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        instance.full_clean()
        instance.save()
        _log_event("result.created", instance, self.user)
        return instance

    @transaction.atomic
    def update_result(self, result: ProjectResult, **fields) -> ProjectResult:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, result.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        result = ProjectResult.objects.select_for_update().get(pk=result.pk)
        for name, value in fields.items():
            setattr(result, name, value)
        result.updated_by = self.user
        result.full_clean()
        result.save()
        _log_event("result.updated", result, self.user)
        return result


class BeneficiaryParticipationService(BaseService):
    """Record beneficiary participation events."""

    @transaction.atomic
    def create(
        self, beneficiary: BeneficiaryRecord, **fields
    ) -> BeneficiaryParticipation:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, beneficiary.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        instance = BeneficiaryParticipation(
            beneficiary=beneficiary,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        instance.full_clean()
        instance.save()
        _log_event("participation.created", instance, self.user)
        return instance


class ProjectTimelineService(BaseService):
    """Maintain project timeline entries."""

    @transaction.atomic
    def create_entry(self, project: Project, **fields) -> ProjectTimeline:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(_("This project is outside your access scope."))
        instance = ProjectTimeline(
            project=project,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        instance.full_clean()
        instance.save()
        _log_event("timeline.created", instance, self.user)
        return instance

    @transaction.atomic
    def update_entry(self, entry: ProjectTimeline, **fields) -> ProjectTimeline:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, entry.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        entry = ProjectTimeline.objects.select_for_update().get(pk=entry.pk)
        for name, value in fields.items():
            setattr(entry, name, value)
        entry.updated_by = self.user
        entry.full_clean()
        entry.save()
        _log_event("timeline.updated", entry, self.user)
        return entry


class EvidenceService(BaseService):
    """Manage evidence records with immutable versioning."""

    @transaction.atomic
    def upload_version(
        self,
        evidence: EvidenceRecord,
        file,
        notes: str = "",
        original_filename: str = "",
    ) -> EvidenceVersion:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, evidence.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        evidence = EvidenceRecord.objects.select_for_update().get(pk=evidence.pk)
        next_version = (evidence.version_number or 1) + 1
        version = EvidenceVersion(
            evidence=evidence,
            version_number=next_version,
            file=file,
            original_filename=original_filename or getattr(file, "name", ""),
            file_size=getattr(file, "size", None),
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        version.full_clean()
        version.save()
        evidence.version_number = next_version
        evidence.notes = notes or evidence.notes
        evidence.updated_by = self.user
        evidence.save()
        _log_event("evidence.version_created", version, self.user)
        return version


class ProjectReportService(BaseService):
    """Manage project reports through the reporting workflow."""

    @transaction.atomic
    def create(self, project: Project, **fields) -> ProjectReport:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, project):
            raise PermissionDenied(_("This project is outside your access scope."))
        instance = ProjectReport(
            project=project,
            status=ProjectReportStatus.DRAFT,
            created_by=self.user,
            updated_by=self.user,
            **fields,
        )
        instance.full_clean()
        instance.save()
        _log_event("project_report.created", instance, self.user)
        return instance

    @transaction.atomic
    def submit(self, report: ProjectReport, summary: str = "") -> ProjectReport:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, report.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        report = ProjectReport.objects.select_for_update().get(pk=report.pk)
        if report.status != ProjectReportStatus.DRAFT:
            raise ValidationError(_("Only draft reports can be submitted."))
        report.status = ProjectReportStatus.SUBMITTED
        report.summary = summary or report.summary
        report.submitted_by = self.user
        report.submitted_at = timezone.now()
        report.updated_by = self.user
        report.save()
        _log_event("project_report.submitted", report, self.user)
        return report

    @transaction.atomic
    def approve(self, report: ProjectReport) -> ProjectReport:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, report.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        report = ProjectReport.objects.select_for_update().get(pk=report.pk)
        if report.status != ProjectReportStatus.SUBMITTED:
            raise ValidationError(_("Only submitted reports can be approved."))
        if report.submitted_by_id == self.user.pk:
            raise ValidationError(
                _("Reports cannot be approved by their submitter."),
                code="report_self_approval",
            )
        report.status = ProjectReportStatus.APPROVED
        report.approved_by = self.user
        report.approved_at = timezone.now()
        report.updated_by = self.user
        report.save()
        _log_event("project_report.approved", report, self.user)
        return report

    @transaction.atomic
    def archive(self, report: ProjectReport) -> ProjectReport:
        _require_permission(self.user, PROJECTS_UPDATE, PROJECTS_MANAGE)
        if not user_can_access_project(self.user, report.project):
            raise PermissionDenied(_("This project is outside your access scope."))
        report = ProjectReport.objects.select_for_update().get(pk=report.pk)
        if report.status != ProjectReportStatus.APPROVED:
            raise ValidationError(_("Only approved reports can be archived."))
        report.status = ProjectReportStatus.ARCHIVED
        report.updated_by = self.user
        report.save()
        _log_event("project_report.archived", report, self.user)
        return report


class ProjectAnalyticsService(BaseService):
    """Compute dashboard analytics for a single project."""

    def summarize(self, project: Project) -> dict:
        tasks = Task.objects.filter(activity__work_plan__project=project)
        milestones = Milestone.objects.filter(project=project)
        deliverables = Deliverable.objects.filter(project=project)
        risks = Issue.objects.filter(project=project)
        budget_total = project.budget_approved or Decimal("0")
        budget_utilization = (
            _budget_utilization(project, budget_total) if budget_total else Decimal("0")
        )
        return {
            "completion_percentage": project.completion_percentage,
            "tasks_total": tasks.count(),
            "tasks_completed": tasks.filter(status="COMPLETED").count(),
            "milestones_total": milestones.count(),
            "milestones_approved": milestones.filter(
                approval_status=MilestoneApprovalStatus.APPROVED
            ).count(),
            "deliverables_total": deliverables.count(),
            "deliverables_approved": deliverables.filter(status="APPROVED").count(),
            "open_issues": risks.filter(status="OPEN").count(),
            "budget_total": budget_total,
            "budget_utilization": budget_utilization,
            "beneficiaries_reached": BeneficiaryRecord.objects.filter(
                project=project, status=BeneficiaryStatus.COMPLETED
            ).count(),
            "wbs_nodes": WBSNode.objects.filter(project=project).count(),
            "timeline_entries": ProjectTimeline.objects.filter(project=project).count(),
        }

    def project_dashboard_data(self) -> dict:
        visible = _visible_projects(self.user)
        total = visible.count()
        return {
            "total_projects": total,
            "active_projects": visible.filter(status=ProjectStatus.EXECUTION).count(),
            "projects_in_completion": visible.filter(
                status=ProjectStatus.COMPLETION
            ).count(),
            "projects_in_closure": visible.filter(status=ProjectStatus.CLOSURE).count(),
            "avg_completion": _average_completion(visible),
        }


def _budget_utilization(project: Project, total: Decimal) -> Decimal:
    utilized = project.budget_utilized or Decimal("0")
    return Decimal(str(round(float(utilized) / float(total) * 100, 2)))


def _average_completion(queryset) -> Decimal:
    values = [
        float(p.completion_percentage)
        for p in queryset.exclude(completion_percentage=None)
    ]
    if not values:
        return Decimal("0.00")
    return Decimal(str(round(sum(values) / len(values), 2)))


def _visible_projects(user):
    from .selectors import visible_projects

    return visible_projects(user)
