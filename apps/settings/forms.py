from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm as DjangoPasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import (
    SystemSettings,
    IntegrationSettings,
    UserSettings,
    UserSettingsDefault,
)

User = get_user_model()


class UserSettingsForm(forms.ModelForm):
    """Form for user appearance & personalization settings."""

    class Meta:
        model = UserSettings
        fields = [
            "theme",
            "accent_color",
            "density",
            "sidebar_collapsed",
            "dashboard_layout",
            "animations_enabled",
            "reduced_motion",
            "high_contrast",
            "larger_text",
            "focus_indicators",
        ]
        widgets = {
            "theme": forms.Select(attrs={"class": "form-select"}),
            "accent_color": forms.TextInput(attrs={"class": "form-control"}),
            "density": forms.Select(attrs={"class": "form-select"}),
            "sidebar_collapsed": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "dashboard_layout": forms.Select(attrs={"class": "form-select"}),
            "animations_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "reduced_motion": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "high_contrast": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "larger_text": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "focus_indicators": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class NotificationSettingsForm(forms.ModelForm):
    """Form for notification preferences."""

    class Meta:
        model = UserSettings
        fields = [
            "email_notifications",
            "in_app_notifications",
            "browser_notifications",
            "report_reminders",
            "report_submission_notifications",
            "report_review_notifications",
            "approval_notifications",
            "meeting_reminders",
            "training_reminders",
            "task_notifications",
            "system_announcements",
            "security_alerts",
            "organizational_announcements",
        ]
        widgets = {
            "email_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "in_app_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "browser_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "report_reminders": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "report_submission_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "report_review_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "approval_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "meeting_reminders": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "training_reminders": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "task_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "system_announcements": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "security_alerts": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "organizational_announcements": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class PrivacySettingsForm(forms.ModelForm):
    """Form for privacy settings."""

    class Meta:
        model = UserSettings
        fields = [
            "profile_visibility",
            "contact_visibility",
            "activity_visibility",
            "show_online_status",
            "directory_visibility",
            "data_sharing",
        ]
        widgets = {
            "profile_visibility": forms.Select(attrs={"class": "form-select"}),
            "contact_visibility": forms.Select(attrs={"class": "form-select"}),
            "activity_visibility": forms.Select(attrs={"class": "form-select"}),
            "show_online_status": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "directory_visibility": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "data_sharing": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class LanguageRegionSettingsForm(forms.ModelForm):
    """Form for language, region & time settings."""

    class Meta:
        model = UserSettings
        fields = [
            "language",
            "country",
            "timezone",
            "date_format",
            "time_format",
            "currency_format",
            "first_day_of_week",
        ]
        widgets = {
            "language": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "timezone": forms.TextInput(attrs={"class": "form-control"}),
            "date_format": forms.TextInput(attrs={"class": "form-control"}),
            "time_format": forms.TextInput(attrs={"class": "form-control"}),
            "currency_format": forms.TextInput(attrs={"class": "form-control"}),
            "first_day_of_week": forms.Select(attrs={"class": "form-select"}),
        }


class AccessibilitySettingsForm(forms.ModelForm):
    """Form for accessibility settings."""

    class Meta:
        model = UserSettings
        fields = [
            "reduced_motion",
            "high_contrast",
            "larger_text",
            "focus_indicators",
            "animations_enabled",
        ]
        widgets = {
            "reduced_motion": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "high_contrast": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "larger_text": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "focus_indicators": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "animations_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile."""

    first_name = forms.CharField(label=_("First Name"), max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(label=_("Last Name"), max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    username = forms.CharField(label=_("Username"), max_length=150, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(label=_("Email Address"), widget=forms.EmailInput(attrs={"class": "form-control"}))
    phone_number = forms.CharField(label=_("Phone Number"), max_length=20, required=False, widget=forms.TextInput(attrs={"class": "form-control"}))

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "phone_number"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists():
            raise ValidationError(_("A user with this email already exists."))
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.exclude(pk=self.user.pk).filter(username__iexact=username).exists():
            raise ValidationError(_("A user with this username already exists."))
        return username


class ProfilePhotoForm(forms.Form):
    """Form for profile photo upload."""

    profile_photo = forms.ImageField(
        label=_("Profile Photo"),
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )


class CustomPasswordChangeForm(DjangoPasswordChangeForm):
    """Custom password change form with validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({"class": "form-check-input"})
            else:
                field.widget.attrs.update({"class": "form-control"})


class TwoFactorSettingsForm(forms.Form):
    """Form for 2FA settings."""

    enable_2fa = forms.BooleanField(
        label=_("Enable Two-Factor Authentication"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    otp_method = forms.ChoiceField(
        label=_("OTP Method"),
        choices=[
            ("email", _("Email")),
            ("sms", _("SMS")),
            ("authenticator", _("Authenticator App")),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class SessionManagementForm(forms.Form):
    """Form for session management."""

    session_key = forms.CharField(widget=forms.HiddenInput())
    terminate = forms.BooleanField(widget=forms.HiddenInput(), required=False)


class SystemSettingsForm(forms.ModelForm):
    """Form for system-wide settings (admin only)."""

    class Meta:
        model = SystemSettings
        fields = [
            "system_name",
            "system_short_name",
            "system_email",
            "system_status",
            "maintenance_mode",
            "maintenance_message",
            "maintenance_allowed_roles",
            "session_timeout_minutes",
            "password_min_length",
            "password_require_uppercase",
            "password_require_lowercase",
            "password_require_digits",
            "password_require_special",
            "password_expiry_days",
            "max_login_attempts",
            "lockout_duration_minutes",
            "require_2fa_admin",
            "max_upload_size_mb",
            "allowed_file_types",
            "audit_log_enabled",
            "audit_retention_days",
            "backup_enabled",
            "backup_frequency",
            "backup_retention_days",
        ]
        widgets = {
            "system_name": forms.TextInput(attrs={"class": "form-control"}),
            "system_short_name": forms.TextInput(attrs={"class": "form-control"}),
            "system_email": forms.EmailInput(attrs={"class": "form-control"}),
            "system_status": forms.Select(attrs={"class": "form-select"}),
            "maintenance_mode": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "maintenance_message": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "maintenance_allowed_roles": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "session_timeout_minutes": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "password_min_length": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "password_require_uppercase": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "password_require_lowercase": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "password_require_digits": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "password_require_special": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "password_expiry_days": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "max_login_attempts": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "lockout_duration_minutes": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "require_2fa_admin": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "max_upload_size_mb": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "allowed_file_types": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "audit_log_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "audit_retention_days": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "backup_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "backup_frequency": forms.Select(attrs={"class": "form-select"}),
            "backup_retention_days": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
        }

    def clean_maintenance_allowed_roles(self):
        data = self.cleaned_data.get("maintenance_allowed_roles", "[]")
        if isinstance(data, str):
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return data

    def clean_allowed_file_types(self):
        data = self.cleaned_data.get("allowed_file_types", "[]")
        if isinstance(data, str):
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return data


class IntegrationSettingsForm(forms.ModelForm):
    """Form for integration settings."""

    class Meta:
        model = IntegrationSettings
        fields = [
            "name",
            "slug",
            "description",
            "integration_type",
            "is_active",
            "configuration",
            "credentials",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "integration_type": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "configuration": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "credentials": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def clean_configuration(self):
        data = self.cleaned_data.get("configuration", "{}")
        if isinstance(data, str):
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return data

    def clean_credentials(self):
        data = self.cleaned_data.get("credentials", "{}")
        if isinstance(data, str):
            import json
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return data


class UserSettingsDefaultForm(forms.ModelForm):
    """Form for default user settings."""

    class Meta:
        model = UserSettingsDefault
        fields = [
            "default_theme",
            "default_density",
            "default_dashboard_layout",
            "default_animations",
            "default_email_notifications",
            "default_in_app_notifications",
            "default_browser_notifications",
            "default_profile_visibility",
            "default_language",
            "default_country",
            "default_timezone",
        ]
        widgets = {
            "default_theme": forms.Select(attrs={"class": "form-select"}),
            "default_density": forms.Select(attrs={"class": "form-select"}),
            "default_dashboard_layout": forms.Select(attrs={"class": "form-select"}),
            "default_animations": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_email_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_in_app_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_browser_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "default_profile_visibility": forms.Select(attrs={"class": "form-select"}),
            "default_language": forms.TextInput(attrs={"class": "form-control"}),
            "default_country": forms.TextInput(attrs={"class": "form-control"}),
            "default_timezone": forms.TextInput(attrs={"class": "form-control"}),
        }