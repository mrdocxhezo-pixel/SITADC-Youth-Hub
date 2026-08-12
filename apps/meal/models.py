"""Normalized data model for the Phase 18 MEAL module.

The module is the organization's centralized monitoring, evaluation,
accountability and learning platform.  Every primary record carries actor and
timestamp metadata, supports soft deletion and archival, and records its
workflow through an immutable status history and audit trail.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, NoReturn, cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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
from apps.programs.validators import validate_percentage, validate_program_document

from . import constants
from .constants import (
    BaselineStatus,
    BestPracticeStatus,
    ComplaintStatus,
    CorrectiveActionStatus,
    DataCollectionPlanStatus,
    DataSubmissionStatus,
    DQADimension,
    DQAStatus,
    EvaluationStatus,
    FeedbackStatus,
    FindingCategory,
    IndicatorStatus,
    IndicatorType,
    LearningLogStatus,
    LessonStatus,
    LogframeLevel,
    MEALReportType,
    MonitoringPlanStatus,
    MonitoringVisitStatus,
    OutcomeHarvestStatus,
    Priority,
    ReferenceDataKind,
    ReportStatus,
    ResultLevel,
    ScorecardStatus,
    TargetStatus,
    WorkflowStatus,
)
from .managers import IMMUTABLE_MEAL_HISTORY_MESSAGE, ActiveMEALManager
from .storage import private_meal_storage


class MEALRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for MEAL domain rows."""

    class Meta:
        abstract = True


