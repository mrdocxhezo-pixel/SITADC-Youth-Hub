"""Normalized data model for the Phase 15 program and project registry."""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar, NoReturn, cast

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.organizations.models import OrganizationUnit
from apps.stakeholders.models import Stakeholder

from .constants import (
    DEFAULT_CURRENCY,
    ActivityStatus,
    BeneficiaryStatus,
    ChangeStatus,
    DeliverableStatus,
    DocumentStatus,
    EvaluationType,
    IssueStatus,
    LessonCategory,
    MilestoneStatus,
    PortfolioStatus,
    Priority,
    ProcurementStatus,
    ProgramStatus,
    ProgressStatus,
    ProjectStatus,
    ReferenceDataKind,
    ResourceType,
    RiskLevel,
    RiskStatus,
    TaskStatus,
    WorkPlanStatus,
)
from .managers import (
    IMMUTABLE_HISTORY_MESSAGE,
    ImmutableHistoryManager,
    ProgramManager,
    ProjectManager,
)
from .storage import private_program_storage
from .validators import (
    validate_date_range,
    validate_percentage,
    validate_positive_amount,
    validate_program_document,
)


class ProgramRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for program domain rows."""

    class Meta:
        abstract = True


class ImmutableHistoricalRecord:
    """Model-method protection for append-only historical rows."""

    def save(self, *args, **kwargs) -> None:
        model = cast(models.Model, self)
        if not model._state.adding:
            raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")
        models.Model.save(model, *args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(IMMUTABLE_HISTORY_MESSAGE, code="immutable_history")


class ProgramReferenceData(ProgramRecord):
    """Configurable taxonomy shared by program and project profiles."""

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
        verbose_name = _("Program Reference Data")
        verbose_name_plural = _("Program Reference Data")
        ordering = ("kind", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "code"], name="program_ref_kind_code_uniq"
            )
        ]
        indexes = [models.Index(fields=["kind", "active", "order"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.name}"


class ProgramPortfolio(ProgramRecord, ArchivableModel):
    """A strategic grouping of programs under one objective."""

    reference_number = models.CharField(
        _("Portfolio ID"), max_length=80, unique=True, db_index=True
    )
    name = models.CharField(_("Portfolio name"), max_length=220)
    strategic_objective = models.TextField(blank=True)
    description = models.TextField(blank=True)
    directorate = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="program_portfolios",
        null=True,
        blank=True,
    )
    portfolio_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_program_portfolios",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=PortfolioStatus.choices,
        default=PortfolioStatus.PLANNED,
        db_index=True,
    )
    budget_allocation = models.DecimalField(
        _("Budget allocation"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    funding_source = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="funded_portfolios",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FUNDING_SOURCE},
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)

    class Meta:
        verbose_name = _("Program Portfolio")
        verbose_name_plural = _("Program Portfolios")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        if self.funding_source_id and (
            self.funding_source is not None
            and self.funding_source.kind != ReferenceDataKind.FUNDING_SOURCE
        ):
            raise ValidationError({"funding_source": _("Invalid funding source kind.")})
        validate_positive_amount(self.budget_allocation)


class Program(ProgramRecord, SoftDeleteModel, ArchivableModel):
    """Authoritative profile for an organizational program."""

    objects: ClassVar[ProgramManager] = ProgramManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    reference_number = models.CharField(
        _("Program ID"), max_length=80, unique=True, db_index=True
    )
    title = models.CharField(_("Program title"), max_length=255)
    short_title = models.CharField(_("Short title"), max_length=120, blank=True)
    portfolio = models.ForeignKey(
        ProgramPortfolio,
        on_delete=models.SET_NULL,
        related_name="programs",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="categorized_programs",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CATEGORY},
    )
    description = models.TextField(blank=True)
    background = models.TextField(blank=True)
    justification = models.TextField(blank=True)
    strategic_objective = models.TextField(blank=True)
    vision = models.TextField(blank=True)
    mission = models.TextField(blank=True)
    pillars = models.ManyToManyField(
        ProgramReferenceData,
        related_name="pillar_programs",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.PILLAR},
    )
    sdgs = models.ManyToManyField(
        ProgramReferenceData,
        related_name="sdg_programs",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SDG},
    )
    expected_outcomes = models.TextField(blank=True)
    expected_outputs = models.TextField(blank=True)
    key_indicators = models.TextField(blank=True)
    geographic_coverage = models.TextField(blank=True)
    regions = models.JSONField(default=list, blank=True)
    districts = models.JSONField(default=list, blank=True)
    communities = models.JSONField(default=list, blank=True)
    target_beneficiaries = models.TextField(blank=True)
    target_beneficiary_count = models.PositiveIntegerField(
        _("Target beneficiary count"), null=True, blank=True
    )
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ProgramStatus.choices,
        default=ProgramStatus.DRAFT,
        db_index=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    program_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_programs",
        null=True,
        blank=True,
    )
    responsible_directorate = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="directorate_programs",
        null=True,
        blank=True,
    )
    budget_approved = models.DecimalField(
        _("Approved budget"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    budget_utilized = models.DecimalField(
        _("Utilized budget"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    funding_sources = models.ManyToManyField(
        ProgramReferenceData,
        related_name="funded_programs",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FUNDING_SOURCE},
    )
    assumptions = models.TextField(blank=True)
    dependencies = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_programs",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Program")
        verbose_name_plural = _("Programs")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["program_manager", "status"]),
            models.Index(fields=["start_date", "end_date"]),
            models.Index(fields=["responsible_directorate", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    @property
    def budget_remaining(self) -> Decimal:
        return self.budget_approved - self.budget_utilized

    @property
    def budget_utilization_percentage(self) -> Decimal:
        if not self.budget_approved:
            return Decimal("0.00")
        return (self.budget_utilized / self.budget_approved * Decimal("100")).quantize(
            Decimal("0.01")
        )

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        if self.category_id and (
            self.category is not None
            and self.category.kind != ReferenceDataKind.CATEGORY
        ):
            raise ValidationError({"category": _("Invalid program category kind.")})
        validate_positive_amount(self.budget_approved)
        validate_positive_amount(self.budget_utilized)
        if self.budget_utilized > self.budget_approved:
            raise ValidationError(
                {"budget_utilized": _("Utilized budget cannot exceed approved budget.")}
            )


class ProgramStatusHistory(ImmutableHistoricalRecord, ProgramRecord):
    """Append-only program lifecycle history."""

    program = models.ForeignKey(
        Program, on_delete=models.PROTECT, related_name="status_history"
    )
    from_status = models.CharField(max_length=30, choices=ProgramStatus.choices)
    to_status = models.CharField(max_length=30, choices=ProgramStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="program_status_changes",
        null=True,
        blank=True,
    )
    reason = models.TextField(blank=True)
    effective_date = models.DateTimeField(default=timezone.now, db_index=True)
    approval_reference = models.CharField(max_length=120, blank=True)
    context = models.JSONField(default=dict, blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["program", "created_at"])]

    def __str__(self) -> str:
        return f"{self.program}: {self.from_status} to {self.to_status}"


class ProgramTeamMember(ProgramRecord):
    """A role-based member of the program delivery team."""

    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="team_members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="program_team_memberships",
    )
    role_title = models.CharField(_("Role title"), max_length=160)
    responsibility = models.TextField(blank=True)
    start_date = models.DateField(default=timezone.localdate)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-is_active", "role_title")
        constraints = [
            models.UniqueConstraint(
                fields=["program", "user", "role_title"],
                condition=models.Q(is_active=True),
                name="program_active_team_member_uniq",
            )
        ]
        indexes = [models.Index(fields=["program", "is_active"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")


class ProgramStakeholderLink(ProgramRecord):
    """A stakeholder relationship (partner, donor, sponsor) on a program."""

    PROGRAM_LINK_KINDS = (
        ("PARTNER", _("Partner")),
        ("IMPLEMENTING", _("Implementing partner")),
        ("DONOR", _("Donor")),
        ("SPONSOR", _("Sponsor")),
        ("GOVERNMENT", _("Government")),
        ("COMMUNITY", _("Community stakeholder")),
        ("OTHER", _("Other")),
    )

    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="stakeholder_links"
    )
    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="program_links"
    )
    link_kind = models.CharField(
        _("Link kind"), max_length=30, choices=PROGRAM_LINK_KINDS, db_index=True
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("link_kind",)
        constraints = [
            models.UniqueConstraint(
                fields=["program", "stakeholder", "link_kind"],
                condition=models.Q(is_active=True),
                name="program_stakeholder_link_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.stakeholder} - {self.get_link_kind_display()}"


class ProgramBudget(ProgramRecord):
    """A period budget allocation for a program."""

    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="budgets"
    )
    period_label = models.CharField(_("Period label"), max_length=120)
    approved_amount = models.DecimalField(
        _("Approved amount"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    utilized_amount = models.DecimalField(
        _("Utilized amount"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    funding_source = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="program_budgets",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FUNDING_SOURCE},
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("-start_date",)
        indexes = [models.Index(fields=["program", "is_active"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        validate_positive_amount(self.approved_amount)
        validate_positive_amount(self.utilized_amount)
        if self.utilized_amount > self.approved_amount:
            raise ValidationError(
                {"utilized_amount": _("Utilized amount cannot exceed approved amount.")}
            )


class ProgramBudgetLineItem(ProgramRecord):
    """A categorized line item within a program budget."""

    budget = models.ForeignKey(
        ProgramBudget, on_delete=models.CASCADE, related_name="line_items"
    )
    category = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="budget_line_items",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.BUDGET_CATEGORY},
    )
    description = models.CharField(max_length=255)
    planned_amount = models.DecimalField(
        _("Planned amount"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    actual_amount = models.DecimalField(
        _("Actual amount"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("budget", "description")

    def clean(self) -> None:
        super().clean()
        validate_positive_amount(self.planned_amount)
        validate_positive_amount(self.actual_amount)


class ProgramRisk(ProgramRecord):
    """A program risk register entry."""

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="risks")
    reference_number = models.CharField(
        _("Risk ID"), max_length=80, unique=True, db_index=True
    )
    category = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="program_risks",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.RISK_CATEGORY},
    )
    title = models.CharField(max_length=220)
    description = models.TextField()
    likelihood = models.PositiveSmallIntegerField(
        _("Likelihood"),
        choices=RiskLevel.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=RiskLevel.MODERATE,
    )
    impact = models.PositiveSmallIntegerField(
        _("Impact"),
        choices=RiskLevel.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=RiskLevel.MODERATE,
    )
    risk_score = models.PositiveSmallIntegerField(default=1, editable=False)
    mitigation_measures = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="program_risks",
        null=True,
        blank=True,
    )
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=RiskStatus.choices,
        default=RiskStatus.OPEN,
        db_index=True,
    )

    class Meta:
        ordering = ("-risk_score", "next_review_date")
        indexes = [models.Index(fields=["program", "status", "risk_score"])]

    def clean(self) -> None:
        super().clean()
        if self.category_id and (
            self.category is not None
            and self.category.kind != ReferenceDataKind.RISK_CATEGORY
        ):
            raise ValidationError({"category": _("Invalid risk category kind.")})
        self.risk_score = self.likelihood * self.impact

    def save(self, *args, **kwargs) -> None:
        self.risk_score = self.likelihood * self.impact
        super().save(*args, **kwargs)


class ProgramIndicator(ProgramRecord):
    """A performance indicator supporting MEAL reporting."""

    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="indicators"
    )
    code = models.CharField(_("Indicator code"), max_length=80)
    description = models.TextField()
    indicator_type = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="program_indicators",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.INDICATOR_TYPE},
    )
    baseline = models.CharField(max_length=120, blank=True)
    target = models.CharField(max_length=120, blank=True)
    actual = models.CharField(max_length=120, blank=True)
    unit = models.CharField(max_length=80, blank=True)
    frequency = models.CharField(max_length=80, blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="program_indicators",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("code",)
        constraints = [
            models.UniqueConstraint(
                fields=["program", "code"], name="program_indicator_code_uniq"
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.indicator_type_id and (
            self.indicator_type is not None
            and self.indicator_type.kind != ReferenceDataKind.INDICATOR_TYPE
        ):
            raise ValidationError({"indicator_type": _("Invalid indicator type.")})


class ProgramEvaluation(ProgramRecord):
    """Baseline, midline, endline, outcome, or impact evaluation record."""

    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="evaluations"
    )
    evaluation_type = models.CharField(
        _("Evaluation type"),
        max_length=20,
        choices=EvaluationType.choices,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    evaluation_date = models.DateField(default=timezone.localdate, db_index=True)
    methodology = models.TextField(blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    success_stories = models.TextField(blank=True)
    best_practices = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="conducted_program_evaluations",
        null=True,
        blank=True,
    )
    report_file = models.FileField(
        _("Evaluation report"),
        upload_to="programs/evaluations/",
        storage=private_program_storage,
        validators=[validate_program_document],
        null=True,
        blank=True,
    )
    is_published = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("-evaluation_date",)
        indexes = [models.Index(fields=["program", "evaluation_type"])]

    def clean(self) -> None:
        super().clean()
        if self.evaluation_date > timezone.localdate():
            raise ValidationError(
                {"evaluation_date": _("Evaluation date cannot be future.")}
            )


class WorkPlan(ProgramRecord, ArchivableModel):
    """A time-bound work plan for a program or project."""

    reference_number = models.CharField(
        _("Work plan ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="work_plans",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        related_name="work_plans",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    reporting_period = models.CharField(max_length=120)
    objectives = models.TextField(blank=True)
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=WorkPlanStatus.choices,
        default=WorkPlanStatus.DRAFT,
        db_index=True,
    )
    budget_allocation = models.DecimalField(
        _("Budget allocation"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_work_plans",
        null=True,
        blank=True,
    )
    version_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ("-start_date",)
        indexes = [models.Index(fields=["program", "status"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("A work plan requires a program or a project."))
        validate_positive_amount(self.budget_allocation)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class Project(ProgramRecord, SoftDeleteModel, ArchivableModel):
    """Authoritative profile for a project under a program."""

    objects: ClassVar[ProjectManager] = ProjectManager()  # type: ignore[assignment]
    all_objects: ClassVar[models.Manager] = models.Manager()

    reference_number = models.CharField(
        _("Project ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        Program, on_delete=models.PROTECT, related_name="projects"
    )
    title = models.CharField(_("Project title"), max_length=255)
    category = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="categorized_projects",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.PROJECT_CATEGORY},
    )
    description = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    expected_outputs = models.TextField(blank=True)
    expected_outcomes = models.TextField(blank=True)
    target_beneficiaries = models.TextField(blank=True)
    target_beneficiary_count = models.PositiveIntegerField(
        _("Target beneficiary count"), null=True, blank=True
    )
    geographic_coverage = models.TextField(blank=True)
    regions = models.JSONField(default=list, blank=True)
    districts = models.JSONField(default=list, blank=True)
    communities = models.JSONField(default=list, blank=True)
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ProjectStatus.choices,
        default=ProjectStatus.CONCEPT,
        db_index=True,
    )
    project_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="managed_projects",
        null=True,
        blank=True,
    )
    budget_approved = models.DecimalField(
        _("Approved budget"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    budget_utilized = models.DecimalField(
        _("Utilized budget"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    funding_source = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="funded_projects",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FUNDING_SOURCE},
    )
    risk_level = models.PositiveSmallIntegerField(
        _("Risk level"),
        choices=RiskLevel.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=RiskLevel.LOW,
    )
    assumptions = models.TextField(blank=True)
    dependencies = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_projects",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["program", "status"]),
            models.Index(fields=["project_manager", "status"]),
            models.Index(fields=["start_date", "end_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    @property
    def budget_remaining(self) -> Decimal:
        return self.budget_approved - self.budget_utilized

    @property
    def budget_utilization_percentage(self) -> Decimal:
        if not self.budget_approved:
            return Decimal("0.00")
        return (self.budget_utilized / self.budget_approved * Decimal("100")).quantize(
            Decimal("0.01")
        )

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        if self.category_id and (
            self.category is not None
            and self.category.kind != ReferenceDataKind.PROJECT_CATEGORY
        ):
            raise ValidationError({"category": _("Invalid project category kind.")})
        if self.funding_source_id and (
            self.funding_source is not None
            and self.funding_source.kind != ReferenceDataKind.FUNDING_SOURCE
        ):
            raise ValidationError({"funding_source": _("Invalid funding source kind.")})
        validate_positive_amount(self.budget_approved)
        validate_positive_amount(self.budget_utilized)
        if self.budget_utilized > self.budget_approved:
            raise ValidationError(
                {"budget_utilized": _("Utilized budget cannot exceed approved budget.")}
            )
        if self.start_date and self.program_id and self.program is not None:
            program = self.program
            if program.start_date and self.start_date < program.start_date:
                raise ValidationError(
                    {"start_date": _("Project cannot start before its program.")}
                )
            if program.end_date and self.end_date and self.end_date > program.end_date:
                raise ValidationError(
                    {"end_date": _("Project cannot end after its program.")}
                )


class ProjectStatusHistory(ImmutableHistoricalRecord, ProgramRecord):
    """Append-only project lifecycle history."""

    project = models.ForeignKey(
        Project, on_delete=models.PROTECT, related_name="status_history"
    )
    from_status = models.CharField(max_length=30, choices=ProjectStatus.choices)
    to_status = models.CharField(max_length=30, choices=ProjectStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="project_status_changes",
        null=True,
        blank=True,
    )
    reason = models.TextField(blank=True)
    effective_date = models.DateTimeField(default=timezone.now, db_index=True)
    approval_reference = models.CharField(max_length=120, blank=True)
    context = models.JSONField(default=dict, blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["project", "created_at"])]

    def __str__(self) -> str:
        return f"{self.project}: {self.from_status} to {self.to_status}"


class Activity(ProgramRecord):
    """A measurable activity within a work plan."""

    reference_number = models.CharField(
        _("Activity ID"), max_length=80, unique=True, db_index=True
    )
    work_plan = models.ForeignKey(
        WorkPlan, on_delete=models.CASCADE, related_name="activities"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_program_activities",
        null=True,
        blank=True,
    )
    location = models.CharField(max_length=180, blank=True)
    planned_date = models.DateField(db_index=True)
    actual_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ActivityStatus.choices,
        default=ActivityStatus.PLANNED,
        db_index=True,
    )
    expected_output = models.TextField(blank=True)
    completion_percentage = models.DecimalField(
        _("Completion percentage"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    budget_allocated = models.DecimalField(
        _("Budget allocated"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )
    budget_spent = models.DecimalField(
        _("Budget spent"), max_digits=18, decimal_places=2, default=Decimal("0.00")
    )

    class Meta:
        ordering = ("planned_date",)
        indexes = [models.Index(fields=["work_plan", "status", "planned_date"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.planned_date, self.actual_date, end_field="actual_date"
        )
        validate_positive_amount(self.budget_allocated)
        validate_positive_amount(self.budget_spent)

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class Task(ProgramRecord):
    """A task belonging to an activity."""

    reference_number = models.CharField(
        _("Task ID"), max_length=80, unique=True, db_index=True
    )
    activity = models.ForeignKey(
        Activity, on_delete=models.CASCADE, related_name="tasks"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_program_tasks",
        null=True,
        blank=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    due_date = models.DateField(null=True, blank=True, db_index=True)
    estimated_effort_hours = models.DecimalField(
        _("Estimated effort (hours)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
    )
    completion_percentage = models.DecimalField(
        _("Completion percentage"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        db_index=True,
    )
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("-priority", "due_date")

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"


class Milestone(ProgramRecord):
    """A milestone against a project timeline."""

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="milestones"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    target_date = models.DateField(db_index=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.PLANNED,
        db_index=True,
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_milestones",
        null=True,
        blank=True,
    )
    deliverables = models.TextField(blank=True)
    approval_status = models.CharField(max_length=20, default="PENDING", db_index=True)
    evidence_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("target_date",)
        indexes = [models.Index(fields=["project", "status", "target_date"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.target_date, self.completion_date, end_field="completion_date"
        )


class Deliverable(ProgramRecord):
    """An expected deliverable for a project or activity."""

    reference_number = models.CharField(
        _("Deliverable ID"), max_length=80, unique=True, db_index=True
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="deliverables"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    deliverable_type = models.CharField(max_length=120, blank=True)
    due_date = models.DateField(null=True, blank=True, db_index=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DeliverableStatus.choices,
        default=DeliverableStatus.PENDING,
        db_index=True,
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_deliverables",
        null=True,
        blank=True,
    )
    approval_notes = models.TextField(blank=True)
    evidence_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("due_date",)
        indexes = [models.Index(fields=["project", "status", "due_date"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.due_date, self.completion_date, end_field="completion_date"
        )


class Issue(ProgramRecord):
    """An operational issue raised during implementation."""

    reference_number = models.CharField(
        _("Issue ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        Program, on_delete=models.CASCADE, related_name="issues", null=True, blank=True
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="issues", null=True, blank=True
    )
    title = models.CharField(max_length=220)
    description = models.TextField()
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
        db_index=True,
    )
    date_identified = models.DateField(default=timezone.localdate, db_index=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_program_issues",
        null=True,
        blank=True,
    )
    corrective_actions = models.TextField(blank=True)
    target_resolution_date = models.DateField(null=True, blank=True)
    resolved_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=IssueStatus.choices,
        default=IssueStatus.OPEN,
        db_index=True,
    )
    evidence_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-priority", "date_identified")
        indexes = [models.Index(fields=["program", "status", "priority"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("An issue requires a program or a project."))
        validate_date_range(
            self.date_identified, self.resolved_date, end_field="resolved_date"
        )


class ChangeRequest(ProgramRecord):
    """A controlled change request affecting a program or project."""

    reference_number = models.CharField(
        _("Change reference"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="change_requests",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="change_requests",
        null=True,
        blank=True,
    )
    requestor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="submitted_change_requests",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=220)
    reason_for_change = models.TextField()
    scope_affected = models.TextField(blank=True)
    budget_impact = models.CharField(max_length=180, blank=True)
    timeline_impact = models.CharField(max_length=180, blank=True)
    risk_assessment = models.TextField(blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ChangeStatus.choices,
        default=ChangeStatus.DRAFT,
        db_index=True,
    )
    decision_notes = models.TextField(blank=True)
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="decided_change_requests",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["program", "status"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(
                _("A change request requires a program or a project.")
            )


class EvidenceRecord(ProgramRecord):
    """An evidence file attached to a program or project."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="evidence",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="evidence",
        null=True,
        blank=True,
    )
    activity = models.ForeignKey(
        Activity,
        on_delete=models.SET_NULL,
        related_name="evidence",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    evidence_type = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="evidence_records",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.EVIDENCE_TYPE},
    )
    file = models.FileField(
        _("Evidence file"),
        upload_to="programs/evidence/",
        storage=private_program_storage,
        validators=[validate_program_document],
    )
    captured_at = models.DateTimeField(null=True, blank=True)
    gps_coordinates = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["program", "is_verified"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("Evidence requires a program or a project."))
        if self.evidence_type_id and (
            self.evidence_type is not None
            and self.evidence_type.kind != ReferenceDataKind.EVIDENCE_TYPE
        ):
            raise ValidationError({"evidence_type": _("Invalid evidence type.")})


