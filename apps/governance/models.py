"""Models for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.constants import StatusConstants
from apps.core.models import (
    CreatedByModel,
    NotesModel,
    StatusModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.governance.constants import (
    RISK_MATRIX_HIGH_MAX,
    RISK_MATRIX_LOW_MAX,
    RISK_MATRIX_MEDIUM_MAX,
    RISK_SCALE_MAX,
    RISK_SCALE_MIN,
    AttendanceStatus,
    CAPPAActionType,
    ComplaintType,
    ComplianceAssessmentResult,
    ComplianceType,
    ConfidentialityLevel,
    ControlFrequency,
    ControlType,
    DeclarationType,
    EthicsCaseType,
    GovernanceDocumentType,
    GovernanceType,
    IncidentCategory,
    IncidentSeverity,
    MeetingType,
    NotificationType,
    PolicyCategory,
    Priority,
    ResolutionType,
    RiskAssessmentType,
    RiskCategory,
    RiskRating,
    RiskTreatmentType,
    SafeguardingCategory,
    TimelineEventType,
    WhistleblowerReportType,
)


class GovernanceRecord(
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    StatusModel,
    NotesModel,
):
    """Base governance record model."""

    governance_type = models.CharField(
        _("Governance type"),
        max_length=20,
        choices=GovernanceType.choices,
    )

    title = models.CharField(_("Title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Description"))

    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    # Related organizational units
    department = models.CharField(_("Department"), max_length=100, blank=True)
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    region = models.CharField(_("Region"), max_length=100, blank=True)

    # Responsible parties
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Responsible officer"),
    )

    # Dates
    effective_date = models.DateField(_("Effective date"), null=True, blank=True)
    expiry_date = models.DateField(_("Expiry date"), null=True, blank=True)
    review_date = models.DateField(_("Next review date"), null=True, blank=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title}"

    def clean(self) -> None:
        """Validate date ordering and review scheduling."""
        super().clean()
        if (
            self.effective_date
            and self.expiry_date
            and self.expiry_date < self.effective_date
        ):
            raise ValidationError(
                {"expiry_date": _("Expiry date cannot be before the effective date.")}
            )
        if (
            self.effective_date
            and self.review_date
            and self.review_date < self.effective_date
        ):
            raise ValidationError(
                {
                    "review_date": _(
                        "Next review date cannot be before the effective date."
                    )
                }
            )


class Policy(GovernanceRecord):
    """Policy management model."""

    policy_category = models.CharField(
        _("Policy category"),
        max_length=20,
        choices=PolicyCategory.choices,
        default=PolicyCategory.OTHER,
    )

    version = models.CharField(_("Version"), max_length=20, default="1.0")
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by",
        verbose_name=_("Supersedes policy"),
    )

    class Meta:
        verbose_name = _("Policy")
        verbose_name_plural = _("Policies")
        indexes = [
            models.Index(fields=["policy_category", "status"]),
            models.Index(fields=["review_date"]),
        ]

    def save(self, *args, **kwargs):
        if not self.governance_type:
            self.governance_type = GovernanceType.POLICY
        super().save(*args, **kwargs)


class PolicyVersion(UUIDModel, TimeStampedModel):
    """Version control for policies."""

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Policy"),
    )

    version_number = models.CharField(_("Version number"), max_length=20)
    effective_date = models.DateField(_("Effective date"))
    expiry_date = models.DateField(_("Expiry date"), null=True, blank=True)
    changes_summary = models.TextField(_("Changes summary"))
    document = models.FileField(_("Policy document"), upload_to="policies/")

    class Meta:
        verbose_name = _("Policy Version")
        verbose_name_plural = _("Policy Versions")
        unique_together = ("policy", "version_number")

    def __str__(self) -> str:
        return f"{self.policy.title} v{self.version_number}"

    def clean(self) -> None:
        """Validate version effective/expiry ordering."""
        super().clean()
        if (
            self.expiry_date
            and self.effective_date
            and self.expiry_date < self.effective_date
        ):
            raise ValidationError(
                {"expiry_date": _("Expiry date cannot be before the effective date.")}
            )


class PolicyAcknowledgement(UUIDModel, TimeStampedModel):
    """Tracking of policy acknowledgements by staff."""

    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name="acknowledgements",
        verbose_name=_("Policy"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="policy_acknowledgements",
        verbose_name=_("User"),
    )

    acknowledged_at = models.DateTimeField(_("Acknowledged at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires at"), null=True, blank=True)
    is_current = models.BooleanField(_("Is current"), default=True)

    class Meta:
        verbose_name = _("Policy Acknowledgement")
        verbose_name_plural = _("Policy Acknowledgements")
        unique_together = ("policy", "user")

    def __str__(self) -> str:
        return f"{self.user.get_full_name()} - {self.policy.title}"


class RiskRegister(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Enterprise risk register."""

    title = models.CharField(_("Risk title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    risk_category = models.CharField(
        _("Risk category"),
        max_length=25,
        choices=RiskCategory.choices,
    )
    description = models.TextField(_("Risk description"))
    root_cause = models.TextField(_("Root cause"), blank=True)

    # Risk assessment
    likelihood = models.PositiveSmallIntegerField(
        _("Likelihood"),
        help_text=_("Scale of 1-5, where 5 is most likely"),
        default=3,
    )
    impact = models.PositiveSmallIntegerField(
        _("Impact"),
        help_text=_("Scale of 1-5, where 5 is highest impact"),
        default=3,
    )

    @property
    def risk_score(self) -> int:
        """Overall risk score based on likelihood and impact."""
        return self.likelihood * self.impact

    @property
    def risk_rating(self) -> str:
        """Calculate overall risk rating based on likelihood and impact."""
        score = self.risk_score
        if score <= RISK_MATRIX_LOW_MAX:
            return RiskRating.LOW
        if score <= RISK_MATRIX_MEDIUM_MAX:
            return RiskRating.MEDIUM
        if score <= RISK_MATRIX_HIGH_MAX:
            return RiskRating.HIGH
        return RiskRating.CRITICAL

    risk_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_risks",
        verbose_name=_("Risk owner"),
    )

    mitigation_strategy = models.TextField(_("Mitigation strategy"))
    residual_likelihood = models.PositiveSmallIntegerField(
        _("Residual likelihood"),
        help_text=_("Scale of 1-5 after mitigation"),
        null=True,
        blank=True,
    )
    residual_impact = models.PositiveSmallIntegerField(
        _("Residual impact"),
        help_text=_("Scale of 1-5 after mitigation"),
        null=True,
        blank=True,
    )

    review_date = models.DateField(_("Next review date"))
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusConstants.choices,
        default=StatusConstants.ACTIVE,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Risk Register")
        verbose_name_plural = _("Risk Registers")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["risk_category", "status"]),
            models.Index(fields=["review_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.risk_category})"

    def clean(self) -> None:
        """Validate risk scores and review dates."""
        super().clean()
        for value, field_name in (
            (self.likelihood, "likelihood"),
            (self.impact, "impact"),
            (self.residual_likelihood, "residual_likelihood"),
            (self.residual_impact, "residual_impact"),
        ):
            if value is not None and (value < RISK_SCALE_MIN or value > RISK_SCALE_MAX):
                raise ValidationError(
                    {field_name: _("Risk scores must be between 1 and 5.")}
                )


class RiskAssessment(UUIDModel, TimeStampedModel):
    """Individual risk assessments."""

    risk_register = models.ForeignKey(
        RiskRegister,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Risk register"),
    )

    assessment_type = models.CharField(
        _("Assessment type"),
        max_length=20,
        choices=RiskAssessmentType.choices,
        default=RiskAssessmentType.INITIAL,
    )

    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_assessments",
        verbose_name=_("Assessed by"),
    )

    assessment_date = models.DateField(_("Assessment date"))
    likelihood = models.PositiveSmallIntegerField(_("Likelihood (1-5)"))
    impact = models.PositiveSmallIntegerField(_("Impact (1-5)"))
    risk_score = models.PositiveSmallIntegerField(_("Risk score"), editable=False)

    assessor_notes = models.TextField(_("Assessor notes"), blank=True)

    class Meta:
        verbose_name = _("Risk Assessment")
        verbose_name_plural = _("Risk Assessments")

    def save(self, *args, **kwargs):
        self.risk_score = self.likelihood * self.impact
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate assessment scores."""
        super().clean()
        for value, field_name in (
            (self.likelihood, "likelihood"),
            (self.impact, "impact"),
        ):
            if value is not None and (value < RISK_SCALE_MIN or value > RISK_SCALE_MAX):
                raise ValidationError(
                    {field_name: _("Risk scores must be between 1 and 5.")}
                )

    def __str__(self) -> str:
        return f"{self.risk_register.title} - {self.assessment_date}"


class RiskTreatmentPlan(UUIDModel, TimeStampedModel):
    """Risk treatment plans."""

    risk_register = models.ForeignKey(
        RiskRegister,
        on_delete=models.CASCADE,
        related_name="treatment_plans",
        verbose_name=_("Risk register"),
    )

    treatment_type = models.CharField(
        _("Treatment type"),
        max_length=10,
        choices=RiskTreatmentType.choices,
        default=RiskTreatmentType.MITIGATE,
    )

    description = models.TextField(_("Treatment description"))
    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="risk_treatments",
        verbose_name=_("Responsible officer"),
    )

    target_completion_date = models.DateField(_("Target completion date"))
    actual_completion_date = models.DateField(
        _("Actual completion date"), null=True, blank=True
    )
    progress_percentage = models.PositiveSmallIntegerField(
        _("Progress percentage"),
        default=0,
        help_text=_("Percentage completion of treatment plan"),
    )

    effectiveness_review_date = models.DateField(
        _("Effectiveness review date"), null=True, blank=True
    )
    effectiveness_rating = models.PositiveSmallIntegerField(
        _("Effectiveness rating (1-5)"),
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("Risk Treatment Plan")
        verbose_name_plural = _("Risk Treatment Plans")

    def clean(self) -> None:
        """Validate progress and effectiveness ranges."""
        super().clean()
        if not (0 <= self.progress_percentage <= 100):
            raise ValidationError(
                {"progress_percentage": _("Progress must be between 0 and 100.")}
            )
        if self.effectiveness_rating is not None and not (
            1 <= self.effectiveness_rating <= 5
        ):
            raise ValidationError(
                {
                    "effectiveness_rating": _(
                        "Effectiveness rating must be between 1 and 5."
                    )
                }
            )

    def __str__(self) -> str:
        return f"Treatment for {self.risk_register.title}"


class ComplianceRequirement(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Compliance requirements tracking."""

    title = models.CharField(_("Compliance requirement title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    compliance_type = models.CharField(
        _("Compliance type"),
        max_length=20,
        choices=ComplianceType.choices,
    )
    description = models.TextField(_("Description"))
    source_organization = models.CharField(
        _("Source organization"), max_length=200, blank=True
    )
    reference_document = models.CharField(
        _("Reference document"), max_length=200, blank=True
    )

    effective_date = models.DateField(_("Effective date"))
    expiry_date = models.DateField(_("Expiry date"), null=True, blank=True)

    is_active = models.BooleanField(_("Is active"), default=True)

    class Meta:
        verbose_name = _("Compliance Requirement")
        verbose_name_plural = _("Compliance Requirements")
        indexes = [
            models.Index(fields=["compliance_type", "is_active"]),
            models.Index(fields=["effective_date"]),
        ]

    def clean(self) -> None:
        """Validate compliance effective/expiry ordering."""
        super().clean()
        if (
            self.expiry_date
            and self.effective_date
            and self.expiry_date < self.effective_date
        ):
            raise ValidationError(
                {"expiry_date": _("Expiry date cannot be before the effective date.")}
            )

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.compliance_type})"


