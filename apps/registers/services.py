"""Permission-checked transactional services for the Organizational Registers module.

Every write flows through these services so that RBAC checks, workflow
transitions, reference-number allocation, validation, versioning and the
immutable activity timeline are enforced consistently.
"""

from __future__ import annotations

import logging
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.models import ReferenceNumberScheme
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from .constants import (
    REFERENCE_MODULE,
    REGISTER_ORGANIZATION_CODE,
    REGISTER_PATTERN,
    REGISTER_SEQUENCE_LENGTH,
    ConfidentialityLevel,
    RegisterActivityAction,
    RegisterApprovalStatus,
    RegisterEntryStatus,
    RegisterStatus,
)
from .models import (
    Register,
    RegisterActivity,
    RegisterAttachment,
    RegisterCategory,
    RegisterEntry,
    RegisterRelationship,
    RegisterReview,
    RegisterTemplate,
    RegisterValidation,
    RegisterVersion,
)
from .permissions import (
    REGISTER_APPROVE,
    REGISTER_ARCHIVE,
    REGISTER_CREATE,
    REGISTER_MANAGE,
    REGISTER_RESTORE,
    REGISTER_REVIEW,
    REGISTER_SUBMIT,
    REGISTER_UPDATE,
    REGISTER_VIEW_CONFIDENTIAL,
)

logger = logging.getLogger(__name__)

# Allowed approval workflow transitions for register entries.
APPROVAL_TRANSITIONS: dict[str, set[str]] = {
    RegisterApprovalStatus.DRAFT: {
        RegisterApprovalStatus.SUBMITTED,
    },
    RegisterApprovalStatus.SUBMITTED: {
        RegisterApprovalStatus.PENDING_REVIEW,
        RegisterApprovalStatus.RETURNED,
    },
    RegisterApprovalStatus.PENDING_REVIEW: {
        RegisterApprovalStatus.UNDER_REVIEW,
        RegisterApprovalStatus.APPROVED,
        RegisterApprovalStatus.APPROVED_WITH_CONDITIONS,
        RegisterApprovalStatus.RETURNED,
        RegisterApprovalStatus.REJECTED,
    },
    RegisterApprovalStatus.UNDER_REVIEW: {
        RegisterApprovalStatus.APPROVED,
        RegisterApprovalStatus.APPROVED_WITH_CONDITIONS,
        RegisterApprovalStatus.RETURNED,
        RegisterApprovalStatus.REJECTED,
    },
    RegisterApprovalStatus.APPROVED_WITH_CONDITIONS: {
        RegisterApprovalStatus.SUBMITTED,
        RegisterApprovalStatus.APPROVED,
    },
    RegisterApprovalStatus.RETURNED: {
        RegisterApprovalStatus.SUBMITTED,
        RegisterApprovalStatus.DRAFT,
    },
    RegisterApprovalStatus.REJECTED: {
        RegisterApprovalStatus.SUBMITTED,
    },
    RegisterApprovalStatus.APPROVED: set(),
}


class _RegisterServiceMixin:
    """Shared guards and audit helpers for register services."""

    user: Any

    def _require_permission(self, permission_code: str) -> None:
        if not self.user or not getattr(self.user, "is_authenticated", False):
            raise PermissionDenied(_("An authenticated actor is required."))
        if not (
            user_has_permission(self.user, permission_code)
            or user_has_permission(self.user, REGISTER_MANAGE)
        ):
            raise PermissionDenied(_("Permission denied for this registers action."))

    def _require_confidentiality(self, instance) -> None:
        sensitive = isinstance(instance, RegisterEntry | Register) and (
            instance.is_confidential
        )
        if sensitive and not (
            user_has_permission(self.user, REGISTER_VIEW_CONFIDENTIAL)
            or user_has_permission(self.user, REGISTER_MANAGE)
        ):
            raise PermissionDenied(
                _("This register record is confidential and outside your access.")
            )

    def _activity(
        self,
        action: str,
        *,
        register: Register | None = None,
        entry: RegisterEntry | None = None,
        previous_status: str = "",
        new_status: str = "",
        comment: str = "",
    ) -> None:
        RegisterActivity.objects.create(
            register=register,
            entry=entry,
            action=action,
            actor=self.user,
            previous_status=previous_status or "",
            new_status=new_status or "",
            comment=comment,
        )
        logger.info(
            "register_activity",
            extra={
                "register_event": {
                    "action": action,
                    "register_id": str(register.pk) if register else "",
                    "entry_id": str(entry.pk) if entry else "",
                    "actor_id": str(getattr(self.user, "pk", "")),
                    "previous_status": previous_status,
                    "new_status": new_status,
                }
            },
        )

    def _validate_transition(self, instance: RegisterEntry, to_status: str) -> None:
        allowed = APPROVAL_TRANSITIONS.get(instance.approval_status, set())
        if to_status not in allowed:
            raise ValidationError(
                _("Cannot move an entry from %(from)s to %(to)s.")
                % {
                    "from": instance.get_approval_status_display(),
                    "to": _approval_display(to_status),
                }
            )


