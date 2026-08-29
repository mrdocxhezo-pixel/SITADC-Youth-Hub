"""Normalized data model for the Phase 14 stakeholder registry."""

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
from apps.leadership.models import LeadershipProfile
from apps.organizations.models import OrganizationUnit

from .constants import (
    DEFAULT_CURRENCY,
    AccessLevel,
    ActionPriority,
    ActionStatus,
    AgreementStatus,
    AssessmentClassification,
    CommitmentStatus,
    CommunicationChannel,
    CommunicationDirection,
    ConfidentialityLevel,
    ConflictStatus,
    ContributionStatus,
    DocumentStatus,
    DueDiligenceStatus,
    DuplicateReviewStatus,
    EngagementStatus,
    EngagementType,
    NoteStatus,
    PlanStatus,
    ReferenceDataKind,
    RenewalStatus,
    ReviewStatus,
    RiskLevel,
    RiskStatus,
    StakeholderEntityType,
    StakeholderStatus,
)
from .managers import (
    FINALIZED_NOTE_VERSION_MESSAGE,
    IMMUTABLE_HISTORY_MESSAGE,
    ImmutableHistoryManager,
    NoteVersionManager,
    StakeholderManager,
)
from .storage import private_stakeholder_storage
from .validators import (
    validate_date_range,
    validate_percentage,
    validate_positive_weight,
    validate_stakeholder_document,
    validate_stakeholder_image,
)


class StakeholderRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
):
    """Common actor and timestamp metadata for stakeholder domain rows."""

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


class StakeholderReferenceData(StakeholderRecord):
    """Configurable taxonomy shared by stakeholder profile fields."""

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
        verbose_name = _("Stakeholder Reference Data")
        verbose_name_plural = _("Stakeholder Reference Data")
        ordering = ("kind", "order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["kind", "code"], name="stakeholder_ref_kind_code_uniq"
            )
        ]
        indexes = [models.Index(fields=["kind", "active", "order"])]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.name}"


