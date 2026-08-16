from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import SystemConfiguration


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for System Configuration."""
    
    def has_add_permission(self, request):
        """Prevent adding more than one instance (singleton pattern)."""
        return not SystemConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the singleton instance."""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to the change view for the singleton instance."""
        obj, created = SystemConfiguration.objects.get_or_create(key="default")
        return self.changeform_view(request, object_id=obj.pk, extra_context=extra_context)
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only based on conditions."""
        # The key field should always be read-only after creation
        if obj:  # editing an existing object
            return self.readonly_fields + ('key',)
        return self.readonly_fields
    
    fieldsets = (
        (_("General System Configuration"), {
            "fields": (
                "application_name",
                "application_short_name",
                "system_status",
                "default_language",
                "default_timezone",
                "date_format",
                "time_format",
                "default_pagination_size",
            )
        }),
        (_("Organizational Configuration"), {
            "fields": (
                "organization",
            )
        }),
        (_("Branding Configuration"), {
            "fields": (
                "branding",
            ),
            "classes": ("collapse",),
        }),
        (_("Email Configuration"), {
            "fields": (
                "email_sender_name",
                "email_sender_address",
                "email_footer",
            )
        }),
        (_("Notification Configuration"), {
            "fields": (
                "notification_retention_days",
                "enable_email_notifications",
                "enable_sms_notifications",
                "enable_push_notifications",
            )
        }),
        (_("Security Configuration"), {
            "fields": (
                "session_timeout_minutes",
                "password_min_length",
                "password_require_uppercase",
                "password_require_lowercase",
                "password_require_digits",
                "password_require_special_chars",
                "max_login_attempts",
                "lockout_duration_minutes",
                "password_validity_days",
                "require_2fa_for_admin",
            )
        }),
        (_("Authentication Configuration"), {
            "fields": (
                "invitation_expiry_days",
                "password_reset_token_expiry_hours",
                "login_attempt_threshold",
            )
        }),
        (_("Workflow Configuration"), {
            "fields": (
                "default_review_deadline_hours",
                "default_approval_deadline_hours",
                "default_correction_deadline_hours",
                "default_escalation_delay_hours",
            )
        }),
        (_("Audit Configuration"), {
            "fields": (
                "audit_retention_days",
                "audit_log_enabled",
            )
        }),
        (_("Dashboard Configuration"), {
            "fields": (
                "default_dashboard_landing_page",
                "dashboard_refresh_interval_seconds",
            )
        }),
        (_("Maintenance Configuration"), {
            "fields": (
                "maintenance_mode_enabled",
                "maintenance_message",
                "maintenance_start_time",
                "maintenance_end_time",
                "maintenance_allowed_roles",
            )
        }),
    )
    
    readonly_fields = ("key", "created_at", "updated_at", "created_by", "updated_by")
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize the form to handle JSON fields better."""
        form = super().get_form(request, obj, **kwargs)
        return form