class ComplianceAssessment(UUIDModel, TimeStampedModel):
    """Assessments of compliance with requirements."""

    compliance_requirement = models.ForeignKey(
        ComplianceRequirement,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Compliance requirement"),
    )

    assessed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compliance_assessments",
        verbose_name=_("Assessed by"),
    )

    assessment_date = models.DateField(_("Assessment date"))
    assessment_period_start = models.DateField(_("Assessment period start"))
    assessment_period_end = models.DateField(_("Assessment period end"))

    result = models.CharField(
        _("Assessment result"),
        max_length=20,
        choices=ComplianceAssessmentResult.choices,
    )

    score_percentage = models.PositiveSmallIntegerField(
        _("Score percentage"),
        null=True,
        blank=True,
        help_text=_("Percentage score if applicable"),
    )

    findings = models.TextField(_("Findings"))
    recommendations = models.TextField(_("Recommendations"), blank=True)

    evidence_documents = models.ManyToManyField(
        "Document",
        blank=True,
        related_name="compliance_assessments",
        verbose_name=_("Evidence documents"),
    )

    class Meta:
        verbose_name = _("Compliance Assessment")
        verbose_name_plural = _("Compliance Assessments")

    def clean(self) -> None:
        """Validate assessment period ordering and score range."""
        super().clean()
        if (
            self.assessment_period_end
            and self.assessment_period_start
            and self.assessment_period_end < self.assessment_period_start
        ):
            raise ValidationError(
                {
                    "assessment_period_end": _(
                        "Assessment period end cannot be before start."
                    )
                }
            )
        if self.score_percentage is not None and not (
            0 <= self.score_percentage <= 100
        ):
            raise ValidationError(
                {"score_percentage": _("Score percentage must be between 0 and 100.")}
            )

    def __str__(self) -> str:
        return f"{self.compliance_requirement.title} - {self.assessment_date}"


