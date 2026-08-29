"""Service layer for report instances (Phase 20 — Report Management).

Business logic for creating, updating, validating, submitting, withdrawing,
resubmitting, archiving, restoring, and exporting reports.  Services raise
``ValueError`` for invalid state transitions which the view layer translates
to HTTP 400 responses.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from django.utils import timezone

from apps.reports.constants import (
    ReportStatus,
    ReportValidationStatus,
    SubmissionStatus,
)
from apps.reports.models import (
    DynamicField,
    ReportConfiguration,
    ReportTemplate,
)

# Try to import notification service, but handle gracefully if not available
try:
    from apps.notifications.services import (
        NotificationService,
        EVENT_TYPE_REPORT_SUBMITTED,
        EVENT_TYPE_REPORT_APPROVED,
        EVENT_TYPE_REPORT_RETURNED,
        EVENT_TYPE_REPORT_REJECTED,
    )
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

def _send_report_notification(
    report: Report,
    event_type: str,
    recipient,
    title: str,
    message: str,
    deep_link: str = "",
    action_label: str = "",
    priority: str = "NORMAL",
) -> None:
    """Send a notification for a report workflow event."""
    if not NOTIFICATIONS_AVAILABLE:
        return
    try:
        NotificationService(user=recipient).create_from_event(
            recipient=recipient,
            event_type=event_type,
            payload={
                "title": title,
                "message": message,
                "report_reference": report.reference_number,
                "report_title": report.title,
            },
            source_app="report_instances",
            source_model="Report",
            source_object_id=str(report.pk),
            source_object_reference=report.reference_number,
            deep_link=deep_link,
            action_label=action_label,
            priority_override=priority,
        )
    except Exception:
        # Silently fail - notifications shouldn't break the main workflow
        pass

from .models import (
    Report,
    ReportAssignment,
    ReportAttachment,
    ReportComment,
    ReportEvidence,
    ReportExport,
    ReportFieldResponse,
    ReportReminder,
    ReportSectionResponse,
    ReportStatusHistory,
    ReportSubmission,
    ReportTimelineEvent,
    ReportValidationResult,
    ReportVersion,
)

# ---------------------------------------------------------------------------
# Reference Number Generation
# ---------------------------------------------------------------------------


def _generate_reference_number(template: ReportTemplate) -> str:
    """Generate a unique reference number for a new report."""
    config = ReportConfiguration.load()
    prefix = config.numbering_prefix or "RPT"
    category_code = template.category.code.upper() if template.category else "UNCAT"
    now = timezone.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")
    count = Report.objects.filter(
        template=template,
        created_at__year=now.year,
    ).count()
    seq = count + 1
    return f"{prefix}/{category_code}/{template.code.upper()}/{year}/{month}/{seq:06d}"


# ---------------------------------------------------------------------------
# Snapshot Helpers
# ---------------------------------------------------------------------------


def _build_report_snapshot(report: Report) -> dict[str, Any]:
    """Build a JSON snapshot of the current report state."""
    section_data = {}
    for sr in report.section_responses.select_related("section").all():
        section_data[str(sr.section_id)] = sr.data

    field_data = {}
    for fr in report.field_responses.select_related("field").all():
        field_data[str(fr.field_id)] = fr.value

    return {
        "title": report.title,
        "status": report.status,
        "validation_status": report.validation_status,
        "section_data": section_data,
        "field_data": field_data,
        "notes": report.notes,
    }


# ---------------------------------------------------------------------------
# Timeline Helper
# ---------------------------------------------------------------------------


def _record_timeline_event(
    report: Report,
    event_type: str,
    description: str,
    *,
    actor: Any = None,
    metadata: dict | None = None,
) -> ReportTimelineEvent:
    """Record an immutable timeline event."""
    return ReportTimelineEvent.objects.create(
        report=report,
        event_type=event_type,
        description=description,
        actor=actor,
        metadata=metadata or {},
    )


# ---------------------------------------------------------------------------
# Status History Helper
# ---------------------------------------------------------------------------


def _record_status_change(
    report: Report,
    from_status: str,
    to_status: str,
    action: str,
    *,
    notes: str = "",
    performed_by: Any = None,
) -> ReportStatusHistory:
    """Record an immutable status transition."""
    return ReportStatusHistory.objects.create(
        report=report,
        from_status=from_status,
        to_status=to_status,
        action=action,
        notes=notes,
        performed_by=performed_by,
    )


# ---------------------------------------------------------------------------
# Report Creation
# ---------------------------------------------------------------------------


@transaction.atomic
def create_report(
    *,
    template: ReportTemplate,
    title: str,
    owner: Any,
    reporting_period: Any = None,
    category: Any = None,
    department: str = "",
    program: Any = None,
    confidentiality: str = "INTERNAL",
    due_date: Any = None,
    notes: str = "",
) -> Report:
    """Create a new draft report from a published template.

    The template's current published version is linked at creation time.
    """
    if not template.is_published:
        raise ValueError("Cannot create a report from a non-published template.")

    template_version = template.current_version
    if template_version is None:
        raise ValueError("Template has no published version.")

    ref_number = _generate_reference_number(template)

    report = Report.objects.create(
        reference_number=ref_number,
        title=title,
        template=template,
        template_version=template_version,
        category=category or template.category,
        reporting_period=reporting_period,
        department=department,
        program=program,
        owner=owner,
        status=ReportStatus.DRAFT,
        validation_status=ReportValidationStatus.NOT_VALIDATED,
        confidentiality=confidentiality,
        due_date=due_date,
        notes=notes,
        version_number=1,
    )

    _record_timeline_event(
        report,
        "REPORT_CREATED",
        f"Report '{title}' created from template {template.code}.",
        actor=owner,
    )
    return report


# ---------------------------------------------------------------------------
# Report Update
# ---------------------------------------------------------------------------


@transaction.atomic
def update_report(
    report: Report,
    *,
    title: str | None = None,
    notes: str | None = None,
    internal_notes: str | None = None,
    confidentiality: str | None = None,
    due_date: Any = None,
    updated_by: Any = None,
) -> Report:
    """Update mutable report metadata while in an editable state."""
    if not report.is_editable:
        raise ValueError("Report is not in an editable state.")

    from_status = report.status
    fields_to_update = []

    if title is not None:
        report.title = title
        fields_to_update.append("title")
    if notes is not None:
        report.notes = notes
        fields_to_update.append("notes")
    if internal_notes is not None:
        report.internal_notes = internal_notes
        fields_to_update.append("internal_notes")
    if confidentiality is not None:
        report.confidentiality = confidentiality
        fields_to_update.append("confidentiality")
    if due_date is not None:
        report.due_date = due_date
        fields_to_update.append("due_date")

    if report.status == ReportStatus.DRAFT and fields_to_update:
        report.status = ReportStatus.IN_PROGRESS
        fields_to_update.append("status")
        _record_status_change(
            report,
            from_status,
            ReportStatus.IN_PROGRESS,
            "UPDATED",
            performed_by=updated_by,
        )

    if fields_to_update:
        report.save(update_fields=fields_to_update)
        _record_timeline_event(
            report,
            "REPORT_UPDATED",
            "Report metadata updated.",
            actor=updated_by,
        )

    return report


# ---------------------------------------------------------------------------
# Section / Field Responses
# ---------------------------------------------------------------------------


@transaction.atomic
def save_section_response(
    report: Report,
    section_id: str,
    data: dict[str, Any],
    *,
    updated_by: Any = None,
) -> ReportSectionResponse:
    """Save or update a section response for a report."""
    if not report.is_editable:
        raise ValueError("Report is not in an editable state.")

    from apps.reports.models import TemplateSection

    section = TemplateSection.objects.get(id=section_id)

    section_response, created = ReportSectionResponse.objects.update_or_create(
        report=report,
        section=section,
        defaults={"data": data, "is_complete": True, "completed_at": timezone.now()},
    )

    _record_timeline_event(
        report,
        "SECTION_UPDATED",
        f"Section '{section.name}' response saved.",
        actor=updated_by,
    )
    return section_response


@transaction.atomic
def save_field_response(
    report: Report,
    field_id: str,
    value: Any,
    *,
    updated_by: Any = None,
) -> ReportFieldResponse:
    """Save or update a field response for a report."""
    if not report.is_editable:
        raise ValueError("Report is not in an editable state.")

    from apps.reports.models import DynamicField

    field = DynamicField.objects.get(id=field_id)

    field_response, created = ReportFieldResponse.objects.update_or_create(
        report=report,
        field=field,
        defaults={"value": value, "display_value": str(value) if value else ""},
    )

    return field_response


@transaction.atomic
def store_dynamic_field_upload(
    report: Report,
    field_id: str,
    uploaded_file: Any,
    *,
    uploaded_by: Any = None,
) -> str:
    """Persist an uploaded file for a dynamic file-type report field.

    Returns the storage name that must be recorded as the field response
    value so the JSON response columns remain serializable.
    """
    if not report.is_editable:
        raise ValueError("Report is not in an editable state.")

    from django.core.files.storage import default_storage

    from apps.reports.models import DynamicField

    field = DynamicField.objects.get(id=field_id)

    storage_name = default_storage.save(
        f"report_field_uploads/{report.pk}/{field.pk}/{uploaded_file.name}",
        uploaded_file,
    )
    _record_timeline_event(
        report,
        "FIELD_FILE_UPLOADED",
        f"File '{uploaded_file.name}' uploaded for field '{field.label}'.",
        actor=uploaded_by,
    )
    return storage_name


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@transaction.atomic
def validate_report(
    report: Report,
    *,
    validated_by: Any = None,
) -> ReportValidationResult:
    """Run validation rules against all report responses.

    Returns a ``ReportValidationResult`` with pass/fail and error details.
    """
    from apps.reports.constants import SectionVisibilityMode

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    total_rules = 0
    passed_rules = 0

    # Build a map of existing field responses for quick lookup.
    existing_responses = {
        fr.field_id: fr for fr in report.field_responses.select_related("field").all()
    }

    # Build a map of existing section responses for quick lookup.
    section_responses_map = {sr.section_id: sr for sr in report.section_responses.all()}

    # Determine which sections to validate: only ALWAYS-visible sections
    # and sections that have already been started.
    template_sections = report.template.sections.all()
    sections_to_validate = []
    for section in template_sections:
        sr = section_responses_map.get(section.id)
        if section.visibility_mode == SectionVisibilityMode.ALWAYS or sr is not None:
            sections_to_validate.append(section)

    # Validate required fields that belong to sections being validated.
    sections_to_validate_ids = {s.id for s in sections_to_validate}
    all_required_fields = DynamicField.objects.filter(
        group__section__template=report.template,
        required=True,
        group__section__id__in=sections_to_validate_ids,
    ).select_related("group", "group__section")

    for field in all_required_fields:
        total_rules += 1
        fr = existing_responses.get(field.id)
        if fr is None or (fr.value is None or fr.value == ""):
            errors.append(
                {
                    "field": str(field.id),
                    "field_label": field.label,
                    "section_name": field.group.section.name,
                    "message": f"'{field.label}' is required.",
                }
            )
        else:
            passed_rules += 1

    # Validate that each applicable section is complete.
    for section in sections_to_validate:
        total_rules += 1
        sr = section_responses_map.get(section.id)
        if sr is None or not sr.is_complete:
            errors.append(
                {
                    "section": str(section.id),
                    "section_name": section.name,
                    "message": f"Section '{section.name}' has not been completed.",
                }
            )
        else:
            passed_rules += 1

    is_valid = len(errors) == 0
    validation_status = (
        ReportValidationStatus.PASSED if is_valid else ReportValidationStatus.FAILED
    )

    result = ReportValidationResult.objects.create(
        report=report,
        is_valid=is_valid,
        total_rules=total_rules,
        passed_rules=passed_rules,
        failed_rules=len(errors),
        errors=errors,
        warnings=warnings,
        validated_by=validated_by,
    )

    report.validation_status = validation_status
    report.save(update_fields=["validation_status"])

    from_status = report.status
    if is_valid:
        # Transition to READY_FOR_SUBMISSION if currently in an editable state
        if report.status in (ReportStatus.DRAFT, ReportStatus.IN_PROGRESS, ReportStatus.VALIDATION_FAILED, ReportStatus.RETURNED_FOR_CORRECTION):
            report.status = ReportStatus.READY_FOR_SUBMISSION
        report.save(update_fields=["status"])

        _record_status_change(
            report,
            from_status,
            report.status,
            "VALIDATED",
            performed_by=validated_by,
        )
    else:
        report.status = ReportStatus.VALIDATION_FAILED
        report.save(update_fields=["status"])

        _record_status_change(
            report,
            from_status,
            report.status,
            "VALIDATED",
            performed_by=validated_by,
        )
    _record_timeline_event(
        report,
        "VALIDATION_COMPLETED",
        f"Validation {'passed' if is_valid else 'failed'}: {len(errors)} error(s).",
        actor=validated_by,
        metadata={"is_valid": is_valid, "error_count": len(errors)},
    )

    return result


# ---------------------------------------------------------------------------
# Submission
# ---------------------------------------------------------------------------


@transaction.atomic
def submit_report(
    report: Report,
    *,
    submitted_by: Any,
    notes: str = "",
) -> ReportSubmission:
    """Submit a report for review.

    The report must be in ``READY_FOR_SUBMISSION`` or ``RETURNED_FOR_CORRECTION``
    status.
    """
    allowed_statuses = {
        ReportStatus.READY_FOR_SUBMISSION,
        ReportStatus.RETURNED_FOR_CORRECTION,
    }
    if report.status not in allowed_statuses:
        raise ValueError(
            f"Cannot submit a report in '{report.get_status_display()}' status."
        )

    submission_number = report.submissions.count() + 1
    from_status = report.status

    submission = ReportSubmission.objects.create(
        report=report,
        submitted_by=submitted_by,
        submission_number=submission_number,
        status=SubmissionStatus.SUBMITTED,
        notes=notes,
    )

    # Create version snapshot
    snapshot = _build_report_snapshot(report)
    ReportVersion.objects.create(
        report=report,
        version_number=report.version_number,
        snapshot=snapshot,
        change_summary=f"Submitted (attempt #{submission_number})",
        author=submitted_by,
        status_at_version=ReportStatus.SUBMITTED,
    )

    report.status = ReportStatus.SUBMITTED
    report.submitted_at = timezone.now()
    report.version_number += 1
    report.save(update_fields=["status", "submitted_at", "version_number"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.SUBMITTED,
        "SUBMITTED",
        notes=notes,
        performed_by=submitted_by,
    )
    _record_timeline_event(
        report,
        "REPORT_SUBMITTED",
        f"Report submitted (attempt #{submission_number}).",
        actor=submitted_by,
    )

    # Notify assigned reviewer
    if report.assigned_reviewer:
        _send_report_notification(
            report=report,
            event_type=EVENT_TYPE_REPORT_SUBMITTED,
            recipient=report.assigned_reviewer,
            title=f"Report Submitted for Review: {report.reference_number}",
            message=f"Report '{report.title}' has been submitted for your review.",
            deep_link=f"/report-instances/{report.pk}/",
            action_label="Review Report",
            priority="HIGH",
        )

    return submission


# ---------------------------------------------------------------------------
# Withdrawal
# ---------------------------------------------------------------------------


@transaction.atomic
def withdraw_report(
    report: Report,
    *,
    withdrawn_by: Any,
    reason: str = "",
) -> ReportSubmission:
    """Withdraw a submitted report.

    The most recent submission is marked as withdrawn and the report
    returns to draft status.
    """
    if not report.is_submitted:
        raise ValueError("Only submitted reports can be withdrawn.")

    submission = report.submissions.filter(
        status=SubmissionStatus.SUBMITTED,
    ).first()
    if submission is None:
        raise ValueError("No active submission found to withdraw.")

    from_status = report.status

    submission.status = SubmissionStatus.WITHDRAWN
    submission.withdrawn_at = timezone.now()
    submission.withdrawal_reason = reason
    submission.save(update_fields=["status", "withdrawn_at", "withdrawal_reason"])

    report.status = ReportStatus.DRAFT
    report.submitted_at = None
    report.save(update_fields=["status", "submitted_at"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.DRAFT,
        "WITHDRAWN",
        notes=reason,
        performed_by=withdrawn_by,
    )
    _record_timeline_event(
        report,
        "REPORT_WITHDRAWN",
        f"Report withdrawn: {reason}" if reason else "Report withdrawn.",
        actor=withdrawn_by,
    )

    return submission


# ---------------------------------------------------------------------------
# Resubmission (after return)
# ---------------------------------------------------------------------------


@transaction.atomic
def resubmit_report(
    report: Report,
    *,
    resubmitted_by: Any,
    notes: str = "",
) -> ReportSubmission:
    """Resubmit a report that was returned for correction."""
    if report.status != ReportStatus.RETURNED_FOR_CORRECTION:
        raise ValueError("Only returned reports can be resubmitted.")

    return submit_report(report, submitted_by=resubmitted_by, notes=notes)


# ---------------------------------------------------------------------------
# Archive & Restore
# ---------------------------------------------------------------------------


@transaction.atomic
def archive_report(report: Report, *, archived_by: Any = None) -> Report:
    """Archive an approved or finalized report."""
    allowed = {ReportStatus.APPROVED, ReportStatus.FINALIZED, ReportStatus.SUBMITTED}
    if report.status not in allowed:
        raise ValueError("Report cannot be archived in its current status.")

    from_status = report.status

    report.status = ReportStatus.ARCHIVED
    report.archived_at = timezone.now()
    report.save(update_fields=["status", "archived_at"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.ARCHIVED,
        "ARCHIVED",
        performed_by=archived_by,
    )
    _record_timeline_event(
        report,
        "REPORT_ARCHIVED",
        "Report archived.",
        actor=archived_by,
    )
    return report


@transaction.atomic
def restore_report(report: Report, *, restored_by: Any = None) -> Report:
    """Restore an archived report to its previous status."""
    if report.status != ReportStatus.ARCHIVED:
        raise ValueError("Only archived reports can be restored.")

    # Restore to submitted status (most common case)
    restore_to = ReportStatus.SUBMITTED

    _record_status_change(
        report,
        ReportStatus.ARCHIVED,
        restore_to,
        "RESTORED",
        performed_by=restored_by,
    )

    report.status = restore_to
    report.archived_at = None
    report.save(update_fields=["status", "archived_at"])

    _record_timeline_event(
        report,
        "REPORT_RESTORED",
        "Report restored from archive.",
        actor=restored_by,
    )
    return report


# ---------------------------------------------------------------------------
# Duplication
# ---------------------------------------------------------------------------


@transaction.atomic
def duplicate_report(
    report: Report,
    *,
    new_title: str | None = None,
    new_period: Any = None,
    duplicated_by: Any = None,
) -> Report:
    """Duplicate an existing report as a new draft."""
    return create_report(
        template=report.template,
        title=new_title or f"Copy of {report.title}",
        owner=duplicated_by or report.owner,
        reporting_period=new_period or report.reporting_period,
        category=report.category,
        department=report.department,
        program=report.program,
        confidentiality=report.confidentiality,
        due_date=report.due_date,
    )


# ---------------------------------------------------------------------------
# Evidence Management
# ---------------------------------------------------------------------------


@transaction.atomic
def add_evidence(
    report: Report,
    *,
    evidence_type: str,
    file: Any,
    original_filename: str,
    file_size: int,
    mime_type: str = "",
    description: str = "",
    uploaded_by: Any = None,
    gps_latitude: Any = None,
    gps_longitude: Any = None,
) -> ReportEvidence:
    """Attach evidence to a report."""
    evidence = ReportEvidence.objects.create(
        report=report,
        evidence_type=evidence_type,
        file=file,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=mime_type,
        description=description,
        uploaded_by=uploaded_by,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        captured_at=timezone.now(),
    )

    _record_timeline_event(
        report,
        "EVIDENCE_ADDED",
        f"Evidence '{original_filename}' ({evidence_type}) attached.",
        actor=uploaded_by,
    )
    return evidence


@transaction.atomic
def verify_evidence(
    evidence: ReportEvidence,
    *,
    verified_by: Any,
) -> ReportEvidence:
    """Mark evidence as verified."""
    evidence.is_verified = True
    evidence.verified_by = verified_by
    evidence.verified_at = timezone.now()
    evidence.save(update_fields=["is_verified", "verified_by", "verified_at"])
    return evidence


# ---------------------------------------------------------------------------
# Attachment Management
# ---------------------------------------------------------------------------


@transaction.atomic
def add_attachment(
    report: Report,
    *,
    file: Any,
    original_filename: str,
    file_size: int,
    mime_type: str = "",
    description: str = "",
    uploaded_by: Any = None,
) -> ReportAttachment:
    """Attach a supporting document to a report."""
    attachment = ReportAttachment.objects.create(
        report=report,
        file=file,
        original_filename=original_filename,
        file_size=file_size,
        mime_type=mime_type,
        description=description,
        uploaded_by=uploaded_by,
    )

    _record_timeline_event(
        report,
        "ATTACHMENT_ADDED",
        f"Attachment '{original_filename}' uploaded.",
        actor=uploaded_by,
    )
    return attachment


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@transaction.atomic
def add_comment(
    report: Report,
    *,
    body: str,
    author: Any,
    section: Any = None,
    field: Any = None,
    parent: Any = None,
    is_internal: bool = False,
) -> ReportComment:
    """Add a comment to a report."""
    comment = ReportComment.objects.create(
        report=report,
        body=body,
        author=author,
        section=section,
        field=field,
        parent=parent,
        is_internal=is_internal,
    )

    _record_timeline_event(
        report,
        "COMMENT_ADDED",
        f"Comment added by {author}.",
        actor=author,
    )
    return comment


# ---------------------------------------------------------------------------
# Version History
# ---------------------------------------------------------------------------


def get_report_versions(report: Report) -> list[ReportVersion]:
    """Return all version snapshots for a report, newest first."""
    return list(report.versions.select_related("author").all())


# ---------------------------------------------------------------------------
# Export Tracking
# ---------------------------------------------------------------------------


@transaction.atomic
def record_export(
    report: Report,
    *,
    format: str,
    file: Any,
    exported_by: Any,
) -> ReportExport:
    """Record a report export event."""
    export = ReportExport.objects.create(
        report=report,
        format=format,
        file=file,
        exported_by=exported_by,
    )

    _record_timeline_event(
        report,
        "REPORT_EXPORTED",
        f"Report exported as {format}.",
        actor=exported_by,
    )
    return export


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


@transaction.atomic
def assign_report(
    report: Report,
    *,
    assigned_to: Any,
    assigned_by: Any,
    role: str = "REVIEWER",
    notes: str = "",
) -> ReportAssignment:
    """Assign a reviewer or approver to a report."""
    assignment = ReportAssignment.objects.create(
        report=report,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        role=role,
        notes=notes,
    )

    if role == "REVIEWER":
        report.assigned_reviewer = assigned_to
        report.save(update_fields=["assigned_reviewer"])

    _record_timeline_event(
        report,
        "REPORT_ASSIGNED",
        f"Report assigned to {assigned_to} as {role}.",
        actor=assigned_by,
    )
    return assignment


# ---------------------------------------------------------------------------
# Reminder Scheduling
# ---------------------------------------------------------------------------


@transaction.atomic
def schedule_reminder(
    report: Report,
    *,
    reminder_type: str,
    recipient: Any,
    scheduled_at: Any,
    message: str = "",
) -> ReportReminder:
    """Schedule a reminder for a report."""
    return ReportReminder.objects.create(
        report=report,
        reminder_type=reminder_type,
        recipient=recipient,
        scheduled_at=scheduled_at,
        message=message,
    )


# ---------------------------------------------------------------------------
# Review Actions (Manager/Approver)
# ---------------------------------------------------------------------------


@transaction.atomic
def start_review(
    report: Report,
    *,
    reviewed_by: Any,
) -> Report:
    """Mark a report as under review."""
    if report.status != ReportStatus.SUBMITTED:
        raise ValueError("Only submitted reports can be reviewed.")

    from_status = report.status
    report.status = ReportStatus.UNDER_REVIEW
    report.save(update_fields=["status"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.UNDER_REVIEW,
        "REVIEW_STARTED",
        performed_by=reviewed_by,
    )
    _record_timeline_event(
        report,
        "REVIEW_STARTED",
        f"Review started by {reviewed_by}.",
        actor=reviewed_by,
    )
    return report


@transaction.atomic
def return_report(
    report: Report,
    *,
    returned_by: Any,
    reason: str = "",
) -> Report:
    """Return a report for correction."""
    allowed = {ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW}
    if report.status not in allowed:
        raise ValueError("Only submitted or under-review reports can be returned.")

    from_status = report.status

    # Add a comment with the return reason
    if reason:
        add_comment(
            report,
            body=f"[RETURNED] {reason}",
            author=returned_by,
            is_internal=False,
        )

    report.status = ReportStatus.RETURNED_FOR_CORRECTION
    report.save(update_fields=["status"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.RETURNED_FOR_CORRECTION,
        "RETURNED",
        notes=reason,
        performed_by=returned_by,
    )
    _record_timeline_event(
        report,
        "REPORT_RETURNED",
        (
            f"Report returned for correction: {reason}"
            if reason
            else "Report returned for correction."
        ),
        actor=returned_by,
    )

    # Notify report owner
    if report.owner:
        _send_report_notification(
            report=report,
            event_type=EVENT_TYPE_REPORT_RETURNED,
            recipient=report.owner,
            title=f"Report Returned for Correction: {report.reference_number}",
            message=f"Your report '{report.title}' has been returned for correction by {returned_by}. Reason: {reason}",
            deep_link=f"/report-instances/{report.pk}/",
            action_label="View Corrections",
            priority="HIGH",
        )

    return report


@transaction.atomic
def approve_report(
    report: Report,
    *,
    approved_by: Any,
    notes: str = "",
    is_final_approval: bool = True,
) -> Report:
    """Approve a report.

    If is_final_approval is True (default, e.g., final approver), status goes
    to APPROVED.  Otherwise (e.g., reviewer recommending approval), status
    goes to PENDING_APPROVAL.
    """
    allowed = {ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW, ReportStatus.PENDING_APPROVAL}
    if report.status not in allowed:
        raise ValueError("Only submitted, under-review, or pending-approval reports can be approved.")

    from_status = report.status

    if notes:
        add_comment(
            report,
            body=f"[APPROVED] {notes}",
            author=approved_by,
            is_internal=False,
        )

    report.status = (
        ReportStatus.APPROVED if is_final_approval else ReportStatus.PENDING_APPROVAL
    )
    if is_final_approval:
        report.approved_at = timezone.now()
        report.save(update_fields=["status", "approved_at"])
    else:
        report.save(update_fields=["status"])

    _record_status_change(
        report,
        from_status,
        report.status,
        "APPROVED" if is_final_approval else "RECOMMENDED_APPROVAL",
        notes=notes,
        performed_by=approved_by,
    )
    _record_timeline_event(
        report,
        "REPORT_APPROVED" if is_final_approval else "REPORT_RECOMMENDED_APPROVAL",
        f"Report {'approved' if is_final_approval else 'recommended for approval'} by {approved_by}.",
        actor=approved_by,
    )

    # Notify report owner
    if report.owner:
        _send_report_notification(
            report=report,
            event_type=EVENT_TYPE_REPORT_APPROVED if is_final_approval else EVENT_TYPE_REPORT_RETURNED,
            recipient=report.owner,
            title=f"Report {'Approved' if is_final_approval else 'Recommended for Approval'}: {report.reference_number}",
            message=f"Your report '{report.title}' has been {'approved' if is_final_approval else 'recommended for approval'} by {approved_by}.",
            deep_link=f"/report-instances/{report.pk}/",
            action_label="View Report",
            priority="HIGH" if is_final_approval else "NORMAL",
        )

    return report


@transaction.atomic
def reject_report(
    report: Report,
    *,
    rejected_by: Any,
    reason: str = "",
) -> Report:
    """Reject a report."""
    allowed = {ReportStatus.SUBMITTED, ReportStatus.UNDER_REVIEW}
    if report.status not in allowed:
        raise ValueError("Only submitted or under-review reports can be rejected.")

    from_status = report.status

    if reason:
        add_comment(
            report,
            body=f"[REJECTED] {reason}",
            author=rejected_by,
            is_internal=False,
        )

    report.status = ReportStatus.REJECTED
    report.save(update_fields=["status"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.REJECTED,
        "REJECTED",
        notes=reason,
        performed_by=rejected_by,
    )
    _record_timeline_event(
        report,
        "REPORT_REJECTED",
        (
            f"Report rejected by {rejected_by}: {reason}"
            if reason
            else f"Report rejected by {rejected_by}."
        ),
        actor=rejected_by,
    )

    # Notify report owner
    if report.owner:
        _send_report_notification(
            report=report,
            event_type=EVENT_TYPE_REPORT_REJECTED,
            recipient=report.owner,
            title=f"Report Rejected: {report.reference_number}",
            message=f"Your report '{report.title}' has been rejected by {rejected_by}. Reason: {reason}",
            deep_link=f"/report-instances/{report.pk}/",
            action_label="View Report",
            priority="HIGH",
        )

    return report


@transaction.atomic
def finalize_report(
    report: Report,
    *,
    finalized_by: Any,
) -> Report:
    """Finalize an approved report (mark as complete)."""
    if report.status != ReportStatus.APPROVED:
        raise ValueError("Only approved reports can be finalized.")

    from_status = report.status
    report.status = ReportStatus.FINALIZED
    report.save(update_fields=["status"])

    _record_status_change(
        report,
        from_status,
        ReportStatus.FINALIZED,
        "FINALIZED",
        performed_by=finalized_by,
    )
    _record_timeline_event(
        report,
        "REPORT_FINALIZED",
        f"Report finalized by {finalized_by}.",
        actor=finalized_by,
    )
    return report


# ---------------------------------------------------------------------------
# Auto-Save
# ---------------------------------------------------------------------------


@transaction.atomic
def auto_save_report(
    report: Report,
    *,
    section_data: dict[str, dict[str, Any]] | None = None,
    field_data: dict[str, Any] | None = None,
    saved_by: Any = None,
) -> Report:
    """Auto-save report data without changing status.

    This is used by the auto-save API endpoint to preserve user progress.
    """
    if not report.is_editable:
        return report

    # Save section responses
    if section_data:
        for section_pk, data in section_data.items():
            save_section_response(report, section_pk, data, updated_by=saved_by)

    # Save field responses
    if field_data:
        for field_pk, value in field_data.items():
            save_field_response(report, field_pk, value, updated_by=saved_by)

    return report
