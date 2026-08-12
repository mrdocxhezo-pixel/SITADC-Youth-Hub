"""Models for concrete report instances (Phase 20 — Report Management).

A ``Report`` is created from a published ``ReportTemplate`` version.  The
module tracks the full report lifecycle — draft, validation, submission,
review, resubmission, approval, archival — along with evidence, comments,
version history, timeline events, assignments, and export tracking.
"""

from __future__ import annotations

from typing import NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    SoftDeleteModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.reports.constants import (
    ConfidentialityLevel,
    EvidenceType,
    ReportStatus,
    ReportValidationStatus,
    SubmissionStatus,
)
from apps.reports.models import (
    DynamicField,
    FieldGroup,
    ReportCategory,
    ReportingPeriod,
    ReportTemplate,
    ReportTemplateVersion,
    TemplateSection,
    WorkflowStage,
)


class ReportRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for report instance domain rows."""

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Report Instance
# ---------------------------------------------------------------------------


class Report(ReportRecord, SoftDeleteModel, ArchivableModel):
    """A report instance created from a published template version.

    Each report captures the template version snapshot at creation time and
    tracks the full lifecycle from draft through approval and archival.
    """

    reference_number = models.CharField(
        _("Reference number"), max_length=80, unique=True, db_index=True
    )
    title = models.CharField(_("Title"), max_length=300)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.PROTECT,
        related_name="report_instances",
        verbose_name=_("Template"),
    )
    template_version = models.ForeignKey(
        ReportTemplateVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="report_instances",
        verbose_name=_("Template version"),
    )
    category = models.ForeignKey(
        ReportCategory,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="report_instances",
        verbose_name=_("Category"),
    )
    reporting_period = models.ForeignKey(
        ReportingPeriod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instances",
        verbose_name=_("Reporting period"),
    )
    department = models.CharField(
        _("Department / directorate"), max_length=120, blank=True
    )
    program = models.ForeignKey(
        "programs.Program",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instances",
        verbose_name=_("Program"),
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="owned_report_instances",
        verbose_name=_("Owner"),
    )
    assigned_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_report_instances",
        verbose_name=_("Assigned reviewer"),
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=ReportStatus.choices,
        default=ReportStatus.DRAFT,
        db_index=True,
    )
    validation_status = models.CharField(
        _("Validation status"),
        max_length=20,
        choices=ReportValidationStatus.choices,
        default=ReportValidationStatus.NOT_VALIDATED,
        db_index=True,
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    submitted_at = models.DateTimeField(_("Submitted at"), null=True, blank=True)
    approved_at = models.DateTimeField(_("Approved at"), null=True, blank=True)
    archived_at = models.DateTimeField(_("Archived at"), null=True, blank=True)
    version_number = models.PositiveIntegerField(_("Version number"), default=1)
    notes = models.TextField(_("Notes"), blank=True)
    internal_notes = models.TextField(_("Internal notes"), blank=True)
    workflow_stage = models.ForeignKey(
        WorkflowStage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instances",
        verbose_name=_("Workflow stage"),
    )

    class Meta:
        verbose_name = _("Report")
        verbose_name_plural = _("Reports")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["owner", "status"]),
            models.Index(fields=["template", "status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference_number} — {self.title}"

    @property
    def is_draft(self) -> bool:
        return self.status in (ReportStatus.DRAFT, ReportStatus.IN_PROGRESS)

    @property
    def is_submitted(self) -> bool:
        return self.status in (
            ReportStatus.SUBMITTED,
            ReportStatus.UNDER_REVIEW,
            ReportStatus.RESUBMITTED,
        )

    @property
    def is_approved(self) -> bool:
        return self.status in (ReportStatus.APPROVED, ReportStatus.FINALIZED)

    @property
    def is_editable(self) -> bool:
        return self.status in (
            ReportStatus.DRAFT,
            ReportStatus.IN_PROGRESS,
            ReportStatus.VALIDATION_FAILED,
            ReportStatus.RETURNED_FOR_CORRECTION,
        )


# ---------------------------------------------------------------------------
# Report Responses
# ---------------------------------------------------------------------------


class ReportSectionResponse(ReportRecord):
    """A user's response to a specific section within a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="section_responses",
        verbose_name=_("Report"),
    )
    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Section"),
    )
    data = models.JSONField(_("Section response data"), default=dict, blank=True)
    is_complete = models.BooleanField(_("Complete"), default=False)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Section Response")
        verbose_name_plural = _("Section Responses")
        constraints = [
            models.UniqueConstraint(
                fields=["report", "section"],
                name="report_section_response_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.report.reference_number} — {self.section.name}"


class ReportFieldResponse(ReportRecord):
    """A user's response to a specific dynamic field within a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="field_responses",
        verbose_name=_("Report"),
    )
    field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Field"),
    )
    section_response = models.ForeignKey(
        ReportSectionResponse,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="field_responses",
        verbose_name=_("Section response"),
    )
    value = models.JSONField(_("Field value"), null=True, blank=True)
    display_value = models.TextField(_("Display value"), blank=True)
    is_valid = models.BooleanField(_("Valid"), default=True)
    validation_errors = models.JSONField(
        _("Validation errors"), default=list, blank=True
    )

    class Meta:
        verbose_name = _("Field Response")
        verbose_name_plural = _("Field Responses")
        constraints = [
            models.UniqueConstraint(
                fields=["report", "field"],
                name="report_field_response_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.report.reference_number} — {self.field.label}"


class ReportGroupResponse(ReportRecord):
    """A user's response to a repeating group within a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="group_responses",
        verbose_name=_("Report"),
    )
    group = models.ForeignKey(
        FieldGroup,
        on_delete=models.CASCADE,
        related_name="responses",
        verbose_name=_("Group"),
    )
    instance_index = models.PositiveIntegerField(_("Instance index"), default=0)
    data = models.JSONField(_("Group response data"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Group Response")
        verbose_name_plural = _("Group Responses")
        ordering = ("group", "instance_index")
        constraints = [
            models.UniqueConstraint(
                fields=["report", "group", "instance_index"],
                name="report_group_response_uniq",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.report.reference_number} — {self.group.name} "
            f"#{self.instance_index}"
        )


class ReportTableResponse(ReportRecord):
    """A user's response to a table/grid field within a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="table_responses",
        verbose_name=_("Report"),
    )
    table_field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        related_name="table_responses",
        verbose_name=_("Table field"),
    )
    rows = models.JSONField(_("Table rows"), default=list, blank=True)

    class Meta:
        verbose_name = _("Table Response")
        verbose_name_plural = _("Table Responses")
        constraints = [
            models.UniqueConstraint(
                fields=["report", "table_field"],
                name="report_table_response_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.report.reference_number} — {self.table_field.label}"


# ---------------------------------------------------------------------------
# Attachments & Evidence
# ---------------------------------------------------------------------------


class ReportAttachment(ReportRecord):
    """A file attachment (supporting document) attached to a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="attachments",
        verbose_name=_("Report"),
    )
    file = models.FileField(_("File"), upload_to="report_attachments/%Y/%m/")
    original_filename = models.CharField(_("Original filename"), max_length=255)
    file_size = models.PositiveIntegerField(_("File size (bytes)"), default=0)
    mime_type = models.CharField(_("MIME type"), max_length=127, blank=True)
    description = models.CharField(_("Description"), max_length=500, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_instance_attachments",
        verbose_name=_("Uploaded by"),
    )

    class Meta:
        verbose_name = _("Report Attachment")
        verbose_name_plural = _("Report Attachments")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.original_filename} ({self.report.reference_number})"


class ReportEvidence(ReportRecord):
    """An evidence item attached to a report instance (Phase 20 section 24)."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="evidence_items",
        verbose_name=_("Report"),
    )
    evidence_type = models.CharField(
        _("Evidence type"),
        max_length=30,
        choices=EvidenceType.choices,
        db_index=True,
    )
    file = models.FileField(_("File"), upload_to="report_evidence/%Y/%m/")
    original_filename = models.CharField(_("Original filename"), max_length=255)
    file_size = models.PositiveIntegerField(_("File size (bytes)"), default=0)
    mime_type = models.CharField(_("MIME type"), max_length=127, blank=True)
    description = models.TextField(_("Description"), blank=True)
    gps_latitude = models.DecimalField(
        _("GPS latitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    gps_longitude = models.DecimalField(
        _("GPS longitude"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    captured_at = models.DateTimeField(_("Captured at"), null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_instance_evidence",
        verbose_name=_("Uploaded by"),
    )
    is_verified = models.BooleanField(_("Verified"), default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_report_evidence",
        verbose_name=_("Verified by"),
    )
    verified_at = models.DateTimeField(_("Verified at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Report Evidence")
        verbose_name_plural = _("Report Evidence")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["report", "evidence_type"])]

    def __str__(self) -> str:
        return f"{self.get_evidence_type_display()} — {self.report.reference_number}"


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class ReportComment(ReportRecord):
    """A comment on a report, section, or field (Phase 20 section 32)."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Report"),
    )
    section = models.ForeignKey(
        TemplateSection,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_instance_comments",
        verbose_name=_("Section"),
    )
    field = models.ForeignKey(
        DynamicField,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="report_instance_comments",
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
        related_name="report_instance_comments",
        verbose_name=_("Author"),
    )
    is_internal = models.BooleanField(_("Internal note"), default=False)
    is_resolved = models.BooleanField(_("Resolved"), default=False)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_report_instance_comments",
        verbose_name=_("Resolved by"),
    )
    resolved_at = models.DateTimeField(_("Resolved at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Report Comment")
        verbose_name_plural = _("Report Comments")
        ordering = ("created_at",)
        indexes = [models.Index(fields=["report", "created_at"])]

    def __str__(self) -> str:
        return f"Comment by {self.author} on {self.report.reference_number}"


# ---------------------------------------------------------------------------
# Status History & Submissions
# ---------------------------------------------------------------------------


class ReportStatusHistory(ReportRecord):
    """Immutable status transition history for a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name=_("Report"),
    )
    from_status = models.CharField(_("From status"), max_length=40, blank=True)
    to_status = models.CharField(_("To status"), max_length=40)
    action = models.CharField(_("Action"), max_length=40)
    notes = models.TextField(_("Notes"), blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instance_status_changes",
        verbose_name=_("Performed by"),
    )

    class Meta:
        verbose_name = _("Report Status History")
        verbose_name_plural = _("Report Status History")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["report", "created_at"])]

    def __str__(self) -> str:
        return (
            f"{self.report.reference_number}: "
            f"{self.from_status or 'NEW'} -> {self.to_status}"
        )

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                "Report status history records are immutable.",
                code="immutable_history",
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            "Report status history records are immutable.",
            code="immutable_history",
        )


class ReportSubmission(ReportRecord):
    """Tracks a submission or resubmission event for a report."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name=_("Report"),
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="report_instance_submissions",
        verbose_name=_("Submitted by"),
    )
    submission_number = models.PositiveIntegerField(_("Submission number"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
        db_index=True,
    )
    notes = models.TextField(_("Notes"), blank=True)
    submitted_at = models.DateTimeField(_("Submitted at"), auto_now_add=True)
    withdrawn_at = models.DateTimeField(_("Withdrawn at"), null=True, blank=True)
    withdrawal_reason = models.TextField(_("Withdrawal reason"), blank=True)

    class Meta:
        verbose_name = _("Report Submission")
        verbose_name_plural = _("Report Submissions")
        ordering = ("-submitted_at",)
        indexes = [models.Index(fields=["report", "status"])]

    def __str__(self) -> str:
        return (
            f"Submission #{self.submission_number} — " f"{self.report.reference_number}"
        )


# ---------------------------------------------------------------------------
# Version History
# ---------------------------------------------------------------------------


class ReportVersion(ReportRecord):
    """Snapshot of a report at a specific point in time for version history."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Report"),
    )
    version_number = models.PositiveIntegerField(_("Version number"))
    snapshot = models.JSONField(_("Report snapshot"), default=dict)
    change_summary = models.TextField(_("Change summary"), blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_instance_versions",
        verbose_name=_("Author"),
    )
    status_at_version = models.CharField(
        _("Status at version"), max_length=30, blank=True
    )

    class Meta:
        verbose_name = _("Report Version")
        verbose_name_plural = _("Report Versions")
        ordering = ("-version_number",)
        constraints = [
            models.UniqueConstraint(
                fields=["report", "version_number"],
                name="report_instance_version_number_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.report.reference_number} v{self.version_number}"


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


class ReportTimelineEvent(ReportRecord):
    """Immutable activity timeline entry for a report."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="timeline_events",
        verbose_name=_("Report"),
    )
    event_type = models.CharField(_("Event type"), max_length=60, db_index=True)
    description = models.TextField(_("Description"))
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instance_timeline_events",
        verbose_name=_("Actor"),
    )
    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Report Timeline Event")
        verbose_name_plural = _("Report Timeline Events")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["report", "event_type"])]

    def __str__(self) -> str:
        return f"{self.event_type} — {self.report.reference_number}"

    def save(self, *args, **kwargs) -> NoReturn:
        if not self._state.adding:
            raise ValidationError(
                "Report timeline events are immutable.",
                code="immutable_timeline",
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            "Report timeline events are immutable.",
            code="immutable_timeline",
        )


