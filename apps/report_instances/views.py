"""View layer for report instances (Phase 20 — Report Management).

Comprehensive views for creating, editing, validating, submitting,
reviewing, approving, returning, rejecting, exporting, and managing reports.
"""

from __future__ import annotations

import json
from contextlib import suppress
from typing import ClassVar

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from apps.reports.constants import ReportStatus
from apps.reports.models import ReportTemplate, TemplateSection

from .exports import export_csv, export_html, export_json, export_pdf, export_xlsx
from .forms import DynamicReportForm
from .permissions import (
    can_approve_report,
    can_archive_report,
    can_create_report,
    can_export_report,
    can_submit_report,
    can_update_report,
    can_validate_report,
    can_view_report,
    can_withdraw_report,
    check_permission,
)
from .selectors import (
    get_all_reports,
    get_approved_reports,
    get_archived_reports,
    get_draft_reports,
    get_overdue_reports,
    get_report_or_404,
    get_report_version_or_404,
    get_reports_pending_review,
    get_submitted_reports,
)
from .services import (
    add_attachment,
    add_comment,
    add_evidence,
    approve_report,
    archive_report,
    assign_report,
    auto_save_report,
    create_report,
    duplicate_report,
    get_report_versions,
    record_export,
    reject_report,
    restore_report,
    resubmit_report,
    return_report,
    save_field_response,
    save_section_response,
    start_review,
    submit_report,
    update_report,
    validate_report,
    withdraw_report,
)

# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------


class ReportCreateForm(forms.Form):
    """Form for creating a new report from a published template."""

    template = forms.ModelChoiceField(
        queryset=ReportTemplate.objects.filter(status="PUBLISHED"),
        label="Template",
    )
    title = forms.CharField(max_length=300, label="Report Title")
    reporting_period = forms.CharField(
        max_length=120, required=False, label="Reporting Period"
    )
    department = forms.CharField(max_length=120, required=False, label="Department")
    confidentiality = forms.ChoiceField(
        choices=[
            ("PUBLIC", "Public"),
            ("INTERNAL", "Internal"),
            ("CONFIDENTIAL", "Confidential"),
            ("RESTRICTED", "Restricted"),
        ],
        initial="INTERNAL",
        label="Confidentiality",
    )
    due_date = forms.DateField(required=False, label="Due Date")
    notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes")


class ReportUpdateForm(forms.Form):
    """Form for updating report metadata."""

    title = forms.CharField(max_length=300, label="Report Title", required=False)
    notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes")
    internal_notes = forms.CharField(
        widget=forms.Textarea, required=False, label="Internal Notes"
    )
    confidentiality = forms.ChoiceField(
        choices=[
            ("PUBLIC", "Public"),
            ("INTERNAL", "Internal"),
            ("CONFIDENTIAL", "Confidential"),
            ("RESTRICTED", "Restricted"),
        ],
        required=False,
        label="Confidentiality",
    )
    due_date = forms.DateField(required=False, label="Due Date")


class CommentForm(forms.Form):
    """Form for adding a comment to a report."""

    body = forms.CharField(widget=forms.Textarea, label="Comment")
    is_internal = forms.BooleanField(
        required=False, initial=False, label="Internal Note"
    )


class ReviewActionForm(forms.Form):
    """Form for review actions (approve, return, reject)."""

    ACTION_CHOICES: ClassVar[list[tuple[str, str]]] = [
        ("approve", "Approve"),
        ("return", "Return for Correction"),
        ("reject", "Reject"),
    ]
    action = forms.ChoiceField(choices=ACTION_CHOICES, label="Action")
    notes = forms.CharField(
        widget=forms.Textarea, required=False, label="Notes / Reason"
    )