def _approval_display(to_status: str) -> str:
    """Return the display label for an approval status value."""
    choices = dict(RegisterApprovalStatus.choices)
    return choices.get(to_status, to_status)


class RegisterCategoryService(BaseService, _RegisterServiceMixin):
    """Create and maintain register categories."""

    def _execute(
        self,
        *,
        name: str,
        code: str,
        description: str = "",
        number_prefix: str = "",
        default_confidentiality: str = ConfidentialityLevel.INTERNAL,
        retention_policy: str = "PERMANENT",
        retention_years: int | None = None,
        sort_order: int = 0,
        is_active: bool = True,
        instance: RegisterCategory | None = None,
    ) -> RegisterCategory:
        if instance is None:
            self._require_permission(REGISTER_CREATE)
        else:
            self._require_permission(REGISTER_UPDATE)
        data = {
            "name": name,
            "code": code,
            "description": description,
            "number_prefix": number_prefix,
            "default_confidentiality": default_confidentiality,
            "retention_policy": retention_policy,
            "retention_years": retention_years,
            "sort_order": sort_order,
            "is_active": is_active,
        }
        if instance is None:
            instance = RegisterCategory.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
            self._activity(
                RegisterActivityAction.CREATED,
                comment=f"Register category {instance.name} created.",
            )
        else:
            for field, value in data.items():
                setattr(instance, field, value)
            instance.updated_by = self.user
            instance.full_clean()
            instance.save()
            self._activity(
                RegisterActivityAction.UPDATED,
                comment=f"Register category {instance.name} updated.",
            )
        return instance


