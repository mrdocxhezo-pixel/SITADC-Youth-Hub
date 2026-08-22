"""Models for the Accessibility Review module (Phase 33).

Implements accessibility governance, configuration, user preferences,
audit tracking, issue management, and analytics.
"""

from __future__ import annotations

from typing import NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.accessibility.constants import (
    AccessibilityCategory,
    AccessibilityIssueStatus,
    AccessibilityStandard,
    AuditType,
    ComplianceStatus,
    FontSizeOption,
    NotificationTimingOption,
    SeverityLevel,
    WCAGLevel,
    WCAGPrinciple,
)
from apps.core.models import (
    CreatedByModel,
    IsActiveModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)


class AccessibilityRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Base model for accessibility records with common metadata."""

    class Meta:
        abstract = True


class AccessibilityStandardRecord(AccessibilityRecord, IsActiveModel):
    """An accessibility standard the organization follows (e.g., WCAG 2.2 AA)."""

    name = models.CharField(_("Standard name"), max_length=100)
    code = models.SlugField(_("Code"), max_length=50, unique=True)
    standard_type = models.CharField(
        _("Standard type"),
        max_length=30,
        choices=AccessibilityStandard.choices,
        default=AccessibilityStandard.WCAG_2_2_AA,
    )
    version = models.CharField(_("Version"), max_length=20, default="2.2")
    target_level = models.CharField(
        _("Target conformance level"),
        max_length=10,
        choices=WCAGLevel.choices,
        default=WCAGLevel.AA,
    )
    description = models.TextField(_("Description"), blank=True)
    reference_url = models.URLField(_("Reference URL"), blank=True)
    effective_date = models.DateField(_("Effective date"))
    review_date = models.DateField(_("Next review date"), null=True, blank=True)

    class Meta:
        verbose_name = _("Accessibility Standard")
        verbose_name_plural = _("Accessibility Standards")
        ordering = ("-effective_date",)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_target_level_display()})"

    def clean(self) -> None:
        super().clean()
        if self.review_date and self.effective_date and self.review_date < self.effective_date:
            raise ValidationError(
                {"review_date": _("Review date cannot be before effective date.")}
            )


class AccessibilityPolicy(AccessibilityRecord, IsActiveModel):
    """Organizational accessibility policy."""

    title = models.CharField(_("Policy title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    standard = models.ForeignKey(
        AccessibilityStandardRecord,
        on_delete=models.PROTECT,
        related_name="policies",
        verbose_name=_("Accessibility standard"),
    )
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=AccessibilityCategory.choices,
    )
    description = models.TextField(_("Description"))
    requirements = models.JSONField(_("Requirements"), default=list, blank=True)
    scope = models.TextField(_("Scope"), blank=True)
    exceptions = models.TextField(_("Exceptions"), blank=True)
    version = models.CharField(_("Version"), max_length=20, default="1.0")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_accessibility_policies",
        verbose_name=_("Approved by"),
    )
    approved_date = models.DateField(_("Approved date"), null=True, blank=True)
    effective_date = models.DateField(_("Effective date"))
    review_date = models.DateField(_("Next review date"))

    class Meta:
        verbose_name = _("Accessibility Policy")
        verbose_name_plural = _("Accessibility Policies")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["category", "is_active"])]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title}"

    def clean(self) -> None:
        super().clean()
        if self.review_date and self.effective_date and self.review_date < self.effective_date:
            raise ValidationError(
                {"review_date": _("Review date cannot be before effective date.")}
            )


class AccessibilityConfiguration(AccessibilityRecord, IsActiveModel):
    """Centralized accessibility configuration (singleton)."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    default_standard = models.ForeignKey(
        AccessibilityStandardRecord,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name=_("Default standard"),
    )
    target_wcag_level = models.CharField(
        _("Target WCAG level"),
        max_length=10,
        choices=WCAGLevel.choices,
        default=WCAGLevel.AA,
    )
    # Global UI settings
    enable_high_contrast = models.BooleanField(_("Enable high contrast mode"), default=True)
    enable_font_scaling = models.BooleanField(_("Enable font scaling"), default=True)
    enable_reduced_motion = models.BooleanField(_("Enable reduced motion"), default=True)
    enable_focus_indicators = models.BooleanField(_("Enhanced focus indicators"), default=True)
    enable_skip_links = models.BooleanField(_("Enable skip navigation links"), default=True)
    # Scan settings
    auto_scan_enabled = models.BooleanField(_("Automated scanning enabled"), default=True)
    scan_schedule_cron = models.CharField(
        _("Scan schedule (cron)"), max_length=100, default="0 2 * * *", blank=True
    )
    scan_modules = models.JSONField(_("Modules to scan"), default=list, blank=True)
    # Notification settings
    notify_on_critical = models.BooleanField(_("Notify on critical issues"), default=True)
    notify_on_regression = models.BooleanField(_("Notify on regressions"), default=True)
    notification_recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="accessibility_notifications",
        verbose_name=_("Notification recipients"),
    )
    # Reporting
    report_retention_days = models.PositiveIntegerField(
        _("Report retention (days)"), default=365
    )
    include_in_dashboard = models.BooleanField(_("Include in dashboard"), default=True)

    class Meta:
        verbose_name = _("Accessibility Configuration")
        verbose_name_plural = _("Accessibility Configurations")

    def __str__(self) -> str:
        return "Accessibility Configuration"

    @classmethod
    def load(cls) -> AccessibilityConfiguration:
        return cls.objects.get_or_create(key="default")[0]