class Stakeholder(
    StakeholderRecord,
    SoftDeleteModel,
    ArchivableModel,
):
    """Authoritative profile for any partner, donor, sponsor, or stakeholder."""

    reference_number = models.CharField(
        _("Stakeholder ID"), max_length=80, unique=True, db_index=True
    )
    entity_type = models.CharField(
        _("Entity type"),
        max_length=20,
        choices=StakeholderEntityType.choices,
        default=StakeholderEntityType.ORGANIZATION,
        db_index=True,
    )
    legal_name = models.CharField(_("Legal or full name"), max_length=255)
    trading_name = models.CharField(
        _("Trading or commonly used name"), max_length=255, blank=True
    )
    display_name = models.CharField(_("Display name"), max_length=255, blank=True)
    acronym = models.CharField(_("Acronym"), max_length=40, blank=True)
    former_names = models.TextField(_("Former names"), blank=True)
    logo = models.ImageField(
        _("Logo or image"),
        upload_to="stakeholders/profiles/",
        storage=private_stakeholder_storage,
        validators=[validate_stakeholder_image],
        null=True,
        blank=True,
    )
    description = models.TextField(_("Description"), blank=True)
    vision = models.TextField(_("Vision"), blank=True)
    mission = models.TextField(_("Mission"), blank=True)
    core_objectives = models.TextField(_("Core objectives"), blank=True)
    areas_of_expertise = models.TextField(_("Areas of expertise"), blank=True)
    primary_areas_of_work = models.TextField(_("Primary areas of work"), blank=True)
    areas_of_interest = models.TextField(_("Areas of interest"), blank=True)
    potential_collaboration_areas = models.TextField(
        _("Potential collaboration areas"), blank=True
    )

    categories = models.ManyToManyField(
        StakeholderReferenceData,
        related_name="category_stakeholders",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CATEGORY},
    )
    relationship_type = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="typed_stakeholders",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.TYPE},
    )
    classification = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="classified_stakeholders",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.CLASSIFICATION},
    )
    ownership_type = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="ownership_stakeholders",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.OWNERSHIP_TYPE},
    )
    priority = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="priority_stakeholders",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.PRIORITY},
    )
    relationship_level = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="relationship_level_stakeholders",
        null=True,
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.RELATIONSHIP_LEVEL},
    )
    sectors = models.ManyToManyField(
        StakeholderReferenceData,
        related_name="sector_stakeholders",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SECTOR},
    )
    focus_areas = models.ManyToManyField(
        StakeholderReferenceData,
        related_name="focus_area_stakeholders",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.FOCUS_AREA},
    )
    sdgs = models.ManyToManyField(
        StakeholderReferenceData,
        related_name="sdg_stakeholders",
        blank=True,
        limit_choices_to={"kind": ReferenceDataKind.SDG},
    )

    registration_number = models.CharField(
        _("Registration number"), max_length=120, blank=True, db_index=True
    )
    tax_identifier = models.CharField(_("Tax identifier"), max_length=120, blank=True)
    registration_authority = models.CharField(
        _("Registration authority"), max_length=180, blank=True
    )
    date_established = models.DateField(_("Date established"), null=True, blank=True)
    country_of_registration = models.CharField(
        _("Country of registration"), max_length=100, blank=True
    )

    physical_address = models.TextField(_("Physical address"), blank=True)
    postal_address = models.TextField(_("Postal address"), blank=True)
    country = models.CharField(_("Country"), max_length=100, blank=True)
    province_or_region = models.CharField(
        _("Province or region"), max_length=120, blank=True, db_index=True
    )
    district = models.CharField(
        _("District"), max_length=120, blank=True, db_index=True
    )
    community = models.CharField(
        _("Community"), max_length=120, blank=True, db_index=True
    )
    geographic_coverage = models.TextField(_("Geographic coverage"), blank=True)
    province_location = models.ForeignKey(
        "locations.Province",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stakeholder_profiles",
        verbose_name=_("Province"),
        db_index=True,
    )
    district_location = models.ForeignKey(
        "locations.District",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stakeholder_profiles",
        verbose_name=_("District"),
        db_index=True,
    )
    ward_location = models.ForeignKey(
        "locations.Ward",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stakeholder_profiles",
        verbose_name=_("Ward / Community"),
        db_index=True,
    )
    gps_coordinates = models.CharField(
        _("GPS coordinates"),
        max_length=80,
        blank=True,
        help_text=_("Record only where operationally necessary and authorized."),
    )
    website = models.URLField(_("Website"), blank=True)
    general_email = models.EmailField(_("General email"), blank=True)
    general_phone = models.CharField(_("General phone"), max_length=40, blank=True)
    alternative_phone = models.CharField(
        _("Alternative phone"), max_length=40, blank=True
    )
    social_media = models.JSONField(_("Social media"), default=dict, blank=True)

    identification_source = models.CharField(
        _("Identification source"), max_length=160, blank=True
    )
    referred_by = models.CharField(_("Referred by"), max_length=180, blank=True)
    program_references = models.TextField(
        _("Deferred program references"),
        blank=True,
        help_text=_("Program names or external references; no Phase 15 foreign key."),
    )
    project_references = models.TextField(
        _("Deferred project references"),
        blank=True,
        help_text=_("Project names or external references; no Phase 16 foreign key."),
    )
    responsibilities = models.TextField(_("Roles and responsibilities"), blank=True)
    relationship_start_date = models.DateField(
        _("Relationship start date"), null=True, blank=True
    )
    relationship_end_date = models.DateField(
        _("Relationship end date"), null=True, blank=True
    )
    last_engagement_date = models.DateField(null=True, blank=True, db_index=True)
    next_engagement_date = models.DateField(null=True, blank=True, db_index=True)
    key_achievements = models.TextField(_("Key achievements"), blank=True)
    relationship_challenges = models.TextField(_("Relationship challenges"), blank=True)

    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="stakeholders",
        null=True,
        blank=True,
    )
    responsible_directorate = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="directorate_stakeholders",
        null=True,
        blank=True,
    )
    primary_responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="primary_stakeholder_responsibilities",
        null=True,
        blank=True,
    )
    responsible_leadership = models.ForeignKey(
        LeadershipProfile,
        on_delete=models.SET_NULL,
        related_name="owned_stakeholder_relationships",
        null=True,
        blank=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=StakeholderStatus.choices,
        default=StakeholderStatus.PROSPECT,
        db_index=True,
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
        db_index=True,
    )
    verified_at = models.DateTimeField(_("Verified at"), null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_stakeholders",
        null=True,
        blank=True,
    )
    consent_recorded = models.BooleanField(_("Consent recorded"), default=False)
    consent_recorded_at = models.DateTimeField(
        _("Consent recorded at"), null=True, blank=True
    )
    retention_until = models.DateField(_("Retain until"), null=True, blank=True)
    specialization_data = models.JSONField(
        _("Specialized relationship details"),
        default=dict,
        blank=True,
        help_text=_(
            "Structured donor, sponsor, partner, government, community, or "
            "service-provider details."
        ),
    )

    objects: ClassVar[StakeholderManager] = StakeholderManager()
    all_objects: ClassVar[models.Manager] = models.Manager()

    class Meta:
        verbose_name = _("Stakeholder")
        verbose_name_plural = _("Stakeholders")
        ordering = ("legal_name",)
        indexes = [
            models.Index(fields=["status", "confidentiality"]),
            models.Index(fields=["province_or_region", "district"]),
            models.Index(fields=["primary_responsible_officer", "status"]),
            models.Index(fields=["created_by", "status"]),
            models.Index(fields=["legal_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.display_name or self.legal_name} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.relationship_start_date,
            self.relationship_end_date,
            end_field="relationship_end_date",
        )
        if self.date_established and self.date_established > timezone.localdate():
            raise ValidationError(
                {"date_established": _("Date established cannot be in the future.")}
            )
        for field_name, expected_kind in (
            ("relationship_type", ReferenceDataKind.TYPE),
            ("classification", ReferenceDataKind.CLASSIFICATION),
            ("ownership_type", ReferenceDataKind.OWNERSHIP_TYPE),
            ("priority", ReferenceDataKind.PRIORITY),
            ("relationship_level", ReferenceDataKind.RELATIONSHIP_LEVEL),
        ):
            value = getattr(self, field_name, None)
            if value and value.kind != expected_kind:
                raise ValidationError(
                    {field_name: _("Selected reference data has the wrong kind.")}
                )
        if self.status == StakeholderStatus.ACTIVE and not (
            self.verified_at and self.verified_by_id
        ):
            raise ValidationError(
                {
                    "status": _(
                        "Verified or active stakeholders require verification metadata."
                    )
                }
            )


class StakeholderStatusHistory(ImmutableHistoricalRecord, StakeholderRecord):
    """Append-only stakeholder lifecycle history."""

    stakeholder = models.ForeignKey(
        Stakeholder,
        on_delete=models.PROTECT,
        related_name="status_history",
    )
    from_status = models.CharField(max_length=30, choices=StakeholderStatus.choices)
    to_status = models.CharField(max_length=30, choices=StakeholderStatus.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_status_changes",
        null=True,
        blank=True,
    )
    reason = models.TextField(blank=True)
    effective_date = models.DateTimeField(default=timezone.now, db_index=True)
    approval_reference = models.CharField(max_length=120, blank=True)
    supporting_document = models.FileField(
        upload_to="stakeholders/status-history/",
        storage=private_stakeholder_storage,
        validators=[validate_stakeholder_document],
        null=True,
        blank=True,
    )
    audit_reference = models.CharField(max_length=120, blank=True)
    context = models.JSONField(default=dict, blank=True)

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["stakeholder", "created_at"])]

    def __str__(self) -> str:
        return f"{self.stakeholder}: {self.from_status} to {self.to_status}"