class InternalControl(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Internal controls management."""

    title = models.CharField(_("Control title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    control_type = models.CharField(
        _("Control type"),
        max_length=15,
        choices=ControlType.choices,
    )
    description = models.TextField(_("Control description"))
    objective = models.TextField(_("Control objective"))

    frequency = models.CharField(
        _("Control frequency"),
        max_length=15,
        choices=ControlFrequency.choices,
    )

    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internal_controls",
        verbose_name=_("Responsible officer"),
    )

    control_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_controls",
        verbose_name=_("Control owner"),
    )

    is_automated = models.BooleanField(_("Is automated"), default=False)
    is_effective = models.BooleanField(_("Is effective"), default=True)
    last_tested_date = models.DateField(_("Last tested date"), null=True, blank=True)
    next_test_date = models.DateField(_("Next test date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Internal Control")
        verbose_name_plural = _("Internal Controls")
        indexes = [
            models.Index(fields=["control_type", "is_effective"]),
        ]

    def clean(self) -> None:
        """Validate test date ordering."""
        super().clean()
        if (
            self.next_test_date
            and self.last_tested_date
            and self.next_test_date < self.last_tested_date
        ):
            raise ValidationError(
                {
                    "next_test_date": _(
                        "Next test date cannot be before last tested date."
                    )
                }
            )

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.control_type})"


class EthicsCase(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Ethics cases management."""

    case_type = models.CharField(
        _("Case type"),
        max_length=30,
        choices=EthicsCaseType.choices,
        default=EthicsCaseType.OTHER,
    )

    title = models.CharField(_("Case title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Case description"))
    reported_date = models.DateField(_("Reported date"))

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_ethics_cases",
        verbose_name=_("Reported by"),
    )

    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_ethics_cases",
        verbose_name=_("Assigned investigator"),
    )

    investigation_start_date = models.DateField(
        _("Investigation start date"), null=True, blank=True
    )
    investigation_end_date = models.DateField(
        _("Investigation end date"), null=True, blank=True
    )

    resolution = models.TextField(_("Resolution"), blank=True)
    outcome = models.TextField(_("Outcome"), blank=True)
    lessons_learned = models.TextField(_("Lessons learned"), blank=True)

    class Meta:
        verbose_name = _("Ethics Case")
        verbose_name_plural = _("Ethics Cases")
        indexes = [
            models.Index(fields=["case_type", "status"]),
            models.Index(fields=["reported_date"]),
        ]

    def clean(self) -> None:
        """Validate investigation date ordering."""
        super().clean()
        if (
            self.investigation_end_date
            and self.investigation_start_date
            and self.investigation_end_date < self.investigation_start_date
        ):
            raise ValidationError(
                {
                    "investigation_end_date": _(
                        "Investigation end date cannot be before start date."
                    )
                }
            )

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.case_type})"


