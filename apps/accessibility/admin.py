"""Admin registration for Accessibility Review models."""

from django.contrib import admin

from .models import (
    AccessibilityAnalytics,
    AccessibilityApproval,
    AccessibilityAudit,
    AccessibilityComplianceRecord,
    AccessibilityConfiguration,
    AccessibilityException,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityNotification,
    AccessibilityPolicy,
    AccessibilityPreference,
    AccessibilityRecommendation,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
    WCAGCriterion,
)


@admin.register(AccessibilityStandardRecord)
class AccessibilityStandardRecordAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "standard_type", "version", "target_level", "is_active", "effective_date")
    list_filter = ("standard_type", "target_level", "is_active")
    search_fields = ("name", "code", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "effective_date"


@admin.register(AccessibilityPolicy)
class AccessibilityPolicyAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "category", "standard", "version", "is_active", "effective_date")
    list_filter = ("category", "standard", "is_active")
    search_fields = ("reference_number", "title", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "effective_date"
    raw_id_fields = ("approved_by",)


@admin.register(AccessibilityConfiguration)
class AccessibilityConfigurationAdmin(admin.ModelAdmin):
    list_display = ("key", "target_wcag_level", "enable_high_contrast", "enable_font_scaling", "auto_scan_enabled")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("General", {"fields": ("key", "default_standard", "target_wcag_level")}),
        ("UI Settings", {"fields": ("enable_high_contrast", "enable_font_scaling", "enable_reduced_motion", "enable_focus_indicators", "enable_skip_links")}),
        ("Scanning", {"fields": ("auto_scan_enabled", "scan_schedule_cron", "scan_modules")}),
        ("Notifications", {"fields": ("notify_on_critical", "notify_on_regression", "notification_recipients")}),
        ("Reporting", {"fields": ("report_retention_days", "include_in_dashboard")}),
    )


@admin.register(AccessibilityPreference)
class AccessibilityPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "font_size", "colour_theme", "high_contrast", "reduced_motion", "enhanced_focus")
    list_filter = ("font_size", "high_contrast", "reduced_motion", "enhanced_focus")
    search_fields = ("user__username", "user__email", "user__first_name", "user__last_name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "last_synced_at")
    raw_id_fields = ("user",)


@admin.register(WCAGCriterion)
class WCAGCriterionAdmin(admin.ModelAdmin):
    list_display = ("guideline_number", "criterion_number", "title", "principle", "level", "category", "is_active")
    list_filter = ("standard", "principle", "level", "category", "is_active")
    search_fields = ("guideline_number", "criterion_number", "title", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    raw_id_fields = ("standard",)


@admin.register(AccessibilityAudit)
class AccessibilityAuditAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "name", "audit_type", "scope", "module", "status", "overall_score", "auditor", "completed_at")
    list_filter = ("audit_type", "scope", "status", "target_level", "standard")
    search_fields = ("reference_number", "name", "module", "component", "summary")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "overall_score")
    date_hierarchy = "created_at"
    raw_id_fields = ("auditor", "standard")
    inlines = []


class AccessibilityFindingInline(admin.TabularInline):
    model = AccessibilityFinding
    extra = 0
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    raw_id_fields = ("criterion", "assigned_to", "resolved_by", "verified_by")
    fields = ("criterion", "component", "severity", "status", "compliance_status", "assigned_to", "due_date")


@admin.register(AccessibilityFinding)
class AccessibilityFindingAdmin(admin.ModelAdmin):
    list_display = ("audit", "criterion", "component", "severity", "status", "compliance_status", "assigned_to", "due_date")
    list_filter = ("severity", "status", "compliance_status", "audit__audit_type")
    search_fields = ("audit__reference_number", "criterion__title", "component", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "resolved_at", "verified_at")
    raw_id_fields = ("audit", "criterion", "assigned_to", "resolved_by", "verified_by")
    date_hierarchy = "created_at"


@admin.register(AccessibilityIssue)
class AccessibilityIssueAdmin(admin.ModelAdmin):
    list_display = ("reference_number", "title", "source", "module", "component", "severity", "status", "reporter", "assigned_to", "due_date")
    list_filter = ("source", "severity", "status", "is_regression")
    search_fields = ("reference_number", "title", "module", "component", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "resolved_at")
    raw_id_fields = ("criterion", "reporter", "assigned_to", "resolved_by", "regression_from")
    date_hierarchy = "created_at"


@admin.register(AccessibilityRecommendation)
class AccessibilityRecommendationAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "status", "estimated_effort", "implemented_at")
    list_filter = ("priority", "status")
    search_fields = ("title", "description", "rationale")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "implemented_at")
    raw_id_fields = ("implemented_by",)
    filter_horizontal = ("related_criteria",)


@admin.register(AccessibilityNotification)
class AccessibilityNotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "title", "recipient", "is_read", "sent_at", "created_at")
    list_filter = ("event_type", "is_read", "sent_via_email")
    search_fields = ("title", "message", "recipient__username")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "sent_at", "read_at")
    raw_id_fields = ("recipient", "related_audit", "related_finding", "related_issue")
    date_hierarchy = "created_at"


@admin.register(AccessibilityTimeline)
class AccessibilityTimelineAdmin(admin.ModelAdmin):
    list_display = ("event_type", "description", "performed_by", "module", "component", "reference_number", "event_date")
    list_filter = ("event_type", "module", "severity")
    search_fields = ("description", "reference_number", "module", "component")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "event_date", "performed_by", "module", "component", "reference_number", "wcag_criterion", "severity", "status_before", "status_after", "metadata")
    date_hierarchy = "event_date"
    raw_id_fields = ("performed_by",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AccessibilityAnalytics)
class AccessibilityAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("snapshot_date", "module", "overall_compliance_score", "total_issues", "critical_issues", "avg_resolution_days")
    list_filter = ("module",)
    search_fields = ("module",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    date_hierarchy = "snapshot_date"


@admin.register(AccessibilityComplianceRecord)
class AccessibilityComplianceRecordAdmin(admin.ModelAdmin):
    list_display = ("module", "component", "compliance_status", "target_level", "last_tested", "open_findings", "critical_findings", "exception_granted")
    list_filter = ("compliance_status", "target_level", "exception_granted", "standard")
    search_fields = ("module", "component", "page_url", "notes")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    raw_id_fields = ("standard", "last_audit", "exception_approved_by")
    date_hierarchy = "last_tested"


@admin.register(AccessibilityException)
class AccessibilityExceptionAdmin(admin.ModelAdmin):
    list_display = ("module", "component", "criterion", "is_active", "approved_date", "expires_on", "approved_by")
    list_filter = ("is_active", "approved_date", "criterion__level")
    search_fields = ("module", "component", "reason", "justification")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    raw_id_fields = ("criterion", "approved_by")
    date_hierarchy = "approved_date"


@admin.register(AccessibilityApproval)
class AccessibilityApprovalAdmin(admin.ModelAdmin):
    list_display = ("approval_type", "reference_number", "title", "status", "requested_by", "approved_by", "decision_date")
    list_filter = ("approval_type", "status")
    search_fields = ("reference_number", "title", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "decision_date")
    raw_id_fields = ("requested_by", "approved_by")
    date_hierarchy = "created_at"