class StakeholderContact(StakeholderRecord):
    """Private, historical contact person associated with a stakeholder."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="contacts"
    )
    full_name = models.CharField(max_length=180)
    title = models.CharField(max_length=80, blank=True)
    designation = models.CharField(max_length=160, blank=True)
    department = models.CharField(max_length=160, blank=True)
    email = models.EmailField(blank=True)
    phone_primary = models.CharField(max_length=40, blank=True)
    phone_secondary = models.CharField(max_length=40, blank=True)
    whatsapp_number = models.CharField(max_length=40, blank=True)
    preferred_communication = models.CharField(max_length=60, blank=True)
    availability = models.CharField(max_length=160, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    is_decision_maker = models.BooleanField(default=False)
    is_technical_contact = models.BooleanField(default=False)
    is_finance_contact = models.BooleanField(default=False)
    is_safeguarding_contact = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateField(default=timezone.localdate)
    valid_to = models.DateField(null=True, blank=True)
    consent_recorded = models.BooleanField(default=False)
    communication_consent = models.BooleanField(default=False)
    private_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-is_primary", "full_name")
        constraints = [
            models.UniqueConstraint(
                fields=["stakeholder"],
                condition=models.Q(is_primary=True, is_active=True),
                name="stakeholder_one_active_primary_contact",
            )
        ]
        indexes = [models.Index(fields=["stakeholder", "is_active", "is_primary"])]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.stakeholder}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.valid_from, self.valid_to, end_field="valid_to")
        if not (self.email or self.phone_primary or self.phone_secondary):
            raise ValidationError(
                _("A contact requires an email address or phone number.")
            )
        if self.is_primary and not self.is_active:
            raise ValidationError(
                {"is_primary": _("A primary contact must be active.")}
            )


class StakeholderAssessment(StakeholderRecord):
    """Power-interest assessment with explicit missing-data output."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="assessments"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    assessment_date = models.DateField(default=timezone.localdate, db_index=True)
    influence_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    interest_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    power_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    impact_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    strategic_importance_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    strategic_relevance_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    relationship_potential_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    resource_capacity_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    technical_capacity_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    geographic_relevance_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    reputation_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    compliance_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    safeguarding_readiness_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    financial_risk_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    operational_risk_score = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    average_score = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    completeness_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    classification = models.CharField(
        max_length=30,
        choices=AssessmentClassification.choices,
        default=AssessmentClassification.INSUFFICIENT_DATA,
        db_index=True,
    )
    missing_fields = models.JSONField(default=list, blank=True)
    matrix_explanation = models.TextField(blank=True)
    formula_version = models.CharField(max_length=40)
    evidence_summary = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    review_date = models.DateField(null=True, blank=True, db_index=True)
    assessment_status = models.CharField(max_length=30, default="DRAFT", db_index=True)
    approval_status = models.CharField(max_length=30, default="PENDING", db_index=True)
    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_assessments_completed",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-assessment_date", "-created_at")
        indexes = [
            models.Index(fields=["stakeholder", "assessment_date"]),
            models.Index(fields=["classification", "assessment_date"]),
        ]

    def clean(self) -> None:
        super().clean()
        if self.assessment_date > timezone.localdate():
            raise ValidationError(
                {"assessment_date": _("Assessment date cannot be future.")}
            )


