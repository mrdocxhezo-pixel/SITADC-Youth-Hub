from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    ApplicationSettings,
    AuthenticationSettings,
    BackupSchedule,
    BrandingSettings,
    Configuration,
    ConfigurationValue,
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
    WorkflowConfiguration,
)


class BootstrapFormMixin:
    """Mixin to add Bootstrap classes to form fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault("class", "form-select")
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.setdefault("class", "form-control")
                field.widget.attrs.setdefault("rows", 3)
            else:
                field.widget.attrs.setdefault("class", "form-control")


class ConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    """Form for Configuration records."""

    class Meta:
        model = Configuration
        fields = [
            "category",
            "key",
            "name",
            "description",
            "organization",
            "status",
            "confidentiality",
            "effective_date",
            "expiry_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "effective_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "expiry_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean_key(self):
        key = self.cleaned_data["key"]
        if Configuration.objects.exclude(pk=self.instance.pk).filter(key=key).exists():
            raise forms.ValidationError(
                _("A configuration with this key already exists.")
            )
        return key


class ConfigurationValueForm(BootstrapFormMixin, forms.ModelForm):
    """Form for ConfigurationValue records."""

    class Meta:
        model = ConfigurationValue
        fields = ["configuration", "key", "value", "description", "is_sensitive"]
        widgets = {
            "value": forms.Textarea(attrs={"rows": 5}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class OrganizationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for OrganizationSettings."""

    class Meta:
        model = OrganizationSettings
        fields = [
            "name",
            "short_name",
            "acronym",
            "logo",
            "mission",
            "vision",
            "core_values",
            "registration_number",
            "registration_date",
            "tax_id",
            "physical_address",
            "postal_address",
            "phone",
            "email",
            "website",
            "official_email",
            "social_media",
            "fiscal_year_start",
            "default_language",
            "default_timezone",
            "currency",
        ]
        widgets = {
            "mission": forms.Textarea(attrs={"rows": 3}),
            "vision": forms.Textarea(attrs={"rows": 3}),
            "core_values": forms.Textarea(attrs={"rows": 3}),
            "physical_address": forms.Textarea(attrs={"rows": 3}),
            "postal_address": forms.Textarea(attrs={"rows": 3}),
            "social_media": forms.Textarea(attrs={"rows": 5}),
            "registration_date": forms.DateInput(attrs={"type": "date"}),
            "fiscal_year_start": forms.DateInput(attrs={"type": "date"}),
        }


class ApplicationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for ApplicationSettings."""

    class Meta:
        model = ApplicationSettings
        fields = [
            "application_name",
            "application_short_name",
            "application_version",
            "system_status",
            "default_language",
            "default_timezone",
            "date_format",
            "time_format",
            "default_pagination_size",
            "theme_config",
            "light_mode_default",
            "dark_mode_available",
            "session_timeout_minutes",
            "file_upload_max_size_mb",
            "default_storage_path",
            "default_export_formats",
            "feature_toggles",
            "maintenance_banner_enabled",
            "maintenance_banner",
        ]
        widgets = {
            "theme_config": forms.Textarea(attrs={"rows": 5}),
            "default_export_formats": forms.Textarea(attrs={"rows": 3}),
            "feature_toggles": forms.Textarea(attrs={"rows": 5}),
            "maintenance_banner": forms.Textarea(attrs={"rows": 3}),
        }


class AuthenticationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for AuthenticationSettings."""

    class Meta:
        model = AuthenticationSettings
        fields = [
            "login_method",
            "password_min_length",
            "password_require_uppercase",
            "password_require_lowercase",
            "password_require_digits",
            "password_require_special",
            "password_expiry_days",
            "password_history_count",
            "password_prevent_common",
            "max_login_attempts",
            "lockout_duration_minutes",
            "login_attempt_window_minutes",
            "mfa_enabled",
            "mfa_required_for_admin",
            "mfa_required_for_staff",
            "mfa_methods",
            "otp_enabled",
            "otp_delivery_methods",
            "otp_length",
            "otp_expiry_minutes",
            "session_timeout_minutes",
            "session_absolute_timeout_hours",
            "concurrent_sessions_limit",
            "device_trust_enabled",
            "device_trust_duration_days",
            "invitation_expiry_days",
            "password_reset_token_expiry_hours",
            "email_verification_required",
            "email_verification_token_expiry_hours",
            "ip_allowlist",
            "ip_blocklist",
            "geo_blocklist",
        ]
        widgets = {
            "mfa_methods": forms.Textarea(attrs={"rows": 3}),
            "otp_delivery_methods": forms.Textarea(attrs={"rows": 3}),
            "ip_allowlist": forms.Textarea(attrs={"rows": 3}),
            "ip_blocklist": forms.Textarea(attrs={"rows": 3}),
            "geo_blocklist": forms.Textarea(attrs={"rows": 3}),
        }


class RolePermissionConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    """Form for RolePermissionConfiguration."""

    class Meta:
        model = RolePermissionConfiguration
        fields = ["role", "module", "permissions", "scope", "conditions", "is_active"]
        widgets = {
            "permissions": forms.Textarea(attrs={"rows": 5}),
            "conditions": forms.Textarea(attrs={"rows": 3}),
        }


class WorkflowConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    """Form for WorkflowConfiguration."""

    class Meta:
        model = WorkflowConfiguration
        fields = [
            "name",
            "slug",
            "description",
            "module",
            "entity_type",
            "status",
            "stages",
            "transitions",
            "escalation_rules",
            "reminder_schedules",
            "due_date_rules",
            "digital_signature_required",
            "multi_level_approval",
            "approval_chain",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "stages": forms.Textarea(attrs={"rows": 5}),
            "transitions": forms.Textarea(attrs={"rows": 5}),
            "escalation_rules": forms.Textarea(attrs={"rows": 5}),
            "reminder_schedules": forms.Textarea(attrs={"rows": 5}),
            "due_date_rules": forms.Textarea(attrs={"rows": 3}),
            "approval_chain": forms.Textarea(attrs={"rows": 3}),
        }


class NotificationSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for NotificationSettings."""

    class Meta:
        model = NotificationSettings
        fields = [
            "email_enabled",
            "email_provider",
            "email_sender_name",
            "email_sender_address",
            "email_footer",
            "email_templates",
            "in_app_enabled",
            "in_app_retention_days",
            "sms_enabled",
            "sms_provider",
            "sms_sender_id",
            "push_enabled",
            "push_provider",
            "default_reminder_schedule",
            "escalation_alerts",
            "digest_summary_enabled",
            "digest_frequency",
            "quiet_hours_start",
            "quiet_hours_end",
        ]
        widgets = {
            "email_footer": forms.Textarea(attrs={"rows": 3}),
            "email_templates": forms.Textarea(attrs={"rows": 5}),
            "default_reminder_schedule": forms.Textarea(attrs={"rows": 5}),
            "escalation_alerts": forms.Textarea(attrs={"rows": 5}),
            "quiet_hours_start": forms.TimeInput(attrs={"type": "time"}),
            "quiet_hours_end": forms.TimeInput(attrs={"type": "time"}),
        }


class BrandingSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for BrandingSettings."""

    class Meta:
        model = BrandingSettings
        fields = [
            "organization",
            "primary_logo",
            "secondary_logo",
            "favicon",
            "color_palette",
            "typography",
            "icons_set",
            "email_header",
            "email_footer",
            "report_header",
            "report_footer",
            "dashboard_banner",
            "watermark_text",
            "watermark_opacity",
            "document_header",
            "document_footer",
            "custom_css",
            "custom_js",
        ]
        widgets = {
            "color_palette": forms.Textarea(attrs={"rows": 5}),
            "typography": forms.Textarea(attrs={"rows": 5}),
            "email_header": forms.Textarea(attrs={"rows": 3}),
            "email_footer": forms.Textarea(attrs={"rows": 3}),
            "report_header": forms.Textarea(attrs={"rows": 3}),
            "report_footer": forms.Textarea(attrs={"rows": 3}),
            "dashboard_banner": forms.Textarea(attrs={"rows": 3}),
            "document_header": forms.Textarea(attrs={"rows": 3}),
            "document_footer": forms.Textarea(attrs={"rows": 3}),
            "custom_css": forms.Textarea(attrs={"rows": 10}),
            "custom_js": forms.Textarea(attrs={"rows": 10}),
        }


class NumberingConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    """Form for NumberingConfiguration."""

    class Meta:
        model = NumberingConfiguration
        fields = [
            "module",
            "prefix",
            "format",
            "sequence",
            "reset_frequency",
            "last_reset",
            "is_active",
        ]
        widgets = {
            "last_reset": forms.DateInput(attrs={"type": "date"}),
        }


class DocumentSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for DocumentSettings."""

    class Meta:
        model = DocumentSettings
        fields = [
            "allowed_file_types",
            "max_file_size_mb",
            "version_control_enabled",
            "max_versions",
            "categories",
            "default_retention_days",
            "confidentiality_levels",
            "watermark_enabled",
            "watermark_text",
            "preview_enabled",
            "download_permissions",
            "expiry_notification_days",
        ]
        widgets = {
            "allowed_file_types": forms.Textarea(attrs={"rows": 3}),
            "categories": forms.Textarea(attrs={"rows": 5}),
            "confidentiality_levels": forms.Textarea(attrs={"rows": 5}),
            "download_permissions": forms.Textarea(attrs={"rows": 5}),
        }


class ExportSettingsForm(BootstrapFormMixin, forms.ModelForm):
    """Form for ExportSettings."""

    class Meta:
        model = ExportSettings
        fields = [
            "supported_formats",
            "default_format",
            "templates",
            "branding_enabled",
            "headers_enabled",
            "footers_enabled",
            "pagination_enabled",
            "watermark_enabled",
            "security_enabled",
            "password_protection",
            "digital_signature",
            "max_rows_csv",
            "max_rows_xlsx",
            "max_pages_pdf",
        ]
        widgets = {
            "supported_formats": forms.Textarea(attrs={"rows": 3}),
            "templates": forms.Textarea(attrs={"rows": 5}),
        }


class SecurityPolicyForm(BootstrapFormMixin, forms.ModelForm):
    """Form for SecurityPolicy."""

    class Meta:
        model = SecurityPolicy
        fields = [
            "name",
            "slug",
            "description",
            "policy_type",
            "rules",
            "enforcement_level",
            "scope",
            "exceptions",
            "is_active",
            "effective_date",
            "review_date",
            "reviewed_by",
            "approved_by",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "rules": forms.Textarea(attrs={"rows": 5}),
            "scope": forms.Textarea(attrs={"rows": 3}),
            "exceptions": forms.Textarea(attrs={"rows": 3}),
            "effective_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "review_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class BackupScheduleForm(BootstrapFormMixin, forms.ModelForm):
    """Form for BackupSchedule."""

    class Meta:
        model = BackupSchedule
        fields = [
            "name",
            "description",
            "backup_type",
            "frequency",
            "schedule_time",
            "schedule_days",
            "retention_days",
            "max_backups",
            "compression_enabled",
            "encryption_enabled",
            "storage_location",
            "notification_on_success",
            "notification_on_failure",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "schedule_days": forms.Textarea(attrs={"rows": 3}),
            "schedule_time": forms.TimeInput(attrs={"type": "time"}),
        }


class IntegrationConfigurationForm(BootstrapFormMixin, forms.ModelForm):
    """Form for IntegrationConfiguration."""

    class Meta:
        model = IntegrationConfiguration
        fields = [
            "name",
            "slug",
            "description",
            "integration_type",
            "provider",
            "base_url",
            "configuration",
            "credentials_encrypted",
            "is_active",
            "health_check_enabled",
            "health_check_url",
            "health_check_interval_minutes",
            "rate_limit",
            "timeout_seconds",
            "retry_attempts",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "configuration": forms.Textarea(attrs={"rows": 5}),
            "credentials_encrypted": forms.Textarea(attrs={"rows": 5}),
            "health_check_url": forms.URLInput(
                attrs={"placeholder": "https://example.com/health"}
            ),
        }


class MaintenanceWindowForm(BootstrapFormMixin, forms.ModelForm):
    """Form for MaintenanceWindow."""

    class Meta:
        model = MaintenanceWindow
        fields = [
            "name",
            "description",
            "maintenance_type",
            "start_time",
            "end_time",
            "timezone",
            "read_only_mode",
            "affected_modules",
            "allowed_roles",
            "notification_banner",
            "estimated_restoration",
            "status",
            "notified_users",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "affected_modules": forms.Textarea(attrs={"rows": 3}),
            "allowed_roles": forms.Textarea(attrs={"rows": 3}),
            "notification_banner": forms.Textarea(attrs={"rows": 3}),
            "estimated_restoration": forms.DateTimeInput(
                attrs={"type": "datetime-local"}
            ),
        }


class SystemConfigurationDashboardForm(BootstrapFormMixin, forms.ModelForm):
    """Form for SystemConfigurationDashboard."""

    class Meta:
        model = SystemConfigurationDashboard
        fields = [
            "name",
            "description",
            "is_default",
            "layout",
            "widgets",
            "refresh_interval_seconds",
            "roles",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "layout": forms.Textarea(attrs={"rows": 5}),
            "widgets": forms.Textarea(attrs={"rows": 5}),
        }
