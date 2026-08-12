"""Transactional service layer for the Phase 19 Dynamic Report Builder.

Every write path is permission-checked server-side, runs inside a database
transaction (via :class:`apps.core.services.BaseService`), allocates centralized
reference numbers, records immutable status history and appends to the report
builder audit trail.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import (
    ConfirmReferenceAssignmentService,
    ReferenceNumberService,
)

from . import validators
from .constants import (
    ConditionOperator,
    ConditionTargetType,
    ConfidentialityLevel,
    ReportingFrequency,
    ReportTemplateAuditAction,
    ReportTemplateStatus,
    TemplateVersionStatus,
)
from .exceptions import (
    CircularConditionalDependencyError,
    CircularFormulaDependencyError,
    InvalidFormulaError,
    InvalidTemplateSchemaError,
    TemplateImportError,
    TemplatePublishError,
    TemplateStatusTransitionError,
    TemplateVersionError,
)
from .formulas import evaluate_formula, extract_field_references, validate_formula
from .models import (
    ConditionalLogicRule,
    DynamicField,
    FieldGroup,
    FieldOption,
    ReportCategory,
    ReportTemplate,
    ReportTemplateAuditRecord,
    ReportTemplateSettings,
    ReportTemplateStatusHistory,
    ReportTemplateVersion,
    TableColumnDefinition,
    TemplateComponent,
    TemplateReferenceRule,
    TemplateSection,
    ValidationRule,
)
from .permissions import (
    REPORT_TEMPLATE_ARCHIVE,
    REPORT_TEMPLATE_CLONE,
    REPORT_TEMPLATE_CONFIGURE,
    REPORT_TEMPLATE_CREATE,
    REPORT_TEMPLATE_DELETE,
    REPORT_TEMPLATE_EXPORT,
    REPORT_TEMPLATE_IMPORT,
    REPORT_TEMPLATE_MANAGE,
    REPORT_TEMPLATE_PUBLISH,
    REPORT_TEMPLATE_RESTORE,
    REPORT_TEMPLATE_UPDATE,
)

REFERENCE_SCHEME_KEY = "report_template"


# ---------------------------------------------------------------------------
# Audit helpers
# ---------------------------------------------------------------------------


def record_report_template_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> ReportTemplateAuditRecord:
    """Append an immutable report builder audit record."""
    return ReportTemplateAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, *codes: str) -> None:
    if user is None or not user.is_authenticated:
        raise PermissionDenied
    if user_has_permission(user, REPORT_TEMPLATE_MANAGE):
        return
    if any(user_has_permission(user, code) for code in codes):
        return
    raise PermissionDenied


def schema_checksum(schema: dict) -> str:
    """Return a stable SHA-256 checksum for a schema snapshot."""
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ReportBuilderService(BaseService):
    """Shared behaviour for report builder services."""

    def __init__(self, user=None):
        super().__init__(user=user)
        self.actor = user

    def _require(self, *codes: str) -> None:
        _require_permission(self.actor, *codes)

    def _log(
        self,
        action: str,
        entity_type: str,
        entity_id,
        *,
        from_data: dict | None = None,
        to_data: dict | None = None,
        notes: str = "",
    ) -> ReportTemplateAuditRecord:
        return record_report_template_audit(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changed_by=self.actor,
            from_data=from_data,
            to_data=to_data,
            notes=notes,
        )

    def _history(
        self,
        template: ReportTemplate,
        from_status: str,
        to_status: str,
        action: str,
        notes: str = "",
    ) -> ReportTemplateStatusHistory:
        return ReportTemplateStatusHistory.objects.create(
            template=template,
            from_status=from_status or "",
            to_status=to_status,
            action=action,
            notes=notes,
            created_by=self.actor,
        )


# ---------------------------------------------------------------------------
# Reference numbering
# ---------------------------------------------------------------------------


def _reserve_reference(actor) -> Any:
    return ReferenceNumberService(user=actor).execute(
        module=ReferenceModules.REPORTS,
        record_type=REFERENCE_SCHEME_KEY,
        scheme_code=REFERENCE_SCHEME_KEY,
        notes="Phase 19 report template reference reservation.",
    )


def _confirm_reference(actor, reference, template: ReportTemplate) -> None:
    ConfirmReferenceAssignmentService(user=actor).execute(
        reference=reference,
        record_id=template.pk,
        notes="Assigned to report template.",
    )


def _allocate_reference(actor, template: ReportTemplate) -> None:
    reference = _reserve_reference(actor)
    template.reference_number = reference.reference_number
    template.save(update_fields=["reference_number", "updated_at"])
    _confirm_reference(actor, reference, template)


# ---------------------------------------------------------------------------
# ReportTemplateService
# ---------------------------------------------------------------------------


class ReportTemplateService(ReportBuilderService):
    """Create, update, delete, restore and transition report templates."""

    def create(
        self,
        *,
        code: str,
        title: str,
        category: ReportCategory,
        reporting_frequency: str = ReportingFrequency.ONE_OFF,
        description: str = "",
        department: str = "",
        owner=None,
        confidentiality: str = ConfidentialityLevel.INTERNAL,
        effective_from=None,
        expires_on=None,
        retention_period_days: int = 365,
        notes: str = "",
    ) -> ReportTemplate:
        self._require(REPORT_TEMPLATE_CREATE)
        template = ReportTemplate.objects.create(
            code=code,
            title=title,
            category=category,
            reporting_frequency=reporting_frequency,
            description=description,
            department=department,
            owner=owner or self.actor,
            confidentiality=confidentiality,
            effective_from=effective_from,
            expires_on=expires_on,
            retention_period_days=retention_period_days,
            notes=notes,
            created_by=self.actor,
            updated_by=self.actor,
        )
        _allocate_reference(self.actor, template)
        ReportTemplateVersion.objects.create(
            template=template,
            version_number="1.0",
            major=1,
            minor=0,
            change_summary="Initial template version.",
            schema_snapshot={},
            created_by=self.actor,
        )
        self._history(template, "", ReportTemplateStatus.DRAFT, "CREATE", notes)
        self._log(
            ReportTemplateAuditAction.CREATED,
            "ReportTemplate",
            template.pk,
            to_data={
                "reference_number": template.reference_number,
                "code": template.code,
                "title": template.title,
            },
            notes=notes,
        )
        return template

    def update(
        self,
        template: ReportTemplate,
        *,
        title: str | None = None,
        category=None,
        reporting_frequency: str | None = None,
        description: str | None = None,
        department: str | None = None,
        owner=None,
        confidentiality: str | None = None,
        effective_from=None,
        expires_on=None,
        retention_period_days: int | None = None,
        notes: str | None = None,
    ) -> ReportTemplate:
        self._require(REPORT_TEMPLATE_UPDATE)
        if not template.is_editable:
            raise TemplateStatusTransitionError(
                "Template metadata can only be edited while the template is a draft."
            )
        from_data = {"status": template.status}
        if title is not None:
            template.title = title
        if category is not None:
            template.category = category
        if reporting_frequency is not None:
            template.reporting_frequency = reporting_frequency
        if description is not None:
            template.description = description
        if department is not None:
            template.department = department
        if owner is not None:
            template.owner = owner
        if confidentiality is not None:
            template.confidentiality = confidentiality
        if effective_from is not None:
            template.effective_from = effective_from
        if expires_on is not None:
            template.expires_on = expires_on
        if retention_period_days is not None:
            template.retention_period_days = retention_period_days
        if notes is not None:
            template.notes = notes
        template.updated_by = self.actor
        template.save()
        self._log(
            ReportTemplateAuditAction.UPDATED,
            "ReportTemplate",
            template.pk,
            from_data=from_data,
            to_data={"title": template.title, "status": template.status},
        )
        return template

    def soft_delete(self, template: ReportTemplate, notes: str = "") -> None:
        self._require(REPORT_TEMPLATE_DELETE)
        if not template.is_editable:
            raise TemplateStatusTransitionError("Only draft templates can be deleted.")
        from_status = template.status
        template.delete(deleted_by=self.actor)
        self._history(
            template, from_status, ReportTemplateStatus.ARCHIVED, "DELETE", notes
        )
        self._log(
            ReportTemplateAuditAction.DELETED,
            "ReportTemplate",
            template.pk,
            from_data={"status": from_status},
            notes=notes,
        )

    def restore(self, template: ReportTemplate, notes: str = "") -> ReportTemplate:
        self._require(REPORT_TEMPLATE_RESTORE)
        template.restore()
        template.status = ReportTemplateStatus.DRAFT
        template.updated_by = self.actor
        template.save(update_fields=["status", "updated_at"])
        self._history(
            template,
            ReportTemplateStatus.ARCHIVED,
            ReportTemplateStatus.DRAFT,
            "RESTORE",
            notes,
        )
        self._log(
            ReportTemplateAuditAction.RESTORED,
            "ReportTemplate",
            template.pk,
            to_data={"status": ReportTemplateStatus.DRAFT},
            notes=notes,
        )
        return template

    def archive(self, template: ReportTemplate, notes: str = "") -> ReportTemplate:
        self._require(REPORT_TEMPLATE_ARCHIVE)
        if template.status not in (
            ReportTemplateStatus.DRAFT,
            ReportTemplateStatus.PUBLISHED,
        ):
            raise TemplateStatusTransitionError(
                "Only draft or published templates can be archived."
            )
        from_status = template.status
        template.archive(archived_by=self.actor)
        template.status = ReportTemplateStatus.ARCHIVED
        template.updated_by = self.actor
        template.save(update_fields=["status", "updated_at"])
        template.versions.update(status=TemplateVersionStatus.ARCHIVED)
        self._history(
            template, from_status, ReportTemplateStatus.ARCHIVED, "ARCHIVE", notes
        )
        self._log(
            ReportTemplateAuditAction.ARCHIVED,
            "ReportTemplate",
            template.pk,
            from_data={"status": from_status},
            to_data={"status": ReportTemplateStatus.ARCHIVED},
            notes=notes,
        )
        return template

    def retire(self, template: ReportTemplate, notes: str = "") -> ReportTemplate:
        """Mark a superseded published template as retired."""
        self._require(REPORT_TEMPLATE_ARCHIVE)
        if template.status != ReportTemplateStatus.PUBLISHED:
            raise TemplateStatusTransitionError(
                "Only published templates can be retired."
            )
        from_status = template.status
        template.status = ReportTemplateStatus.RETIRED
        template.updated_by = self.actor
        template.save(update_fields=["status", "updated_at"])
        self._history(
            template, from_status, ReportTemplateStatus.RETIRED, "RETIRE", notes
        )
        self._log(
            ReportTemplateAuditAction.ARCHIVED,
            "ReportTemplate",
            template.pk,
            from_data={"status": from_status},
            to_data={"status": ReportTemplateStatus.RETIRED},
            notes=notes,
        )
        return template


# ---------------------------------------------------------------------------
# TemplateVersionService
# ---------------------------------------------------------------------------


class TemplateVersionService(ReportBuilderService):
    """Version management: create, restore, compare and snapshot versions."""

    def create_version(
        self,
        template: ReportTemplate,
        *,
        change_summary: str = "",
        bump: str = "minor",
    ) -> ReportTemplateVersion:
        self._require(REPORT_TEMPLATE_UPDATE)
        if template.status == ReportTemplateStatus.ARCHIVED:
            raise TemplateVersionError("Archived templates cannot create versions.")
        latest = template.versions.order_by("-major", "-minor").first()
        if latest is None:
            major, minor, version_number = 1, 0, "1.0"
        elif bump == "major":
            major = latest.major + 1
            minor = 0
            version_number = f"{major}.0"
        else:
            major = latest.major
            minor = latest.minor + 1
            version_number = f"{major}.{minor}"
        version = ReportTemplateVersion.objects.create(
            template=template,
            version_number=version_number,
            major=major,
            minor=minor,
            change_summary=change_summary,
            schema_snapshot=latest.schema_snapshot if latest else {},
            created_by=self.actor,
        )
        version.checksum = schema_checksum(version.schema_snapshot)
        version.save(update_fields=["checksum"])
        self._log(
            ReportTemplateAuditAction.VERSION_CREATED,
            "ReportTemplate",
            template.pk,
            to_data={"version_number": version_number, "bump": bump},
            notes=change_summary,
        )
        return version

    def restore_version(
        self,
        template: ReportTemplate,
        version: ReportTemplateVersion,
        *,
        change_summary: str = "",
    ) -> ReportTemplateVersion:
        self._require(REPORT_TEMPLATE_UPDATE)
        if template.status == ReportTemplateStatus.ARCHIVED:
            raise TemplateVersionError("Archived templates cannot be restored.")
        if version.template_id != template.pk:
            raise TemplateVersionError("Version does not belong to the template.")
        restored = ReportTemplateVersion.objects.create(
            template=template,
            version_number=self._next_minor_number(template),
            major=template.versions.aggregate(max_major=Max("major"))["max_major"] or 1,
            minor=(
                template.versions.aggregate(max_minor=Max("minor"))["max_minor"] or 0
            )
            + 1,
            change_summary=change_summary or f"Restored from {version.version_number}.",
            schema_snapshot=version.schema_snapshot,
            created_by=self.actor,
        )
        restored.checksum = schema_checksum(restored.schema_snapshot)
        restored.save(update_fields=["checksum"])
        self._log(
            ReportTemplateAuditAction.VERSION_RESTORED,
            "ReportTemplate",
            template.pk,
            from_data={"version_number": version.version_number},
            to_data={"version_number": restored.version_number},
            notes=change_summary,
        )
        return restored

    @staticmethod
    def _next_minor_number(template: ReportTemplate) -> str:
        latest = template.versions.order_by("-major", "-minor").first()
        if latest is None:
            return "1.0"
        return f"{latest.major}.{latest.minor + 1}"

    def working_version(self, template: ReportTemplate) -> ReportTemplateVersion | None:
        """The draft version that the designer edits, if one exists."""
        return template.versions.filter(status=TemplateVersionStatus.DRAFT).first()


# ---------------------------------------------------------------------------
# TemplateSchemaService
# ---------------------------------------------------------------------------


class TemplateSchemaService(ReportBuilderService):
    """Build, validate, serialize and persist template schemas."""

    def build_schema(self, template: ReportTemplate) -> dict:
        """Assemble the current schema tree from the database."""
        sections = []
        for section in template.sections.select_related("parent").order_by(
            "sort_order", "name"
        ):
            groups = []
            for group in section.groups.order_by("sort_order", "name"):
                fields = []
                for field in group.fields.order_by("sort_order", "label"):
                    fields.append(self._field_to_dict(field))
                groups.append(
                    {
                        "code": group.code,
                        "name": group.name,
                        "description": group.description,
                        "sort_order": group.sort_order,
                        "fields": fields,
                    }
                )
            sections.append(
                {
                    "code": section.code,
                    "name": section.name,
                    "description": section.description,
                    "instructions": section.instructions,
                    "sort_order": section.sort_order,
                    "parent": section.parent.code if section.parent_id else None,
                    "is_repeatable": section.is_repeatable,
                    "is_collapsible": section.is_collapsible,
                    "is_locked": section.is_locked,
                    "visibility_mode": section.visibility_mode,
                    "condition": section.condition,
                    "required_roles": section.required_roles,
                    "required_departments": section.required_departments,
                    "groups": groups,
                }
            )
        conditional_rules = []
        for rule in template.conditional_rules.select_related(
            "source_field", "target_field", "target_section"
        ).filter(is_active=True):
            conditional_rules.append(
                {
                    "target_type": rule.target_type,
                    "target": (
                        rule.target_field.code
                        if rule.target_type == ConditionTargetType.FIELD
                        and rule.target_field
                        else rule.target_section.code if rule.target_section else None
                    ),
                    "condition_type": rule.condition_type,
                    "source_field": (
                        rule.source_field.code if rule.source_field else None
                    ),
                    "operator": rule.operator,
                    "value": rule.value,
                    "logic": rule.logic,
                    "priority": rule.priority,
                }
            )
        components = []
        for component in template.components.order_by("sort_order", "name"):
            components.append(
                {
                    "component_type": component.component_type,
                    "code": component.code,
                    "name": component.name,
                    "configuration": component.configuration,
                    "is_shared": component.is_shared,
                    "sort_order": component.sort_order,
                }
            )
        return {
            "template": {
                "code": template.code,
                "title": template.title,
                "reference_number": template.reference_number,
            },
            "sections": sections,
            "conditional_rules": conditional_rules,
            "components": components,
        }

    def _field_to_dict(self, field: DynamicField) -> dict:
        reference_rule = None
        rule = getattr(field, "reference_rule", None)
        if rule is not None:
            reference_rule = {
                "source_module": rule.source_module,
                "model_name": rule.model_name,
                "display_field": rule.display_field,
                "value_field": rule.value_field,
                "filters": rule.filters,
                "is_multiple": rule.is_multiple,
                "allowed_roles": rule.allowed_roles,
            }
        return {
            "code": field.code,
            "label": field.label,
            "field_type": field.field_type,
            "data_type": field.data_type,
            "required": field.required,
            "read_only": field.read_only,
            "hidden": field.hidden,
            "is_repeatable": field.is_repeatable,
            "is_calculated": field.is_calculated,
            "formula": field.formula,
            "default_value": field.default_value,
            "placeholder": field.placeholder,
            "help_text": field.help_text,
            "tooltip": field.tooltip,
            "sort_order": field.sort_order,
            "options": [
                {
                    "value": option.value,
                    "label": option.label,
                    "sort_order": option.sort_order,
                }
                for option in field.options.order_by("sort_order", "value")
            ],
            "validation_rules": [
                {
                    "rule_type": rule.rule_type,
                    "operator": rule.operator,
                    "params": rule.params,
                    "message": rule.message,
                    "is_active": rule.is_active,
                    "sort_order": rule.sort_order,
                }
                for rule in field.validation_rules.order_by("sort_order")
            ],
            "reference_rule": reference_rule,
            "table_columns": [
                {
                    "column_code": column.column_code,
                    "column_name": column.column_name,
                    "data_type": column.data_type,
                    "width": column.width,
                    "required": column.required,
                    "sort_order": column.sort_order,
                }
                for column in field.table_columns.order_by("sort_order")
            ],
        }

    def validate_schema(
        self, template: ReportTemplate, schema: dict | None = None
    ) -> list[str]:
        """Return a list of validation errors; empty means the schema is valid."""
        schema = schema if schema is not None else self.build_schema(template)
        errors: list[str] = []
        try:
            validators.validate_schema_structure(schema)
        except ValidationError as exc:
            errors.append(str(exc))
            return errors
        field_codes = self._collect_field_codes(schema)
        for section in schema.get("sections", []):
            for group in section.get("groups", []):
                for field in group.get("fields", []):
                    if field.get("is_calculated"):
                        formula = field.get("formula", "")
                        try:
                            validate_formula(formula)
                        except InvalidFormulaError as exc:
                            errors.append(f"Field '{field.get('code')}': {exc}")
                        for ref in extract_field_references(formula):
                            if ref not in field_codes and ref != field["code"]:
                                errors.append(
                                    f"Field '{field.get('code')}' references unknown "
                                    f"field '{ref}'."
                                )
        for rule in schema.get("conditional_rules", []):
            source = rule.get("source_field")
            target = rule.get("target")
            if source and source not in field_codes:
                errors.append(
                    f"Conditional rule source field '{source}' does not exist."
                )
            if (
                target
                and target not in field_codes
                and rule.get("target_type") == "FIELD"
            ):
                errors.append(
                    f"Conditional rule target field '{target}' does not exist."
                )
            if rule.get("target_type") == "SECTION":
                section_codes = {s["code"] for s in schema.get("sections", [])}
                if target and target not in section_codes:
                    errors.append(
                        f"Conditional rule target section '{target}' does not exist."
                    )
        return errors

    @staticmethod
    def _collect_field_codes(schema: dict) -> set[str]:
        codes: set[str] = set()
        for section in schema.get("sections", []):
            for group in section.get("groups", []):
                for field in group.get("fields", []):
                    codes.add(field.get("code"))
        return codes

    def validate_formula_graph(
        self, template: ReportTemplate, schema: dict | None = None
    ) -> None:
        """Detect circular references between calculated fields."""
        schema = schema if schema is not None else self.build_schema(template)
        graph: dict[str, set[str]] = {}
        for section in schema.get("sections", []):
            for group in section.get("groups", []):
                for field in group.get("fields", []):
                    if field.get("is_calculated"):
                        code = field["code"]
                        refs = {
                            ref
                            for ref in extract_field_references(
                                field.get("formula", "")
                            )
                            if ref != code
                        }
                        graph[code] = refs
        self._assert_acyclic(graph, CircularFormulaDependencyError, "Formula")

    def validate_condition_graph(
        self, template: ReportTemplate, schema: dict | None = None
    ) -> None:
        """Detect circular dependencies in conditional logic rules."""
        schema = schema if schema is not None else self.build_schema(template)
        graph: dict[str, set[str]] = {}
        for rule in schema.get("conditional_rules", []):
            source = rule.get("source_field")
            target = rule.get("target")
            if source and target:
                graph.setdefault(source, set()).add(target)
            for leaf in self._logic_leaves(rule.get("logic", {})):
                if leaf.get("field") and target:
                    graph.setdefault(leaf["field"], set()).add(target)
        self._assert_acyclic(
            graph, CircularConditionalDependencyError, "Conditional logic"
        )

    @staticmethod
    def _logic_leaves(logic: dict) -> list[dict]:
        leaves: list[dict] = []
        for key in ("all", "any"):
            for clause in logic.get(key, []):
                if isinstance(clause, dict) and ("all" in clause or "any" in clause):
                    leaves.extend(TemplateSchemaService._logic_leaves(clause))
                elif isinstance(clause, dict):
                    leaves.append(clause)
        return leaves

    @staticmethod
    def _assert_acyclic(graph: dict[str, set[str]], error_class, label: str) -> None:
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str, path: tuple[str, ...]) -> None:
            if node in visiting:
                cycle = " -> ".join((*path, node))
                raise error_class(f"{label} cycle detected: {cycle}")
            if node in visited:
                return
            visiting.add(node)
            for child in graph.get(node, ()):
                visit(child, (*path, node))
            visiting.discard(node)
            visited.add(node)

        for node in graph:
            visit(node, (node,))

    def save_schema(
        self,
        template: ReportTemplate,
        schema: dict,
        *,
        version: ReportTemplateVersion | None = None,
    ) -> ReportTemplateVersion:
        """Replace the template's schema tree and refresh the working version."""
        self._require(REPORT_TEMPLATE_UPDATE)
        if not template.is_editable:
            raise TemplateVersionError(
                "Schema changes require a draft template. "
                "Create a new draft version first."
            )
        errors = self.validate_schema(template, schema)
        if errors:
            self._log(
                ReportTemplateAuditAction.VALIDATION_FAILED,
                "ReportTemplate",
                template.pk,
                notes="; ".join(errors),
            )
            raise InvalidTemplateSchemaError("; ".join(errors))
        self.validate_formula_graph(template, schema)
        self.validate_condition_graph(template, schema)
        working = version or TemplateVersionService(user=self.actor).working_version(
            template
        )
        if working is None:
            raise TemplateVersionError(
                "No draft version exists for schema changes. Create a version first."
            )
        with transaction.atomic():
            self._replace_schema(template, schema)
            working.schema_snapshot = schema
            working.checksum = schema_checksum(schema)
            working.save(update_fields=["schema_snapshot", "checksum"])
        self._log(
            ReportTemplateAuditAction.SCHEMA_UPDATED,
            "ReportTemplate",
            template.pk,
            to_data={
                "version_number": working.version_number,
                "checksum": working.checksum,
            },
        )
        return working

    def _replace_schema(self, template: ReportTemplate, schema: dict) -> None:
        template.sections.all().delete()
        template.conditional_rules.all().delete()
        template.components.all().delete()
        sections_by_code: dict[str, TemplateSection] = {}
        for index, section_data in enumerate(schema.get("sections", [])):
            section = TemplateSection.objects.create(
                template=template,
                name=section_data.get("name", section_data["code"]),
                code=section_data["code"],
                description=section_data.get("description", ""),
                instructions=section_data.get("instructions", ""),
                sort_order=section_data.get("sort_order", index),
                is_repeatable=section_data.get("is_repeatable", False),
                is_collapsible=section_data.get("is_collapsible", True),
                is_locked=section_data.get("is_locked", False),
                visibility_mode=section_data.get("visibility_mode", "ALWAYS"),
                condition=section_data.get("condition", {}),
                required_roles=section_data.get("required_roles", []),
                required_departments=section_data.get("required_departments", []),
                created_by=self.actor,
            )
            sections_by_code[section.code] = section
        for section_data in schema.get("sections", []):
            parent_code = section_data.get("parent")
            if parent_code and parent_code in sections_by_code:
                section = sections_by_code[section_data["code"]]
                section.parent = sections_by_code[parent_code]
                section.save(update_fields=["parent"])
            for group_index, group_data in enumerate(section_data.get("groups", [])):
                group = FieldGroup.objects.create(
                    section=sections_by_code[section_data["code"]],
                    name=group_data.get("name", group_data["code"]),
                    code=group_data["code"],
                    description=group_data.get("description", ""),
                    sort_order=group_data.get("sort_order", group_index),
                    created_by=self.actor,
                )
                for field_index, field_data in enumerate(group_data.get("fields", [])):
                    self._create_field(group, field_data, field_index)
        for rule_data in schema.get("conditional_rules", []):
            self._create_conditional_rule(template, rule_data, sections_by_code)
        for component_index, component_data in enumerate(schema.get("components", [])):
            TemplateComponent.objects.create(
                template=template,
                component_type=component_data.get("component_type", "HEADER"),
                code=component_data.get("code", ""),
                name=component_data.get("name", "Component"),
                configuration=component_data.get("configuration", {}),
                is_shared=component_data.get("is_shared", False),
                sort_order=component_data.get("sort_order", component_index),
                created_by=self.actor,
            )

    def _create_field(
        self, group: FieldGroup, field_data: dict, index: int
    ) -> DynamicField:
        field = DynamicField.objects.create(
            group=group,
            label=field_data.get("label", field_data["code"]),
            code=field_data["code"],
            field_type=field_data.get("field_type", "TEXT"),
            data_type=field_data.get("data_type", "STRING"),
            required=field_data.get("required", False),
            read_only=field_data.get("read_only", False),
            hidden=field_data.get("hidden", False),
            is_repeatable=field_data.get("is_repeatable", False),
            is_calculated=field_data.get("is_calculated", False),
            formula=field_data.get("formula", ""),
            default_value=field_data.get("default_value"),
            placeholder=field_data.get("placeholder", ""),
            help_text=field_data.get("help_text", ""),
            tooltip=field_data.get("tooltip", ""),
            sort_order=field_data.get("sort_order", index),
            created_by=self.actor,
        )
        for option_index, option_data in enumerate(field_data.get("options", [])):
            FieldOption.objects.create(
                field=field,
                value=option_data["value"],
                label=option_data.get("label", option_data["value"]),
                sort_order=option_data.get("sort_order", option_index),
                created_by=self.actor,
            )
        for rule_index, rule_data in enumerate(field_data.get("validation_rules", [])):
            ValidationRule.objects.create(
                field=field,
                rule_type=rule_data.get("rule_type", "REQUIRED"),
                operator=rule_data.get("operator", ""),
                params=rule_data.get("params", {}),
                message=rule_data.get("message", ""),
                is_active=rule_data.get("is_active", True),
                sort_order=rule_data.get("sort_order", rule_index),
                created_by=self.actor,
            )
        reference_rule = field_data.get("reference_rule")
        if reference_rule:
            TemplateReferenceRule.objects.create(
                field=field,
                source_module=reference_rule.get("source_module", ""),
                model_name=reference_rule.get("model_name", ""),
                display_field=reference_rule.get("display_field", ""),
                value_field=reference_rule.get("value_field", ""),
                filters=reference_rule.get("filters", {}),
                is_multiple=reference_rule.get("is_multiple", False),
                allowed_roles=reference_rule.get("allowed_roles", []),
                created_by=self.actor,
            )
        for column_index, column_data in enumerate(field_data.get("table_columns", [])):
            TableColumnDefinition.objects.create(
                table_field=field,
                column_code=column_data["column_code"],
                column_name=column_data.get("column_name", column_data["column_code"]),
                data_type=column_data.get("data_type", "STRING"),
                width=column_data.get("width"),
                required=column_data.get("required", False),
                sort_order=column_data.get("sort_order", column_index),
                created_by=self.actor,
            )
        return field

    def _create_conditional_rule(
        self, template: ReportTemplate, rule_data: dict, sections_by_code: dict
    ) -> ConditionalLogicRule:
        source = DynamicField.objects.filter(
            group__section__template=template, code=rule_data.get("source_field", "")
        ).first()
        if source is None:
            return None
        target_field = None
        target_section = None
        if rule_data.get("target_type") == ConditionTargetType.FIELD:
            target_field = DynamicField.objects.filter(
                group__section__template=template, code=rule_data.get("target")
            ).first()
        else:
            target_section = sections_by_code.get(rule_data.get("target"))
        return ConditionalLogicRule.objects.create(
            template=template,
            target_type=rule_data.get("target_type", ConditionTargetType.FIELD),
            target_field=target_field,
            target_section=target_section,
            condition_type=rule_data.get("condition_type", "SHOW_FIELD"),
            source_field=source,
            operator=rule_data.get("operator", ConditionOperator.EQUALS),
            value=rule_data.get("value"),
            logic=rule_data.get("logic", {}),
            priority=rule_data.get("priority", 0),
            is_active=True,
            created_by=self.actor,
        )

    def export_json(self, template: ReportTemplate) -> dict:
        """Serialize a template and its full schema for JSON export."""
        self._require(REPORT_TEMPLATE_EXPORT)
        schema = self.build_schema(template)
        payload = {
            "schema_version": 1,
            "template": {
                "code": template.code,
                "title": template.title,
                "reference_number": template.reference_number,
                "category": template.category.code,
                "department": template.department,
                "reporting_frequency": template.reporting_frequency,
                "description": template.description,
                "confidentiality": template.confidentiality,
                "retention_period_days": template.retention_period_days,
                "effective_from": (
                    template.effective_from.isoformat()
                    if template.effective_from
                    else None
                ),
                "expires_on": (
                    template.expires_on.isoformat() if template.expires_on else None
                ),
            },
            "sections": schema["sections"],
            "conditional_rules": schema["conditional_rules"],
            "components": schema["components"],
        }
        self._log(
            ReportTemplateAuditAction.EXPORTED,
            "ReportTemplate",
            template.pk,
            to_data={"checksum": schema_checksum(schema)},
        )
        return payload


