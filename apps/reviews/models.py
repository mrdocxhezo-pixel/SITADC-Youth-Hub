"""Models for Review and Approval module (Phase 21).

Provides structured, auditable workflows for reviewing, validating,
commenting on, approving, rejecting, returning, escalating, and
digitally signing reports submitted through Report Management.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from typing import NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    CreatedByModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)


class ReviewRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for review domain rows."""

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Review Status & Decision Choices
# ---------------------------------------------------------------------------


class ReviewStatus(models.TextChoices):
    PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT", _("Pending Assignment")
    ASSIGNED = "ASSIGNED", _("Assigned")
    ACCEPTED = "ACCEPTED", _("Accepted")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    AWAITING_CLARIFICATION = "AWAITING_CLARIFICATION", _("Awaiting Clarification")
    EVIDENCE_VERIFICATION = "EVIDENCE_VERIFICATION", _("Evidence Verification")
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED", _("Validation Completed")
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION", _("Returned for Correction")
    RESUBMITTED = "RESUBMITTED", _("Resubmitted")
    APPROVED = "APPROVED", _("Approved")
    CONDITIONALLY_APPROVED = "CONDITIONALLY_APPROVED", _("Conditionally Approved")
    REJECTED = "REJECTED", _("Rejected")
    ESCALATED = "ESCALATED", _("Escalated")
    DELEGATED = "DELEGATED", _("Delegated")
    CLOSED = "CLOSED", _("Closed")


class ReviewDecisionType(models.TextChoices):
    APPROVED = "APPROVED", _("Approved")
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS", _("Approved with Conditions")
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION", _("Returned for Correction")
    REJECTED = "REJECTED", _("Rejected")
    ESCALATED = "ESCALATED", _("Escalated")
    DELEGATED = "DELEGATED", _("Delegated")


class ReviewerRole(models.TextChoices):
    PRIMARY = "PRIMARY", _("Primary Reviewer")
    SECONDARY = "SECONDARY", _("Secondary Reviewer")
    TECHNICAL = "TECHNICAL", _("Technical Reviewer")
    FINANCIAL = "FINANCIAL", _("Financial Reviewer")
    MEAL = "MEAL", _("MEAL Reviewer")
    QA = "QA", _("Quality Assurance Reviewer")
    COMPLIANCE = "COMPLIANCE", _("Compliance Reviewer")
    DIRECTORATE = "DIRECTORATE", _("Directorate Reviewer")
    EXECUTIVE = "EXECUTIVE", _("Executive Reviewer")
    FINAL_APPROVER = "FINAL_APPROVER", _("Final Approver")


class CommentType(models.TextChoices):
    GENERAL = "GENERAL", _("General Comment")
    SECTION = "SECTION", _("Section Comment")
    FIELD = "FIELD", _("Field Comment")
    RECOMMENDATION = "RECOMMENDATION", _("Recommendation")
    REQUIRED_CORRECTION = "REQUIRED_CORRECTION", _("Required Correction")
    CLARIFICATION = "CLARIFICATION", _("Clarification")
    COMPLIANCE = "COMPLIANCE", _("Compliance Observation")
    QUALITY = "QUALITY", _("Quality Observation")
    POSITIVE = "POSITIVE", _("Positive Feedback")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential Note")


class EscalationTrigger(models.TextChoices):
    OVERDUE = "OVERDUE", _("Overdue Review")
    HIGH_RISK = "HIGH_RISK", _("High-Risk Report")
    GOVERNANCE = "GOVERNANCE", _("Governance Exception")
    COMPLIANCE = "COMPLIANCE", _("Compliance Concern")
    FINANCIAL = "FINANCIAL", _("Financial Exception")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding Concern")
    TECHNICAL = "TECHNICAL", _("Technical Dispute")
    CUSTOM = "CUSTOM", _("Custom Trigger")


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