class EvidenceForm(forms.Form):
    """Form for uploading evidence."""

    evidence_type = forms.ChoiceField(
        choices=[
            ("PHOTOGRAPH", "Photograph"),
            ("VIDEO", "Video"),
            ("AUDIO", "Audio Recording"),
            ("DOCUMENT", "Document"),
            ("SPREADSHEET", "Spreadsheet"),
            ("PDF", "PDF"),
            ("SIGNED_DOCUMENT", "Signed Document"),
            ("ATTENDANCE_SHEET", "Attendance Sheet"),
            ("FINANCIAL_RECORD", "Financial Record"),
            ("RECEIPT", "Receipt"),
            ("BENEFICIARY_LIST", "Beneficiary List"),
            ("MONITORING_TOOL", "Monitoring Tool"),
            ("EVALUATION_TOOL", "Evaluation Tool"),
            ("GPS_COORDINATES", "GPS Coordinates"),
            ("QR_CODE", "QR Code"),
            ("OTHER", "Other"),
        ],
        label="Evidence Type",
    )
    file = forms.FileField(label="File")
    description = forms.CharField(
        widget=forms.Textarea, required=False, label="Description"
    )


class VideoLinkForm(forms.Form):
    """Form for adding a video link."""

    url = forms.URLField(label="Video URL")
    description = forms.CharField(max_length=500, required=False, label="Description")


class AttachmentForm(forms.Form):
    """Form for uploading a supporting document."""

    file = forms.FileField(label="File")
    description = forms.CharField(max_length=500, required=False, label="Description")


class ExportForm(forms.Form):
    """Form for exporting a report."""

    format = forms.ChoiceField(
        choices=[
            ("PDF", "PDF"),
            ("DOCX", "DOCX"),
            ("XLSX", "XLSX"),
            ("CSV", "CSV"),
            ("HTML", "HTML"),
        ],
        label="Export Format",
    )


class AssignForm(forms.Form):
    """Form for assigning a reviewer."""

    assigned_to = forms.CharField(max_length=100, label="Assign to User ID")
    role = forms.ChoiceField(
        choices=[
            ("REVIEWER", "Reviewer"),
            ("APPROVER", "Approver"),
            ("COLLABORATOR", "Collaborator"),
        ],
        initial="REVIEWER",
        label="Role",
    )
    notes = forms.CharField(widget=forms.Textarea, required=False, label="Notes")


# ---------------------------------------------------------------------------
# Dashboard View
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportDashboardView(View):
    """Report management dashboard with summary widgets."""

    def get(self, request):
        user = request.user
        from django.db.models import Count
        from django.utils import timezone

        from apps.reports.models import ReportCategory

        categories = (
            ReportCategory.objects.filter(is_active=True)
            .annotate(template_count=Count("templates"))
            .order_by("code")
        )

        context = {
            "my_drafts": get_draft_reports(user).count(),
            "my_submitted": get_submitted_reports(user).count(),
            "my_approved": get_approved_reports(user).count(),
            "my_archived": get_archived_reports(user).count(),
            "pending_review": get_reports_pending_review(user).count(),
            "overdue": get_overdue_reports().count(),
            "total_reports": get_all_reports().count(),
            "recent_reports": get_all_reports().select_related(
                "template", "category", "owner"
            )[:10],
            "categories": categories,
            "today": timezone.now().date(),
        }
        return render(request, "report_instances/dashboard.html", context)


# ---------------------------------------------------------------------------
# CRUD Views
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportListView(View):
    """List all reports visible to the current user."""

    def get(self, request):
        if not check_permission(request, "report_instances.view"):
            messages.error(request, "You do not have permission to view reports.")
            return redirect("core:home")

        status_filter = request.GET.get("status", "")
        category_filter = request.GET.get("category", "")
        search_query = request.GET.get("q", "")

        qs = get_all_reports().select_related(
            "template", "category", "owner", "assigned_reviewer"
        )

        if status_filter:
            qs = qs.filter(status=status_filter)
        if category_filter:
            qs = qs.filter(category_id=category_filter)
        if search_query:
            qs = qs.filter(
                models.Q(reference_number__icontains=search_query)
                | models.Q(title__icontains=search_query)
            )

        return render(
            request,
            "report_instances/report_list.html",
            {
                "reports": qs[:100],
                "status_choices": ReportStatus.choices,
                "current_status": status_filter,
                "current_category": category_filter,
                "search_query": search_query,
            },
        )