# ---------------------------------------------------------------------------
# TemplateConditionService
# ---------------------------------------------------------------------------


class TemplateConditionService(ReportBuilderService):
    """Evaluate conditional logic rules and resolve field/section visibility."""

    def evaluate_rules(
        self, template: ReportTemplate, values: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Evaluate every active rule; returns result objects for preview."""
        results = []
        for rule in (
            template.conditional_rules.select_related(
                "source_field", "target_field", "target_section"
            )
            .filter(is_active=True)
            .order_by("priority", "created_at")
        ):
            source_value = values.get(rule.source_field.code)
            matched = self._evaluate_rule(rule, values)
            target_code = (
                rule.target_field.code
                if rule.target_type == ConditionTargetType.FIELD and rule.target_field
                else rule.target_section.code if rule.target_section else None
            )
            results.append(
                {
                    "rule_id": str(rule.pk),
                    "target_type": rule.target_type,
                    "target": target_code,
                    "condition_type": rule.condition_type,
                    "source_field": rule.source_field.code,
                    "source_value": source_value,
                    "matched": matched,
                }
            )
        return results

    def resolve_visibility(
        self, template: ReportTemplate, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Return a visibility map for fields and sections."""
        field_states: dict[str, dict[str, bool]] = {}
        section_states: dict[str, dict[str, bool]] = {}
        for result in self.evaluate_rules(template, values):
            if not result["matched"]:
                continue
            condition_type = result["condition_type"]
            target = result["target"]
            if not target:
                continue
            if result["target_type"] == ConditionTargetType.FIELD:
                state = field_states.setdefault(
                    target, {"visible": True, "enabled": True, "required": False}
                )
                if condition_type in ("HIDE_FIELD",):
                    state["visible"] = False
                elif condition_type == "SHOW_FIELD":
                    state["visible"] = True
                elif condition_type == "DISABLE_FIELD":
                    state["enabled"] = False
                elif condition_type == "ENABLE_FIELD":
                    state["enabled"] = True
                elif condition_type == "REQUIRE_FIELD":
                    state["required"] = True
            else:
                state = section_states.setdefault(target, {"visible": True})
                if condition_type == "HIDE_SECTION":
                    state["visible"] = False
                elif condition_type == "SHOW_SECTION":
                    state["visible"] = True
        return {"fields": field_states, "sections": section_states}

    def _evaluate_rule(
        self, rule: ConditionalLogicRule, values: dict[str, Any]
    ) -> bool:
        if rule.logic:
            return self._evaluate_logic(rule.logic, values)
        return self._matches(
            values.get(rule.source_field.code), rule.operator, rule.value
        )

    def _evaluate_logic(self, logic: dict, values: dict[str, Any]) -> bool:
        if not isinstance(logic, dict):
            return False
        results: list[bool] = []
        for key in ("all", "any"):
            for clause in logic.get(key, []):
                results.append(self._evaluate_clause(clause, values))
            if key == "all":
                return all(results)
            if results:
                return any(results)
        return False

    def _evaluate_clause(self, clause: Any, values: dict[str, Any]) -> bool:
        if isinstance(clause, dict) and ("all" in clause or "any" in clause):
            return self._evaluate_logic(clause, values)
        if isinstance(clause, dict):
            return self._matches(
                values.get(clause.get("field")),
                clause.get("operator"),
                clause.get("value"),
            )
        return False

    @staticmethod
    def _matches(source: Any, operator: str, expected: Any) -> bool:
        if operator == ConditionOperator.IS_EMPTY:
            return source in (None, "", [], {}, ())
        if operator == ConditionOperator.IS_NOT_EMPTY:
            return source not in (None, "", [], {}, ())
        if operator == ConditionOperator.EQUALS:
            return source == expected
        if operator == ConditionOperator.NOT_EQUALS:
            return source != expected
        if operator == ConditionOperator.CONTAINS:
            haystack = source if isinstance(source, list | tuple) else str(source or "")
            return expected in haystack
        if operator == ConditionOperator.NOT_CONTAINS:
            haystack = source if isinstance(source, list | tuple) else str(source or "")
            return expected not in haystack
        if operator == ConditionOperator.IN:
            return source in (expected or [])
        if operator == ConditionOperator.NOT_IN:
            return source not in (expected or [])
        if operator == ConditionOperator.STARTS_WITH:
            return str(source or "").startswith(str(expected))
        if operator == ConditionOperator.ENDS_WITH:
            return str(source or "").endswith(str(expected))
        if operator in (
            ConditionOperator.GREATER_THAN,
            ConditionOperator.GREATER_THAN_OR_EQUAL,
        ):
            comparison = TemplateConditionService._compare_values(source, expected)
            if comparison is None:
                return False
            return (
                comparison > 0
                if operator == ConditionOperator.GREATER_THAN
                else comparison >= 0
            )
        if operator in (
            ConditionOperator.LESS_THAN,
            ConditionOperator.LESS_THAN_OR_EQUAL,
        ):
            comparison = TemplateConditionService._compare_values(source, expected)
            if comparison is None:
                return False
            return (
                comparison < 0
                if operator == ConditionOperator.LESS_THAN
                else comparison <= 0
            )
        return False

    @staticmethod
    def _compare_values(left: Any, right: Any):
        try:
            return float(left) - float(right)
        except (TypeError, ValueError):
            try:
                return (left or "") < (right or "")
            except TypeError:
                return None


# ---------------------------------------------------------------------------
# TemplateCalculationService
# ---------------------------------------------------------------------------


class TemplateCalculationService(ReportBuilderService):
    """Evaluate calculated fields with the safe formula engine."""

    def evaluate(
        self, template: ReportTemplate, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Compute every calculated field in dependency order."""
        calculations = []
        for section in template.sections.all():
            for group in section.groups.all():
                for field in group.fields.filter(is_calculated=True):
                    calculations.append(field)
        results = dict(values)
        resolved: set[str] = set()
        for field in self._order_by_dependency(calculations):
            results[field.code] = evaluate_formula(field.formula, results)
            resolved.add(field.code)
        return results

    @staticmethod
    def _order_by_dependency(fields: list[DynamicField]) -> list[DynamicField]:
        by_code = {field.code: field for field in fields}
        ordered: list[DynamicField] = []
        visited: set[str] = set()

        def visit(code: str, path: tuple[str, ...]) -> None:
            if code in visited:
                return
            if code in path:
                raise CircularFormulaDependencyError(
                    "Formula cycle detected: " + " -> ".join((*path, code))
                )
            field = by_code[code]
            for ref in extract_field_references(field.formula):
                if ref in by_code:
                    visit(ref, (*path, code))
            visited.add(code)
            ordered.append(field)

        for code in by_code:
            visit(code, ())
        return ordered


# ---------------------------------------------------------------------------
# TemplatePreviewService
# ---------------------------------------------------------------------------


class TemplatePreviewService(ReportBuilderService):
    """Build preview context and render a safe server-side HTML preview."""

    def build_preview(
        self, template: ReportTemplate, values: dict[str, Any] | None = None
    ) -> dict:
        base_values = self._default_values(template)
        base_values.update(values or {})
        calculated = TemplateCalculationService(user=self.actor).evaluate(
            template, base_values
        )
        visibility = TemplateConditionService(user=self.actor).resolve_visibility(
            template, calculated
        )
        sections = self._build_sections(template, calculated, visibility)
        return {
            "template": template,
            "values": calculated,
            "visibility": visibility,
            "sections": sections,
        }

    @staticmethod
    def _default_values(template: ReportTemplate) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for section in template.sections.all():
            for group in section.groups.all():
                for field in group.fields.all():
                    if field.default_value is not None:
                        values[field.code] = field.default_value
        return values

    def _build_sections(self, template, values, visibility) -> list[dict]:
        sections = []
        top_level = template.sections.filter(parent__isnull=True).order_by(
            "sort_order", "name"
        )
        for section in top_level:
            sections.append(self._section_dict(section, values, visibility))
        return sections

    def _section_dict(self, section, values, visibility) -> dict:
        state = visibility.get("sections", {}).get(section.code, {"visible": True})
        groups = []
        for group in section.groups.order_by("sort_order", "name"):
            fields = []
            for field in group.fields.order_by("sort_order", "label"):
                fields.append(self._field_dict(field, values, visibility))
            groups.append({"group": group, "fields": fields})
        return {
            "section": section,
            "visible": state.get("visible", True),
            "groups": groups,
            "subsections": [
                self._section_dict(child, values, visibility)
                for child in section.subsections.order_by("sort_order", "name")
            ],
        }

    def _field_dict(self, field, values, visibility) -> dict:
        state = visibility.get("fields", {}).get(
            field.code, {"visible": True, "enabled": True, "required": False}
        )
        return {
            "field": field,
            "value": values.get(field.code),
            "visible": state.get("visible", True),
            "enabled": state.get("enabled", True),
            "required": state.get("required", field.required),
            "options": list(field.options.order_by("sort_order", "value")),
        }

    def render_html(
        self, template: ReportTemplate, values: dict[str, Any] | None = None
    ) -> str:
        context = self.build_preview(template, values)
        self._log(
            ReportTemplateAuditAction.PREVIEWED,
            "ReportTemplate",
            template.pk,
            to_data={"code": template.code},
        )
        return render_to_string("reports/includes/preview_schema.html", context)


# ---------------------------------------------------------------------------
# TemplateCloneService
# ---------------------------------------------------------------------------


class TemplateCloneService(ReportBuilderService):
    """Deep-clone a template into a new draft with new identifiers."""

    def clone(
        self,
        template: ReportTemplate,
        *,
        new_code: str,
        new_title: str,
        notes: str = "",
    ) -> ReportTemplate:
        self._require(REPORT_TEMPLATE_CLONE)
        schema = TemplateSchemaService(user=self.actor).build_schema(template)
        schema["template"] = {
            "code": new_code,
            "title": new_title,
            "reference_number": "",
        }
        clone = ReportTemplateService(user=self.actor).create(
            code=new_code,
            title=new_title,
            category=template.category,
            reporting_frequency=template.reporting_frequency,
            description=template.description,
            department=template.department,
            owner=template.owner,
            confidentiality=template.confidentiality,
            effective_from=template.effective_from,
            expires_on=template.expires_on,
            retention_period_days=template.retention_period_days,
            notes=notes,
        )
        TemplateSchemaService(user=self.actor).save_schema(clone, schema)
        self._log(
            ReportTemplateAuditAction.CLONED,
            "ReportTemplate",
            clone.pk,
            from_data={"source": template.reference_number},
            to_data={"clone": clone.reference_number},
            notes=notes,
        )
        return clone


# ---------------------------------------------------------------------------
# TemplateImportService
# ---------------------------------------------------------------------------


class TemplateImportService(ReportBuilderService):
    """Validate and import report templates from JSON payloads."""

    def validate_payload(self, payload: dict) -> list[str]:
        """Validate an import payload without creating records."""
        if not isinstance(payload, dict):
            return ["Import payload must be a JSON object."]
        schema = {
            "sections": payload.get("sections", []),
            "conditional_rules": payload.get("conditional_rules", []),
            "components": payload.get("components", []),
        }
        try:
            validators.validate_schema_structure(schema)
        except ValidationError as exc:
            return [str(exc)]
        errors: list[str] = []
        codes = set()
        for section in schema["sections"]:
            for group in section.get("groups", []):
                for field in group.get("fields", []):
                    if field.get("code") in codes:
                        errors.append(f"Duplicate field code '{field.get('code')}'.")
                    codes.add(field.get("code"))
                    if field.get("is_calculated"):
                        try:
                            validate_formula(field.get("formula", ""))
                        except InvalidFormulaError as exc:
                            errors.append(f"Field '{field.get('code')}': {exc}")
        return errors

    def import_json(
        self,
        payload: dict,
        *,
        category: ReportCategory,
        code: str | None = None,
        title: str | None = None,
        notes: str = "",
        dry_run: bool = False,
    ) -> ReportTemplate | None:
        """Import a template from an export payload.

        With ``dry_run=True`` only validation is performed and ``None`` is
        returned.
        """
        errors = self.validate_payload(payload)
        if errors:
            raise TemplateImportError("; ".join(errors))
        self._require(REPORT_TEMPLATE_IMPORT)
        template_data = payload.get("template", {})
        template_code = code or template_data.get("code")
        template_title = title or template_data.get("title")
        if not template_code or not template_title:
            raise TemplateImportError(
                "Import payload requires a template code and title."
            )
        if dry_run:
            return None
        template = ReportTemplateService(user=self.actor).create(
            code=template_code,
            title=template_title,
            category=category,
            reporting_frequency=template_data.get(
                "reporting_frequency", ReportingFrequency.ONE_OFF
            ),
            description=template_data.get("description", ""),
            department=template_data.get("department", ""),
            confidentiality=template_data.get(
                "confidentiality", ConfidentialityLevel.INTERNAL
            ),
            retention_period_days=template_data.get("retention_period_days", 365),
            notes=notes,
        )
        schema = {
            "template": {
                "code": template_code,
                "title": template_title,
                "reference_number": template.reference_number,
            },
            "sections": payload.get("sections", []),
            "conditional_rules": payload.get("conditional_rules", []),
            "components": payload.get("components", []),
        }
        TemplateSchemaService(user=self.actor).save_schema(template, schema)
        self._log(
            ReportTemplateAuditAction.IMPORTED,
            "ReportTemplate",
            template.pk,
            to_data={"reference_number": template.reference_number},
            notes=notes,
        )
        return template


# ---------------------------------------------------------------------------
# TemplateComparisonService
# ---------------------------------------------------------------------------


class TemplateComparisonService(ReportBuilderService):
    """Compare template versions and templates."""

    def compare_versions(
        self, left: ReportTemplateVersion, right: ReportTemplateVersion
    ) -> dict[str, Any]:
        changes = self._diff_dicts(left.schema_snapshot, right.schema_snapshot, path=())
        return {
            "left": {"version_number": left.version_number, "status": left.status},
            "right": {"version_number": right.version_number, "status": right.status},
            "changes": changes,
            "added_sections": self._added(left.schema_snapshot, right.schema_snapshot),
            "removed_sections": self._removed(
                left.schema_snapshot, right.schema_snapshot
            ),
            "added_fields": self._fields_diff(
                left.schema_snapshot, right.schema_snapshot
            ),
            "removed_fields": self._fields_diff(
                right.schema_snapshot, left.schema_snapshot
            ),
        }

    def compare_templates(
        self, left: ReportTemplate, right: ReportTemplate
    ) -> dict[str, Any]:
        left_version = left.versions.order_by("-major", "-minor").first()
        right_version = right.versions.order_by("-major", "-minor").first()
        if left_version is None or right_version is None:
            return {"changes": [], "added_sections": [], "removed_sections": []}
        return self.compare_versions(left_version, right_version)

    def _diff_dicts(
        self, left: Any, right: Any, path: tuple[str, ...]
    ) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        if type(left) is not type(right):
            return [{"path": "/".join(path) or "/", "from": left, "to": right}]
        if isinstance(left, dict):
            for key in sorted(set(left) | set(right)):
                if key not in left:
                    changes.append(
                        {
                            "path": "/".join((*path, str(key))),
                            "from": None,
                            "to": right[key],
                        }
                    )
                elif key not in right:
                    changes.append(
                        {
                            "path": "/".join((*path, str(key))),
                            "from": left[key],
                            "to": None,
                        }
                    )
                elif left[key] != right[key]:
                    changes.extend(
                        self._diff_dicts(left[key], right[key], (*path, str(key)))
                    )
        elif isinstance(left, list):
            if left != right:
                changes.append(
                    {"path": "/".join(path) or "/", "from": left, "to": right}
                )
        elif left != right:
            changes.append({"path": "/".join(path) or "/", "from": left, "to": right})
        return changes

    @staticmethod
    def _added(left: dict, right: dict) -> list[str]:
        left_codes = {s["code"] for s in left.get("sections", [])}
        return [
            s["code"] for s in right.get("sections", []) if s["code"] not in left_codes
        ]

    @staticmethod
    def _removed(left: dict, right: dict) -> list[str]:
        right_codes = {s["code"] for s in right.get("sections", [])}
        return [
            s["code"] for s in left.get("sections", []) if s["code"] not in right_codes
        ]

    @staticmethod
    def _fields_diff(left: dict, right: dict) -> list[str]:
        def collect(schema: dict) -> set[str]:
            codes: set[str] = set()
            for section in schema.get("sections", []):
                for group in section.get("groups", []):
                    for field in group.get("fields", []):
                        codes.add(field.get("code"))
            return codes

        return sorted(collect(right) - collect(left))


# ---------------------------------------------------------------------------
# TemplatePublicationService
# ---------------------------------------------------------------------------


class TemplatePublicationService(ReportBuilderService):
    """Validate and publish templates, and revert publication."""

    def validate_ready(self, template: ReportTemplate) -> list[str]:
        """Return human-readable blockers; empty means the template can publish."""
        errors: list[str] = []
        if template.status == ReportTemplateStatus.ARCHIVED:
            errors.append("Archived templates cannot be published.")
        if not template.title:
            errors.append("A template title is required.")
        if not template.category_id:
            errors.append("A report category is required.")
        working = TemplateVersionService(user=self.actor).working_version(template)
        if working is None:
            errors.append("A draft version is required before publishing.")
        schema_errors = TemplateSchemaService(user=self.actor).validate_schema(template)
        errors.extend(schema_errors)
        schema = TemplateSchemaService(user=self.actor).build_schema(template)
        sections = schema.get("sections", [])
        if not sections:
            errors.append("At least one section is required before publishing.")
        if not self._has_any_field(sections):
            errors.append("At least one dynamic field is required before publishing.")
        if not errors:
            try:
                TemplateSchemaService(user=self.actor).validate_formula_graph(template)
            except (CircularFormulaDependencyError, InvalidFormulaError) as exc:
                errors.append(str(exc))
            try:
                TemplateSchemaService(user=self.actor).validate_condition_graph(
                    template
                )
            except CircularConditionalDependencyError as exc:
                errors.append(str(exc))
        if template.expires_on and template.expires_on < timezone.localdate():
            errors.append("The template expiry date is in the past.")
        return errors

    @staticmethod
    def _has_any_field(sections: list[dict]) -> bool:
        return any(
            group.get("fields")
            for section in sections
            for group in section.get("groups", [])
        )

    def publish(
        self,
        template: ReportTemplate,
        *,
        version: ReportTemplateVersion | None = None,
        notes: str = "",
    ) -> ReportTemplateVersion:
        self._require(REPORT_TEMPLATE_PUBLISH)
        blockers = self.validate_ready(template)
        if blockers:
            self._log(
                ReportTemplateAuditAction.VALIDATION_FAILED,
                "ReportTemplate",
                template.pk,
                notes="; ".join(blockers),
            )
            raise TemplatePublishError("; ".join(blockers))
        working = version or TemplateVersionService(user=self.actor).working_version(
            template
        )
        if working is None:
            raise TemplatePublishError("No draft version is available to publish.")
        for previous in template.versions.filter(is_current=True):
            previous.is_current = False
            if previous.status == TemplateVersionStatus.PUBLISHED:
                previous.status = TemplateVersionStatus.SUPERSEDED
            previous.save(update_fields=["is_current", "status"])
        working.status = TemplateVersionStatus.PUBLISHED
        working.is_current = True
        working.published_at = timezone.now()
        working.published_by = self.actor
        working.save(
            update_fields=["status", "is_current", "published_at", "published_by"]
        )
        from_status = template.status
        template.status = ReportTemplateStatus.PUBLISHED
        template.current_version = working
        template.published_at = timezone.now()
        template.updated_by = self.actor
        template.save(
            update_fields=["status", "current_version", "published_at", "updated_at"]
        )
        self._history(
            template,
            from_status,
            ReportTemplateStatus.PUBLISHED,
            "PUBLISH",
            notes,
        )
        self._log(
            ReportTemplateAuditAction.PUBLISHED,
            "ReportTemplate",
            template.pk,
            to_data={
                "version_number": working.version_number,
                "status": ReportTemplateStatus.PUBLISHED,
                "checksum": working.checksum,
            },
            notes=notes,
        )
        return working

    def unpublish(self, template: ReportTemplate, *, notes: str = "") -> ReportTemplate:
        self._require(REPORT_TEMPLATE_PUBLISH)
        if template.status != ReportTemplateStatus.PUBLISHED:
            raise TemplateStatusTransitionError(
                "Only published templates can be unpublished."
            )
        from_status = template.status
        template.status = ReportTemplateStatus.DRAFT
        template.updated_by = self.actor
        template.save(update_fields=["status", "updated_at"])
        self._history(
            template,
            from_status,
            ReportTemplateStatus.DRAFT,
            "UNPUBLISH",
            notes,
        )
        self._log(
            ReportTemplateAuditAction.UNPUBLISHED,
            "ReportTemplate",
            template.pk,
            from_data={"status": from_status},
            to_data={"status": ReportTemplateStatus.DRAFT},
            notes=notes,
        )
        return template


# ---------------------------------------------------------------------------
# Category & settings services
# ---------------------------------------------------------------------------


class ReportCategoryService(ReportBuilderService):
    """Manage report categories."""

    def create(
        self,
        *,
        code: str,
        name: str,
        description: str = "",
        color: str = "",
        icon: str = "",
        sort_order: int = 0,
    ) -> ReportCategory:
        self._require(REPORT_TEMPLATE_CONFIGURE)
        category = ReportCategory.objects.create(
            code=code,
            name=name,
            description=description,
            color=color,
            icon=icon,
            sort_order=sort_order,
            created_by=self.actor,
            updated_by=self.actor,
        )
        self._log(
            ReportTemplateAuditAction.CATEGORY_CREATED,
            "ReportCategory",
            category.pk,
            to_data={"code": code, "name": name},
        )
        return category

    def update(self, category: ReportCategory, **fields) -> ReportCategory:
        self._require(REPORT_TEMPLATE_CONFIGURE)
        for name, value in fields.items():
            if value is not None and hasattr(category, name):
                setattr(category, name, value)
        category.updated_by = self.actor
        category.save()
        self._log(
            ReportTemplateAuditAction.CATEGORY_UPDATED,
            "ReportCategory",
            category.pk,
            to_data={"name": category.name},
        )
        return category

    def set_active(self, category: ReportCategory, active: bool) -> ReportCategory:
        self._require(REPORT_TEMPLATE_CONFIGURE)
        category.is_active = active
        category.updated_by = self.actor
        category.save(update_fields=["is_active", "updated_at"])
        action = (
            ReportTemplateAuditAction.CATEGORY_ACTIVATED
            if active
            else ReportTemplateAuditAction.CATEGORY_DEACTIVATED
        )
        self._log(action, "ReportCategory", category.pk, to_data={"is_active": active})
        return category


class ReportBuilderSettingsService(ReportBuilderService):
    """Update the centralized report builder settings singleton."""

    def update(self, **fields) -> ReportTemplateSettings:
        self._require(REPORT_TEMPLATE_CONFIGURE)
        settings = ReportTemplateSettings.load()
        for name, value in fields.items():
            if value is not None and hasattr(settings, name):
                setattr(settings, name, value)
        settings.updated_by = self.actor
        settings.save()
        self._log(
            ReportTemplateAuditAction.SETTINGS_UPDATED,
            "ReportTemplateSettings",
            settings.pk,
            to_data={key: value for key, value in fields.items() if value is not None},
        )
        return settings
