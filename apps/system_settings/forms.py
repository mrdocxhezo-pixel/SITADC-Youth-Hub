"""Forms for System Settings (Phase 28)."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import SystemConfiguration


class SystemConfigurationForm(forms.ModelForm):
    """Form for editing the singleton system configuration."""

    class Meta:
        model = SystemConfiguration
        fields = [
            'application_name',
            'application_short_name',
            'system_status',
            'default_language',
            'default_timezone',
            'date_format',
            'time_format',
            'default_pagination_size',
            'organization',
            'branding',
            'email_sender_name',
            'email_sender_address',
            'email_footer',
            'notification_retention_days',
            'enable_email_notifications',
            'enable_sms_notifications',
            'enable_push_notifications',
            'session_timeout_minutes',
            'password_min_length',
            'password_require_uppercase',
            'password_require_lowercase',
            'password_require_digits',
            'password_require_special_chars',
            'max_login_attempts',
            'lockout_duration_minutes',
            'password_validity_days',
            'require_2fa_for_admin',
            'invitation_expiry_days',
            'password_reset_token_expiry_hours',
            'login_attempt_threshold',
            'default_review_deadline_hours',
            'default_approval_deadline_hours',
            'default_correction_deadline_hours',
            'default_escalation_delay_hours',
            'audit_retention_days',
            'audit_log_enabled',
            'default_dashboard_landing_page',
            'dashboard_refresh_interval_seconds',
            'maintenance_mode_enabled',
            'maintenance_message',
            'maintenance_start_time',
            'maintenance_end_time',
            'maintenance_allowed_roles',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs['class'] = 'form-select'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'