class AccessibilityPreference(AccessibilityRecord):
    """User-specific accessibility preferences."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accessibility_preferences",
        verbose_name=_("User"),
    )
    font_size = models.CharField(
        _("Font size"),
        max_length=20,
        choices=FontSizeOption.choices,
        default=FontSizeOption.MEDIUM,
    )
    custom_font_size_px = models.PositiveSmallIntegerField(
        _("Custom font size (px)"), null=True, blank=True
    )
    colour_theme = models.CharField(
        _("Colour theme"),
        max_length=30,
        choices=FontSizeOption.choices,
        default="SYSTEM",
    )
    high_contrast = models.BooleanField(_("High contrast mode"), default=False)
    reduced_motion = models.BooleanField(_("Reduced motion"), default=False)
    enhanced_focus = models.BooleanField(_("Enhanced focus indicators"), default=False)
    keyboard_navigation_enhanced = models.BooleanField(
        _("Enhanced keyboard navigation"), default=False
    )
    screen_reader_optimized = models.BooleanField(
        _("Screen reader optimizations"), default=False
    )
    notification_timing = models.CharField(
        _("Notification display timing"),
        max_length=20,
        choices=NotificationTimingOption.choices,
        default=NotificationTimingOption.DELAYED_5S,
    )
    preferred_language = models.CharField(
        _("Preferred language"), max_length=10, default="en"
    )
    reading_line_height = models.DecimalField(
        _("Line height multiplier"), max_digits=3, decimal_places=2, default=1.5
    )
    reading_letter_spacing = models.DecimalField(
        _("Letter spacing (em)"), max_digits=3, decimal_places=2, default=0.0
    )
    reading_word_spacing = models.DecimalField(
        _("Word spacing (em)"), max_digits=3, decimal_places=2, default=0.0
    )
    sync_across_devices = models.BooleanField(_("Sync across devices"), default=True)
    last_synced_at = models.DateTimeField(_("Last synced"), null=True, blank=True)

    class Meta:
        verbose_name = _("Accessibility Preference")
        verbose_name_plural = _("Accessibility Preferences")

    def __str__(self) -> str:
        return f"Preferences for {self.user.get_full_name()}"

    @classmethod
    def get_or_create_for_user(cls, user) -> AccessibilityPreference:
        return cls.objects.get_or_create(user=user)[0]


class WCAGCriterion(AccessibilityRecord, IsActiveModel):
    """A specific WCAG success criterion."""

    standard = models.ForeignKey(
        AccessibilityStandardRecord,
        on_delete=models.PROTECT,
        related_name="criteria",
        verbose_name=_("Standard"),
    )
    guideline_number = models.CharField(_("Guideline number"), max_length=20)
    criterion_number = models.CharField(_("Criterion number"), max_length=20)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    principle = models.CharField(
        _("Principle"),
        max_length=20,
        choices=WCAGPrinciple.choices,
    )
    level = models.CharField(
        _("Conformance level"),
        max_length=10,
        choices=WCAGLevel.choices,
    )
    category = models.CharField(
        _("Category"),
        max_length=20,
        choices=AccessibilityCategory.choices,
    )
    understanding_url = models.URLField(_("Understanding doc URL"), blank=True)
    techniques_url = models.URLField(_("Techniques doc URL"), blank=True)
    how_to_meet_url = models.URLField(_("How to meet URL"), blank=True)

    class Meta:
        verbose_name = _("WCAG Criterion")
        verbose_name_plural = _("WCAG Criteria")
        ordering = ("guideline_number", "criterion_number")
        constraints = [
            models.UniqueConstraint(
                fields=["standard", "guideline_number", "criterion_number"],
                name="accessibility_wcag_criterion_unique",
            )
        ]

    def __str__(self) -> str:
        return f"{self.guideline_number}.{self.criterion_number} - {self.title}"


class AccessibilityAudit(AccessibilityRecord, IsActiveModel, SoftDeleteModel):
    """An accessibility audit of a module or component."""

    AUDIT_SCOPE_CHOICES = [
        ("MODULE", _("Module")),
        ("COMPONENT", _("Component")),
        ("PAGE", _("Page")),
        ("WORKFLOW", _("Workflow")),
        ("FULL_SITE", _("Full Site")),
    ]

    name = models.CharField(_("Audit name"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    audit_type = models.CharField(
        _("Audit type"),
        max_length=20,
        choices=AuditType.choices,
        default=AuditType.MANUAL,
    )
    scope = models.CharField(_("Scope"), max_length=20, choices=AUDIT_SCOPE_CHOICES)
    module = models.CharField(_("Module"), max_length=100, blank=True)
    component = models.CharField(_("Component"), max_length=200, blank=True)
    page_url = models.CharField(_("Page URL"), max_length=500, blank=True)
    standard = models.ForeignKey(
        AccessibilityStandardRecord,
        on_delete=models.PROTECT,
        related_name="audits",
        verbose_name=_("Standard"),
    )
    target_level = models.CharField(
        _("Target level"),
        max_length=10,
        choices=WCAGLevel.choices,
        default=WCAGLevel.AA,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.NOT_TESTED,
        db_index=True,
    )
    auditor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conducted_audits",
        verbose_name=_("Auditor"),
    )
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    total_criteria_tested = models.PositiveIntegerField(_("Criteria tested"), default=0)
    compliant_count = models.PositiveIntegerField(_("Compliant"), default=0)
    non_compliant_count = models.PositiveIntegerField(_("Non-compliant"), default=0)
    partial_count = models.PositiveIntegerField(_("Partial"), default=0)
    not_applicable_count = models.PositiveIntegerField(_("Not applicable"), default=0)
    overall_score = models.DecimalField(
        _("Overall score (%)"), max_digits=5, decimal_places=2, default=0
    )
    summary = models.TextField(_("Summary"), blank=True)
    recommendations = models.TextField(_("Recommendations"), blank=True)
    report_file = models.FileField(_("Report file"), upload_to="accessibility_reports/", blank=True)

    class Meta:
        verbose_name = _("Accessibility Audit")
        verbose_name_plural = _("Accessibility Audits")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["audit_type", "status"]),
            models.Index(fields=["module", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.name}"

    def save(self, *args, **kwargs) -> None:
        if self.started_at and self.completed_at and not self.total_criteria_tested:
            self.total_criteria_tested = (
                self.compliant_count + self.non_compliant_count + self.partial_count + self.not_applicable_count
            )
        if self.total_criteria_tested > 0:
            self.overall_score = round(
                (self.compliant_count + self.partial_count * 0.5) / self.total_criteria_tested * 100, 2
            )
        super().save(*args, **kwargs)


class AccessibilityFinding(AccessibilityRecord):
    """A specific finding from an accessibility audit."""

    audit = models.ForeignKey(
        AccessibilityAudit,
        on_delete=models.CASCADE,
        related_name="findings",
        verbose_name=_("Audit"),
    )
    criterion = models.ForeignKey(
        WCAGCriterion,
        on_delete=models.PROTECT,
        related_name="findings",
        verbose_name=_("WCAG criterion"),
    )
    component = models.CharField(_("Component"), max_length=200)
    page_url = models.CharField(_("Page URL"), max_length=500, blank=True)
    description = models.TextField(_("Finding description"))
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=SeverityLevel.choices,
        default=SeverityLevel.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AccessibilityIssueStatus.choices,
        default=AccessibilityIssueStatus.OPEN,
        db_index=True,
    )
    compliance_status = models.CharField(
        _("Compliance status"),
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.NON_COMPLIANT,
    )
    code_snippet = models.TextField(_("Code snippet"), blank=True)
    recommended_fix = models.TextField(_("Recommended fix"), blank=True)
    wcag_technique_ref = models.CharField(_("WCAG technique reference"), max_length=100, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_accessibility_findings",
        verbose_name=_("Assigned to"),
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolved at"), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_accessibility_findings",
        verbose_name=_("Resolved by"),
    )
    resolution_notes = models.TextField(_("Resolution notes"), blank=True)
    verified_at = models.DateTimeField(_("Verified at"), null=True, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_accessibility_findings",
        verbose_name=_("Verified by"),
    )

    class Meta:
        verbose_name = _("Accessibility Finding")
        verbose_name_plural = _("Accessibility Findings")
        ordering = ("-severity", "-created_at")
        indexes = [
            models.Index(fields=["audit", "severity"]),
            models.Index(fields=["status", "due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.audit.reference_number} - {self.criterion} - {self.get_severity_display()}"


class AccessibilityIssue(AccessibilityRecord, SoftDeleteModel):
    """An accessibility issue reported outside of formal audits."""

    SOURCE_CHOICES = [
        ("USER_REPORT", _("User Report")),
        ("AUTOMATED_SCAN", _("Automated Scan")),
        ("MANUAL_TESTING", _("Manual Testing")),
        ("REGRESSION", _("Regression")),
        ("EXTERNAL_AUDIT", _("External Audit")),
    ]

    title = models.CharField(_("Issue title"), max_length=200)
    reference_number = models.CharField(
        _("Reference number"), max_length=50, unique=True, db_index=True
    )
    source = models.CharField(_("Source"), max_length=20, choices=SOURCE_CHOICES)
    module = models.CharField(_("Module"), max_length=100, blank=True)
    component = models.CharField(_("Component"), max_length=200)
    page_url = models.CharField(_("Page URL"), max_length=500, blank=True)
    description = models.TextField(_("Description"))
    steps_to_reproduce = models.TextField(_("Steps to reproduce"), blank=True)
    expected_behavior = models.TextField(_("Expected behavior"), blank=True)
    actual_behavior = models.TextField(_("Actual behavior"), blank=True)
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=SeverityLevel.choices,
        default=SeverityLevel.MEDIUM,
        db_index=True,
    )
    criterion = models.ForeignKey(
        WCAGCriterion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="issues",
        verbose_name=_("WCAG criterion"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AccessibilityIssueStatus.choices,
        default=AccessibilityIssueStatus.OPEN,
        db_index=True,
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reported_accessibility_issues",
        verbose_name=_("Reporter"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_accessibility_issues",
        verbose_name=_("Assigned to"),
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolved at"), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_accessibility_issues",
        verbose_name=_("Resolved by"),
    )
    resolution_notes = models.TextField(_("Resolution notes"), blank=True)
    is_regression = models.BooleanField(_("Is regression"), default=False)
    regression_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regressions",
        verbose_name=_("Regression from"),
    )
    tags = models.JSONField(_("Tags"), default=list, blank=True)

    class Meta:
        verbose_name = _("Accessibility Issue")
        verbose_name_plural = _("Accessibility Issues")
        ordering = ("-severity", "-created_at")
        indexes = [
            models.Index(fields=["module", "status"]),
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["source", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} - {self.title}"


class AccessibilityRecommendation(AccessibilityRecord):
    """A recommendation for accessibility improvement."""

    PRIORITY_CHOICES = [
        ("IMMEDIATE", _("Immediate")),
        ("HIGH", _("High")),
        ("MEDIUM", _("Medium")),
        ("LOW", _("Low")),
        ("FUTURE", _("Future Enhancement")),
    ]

    title = models.CharField(_("Recommendation title"), max_length=200)
    description = models.TextField(_("Description"))
    rationale = models.TextField(_("Rationale"), blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=10,
        choices=PRIORITY_CHOICES,
        default=PRIORITY_CHOICES[2][0],
    )
    related_criteria = models.ManyToManyField(
        WCAGCriterion,
        blank=True,
        related_name="recommendations",
        verbose_name=_("Related WCAG criteria"),
    )
    affected_modules = models.JSONField(_("Affected modules"), default=list, blank=True)
    estimated_effort = models.CharField(_("Estimated effort"), max_length=50, blank=True)
    implementation_notes = models.TextField(_("Implementation notes"), blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AccessibilityIssueStatus.choices,
        default=AccessibilityIssueStatus.OPEN,
    )
    implemented_at = models.DateTimeField(_("Implemented at"), null=True, blank=True)
    implemented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="implemented_accessibility_recommendations",
        verbose_name=_("Implemented by"),
    )

    class Meta:
        verbose_name = _("Accessibility Recommendation")
        verbose_name_plural = _("Accessibility Recommendations")
        ordering = ("priority", "-created_at")

    def __str__(self) -> str:
        return self.title


class AccessibilityNotification(AccessibilityRecord):
    """Notifications for accessibility events."""

    EVENT_TYPES = [
        ("CRITICAL_ISSUE", _("Critical Issue Found")),
        ("REGRESSION_DETECTED", _("Regression Detected")),
        ("AUDIT_COMPLETED", _("Audit Completed")),
        ("ISSUE_ASSIGNED", _("Issue Assigned")),
        ("ISSUE_RESOLVED", _("Issue Resolved")),
        ("ISSUE_VERIFIED", _("Issue Verified")),
        ("SCAN_SCHEDULED", _("Scan Scheduled")),
        ("SCAN_COMPLETED", _("Scan Completed")),
        ("REVIEW_DUE", _("Review Due")),
        ("COMPLIANCE_CHANGED", _("Compliance Status Changed")),
    ]

    event_type = models.CharField(_("Event type"), max_length=30, choices=EVENT_TYPES)
    title = models.CharField(_("Title"), max_length=200)
    message = models.TextField(_("Message"))
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accessibility_notifications_received",
        verbose_name=_("Recipient"),
    )
    related_audit = models.ForeignKey(
        AccessibilityAudit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Related audit"),
    )
    related_finding = models.ForeignKey(
        AccessibilityFinding,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Related finding"),
    )
    related_issue = models.ForeignKey(
        AccessibilityIssue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Related issue"),
    )
    is_read = models.BooleanField(_("Is read"), default=False)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)
    sent_via_email = models.BooleanField(_("Sent via email"), default=False)
    sent_via_in_app = models.BooleanField(_("Sent via in-app"), default=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Accessibility Notification")
        verbose_name_plural = _("Accessibility Notifications")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["recipient", "is_read", "created_at"])]

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} - {self.recipient.get_full_name()}"


class AccessibilityTimeline(AccessibilityRecord):
    """Timeline of accessibility activities for audit trail."""

    EVENT_TYPES = [
        ("STANDARD_CREATED", _("Standard Created")),
        ("STANDARD_UPDATED", _("Standard Updated")),
        ("POLICY_CREATED", _("Policy Created")),
        ("POLICY_UPDATED", _("Policy Updated")),
        ("AUDIT_STARTED", _("Audit Started")),
        ("AUDIT_COMPLETED", _("Audit Completed")),
        ("FINDING_CREATED", _("Finding Created")),
        ("FINDING_UPDATED", _("Finding Updated")),
        ("FINDING_RESOLVED", _("Finding Resolved")),
        ("FINDING_VERIFIED", _("Finding Verified")),
        ("ISSUE_REPORTED", _("Issue Reported")),
        ("ISSUE_ASSIGNED", _("Issue Assigned")),
        ("ISSUE_RESOLVED", _("Issue Resolved")),
        ("RECOMMENDATION_CREATED", _("Recommendation Created")),
        ("RECOMMENDATION_IMPLEMENTED", _("Recommendation Implemented")),
        ("CONFIGURATION_CHANGED", _("Configuration Changed")),
        ("PREFERENCE_CHANGED", _("User Preference Changed")),
        ("SCAN_TRIGGERED", _("Automated Scan Triggered")),
        ("SCAN_COMPLETED", _("Automated Scan Completed")),
    ]

    event_type = models.CharField(_("Event type"), max_length=30, choices=EVENT_TYPES)
    description = models.TextField(_("Description"))
    event_date = models.DateTimeField(_("Event date"), default=timezone.now)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accessibility_timeline_events",
        verbose_name=_("Performed by"),
    )
    module = models.CharField(_("Module"), max_length=100, blank=True)
    component = models.CharField(_("Component"), max_length=200, blank=True)
    reference_number = models.CharField(_("Reference number"), max_length=50, blank=True)
    wcag_criterion = models.CharField(_("WCAG criterion"), max_length=50, blank=True)
    severity = models.CharField(
        _("Severity"), max_length=10, choices=SeverityLevel.choices, blank=True
    )
    status_before = models.CharField(_("Status before"), max_length=50, blank=True)
    status_after = models.CharField(_("Status after"), max_length=50, blank=True)
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Accessibility Timeline Event")
        verbose_name_plural = _("Accessibility Timeline Events")
        ordering = ("-event_date",)
        indexes = [
            models.Index(fields=["event_type", "event_date"]),
            models.Index(fields=["module", "event_date"]),
        ]

    def __str__(self) -> str:
        dt = self.event_date.strftime("%Y-%m-%d %H:%M")
        return f"{self.get_event_type_display()} - {dt}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                "Accessibility timeline events are immutable.", code="immutable_timeline"
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            "Accessibility timeline events are immutable.", code="immutable_timeline"
        )


class AccessibilityAnalytics(AccessibilityRecord):
    """Periodic accessibility analytics snapshots."""

    snapshot_date = models.DateField(_("Snapshot date"))
    module = models.CharField(_("Module"), max_length=100, blank=True)
    overall_compliance_score = models.DecimalField(
        _("Overall compliance score (%)"), max_digits=5, decimal_places=2, default=0
    )
    critical_issues = models.PositiveIntegerField(_("Critical issues"), default=0)
    high_issues = models.PositiveIntegerField(_("High issues"), default=0)
    medium_issues = models.PositiveIntegerField(_("Medium issues"), default=0)
    low_issues = models.PositiveIntegerField(_("Low issues"), default=0)
    total_issues = models.PositiveIntegerField(_("Total open issues"), default=0)
    resolved_this_period = models.PositiveIntegerField(_("Resolved this period"), default=0)
    new_this_period = models.PositiveIntegerField(_("New this period"), default=0)
    avg_resolution_days = models.DecimalField(
        _("Average resolution (days)"), max_digits=6, decimal_places=2, default=0
    )
    audit_coverage_percent = models.DecimalField(
        _("Audit coverage (%)"), max_digits=5, decimal_places=2, default=0
    )
    keyboard_test_coverage = models.DecimalField(
        _("Keyboard test coverage (%)"), max_digits=5, decimal_places=2, default=0
    )
    screen_reader_test_coverage = models.DecimalField(
        _("Screen reader test coverage (%)"), max_digits=5, decimal_places=2, default=0
    )
    user_preference_adoption = models.DecimalField(
        _("User preference adoption (%)"), max_digits=5, decimal_places=2, default=0
    )
    regressions_count = models.PositiveIntegerField(_("Regressions"), default=0)

    class Meta:
        verbose_name = _("Accessibility Analytics")
        verbose_name_plural = _("Accessibility Analytics")
        ordering = ("-snapshot_date",)
        constraints = [
            models.UniqueConstraint(
                fields=["snapshot_date", "module"],
                name="accessibility_analytics_unique",
            )
        ]

    def __str__(self) -> str:
        mod = self.module or "Global"
        return f"{mod} - {self.snapshot_date} ({self.overall_compliance_score}%)"


class AccessibilityComplianceRecord(AccessibilityRecord):
    """Record of compliance status for a specific module/component."""

    module = models.CharField(_("Module"), max_length=100)
    component = models.CharField(_("Component"), max_length=200, blank=True)
    page_url = models.CharField(_("Page URL"), max_length=500, blank=True)
    standard = models.ForeignKey(
        AccessibilityStandardRecord,
        on_delete=models.PROTECT,
        related_name="compliance_records",
        verbose_name=_("Standard"),
    )
    target_level = models.CharField(
        _("Target level"),
        max_length=10,
        choices=WCAGLevel.choices,
        default=WCAGLevel.AA,
    )
    compliance_status = models.CharField(
        _("Compliance status"),
        max_length=20,
        choices=ComplianceStatus.choices,
        default=ComplianceStatus.NOT_TESTED,
        db_index=True,
    )
    last_audit = models.ForeignKey(
        AccessibilityAudit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="compliance_records",
        verbose_name=_("Last audit"),
    )
    last_tested = models.DateTimeField(_("Last tested"), null=True, blank=True)
    next_review_due = models.DateField(_("Next review due"), null=True, blank=True)
    open_findings = models.PositiveIntegerField(_("Open findings"), default=0)
    critical_findings = models.PositiveIntegerField(_("Critical findings"), default=0)
    notes = models.TextField(_("Notes"), blank=True)
    exception_granted = models.BooleanField(_("Exception granted"), default=False)
    exception_reason = models.TextField(_("Exception reason"), blank=True)
    exception_expires = models.DateField(_("Exception expires"), null=True, blank=True)
    exception_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_accessibility_exceptions",
        verbose_name=_("Exception approved by"),
    )

    class Meta:
        verbose_name = _("Accessibility Compliance Record")
        verbose_name_plural = _("Accessibility Compliance Records")
        ordering = ("module", "component")
        constraints = [
            models.UniqueConstraint(
                fields=["module", "component", "page_url"],
                name="accessibility_compliance_unique",
            )
        ]

    def __str__(self) -> str:
        comp = self.component or "Global"
        return f"{self.module} / {comp} - {self.get_compliance_status_display()}"


class AccessibilityException(AccessibilityRecord):
    """An approved exception to accessibility requirements."""

    module = models.CharField(_("Module"), max_length=100)
    component = models.CharField(_("Component"), max_length=200, blank=True)
    criterion = models.ForeignKey(
        WCAGCriterion,
        on_delete=models.PROTECT,
        related_name="exceptions",
        verbose_name=_("WCAG criterion"),
    )
    reason = models.TextField(_("Reason for exception"))
    justification = models.TextField(_("Technical/business justification"))
    alternative_provided = models.TextField(_("Alternative provided"), blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_accessibility_exceptions",
        verbose_name=_("Approved by"),
    )
    approved_date = models.DateField(_("Approved date"))
    expires_on = models.DateField(_("Expires on"))
    is_active = models.BooleanField(_("Active"), default=True)
    review_notes = models.TextField(_("Review notes"), blank=True)

    class Meta:
        verbose_name = _("Accessibility Exception")
        verbose_name_plural = _("Accessibility Exceptions")
        ordering = ("-approved_date",)

    def __str__(self) -> str:
        return f"Exception for {self.module}/{self.component} - {self.criterion}"

    def clean(self) -> None:
        super().clean()
        if self.expires_on and self.approved_date and self.expires_on < self.approved_date:
            raise ValidationError(
                {"expires_on": _("Expiry date cannot be before approval date.")}
            )


class AccessibilityApproval(AccessibilityRecord):
    """Approval record for accessibility-related changes."""

    APPROVAL_TYPES = [
        ("AUDIT_REPORT", _("Audit Report")),
        ("POLICY", _("Policy")),
        ("EXCEPTION", _("Exception")),
        ("RELEASE", _("Release Sign-off")),
        ("CONFIGURATION", _("Configuration Change")),
    ]

    approval_type = models.CharField(_("Approval type"), max_length=20, choices=APPROVAL_TYPES)
    reference_number = models.CharField(_("Reference number"), max_length=50)
    title = models.CharField(_("Title"), max_length=200)
    description = models.TextField(_("Description"))
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="requested_accessibility_approvals",
        verbose_name=_("Requested by"),
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_accessibility_approvals",
        verbose_name=_("Approved by"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ("PENDING", _("Pending")),
            ("APPROVED", _("Approved")),
            ("REJECTED", _("Rejected")),
            ("REVISION_REQUESTED", _("Revision Requested")),
        ],
        default="PENDING",
    )
    decision_date = models.DateTimeField(_("Decision date"), null=True, blank=True)
    decision_notes = models.TextField(_("Decision notes"), blank=True)
    conditions = models.TextField(_("Conditions"), blank=True)
    expires_on = models.DateField(_("Expires on"), null=True, blank=True)

    class Meta:
        verbose_name = _("Accessibility Approval")
        verbose_name_plural = _("Accessibility Approvals")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.get_approval_type_display()} - {self.reference_number} ({self.status})"