class BeneficiaryRecord(ProgramRecord):
    """A beneficiary enrolled in a program or project."""

    reference_number = models.CharField(
        _("Beneficiary ID"), max_length=80, unique=True, db_index=True
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="beneficiaries",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="beneficiaries",
        null=True,
        blank=True,
    )
    name = models.CharField(_("Name or group"), max_length=220)
    category = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="beneficiaries",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.BENEFICIARY_CATEGORY},
    )
    age = models.PositiveIntegerField(_("Age"), null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=180, blank=True)
    vulnerability_status = models.CharField(max_length=120, blank=True)
    disability_included = models.BooleanField(default=False)
    services_received = models.TextField(blank=True)
    enrollment_date = models.DateField(default=timezone.localdate)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BeneficiaryStatus.choices,
        default=BeneficiaryStatus.ENROLLED,
        db_index=True,
    )

    class Meta:
        ordering = ("name",)
        indexes = [models.Index(fields=["program", "status"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("A beneficiary requires a program or a project."))
        if self.category_id and (
            self.category is not None
            and self.category.kind != ReferenceDataKind.BENEFICIARY_CATEGORY
        ):
            raise ValidationError({"category": _("Invalid beneficiary category.")})
        validate_date_range(
            self.enrollment_date, self.completion_date, end_field="completion_date"
        )


class ProgressUpdate(ProgramRecord):
    """A periodic progress update on a program or project."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="progress_updates",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="progress_updates",
        null=True,
        blank=True,
    )
    period_label = models.CharField(max_length=120)
    overall_completion = models.DecimalField(
        _("Overall completion"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    budget_utilization = models.DecimalField(
        _("Budget utilization"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ProgressStatus.choices,
        default=ProgressStatus.ON_TRACK,
        db_index=True,
    )
    summary = models.TextField(blank=True)
    challenges = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_progress_updates",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["program", "period_label"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(
                _("A progress update requires a program or a project.")
            )


class ProgramDocument(ProgramRecord):
    """A protected program or project document."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="documents",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    document_type = models.ForeignKey(
        ProgramReferenceData,
        on_delete=models.PROTECT,
        related_name="program_documents",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.DOCUMENT_TYPE},
    )
    file = models.FileField(
        _("Document"),
        upload_to="programs/documents/",
        storage=private_program_storage,
        validators=[validate_program_document],
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.CURRENT,
        db_index=True,
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("title",)
        indexes = [models.Index(fields=["program", "status"])]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(_("A document requires a program or a project."))
        if self.document_type_id and (
            self.document_type is not None
            and self.document_type.kind != ReferenceDataKind.DOCUMENT_TYPE
        ):
            raise ValidationError({"document_type": _("Invalid document type.")})

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            _("Program documents must be archived, not deleted."),
            code="protected_program_document",
        )