class Review(ReviewRecord, SoftDeleteModel):
    """A review instance tied to a submitted report."""

    report = models.ForeignKey(
        "report_instances.Report",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Report"),
    )
    review_number = models.PositiveIntegerField(_("Review number"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING_ASSIGNMENT,
        db_index=True,
    )
    primary_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="primary_reviews",
        verbose_name=_("Primary reviewer"),
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    decision = models.CharField(
        _("Decision"),
        max_length=30,
        choices=ReviewDecisionType.choices,
        blank=True,
        db_index=True,
    )
    decision_at = models.DateTimeField(_("Decision at"), null=True, blank=True)
    decision_notes = models.TextField(_("Decision notes"), blank=True)
    overall_score = models.DecimalField(
        _("Overall score"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    checklist_completed = models.BooleanField(_("Checklist completed"), default=False)
    evidence_verified = models.BooleanField(_("Evidence verified"), default=False)
    validation_completed = models.BooleanField(_("Validation completed"), default=False)

    class Meta:
        verbose_name = _("Review")
        verbose_name_plural = _("Reviews")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["report", "status"]),
            models.Index(fields=["primary_reviewer", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self) -> str:
        return f"Review #{self.review_number} — {self.report.reference_number}"

    @property
    def is_overdue(self) -> bool:
        if self.due_date and self.status not in (
            ReviewStatus.APPROVED,
            ReviewStatus.REJECTED,
            ReviewStatus.CLOSED,
        ):
            return timezone.now().date() > self.due_date
        return False

    @property
    def duration_days(self) -> int | None:
        if self.started_at:
            end = self.completed_at or timezone.now()
            return (end - self.started_at).days
        return None


# ---------------------------------------------------------------------------
# Review Assignment
# ---------------------------------------------------------------------------


class ReviewAssignment(ReviewRecord):
    """Tracks reviewer assignments for a review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Review"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_assignments",
        verbose_name=_("Assigned to"),
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="review_assignments_made",
        verbose_name=_("Assigned by"),
    )
    role = models.CharField(
        _("Reviewer role"),
        max_length=30,
        choices=ReviewerRole.choices,
        default=ReviewerRole.PRIMARY,
    )
    is_active = models.BooleanField(_("Active"), default=True)
    accepted_at = models.DateTimeField(_("Accepted at"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Review Assignment")
        verbose_name_plural = _("Review Assignments")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["review", "is_active"])]

    def __str__(self) -> str:
        return (
            f"{self.assigned_to} as {self.get_role_display()} "
            f"for Review #{self.review.review_number}"
        )


# ---------------------------------------------------------------------------
# Review Checklist
# ---------------------------------------------------------------------------


class ReviewChecklist(ReviewRecord):
    """A checklist template for review processes."""

    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    category = models.ForeignKey(
        "reports.ReportCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="review_checklists",
        verbose_name=_("Category"),
    )
    is_active = models.BooleanField(_("Active"), default=True)
    is_default = models.BooleanField(_("Default checklist"), default=False)

    class Meta:
        verbose_name = _("Review Checklist")
        verbose_name_plural = _("Review Checklists")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class ReviewChecklistItem(ReviewRecord):
    """An individual item within a review checklist."""

    checklist = models.ForeignKey(
        ReviewChecklist,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("Checklist"),
    )
    label = models.CharField(_("Label"), max_length=300)
    description = models.TextField(_("Description"), blank=True)
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)
    is_required = models.BooleanField(_("Required"), default=True)
    weight = models.DecimalField(
        _("Weight"), max_digits=5, decimal_places=2, default=1.0
    )

    class Meta:
        verbose_name = _("Review Checklist Item")
        verbose_name_plural = _("Review Checklist Items")
        ordering = ("sort_order", "label")

    def __str__(self) -> str:
        return f"{self.checklist.name} — {self.label}"


class ReviewChecklistResponse(ReviewRecord):
    """A reviewer's response to a checklist item for a specific review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="checklist_responses",
        verbose_name=_("Review"),
    )
    item = models.ForeignKey(
        ReviewChecklistItem,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Checklist item"),
    )
    is_completed = models.BooleanField(_("Completed"), default=False)
    score = models.DecimalField(
        _("Score"), max_digits=5, decimal_places=2, null=True, blank=True
    )
    notes = models.TextField(_("Notes"), blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="checklist_item_reviews",
        verbose_name=_("Reviewed by"),
    )

    class Meta:
        verbose_name = _("Checklist Response")
        verbose_name_plural = _("Checklist Responses")
        constraints = [
            models.UniqueConstraint(
                fields=["review", "item"],
                name="review_checklist_response_uniq",
            )
        ]

    def __str__(self) -> str:
        status = "✓" if self.is_completed else "✗"
        return f"{status} {self.item.label}"


# ---------------------------------------------------------------------------
# Review Comment
# ---------------------------------------------------------------------------


class ReviewComment(ReviewRecord):
    """A structured comment on a review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Review"),
    )
    comment_type = models.CharField(
        _("Comment type"),
        max_length=30,
        choices=CommentType.choices,
        default=CommentType.GENERAL,
        db_index=True,
    )
    section = models.ForeignKey(
        "reports.TemplateSection",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_comments",
        verbose_name=_("Section"),
    )
    field = models.ForeignKey(
        "reports.DynamicField",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="review_comments",
        verbose_name=_("Field"),
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Parent comment"),
    )
    body = models.TextField(_("Comment"))
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="review_comments",
        verbose_name=_("Author"),
    )
    is_internal = models.BooleanField(_("Internal note"), default=False)
    is_resolved = models.BooleanField(_("Resolved"), default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_review_comments",
        verbose_name=_("Resolved by"),
    )
    resolved_at = models.DateTimeField(_("Resolved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Review Comment")
        verbose_name_plural = _("Review Comments")
        ordering = ("created_at",)
        indexes = [models.Index(fields=["review", "comment_type"])]

    def __str__(self) -> str:
        return f"{self.get_comment_type_display()} by {self.author}"


# ---------------------------------------------------------------------------
# Review Decision
# ---------------------------------------------------------------------------


class ReviewDecision(ReviewRecord):
    """A formal review decision recorded against a review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="decisions",
        verbose_name=_("Review"),
    )
    decision = models.CharField(
        _("Decision"),
        max_length=30,
        choices=ReviewDecisionType.choices,
        db_index=True,
    )
    reason = models.TextField(_("Decision reason"))
    conditions = models.TextField(_("Conditions"), blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="review_decisions",
        verbose_name=_("Reviewer"),
    )
    decided_at = models.DateTimeField(_("Decided at"), auto_now_add=True)
    signature_data = models.TextField(_("Signature data"), blank=True)
    signature_type = models.CharField(_("Signature type"), max_length=30, blank=True)

    class Meta:
        verbose_name = _("Review Decision")
        verbose_name_plural = _("Review Decisions")
        ordering = ("-decided_at",)

    def __str__(self) -> str:
        return f"{self.get_decision_display()} — Review #{self.review.review_number}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                "Review decisions are immutable.",
                code="immutable_decision",
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            "Review decisions are immutable.",
            code="immutable_decision",
        )