class StakeholderEngagementPlan(StakeholderRecord):
    """Time-bound engagement strategy for a stakeholder relationship."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="engagement_plans"
    )
    title = models.CharField(max_length=220)
    purpose = models.TextField(blank=True)
    objectives = models.TextField()
    strategy = models.TextField(blank=True)
    communication_method = models.CharField(max_length=120, blank=True)
    key_messages = models.TextField(blank=True)
    risks = models.TextField(blank=True)
    engagement_level = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="engagement_plans",
        limit_choices_to={"kind": ReferenceDataKind.ENGAGEMENT_LEVEL},
    )
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_engagement_plans",
        null=True,
        blank=True,
    )
    planned_activities = models.TextField(blank=True)
    communication_frequency = models.CharField(max_length=100, blank=True)
    expected_outcomes = models.TextField(blank=True)
    success_indicators = models.TextField(blank=True)
    escalation_procedure = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=PlanStatus.choices,
        default=PlanStatus.DRAFT,
        db_index=True,
    )

    class Meta:
        ordering = ("-start_date",)
        indexes = [models.Index(fields=["stakeholder", "status"])]

    def __str__(self) -> str:
        return f"{self.stakeholder}: {self.title}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.start_date, self.end_date)
        if (
            self.engagement_level_id
            and self.engagement_level.kind != ReferenceDataKind.ENGAGEMENT_LEVEL
        ):
            raise ValidationError(
                {"engagement_level": _("Invalid engagement level kind.")}
            )


class StakeholderEngagement(StakeholderRecord):
    """Meeting, consultation, event, or other stakeholder engagement."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="engagements"
    )
    plan = models.ForeignKey(
        StakeholderEngagementPlan,
        on_delete=models.SET_NULL,
        related_name="engagements",
        null=True,
        blank=True,
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    engagement_type = models.CharField(max_length=30, choices=EngagementType.choices)
    title = models.CharField(max_length=220)
    scheduled_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    venue_or_link = models.CharField(max_length=255, blank=True)
    purpose = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_stakeholder_engagements",
        null=True,
        blank=True,
    )
    internal_participants = models.TextField(blank=True)
    external_participants = models.TextField(blank=True)
    agenda = models.TextField(blank=True)
    minutes = models.TextField(blank=True)
    decisions = models.TextField(blank=True)
    outcomes = models.TextField(blank=True)
    commitments = models.TextField(blank=True)
    follow_up_actions = models.TextField(blank=True)
    follow_up_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=EngagementStatus.choices,
        default=EngagementStatus.PLANNED,
        db_index=True,
    )
    is_confidential = models.BooleanField(default=False)

    class Meta:
        ordering = ("-scheduled_at",)
        indexes = [models.Index(fields=["stakeholder", "status", "scheduled_at"])]

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        if self.completed_at and self.completed_at < self.scheduled_at:
            raise ValidationError(
                {"completed_at": _("Completion cannot precede scheduling.")}
            )
        if self.status == EngagementStatus.COMPLETED and not self.completed_at:
            raise ValidationError(
                {"completed_at": _("Completed engagements need a completion time.")}
            )
        plan = self.plan
        if (
            self.plan_id
            and plan is not None
            and plan.stakeholder_id != self.stakeholder_id
        ):
            raise ValidationError(
                {"plan": _("Plan belongs to a different stakeholder.")}
            )


class StakeholderCommunication(StakeholderRecord):
    """Retained inbound, outbound, or internal communication history."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="communications"
    )
    contact = models.ForeignKey(
        StakeholderContact,
        on_delete=models.SET_NULL,
        related_name="communications",
        null=True,
        blank=True,
    )
    engagement = models.ForeignKey(
        StakeholderEngagement,
        on_delete=models.SET_NULL,
        related_name="communications",
        null=True,
        blank=True,
    )
    channel = models.CharField(max_length=20, choices=CommunicationChannel.choices)
    direction = models.CharField(max_length=20, choices=CommunicationDirection.choices)
    subject = models.CharField(max_length=255)
    summary = models.TextField()
    occurred_at = models.DateTimeField(default=timezone.now, db_index=True)
    sender = models.CharField(max_length=180, blank=True)
    recipients = models.TextField(blank=True)
    outcome = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="responsible_stakeholder_communications",
        null=True,
        blank=True,
    )
    attachment = models.FileField(
        upload_to="stakeholders/communications/",
        storage=private_stakeholder_storage,
        validators=[validate_stakeholder_document],
        null=True,
        blank=True,
    )
    requires_follow_up = models.BooleanField(default=False)
    follow_up_due_date = models.DateField(null=True, blank=True, db_index=True)
    is_confidential = models.BooleanField(default=False)

    class Meta:
        ordering = ("-occurred_at",)
        indexes = [models.Index(fields=["stakeholder", "channel", "occurred_at"])]

    def clean(self) -> None:
        super().clean()
        if self.requires_follow_up and not self.follow_up_due_date:
            raise ValidationError(
                {"follow_up_due_date": _("A follow-up date is required.")}
            )
        contact = self.contact
        if (
            self.contact_id
            and contact is not None
            and contact.stakeholder_id != self.stakeholder_id
        ):
            raise ValidationError(
                {"contact": _("Contact belongs to a different stakeholder.")}
            )


class StakeholderCommitment(StakeholderRecord):
    """A dated obligation made by either party."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="commitments"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    title = models.CharField(max_length=220)
    commitment_type = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    responsible_party = models.CharField(max_length=180)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_commitments",
        null=True,
        blank=True,
    )
    due_date = models.DateField(db_index=True)
    commitment_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20,
        choices=CommitmentStatus.choices,
        default=CommitmentStatus.OPEN,
        db_index=True,
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    progress_notes = models.TextField(blank=True)
    completion_date = models.DateField(null=True, blank=True)
    evidence_reference = models.CharField(max_length=255, blank=True)
    expected_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    actual_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    in_kind_details = models.TextField(blank=True)
    follow_up_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_commitment_followups",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("due_date",)
        indexes = [models.Index(fields=["stakeholder", "status", "due_date"])]

    def clean(self) -> None:
        super().clean()
        if self.status == CommitmentStatus.COMPLETED and not self.completion_date:
            raise ValidationError(
                {"completion_date": _("Completion date is required.")}
            )