class ResourceAllocation(ProgramRecord):
    """A resource allocated to a program or project."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="resource_allocations",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="resource_allocations",
        null=True,
        blank=True,
    )
    reference_number = models.CharField(
        _("Allocation ID"), max_length=80, unique=True, db_index=True
    )
    resource_type = models.CharField(
        _("Resource type"),
        max_length=30,
        choices=ResourceType.choices,
        default=ResourceType.HUMAN,
        db_index=True,
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(
        _("Quantity"),
        max_digits=12,
        decimal_places=2,
        default=Decimal("1.00"),
    )
    unit = models.CharField(_("Unit"), max_length=40, blank=True)
    estimated_cost = models.DecimalField(
        _("Estimated cost"),
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    supplier_name = models.CharField(max_length=220, blank=True)
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True, db_index=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["program", "resource_type"]),
            models.Index(fields=["project", "resource_type"]),
        ]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(
                _("A resource allocation requires a program or a project.")
            )
        if self.program and self.project:
            raise ValidationError(
                _("A resource allocation belongs to a program or a project, not both.")
            )
        validate_date_range(self.start_date, self.end_date, end_field="end_date")
        validate_positive_amount(self.estimated_cost)


class ProcurementRequest(ProgramRecord):
    """A procurement request raised against a program or project budget."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="procurement_requests",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="procurement_requests",
        null=True,
        blank=True,
    )
    reference_number = models.CharField(
        _("Procurement reference"), max_length=80, unique=True, db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    items = models.TextField(_("Requested items"))
    quantity = models.DecimalField(
        _("Quantity"), max_digits=12, decimal_places=2, default=Decimal("1.00")
    )
    estimated_cost = models.DecimalField(
        _("Estimated cost"),
        max_digits=18,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    justification = models.TextField(blank=True)
    supplier_name = models.CharField(max_length=220, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ProcurementStatus.choices,
        default=ProcurementStatus.DRAFT,
        db_index=True,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="requested_procurement",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_procurement",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    delivery_status = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["program", "status"]),
            models.Index(fields=["project", "status"]),
        ]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(
                _("A procurement request requires a program or a project.")
            )
        if self.program and self.project:
            raise ValidationError(
                _("A procurement request belongs to a program or a project, not both.")
            )
        validate_positive_amount(self.estimated_cost)


class LessonsLearned(ProgramRecord):
    """An organizational learning record attached to a program or project."""

    program = models.ForeignKey(
        Program,
        on_delete=models.CASCADE,
        related_name="lessons_learned",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="lessons_learned",
        null=True,
        blank=True,
    )
    reference_number = models.CharField(
        _("Lesson ID"), max_length=80, unique=True, db_index=True
    )
    title = models.CharField(max_length=255)
    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=LessonCategory.choices,
        default=LessonCategory.SUCCESS,
        db_index=True,
    )
    summary = models.TextField()
    context = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="recorded_lessons",
        null=True,
        blank=True,
    )
    recorded_at = models.DateField(default=timezone.localdate, db_index=True)

    class Meta:
        ordering = ("-recorded_at",)
        indexes = [
            models.Index(fields=["program", "category"]),
            models.Index(fields=["project", "category"]),
        ]

    def clean(self) -> None:
        super().clean()
        if self.program_id is None and self.project_id is None:
            raise ValidationError(
                _("A lessons learned record requires a program or a project.")
            )
        if self.program and self.project:
            raise ValidationError(
                _(
                    "A lessons learned record belongs to a program or a "
                    "project, not both."
                )
            )