class RegisterService(BaseService, _RegisterServiceMixin):
    """Create and maintain organizational registers."""

    def _execute(
        self,
        *,
        name: str,
        code: str,
        category: RegisterCategory,
        owner,
        description: str = "",
        responsible_department: str = "",
        numbering_scheme: ReferenceNumberScheme | None = None,
        confidentiality: str = ConfidentialityLevel.INTERNAL,
        approval_required: bool = True,
        retention_policy: str = "PERMANENT",
        retention_years: int | None = None,
        status: str = RegisterStatus.DRAFT,
        is_active: bool = True,
        instance: Register | None = None,
    ) -> Register:
        if instance is None:
            self._require_permission(REGISTER_CREATE)
        else:
            self._require_permission(REGISTER_UPDATE)

        scheme = numbering_scheme or self._resolve_scheme(category)

        data = {
            "name": name,
            "code": code,
            "category": category,
            "owner": owner,
            "description": description,
            "responsible_department": responsible_department,
            "numbering_scheme": scheme,
            "confidentiality": confidentiality,
            "approval_required": approval_required,
            "retention_policy": retention_policy,
            "retention_years": retention_years,
            "status": status,
            "is_active": is_active,
        }
        if instance is None:
            instance = Register(**data)
            instance.created_by = self.user
            instance.updated_by = self.user
            reference = self._allocate_register_reference(instance)
            if reference is not None:
                instance.reference_number = reference.reference_number
            instance.full_clean()
            instance.save()
            if reference is not None:
                ConfirmReferenceAssignmentService(user=self.user).execute(
                    reference=reference, record_id=instance.pk
                )
            self._activity(
                RegisterActivityAction.CREATED,
                register=instance,
                new_status=status,
                comment=f"Register {instance.name} created.",
            )
        else:
            for field, value in data.items():
                setattr(instance, field, value)
            instance.updated_by = self.user
            instance.full_clean()
            instance.save()
            self._activity(
                RegisterActivityAction.UPDATED,
                register=instance,
                comment=f"Register {instance.name} updated.",
            )
        return instance

    def _resolve_scheme(
        self, category: RegisterCategory
    ) -> ReferenceNumberScheme | None:
        """Resolve or create the numbering scheme for a register category."""
        prefix = category.number_prefix or "REG"
        scheme, _ = ReferenceNumberScheme.objects.get_or_create(
            module=REFERENCE_MODULE,
            record_type=category.code,
            prefix=prefix,
            defaults={
                "name": f"{category.name} Register",
                "code": f"reg_{category.code}",
                "description": f"Phase 23 scheme for the {category.name} register.",
                "pattern": REGISTER_PATTERN,
                "organization_code": REGISTER_ORGANIZATION_CODE,
                "sequence_length": REGISTER_SEQUENCE_LENGTH,
                "start_value": 1,
                "reset_period": "ANNUALLY",
                "is_default_for_module": False,
                "is_default_for_record_type": True,
                "is_fallback": False,
                "status": "ACTIVE",
                "is_active": True,
            },
        )
        return scheme

    def _allocate_register_reference(self, register: Register):
        scheme = register.numbering_scheme
        if scheme is None:
            return None
        return ReferenceNumberService(user=self.user).execute(
            module=REFERENCE_MODULE,
            record_type=register.category.code,
            scheme_code=scheme.code,
            notes=f"Register reference for {register.name}.",
        )

    def archive(self, *, instance: Register) -> Register:
        self._require_permission(REGISTER_ARCHIVE)
        previous = instance.status
        instance.archive(archived_by=self.user)
        self._activity(
            RegisterActivityAction.ARCHIVED,
            register=instance,
            previous_status=previous,
            new_status=RegisterStatus.ARCHIVED,
            comment=f"Register {instance.name} archived.",
        )
        return instance

    def restore(self, *, instance: Register) -> Register:
        self._require_permission(REGISTER_RESTORE)
        previous = instance.status
        instance.restore()
        self._activity(
            RegisterActivityAction.RESTORED,
            register=instance,
            previous_status=previous,
            new_status=RegisterStatus.ACTIVE,
            comment=f"Register {instance.name} restored.",
        )
        return instance


class RegisterTemplateService(BaseService, _RegisterServiceMixin):
    """Create and maintain register templates."""

    def _execute(
        self,
        *,
        name: str,
        code: str,
        register: Register,
        description: str = "",
        fields: list | None = None,
        validation_rules: list | None = None,
        default_confidentiality: str = ConfidentialityLevel.INTERNAL,
        is_default: bool = False,
        is_active: bool = True,
        instance: RegisterTemplate | None = None,
    ) -> RegisterTemplate:
        if instance is None:
            self._require_permission(REGISTER_CREATE)
        else:
            self._require_permission(REGISTER_UPDATE)
        data = {
            "name": name,
            "code": code,
            "register": register,
            "description": description,
            "fields": fields or [],
            "validation_rules": validation_rules or [],
            "default_confidentiality": default_confidentiality,
            "is_default": is_default,
            "is_active": is_active,
        }
        if instance is None:
            instance = RegisterTemplate.objects.create(
                **data, created_by=self.user, updated_by=self.user
            )
        else:
            for field, value in data.items():
                setattr(instance, field, value)
            instance.updated_by = self.user
            instance.full_clean()
            instance.save()
        return instance