class StakeholderContribution(StakeholderRecord):
    """Financial, in-kind, technical, or advisory stakeholder support."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="contributions"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    contribution_type = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="contributions",
        limit_choices_to={"kind": ReferenceDataKind.CONTRIBUTION_TYPE},
    )
    description = models.TextField()
    contribution_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    estimated_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    quantity = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    unit = models.CharField(max_length=60, blank=True)
    program_reference = models.CharField(max_length=180, blank=True)
    project_reference = models.CharField(max_length=180, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ContributionStatus.choices,
        default=ContributionStatus.PLEDGED,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="verified_stakeholder_contributions",
        null=True,
        blank=True,
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-contribution_date",)
        indexes = [models.Index(fields=["stakeholder", "status", "contribution_date"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__isnull=True) | models.Q(amount__gte=0),
                name="stakeholder_contribution_amount_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(estimated_value__isnull=True)
                | models.Q(estimated_value__gte=0),
                name="stakeholder_contribution_value_nonnegative",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if (
            self.contribution_type_id
            and self.contribution_type.kind != ReferenceDataKind.CONTRIBUTION_TYPE
        ):
            raise ValidationError(
                {"contribution_type": _("Invalid contribution type kind.")}
            )
        if not (
            self.amount is not None
            or self.estimated_value is not None
            or self.quantity is not None
        ):
            raise ValidationError(_("Record an amount, estimated value, or quantity."))
        if self.status == ContributionStatus.VERIFIED and not (
            self.verified_by_id and self.verified_at
        ):
            raise ValidationError(
                {"status": _("Verified contributions need verification metadata.")}
            )


class StakeholderAgreement(StakeholderRecord, ArchivableModel):
    """MoU, contract, grant, or other formal stakeholder agreement."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="agreements"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    agreement_type = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="agreements",
        limit_choices_to={"kind": ReferenceDataKind.AGREEMENT_TYPE},
    )
    title = models.CharField(max_length=255)
    purpose = models.TextField(blank=True)
    description = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    deliverables = models.TextField(blank=True)
    obligations = models.TextField(blank=True)
    reporting_requirements = models.TextField(blank=True)
    confidentiality_terms = models.TextField(blank=True)
    termination_terms = models.TextField(blank=True)
    program_references = models.TextField(blank=True)
    project_references = models.TextField(blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    notice_period_days = models.PositiveIntegerField(default=60)
    signing_date = models.DateField(null=True, blank=True)
    renewal_date = models.DateField(null=True, blank=True, db_index=True)
    sitadc_signatory = models.CharField(max_length=180, blank=True)
    stakeholder_signatory = models.CharField(max_length=180, blank=True)
    financial_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    in_kind_value = models.DecimalField(
        max_digits=16, decimal_places=2, null=True, blank=True
    )
    currency = models.CharField(max_length=3, default=DEFAULT_CURRENCY)
    status = models.CharField(
        max_length=20,
        choices=AgreementStatus.choices,
        default=AgreementStatus.DRAFT,
        db_index=True,
    )
    current_version_number = models.PositiveIntegerField(default=0)
    relationship_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_stakeholder_agreements",
        null=True,
        blank=True,
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="approved_stakeholder_agreements",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)
    termination_reason = models.TextField(blank=True)

    class Meta:
        ordering = ("-effective_date", "title")
        indexes = [
            models.Index(fields=["stakeholder", "status"]),
            models.Index(fields=["status", "expiry_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.reference_number})"

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.effective_date, self.expiry_date, end_field="expiry_date"
        )
        if (
            self.agreement_type_id
            and self.agreement_type.kind != ReferenceDataKind.AGREEMENT_TYPE
        ):
            raise ValidationError({"agreement_type": _("Invalid agreement type kind.")})
        if self.status == AgreementStatus.ACTIVE and not (
            self.effective_date and self.approved_by_id and self.approved_at
        ):
            raise ValidationError(
                {"status": _("Active agreements must be approved and effective.")}
            )
        for field_name in ("financial_value", "in_kind_value"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValidationError({field_name: _("Value cannot be negative.")})

    @property
    def is_expired(self) -> bool:
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())


class StakeholderAgreementVersion(ImmutableHistoricalRecord, StakeholderRecord):
    """Immutable signed or draft content snapshot for an agreement."""

    agreement = models.ForeignKey(
        StakeholderAgreement, on_delete=models.PROTECT, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    purpose = models.TextField(blank=True)
    responsibilities = models.TextField(blank=True)
    deliverables = models.TextField(blank=True)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    file = models.FileField(
        upload_to="stakeholders/agreements/",
        storage=private_stakeholder_storage,
        validators=[validate_stakeholder_document],
        null=True,
        blank=True,
    )
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.PositiveBigIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=128, blank=True)
    change_summary = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="finalized_stakeholder_agreement_versions",
        null=True,
        blank=True,
    )

    objects = ImmutableHistoryManager()

    class Meta:
        ordering = ("agreement", "-version_number")
        constraints = [
            models.UniqueConstraint(
                fields=["agreement", "version_number"],
                name="stakeholder_agreement_version_uniq",
            )
        ]

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.effective_date, self.expiry_date, end_field="expiry_date"
        )