class MEALReferenceData(MEALRecord):
    """Configurable taxonomy shared by the MEAL module."""

    kind = models.CharField(
        _("Kind"), max_length=40, choices=ReferenceDataKind.choices, db_index=True
    )
    code = models.SlugField(_("Code"), max_length=80)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    active = models.BooleanField(_("Active"), default=True, db_index=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("MEAL Reference Data")
        verbose_name_plural = _("MEAL Reference Data")
        ordering = ("kind", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "code"], name="meal_ref_kind_code_uniq"
            )
        ]
        indexes = [models.Index(fields=["kind", "active", "order"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.name}"


class TheoryOfChange(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A strategic change pathway for the organization or a program."""

    reference_number = models.CharField(
        _("Theory of Change ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="theories_of_change",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    strategic_goal = models.TextField()
    development_challenge = models.TextField(blank=True)
    context = models.TextField(blank=True)
    assumptions = models.TextField(blank=True)
    preconditions = models.TextField(blank=True)
    inputs = models.TextField(blank=True)
    activities = models.TextField(blank=True)
    outputs = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    long_term_impact = models.TextField(blank=True)
    risks = models.TextField(blank=True)
    external_factors = models.TextField(blank=True)
    success_indicators = models.TextField(blank=True)
    version = models.CharField(_("Version"), max_length=40, default="1.0")
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )
    effective_from = models.DateField(_("Effective from"), null=True, blank=True)

    objects: ClassVar[models.Manager[TheoryOfChange]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Theory of Change")
        verbose_name_plural = _("Theories of Change")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class ResultsFramework(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A results framework linking strategic objectives to results."""

    reference_number = models.CharField(
        _("Framework ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="results_frameworks",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    strategic_objective = models.TextField()
    description = models.TextField(blank=True)
    reporting_frequency = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="results_framework_frequencies",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REPORTING_FREQUENCY},
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_results_frameworks",
        null=True,
        blank=True,
    )
    version = models.CharField(_("Version"), max_length=40, default="1.0")
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )
    effective_from = models.DateField(_("Effective from"), null=True, blank=True)
    effective_to = models.DateField(_("Effective to"), null=True, blank=True)

    objects: ClassVar[models.Manager[ResultsFramework]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Results Framework")
        verbose_name_plural = _("Results Frameworks")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range

        validate_date_range(self.effective_from, self.effective_to)


class ResultStatement(MEALRecord):
    """A goal, intermediate result, output, outcome, or impact in a framework."""

    framework = models.ForeignKey(
        ResultsFramework,
        on_delete=models.CASCADE,
        related_name="statements",
    )
    level = models.CharField(
        _("Level"),
        max_length=30,
        choices=ResultLevel.choices,
        default=ResultLevel.OUTCOME,
        db_index=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(blank=True)
    indicators: models.ManyToManyField[Indicator, Indicator] = models.ManyToManyField(
        "Indicator",
        related_name="result_statements",
        blank=True,
    )
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Result Statement")
        verbose_name_plural = _("Result Statements")
        ordering = ("framework", "order", "level")

    def __str__(self) -> str:
        return f"{self.get_level_display()}: {self.title}"


class LogicalFramework(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A logical framework (logframe) with versioned revisions."""

    reference_number = models.CharField(
        _("Logframe ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="logframes",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="logframes",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    goal = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    version = models.CharField(_("Version"), max_length=40, default="1.0")
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=WorkflowStatus.choices,
        default=WorkflowStatus.DRAFT,
        db_index=True,
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_logframes",
        null=True,
        blank=True,
    )
    reporting_schedule = models.TextField(blank=True)

    objects: ClassVar[models.Manager[LogicalFramework]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Logical Framework")
        verbose_name_plural = _("Logical Frameworks")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("A logframe requires a program or a project."))
        if self.program and self.project:
            raise ValidationError(
                _("A logframe belongs to a program or a project, not both.")
            )


class LogframeRow(MEALRecord):
    """A goal/purpose/output/activity row with verification and assumptions."""

    logframe = models.ForeignKey(
        LogicalFramework,
        on_delete=models.CASCADE,
        related_name="rows",
    )
    level = models.CharField(
        _("Level"),
        max_length=20,
        choices=LogframeLevel.choices,
        default=LogframeLevel.ACTIVITY,
        db_index=True,
    )
    statement = models.CharField(_("Statement"), max_length=255)
    means_of_verification = models.TextField(blank=True)
    assumptions = models.TextField(blank=True)
    indicators: models.ManyToManyField[Indicator, Indicator] = models.ManyToManyField(
        "Indicator",
        related_name="logframe_rows",
        blank=True,
    )
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Logframe Row")
        verbose_name_plural = _("Logframe Rows")
        ordering = ("logframe", "level", "order")

    def __str__(self) -> str:
        return f"{self.get_level_display()}: {self.statement}"


class IndicatorCategory(MEALRecord, IsActiveModel):
    """Configurable indicator category (output, outcome, impact, ...)."""

    code = models.SlugField(_("Code"), max_length=80, unique=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    order = models.PositiveIntegerField(_("Order"), default=0)

    class Meta:
        verbose_name = _("Indicator Category")
        verbose_name_plural = _("Indicator Categories")
        ordering = ("order", "name")

    def __str__(self) -> str:
        return self.name


class Indicator(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A reusable performance indicator in the organizational registry."""

    reference_number = models.CharField(
        _("Indicator ID"), max_length=80, unique=True, db_index=True
    )
    code = models.SlugField(_("Indicator code"), max_length=80, unique=True)
    title = models.CharField(_("Indicator title"), max_length=255)
    description = models.TextField(blank=True)
    formula = models.CharField(_("Formula"), max_length=255, blank=True)
    calculation_method = models.TextField(blank=True)
    unit = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="indicator_units",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.INDICATOR_UNIT},
    )
    indicator_type = models.CharField(
        _("Indicator type"),
        max_length=30,
        choices=IndicatorType.choices,
        default=IndicatorType.OUTPUT,
        db_index=True,
    )
    category = models.ForeignKey(
        IndicatorCategory,
        on_delete=models.PROTECT,
        related_name="indicators",
        null=True,
        blank=True,
    )
    data_source = models.ForeignKey(
        "DataSource",
        on_delete=models.SET_NULL,
        related_name="indicators",
        null=True,
        blank=True,
    )
    collection_method = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="indicator_collection_methods",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.COLLECTION_METHOD},
    )
    reporting_frequency = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="indicator_frequencies",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REPORTING_FREQUENCY},
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_meal_indicators",
        null=True,
        blank=True,
    )
    verification_method = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="indicator_verification_methods",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.VERIFICATION_METHOD},
    )
    disaggregation = models.ManyToManyField(
        MEALReferenceData,
        related_name="disaggregated_indicators",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.DISAGGREGATION_DIMENSION},
    )
    programs = models.ManyToManyField(
        "programs.Program", related_name="meal_indicators", blank=True
    )
    projects = models.ManyToManyField(
        "programs.Project", related_name="meal_indicators", blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=IndicatorStatus.choices,
        default=IndicatorStatus.DRAFT,
        db_index=True,
    )

    objects: ClassVar[models.Manager[Indicator]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Indicator")
        verbose_name_plural = _("Indicators")
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"

    @property
    def latest_approved_baseline(self):
        return (
            self.baselines.filter(status=BaselineStatus.APPROVED)
            .order_by("-collection_date")
            .first()
        )

    @property
    def latest_target(self):
        return (
            self.targets.filter(status=TargetStatus.APPROVED)
            .order_by("-period_end")
            .first()
        )

    @property
    def latest_result(self):
        return (
            self.results.filter(status=DataSubmissionStatus.APPROVED)
            .order_by("-submission_date")
            .first()
        )


class IndicatorBaseline(MEALRecord):
    """An immutable-after-approval baseline value for an indicator."""

    reference_number = models.CharField(
        _("Baseline ID"), max_length=80, unique=True, db_index=True
    )
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="baselines",
    )
    value = models.DecimalField(_("Baseline value"), max_digits=18, decimal_places=2)
    collection_date = models.DateField(_("Collection date"), default=timezone.localdate)
    data_source = models.TextField(_("Data source"), blank=True)
    collection_method = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="baseline_collection_methods",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.COLLECTION_METHOD},
    )
    geographic_coverage = models.CharField(max_length=160, blank=True)
    population_covered = models.CharField(max_length=160, blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_meal_baselines",
        null=True,
        blank=True,
    )
    evidence_file = models.FileField(
        _("Supporting evidence"),
        upload_to="meal/baselines/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BaselineStatus.choices,
        default=BaselineStatus.PENDING_APPROVAL,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Indicator Baseline")
        verbose_name_plural = _("Indicator Baselines")
        ordering = ("-collection_date",)
        indexes = [models.Index(fields=["indicator", "status"])]

    def __str__(self) -> str:
        return f"{self.indicator.code} baseline: {self.value}"


class IndicatorTarget(MEALRecord):
    """A target value for an indicator over a defined period."""

    reference_number = models.CharField(
        _("Target ID"), max_length=80, unique=True, db_index=True
    )
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="targets",
    )
    period_label = models.CharField(_("Period label"), max_length=120)
    period_start = models.DateField(_("Period start"), null=True, blank=True)
    period_end = models.DateField(_("Period end"), null=True, blank=True)
    value = models.DecimalField(_("Target value"), max_digits=18, decimal_places=2)
    threshold = models.PositiveIntegerField(_("Achievement threshold (%)"), default=100)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TargetStatus.choices,
        default=TargetStatus.PENDING_APPROVAL,
        db_index=True,
    )
    revised_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        related_name="revisions",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Indicator Target")
        verbose_name_plural = _("Indicator Targets")
        ordering = ("-period_end",)
        indexes = [models.Index(fields=["indicator", "status"])]

    def __str__(self) -> str:
        return f"{self.indicator.code} target ({self.period_label})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range, validate_percentage

        validate_date_range(self.period_start, self.period_end)
        validate_percentage(self.threshold)