# ---------------------------------------------------------------------------
# Digital Signature
# ---------------------------------------------------------------------------


class DigitalSignature(ReviewRecord):
    """A digital signature applied to a review decision."""

    decision = models.ForeignKey(
        ReviewDecision,
        on_delete=models.CASCADE,
        related_name="signatures",
        verbose_name=_("Decision"),
    )
    signer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="digital_signatures",
        verbose_name=_("Signer"),
    )
    signature_type = models.CharField(
        _("Signature type"),
        max_length=30,
        choices=[
            ("TYPED", _("Typed Signature")),
            ("HANDWRITTEN", _("Handwritten Signature")),
            ("UPLOADED", _("Uploaded Signature Image")),
            ("ELECTRONIC", _("Verified Electronic Signature")),
            ("STAMP", _("Organizational Approval Stamp")),
        ],
    )
    signature_data = models.TextField(_("Signature data"))
    signature_hash = models.CharField(_("Signature hash"), max_length=255, blank=True)
    signed_at = models.DateTimeField(_("Signed at"), auto_now_add=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    is_valid = models.BooleanField(_("Valid"), default=True)

    class Meta:
        verbose_name = _("Digital Signature")
        verbose_name_plural = _("Digital Signatures")
        ordering = ("-signed_at",)

    def __str__(self) -> str:
        return f"Signature by {self.signer} on {self.signed_at}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                "Digital signatures are immutable.",
                code="immutable_signature",
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            "Digital signatures are immutable.",
            code="immutable_signature",
        )


# ---------------------------------------------------------------------------
# Escalation
# ---------------------------------------------------------------------------


