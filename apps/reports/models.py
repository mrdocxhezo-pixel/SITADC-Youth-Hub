"""Normalized data model for the Dynamic Report Builder and Report Management modules.

Phase 19 — The organization's centralized report template engine.  Templates
own immutable version snapshots, a tree of sections -> field groups -> dynamic
fields, plus options, validation rules, conditional logic, reference rules,
table column definitions, layout components, status history and an immutable
audit trail.  Every primary record carries actor and timestamp metadata and
supports soft deletion and archival.

Phase 20 — Report Management configuration models (ReportingPeriod,
ReportConfiguration) that support the report_instances app.
"""

from __future__ import annotations

from typing import ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    IsActiveModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)

from .constants import (
    ConditionOperator,
    ConditionTargetType,
    ConditionType,
    ConfidentialityLevel,
    FieldDataType,
    FieldType,
    ReferenceSourceModule,
    ReportingFrequency,
    ReportTemplateAuditAction,
    ReportTemplateStatus,
    SectionVisibilityMode,
    TemplateComponentType,
    TemplateVersionStatus,
    ValidationRuleType,
    ReportStatus,
    ReportValidationStatus,
    SubmissionStatus,
    EvidenceType,
)
from .managers import (
    IMMUTABLE_REPORT_HISTORY_MESSAGE,
    ActiveCategoryManager,
    ActiveReportManager,
    AllReportManager,
)
from .querysets import ReportCategoryQuerySet, ReportTemplateQuerySet


class ReportRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for report builder domain rows."""

    class Meta:
        abstract = True


class ReportCategory(ReportRecord, IsActiveModel):
    """An approved organizational report category (Phase 19 section 7)."""

    code = models.SlugField(_("Code"), max_length=60, unique=True, db_index=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    color = models.CharField(_("Color"), max_length=20, blank=True)
    icon = models.CharField(_("Icon"), max_length=60, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects: ClassVar = ActiveCategoryManager.from_queryset(ReportCategoryQuerySet)()
    all_objects: ClassVar = models.Manager()

    class Meta:
        verbose_name = _("Report Category")
        verbose_name_plural = _("Report Categories")
        ordering = ("sort_order", "name")
        indexes = [models.Index(fields=["is_active", "sort_order"])]

    def __str__(self) -> str:
        return self.name


class ReportTemplate(ReportRecord, SoftDeleteModel, ArchivableModel):
    """A reusable, versioned report template (Phase 19 section 6)."""

    reference_number = models.CharField(
        _("Template ID"), max_length=80, unique=True, db_index=True
    )
    code = models.SlugField(
        _("Template code"), max_length=100, unique=True, db_index=True
    )
    title = models.CharField(_("Title"), max_length=255)
    category = models.ForeignKey(
        ReportCategory,
        on_delete=models.PROTECT,
        related_name="templates",
        verbose_name=_("Report category"),
    )
    department = models.CharField(
        _("Department / directorate"), max_length=120, blank=True
    )
    reporting_frequency = models.CharField(
        _("Reporting frequency"),
        max_length=20,
        choices=ReportingFrequency.choices,
        default=ReportingFrequency.ONE_OFF,
    )
    description = models.TextField(_("Description"), blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_report_templates",
        verbose_name=_("Owner"),
    )
    current_version = models.ForeignKey(
        "ReportTemplateVersion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Current version"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReportTemplateStatus.choices,
        default=ReportTemplateStatus.DRAFT,
        db_index=True,
    )
    effective_from = models.DateField(_("Effective from"), null=True, blank=True)
    expires_on = models.DateField(_("Expiry date"), null=True, blank=True)
    retention_period_days = models.PositiveIntegerField(
        _("Retention period (days)"), default=365
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    objects: ClassVar = ActiveReportManager.from_queryset(ReportTemplateQuerySet)()
    all_objects: ClassVar = AllReportManager()

    class Meta:
        verbose_name = _("Report Template")
        verbose_name_plural = _("Report Templates")
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    @property
    def is_published(self) -> bool:
        return self.status == ReportTemplateStatus.PUBLISHED

    @property
    def is_editable(self) -> bool:
        return self.status == ReportTemplateStatus.DRAFT


class ReportTemplateVersion(ReportRecord):
    """An immutable schema snapshot for a template version (Phase 19 section 8)."""

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Template"),
    )
    version_number = models.CharField(_("Version number"), max_length=40)
    major = models.PositiveSmallIntegerField(_("Major version"), default=1)
    minor = models.PositiveSmallIntegerField(_("Minor version"), default=0)
    change_summary = models.TextField(_("Change summary"), blank=True)
    schema_snapshot = models.JSONField(_("Schema snapshot"), default=dict, blank=True)
    checksum = models.CharField(_("Checksum"), max_length=64, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TemplateVersionStatus.choices,
        default=TemplateVersionStatus.DRAFT,
        db_index=True,
    )
    is_current = models.BooleanField(_("Is current"), default=False, db_index=True)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_template_versions_published",
        verbose_name=_("Published by"),
    )

    class Meta:
        verbose_name = _("Template Version")
        verbose_name_plural = _("Template Versions")
        ordering = ("-major", "-minor")
        constraints = [
            models.UniqueConstraint(
                fields=["template", "version_number"],
                name="report_template_version_number_uniq",
            ),
            models.UniqueConstraint(
                fields=["template"],
                condition=models.Q(is_current=True),
                name="report_template_single_current_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.template.code} v{self.version_number}"

    @property
    def is_published(self) -> bool:
        return self.status == TemplateVersionStatus.PUBLISHED


class TemplateSection(ReportRecord):
    """A configurable section of a report template (Phase 19 section 10)."""

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name=_("Template"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subsections",
        verbose_name=_("Parent section"),
    )
    name = models.CharField(_("Name"), max_length=200)
    code = models.SlugField(_("Code"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    instructions = models.TextField(_("Instructions"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_repeatable = models.BooleanField(_("Repeatable"), default=False)
    is_collapsible = models.BooleanField(_("Collapsible"), default=True)
    is_locked = models.BooleanField(_("Locked"), default=False)
    visibility_mode = models.CharField(
        _("Visibility"),
        max_length=20,
        choices=SectionVisibilityMode.choices,
        default=SectionVisibilityMode.ALWAYS,
    )
    condition = models.JSONField(_("Visibility condition"), default=dict, blank=True)
    required_roles = models.JSONField(_("Required roles"), default=list, blank=True)
    required_departments = models.JSONField(
        _("Required departments"), default=list, blank=True
    )

    class Meta:
        verbose_name = _("Template Section")
        verbose_name_plural = _("Template Sections")
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["template", "code"],
                name="report_template_section_code_uniq",
            )
        ]

    def __str__(self) -> str:
        return self.name


class FieldGroup(ReportRecord):
    """A logical grouping of dynamic fields (Phase 19 section 12)."""

    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        related_name="groups",
        verbose_name=_("Section"),
    )
    name = models.CharField(_("Name"), max_length=200)
    code = models.SlugField(_("Code"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Field Group")
        verbose_name_plural = _("Field Groups")
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["section", "code"],
                name="report_field_group_code_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.section.name} / {self.name}"


class DynamicField(ReportRecord):
    """A configurable dynamic field within a field group (Phase 19 section 11)."""

    group = models.ForeignKey(
        FieldGroup,
        on_delete=models.CASCADE,
        related_name="fields",
        verbose_name=_("Field group"),
    )
    label = models.CharField(_("Label"), max_length=255)
    code = models.SlugField(_("Internal name"), max_length=120)
    field_type = models.CharField(
        _("Field type"),
        max_length=30,
        choices=FieldType.choices,
        default=FieldType.TEXT,
        db_index=True,
    )
    data_type = models.CharField(
        _("Data type"),
        max_length=20,
        choices=FieldDataType.choices,
        default=FieldDataType.STRING,
    )
    required = models.BooleanField(_("Required"), default=False)
    read_only = models.BooleanField(_("Read only"), default=False)
    hidden = models.BooleanField(_("Hidden"), default=False)
    is_repeatable = models.BooleanField(_("Repeatable"), default=False)
    is_calculated = models.BooleanField(_("Calculated"), default=False)
    formula = models.CharField(_("Formula"), max_length=500, blank=True)
    default_value = models.JSONField(_("Default value"), null=True, blank=True)
    placeholder = models.CharField(_("Placeholder"), max_length=255, blank=True)
    help_text = models.TextField(_("Help text"), blank=True)
    tooltip = models.CharField(_("Tooltip"), max_length=255, blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Dynamic Field")
        verbose_name_plural = _("Dynamic Fields")
        ordering = ("sort_order", "label")
        constraints = [
            models.UniqueConstraint(
                fields=["group", "code"],
                name="report_dynamic_field_code_uniq",
            )
        ]
        indexes = [models.Index(fields=["field_type"])]

    def __str__(self) -> str:
        return self.label


class FieldOption(ReportRecord):
    """A selectable option for selection-type dynamic fields."""

    field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name=_("Field"),
    )
    value = models.CharField(_("Value"), max_length=120)
    label = models.CharField(_("Label"), max_length=200)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Field Option")
        verbose_name_plural = _("Field Options")
        ordering = ("sort_order", "value")
        constraints = [
            models.UniqueConstraint(
                fields=["field", "value"],
                name="report_field_option_value_uniq",
            )
        ]

    def __str__(self) -> str:
        return self.label


class ValidationRule(ReportRecord):
    """A configurable validation rule attached to a dynamic field."""

    field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="validation_rules",
        verbose_name=_("Field"),
    )
    rule_type = models.CharField(
        _("Rule type"),
        max_length=30,
        choices=ValidationRuleType.choices,
        db_index=True,
    )
    operator = models.CharField(_("Operator"), max_length=40, blank=True)
    params = models.JSONField(_("Parameters"), default=dict, blank=True)
    message = models.CharField(_("Message"), max_length=255, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Validation Rule")
        verbose_name_plural = _("Validation Rules")
        ordering = ("sort_order",)

    def __str__(self) -> str:
        return f"{self.field.label}: {self.get_rule_type_display()}"


class ConditionalLogicRule(ReportRecord):
    """A conditional rule that shows, hides, enables, disables or requires
    a field or section based on the value of a source field."""

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="conditional_rules",
        verbose_name=_("Template"),
    )
    target_type = models.CharField(
        _("Target type"),
        max_length=20,
        choices=ConditionTargetType.choices,
        default=ConditionTargetType.FIELD,
    )
    target_field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conditional_rules",
        verbose_name=_("Target field"),
    )
    target_section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="conditional_rules",
        verbose_name=_("Target section"),
    )
    condition_type = models.CharField(
        _("Condition type"),
        max_length=20,
        choices=ConditionType.choices,
        db_index=True,
    )
    source_field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="drives_conditional_rules",
        verbose_name=_("Source field"),
    )
    operator = models.CharField(
        _("Operator"),
        max_length=30,
        choices=ConditionOperator.choices,
        default=ConditionOperator.EQUALS,
    )
    value = models.JSONField(_("Value"), null=True, blank=True)
    logic = models.JSONField(_("Advanced logic"), default=dict, blank=True)
    priority = models.PositiveIntegerField(_("Priority"), default=0)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Conditional Logic Rule")
        verbose_name_plural = _("Conditional Logic Rules")
        ordering = ("priority", "created_at")

    def __str__(self) -> str:
        target = self.target_field or self.target_section
        return f"{self.condition_type}: {target}"

    def clean(self) -> None:
        target_field = self.target_field
        target_section = self.target_section
        has_field_target = target_field is not None
        has_section_target = target_section is not None
        if self.target_type == ConditionTargetType.FIELD and not has_field_target:
            raise ValidationError(
                _("A field rule requires a target field."), code="condition_target"
            )
        if self.target_type == ConditionTargetType.SECTION and not has_section_target:
            raise ValidationError(
                _("A section rule requires a target section."), code="condition_target"
            )
        if has_field_target and has_section_target:
            raise ValidationError(
                _("A rule cannot target both a field and a section."),
                code="condition_target",
            )
        if (
            self.source_field is not None
            and self.source_field_id == self.target_field_id
        ):
            raise ValidationError(
                _("A rule cannot evaluate a field against itself."),
                code="condition_self",
            )


class TemplateReferenceRule(ReportRecord):
    """Configuration for a referenced field that pulls values from another
    module without duplicating records."""

    field = models.OneToOneField(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="reference_rule",
        verbose_name=_("Field"),
    )
    source_module = models.CharField(
        _("Source module"),
        max_length=30,
        choices=ReferenceSourceModule.choices,
    )
    model_name = models.CharField(_("Model name"), max_length=120)
    display_field = models.CharField(_("Display field"), max_length=120, blank=True)
    value_field = models.CharField(_("Value field"), max_length=120, blank=True)
    filters = models.JSONField(_("Filters"), default=dict, blank=True)
    is_multiple = models.BooleanField(_("Multiple selection"), default=False)
    allowed_roles = models.JSONField(_("Allowed roles"), default=list, blank=True)

    class Meta:
        verbose_name = _("Template Reference Rule")
        verbose_name_plural = _("Template Reference Rules")

    def __str__(self) -> str:
        return f"{self.field.label} <- {self.source_module}.{self.model_name}"


class ReportTemplateStatusHistory(ReportRecord):
    """Immutable status transition history for a report template."""

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name=_("Template"),
    )
    from_status = models.CharField(_("From status"), max_length=40, blank=True)
    to_status = models.CharField(_("To status"), max_length=40)
    action = models.CharField(_("Action"), max_length=40)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Template Status History")
        verbose_name_plural = _("Template Status History")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["template", "created_at"])]

    def __str__(self) -> str:
        return f"{self.template.code}: {self.from_status or 'NEW'} -> {self.to_status}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_REPORT_HISTORY_MESSAGE, code="immutable_history"
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_REPORT_HISTORY_MESSAGE, code="immutable_history"
        )


class TemplateComponent(ReportRecord):
    """A reusable layout component of a report template (Phase 19 section 9)."""

    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="components",
        verbose_name=_("Template"),
    )
    component_type = models.CharField(
        _("Component type"),
        max_length=20,
        choices=TemplateComponentType.choices,
        default=TemplateComponentType.HEADER,
    )
    name = models.CharField(_("Name"), max_length=200)
    code = models.SlugField(_("Code"), max_length=100, blank=True)
    configuration = models.JSONField(_("Configuration"), default=dict, blank=True)
    is_shared = models.BooleanField(_("Shared component"), default=False)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Template Component")
        verbose_name_plural = _("Template Components")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class TableColumnDefinition(ReportRecord):
    """A column definition for a table / grid dynamic field."""

    table_field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="table_columns",
        verbose_name=_("Table field"),
    )
    column_name = models.CharField(_("Column name"), max_length=200)
    column_code = models.CharField(_("Column code"), max_length=120)
    data_type = models.CharField(
        _("Data type"),
        max_length=20,
        choices=FieldDataType.choices,
        default=FieldDataType.STRING,
    )
    width = models.PositiveSmallIntegerField(_("Width"), null=True, blank=True)
    required = models.BooleanField(_("Required"), default=False)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Table Column Definition")
        verbose_name_plural = _("Table Column Definitions")
        ordering = ("sort_order",)
        constraints = [
            models.UniqueConstraint(
                fields=["table_field", "column_code"],
                name="report_table_column_code_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.table_field.label}.{self.column_code}"


class ReportTemplateSettings(ReportRecord):
    """Centralized report builder configuration (Phase 19 section 69)."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    template_numbering_scheme_code = models.CharField(
        _("Template numbering scheme"), max_length=60, blank=True
    )
    default_reporting_frequency = models.CharField(
        _("Default reporting frequency"), max_length=20, blank=True
    )
    branding = models.JSONField(_("Branding"), default=dict, blank=True)
    default_page_layout = models.JSONField(
        _("Default page layout"), default=dict, blank=True
    )
    default_export_settings = models.JSONField(
        _("Default export settings"), default=dict, blank=True
    )
    auto_save_interval_seconds = models.PositiveIntegerField(
        _("Auto-save interval (seconds)"), default=60
    )
    archive_rules = models.JSONField(_("Archive rules"), default=dict, blank=True)
    notification_rules = models.JSONField(
        _("Notification rules"), default=dict, blank=True
    )
    retention_default_days = models.PositiveIntegerField(
        _("Default retention period (days)"), default=365
    )
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Report Builder Settings")
        verbose_name_plural = _("Report Builder Settings")

    def __str__(self) -> str:
        return "Report Builder Settings"

    @classmethod
    def load(cls) -> ReportTemplateSettings:
        """Return the singleton settings row, creating it if necessary."""
        return cls.objects.get_or_create(key="default")[0]