# ---------------------------------------------------------------------------
# Assignments
# ---------------------------------------------------------------------------


class ReportAssignment(ReportRecord):
    """Tracks reviewer/owner assignments for a report."""

    class AssignmentRole(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        REVIEWER = "REVIEWER", _("Reviewer")
        APPROVER = "APPROVER", _("Approver")
        COLLABORATOR = "COLLABORATOR", _("Collaborator")

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name=_("Report"),
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_instance_assignments",
        verbose_name=_("Assigned to"),
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_instance_assignments_made",
        verbose_name=_("Assigned by"),
    )
    role = models.CharField(
        _("Assignment role"),
        max_length=30,
        choices=AssignmentRole.choices,
        default=AssignmentRole.REVIEWER,
    )
    is_active = models.BooleanField(_("Active"), default=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Report Assignment")
        verbose_name_plural = _("Report Assignments")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["report", "is_active"])]

    def __str__(self) -> str:
        return (
            f"{self.assigned_to} as {self.get_role_display()} "
            f"for {self.report.reference_number}"
        )


# ---------------------------------------------------------------------------
# Validation Results
# ---------------------------------------------------------------------------


class ReportValidationResult(ReportRecord):
    """Result of a validation run against a report instance."""

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="validation_results",
        verbose_name=_("Report"),
    )
    is_valid = models.BooleanField(_("Valid"), default=False)
    total_rules = models.PositiveIntegerField(_("Total rules checked"), default=0)
    passed_rules = models.PositiveIntegerField(_("Rules passed"), default=0)
    failed_rules = models.PositiveIntegerField(_("Rules failed"), default=0)
    errors = models.JSONField(_("Validation errors"), default=list, blank=True)
    warnings = models.JSONField(_("Validation warnings"), default=list, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="report_instance_validations",
        verbose_name=_("Validated by"),
    )

    class Meta:
        verbose_name = _("Report Validation Result")
        verbose_name_plural = _("Report Validation Results")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        return f"Validation {status} — {self.report.reference_number}"


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------