class EscalationRecord(ReviewRecord):
    """Tracks escalation of a review to higher authority."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="escalations",
        verbose_name=_("Review"),
    )
    trigger = models.CharField(
        _("Escalation trigger"),
        max_length=30,
        choices=EscalationTrigger.choices,
        db_index=True,
    )
    reason = models.TextField(_("Escalation reason"))
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="escalations_initiated",
        verbose_name=_("Escalated by"),
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="escalations_received",
        verbose_name=_("Escalated to"),
    )
    escalated_at = models.DateTimeField(_("Escalated at"), auto_now_add=True)
    resolved_at = models.DateTimeField(_("Resolved at"), null=True, blank=True)
    resolution_notes = models.TextField(_("Resolution notes"), blank=True)
    is_resolved = models.BooleanField(_("Resolved"), default=False)

    class Meta:
        verbose_name = _("Escalation Record")
        verbose_name_plural = _("Escalation Records")
        ordering = ("-escalated_at",)

    def __str__(self) -> str:
        return f"Escalation — Review #{self.review.review_number}"


# ---------------------------------------------------------------------------
# Delegation
# ---------------------------------------------------------------------------


class DelegationRecord(ReviewRecord):
    """Tracks delegation of review authority to another reviewer."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="delegations",
        verbose_name=_("Review"),
    )
    delegated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="delegations_made",
        verbose_name=_("Delegated by"),
    )
    delegated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="delegations_received",
        verbose_name=_("Delegated to"),
    )
    reason = models.TextField(_("Delegation reason"))
    delegated_at = models.DateTimeField(_("Delegated at"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires at"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Delegation Record")
        verbose_name_plural = _("Delegation Records")
        ordering = ("-delegated_at",)

    def __str__(self) -> str:
        return (
            f"Delegation from {self.delegated_by} to {self.delegated_to} "
            f"— Review #{self.review.review_number}"
        )

    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


# ---------------------------------------------------------------------------
# SLA Configuration & Events
# ---------------------------------------------------------------------------


class SLAConfiguration(ReviewRecord):
    """Service Level Agreement configuration for reviews."""

    name = models.CharField(_("Name"), max_length=200)
    category = models.ForeignKey(
        "reports.ReportCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sla_configurations",
        verbose_name=_("Category"),
    )
    review_deadline_days = models.PositiveIntegerField(
        _("Review deadline (days)"), default=7
    )
    reminder_days_before = models.PositiveIntegerField(
        _("Reminder days before deadline"), default=2
    )
    escalation_days_after = models.PositiveIntegerField(
        _("Escalation days after deadline"), default=3
    )
    max_extensions = models.PositiveIntegerField(_("Max extensions"), default=2)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("SLA Configuration")
        verbose_name_plural = _("SLA Configurations")
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class SLAEvent(ReviewRecord):
    """Tracks SLA-related events for a review."""

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="sla_events",
        verbose_name=_("Review"),
    )
    sla_config = models.ForeignKey(
        SLAConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        related_name="events",
        verbose_name=_("SLA configuration"),
    )
    event_type = models.CharField(
        _("Event type"),
        max_length=30,
        choices=[
            ("DEADLINE_SET", _("Deadline Set")),
            ("REMINDER_SENT", _("Reminder Sent")),
            ("OVERDUE", _("Overdue")),
            ("ESCALATED", _("Escalated")),
            ("EXTENDED", _("Extended")),
            ("MET", _("SLA Met")),
            ("BREACHED", _("SLA Breached")),
        ],
        db_index=True,
    )
    event_date = models.DateTimeField(_("Event date"), auto_now_add=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("SLA Event")
        verbose_name_plural = _("SLA Events")
        ordering = ("-event_date",)

    def __str__(self) -> str:
        return f"{self.event_type} — Review #{self.review.review_number}"


# ---------------------------------------------------------------------------
# Review Configuration
# ---------------------------------------------------------------------------


class ReviewConfiguration(ReviewRecord):
    """Global review and approval configuration settings."""

    key = models.CharField(_("Key"), max_length=100, unique=True)
    value = models.JSONField(_("Value"))
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Review Configuration")
        verbose_name_plural = _("Review Configurations")
        ordering = ("key",)

    def __str__(self) -> str:
        return f"{self.key}: {self.value}"

    @classmethod
    def get_value(cls, key: str, default=None):
        """Get a configuration value by key."""
        try:
            config = cls.objects.get(key=key)
            return config.value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set_value(cls, key: str, value, description: str = ""):
        """Set a configuration value."""
        config, _ = cls.objects.update_or_create(
            key=key, defaults={"value": value, "description": description}
        )
        return config