class ReportTemplateAuditRecord(ReportRecord):
    """Immutable audit trail for report builder activity (Phase 19 section 55)."""

    entity_type = models.CharField(_("Entity type"), max_length=60, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=60, db_index=True)
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=ReportTemplateAuditAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_template_audits",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Report Builder Audit Record")
        verbose_name_plural = _("Report Builder Audit Records")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["entity_type", "entity_id"])]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type} {self.entity_id}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_REPORT_HISTORY_MESSAGE, code="immutable_audit"
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_REPORT_HISTORY_MESSAGE, code="immutable_audit")

# --- Workflow Configuration (Phase 19 Section 71) ---

class WorkflowStage(ReportRecord, IsActiveModel):
    """A configurable stage in a report submission workflow (Phase 19 section 71)."""

    name = models.CharField(_("Stage name"), max_length=100)
    code = models.SlugField(_("Stage code"), max_length=60, unique=True)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_initial = models.BooleanField(_("Initial stage"), default=False)
    is_final = models.BooleanField(_("Final stage"), default=False)

    class Meta:
        verbose_name = _("Workflow Stage")
        verbose_name_plural = _("Workflow Stages")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class ApprovalRule(ReportRecord):
    """A rule defining who can approve a report at a specific stage."""

    stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.CASCADE,
        related_name="approval_rules",
        verbose_name=_("Workflow stage"),
    )
    role = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_approval_rules",
        verbose_name=_("Required role/user"),
    )
    requires_signature = models.BooleanField(
        _("Requires digital signature"), default=False
    )
    min_approvals_required = models.PositiveSmallIntegerField(
        _("Min approvals required"), default=1
    )
    is_mandatory = models.BooleanField(_("Mandatory"), default=True)

    class Meta:
        verbose_name = _("Approval Rule")
        verbose_name_plural = _("Approval Rules")
        ordering = ("stage", "created_at")

    def __str__(self) -> str:
        return f"{self.stage.name} - {self.role}"


