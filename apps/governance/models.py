"""Models for Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
    UUIDModel,
    StatusModel,
    NotesModel,
)
from apps.core.constants import StatusConstants


class GovernanceRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel, NotesModel):
    """Base governance record model."""
    
    GOVERNANCE_TYPE_CHOICES = [
        ("POLICY", _("Policy")),
        ("RISK", _("Risk")),
        ("COMPLIANCE", _("Compliance")),
        ("ETHICS", _("Ethics")),
        ("SAFEGUARDING", _("Safeguarding")),
        ("INCIDENT", _("Incident")),
        ("COMPLAINT", _("Complaint")),
        ("WHISTLEBLOWER", _("Whistleblower")),
        ("CAPA", _("Corrective & Preventive Action")),
        ("GOVERNANCE_MEETING", _("Governance Meeting")),
    ]
    
    PRIORITY_CHOICES = [
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    ]
    
    CONFIDENTIALITY_CHOICES = [
        ("PUBLIC", _("Public")),
        ("INTERNAL", _("Internal")),
        ("RESTRICTED", _("Restricted")),
        ("CONFIDENTIAL", _("Confidential")),
        ("HIGHLY_CONFIDENTIAL", _("Highly Confidential")),
    ]
    
    governance_type = models.CharField(
        _("Governance type"),
        max_length=20,
        choices=GOVERNANCE_TYPE_CHOICES,
    )
    
    title = models.CharField(_("Title"), max_length=200)
    reference_number = models.CharField(_("Reference number"), max_length=50, unique=True)
    description = models.TextField(_("Description"))
    
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
    )
    
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=CONFIDENTIALITY_CHOICES,
        default="INTERNAL",
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


class Policy(GovernanceRecord):
    """Policy management model."""
    
    POLICY_CATEGORY_CHOICES = [
        ("HR", _("Human Resources")),
        ("FINANCE", _("Finance")),
        ("OPERATIONS", _("Operations")),
        ("IT", _("Information Technology")),
        ("SAFEGUARDING", _("Safeguarding")),
        ("ETHICS", _("Ethics")),
        ("COMPLIANCE", _("Compliance")),
        ("GOVERNANCE", _("Governance")),
        ("OTHER", _("Other")),
    ]
    
    policy_category = models.CharField(
        _("Policy category"),
        max_length=20,
        choices=POLICY_CATEGORY_CHOICES,
        default="OTHER",
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
        
    def save(self, *args, **kwargs):
        if not self.governance_type:
            self.governance_type = "POLICY"
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
    
    RISK_CATEGORY_CHOICES = [
        ("STRATEGIC", _("Strategic")),
        ("OPERATIONAL", _("Operational")),
        ("FINANCIAL", _("Financial")),
        ("COMPLIANCE", _("Compliance")),
        ("REPUTATIONAL", _("Reputational")),
        ("INFORMATION_SECURITY", _("Information Security")),
        ("SAFEGUARDING", _("Safeguarding")),
        ("PROJECT", _("Project")),
        ("PROGRAMME", _("Programme")),
        ("ENVIRONMENTAL", _("Environmental")),
        ("LEGAL", _("Legal")),
    ]
    
    RISK_RATING_CHOICES = [
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    ]
    
    title = models.CharField(_("Risk title"), max_length=200)
    risk_category = models.CharField(
        _("Risk category"),
        max_length=25,
        choices=RISK_CATEGORY_CHOICES,
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
    def risk_rating(self) -> str:
        """Calculate overall risk rating based on likelihood and impact."""
        score = self.likelihood * self.impact
        if score <= 5:
            return "LOW"
        elif score <= 10:
            return "MEDIUM"
        elif score <= 15:
            return "HIGH"
        else:
            return "CRITICAL"
    
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
    )
    
    class Meta:
        verbose_name = _("Risk Register")
        verbose_name_plural = _("Risk Registers")
        ordering = ["-created_at"]
        
    def __str__(self) -> str:
        return f"{self.title} ({self.risk_category})"


class RiskAssessment(UUIDModel, TimeStampedModel):
    """Individual risk assessments."""
    
    ASSESSMENT_TYPE_CHOICES = [
        ("INITIAL", _("Initial Assessment")),
        ("REVIEW", _("Review")),
        ("POST_INCIDENT", _("Post-Incident")),
        ("AUDIT_FINDING", _("Audit Finding")),
    ]
    
    risk_register = models.ForeignKey(
        RiskRegister,
        on_delete=models.CASCADE,
        related_name="assessments",
        verbose_name=_("Risk register"),
    )
    
    assessment_type = models.CharField(
        _("Assessment type"),
        max_length=20,
        choices=ASSESSMENT_TYPE_CHOICES,
        default="INITIAL",
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
        
    def __str__(self) -> str:
        return f"{self.risk_register.title} - {self.assessment_date}"


class RiskTreatmentPlan(UUIDModel, TimeStampedModel):
    """Risk treatment plans."""
    
    TREATMENT_TYPE_CHOICES = [
        ("AVOID", _("Avoid")),
        ("TRANSFER", _("Transfer")),
        ("MITIGATE", _("Mitigate")),
        ("ACCEPT", _("Accept")),
    ]
    
    risk_register = models.ForeignKey(
        RiskRegister,
        on_delete=models.CASCADE,
        related_name="treatment_plans",
        verbose_name=_("Risk register"),
    )
    
    treatment_type = models.CharField(
        _("Treatment type"),
        max_length=10,
        choices=TREATMENT_TYPE_CHOICES,
        default="MITIGATE",
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
    actual_completion_date = models.DateField(_("Actual completion date"), null=True, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(
        _("Progress percentage"),
        default=0,
        help_text=_("Percentage completion of treatment plan"),
    )
    
    effectiveness_review_date = models.DateField(_("Effectiveness review date"), null=True, blank=True)
    effectiveness_rating = models.PositiveSmallIntegerField(
        _("Effectiveness rating (1-5)"),
        null=True,
        blank=True,
    )
    
    class Meta:
        verbose_name = _("Risk Treatment Plan")
        verbose_name_plural = _("Risk Treatment Plans")
        
    def __str__(self) -> str:
        return f"Treatment for {self.risk_register.title}"


class ComplianceRequirement(UUIDModel, TimeStampedModel):
    """Compliance requirements tracking."""
    
    COMPLIANCE_TYPE_CHOICES = [
        ("REGULATORY", _("Regulatory")),
        ("DONOR", _("Donor Requirements")),
        ("GRANT", _("Grant Conditions")),
        ("INTERNAL_POLICY", _("Internal Policy")),
        ("CONTRACTUAL", _("Contractual")),
        ("INDUSTRY_STANDARD", _("Industry Standard")),
        ("LEGAL", _("Legal")),
    ]
    
    title = models.CharField(_("Compliance requirement title"), max_length=200)
    compliance_type = models.CharField(
        _("Compliance type"),
        max_length=20,
        choices=COMPLIANCE_TYPE_CHOICES,
    )
    description = models.TextField(_("Description"))
    source_organization = models.CharField(_("Source organization"), max_length=200, blank=True)
    reference_document = models.CharField(_("Reference document"), max_length=200, blank=True)
    
    effective_date = models.DateField(_("Effective date"))
    expiry_date = models.DateField(_("Expiry date"), null=True, blank=True)
    
    is_active = models.BooleanField(_("Is active"), default=True)
    
    class Meta:
        verbose_name = _("Compliance Requirement")
        verbose_name_plural = _("Compliance Requirements")
        
    def __str__(self) -> str:
        return f"{self.title} ({self.compliance_type})"


class ComplianceAssessment(UUIDModel, TimeStampedModel):
    """Assessments of compliance with requirements."""
    
    ASSESSMENT_RESULT_CHOICES = [
        ("COMPLIANT", _("Compliant")),
        ("PARTIALLY_COMPLIANT", _("Partially Compliant")),
        ("NON_COMPLIANT", _("Non-Compliant")),
        ("NOT_APPLICABLE", _("Not Applicable")),
    ]
    
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
        choices=ASSESSMENT_RESULT_CHOICES,
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
        
    def __str__(self) -> str:
        return f"{self.compliance_requirement.title} - {self.assessment_date}"


class InternalControl(UUIDModel, TimeStampedModel):
    """Internal controls management."""
    
    CONTROL_TYPE_CHOICES = [
        ("FINANCIAL", _("Financial")),
        ("OPERATIONAL", _("Operational")),
        ("ADMINISTRATIVE", _("Administrative")),
        ("IT", _("IT/Technology")),
        ("PROCUREMENT", _("Procurement")),
        ("HR", _("Human Resources")),
        ("SAFEGUARDING", _("Safeguarding")),
    ]
    
    CONTROL_FREQUENCY_CHOICES = [
        ("CONTINUOUS", _("Continuous")),
        ("REAL_TIME", _("Real-time")),
        ("DAILY", _("Daily")),
        ("WEEKLY", _("Weekly")),
        ("MONTHLY", _("Monthly")),
        ("QUARTERLY", _("Quarterly")),
        ("ANNUALLY", _("Annually")),
        ("AS_NEEDED", _("As needed")),
    ]
    
    title = models.CharField(_("Control title"), max_length=200)
    control_type = models.CharField(
        _("Control type"),
        max_length=15,
        choices=CONTROL_TYPE_CHOICES,
    )
    description = models.TextField(_("Control description"))
    objective = models.TextField(_("Control objective"))
    
    frequency = models.CharField(
        _("Control frequency"),
        max_length=15,
        choices=CONTROL_FREQUENCY_CHOICES,
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
        
    def __str__(self) -> str:
        return f"{self.title} ({self.control_type})"


class EthicsCase(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Ethics cases management."""
    
    ETHICS_CASE_TYPE_CHOICES = [
        ("CONFLICT_OF_INTEREST", _("Conflict of Interest")),
        ("CODE_OF_CONDUCT_VIOLATION", _("Code of Conduct Violation")),
        ("FRAUD", _("Fraud")),
        ("CORRUPTION", _("Corruption")),
        ("HARASSMENT", _("Harassment")),
        ("DISCRIMINATION", _("Discrimination")),
        ("OTHER", _("Other Ethics Issue")),
    ]
    
    case_type = models.CharField(
        _("Case type"),
        max_length=30,
        choices=ETHICS_CASE_TYPE_CHOICES,
        default="OTHER",
    )
    
    title = models.CharField(_("Case title"), max_length=200)
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
    
    investigation_start_date = models.DateField(_("Investigation start date"), null=True, blank=True)
    investigation_end_date = models.DateField(_("Investigation end date"), null=True, blank=True)
    
    resolution = models.TextField(_("Resolution"), blank=True)
    outcome = models.TextField(_("Outcome"), blank=True)
    lessons_learned = models.TextField(_("Lessons learned"), blank=True)
    
    class Meta:
        verbose_name = _("Ethics Case")
        verbose_name_plural = _("Ethics Cases")
        
    def __str__(self) -> str:
        return f"{self.title} ({self.case_type})"