class RegisterEntryService(BaseService, _RegisterServiceMixin):
    """Create, update and transition register entries."""

    def _execute(
        self,
        *,
        register: Register,
        title: str,
        description: str = "",
        owner=None,
        directorate=None,
        program=None,
        project=None,
        reporting_period_start=None,
        reporting_period_end=None,
        confidentiality: str | None = None,
        field_data: dict | None = None,
        tags: list | None = None,
        keywords: str = "",
        template: RegisterTemplate | None = None,
        instance: RegisterEntry | None = None,
    ) -> RegisterEntry:
        if instance is None:
            self._require_permission(REGISTER_CREATE)
        else:
            self._require_permission(REGISTER_UPDATE)
            self._require_confidentiality(instance)

        actor = self.user
        owner = owner or actor
        level = confidentiality or register.confidentiality

        data = {
            "register": register,
            "template": template,
            "title": title,
            "description": description,
            "owner": owner,
            "directorate": directorate,
            "program": program,
            "project": project,
            "reporting_period_start": reporting_period_start,
            "reporting_period_end": reporting_period_end,
            "confidentiality": level,
            "field_data": field_data or {},
            "tags": tags or [],
            "keywords": keywords,
        }
        if instance is None:
            instance = RegisterEntry(**data)
            instance.created_by = actor
            instance.updated_by = actor
            reference = self._reserve_entry_reference(instance)
            if reference is not None:
                instance.reference_number = reference.reference_number
            instance.full_clean()
            instance.save()
            if reference is not None:
                ConfirmReferenceAssignmentService(user=actor).execute(
                    reference=reference, record_id=instance.pk
                )
            self._create_version(instance, "Initial version.", create=True)
            self._activity(
                RegisterActivityAction.CREATED,
                register=register,
                entry=instance,
                new_status=instance.approval_status,
                comment=f"Entry {instance.reference_number} created.",
            )
        else:
            for field, value in data.items():
                setattr(instance, field, value)
            instance.updated_by = actor
            instance.full_clean()
            instance.save()
            self._create_version(instance, "Entry updated.")
            self._activity(
                RegisterActivityAction.UPDATED,
                register=register,
                entry=instance,
                new_status=instance.approval_status,
                comment=f"Entry {instance.reference_number} updated.",
            )
        return instance

    def _reserve_entry_reference(self, instance: RegisterEntry):
        scheme = instance.register.numbering_scheme
        if scheme is None:
            return None
        return ReferenceNumberService(user=self.user).execute(
            module=REFERENCE_MODULE,
            record_type=instance.register.category.code,
            scheme_code=scheme.code,
            notes=f"Register entry for {instance.register.name}.",
        )

    def _create_version(
        self, instance: RegisterEntry, change_summary: str, create: bool = False
    ) -> None:
        next_version = 1 if create else instance.versions.count() + 1
        RegisterVersion.objects.create(
            entry=instance,
            version_number=next_version,
            author=self.user,
            change_summary=change_summary,
            data_snapshot={
                "title": instance.title,
                "description": instance.description,
                "confidentiality": instance.confidentiality,
                "field_data": instance.field_data,
                "tags": instance.tags,
                "keywords": instance.keywords,
                "approval_status": instance.approval_status,
                "status": instance.status,
            },
        )

    def submit(self, *, instance: RegisterEntry, comment: str = "") -> RegisterEntry:
        self._require_permission(REGISTER_SUBMIT)
        self._require_confidentiality(instance)
        self._validate_transition(instance, RegisterApprovalStatus.SUBMITTED)
        previous = instance.approval_status
        instance.approval_status = RegisterApprovalStatus.SUBMITTED
        instance.status = RegisterEntryStatus.SUBMITTED
        instance.submitted_at = timezone.now()
        instance.updated_by = self.user
        instance.save(
            update_fields=[
                "approval_status",
                "status",
                "submitted_at",
                "updated_at",
            ]
        )
        self._activity(
            RegisterActivityAction.SUBMITTED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=instance.approval_status,
            comment=comment,
        )
        return instance

    def start_review(
        self, *, instance: RegisterEntry, comment: str = ""
    ) -> RegisterEntry:
        self._require_permission(REGISTER_REVIEW)
        self._require_confidentiality(instance)
        self._validate_transition(instance, RegisterApprovalStatus.PENDING_REVIEW)
        previous = instance.approval_status
        instance.approval_status = RegisterApprovalStatus.PENDING_REVIEW
        instance.status = RegisterEntryStatus.PENDING_REVIEW
        instance.updated_by = self.user
        instance.save(update_fields=["approval_status", "status", "updated_at"])
        self._activity(
            RegisterActivityAction.REVIEWED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=instance.approval_status,
            comment=comment,
        )
        return instance

    def approve(self, *, instance: RegisterEntry, comment: str = "") -> RegisterEntry:
        self._require_permission(REGISTER_APPROVE)
        self._require_confidentiality(instance)
        self._validate_transition(instance, RegisterApprovalStatus.APPROVED)
        previous = instance.approval_status
        instance.approval_status = RegisterApprovalStatus.APPROVED
        instance.status = RegisterEntryStatus.ACTIVE
        instance.approved_at = timezone.now()
        instance.approved_by = self.user
        instance.updated_by = self.user
        instance.save(
            update_fields=[
                "approval_status",
                "status",
                "approved_at",
                "approved_by",
                "updated_at",
            ]
        )
        RegisterReview.objects.create(
            entry=instance,
            reviewer=self.user,
            decision=RegisterApprovalStatus.APPROVED,
            comments=comment,
        )
        self._activity(
            RegisterActivityAction.APPROVED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=instance.approval_status,
            comment=comment,
        )
        return instance

    def return_entry(
        self, *, instance: RegisterEntry, comment: str = ""
    ) -> RegisterEntry:
        self._require_permission(REGISTER_REVIEW)
        self._require_confidentiality(instance)
        self._validate_transition(instance, RegisterApprovalStatus.RETURNED)
        previous = instance.approval_status
        instance.approval_status = RegisterApprovalStatus.RETURNED
        instance.status = RegisterEntryStatus.RETURNED
        instance.updated_by = self.user
        instance.save(update_fields=["approval_status", "status", "updated_at"])
        RegisterReview.objects.create(
            entry=instance,
            reviewer=self.user,
            decision=RegisterApprovalStatus.RETURNED,
            comments=comment,
        )
        self._activity(
            RegisterActivityAction.RETURNED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=instance.approval_status,
            comment=comment,
        )
        return instance

    def reject(self, *, instance: RegisterEntry, comment: str = "") -> RegisterEntry:
        self._require_permission(REGISTER_APPROVE)
        self._require_confidentiality(instance)
        self._validate_transition(instance, RegisterApprovalStatus.REJECTED)
        previous = instance.approval_status
        instance.approval_status = RegisterApprovalStatus.REJECTED
        instance.status = RegisterEntryStatus.REJECTED
        instance.updated_by = self.user
        instance.save(update_fields=["approval_status", "status", "updated_at"])
        RegisterReview.objects.create(
            entry=instance,
            reviewer=self.user,
            decision=RegisterApprovalStatus.REJECTED,
            comments=comment,
        )
        self._activity(
            RegisterActivityAction.REJECTED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=instance.approval_status,
            comment=comment,
        )
        return instance

    def archive(self, *, instance: RegisterEntry) -> RegisterEntry:
        self._require_permission(REGISTER_ARCHIVE)
        self._require_confidentiality(instance)
        previous = instance.status
        instance.archive(archived_by=self.user)
        instance.status = RegisterEntryStatus.ARCHIVED
        instance.save(update_fields=["status", "updated_at"])
        self._activity(
            RegisterActivityAction.ARCHIVED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=RegisterEntryStatus.ARCHIVED,
            comment=f"Entry {instance.reference_number} archived.",
        )
        return instance

    def restore(self, *, instance: RegisterEntry) -> RegisterEntry:
        self._require_permission(REGISTER_RESTORE)
        previous = instance.status
        instance.unarchive()
        instance.status = RegisterEntryStatus.ACTIVE
        instance.save(update_fields=["status", "updated_at"])
        self._activity(
            RegisterActivityAction.RESTORED,
            register=instance.register,
            entry=instance,
            previous_status=previous,
            new_status=RegisterEntryStatus.ACTIVE,
            comment=f"Entry {instance.reference_number} restored.",
        )
        return instance