class WorkflowDefinition(ReportRecord):
    """Configuration for a report template's workflow."""

    template = models.OneToOneField(
        ReportTemplate,
        on_delete=models.CASCADE,
        related_name="workflow_definition",
        verbose_name=_("Template"),
    )
    name = models.CharField(_("Workflow name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Workflow Definition")
        verbose_name_plural = _("Workflow Definitions")

    def __str__(self) -> str:
        return f"Workflow for {self.template.code}"


# --- Phase 20: Report Management Configuration Models ---


class ReportingPeriod(ReportRecord):
    """A defined reporting period (e.g. Q1 2026, FY2025)."""

    name = models.CharField(_("Period name"), max_length=120)
    code = models.SlugField(_("Code"), max_length=60, unique=True)
    frequency = models.CharField(
        _("Frequency"),
        max_length=20,
        choices=ReportingFrequency.choices,
        default=ReportingFrequency.QUARTERLY,
    )
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Reporting Period")
        verbose_name_plural = _("Reporting Periods")
        ordering = ("-start_date",)
        indexes = [models.Index(fields=["start_date", "end_date"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.start_date} – {self.end_date})"


class ReportConfiguration(ReportRecord):
    """Global configuration for Report Management (singleton)."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    numbering_scheme_code = models.CharField(
        _("Numbering scheme code"), max_length=60, blank=True
    )
    numbering_prefix = models.CharField(
        _("Reference number prefix"), max_length=30, default="RPT"
    )
    auto_save_interval_seconds = models.PositiveIntegerField(
        _("Auto-save interval (seconds)"), default=60
    )
    draft_retention_days = models.PositiveIntegerField(
        _("Draft retention (days)"), default=90
    )
    archive_after_days = models.PositiveIntegerField(
        _("Archive approved reports after (days)"), default=30
    )
    default_confidentiality = models.CharField(
        _("Default confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    allow_withdrawal = models.BooleanField(_("Allow report withdrawal"), default=True)
    allow_resubmission = models.BooleanField(_("Allow resubmission"), default=True)
    require_evidence_on_submit = models.BooleanField(
        _("Require evidence on submit"), default=False
    )
    reminder_days_before_due = models.PositiveIntegerField(
        _("Reminder days before due"), default=7
    )
    escalation_days_after_due = models.PositiveIntegerField(
        _("Escalation days after due"), default=3
    )
    max_file_size_mb = models.PositiveIntegerField(
        _("Max attachment file size (MB)"), default=20
    )
    allowed_file_types = models.JSONField(
        _("Allowed file types"), default=list, blank=True
    )
    notification_rules = models.JSONField(
        _("Notification rules"), default=dict, blank=True
    )
    export_defaults = models.JSONField(
        _("Export defaults"), default=dict, blank=True
    )
    branding = models.JSONField(_("Branding"), default=dict, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Report Management Configuration")
        verbose_name_plural = _("Report Management Configurations")

    def __str__(self) -> str:
        return "Report Management Configuration"

    @classmethod
    def load(cls) -> ReportConfiguration:
        """Return the singleton settings row, creating it if necessary."""
        return cls.objects.get_or_create(key="default")[0]