class ConflictOfInterestDeclaration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Conflict of interest declarations."""

    declarant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conflict_declarations",
        verbose_name=_("Declarant"),
    )

    declaration_type = models.CharField(
        _("Declaration type"),
        max_length=15,
        choices=DeclarationType.choices,
    )

    nature_of_conflict = models.TextField(_("Nature of conflict"))
    related_organization = models.CharField(
        _("Related organization"), max_length=200, blank=True
    )
    related_individual = models.CharField(
        _("Related individual"), max_length=200, blank=True
    )

    date_declared = models.DateField(_("Date declared"))
    review_date = models.DateField(_("Next review date"))

    mitigation_measures = models.TextField(_("Mitigation measures"))
    approval_status = models.CharField(
        _("Approval status"),
        max_length=20,
        choices=StatusConstants.choices,
        default=StatusConstants.PENDING_REVIEW,
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_conflicts",
        verbose_name=_("Approved by"),
    )

    approved_date = models.DateField(_("Approved date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Conflict of Interest Declaration")
        verbose_name_plural = _("Conflict of Interest Declarations")
        indexes = [
            models.Index(fields=["declaration_type", "approval_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.declarant.get_full_name()} - {self.declaration_type}"


class SafeguardingCase(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Safeguarding cases management."""

    case_category = models.CharField(
        _("Case category"),
        max_length=25,
        choices=SafeguardingCategory.choices,
    )

    title = models.CharField(_("Case title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Case description"))
    date_reported = models.DateField(_("Date reported"))

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_safeguarding_cases",
        verbose_name=_("Reported by"),
    )

    affected_individuals = models.TextField(
        _("Affected individuals"),
        help_text=_("Initials or reference numbers only for confidentiality"),
    )
    risk_level = models.CharField(
        _("Risk level"),
        max_length=10,
        choices=RiskRating.choices,
        default=RiskRating.MEDIUM,
    )

    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_safeguarding_cases",
        verbose_name=_("Assigned safeguarding officer"),
    )

    date_assigned = models.DateField(_("Date assigned"), null=True, blank=True)
    investigation_start_date = models.DateField(
        _("Investigation start date"), null=True, blank=True
    )
    investigation_end_date = models.DateField(
        _("Investigation end date"), null=True, blank=True
    )

    actions_taken = models.TextField(_("Actions taken"))
    outcome = models.TextField(_("Outcome"), blank=True)
    closure_date = models.DateField(_("Closure date"), null=True, blank=True)

    # Confidentiality is always HIGHLY_CONFIDENTIAL for safeguarding
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        default=ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        editable=False,
    )

    class Meta:
        verbose_name = _("Safeguarding Case")
        verbose_name_plural = _("Safeguarding Cases")
        indexes = [
            models.Index(fields=["case_category", "status"]),
            models.Index(fields=["risk_level", "status"]),
        ]

    def save(self, *args, **kwargs):
        # Safeguarding cases are always highly confidential
        self.confidentiality_level = ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Validate investigation date ordering."""
        super().clean()
        if (
            self.investigation_end_date
            and self.investigation_start_date
            and self.investigation_end_date < self.investigation_start_date
        ):
            raise ValidationError(
                {
                    "investigation_end_date": _(
                        "Investigation end date cannot be before start date."
                    )
                }
            )

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.case_category})"


class IncidentReport(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Organizational incident reporting."""

    incident_category = models.CharField(
        _("Incident category"),
        max_length=20,
        choices=IncidentCategory.choices,
    )

    title = models.CharField(_("Incident title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Incident description"))
    date_occurred = models.DateTimeField(_("Date and time occurred"))
    date_reported = models.DateTimeField(_("Date and time reported"), auto_now_add=True)

    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_incidents",
        verbose_name=_("Reported by"),
    )

    location = models.CharField(_("Location"), max_length=200, blank=True)
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=IncidentSeverity.choices,
        default=IncidentSeverity.MEDIUM,
    )

    immediate_actions_taken = models.TextField(_("Immediate actions taken"))
    investigation_required = models.BooleanField(
        _("Investigation required"), default=False
    )
    investigation_start_date = models.DateTimeField(
        _("Investigation start date"), null=True, blank=True
    )
    investigation_end_date = models.DateTimeField(
        _("Investigation end date"), null=True, blank=True
    )

    root_cause_analysis = models.TextField(_("Root cause analysis"), blank=True)
    corrective_actions = models.TextField(_("Corrective actions"), blank=True)
    preventive_actions = models.TextField(_("Preventive actions"), blank=True)

    # Link to related records
    safeguarding_case = models.ForeignKey(
        SafeguardingCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_incidents",
        verbose_name=_("Related safeguarding case"),
    )

    class Meta:
        verbose_name = _("Incident Report")
        verbose_name_plural = _("Incident Reports")
        indexes = [
            models.Index(fields=["incident_category", "status"]),
            models.Index(fields=["severity", "status"]),
        ]

    def clean(self) -> None:
        """Validate investigation date ordering."""
        super().clean()
        if (
            self.investigation_end_date
            and self.investigation_start_date
            and self.investigation_end_date < self.investigation_start_date
        ):
            raise ValidationError(
                {
                    "investigation_end_date": _(
                        "Investigation end date cannot be before start date."
                    )
                }
            )

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.incident_category})"