class ReportExport(ReportRecord):
    """Tracks an export/download event for a report."""

    class ExportFormat(models.TextChoices):
        PDF = "PDF", _("PDF")
        DOCX = "DOCX", _("DOCX")
        XLSX = "XLSX", _("XLSX")
        CSV = "CSV", _("CSV")
        HTML = "HTML", _("HTML")

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="exports",
        verbose_name=_("Report"),
    )
    format = models.CharField(
        _("Export format"),
        max_length=10,
        choices=ExportFormat.choices,
    )
    file = models.FileField(_("Exported file"), upload_to="report_exports/%Y/%m/")
    exported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="report_instance_exports",
        verbose_name=_("Exported by"),
    )

    class Meta:
        verbose_name = _("Report Export")
        verbose_name_plural = _("Report Exports")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.format} export — {self.report.reference_number}"


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------


class ReportReminder(ReportRecord):
    """A scheduled reminder for a report (due date, overdue, etc.)."""

    class ReminderType(models.TextChoices):
        DUE_SOON = "DUE_SOON", _("Due soon")
        OVERDUE = "OVERDUE", _("Overdue")
        RESUBMISSION = "RESUBMISSION", _("Resubmission needed")
        CUSTOM = "CUSTOM", _("Custom")

    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name="reminders",
        verbose_name=_("Report"),
    )
    reminder_type = models.CharField(
        _("Reminder type"),
        max_length=30,
        choices=ReminderType.choices,
        default=ReminderType.DUE_SOON,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="report_instance_reminders",
        verbose_name=_("Recipient"),
    )
    scheduled_at = models.DateTimeField(_("Scheduled at"))
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    is_sent = models.BooleanField(_("Sent"), default=False)
    message = models.TextField(_("Message"), blank=True)

    class Meta:
        verbose_name = _("Report Reminder")
        verbose_name_plural = _("Report Reminders")
        ordering = ("scheduled_at",)
        indexes = [models.Index(fields=["is_sent", "scheduled_at"])]

    def __str__(self) -> str:
        return (
            f"{self.get_reminder_type_display()} — " f"{self.report.reference_number}"
        )
