"""Admin configuration for report instances."""

from django.contrib import admin

from .models import (
    Report,
    ReportAssignment,
    ReportAttachment,
    ReportComment,
    ReportEvidence,
    ReportExport,
    ReportReminder,
    ReportSubmission,
    ReportTimelineEvent,
    ReportValidationResult,
    ReportVersion,
)


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "title",
        "status",
        "validation_status",
        "category",
        "owner",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "validation_status", "category", "confidentiality")
    search_fields = ("reference_number", "title", "notes")
    readonly_fields = (
        "reference_number",
        "created_at",
        "updated_at",
        "submitted_at",
        "approved_at",
        "archived_at",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("template", "template_version", "category", "owner", "assigned_reviewer")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            "template", "category", "owner", "assigned_reviewer"
        )


@admin.register(ReportVersion)
class ReportVersionAdmin(admin.ModelAdmin):
    list_display = ("report", "version_number", "status_at_version", "author", "created_at")
    list_filter = ("status_at_version",)
    search_fields = ("report__reference_number", "report__title")
    readonly_fields = (
        "report",
        "version_number",
        "snapshot",
        "change_summary",
        "author",
        "status_at_version",
        "created_at",
    )
    ordering = ("-created_at",)
    raw_id_fields = ("report", "author")


@admin.register(ReportSubmission)
class ReportSubmissionAdmin(admin.ModelAdmin):
    list_display = ("report", "submission_number", "status", "submitted_by", "submitted_at")
    list_filter = ("status",)
    search_fields = ("report__reference_number",)
    readonly_fields = ("submitted_at",)
    ordering = ("-submitted_at",)
    raw_id_fields = ("report", "submitted_by")


@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    list_display = ("report", "author", "is_internal", "is_resolved", "created_at")
    list_filter = ("is_internal", "is_resolved")
    search_fields = ("report__reference_number", "body")
    raw_id_fields = ("report", "section", "field", "parent", "author")
    ordering = ("-created_at",)


@admin.register(ReportAttachment)
class ReportAttachmentAdmin(admin.ModelAdmin):
    list_display = ("report", "original_filename", "file_size", "uploaded_by", "created_at")
    search_fields = ("report__reference_number", "original_filename")
    raw_id_fields = ("report", "uploaded_by")
    ordering = ("-created_at",)


@admin.register(ReportEvidence)
class ReportEvidenceAdmin(admin.ModelAdmin):
    list_display = ("report", "evidence_type", "original_filename", "is_verified", "created_at")
    list_filter = ("evidence_type", "is_verified")
    search_fields = ("report__reference_number", "original_filename")
    raw_id_fields = ("report", "uploaded_by", "verified_by")
    ordering = ("-created_at",)


@admin.register(ReportAssignment)
class ReportAssignmentAdmin(admin.ModelAdmin):
    list_display = ("report", "assigned_to", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("report__reference_number",)
    raw_id_fields = ("report", "assigned_to", "assigned_by")
    ordering = ("-created_at",)


@admin.register(ReportValidationResult)
class ReportValidationResultAdmin(admin.ModelAdmin):
    list_display = ("report", "is_valid", "total_rules", "passed_rules", "failed_rules", "created_at")
    list_filter = ("is_valid",)
    search_fields = ("report__reference_number",)
    raw_id_fields = ("report", "validated_by")
    ordering = ("-created_at",)


@admin.register(ReportTimelineEvent)
class ReportTimelineEventAdmin(admin.ModelAdmin):
    list_display = ("report", "event_type", "actor", "created_at")
    list_filter = ("event_type",)
    search_fields = ("report__reference_number", "description")
    raw_id_fields = ("report", "actor")
    ordering = ("-created_at",)


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ("report", "format", "exported_by", "created_at")
    list_filter = ("format",)
    search_fields = ("report__reference_number",)
    raw_id_fields = ("report", "exported_by")
    ordering = ("-created_at",)


@admin.register(ReportReminder)
class ReportReminderAdmin(admin.ModelAdmin):
    list_display = ("report", "reminder_type", "recipient", "is_sent", "scheduled_at")
    list_filter = ("reminder_type", "is_sent")
    search_fields = ("report__reference_number",)
    raw_id_fields = ("report", "recipient")
    ordering = ("scheduled_at",)