class StakeholderAgreementRenewal(StakeholderRecord):
    """Review and decision record for an agreement renewal."""

    agreement = models.ForeignKey(
        StakeholderAgreement, on_delete=models.PROTECT, related_name="renewals"
    )
    requested_at = models.DateTimeField(default=timezone.now)
    proposed_effective_date = models.DateField()
    proposed_expiry_date = models.DateField(null=True, blank=True)
    rationale = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=RenewalStatus.choices,
        default=RenewalStatus.PENDING,
        db_index=True,
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="decided_stakeholder_renewals",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    decision_notes = models.TextField(blank=True)
    renewed_agreement = models.OneToOneField(
        StakeholderAgreement,
        on_delete=models.SET_NULL,
        related_name="source_renewal",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-requested_at",)
        indexes = [models.Index(fields=["agreement", "status"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.proposed_effective_date,
            self.proposed_expiry_date,
            end_field="proposed_expiry_date",
        )
        if self.renewed_agreement_id and self.renewed_agreement_id == self.agreement_id:
            raise ValidationError(
                {"renewed_agreement": _("Renewal must create a new agreement.")}
            )


class StakeholderDueDiligence(StakeholderRecord):
    """Structured legal, financial, safeguarding, and compliance review."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="due_diligence_reviews"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    review_date = models.DateField(default=timezone.localdate, db_index=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=DueDiligenceStatus.choices,
        default=DueDiligenceStatus.DRAFT,
        db_index=True,
    )
    checks = models.JSONField(
        default=dict,
        blank=True,
        help_text=_("Named checks with result, evidence, and rationale."),
    )
    missing_information = models.JSONField(default=list, blank=True)
    findings = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    recommendation = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_due_diligence_reviews",
        null=True,
        blank=True,
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-review_date",)
        indexes = [models.Index(fields=["stakeholder", "status", "expiry_date"])]

    def clean(self) -> None:
        super().clean()
        validate_date_range(self.review_date, self.expiry_date, end_field="expiry_date")
        if self.status in {
            DueDiligenceStatus.PASSED,
            DueDiligenceStatus.CONDITIONAL,
            DueDiligenceStatus.FAILED,
        } and not (self.reviewed_by_id and self.completed_at):
            raise ValidationError(
                {"status": _("Completed reviews require actor metadata.")}
            )


class StakeholderConflictOfInterest(StakeholderRecord):
    """Conflict declaration and mitigation record."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="conflicts_of_interest"
    )
    declared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_conflicts_declared",
        null=True,
        blank=True,
    )
    declared_at = models.DateTimeField(default=timezone.now)
    nature = models.TextField()
    affected_decisions = models.TextField(blank=True)
    mitigation = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=ConflictStatus.choices,
        default=ConflictStatus.DECLARED,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_conflicts_reviewed",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-declared_at",)
        indexes = [models.Index(fields=["stakeholder", "status"])]