class IndicatorResult(MEALRecord):
    """An approved actual result for an indicator period."""

    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="results",
    )
    target = models.ForeignKey(
        IndicatorTarget,
        on_delete=models.SET_NULL,
        related_name="results",
        null=True,
        blank=True,
    )
    period_label = models.CharField(_("Period label"), max_length=120)
    submission_date = models.DateField(_("Submission date"), default=timezone.localdate)
    value = models.DecimalField(_("Actual value"), max_digits=18, decimal_places=2)
    data_source = models.ForeignKey(
        "DataSource",
        on_delete=models.SET_NULL,
        related_name="indicator_results",
        null=True,
        blank=True,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_indicator_results",
        null=True,
        blank=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_indicator_results",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DataSubmissionStatus.choices,
        default=DataSubmissionStatus.DRAFT,
        db_index=True,
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Indicator Result")
        verbose_name_plural = _("Indicator Results")
        ordering = ("-submission_date",)
        indexes = [models.Index(fields=["indicator", "status"])]

    def __str__(self) -> str:
        return f"{self.indicator.code}: {self.value}"


class DataSource(MEALRecord, IsActiveModel):
    """A configurable data source for monitoring data."""

    code = models.SlugField(_("Code"), max_length=80, unique=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    source_type = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="data_sources",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.DATA_SOURCE_TYPE},
    )
    verification_method = models.TextField(_("Verification method"), blank=True)

    class Meta:
        verbose_name = _("Data Source")
        verbose_name_plural = _("Data Sources")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class DataCollectionTool(MEALRecord, IsActiveModel):
    """A configurable data collection tool or template."""

    code = models.SlugField(_("Code"), max_length=80, unique=True)
    name = models.CharField(_("Name"), max_length=160)
    description = models.TextField(_("Description"), blank=True)
    tool_type = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="collection_tools",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.COLLECTION_TOOL_TYPE},
    )
    template_file = models.FileField(
        _("Template"),
        upload_to="meal/tools/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Data Collection Tool")
        verbose_name_plural = _("Data Collection Tools")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class DataCollectionPlan(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A scheduled data collection activity with assigned enumerators."""

    reference_number = models.CharField(
        _("Plan ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_collection_plans",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_collection_plans",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(blank=True)
    start_date = models.DateField(_("Start date"), default=timezone.localdate)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    frequency = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="collection_plan_frequencies",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REPORTING_FREQUENCY},
    )
    tools = models.ManyToManyField(
        DataCollectionTool, related_name="collection_plans", blank=True
    )
    enumerators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="meal_collection_plans", blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DataCollectionPlanStatus.choices,
        default=DataCollectionPlanStatus.DRAFT,
        db_index=True,
    )

    objects: ClassVar[models.Manager[DataCollectionPlan]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Data Collection Plan")
        verbose_name_plural = _("Data Collection Plans")
        ordering = ("-start_date",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range

        validate_date_range(self.start_date, self.end_date)


class DataSubmission(MEALRecord):
    """A traceable, validated data submission against a collection plan."""

    plan = models.ForeignKey(
        DataCollectionPlan,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    indicator = models.ForeignKey(
        Indicator,
        on_delete=models.CASCADE,
        related_name="data_submissions",
    )
    submission_date = models.DateField(_("Submission date"), default=timezone.localdate)
    enumerator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="meal_data_submissions",
        null=True,
        blank=True,
    )
    data = models.JSONField(_("Data"), default=dict, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DataSubmissionStatus.choices,
        default=DataSubmissionStatus.DRAFT,
        db_index=True,
    )
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="validated_meal_submissions",
        null=True,
        blank=True,
    )
    validated_at = models.DateTimeField(_("Validated at"), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_meal_submissions",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    evidence_file = models.FileField(
        _("Supporting evidence"),
        upload_to="meal/submissions/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Data Submission")
        verbose_name_plural = _("Data Submissions")
        ordering = ("-submission_date",)
        indexes = [models.Index(fields=["plan", "status"])]

    def __str__(self) -> str:
        return f"{self.indicator.code} submission ({self.submission_date})"


class MonitoringPlan(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A recurring monitoring schedule for a program or project."""

    reference_number = models.CharField(
        _("Monitoring plan ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_monitoring_plans",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_monitoring_plans",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    frequency = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="monitoring_plan_frequencies",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REPORTING_FREQUENCY},
    )
    next_due_date = models.DateField(_("Next due date"), default=timezone.localdate)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_monitoring_plans",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MonitoringPlanStatus.choices,
        default=MonitoringPlanStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(_("Notes"), blank=True)

    objects: ClassVar[models.Manager[MonitoringPlan]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Monitoring Plan")
        verbose_name_plural = _("Monitoring Plans")
        ordering = ("next_due_date",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class MonitoringVisit(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A field monitoring visit with findings and recommendations."""

    reference_number = models.CharField(
        _("Visit ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="monitoring_visits",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="monitoring_visits",
        null=True,
        blank=True,
    )
    community = models.CharField(_("Community"), max_length=160, blank=True)
    visit_date = models.DateField(_("Visit date"), default=timezone.localdate)
    team = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="monitoring_visits", blank=True
    )
    objectives = models.TextField(_("Objectives"), blank=True)
    findings_summary = models.TextField(_("Findings summary"), blank=True)
    recommendations = models.TextField(_("Recommendations"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=25,
        choices=MonitoringVisitStatus.choices,
        default=MonitoringVisitStatus.PLANNED,
        db_index=True,
    )
    follow_up_due = models.DateField(_("Follow-up due"), null=True, blank=True)
    gps_coordinates = models.CharField(_("GPS coordinates"), max_length=120, blank=True)
    report_file = models.FileField(
        _("Visit report"),
        upload_to="meal/monitoring/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )
    photo = models.FileField(
        _("Supporting photograph"),
        upload_to="meal/monitoring/photos/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )

    objects: ClassVar[models.Manager[MonitoringVisit]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Monitoring Visit")
        verbose_name_plural = _("Monitoring Visits")
        ordering = ("-visit_date",)

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.visit_date}"

    def clean(self) -> None:
        super().clean()
        if self.visit_date > timezone.localdate():
            raise ValidationError({"visit_date": _("Visit date cannot be future.")})


class MonitoringFinding(MEALRecord):
    """An individual finding raised during a monitoring visit."""

    visit = models.ForeignKey(
        MonitoringVisit,
        on_delete=models.CASCADE,
        related_name="findings",
    )
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=FindingCategory.choices,
        default=FindingCategory.OBSERVATION,
        db_index=True,
    )
    description = models.TextField(_("Description"))
    recommendation = models.TextField(_("Recommendation"), blank=True)
    verified = models.BooleanField(_("Verified"), default=False)

    class Meta:
        verbose_name = _("Monitoring Finding")
        verbose_name_plural = _("Monitoring Findings")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.get_category_display()}: {self.description[:60]}"


class CorrectiveAction(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A tracked corrective or follow-up action for accountability."""

    reference_number = models.CharField(
        _("Action ID"), max_length=80, unique=True, db_index=True
    )
    title = models.CharField(_("Title"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    finding = models.ForeignKey(
        MonitoringFinding,
        on_delete=models.SET_NULL,
        related_name="corrective_actions",
        null=True,
        blank=True,
    )
    dqa = models.ForeignKey(
        "DataQualityAssessment",
        on_delete=models.SET_NULL,
        related_name="corrective_actions",
        null=True,
        blank=True,
    )
    complaint = models.ForeignKey(
        "Complaint",
        on_delete=models.SET_NULL,
        related_name="corrective_actions",
        null=True,
        blank=True,
    )
    feedback = models.ForeignKey(
        "Feedback",
        on_delete=models.SET_NULL,
        related_name="corrective_actions",
        null=True,
        blank=True,
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_corrective_actions",
        null=True,
        blank=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=CorrectiveActionStatus.choices,
        default=CorrectiveActionStatus.OPEN,
        db_index=True,
    )
    resolution = models.TextField(_("Resolution"), blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="closed_corrective_actions",
        null=True,
        blank=True,
    )
    closed_at = models.DateTimeField(_("Closed at"), null=True, blank=True)

    objects: ClassVar[models.Manager[CorrectiveAction]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Corrective Action")
        verbose_name_plural = _("Corrective Actions")
        ordering = ("due_date", "priority")

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title}"

    def clean(self) -> None:
        super().clean()
        if not any(
            [
                self.finding_id,
                self.dqa_id,
                self.complaint_id,
                self.feedback_id,
            ]
        ):
            raise ValidationError(
                _(
                    "A corrective action must link to a finding, DQA, complaint, "
                    "or feedback."
                )
            )


class Evaluation(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A baseline, midline, endline, or impact evaluation."""

    reference_number = models.CharField(
        _("Evaluation ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_evaluations",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_evaluations",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    evaluation_type = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="evaluations",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.EVALUATION_TYPE},
    )
    start_date = models.DateField(_("Start date"), default=timezone.localdate)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    methodology = models.TextField(_("Methodology"), blank=True)
    findings = models.TextField(_("Findings"), blank=True)
    conclusions = models.TextField(_("Conclusions"), blank=True)
    lead_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="lead_meal_evaluations",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=EvaluationStatus.choices,
        default=EvaluationStatus.PLANNED,
        db_index=True,
    )
    report_file = models.FileField(
        _("Evaluation report"),
        upload_to="meal/evaluations/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )

    objects: ClassVar[models.Manager[Evaluation]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Evaluation")
        verbose_name_plural = _("Evaluations")
        ordering = ("-start_date",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range

        validate_date_range(self.start_date, self.end_date)


class EvaluationRecommendation(MEALRecord):
    """A recommendation arising from an evaluation."""

    evaluation = models.ForeignKey(
        Evaluation,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    recommendation = models.TextField(_("Recommendation"))
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="evaluation_recommendations",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.LEARNING_CATEGORY},
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_evaluation_recommendations",
        null=True,
        blank=True,
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    adopted = models.BooleanField(_("Adopted"), default=False)

    class Meta:
        verbose_name = _("Evaluation Recommendation")
        verbose_name_plural = _("Evaluation Recommendations")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.recommendation[:60]


class DataQualityAssessment(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A structured data quality assessment across defined dimensions."""

    reference_number = models.CharField(
        _("DQA ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_dqas",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_dqas",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    assessment_date = models.DateField(_("Assessment date"), default=timezone.localdate)
    assessor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conducted_meal_dqas",
        null=True,
        blank=True,
    )
    scope = models.TextField(_("Scope"), blank=True)
    overall_score = models.PositiveIntegerField(_("Overall score (%)"), default=0)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DQAStatus.choices,
        default=DQAStatus.PLANNED,
        db_index=True,
    )
    report_file = models.FileField(
        _("DQA report"),
        upload_to="meal/dqa/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )

    objects: ClassVar[models.Manager[DataQualityAssessment]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Data Quality Assessment")
        verbose_name_plural = _("Data Quality Assessments")
        ordering = ("-assessment_date",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_percentage(self.overall_score)


class DQADimensionScore(MEALRecord):
    """Score for a single quality dimension within a DQA."""

    dqa = models.ForeignKey(
        DataQualityAssessment,
        on_delete=models.CASCADE,
        related_name="dimension_scores",
    )
    dimension = models.CharField(
        _("Dimension"),
        max_length=20,
        choices=DQADimension.choices,
        db_index=True,
    )
    score = models.PositiveIntegerField(_("Score (%)"))
    findings = models.TextField(_("Findings"), blank=True)

    class Meta:
        verbose_name = _("DQA Dimension Score")
        verbose_name_plural = _("DQA Dimension Scores")
        ordering = ("dqa", "dimension")
        constraints = [
            models.UniqueConstraint(
                fields=["dqa", "dimension"], name="meal_dqa_dimension_uniq"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_dimension_display()}: {self.score}%"

    def clean(self) -> None:
        super().clean()
        validate_percentage(self.score)


class Complaint(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A structured complaint with confidentiality controls."""

    reference_number = models.CharField(
        _("Complaint ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_complaints",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_complaints",
        null=True,
        blank=True,
    )
    beneficiary = models.ForeignKey(
        "beneficiaries.Beneficiary",
        on_delete=models.SET_NULL,
        related_name="meal_complaints",
        null=True,
        blank=True,
    )
    submission_date = models.DateField(_("Submission date"), default=timezone.localdate)
    source = models.CharField(_("Source"), max_length=160, blank=True)
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="complaints",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.COMPLAINT_CATEGORY},
    )
    channel = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="complaint_channels",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SUGGESTION_CHANNEL},
    )
    description = models.TextField(_("Description"))
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_meal_complaints",
        null=True,
        blank=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=25,
        choices=ComplaintStatus.choices,
        default=ComplaintStatus.RECEIVED,
        db_index=True,
    )
    is_confidential = models.BooleanField(_("Confidential"), default=False)
    investigation = models.TextField(_("Investigation"), blank=True)
    resolution = models.TextField(_("Resolution"), blank=True)
    response_date = models.DateField(_("Response date"), null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="closed_meal_complaints",
        null=True,
        blank=True,
    )
    closed_at = models.DateTimeField(_("Closed at"), null=True, blank=True)

    objects: ClassVar[models.Manager[Complaint]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Complaint")
        verbose_name_plural = _("Complaints")
        ordering = ("-submission_date",)

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.description[:60]}"


class Feedback(MEALRecord, SoftDeleteModel, ArchivableModel):
    """Structured beneficiary, community, or stakeholder feedback."""

    reference_number = models.CharField(
        _("Feedback ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_feedback",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_feedback",
        null=True,
        blank=True,
    )
    beneficiary = models.ForeignKey(
        "beneficiaries.Beneficiary",
        on_delete=models.SET_NULL,
        related_name="meal_feedback",
        null=True,
        blank=True,
    )
    submission_date = models.DateField(_("Submission date"), default=timezone.localdate)
    source = models.CharField(_("Source"), max_length=160, blank=True)
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="feedback_records",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FEEDBACK_CATEGORY},
    )
    channel = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="feedback_channels",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SUGGESTION_CHANNEL},
    )
    description = models.TextField(_("Description"))
    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_meal_feedback",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=FeedbackStatus.choices,
        default=FeedbackStatus.RECEIVED,
        db_index=True,
    )
    is_confidential = models.BooleanField(_("Confidential"), default=False)
    response = models.TextField(_("Response"), blank=True)
    response_date = models.DateField(_("Response date"), null=True, blank=True)
    satisfaction_rating = models.PositiveSmallIntegerField(
        _("Satisfaction rating (1-5)"), null=True, blank=True
    )

    objects: ClassVar[models.Manager[Feedback]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Feedback")
        verbose_name_plural = _("Feedback")
        ordering = ("-submission_date",)

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.description[:60]}"

    def clean(self) -> None:
        super().clean()
        if (
            self.satisfaction_rating is not None
            and not 1 <= self.satisfaction_rating <= 5
        ):
            raise ValidationError(
                {"satisfaction_rating": _("Rating must be between 1 and 5.")}
            )


class OutcomeHarvest(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A harvested outcome using the Outcome Harvesting methodology."""

    reference_number = models.CharField(
        _("Outcome harvest ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_outcome_harvests",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_outcome_harvests",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="outcome_harvests",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.OUTCOME_CATEGORY},
    )
    outcome_description = models.TextField(_("Outcome description"))
    evidence = models.TextField(_("Evidence"), blank=True)
    contributing_factors = models.TextField(_("Contributing factors"), blank=True)
    stakeholders = models.TextField(_("Responsible stakeholders"), blank=True)
    verification_method = models.TextField(_("Verification method"), blank=True)
    lessons_learned = models.TextField(_("Lessons learned"), blank=True)
    sustainability = models.TextField(_("Sustainability considerations"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OutcomeHarvestStatus.choices,
        default=OutcomeHarvestStatus.DRAFT,
        db_index=True,
    )

    objects: ClassVar[models.Manager[OutcomeHarvest]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Outcome Harvest")
        verbose_name_plural = _("Outcome Harvests")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class LearningLog(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A continuous organizational learning log entry."""

    reference_number = models.CharField(
        _("Learning ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_learning_logs",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_learning_logs",
        null=True,
        blank=True,
    )
    log_date = models.DateField(_("Log date"), default=timezone.localdate)
    source = models.CharField(_("Source"), max_length=160, blank=True)
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="learning_logs",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.LEARNING_CATEGORY},
    )
    description = models.TextField(_("Description"))
    recommendation = models.TextField(_("Recommendation"), blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_learning_logs",
        null=True,
        blank=True,
    )
    follow_up_actions = models.TextField(_("Follow-up actions"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=LearningLogStatus.choices,
        default=LearningLogStatus.OPEN,
        db_index=True,
    )

    objects: ClassVar[models.Manager[LearningLog]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Learning Log")
        verbose_name_plural = _("Learning Logs")
        ordering = ("-log_date",)

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.description[:60]}"


class BestPractice(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A validated best practice in the organizational Best Practices Register."""

    reference_number = models.CharField(
        _("Practice ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_best_practices",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_best_practices",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Practice title"), max_length=255)
    description = models.TextField(_("Description"))
    evidence = models.TextField(_("Evidence"), blank=True)
    results_achieved = models.TextField(_("Results achieved"), blank=True)
    replication_guidance = models.TextField(_("Replication guidance"), blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_best_practices",
        null=True,
        blank=True,
    )
    evidence_file = models.FileField(
        _("Supporting evidence"),
        upload_to="meal/best_practices/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BestPracticeStatus.choices,
        default=BestPracticeStatus.DRAFT,
        db_index=True,
    )

    objects: ClassVar[models.Manager[BestPractice]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Best Practice")
        verbose_name_plural = _("Best Practices")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class LessonLearned(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A structured organizational lesson learned."""

    reference_number = models.CharField(
        _("Lesson ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_lessons",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_lessons",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Lesson title"), max_length=255)
    category = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="meal_lesson_records",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.LESSON_CATEGORY},
    )
    context = models.TextField(_("Context"), blank=True)
    observation = models.TextField(_("Observation"))
    analysis = models.TextField(_("Analysis"), blank=True)
    recommendation = models.TextField(_("Recommendation"), blank=True)
    responsible_team = models.CharField(
        _("Responsible team"), max_length=160, blank=True
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=LessonStatus.choices,
        default=LessonStatus.DRAFT,
        db_index=True,
    )

    objects: ClassVar[models.Manager[LessonLearned]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Lesson Learned")
        verbose_name_plural = _("Lessons Learned")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class OrganizationalKPI(MEALRecord, IsActiveModel):
    """An organizational performance KPI for scorecards."""

    reference_number = models.CharField(
        _("KPI ID"), max_length=80, unique=True, db_index=True
    )
    code = models.SlugField(_("KPI code"), max_length=80, unique=True)
    name = models.CharField(_("Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True)
    formula = models.CharField(_("Formula"), max_length=255, blank=True)
    unit = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="organizational_kpis",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.INDICATOR_UNIT},
    )
    target_value = models.DecimalField(
        _("Target value"), max_digits=18, decimal_places=2, null=True, blank=True
    )
    frequency = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="kpi_frequencies",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.REPORTING_FREQUENCY},
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_organizational_kpis",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Organizational KPI")
        verbose_name_plural = _("Organizational KPIs")
        ordering = ("code",)

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class PerformanceScorecard(MEALRecord, SoftDeleteModel, ArchivableModel):
    """A published organizational performance scorecard."""

    reference_number = models.CharField(
        _("Scorecard ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_scorecards",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    period_label = models.CharField(_("Period label"), max_length=120)
    period_start = models.DateField(_("Period start"), null=True, blank=True)
    period_end = models.DateField(_("Period end"), null=True, blank=True)
    period_type = models.ForeignKey(
        MEALReferenceData,
        on_delete=models.PROTECT,
        related_name="scorecard_periods",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SCORECARD_PERIOD},
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ScorecardStatus.choices,
        default=ScorecardStatus.DRAFT,
        db_index=True,
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="published_scorecards",
        null=True,
        blank=True,
    )
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)

    objects: ClassVar[models.Manager[PerformanceScorecard]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Performance Scorecard")
        verbose_name_plural = _("Performance Scorecards")
        ordering = ("-period_end",)

    def __str__(self) -> str:
        return f"{self.title} ({self.period_label})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range

        validate_date_range(self.period_start, self.period_end)

    @property
    def average_score(self) -> Decimal:
        scores = [
            dimension.score
            for dimension in self.dimensions.all()
            if dimension.score is not None
        ]
        if not scores:
            return Decimal("0")
        total = sum(scores, Decimal("0"))
        return (total / Decimal(len(scores))).quantize(Decimal("0.1"))


class ScorecardDimension(MEALRecord):
    """A KPI row within a performance scorecard."""

    scorecard = models.ForeignKey(
        PerformanceScorecard,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )
    dimension = models.CharField(
        _("Dimension"),
        max_length=30,
        choices=constants.ScorecardDimension.choices,
        db_index=True,
    )
    label = models.CharField(_("Label"), max_length=255)
    target = models.DecimalField(
        _("Target"), max_digits=18, decimal_places=2, null=True, blank=True
    )
    actual = models.DecimalField(
        _("Actual"), max_digits=18, decimal_places=2, null=True, blank=True
    )
    score = models.PositiveIntegerField(_("Score (%)"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Scorecard Dimension")
        verbose_name_plural = _("Scorecard Dimensions")
        ordering = ("scorecard", "dimension")

    def __str__(self) -> str:
        return f"{self.get_dimension_display()}: {self.label}"

    def clean(self) -> None:
        super().clean()
        validate_percentage(self.score)


class MEALReport(MEALRecord, SoftDeleteModel, ArchivableModel):
    """An organizational MEAL report supporting approval and export."""

    reference_number = models.CharField(
        _("Report ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.CASCADE,
        related_name="meal_reports",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "programs.Project",
        on_delete=models.CASCADE,
        related_name="meal_reports",
        null=True,
        blank=True,
    )
    title = models.CharField(_("Title"), max_length=255)
    report_type = models.CharField(
        _("Report type"),
        max_length=40,
        choices=MEALReportType.choices,
        db_index=True,
    )
    period_start = models.DateField(_("Period start"), null=True, blank=True)
    period_end = models.DateField(_("Period end"), null=True, blank=True)
    content = models.TextField(_("Content"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
        db_index=True,
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="prepared_meal_reports",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_meal_reports",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    file = models.FileField(
        _("Report file"),
        upload_to="meal/reports/",
        storage=private_meal_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )

    objects: ClassVar[models.Manager[MEALReport]] = ActiveMEALManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("MEAL Report")
        verbose_name_plural = _("MEAL Reports")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        from apps.programs.validators import validate_date_range

        validate_date_range(self.period_start, self.period_end)


class MEALStatusHistory(MEALRecord):
    """Immutable workflow transition history for MEAL records."""

    entity_type = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    action = models.CharField(max_length=60, db_index=True)
    from_status = models.CharField(max_length=40, blank=True)
    to_status = models.CharField(max_length=40)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("MEAL Status History")
        verbose_name_plural = _("MEAL Status History")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["entity_type", "entity_id", "created_at"])]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs) -> None:
        model = cast(models.Model, self)
        if not model._state.adding:
            raise ValidationError(
                IMMUTABLE_MEAL_HISTORY_MESSAGE, code="immutable_meal_history"
            )
        models.Model.save(model, *args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_MEAL_HISTORY_MESSAGE, code="immutable_meal_history"
        )


class MEALAuditRecord(MEALRecord):
    """Immutable structured audit trail for significant MEAL events."""

    entity_type = models.CharField(max_length=80, db_index=True)
    entity_id = models.CharField(max_length=80, db_index=True)
    action = models.CharField(max_length=60, db_index=True)
    from_data = models.JSONField(default=dict, blank=True)
    to_data = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("MEAL Audit Record")
        verbose_name_plural = _("MEAL Audit Records")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["entity_type", "entity_id", "created_at"])]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}:{self.entity_id}"

    def save(self, *args, **kwargs) -> None:
        model = cast(models.Model, self)
        if not model._state.adding:
            raise ValidationError(
                IMMUTABLE_MEAL_HISTORY_MESSAGE, code="immutable_meal_audit"
            )
        models.Model.save(model, *args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_MEAL_HISTORY_MESSAGE, code="immutable_meal_audit"
        )