class ConflictOfInterestDeclaration(UUIDModel, TimeStampedModel):
    """Conflict of interest declarations."""
    
    DECLARATION_TYPE_CHOICES = [
        ("FINANCIAL", _("Financial Interest")),
        ("PERSONAL", _("Personal Relationship")),
        ("PROFESSIONAL", _("Professional Affiliation")),
        ("FAMILY", _("Family Connection")),
        ("BUSINESS", _("Business Interest")),
        ("OTHER", _("Other Interest")),
    ]
    
    declarant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conflict_declarations",
        verbose_name=_("Declarant"),
    )
    
    declaration_type = models.CharField(
        _("Declaration type"),
        max_length=15,
        choices=DECLARATION_TYPE_CHOICES,
    )
    
    nature_of_conflict = models.TextField(_("Nature of conflict"))
    related_organization = models.CharField(_("Related organization"), max_length=200, blank=True)
    related_individual = models.CharField(_("Related individual"), max_length=200, blank=True)
    
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
        
    def __str__(self) -> str:
        return f"{self.declarant.get_full_name()} - {self.declaration_type}"


class SafeguardingCase(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Safeguarding cases management."""
    
    CASE_CATEGORY_CHOICES = [
        ("CHILD_PROTECTION", _("Child Protection")),
        ("VULNERABLE_ADULT", _("Vulnerable Adult Protection")),
        ("WORKPLACE_SAFEGUARDING", _("Workplace Safeguarding")),
        ("ONLINE_SAFETY", _("Online Safety")),
        ("OTHER", _("Other Safeguarding Concern")),
    ]
    
    RISK_LEVEL_CHOICES = [
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    ]
    
    case_category = models.CharField(
        _("Case category"),
        max_length=25,
        choices=CASE_CATEGORY_CHOICES,
    )
    
    title = models.CharField(_("Case title"), max_length=200)
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
    
    affected_individuals = models.TextField(_("Affected individuals"), help_text=_("Initials or reference numbers only for confidentiality"))
    risk_level = models.CharField(
        _("Risk level"),
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        default="MEDIUM",
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
    investigation_start_date = models.DateField(_("Investigation start date"), null=True, blank=True)
    investigation_end_date = models.DateField(_("Investigation end date"), null=True, blank=True)
    
    actions_taken = models.TextField(_("Actions taken"))
    outcome = models.TextField(_("Outcome"), blank=True)
    closure_date = models.DateField(_("Closure date"), null=True, blank=True)
    
    # Confidentiality is always HIGHLY_CONFIDENTIAL for safeguarding
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        default="HIGHLY_CONFIDENTIAL",
        editable=False,
    )
    
    class Meta:
        verbose_name = _("Safeguarding Case")
        verbose_name_plural = _("Safeguarding Cases")
        
    def save(self, *args, **kwargs):
        # Safeguarding cases are always highly confidential
        if not self.confidentiality_level:
            self.confidentiality_level = "HIGHLY_CONFIDENTIAL"
        super().save(*args, **kwargs)
        
    def __str__(self) -> str:
        return f"{self.title} ({self.case_category})"


class IncidentReport(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Organizational incident reporting."""
    
    INCIDENT_CATEGORY_CHOICES = [
        ("HEALTH_AND_SAFETY", _("Health and Safety")),
        ("SECURITY", _("Security")),
        ("PROGRAMME", _("Programme Incident")),
        ("OPERATIONAL", _("Operational")),
        ("FINANCIAL", _("Financial")),
        ("TECHNOLOGY", _("Technology")),
        ("SAFEGUARDING", _("Safeguarding")),
        ("ENVIRONMENTAL", _("Environmental")),
        ("REPUTATIONAL", _("Reputational")),
        ("OTHER", _("Other")),
    ]
    
    SEVERITY_CHOICES = [
        ("LOW", _("Low")),
        ("MEDIUM", _("Medium")),
        ("HIGH", _("High")),
        ("CRITICAL", _("Critical")),
    ]
    
    incident_category = models.CharField(
        _("Incident category"),
        max_length=20,
        choices=INCIDENT_CATEGORY_CHOICES,
    )
    
    title = models.CharField(_("Incident title"), max_length=200)
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
        choices=SEVERITY_CHOICES,
        default="MEDIUM",
    )
    
    immediate_actions_taken = models.TextField(_("Immediate actions taken"))
    investigation_required = models.BooleanField(_("Investigation required"), default=False)
    investigation_start_date = models.DateTimeField(_("Investigation start date"), null=True, blank=True)
    investigation_end_date = models.DateTimeField(_("Investigation end date"), null=True, blank=True)
    
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
        
    def __str__(self) -> str:
        return f"{self.title} ({self.incident_category})"