class RegisterValidationService(BaseService, _RegisterServiceMixin):
    """Validate a register entry against its template's rules."""

    def _execute(self, *, instance: RegisterEntry) -> list[RegisterValidation]:
        self._require_permission(REGISTER_UPDATE)
        self._require_confidentiality(instance)
        RegisterValidation.objects.filter(entry=instance).delete()
        results: list[RegisterValidation] = []
        template = instance.template
        if template is None:
            return results
        for rule in template.validation_rules or []:
            passed = self._run_rule(instance, rule)
            record = RegisterValidation.objects.create(
                entry=instance,
                rule_code=rule.get("code", "unknown"),
                passed=passed,
                message=rule.get("message", ""),
                checked_by=self.user,
            )
            results.append(record)
        self._activity(
            RegisterActivityAction.VALIDATED,
            register=instance.register,
            entry=instance,
            comment="Entry validation run completed.",
        )
        return results

    def _run_rule(self, instance: RegisterEntry, rule: dict) -> bool:
        field = rule.get("field")
        kind = rule.get("rule")
        value = instance.field_data.get(field) if field else None
        if kind == "required":
            return bool(value not in (None, "", []))
        if kind == "min_length":
            return value is None or len(str(value)) >= int(rule.get("value", 0))
        if kind == "max_length":
            return value is None or len(str(value)) <= int(rule.get("value", 0))
        if kind == "min_value":
            try:
                return value is None or float(value) >= float(rule.get("value", 0))
            except (TypeError, ValueError):
                return False
        if kind == "max_value":
            try:
                return value is None or float(value) <= float(rule.get("value", 0))
            except (TypeError, ValueError):
                return False
        return True


