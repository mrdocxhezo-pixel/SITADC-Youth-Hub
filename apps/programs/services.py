"""Permission-checked transactional services for program and project management."""

from __future__ import annotations

import logging
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

from .constants import REFERENCE_SCHEME_CODES, ProgramStatus, ProjectStatus
from .models import (
    Activity,
    BeneficiaryRecord,
    ChangeRequest,
    Deliverable,
    EvidenceRecord,
    Issue,
    LessonsLearned,
    Milestone,
    ProcurementRequest,
    Program,
    ProgramDocument,
    ProgramStatusHistory,
    Project,
    ProjectStatusHistory,
    ResourceAllocation,
    Task,
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
    }
    UPDATE_FIELDS: ClassVar[set[str]] = set(CREATE_FIELDS)

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
        for name, value in fields.items():
            if getattr(project, name) != value:
                setattr(project, name, value)
                changed.append(name)
        project.updated_by = self.user
        project.full_clean()
        project.save()
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
    }
    return mapping.get(model_cls)


def _model_has_field(model_cls, field_name: str) -> bool:
    return field_name in {field.name for field in model_cls._meta.fields}