class Complaint(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Complaints management."""
    
    COMPLAINT_TYPE_CHOICES = [
        ("SERVICE_DELIVERY", _("Service Delivery")),
        ("STAFF_CONDUCT", _("Staff Conduct")),
        ("POLICY_ISSUE", _("Policy Issue")),
        ("FACILITIES", _("Facilities")),
        ("PROGRAMME", _("Programme")),
        ("FINANCIAL", _("Financial")),
        ("OTHER", _("Other")),
    ]
    
    RESOLUTION_TYPE_CHOICES = [
        ("RESOLVED", _("Resolved")),
        ("PARTIALLY_RESOLVED", _("Partially Resolved")),
        ("UNRESOLVED", _("Unresolved")),
        ("REFERRED", _("Referred to altro")),
        ("WITHDRAWN", _("Withdrawn")),
    ]
    
    complaint_type = models.CharField(
        _("Complaint type"),
        max_length=20,
        choices=COMPLAINT_TYPE_CHOICES,
    )
    
    title = models.CharField(_("Complaint title"), max_length=200)
    description = models.TextField(_("Complaint description"))
    date_received = models.DateTimeField(_("Date and time received"), auto_now_add=True)
    
    complainant_name = models.CharField(_("Complainant name"), max_length=200, blank=True)
    complainant_contact = models.CharField(_("Complainant contact"), max_length=200, blank=True)
    complainant_is_anonymous = models.BooleanField(_("Complainant is anonymous"), default=False)
    
    # Related to service/programme if applicable
    programme = models.CharField(_("Related programme"), max_length=200, blank=True)
    service_location = models.CharField(_("Service location"), max_length=200, blank=True)
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
    investigation_start_date = models.DateTimeField(_("Investigation start date"), null=True, blank=True)
    investigation_end_date = models.DateTimeField(_("Investigation end date"), null=True, blank=True)
    
    resolution_type = models.CharField(
        _("Resolution type"),
        max_length=20,
        choices=RESOLUTION_TYPE_CHOICES,
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
        
    def __str__(self) -> str:
        return f"{self.title} ({self.complaint_type})"


class WhistleblowerReport(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, StatusModel):
    """Confidential whistleblower reporting."""
    
    REPORT_TYPE_CHOICES = [
        ("FRAUD", _("Fraud")),
        ("CORRUPTION", _("Corruption")),
        ("SAFEGUARDING", _("Safeguarding")),
        ("ETHICS_VIOLATION", _("Ethics Violation")),
        ("POLICY_VIOLATION", _("Policy Violation")),
        ("FINANCIAL_MISMANAGEMENT", _("Financial Mismanagement")),
        ("OTHER", _("Other")),
    ]
    
    report_type = models.CharField(
        _("Report type"),
        max_length=25,
        choices=REPORT_TYPE_CHOICES,
    )
    
    title = models.CharField(_("Report title"), max_length=200)
    description = models.TextField(_("Report description"))
    date_reported = models.DateTimeField(_("Date and time reported"), auto_now_add=True)
    
    # Whistleblower identity protection
    reporter_is_anonymous = models.BooleanField(_("Reporter is anonymous"), default=True)
    reporter_name = models.CharField(_("Reporter name (if known)"), max_length=200, blank=True)
    reporter_contact = models.CharField(_("Reporter contact (if known)"), max_length=200, blank=True)
    reporter_relationship = models.CharField(_("Reporter relationship to organization"), max_length=100, blank=True)
    
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
    investigation_start_date = models.DateTimeField(_("Investigation start date"), null=True, blank=True)
    investigation_end_date = models.DateTimeField(_("Investigation end date"), null=True, blank=True)
    
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
        default="HIGHLY_CONFIDENTIAL",
        editable=False,
    )
    
    class Meta:
        verbose_name = _("Whistleblower Report")
        verbose_name_plural = _("Whistleblower Reports")
        
    def save(self, *args, **kwargs):
        # Whistleblower reports are always highly confidential
        if not self.confidentiality_level:
            self.confidentiality_level = "HIGHLY_CONFIDENTIAL"
        super().save(*args, **kwargs)
        
    def __str__(self) -> str:
        reporter_info = "Anonymous" if self.reporter_is_anonymous else self.reporter_name
        return f"{self.title} - Reporter: {reporter_info}"


class CorrectivePreventiveAction(UUIDModel, TimeStampedModel):
    """Corrective and Preventive Actions (CAPA)."""
    
    ACTION_TYPE_CHOICES = [
        ("CORRECTIVE", _("Corrective Action")),
        ("PREVENTIVE", _("Preventive Action")),
        ("BOTH", _("Both Corrective and Preventive")),
    ]
    
    action_type = models.CharField(
        _("Action type"),
        max_length=10,
        choices=ACTION_TYPE_CHOICES,
        default="BOTH",
    )
    
    title = models.CharField(_("Action title"), max_length=200)
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
    source_audit_finding = models.CharField(_("Source audit finding"), max_length=200, blank=True)
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
    preventive_action_description = models.TextField(_("Preventive action description"), blank=True)
    
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
    )
    
    class Meta:
        verbose_name = _("Corrective & Preventive Action")
        verbose_name_plural = _("Corrective & Preventive Actions")
        
    def __str__(self) -> str:
        return f"{self.title} ({self.get_action_type_display()})"


class Document(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Document management for governance records."""
    
    DOCUMENT_TYPE_CHOICES = [
        ("POLICY", _("Policy")),
        ("PROCEDURE", _("Procedure")),
        ("GUIDELINE", _("Guideline")),
        ("FORM", _("Form")),
        ("TEMPLATE", _("Template")),
        ("REPORT", _("Report")),
        ("EVIDENCE", _("Evidence")),
        ("INVESTIGATION", _("Investigation Report")),
        ("AUDIT", _("Audit Report")),
        ("LEGAL", _("Legal Document")),
        ("OTHER", _("Other")),
    ]
    
    document_type = models.CharField(
        _("Document type"),
        max_length=15,
        choices=DOCUMENT_TYPE_CHOICES,
        default="OTHER",
    )
    
    title = models.CharField(_("Document title"), max_length=200)
    description = models.TextField(_("Document description"), blank=True)
    file = models.FileField(_("File"), upload_to="governance_documents/")
    file_size = models.PositiveIntegerField(_("File size (bytes)"), null=True, blank=True)
    mime_type = models.CharField(_("MIME type"), max_length=100, blank=True)
    
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    is_current_version = models.BooleanField(_("Is current version"), default=True)
    
    # Access controls
    confidentiality_level = models.CharField(
        _("Confidentiality level"),
        max_length=20,
        choices=GovernanceRecord.CONFIDENTIALITY_CHOICES,
        default="INTERNAL",
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
        return f"{self.title} v{self.version}"


class GovernanceMeeting(GovernanceRecord):
    """Governance meetings management."""
    
    MEETING_TYPE_CHOICES = [
        ("BOARD", _("Board Meeting")),
        ("EXECUTIVE", _("Executive Committee")),
        ("AUDIT", _("Audit Committee")),
        ("RISK", _("Risk Committee")),
        ("COMPLIANCE", _("Compliance Committee")),
        ("SAFEGUARDING", _("Safeguarding Committee")),
        ("ETHICS", _("Ethics Committee")),
        ("OTHER", _("Other Governance Meeting")),
    ]
    
    meeting_type = models.CharField(
        _("Meeting type"),
        max_length=15,
        choices=MEETING_TYPE_CHOICES,
        default="OTHER",
    )

    governance_type = models.CharField(
        _("Governance type"),
        max_length=20,
        choices=GovernanceRecord.GOVERNANCE_TYPE_CHOICES,
        default="GOVERNANCE_MEETING",
    )

    scheduled_date = models.DateTimeField(_("Scheduled date and time"))
    actual_start_time = models.DateTimeField(_("Actual start time"), null=True, blank=True)
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
    
    def save(self, *args, **kwargs):
        if not self.reference_number:
            self.reference_number = f"MEET-{uuid.uuid4().hex.upper()[:8]}"
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Governance Meeting")
        verbose_name_plural = _("Governance Meetings")
        
    def __str__(self) -> str:
        return f"{self.title} - {self.scheduled_date.strftime('%Y-%m-%d %H:%M')}"


class MeetingAttendance(UUIDModel, TimeStampedModel):
    """Tracking of meeting attendance."""
    
    ATTENDANCE_STATUS_CHOICES = [
        ("PRESENT", _("Present")),
        ("ABSENT", _("Absent")),
        ("APOLOGIES", _("Apologies")),
        ("LATE", _("Late")),
        ("LEFT_EARLY", _("Left early")),
    ]
    
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
        choices=ATTENDANCE_STATUS_CHOICES,
        default="ABSENT",
    )
    
    joined_at = models.DateTimeField(_("Joined at"), null=True, blank=True)
    left_at = models.DateTimeField(_("Left at"), null=True, blank=True)
    
    apologies_note = models.TextField(_("Apologies note"), blank=True)
    
    class Meta:
        verbose_name = _("Meeting Attendance")
        verbose_name_plural = _("Meeting Attendances")
        unique_together = ("meeting", "user")
        
    def __str__(self) -> str:
        return f"{self.user.get_full_name()} - {self.meeting.title} ({self.get_attendance_status_display()})"


class GovernanceNotification(UUIDModel, TimeStampedModel):
    """Notifications for governance activities."""
    
    NOTIFICATION_TYPE_CHOICES = [
        ("POLICY_REVIEW_DUE", _("Policy Review Due")),
        ("POLICY_APPROVED", _("Policy Approved")),
        ("RISK_REVIEW_DUE", _("Risk Review Due")),
        ("HIGH_RISK_ALERT", _("High Risk Alert")),
        ("COMPLIANCE_ISSUE_DETECTED", _("Compliance Issue Detected")),
        ("SAFEGUARDING_CASE_ASSIGNED", _("Safeguarding Case Assigned")),
        ("INCIDENT_REPORTED", _("Incident Reported")),
        ("COMPLAINT_RECEIVED", _("Complaint Received")),
        ("WHISTLEBLOWER_REPORT_RECEIVED", _("Whistleblower Report Received")),
        ("CAPA_OVERDUE", _("CAPA Overdue")),
        ("GOVERNANCE_MEETING_REMINDER", _("Governance Meeting Reminder")),
        ("RISK_ASSESSMENT_COMPLETED", _("Risk Assessment Completed")),
        ("COMPLIANCE_ASSESSMENT_COMPLETED", _("Compliance Assessment Completed")),
        ("ETHICS_CASE_RESOLVED", _("Ethics Case Resolved")),
    ]
    
    notification_type = models.CharField(
        _("Notification type"),
        max_length=40,
        choices=NOTIFICATION_TYPE_CHOICES,
    )
    
    title = models.CharField(_("Notification title"), max_length=200)
    message = models.TextField(_("Notification message"))
    
    # Related to specific governance records
    # related_governance_record = models.ForeignKey(
    #     GovernanceRecord,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="notifications",
    #     verbose_name=_("Related governance record"),
    # )
    
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
    
    TIMELINE_EVENT_TYPE_CHOICES = [
        ("RECORD_CREATED", _("Governance Record Created")),
        ("POLICY_APPROVED", _("Policy Approved")),
        ("RISK_IDENTIFIED", _("Risk Identified")),
        ("RISK_ASSESSED", _("Risk Assessed")),
        ("COMPLIANCE_REVIEW_COMPLETED", _("Compliance Review Completed")),
        ("SAFEGUARDING_CASE_OPENED", _("Safeguarding Case Opened")),
        ("INCIDENT_REPORTED", _("Incident Reported")),
        ("COMPLAINT_RECEIVED", _("Complaint Received")),
        ("WHISTLEBLOWER_REPORT_SUBMITTED", _("Whistleblower Report Submitted")),
        ("CAPA_INITIATED", _("CAPA Initiated")),
        ("GOVERNANCE_RECORD_ARCHIVED", _("Governance Record Archived")),
        ("MEETING_HELD", _("Governance Meeting Held")),
        ("DECISION_MADE", _("Decision Made")),
    ]
    
    event_type = models.CharField(
        _("Event type"),
        max_length=30,
        choices=TIMELINE_EVENT_TYPE_CHOICES,
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
    
    # Related governance record
    # related_governance_record = models.ForeignKey(
    #     GovernanceRecord,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name="timeline_events",
    #     verbose_name=_("Related governance record"),
    # )
    
    # Additional metadata
    module = models.CharField(_("Module"), max_length=50, blank=True)
    reference_number = models.CharField(_("Reference number"), max_length=50, blank=True)
    action_performed = models.CharField(_("Action performed"), max_length=100, blank=True)
    status_after_event = models.CharField(_("Status after event"), max_length=50, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    
    class Meta:
        verbose_name = _("Governance Timeline Event")
        verbose_name_plural = _("Governance Timeline Events")
        ordering = ["-event_date"]
        
    def __str__(self) -> str:
        return f"{self.event_type} - {self.event_date.strftime('%Y-%m-%d %H:%M')}"