class Complaint(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Complaints management."""

    complaint_type = models.CharField(
        _("Complaint type"),
        max_length=20,
        choices=ComplaintType.choices,
    )

    title = models.CharField(_("Complaint title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Complaint description"))
    date_received = models.DateTimeField(_("Date and time received"), auto_now_add=True)

    complainant_name = models.CharField(
        _("Complainant name"), max_length=200, blank=True
    )
    complainant_contact = models.CharField(
        _("Complainant contact"), max_length=200, blank=True
    )
    complainant_is_anonymous = models.BooleanField(
        _("Complainant is anonymous"), default=False
    )

    # Related to service/programme if applicable
    programme = models.CharField(_("Related programme"), max_length=200, blank=True)
    service_location = models.CharField(
        _("Service location"), max_length=200, blank=True
    )
    staff_involved = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="involved_in_complaints",
        verbose_name=_("Staff involved"),
    )

    assigned_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_complaints",
        verbose_name=_("Assigned officer"),
    )

    date_assigned = models.DateTimeField(_("Date assigned"), null=True, blank=True)
    investigation_start_date = models.DateTimeField(
        _("Investigation start date"), null=True, blank=True
    )
    investigation_end_date = models.DateTimeField(
        _("Investigation end date"), null=True, blank=True
    )

    resolution_type = models.CharField(
        _("Resolution type"),
        max_length=20,
        choices=ResolutionType.choices,
        blank=True,
    )
    resolution_description = models.TextField(_("Resolution description"), blank=True)
    date_resolved = models.DateTimeField(_("Date resolved"), null=True, blank=True)

    appeal_date = models.DateTimeField(_("Appeal date"), null=True, blank=True)
    appeal_outcome = models.TextField(_("Appeal outcome"), blank=True)

    lessons_learned = models.TextField(_("Lessons learned"), blank=True)

    class Meta:
        verbose_name = _("Complaint")
        verbose_name_plural = _("Complaints")
        indexes = [
            models.Index(fields=["complaint_type", "status"]),
            models.Index(fields=["date_received"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} ({self.complaint_type})"


class WhistleblowerReport(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel
):
    """Confidential whistleblower reporting."""

    report_type = models.CharField(
        _("Report type"),
        max_length=25,
        choices=WhistleblowerReportType.choices,
    )

    title = models.CharField(_("Report title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Report description"))
    date_reported = models.DateTimeField(_("Date and time reported"), auto_now_add=True)

    # Whistleblower identity protection
    reporter_is_anonymous = models.BooleanField(
        _("Reporter is anonymous"), default=True
    )
    reporter_name = models.CharField(
        _("Reporter name (if known)"), max_length=200, blank=True
    )
    reporter_contact = models.CharField(
        _("Reporter contact (if known)"), max_length=200, blank=True
    )
    reporter_relationship = models.CharField(
        _("Reporter relationship to organization"), max_length=100, blank=True
    )

    alleged_subjects = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="whistleblower_allegations",
        verbose_name=_("Alleged subjects"),
    )

    assigned_investigator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_whistleblower_investigations",
        verbose_name=_("Assigned investigator"),
    )

    date_assigned = models.DateTimeField(_("Date assigned"), null=True, blank=True)
    investigation_start_date = models.DateTimeField(
        _("Investigation start date"), null=True, blank=True
    )
    investigation_end_date = models.DateTimeField(
        _("Investigation end date"), null=True, blank=True
    )

    evidence_documents = models.ManyToManyField(
        "Document",
        blank=True,
        related_name="whistleblower_reports",
        verbose_name=_("Evidence documents"),
    )

    outcome = models.TextField(_("Outcome"), blank=True)
    date_closed = models.DateTimeField(_("Date closed"), null=True, blank=True)

    # Always highly confidential for whistleblower reports
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        default=ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
        editable=False,
    )

    class Meta:
        verbose_name = _("Whistleblower Report")
        verbose_name_plural = _("Whistleblower Reports")
        indexes = [
            models.Index(fields=["report_type", "status"]),
        ]

    def save(self, *args, **kwargs):
        # Whistleblower reports are always highly confidential
        self.confidentiality_level = ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        reporter_info = (
            "Anonymous" if self.reporter_is_anonymous else self.reporter_name
        )
        return f"{self.reference_number} - {self.title} - Reporter: {reporter_info}"


class CorrectivePreventiveAction(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Corrective and Preventive Actions (CAPA)."""

    action_type = models.CharField(
        _("Action type"),
        max_length=10,
        choices=CAPPAActionType.choices,
        default=CAPPAActionType.BOTH,
    )

    title = models.CharField(_("Action title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Action description"))

    # Source issue
    source_incident = models.ForeignKey(
        IncidentReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="capa_from_incident",
        verbose_name=_("Source incident"),
    )
    source_complaint = models.ForeignKey(
        Complaint,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
        verbose_name=_("Source complaint"),
    )
    source_audit_finding = models.CharField(
        _("Source audit finding"), max_length=200, blank=True
    )
    source_risk_assessment = models.ForeignKey(
        RiskAssessment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
        verbose_name=_("Source risk assessment"),
    )
    source_whistleblower_report = models.ForeignKey(
        WhistleblowerReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
        verbose_name=_("Source whistleblower report"),
    )
    source_safeguarding_case = models.ForeignKey(
        SafeguardingCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
        verbose_name=_("Source safeguarding case"),
    )
    source_ethics_case = models.ForeignKey(
        EthicsCase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="corrective_actions",
        verbose_name=_("Source ethics case"),
    )

    root_cause = models.TextField(_("Root cause analysis"))
    corrective_action_description = models.TextField(_("Corrective action description"))
    preventive_action_description = models.TextField(
        _("Preventive action description"), blank=True
    )

    responsible_officer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_capactions",
        verbose_name=_("Responsible officer"),
    )

    due_date = models.DateField(_("Due date"))
    completion_date = models.DateField(_("Completion date"), null=True, blank=True)
    verification_date = models.DateField(_("Verification date"), null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_capactions",
        verbose_name=_("Verified by"),
    )

    effectiveness_rating = models.PositiveSmallIntegerField(
        _("Effectiveness rating (1-5)"),
        null=True,
        blank=True,
    )
    lessons_learned = models.TextField(_("Lessons learned"), blank=True)

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusConstants.choices,
        default=StatusConstants.DRAFT,
        db_index=True,
    )

    class Meta:
        verbose_name = _("Corrective & Preventive Action")
        verbose_name_plural = _("Corrective & Preventive Actions")
        indexes = [
            models.Index(fields=["action_type", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def clean(self) -> None:
        """Validate CAPA dates and effectiveness range."""
        super().clean()
        if self.effectiveness_rating is not None and not (
            1 <= self.effectiveness_rating <= 5
        ):
            raise ValidationError(
                {
                    "effectiveness_rating": _(
                        "Effectiveness rating must be between 1 and 5."
                    )
                }
            )
        if (
            self.completion_date
            and self.due_date
            and self.completion_date < self.due_date
        ):
            raise ValidationError(
                {"completion_date": _("Completion date cannot be before the due date.")}
            )

    def __str__(self) -> str:
        return (
            f"{self.reference_number} - {self.title} ({self.get_action_type_display()})"
        )


class Document(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Document management for governance records."""

    document_type = models.CharField(
        _("Document type"),
        max_length=15,
        choices=GovernanceDocumentType.choices,
        default=GovernanceDocumentType.OTHER,
    )

    title = models.CharField(_("Document title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    description = models.TextField(_("Document description"), blank=True)
    file = models.FileField(_("File"), upload_to="governance_documents/")
    file_size = models.PositiveIntegerField(
        _("File size (bytes)"), null=True, blank=True
    )
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)

    version = models.CharField(_("Version"), max_length=20, default="1.0")
    is_current_version = models.BooleanField(_("Is current version"), default=True)

    # Access controls
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    # Related governance records
    related_policies = models.ManyToManyField(
        Policy,
        blank=True,
        related_name="related_documents",
        verbose_name=_("Related policies"),
    )
    related_risks = models.ManyToManyField(
        RiskRegister,
        blank=True,
        related_name="related_documents",
        verbose_name=_("Related risks"),
    )
    related_compliance = models.ManyToManyField(
        ComplianceRequirement,
        blank=True,
        related_name="related_documents",
        verbose_name=_("Related compliance requirements"),
    )
    related_incidents = models.ManyToManyField(
        IncidentReport,
        blank=True,
        related_name="related_documents",
        verbose_name=_("Related incidents"),
    )

    class Meta:
        verbose_name = _("Document")
        verbose_name_plural = _("Documents")

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title} v{self.version}"


class GovernanceMeeting(GovernanceRecord):
    """Governance meetings management."""

    meeting_type = models.CharField(
        _("Meeting type"),
        max_length=15,
        choices=MeetingType.choices,
        default=MeetingType.OTHER,
    )

    governance_type = models.CharField(
        _("Governance type"),
        max_length=20,
        choices=GovernanceType.choices,
        default=GovernanceType.GOVERNANCE_MEETING,
    )

    scheduled_date = models.DateTimeField(_("Scheduled date and time"))
    actual_start_time = models.DateTimeField(
        _("Actual start time"), null=True, blank=True
    )
    actual_end_time = models.DateTimeField(_("Actual end time"), null=True, blank=True)

    location = models.CharField(_("Location"), max_length=200, blank=True)
    meeting_chair = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chaired_governance_meetings",
        verbose_name=_("Meeting chair"),
    )

    minutes = models.TextField(_("Meeting minutes"), blank=True)
    action_items = models.TextField(_("Action items"), blank=True)
    decisions_made = models.TextField(_("Decisions made"), blank=True)

    attendance = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="governance.MeetingAttendance",
        related_name="attended_governance_meetings",
        verbose_name=_("Attendees"),
    )

    class Meta:
        verbose_name = _("Governance Meeting")
        verbose_name_plural = _("Governance Meetings")
        indexes = [
            models.Index(fields=["meeting_type", "status"]),
            models.Index(fields=["scheduled_date"]),
        ]

    def __str__(self) -> str:
        dt = self.scheduled_date.strftime("%Y-%m-%d %H:%M")
        return f"{self.reference_number} - {self.title} - {dt}"


class MeetingAttendance(UUIDModel, TimeStampedModel):
    """Tracking of meeting attendance."""

    meeting = models.ForeignKey(
        GovernanceMeeting,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("Meeting"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="meeting_attendance",
        verbose_name=_("User"),
    )

    attendance_status = models.CharField(
        _("Attendance status"),
        max_length=15,
        choices=AttendanceStatus.choices,
        default=AttendanceStatus.ABSENT,
    )

    joined_at = models.DateTimeField(_("Joined at"), null=True, blank=True)
    left_at = models.DateTimeField(_("Left at"), null=True, blank=True)

    apologies_note = models.TextField(_("Apologies note"), blank=True)

    class Meta:
        verbose_name = _("Meeting Attendance")
        verbose_name_plural = _("Meeting Attendances")
        unique_together = ("meeting", "user")

    def __str__(self) -> str:
        name = self.user.get_full_name()
        title = self.meeting.title
        status = self.get_attendance_status_display()
        return f"{name} - {title} ({status})"


class GovernanceNotification(UUIDModel, TimeStampedModel):
    """Notifications for governance activities."""

    notification_type = models.CharField(
        _("Notification type"),
        max_length=40,
        choices=NotificationType.choices,
    )

    title = models.CharField(_("Notification title"), max_length=200)
    message = models.TextField(_("Notification message"))

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="governance_notifications",
        verbose_name=_("Recipient"),
    )

    is_read = models.BooleanField(_("Is read"), default=False)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)

    # For sending via external systems (email, SMS, etc.)
    sent_via_email = models.BooleanField(_("Sent via email"), default=False)
    sent_via_sms = models.BooleanField(_("Sent via SMS"), default=False)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Governance Notification")
        verbose_name_plural = _("Governance Notifications")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} - {self.recipient.get_full_name()}"


class GovernanceTimeline(UUIDModel, TimeStampedModel):
    """Timeline of governance activities."""

    event_type = models.CharField(
        _("Event type"),
        max_length=30,
        choices=TimelineEventType.choices,
    )

    description = models.TextField(_("Event description"))
    event_date = models.DateTimeField(_("Event date and time"))

    # User who performed the action
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="governance_timeline_events",
        verbose_name=_("Performed by"),
    )

    # Additional metadata
    module = models.CharField(_("Module"), max_length=50, blank=True)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, blank=True
    )
    action_performed = models.CharField(
        _("Action performed"), max_length=100, blank=True
    )
    status_after_event = models.CharField(
        _("Status after event"), max_length=50, blank=True
    )
    remarks = models.TextField(_("Remarks"), blank=True)

    class Meta:
        verbose_name = _("Governance Timeline Event")
        verbose_name_plural = _("Governance Timeline Events")
        ordering = ["-event_date"]
        indexes = [
            models.Index(fields=["event_type", "event_date"]),
        ]

    def __str__(self) -> str:
        dt = self.event_date.strftime("%Y-%m-%d %H:%M")
        return f"{self.event_type} - {dt}"