class RegisterRelationshipService(BaseService, _RegisterServiceMixin):
    """Manage relationships between register entries and related records."""

    def add(
        self,
        *,
        instance: RegisterEntry,
        relationship_type: str,
        content_type,
        object_id,
        notes: str = "",
        related_entry: RegisterEntry | None = None,
    ) -> RegisterRelationship:
        self._require_permission(REGISTER_UPDATE)
        self._require_confidentiality(instance)
        relationship = RegisterRelationship.objects.create(
            entry=instance,
            relationship_type=relationship_type,
            content_type=content_type,
            object_id=object_id,
            related_entry=related_entry,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        self._activity(
            RegisterActivityAction.RELATIONSHIP_ADDED,
            register=instance.register,
            entry=instance,
            comment=f"{relationship.get_relationship_type_display()} linked.",
        )
        return relationship

    def remove(self, *, relationship: RegisterRelationship) -> None:
        self._require_permission(REGISTER_UPDATE)
        entry = relationship.entry
        self._require_confidentiality(entry)
        relationship.delete()
        self._activity(
            RegisterActivityAction.RELATIONSHIP_REMOVED,
            register=entry.register,
            entry=entry,
            comment="Related record unlinked.",
        )


class RegisterAttachmentService(BaseService, _RegisterServiceMixin):
    """Manage supporting attachments on register entries."""

    def add(
        self,
        *,
        instance: RegisterEntry,
        file,
        original_filename: str,
        content_type: str = "",
        description: str = "",
    ) -> RegisterAttachment:
        self._require_permission(REGISTER_UPDATE)
        self._require_confidentiality(instance)
        attachment = RegisterAttachment.objects.create(
            entry=instance,
            file=file,
            original_filename=original_filename,
            content_type=content_type,
            size=file.size,
            description=description,
            created_by=self.user,
            updated_by=self.user,
        )
        self._activity(
            RegisterActivityAction.ATTACHMENT_ADDED,
            register=instance.register,
            entry=instance,
            comment=f"Attachment {original_filename} added.",
        )
        return attachment

    def remove(self, *, attachment: RegisterAttachment) -> None:
        self._require_permission(REGISTER_UPDATE)
        entry = attachment.entry
        self._require_confidentiality(entry)
        name = attachment.original_filename
        attachment.delete()
        self._activity(
            RegisterActivityAction.ATTACHMENT_REMOVED,
            register=entry.register,
            entry=entry,
            comment=f"Attachment {name} removed.",
        )