class StakeholderRisk(StakeholderRecord):
    """Relationship risk with likelihood-impact scoring and mitigation."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="risks"
    )
    category = models.ForeignKey(
        StakeholderReferenceData,
        on_delete=models.PROTECT,
        related_name="stakeholder_risks",
        limit_choices_to={"kind": ReferenceDataKind.RISK_CATEGORY},
    )
    title = models.CharField(max_length=220)
    description = models.TextField()
    likelihood = models.PositiveSmallIntegerField(
        choices=RiskLevel.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    impact = models.PositiveSmallIntegerField(
        choices=RiskLevel.choices,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    risk_score = models.PositiveSmallIntegerField(default=1, editable=False)
    mitigation_strategy = models.TextField(blank=True)
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_risks",
        null=True,
        blank=True,
    )
    next_review_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=RiskStatus.choices,
        default=RiskStatus.OPEN,
        db_index=True,
    )

    class Meta:
        ordering = ("-risk_score", "next_review_date")
        indexes = [models.Index(fields=["stakeholder", "status", "risk_score"])]

    def clean(self) -> None:
        super().clean()
        if self.category_id and self.category.kind != ReferenceDataKind.RISK_CATEGORY:
            raise ValidationError({"category": _("Invalid risk category kind.")})
        self.risk_score = self.likelihood * self.impact

    def save(self, *args, **kwargs) -> None:
        self.risk_score = self.likelihood * self.impact
        super().save(*args, **kwargs)


class StakeholderPerformanceDimension(StakeholderRecord):
    """Configurable weighted dimension for stakeholder scorecards."""

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    weight = models.DecimalField(
        max_digits=7,
        decimal_places=4,
        default=Decimal("1.0000"),
        validators=[validate_positive_weight],
    )
    minimum_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    maximum_score = models.DecimalField(max_digits=7, decimal_places=2, default=100)
    active = models.BooleanField(default=True, db_index=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")
        indexes = [models.Index(fields=["active", "order"])]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        super().clean()
        if self.maximum_score <= self.minimum_score:
            raise ValidationError({"maximum_score": _("Maximum must exceed minimum.")})


class StakeholderPerformanceReview(StakeholderRecord):
    """Periodic stakeholder scorecard with a reproducible weighted result."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="performance_reviews"
    )
    reference_number = models.CharField(max_length=80, unique=True, db_index=True)
    review_period = models.CharField(max_length=80)
    review_date = models.DateField(default=timezone.localdate, db_index=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_performance_reviews",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.DRAFT,
        db_index=True,
    )
    weighted_score = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    completeness_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[validate_percentage],
    )
    missing_dimensions = models.JSONField(default=list, blank=True)
    formula_explanation = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    improvement_areas = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-review_date",)
        constraints = [
            models.UniqueConstraint(
                fields=["stakeholder", "review_period"],
                name="stakeholder_performance_period_uniq",
            )
        ]
        indexes = [models.Index(fields=["stakeholder", "status", "review_date"])]

    def __str__(self) -> str:
        return f"{self.stakeholder} - {self.review_period}"


class StakeholderPerformanceScore(StakeholderRecord):
    """One dimension score and the weight snapshot used by a review."""

    review = models.ForeignKey(
        StakeholderPerformanceReview, on_delete=models.PROTECT, related_name="scores"
    )
    dimension = models.ForeignKey(
        StakeholderPerformanceDimension,
        on_delete=models.PROTECT,
        related_name="scores",
    )
    score = models.DecimalField(max_digits=7, decimal_places=2)
    weight_snapshot = models.DecimalField(max_digits=7, decimal_places=4)
    normalized_score = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True
    )
    comments = models.TextField(blank=True)

    class Meta:
        ordering = ("dimension__order",)
        constraints = [
            models.UniqueConstraint(
                fields=["review", "dimension"],
                name="stakeholder_review_dimension_uniq",
            )
        ]

    def clean(self) -> None:
        super().clean()
        if self.dimension_id and not (
            self.dimension.minimum_score <= self.score <= self.dimension.maximum_score
        ):
            raise ValidationError({"score": _("Score is outside the dimension range.")})
        validate_positive_weight(self.weight_snapshot)


class StakeholderActionItem(StakeholderRecord):
    """Follow-up action arising from any stakeholder domain activity."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="action_items"
    )
    engagement = models.ForeignKey(
        StakeholderEngagement,
        on_delete=models.SET_NULL,
        related_name="action_items",
        null=True,
        blank=True,
    )
    commitment = models.ForeignKey(
        StakeholderCommitment,
        on_delete=models.SET_NULL,
        related_name="action_items",
        null=True,
        blank=True,
    )
    agreement = models.ForeignKey(
        StakeholderAgreement,
        on_delete=models.SET_NULL,
        related_name="action_items",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_action_items",
        null=True,
        blank=True,
    )
    due_date = models.DateField(db_index=True)
    priority = models.CharField(
        max_length=10, choices=ActionPriority.choices, default=ActionPriority.MEDIUM
    )
    status = models.CharField(
        max_length=20,
        choices=ActionStatus.choices,
        default=ActionStatus.OPEN,
        db_index=True,
    )
    progress_notes = models.TextField(blank=True)
    assigned_date = models.DateField(default=timezone.localdate)
    evidence_reference = models.CharField(max_length=255, blank=True)
    escalation_status = models.CharField(max_length=40, blank=True)
    comments = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("due_date", "-priority")
        indexes = [models.Index(fields=["stakeholder", "status", "due_date"])]

    def clean(self) -> None:
        super().clean()
        for field_name in ("engagement", "commitment", "agreement"):
            value = getattr(self, field_name, None)
            if value and value.stakeholder_id != self.stakeholder_id:
                raise ValidationError(
                    {field_name: _("Related record belongs to another stakeholder.")}
                )
        if self.status == ActionStatus.COMPLETED and not self.completed_at:
            raise ValidationError(
                {"completed_at": _("Completed actions need a timestamp.")}
            )


class StakeholderNote(StakeholderRecord):
    """Versioned internal note container."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="stakeholder_notes"
    )
    title = models.CharField(max_length=220)
    category = models.CharField(max_length=40, default="GENERAL", db_index=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="owned_stakeholder_notes",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=NoteStatus.choices,
        default=NoteStatus.DRAFT,
        db_index=True,
    )
    current_version_number = models.PositiveIntegerField(default=0)
    confidentiality = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.CONFIDENTIAL,
    )
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="finalized_stakeholder_notes",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=["stakeholder", "status"])]

    def __str__(self) -> str:
        return f"{self.stakeholder}: {self.title}"


