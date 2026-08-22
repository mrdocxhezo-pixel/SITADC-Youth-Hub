from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
    ApplicationSettings,
    AuthenticationSettings,
    BackupHistory,
    BackupSchedule,
    BrandingSettings,
    Configuration,
    ConfigurationAuditReference,
    ConfigurationNotification,
    ConfigurationTimeline,
    ConfigurationValue,
    ConfigurationVersion,
    DocumentSettings,
    ExportSettings,
    IntegrationConfiguration,
    MaintenanceWindow,
    NotificationSettings,
    NumberingConfiguration,
    OrganizationSettings,
    RolePermissionConfiguration,
    SecurityPolicy,
    SystemConfigurationDashboard,
    SystemHealthRecord,
    WorkflowConfiguration,
)


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "key",
        "name",
        "category",
        "status",
        "version",
        "confidentiality",
        "organization",
        "effective_date",
        "updated_at",
    )
    list_filter = ("category", "status", "confidentiality", "organization")
    search_fields = ("key", "name", "description")
    readonly_fields = (
        "key",
        "version",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "reviewed_by",
        "reviewed_at",
        "approved_by",
        "approved_at",
        "activated_by",
        "activated_at",
    )
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("category", "key", "name", "description", "organization")},
        ),
        (
            _("Lifecycle"),
            {
                "fields": (
                    "status",
                    "confidentiality",
                    "version",
                    "effective_date",
                    "expiry_date",
                )
            },
        ),
        (
            _("Approval Workflow"),
            {
                "fields": (
                    "reviewed_by",
                    "reviewed_at",
                    "approved_by",
                    "approved_at",
                    "activated_by",
                    "activated_at",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )
    ordering = ("category", "key")


@admin.register(ConfigurationValue)
class ConfigurationValueAdmin(admin.ModelAdmin):
    list_display = (
        "configuration",
        "key",
        "value_preview",
        "is_sensitive",
        "encryption_version",
        "updated_at",
    )
    list_filter = ("configuration__category", "is_sensitive")
    search_fields = ("configuration__key", "key", "description")
    readonly_fields = (
        "encryption_version",
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
    )
    ordering = ("configuration", "key")

    def value_preview(self, obj):
        if obj.is_sensitive:
            return format_html('<span class="text-muted">***ENCRYPTED***</span>')
        import json

        val = json.dumps(obj.value)
        return val[:100] + "..." if len(val) > 100 else val

    value_preview.short_description = _("Value Preview")


@admin.register(ConfigurationVersion)
class ConfigurationVersionAdmin(admin.ModelAdmin):
    list_display = (
        "configuration",
        "version",
        "change_summary",
        "changed_by",
        "is_active_version",
        "created_at",
    )
    list_filter = ("is_active_version", "configuration__category")
    search_fields = ("configuration__key", "change_summary")
    readonly_fields = ("snapshot", "created_at", "created_by")
    ordering = ("configuration", "-version")


@admin.register(ConfigurationTimeline)
class ConfigurationTimelineAdmin(admin.ModelAdmin):
    list_display = ("configuration", "event_type", "user", "created_at")
    list_filter = ("event_type", "configuration__category")
    search_fields = ("configuration__key", "remarks", "user__email")
    readonly_fields = (
        "configuration",
        "event_type",
        "user",
        "previous_value",
        "new_value",
        "remarks",
        "ip_address",
        "user_agent",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"


@admin.register(OrganizationSettings)
class OrganizationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "name",
        "short_name",
        "acronym",
        "email",
        "default_language",
        "currency",
    )
    search_fields = ("name", "short_name", "acronym", "email", "registration_number")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("organization", "name", "short_name", "acronym", "logo")},
        ),
        (_("Mission & Values"), {"fields": ("mission", "vision", "core_values")}),
        (
            _("Registration"),
            {"fields": ("registration_number", "registration_date", "tax_id")},
        ),
        (
            _("Contact Information"),
            {
                "fields": (
                    "physical_address",
                    "postal_address",
                    "phone",
                    "email",
                    "website",
                    "official_email",
                )
            },
        ),
        (
            _("Social & Regional"),
            {
                "fields": (
                    "social_media",
                    "fiscal_year_start",
                    "default_language",
                    "default_timezone",
                    "currency",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "application_name",
        "application_short_name",
        "application_version",
        "system_status",
        "default_language",
    )
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Application Identity"),
            {
                "fields": (
                    "key",
                    "application_name",
                    "application_short_name",
                    "application_version",
                    "system_status",
                )
            },
        ),
        (
            _("Localization"),
            {
                "fields": (
                    "default_language",
                    "default_timezone",
                    "date_format",
                    "time_format",
                    "default_pagination_size",
                )
            },
        ),
        (
            _("Theme & UI"),
            {"fields": ("theme_config", "light_mode_default", "dark_mode_available")},
        ),
        (
            _("Session & Storage"),
            {
                "fields": (
                    "session_timeout_minutes",
                    "file_upload_max_size_mb",
                    "default_storage_path",
                    "default_export_formats",
                )
            },
        ),
        (
            _("Features & Maintenance"),
            {
                "fields": (
                    "feature_toggles",
                    "maintenance_banner_enabled",
                    "maintenance_banner",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not ApplicationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = ApplicationSettings.objects.get_or_create(key="default")
        return self.changeform_view(
            request, object_id=obj.pk, extra_context=extra_context
        )


@admin.register(AuthenticationSettings)
class AuthenticationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "login_method",
        "password_min_length",
        "mfa_enabled",
        "mfa_required_for_admin",
        "session_timeout_minutes",
    )
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (_("Login Methods"), {"fields": ("key", "login_method")}),
        (
            _("Password Policy"),
            {
                "fields": (
                    "password_min_length",
                    "password_require_uppercase",
                    "password_require_lowercase",
                    "password_require_digits",
                    "password_require_special",
                    "password_expiry_days",
                    "password_history_count",
                    "password_prevent_common",
                )
            },
        ),
        (
            _("Account Lockout"),
            {
                "fields": (
                    "max_login_attempts",
                    "lockout_duration_minutes",
                    "login_attempt_window_minutes",
                )
            },
        ),
        (
            _("Multi-Factor Authentication"),
            {
                "fields": (
                    "mfa_enabled",
                    "mfa_required_for_admin",
                    "mfa_required_for_staff",
                    "mfa_methods",
                )
            },
        ),
        (
            _("OTP Settings"),
            {
                "fields": (
                    "otp_enabled",
                    "otp_delivery_methods",
                    "otp_length",
                    "otp_expiry_minutes",
                )
            },
        ),
        (
            _("Session Management"),
            {
                "fields": (
                    "session_timeout_minutes",
                    "session_absolute_timeout_hours",
                    "concurrent_sessions_limit",
                    "device_trust_enabled",
                    "device_trust_duration_days",
                )
            },
        ),
        (
            _("Invitation & Recovery"),
            {
                "fields": (
                    "invitation_expiry_days",
                    "password_reset_token_expiry_hours",
                    "email_verification_required",
                    "email_verification_token_expiry_hours",
                )
            },
        ),
        (
            _("IP & Geographic Restrictions"),
            {
                "fields": ("ip_allowlist", "ip_blocklist", "geo_blocklist"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not AuthenticationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = AuthenticationSettings.objects.get_or_create(key="default")
        return self.changeform_view(
            request, object_id=obj.pk, extra_context=extra_context
        )


@admin.register(RolePermissionConfiguration)
class RolePermissionConfigurationAdmin(admin.ModelAdmin):
    list_display = ("role", "module", "scope", "is_active", "updated_at")
    list_filter = ("module", "scope", "is_active", "role")
    search_fields = ("role__name", "module")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("role", "module")


@admin.register(WorkflowConfiguration)
class WorkflowConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "module",
        "entity_type",
        "status",
        "digital_signature_required",
        "multi_level_approval",
        "updated_at",
    )
    list_filter = (
        "module",
        "status",
        "digital_signature_required",
        "multi_level_approval",
    )
    search_fields = ("name", "slug", "description", "entity_type")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "module",
                    "entity_type",
                    "status",
                )
            },
        ),
        (
            _("Workflow Definition"),
            {
                "fields": (
                    "stages",
                    "transitions",
                    "escalation_rules",
                    "reminder_schedules",
                    "due_date_rules",
                )
            },
        ),
        (
            _("Approval Settings"),
            {
                "fields": (
                    "digital_signature_required",
                    "multi_level_approval",
                    "approval_chain",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "email_enabled",
        "in_app_enabled",
        "sms_enabled",
        "push_enabled",
        "digest_summary_enabled",
    )
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Email Settings"),
            {
                "fields": (
                    "key",
                    "email_enabled",
                    "email_provider",
                    "email_sender_name",
                    "email_sender_address",
                    "email_footer",
                    "email_templates",
                )
            },
        ),
        (_("In-App Settings"), {"fields": ("in_app_enabled", "in_app_retention_days")}),
        (
            _("SMS Settings"),
            {"fields": ("sms_enabled", "sms_provider", "sms_sender_id")},
        ),
        (_("Push Settings"), {"fields": ("push_enabled", "push_provider")}),
        (
            _("Scheduling & Alerts"),
            {
                "fields": (
                    "default_reminder_schedule",
                    "escalation_alerts",
                    "digest_summary_enabled",
                    "digest_frequency",
                    "quiet_hours_start",
                    "quiet_hours_end",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not NotificationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = NotificationSettings.objects.get_or_create(key="default")
        return self.changeform_view(
            request, object_id=obj.pk, extra_context=extra_context
        )


@admin.register(BrandingSettings)
class BrandingSettingsAdmin(admin.ModelAdmin):
    list_display = ("__str__", "organization", "updated_at")
    list_filter = ("organization",)
    search_fields = ("organization__name",)
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Logos"),
            {
                "fields": (
                    "key",
                    "organization",
                    "primary_logo",
                    "secondary_logo",
                    "favicon",
                )
            },
        ),
        (
            _("Visual Identity"),
            {"fields": ("color_palette", "typography", "icons_set")},
        ),
        (_("Email Branding"), {"fields": ("email_header", "email_footer")}),
        (_("Report Branding"), {"fields": ("report_header", "report_footer")}),
        (_("Dashboard Branding"), {"fields": ("dashboard_banner",)}),
        (_("Watermarks"), {"fields": ("watermark_text", "watermark_opacity")}),
        (_("Document Branding"), {"fields": ("document_header", "document_footer")}),
        (
            _("Custom Code"),
            {
                "fields": ("custom_css", "custom_js"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(NumberingConfiguration)
class NumberingConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "module",
        "prefix",
        "format",
        "sequence",
        "reset_frequency",
        "last_reset",
        "is_active",
    )
    list_filter = ("module", "reset_frequency", "is_active")
    search_fields = ("module", "prefix")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("module", "prefix")


@admin.register(DocumentSettings)
class DocumentSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "max_file_size_mb",
        "version_control_enabled",
        "max_versions",
        "default_retention_days",
        "watermark_enabled",
        "preview_enabled",
    )
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("File Handling"),
            {"fields": ("key", "allowed_file_types", "max_file_size_mb")},
        ),
        (_("Version Control"), {"fields": ("version_control_enabled", "max_versions")}),
        (
            _("Categories & Retention"),
            {"fields": ("categories", "default_retention_days")},
        ),
        (
            _("Confidentiality & Security"),
            {
                "fields": (
                    "confidentiality_levels",
                    "watermark_enabled",
                    "watermark_text",
                    "preview_enabled",
                    "download_permissions",
                    "expiry_notification_days",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not DocumentSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = DocumentSettings.objects.get_or_create(key="default")
        return self.changeform_view(
            request, object_id=obj.pk, extra_context=extra_context
        )


@admin.register(ExportSettings)
class ExportSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "default_format",
        "branding_enabled",
        "headers_enabled",
        "footers_enabled",
        "watermark_enabled",
        "security_enabled",
    )
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Format Settings"),
            {"fields": ("key", "supported_formats", "default_format")},
        ),
        (
            _("Template & Branding"),
            {
                "fields": (
                    "templates",
                    "branding_enabled",
                    "headers_enabled",
                    "footers_enabled",
                    "pagination_enabled",
                )
            },
        ),
        (
            _("Security"),
            {
                "fields": (
                    "watermark_enabled",
                    "security_enabled",
                    "password_protection",
                    "digital_signature",
                )
            },
        ),
        (_("Limits"), {"fields": ("max_rows_csv", "max_rows_xlsx", "max_pages_pdf")}),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return not ExportSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = ExportSettings.objects.get_or_create(key="default")
        return self.changeform_view(
            request, object_id=obj.pk, extra_context=extra_context
        )


@admin.register(SecurityPolicy)
class SecurityPolicyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "policy_type",
        "enforcement_level",
        "is_active",
        "effective_date",
        "review_date",
        "reviewed_by",
    )
    list_filter = ("policy_type", "enforcement_level", "is_active")
    search_fields = ("name", "slug", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "slug", "description", "policy_type")},
        ),
        (
            _("Policy Definition"),
            {"fields": ("rules", "enforcement_level", "scope", "exceptions")},
        ),
        (
            _("Status & Review"),
            {
                "fields": (
                    "is_active",
                    "effective_date",
                    "review_date",
                    "reviewed_by",
                    "approved_by",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "backup_type",
        "frequency",
        "schedule_time",
        "retention_days",
        "is_active",
        "last_run",
        "last_status",
    )
    list_filter = ("backup_type", "frequency", "is_active", "last_status")
    search_fields = ("name", "description")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "last_run",
        "last_status",
        "last_error",
    )
    fieldsets = (
        (_("Basic Information"), {"fields": ("name", "description", "backup_type")}),
        (_("Schedule"), {"fields": ("frequency", "schedule_time", "schedule_days")}),
        (
            _("Storage & Retention"),
            {
                "fields": (
                    "retention_days",
                    "max_backups",
                    "compression_enabled",
                    "encryption_enabled",
                    "storage_location",
                )
            },
        ),
        (
            _("Notifications"),
            {"fields": ("notification_on_success", "notification_on_failure")},
        ),
        (
            _("Status"),
            {"fields": ("is_active", "last_run", "last_status", "last_error")},
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(BackupHistory)
class BackupHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "schedule",
        "backup_type",
        "status",
        "started_at",
        "completed_at",
        "file_size_mb",
        "verification_status",
    )
    list_filter = ("backup_type", "status", "verification_status")
    search_fields = ("schedule__name", "file_path", "error_message")
    readonly_fields = (
        "schedule",
        "backup_type",
        "status",
        "started_at",
        "completed_at",
        "file_path",
        "file_size",
        "error_message",
        "checksum",
        "verification_status",
        "verified_at",
        "created_at",
    )
    ordering = ("-started_at",)
    date_hierarchy = "started_at"

    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / 1024 / 1024:.2f} MB"
        return "-"

    file_size_mb.short_description = _("File Size (MB)")

    def has_add_permission(self, request):
        return False


@admin.register(IntegrationConfiguration)
class IntegrationConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "integration_type",
        "provider",
        "is_active",
        "last_sync",
        "last_status",
        "health_check_enabled",
    )
    list_filter = (
        "integration_type",
        "is_active",
        "last_status",
        "health_check_enabled",
    )
    search_fields = ("name", "slug", "provider", "base_url")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "last_sync",
        "last_status",
        "last_error",
    )
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "integration_type",
                    "provider",
                    "base_url",
                )
            },
        ),
        (_("Configuration"), {"fields": ("configuration", "credentials_encrypted")}),
        (
            _("Status & Health"),
            {
                "fields": (
                    "is_active",
                    "health_check_enabled",
                    "health_check_url",
                    "health_check_interval_minutes",
                    "last_sync",
                    "last_status",
                    "last_error",
                )
            },
        ),
        (
            _("Performance"),
            {"fields": ("rate_limit", "timeout_seconds", "retry_attempts")},
        ),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(MaintenanceWindow)
class MaintenanceWindowAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "maintenance_type",
        "start_time",
        "end_time",
        "status",
        "read_only_mode",
    )
    list_filter = ("maintenance_type", "status", "read_only_mode")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    filter_horizontal = ("notified_users",)
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "description", "maintenance_type")},
        ),
        (_("Schedule"), {"fields": ("start_time", "end_time", "timezone")}),
        (
            _("Access Control"),
            {"fields": ("read_only_mode", "affected_modules", "allowed_roles")},
        ),
        (
            _("Communication"),
            {"fields": ("notification_banner", "estimated_restoration")},
        ),
        (_("Status"), {"fields": ("status", "notified_users")}),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(SystemHealthRecord)
class SystemHealthRecordAdmin(admin.ModelAdmin):
    list_display = ("component", "metric_name", "value", "unit", "status", "created_at")
    list_filter = ("component", "status")
    search_fields = ("metric_name",)
    readonly_fields = (
        "component",
        "metric_name",
        "value",
        "unit",
        "status",
        "threshold_warning",
        "threshold_critical",
        "details",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ConfigurationNotification)
class ConfigurationNotificationAdmin(admin.ModelAdmin):
    list_display = ("event_type", "title", "priority", "is_read", "created_at")
    list_filter = ("event_type", "priority", "is_read")
    search_fields = ("title", "message", "configuration__key")
    readonly_fields = (
        "event_type",
        "configuration",
        "title",
        "message",
        "recipients",
        "roles_notified",
        "is_read",
        "read_at",
        "priority",
        "created_at",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False


@admin.register(SystemConfigurationDashboard)
class SystemConfigurationDashboardAdmin(admin.ModelAdmin):
    list_display = ("name", "is_default", "refresh_interval_seconds", "updated_at")
    list_filter = ("is_default",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    filter_horizontal = ("roles",)
    fieldsets = (
        (_("Basic Information"), {"fields": ("name", "description", "is_default")}),
        (
            _("Layout & Widgets"),
            {"fields": ("layout", "widgets", "refresh_interval_seconds")},
        ),
        (_("Access Control"), {"fields": ("roles",)}),
        (
            _("Metadata"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(ConfigurationAuditReference)
class ConfigurationAuditReferenceAdmin(admin.ModelAdmin):
    list_display = ("configuration", "event_type", "user", "event_timestamp")
    list_filter = ("event_type", "configuration__category")
    search_fields = ("configuration__key", "audit_log_id", "user__email")
    readonly_fields = (
        "configuration",
        "audit_log_id",
        "event_type",
        "event_timestamp",
        "user",
        "details",
        "created_at",
    )
    ordering = ("-event_timestamp",)
    date_hierarchy = "event_timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