@method_decorator(login_required, name="dispatch")
class ReportCreateView(View):
    """Create a new report from a published template."""

    def get(self, request):
        if not can_create_report(request):
            messages.error(request, "You do not have permission to create reports.")
            return redirect("report_instances:list")

        form = ReportCreateForm()
        templates = ReportTemplate.objects.filter(status="PUBLISHED")
        return render(
            request,
            "report_instances/report_form.html",
            {
                "form": form,
                "templates": templates,
            },
        )

    def post(self, request):
        if not can_create_report(request):
            messages.error(request, "You do not have permission to create reports.")
            return redirect("report_instances:list")

        form = ReportCreateForm(request.POST)
        if form.is_valid():
            try:
                report = create_report(
                    template=form.cleaned_data["template"],
                    title=form.cleaned_data["title"],
                    owner=request.user,
                    department=form.cleaned_data.get("department", ""),
                    confidentiality=form.cleaned_data.get(
                        "confidentiality", "INTERNAL"
                    ),
                    due_date=form.cleaned_data.get("due_date"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, f"Report '{report.title}' created.")
                return redirect("report_instances:enter_data", pk=report.pk)
            except ValueError as exc:
                messages.error(request, str(exc))

        return render(request, "report_instances/report_form.html", {"form": form})


@method_decorator(login_required, name="dispatch")
class ReportDetailView(View):
    """View report details with all related data."""

    def get(self, request, pk):
        report = get_report_or_404(pk)
        if not can_view_report(request, report):
            messages.error(request, "You do not have permission to view this report.")
            return redirect("report_instances:list")

        timeline = report.timeline_events.select_related("actor").all()[:50]
        comments = report.comments.select_related("author").all()
        versions = report.versions.select_related("author").all()
        section_responses = report.section_responses.select_related("section").all()
        field_responses = report.field_responses.select_related("field").all()
        evidence = report.evidence_items.all()
        attachments = report.attachments.all()
        submissions = report.submissions.select_related("submitted_by").all()
        assignments = report.assignments.select_related("assigned_to").all()
        validation_result = report.validation_results.first()

        return render(
            request,
            "report_instances/report_detail.html",
            {
                "report": report,
                "timeline": timeline,
                "comments": comments,
                "versions": versions,
                "section_responses": section_responses,
                "field_responses": field_responses,
                "evidence": evidence,
                "attachments": attachments,
                "submissions": submissions,
                "assignments": assignments,
                "validation_result": validation_result,
                "comment_form": CommentForm(),
                "evidence_form": EvidenceForm(),
                "attachment_form": AttachmentForm(),
                "export_form": ExportForm(),
                "assign_form": AssignForm(),
                "review_form": ReviewActionForm(),
            },
        )


@method_decorator(login_required, name="dispatch")
class ReportEditView(View):
    """Edit report metadata."""

    def get(self, request, pk):
        report = get_report_or_404(pk)
        if not can_update_report(request, report):
            messages.error(request, "You do not have permission to edit this report.")
            return redirect("report_instances:detail", pk=pk)

        form = ReportUpdateForm(
            initial={
                "title": report.title,
                "notes": report.notes,
                "internal_notes": report.internal_notes,
                "confidentiality": report.confidentiality,
                "due_date": report.due_date,
            }
        )
        return render(
            request,
            "report_instances/report_form.html",
            {
                "report": report,
                "form": form,
            },
        )

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_update_report(request, report):
            messages.error(request, "You do not have permission to edit this report.")
            return redirect("report_instances:detail", pk=pk)

        form = ReportUpdateForm(request.POST)
        if form.is_valid():
            try:
                update_report(
                    report,
                    title=form.cleaned_data.get("title"),
                    notes=form.cleaned_data.get("notes"),
                    internal_notes=form.cleaned_data.get("internal_notes"),
                    confidentiality=form.cleaned_data.get("confidentiality"),
                    due_date=form.cleaned_data.get("due_date"),
                    updated_by=request.user,
                )
                messages.success(request, "Report updated.")
                return redirect("report_instances:detail", pk=pk)
            except ValueError as exc:
                messages.error(request, str(exc))

        return render(
            request,
            "report_instances/report_form.html",
            {
                "report": report,
                "form": form,
            },
        )


# ---------------------------------------------------------------------------
# Data Entry View (Dynamic Form)
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportDataEntryView(View):
    """Dynamic form for entering report data based on template schema."""

    def get(self, request, pk):
        report = get_report_or_404(pk)
        if not can_update_report(request, report):
            messages.error(request, "You do not have permission to edit this report.")
            return redirect("report_instances:detail", pk=pk)

        # Pre-populate form with existing responses
        initial_data = {}
        for fr in report.field_responses.select_related("field").all():
            field_name = f"section_{fr.field.group.section.pk}_field_{fr.field.pk}"
            initial_data[field_name] = fr.value

        form = DynamicReportForm(
            initial=initial_data,
            template_id=report.template_id,
        )

        sections = TemplateSection.objects.filter(template=report.template).order_by(
            "sort_order", "name"
        )

        return render(
            request,
            "report_instances/report_data_entry.html",
            {
                "report": report,
                "form": form,
                "sections": sections,
            },
        )

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_update_report(request, report):
            messages.error(request, "You do not have permission to edit this report.")
            return redirect("report_instances:detail", pk=pk)

        form = DynamicReportForm(
            request.POST,
            request.FILES,
            template_id=report.template_id,
        )

        if form.is_valid():
            # Save all section/field responses
            for section in TemplateSection.objects.filter(template=report.template):
                section_data = form.section_data(str(section.pk))
                if section_data:
                    save_section_response(
                        report, str(section.pk), section_data, updated_by=request.user
                    )
                    for field_pk, value in section_data.items():
                        save_field_response(
                            report, field_pk, value, updated_by=request.user
                        )

            messages.success(request, "Report data saved.")
            return redirect("report_instances:detail", pk=pk)

        sections = TemplateSection.objects.filter(template=report.template).order_by(
            "sort_order", "name"
        )
        return render(
            request,
            "report_instances/report_data_entry.html",
            {
                "report": report,
                "form": form,
                "sections": sections,
            },
        )


# ---------------------------------------------------------------------------
# Lifecycle Actions
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportSubmitView(View):
    """Submit a report for review."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_submit_report(request, report):
            messages.error(request, "You do not have permission to submit this report.")
            return redirect("report_instances:detail", pk=pk)

        notes = request.POST.get("notes", "")
        try:
            submit_report(report, submitted_by=request.user, notes=notes)
            messages.success(request, "Report submitted successfully.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportWithdrawView(View):
    """Withdraw a submitted report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_withdraw_report(request, report):
            messages.error(
                request, "You do not have permission to withdraw this report."
            )
            return redirect("report_instances:detail", pk=pk)

        reason = request.POST.get("reason", "")
        try:
            withdraw_report(report, withdrawn_by=request.user, reason=reason)
            messages.success(request, "Report withdrawn.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportResubmitView(View):
    """Resubmit a returned report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        notes = request.POST.get("notes", "")
        try:
            resubmit_report(report, resubmitted_by=request.user, notes=notes)
            messages.success(request, "Report resubmitted.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportArchiveView(View):
    """Archive a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_archive_report(request):
            messages.error(request, "You do not have permission to archive reports.")
            return redirect("report_instances:detail", pk=pk)

        try:
            archive_report(report, archived_by=request.user)
            messages.success(request, "Report archived.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportRestoreView(View):
    """Restore an archived report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not check_permission(request, "report_instances.restore"):
            messages.error(request, "You do not have permission to restore reports.")
            return redirect("report_instances:detail", pk=pk)

        try:
            restore_report(report, restored_by=request.user)
            messages.success(request, "Report restored.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportDuplicateView(View):
    """Duplicate a report as a new draft."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        new_title = request.POST.get("title", "")
        try:
            new_report = duplicate_report(
                report,
                new_title=new_title or None,
                duplicated_by=request.user,
            )
            messages.success(request, f"Report duplicated as '{new_report.title}'.")
            return redirect("report_instances:detail", pk=new_report.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
            return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportValidateView(View):
    """Run validation against a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_validate_report(request):
            messages.error(request, "You do not have permission to validate reports.")
            return redirect("report_instances:detail", pk=pk)

        try:
            result = validate_report(report, validated_by=request.user)
            if result.is_valid:
                messages.success(request, "Validation passed.")
            else:
                messages.warning(
                    request,
                    f"Validation failed: {result.failed_rules} error(s).",
                )
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# Review Actions (Manager/Approver)
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportReviewView(View):
    """Process review actions (approve, return, reject)."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_approve_report(request):
            messages.error(request, "You do not have permission to review reports.")
            return redirect("report_instances:detail", pk=pk)

        form = ReviewActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            notes = form.cleaned_data.get("notes", "")

            try:
                if action == "approve":
                    approve_report(report, approved_by=request.user, notes=notes)
                    messages.success(request, "Report approved.")
                elif action == "return":
                    return_report(report, returned_by=request.user, reason=notes)
                    messages.success(request, "Report returned for correction.")
                elif action == "reject":
                    reject_report(report, rejected_by=request.user, reason=notes)
                    messages.success(request, "Report rejected.")
            except ValueError as exc:
                messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportStartReviewView(View):
    """Start reviewing a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        try:
            start_review(report, reviewed_by=request.user)
            messages.success(request, "Review started.")
        except ValueError as exc:
            messages.error(request, str(exc))

        return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportCommentView(View):
    """Add a comment to a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        form = CommentForm(request.POST)
        if form.is_valid():
            add_comment(
                report,
                body=form.cleaned_data["body"],
                author=request.user,
                is_internal=form.cleaned_data.get("is_internal", False),
            )
            messages.success(request, "Comment added.")
        return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# Evidence & Attachments
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportEvidenceView(View):
    """Upload evidence to a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        form = EvidenceForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            add_evidence(
                report,
                evidence_type=form.cleaned_data["evidence_type"],
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or "",
                description=form.cleaned_data.get("description", ""),
                uploaded_by=request.user,
            )
            messages.success(request, "Evidence uploaded.")
        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportVideoLinkView(View):
    """Add a video link to a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        form = VideoLinkForm(request.POST)
        if form.is_valid():
            add_evidence(
                report,
                evidence_type="VIDEO",
                file=None,
                original_filename=form.cleaned_data["url"],
                file_size=0,
                description=form.cleaned_data.get("description", ""),
                uploaded_by=request.user,
            )
            messages.success(request, "Video link added.")
        return redirect("report_instances:detail", pk=pk)


@method_decorator(login_required, name="dispatch")
class ReportAttachmentView(View):
    """Upload a supporting document."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.cleaned_data["file"]
            add_attachment(
                report,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                mime_type=uploaded_file.content_type or "",
                description=form.cleaned_data.get("description", ""),
                uploaded_by=request.user,
            )
            messages.success(request, "Attachment uploaded.")
        return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# Version History
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportVersionsView(View):
    """View version history for a report."""

    def get(self, request, pk):
        report = get_report_or_404(pk)
        versions = get_report_versions(report)
        return render(
            request,
            "report_instances/report_versions.html",
            {
                "report": report,
                "versions": versions,
            },
        )


@method_decorator(login_required, name="dispatch")
class ReportVersionDetailView(View):
    """View a specific version snapshot."""

    def get(self, request, pk, version_number):
        report = get_report_or_404(pk)
        version = get_report_version_or_404(pk, version_number)
        return render(
            request,
            "report_instances/report_version_detail.html",
            {
                "report": report,
                "version": version,
            },
        )


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportExportView(View):
    """Export a report in the specified format."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_export_report(request):
            messages.error(request, "You do not have permission to export reports.")
            return redirect("report_instances:detail", pk=pk)

        format_type = request.POST.get("format", "PDF")

        with suppress(Exception):
            record_export(
                report,
                format=format_type,
                file=None,
                exported_by=request.user,
            )

        if format_type == "PDF":
            return export_pdf(report)
        elif format_type == "DOCX":
            return export_html(report)  # Fallback
        elif format_type == "XLSX":
            return export_xlsx(report)
        elif format_type == "CSV":
            return export_csv(report)
        elif format_type == "HTML":
            return export_html(report)
        else:
            return export_json(report)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportPreviewView(View):
    """Preview a report before submission."""

    def get(self, request, pk):
        report = get_report_or_404(pk)
        if not can_view_report(request, report):
            messages.error(request, "You do not have permission to view this report.")
            return redirect("report_instances:list")

        section_responses = report.section_responses.select_related("section").all()
        field_responses = report.field_responses.select_related("field").all()
        evidence = report.evidence_items.all()
        attachments = report.attachments.all()

        return render(
            request,
            "report_instances/report_preview.html",
            {
                "report": report,
                "section_responses": section_responses,
                "field_responses": field_responses,
                "evidence": evidence,
                "attachments": attachments,
            },
        )


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportAssignView(View):
    """Assign a reviewer to a report."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not check_permission(request, "report_instances.assign"):
            messages.error(request, "You do not have permission to assign reports.")
            return redirect("report_instances:detail", pk=pk)

        form = AssignForm(request.POST)
        if form.is_valid():
            from django.contrib.auth import get_user_model

            User = get_user_model()
            try:
                assigned_to = User.objects.get(pk=form.cleaned_data["assigned_to"])
                assign_report(
                    report,
                    assigned_to=assigned_to,
                    assigned_by=request.user,
                    role=form.cleaned_data.get("role", "REVIEWER"),
                    notes=form.cleaned_data.get("notes", ""),
                )
                messages.success(request, "Report assigned.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")

        return redirect("report_instances:detail", pk=pk)


# ---------------------------------------------------------------------------
# API Endpoints (for auto-save, etc.)
# ---------------------------------------------------------------------------


@method_decorator(login_required, name="dispatch")
class ReportAutoSaveView(View):
    """API endpoint for auto-saving report data."""

    def post(self, request, pk):
        report = get_report_or_404(pk)
        if not can_update_report(request, report):
            return JsonResponse({"error": "Permission denied"}, status=403)

        try:
            data = json.loads(request.body)
            auto_save_report(
                report,
                section_data=data.get("sections"),
                field_data=data.get("fields"),
                saved_by=request.user,
            )
            return JsonResponse({"status": "ok", "saved_at": str(timezone.now())})
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)


@method_decorator(login_required, name="dispatch")
class ReportTemplateFieldsView(View):
    """API endpoint to get template fields for dynamic form rendering."""

    def get(self, request, template_id):
        try:
            sections = TemplateSection.objects.filter(template_id=template_id).order_by(
                "sort_order", "name"
            )
            result = []
            for section in sections:
                section_data = {
                    "id": str(section.pk),
                    "name": section.name,
                    "groups": [],
                }
                for group in section.groups.order_by("sort_order", "name"):
                    group_data = {
                        "id": str(group.pk),
                        "name": group.name,
                        "fields": [],
                    }
                    for field in group.fields.order_by("sort_order", "label"):
                        field_data = {
                            "id": str(field.pk),
                            "label": field.label,
                            "type": field.field_type,
                            "required": field.required,
                            "help_text": field.help_text,
                            "options": [
                                {"value": opt.value, "label": opt.label}
                                for opt in field.options.all()
                            ],
                        }
                        group_data["fields"].append(field_data)
                    section_data["groups"].append(group_data)
                result.append(section_data)
            return JsonResponse({"sections": result})
        except Exception as exc:
            return JsonResponse({"error": str(exc)}, status=400)