class StakeholderNoteVersion(StakeholderRecord):
    """A note content snapshot; finalized snapshots cannot be changed or deleted."""

    note = models.ForeignKey(
        StakeholderNote, on_delete=models.PROTECT, related_name="versions"
    )
    version_number = models.PositiveIntegerField()
    content = models.TextField()
    change_summary = models.TextField(blank=True)
    is_finalized = models.BooleanField(default=False, db_index=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="finalized_stakeholder_note_versions",
        null=True,
        blank=True,
    )

    objects = NoteVersionManager()

    class Meta:
        ordering = ("note", "-version_number")
        constraints = [
            models.UniqueConstraint(
                fields=["note", "version_number"],
                name="stakeholder_note_version_uniq",
            )
        ]

    def save(self, *args, **kwargs) -> None:
        if self.pk:
            previous = (
                type(self).objects.filter(pk=self.pk).values("is_finalized").first()
            )
            if previous and previous["is_finalized"]:
                raise ValidationError(
                    FINALIZED_NOTE_VERSION_MESSAGE,
                    code="finalized_note_version",
                )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.is_finalized:
            raise ValidationError(
                FINALIZED_NOTE_VERSION_MESSAGE,
                code="finalized_note_version",
            )
        return super().delete(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.is_finalized and not (self.finalized_at and self.finalized_by_id):
            raise ValidationError(
                {"is_finalized": _("Finalization metadata is required.")}
            )


class StakeholderDocument(StakeholderRecord):
    """Protected private document version linked to a stakeholder."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="documents"
    )
    document_key = models.SlugField(max_length=100)
    version_number = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="subsequent_versions",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    document_type = models.CharField(max_length=120)
    file = models.FileField(
        upload_to="stakeholders/documents/",
        storage=private_stakeholder_storage,
        validators=[validate_stakeholder_document],
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=20,
        choices=DocumentStatus.choices,
        default=DocumentStatus.CURRENT,
        db_index=True,
    )
    confidentiality = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.CONFIDENTIAL,
        db_index=True,
    )
    is_protected = models.BooleanField(default=True)
    legal_hold = models.BooleanField(default=False)
    effective_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, db_index=True)
    retention_until = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("document_key", "-version_number")
        constraints = [
            models.UniqueConstraint(
                fields=["stakeholder", "document_key", "version_number"],
                name="stakeholder_document_version_uniq",
            )
        ]
        indexes = [models.Index(fields=["stakeholder", "status", "confidentiality"])]

    def __str__(self) -> str:
        return f"{self.title} v{self.version_number}"

    def clean(self) -> None:
        super().clean()
        validate_date_range(
            self.effective_date, self.expiry_date, end_field="expiry_date"
        )
        previous_version = self.previous_version
        if self.previous_version_id and previous_version is not None:
            if previous_version.stakeholder_id != self.stakeholder_id:
                raise ValidationError(
                    {"previous_version": _("Previous version has another owner.")}
                )
            if previous_version.document_key != self.document_key:
                raise ValidationError(
                    {"previous_version": _("Document keys must match.")}
                )

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            _("Stakeholder documents must be archived, not deleted."),
            code="protected_stakeholder_document",
        )


class StakeholderDuplicateReview(StakeholderRecord):
    """Human resolution of a possible duplicate profile pair."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="duplicate_reviews"
    )
    possible_duplicate = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="duplicate_candidates"
    )
    match_score = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[validate_percentage]
    )
    matching_fields = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=30,
        choices=DuplicateReviewStatus.choices,
        default=DuplicateReviewStatus.PENDING,
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_duplicate_reviews",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["stakeholder", "possible_duplicate"],
                name="stakeholder_duplicate_pair_uniq",
            ),
            models.CheckConstraint(
                condition=~models.Q(stakeholder=models.F("possible_duplicate")),
                name="stakeholder_duplicate_not_self",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.stakeholder_id == self.possible_duplicate_id:
            raise ValidationError(
                {"possible_duplicate": _("A stakeholder cannot duplicate itself.")}
            )


class StakeholderAccessGrant(StakeholderRecord):
    """Explicit time-bound access to one stakeholder profile."""

    stakeholder = models.ForeignKey(
        Stakeholder, on_delete=models.PROTECT, related_name="access_grants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stakeholder_access_grants",
    )
    access_level = models.CharField(
        max_length=20, choices=AccessLevel.choices, default=AccessLevel.VIEW
    )
    reason = models.TextField()
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_access_grants_made",
        null=True,
        blank=True,
    )
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="stakeholder_access_grants_revoked",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["stakeholder", "user"],
                condition=models.Q(is_active=True),
                name="stakeholder_one_active_grant_per_user",
            )
        ]
        indexes = [models.Index(fields=["user", "is_active", "expires_at"])]

    def clean(self) -> None:
        super().clean()
        if self.expires_at and self.expires_at <= self.starts_at:
            raise ValidationError(
                {"expires_at": _("Expiry must follow the start time.")}
            )
        if self.is_active and self.revoked_at:
            raise ValidationError(
                {"is_active": _("A revoked grant cannot remain active.")}
            )
