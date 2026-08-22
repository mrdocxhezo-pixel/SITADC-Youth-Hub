"""
Forms for the Security Hardening framework.
"""

from __future__ import annotations

import json

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role

from .models import (
    EnterpriseSecurityPolicy,
    Identity,
    ServiceIdentity,
    OrganizationalIdentity,
    Permission,
    RolePermission,
    IdentityRole,
    LoginAttempt,
    AccessReview,
    AccessReviewItem,
    RoleHierarchy,
    PermissionGrant,
    Session,
    MFAEnrollment,
    MFAVerificationAttempt,
    APICredential,
    APIAccessToken,
    APIRateLimit,
    DatabaseSecurityPolicy,
    DatabaseAccessLog,
    SecureFile,
)
from .constants import (
    SecurityConfidentialityLevel,
    SecurityStatus,
    MFAMethod,
    SessionStatus,
    AccessReviewStatus,
    AccessReviewDecision,
)

User = get_user_model()


class JSONFieldWidget(forms.Textarea):
    """Widget for JSON fields with validation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs.update({"class": "form-control font-monospace", "rows": 6})


class EnterpriseSecurityPolicyForm(forms.ModelForm):
    """Form for Enterprise Security Policy."""

    rules = forms.CharField(
        widget=JSONFieldWidget,
        help_text=_("Policy rules in JSON format."),
        required=False,
    )
    scope = forms.CharField(
        widget=JSONFieldWidget,
        help_text=_("Policy scope in JSON format."),
        required=False,
    )
    exceptions = forms.CharField(
        widget=JSONFieldWidget,
        help_text=_("Policy exceptions in JSON format."),
        required=False,
    )

    class Meta:
        model = EnterpriseSecurityPolicy
        fields = [
            "name",
            "policy_type",
            "description",
            "rules",
            "enforcement_level",
            "scope",
            "exceptions",
            "is_active",
            "effective_date",
            "expiry_date",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "policy_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "enforcement_level": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "effective_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "expiry_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }

    def clean_rules(self):
        value = self.cleaned_data.get("rules", "{}")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return value

    def clean_scope(self):
        value = self.cleaned_data.get("scope", "{}")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return value

    def clean_exceptions(self):
        value = self.cleaned_data.get("exceptions", "[]")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return value


class IdentityForm(forms.ModelForm):
    """Form for core Identity."""

    managed_by = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("email"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )

    class Meta:
        model = Identity
        fields = [
            "identity_type",
            "identifier",
            "display_name",
            "description",
            "owner",
            "managed_by",
            "status",
            "confidentiality",
            "expires_at",
            "tags",
            "attributes",
        ]
        widgets = {
            "identity_type": forms.Select(attrs={"class": "form-select"}),
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "confidentiality": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "tags": JSONFieldWidget,
            "attributes": JSONFieldWidget,
        }


class ServiceIdentityForm(forms.ModelForm):
    """Form for Service Identity."""

    managed_by = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("email"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )

    class Meta:
        model = ServiceIdentity
        fields = [
            "identifier",
            "display_name",
            "description",
            "owner",
            "managed_by",
            "status",
            "confidentiality",
            "expires_at",
            "service_type",
            "service_account_token",
            "token_expires_at",
            "ip_allowlist",
            "allowed_operations",
            "tags",
            "attributes",
        ]
        widgets = {
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "confidentiality": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "service_type": forms.Select(attrs={"class": "form-select"}),
            "service_account_token": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "token_expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "ip_allowlist": JSONFieldWidget,
            "allowed_operations": JSONFieldWidget,
            "tags": JSONFieldWidget,
            "attributes": JSONFieldWidget,
        }

    def clean_service_account_token(self):
        service_type = self.cleaned_data.get("service_type")
        token = self.cleaned_data.get("service_account_token")
        if service_type == "api" and not token:
            raise ValidationError(_("API services must have a service account token."))
        return token


class OrganizationalIdentityForm(forms.ModelForm):
    """Form for Organizational Identity."""

    managed_by = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("email"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )

    class Meta:
        model = OrganizationalIdentity
        fields = [
            "identifier",
            "display_name",
            "description",
            "owner",
            "managed_by",
            "status",
            "confidentiality",
            "expires_at",
            "org_identity_type",
            "parent_organization",
            "organization_unit",
            "contact_person",
            "tags",
            "attributes",
        ]
        widgets = {
            "identifier": forms.TextInput(attrs={"class": "form-control"}),
            "display_name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "confidentiality": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "org_identity_type": forms.Select(attrs={"class": "form-select"}),
            "parent_organization": forms.Select(attrs={"class": "form-select"}),
            "organization_unit": forms.Select(attrs={"class": "form-select"}),
            "contact_person": forms.Select(attrs={"class": "form-select"}),
            "tags": JSONFieldWidget,
            "attributes": JSONFieldWidget,
        }


class PermissionForm(forms.ModelForm):
    """Form for granular Permission."""

    class Meta:
        model = Permission
        fields = [
            "name",
            "module",
            "resource_type",
            "action",
            "description",
            "is_system",
            "is_assignable",
            "requires_approval",
            "conditions",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "module": forms.TextInput(attrs={"class": "form-control"}),
            "resource_type": forms.TextInput(attrs={"class": "form-control"}),
            "action": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_system": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_assignable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "requires_approval": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "conditions": JSONFieldWidget,
        }

    def clean_conditions(self):
        value = self.cleaned_data.get("conditions", "{}")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return value


class RolePermissionForm(forms.ModelForm):
    """Form for Role-Permission mapping."""

    class Meta:
        model = RolePermission
        fields = [
            "role",
            "permission",
            "expires_at",
            "is_active",
            "conditions",
            "justification",
        ]
        widgets = {
            "role": forms.Select(attrs={"class": "form-select"}),
            "permission": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "conditions": JSONFieldWidget,
            "justification": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class IdentityRoleForm(forms.ModelForm):
    """Form for Identity-Role assignment."""

    class Meta:
        model = IdentityRole
        fields = [
            "identity",
            "role",
            "expires_at",
            "is_active",
            "conditions",
            "justification",
        ]
        widgets = {
            "identity": forms.Select(attrs={"class": "form-select"}),
            "role": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "conditions": JSONFieldWidget,
            "justification": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class PermissionGrantForm(forms.ModelForm):
    """Form for direct Permission Grant."""

    class Meta:
        model = PermissionGrant
        fields = [
            "identity",
            "permission",
            "expires_at",
            "is_active",
            "conditions",
            "justification",
        ]
        widgets = {
            "identity": forms.Select(attrs={"class": "form-select"}),
            "permission": forms.Select(attrs={"class": "form-select"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "conditions": JSONFieldWidget,
            "justification": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class RoleHierarchyForm(forms.ModelForm):
    """Form for Role Hierarchy."""

    class Meta:
        model = RoleHierarchy
        fields = [
            "parent_role",
            "child_role",
            "inherit_permissions",
            "inherit_role_permissions",
            "justification",
        ]
        widgets = {
            "parent_role": forms.Select(attrs={"class": "form-select"}),
            "child_role": forms.Select(attrs={"class": "form-select"}),
            "inherit_permissions": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "inherit_role_permissions": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "justification": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        parent = cleaned_data.get("parent_role")
        child = cleaned_data.get("child_role")
        if parent and child and parent == child:
            raise ValidationError(_("A role cannot be parent of itself."))
        return cleaned_data


class LoginAttemptForm(forms.ModelForm):
    """Form for Login Attempt (read-only display)."""

    class Meta:
        model = LoginAttempt
        fields = "__all__"
        widgets = {
            "username_attempted": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "ip_address": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "user_agent": forms.Textarea(attrs={"class": "form-control font-monospace", "readonly": True, "rows": 2}),
            "outcome": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "failure_reason": forms.Textarea(attrs={"class": "form-control", "readonly": True, "rows": 2}),
            "risk_score": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "is_suspicious": forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": True}),
            "country_code": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "city": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
        }


class AccessReviewForm(forms.ModelForm):
    """Form for Access Review."""

    reviewers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(is_active=True).order_by("email"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )

    class Meta:
        model = AccessReview
        fields = [
            "name",
            "description",
            "review_type",
            "target_identity",
            "target_role",
            "target_permission",
            "started_at",
            "due_date",
            "auto_approve_low_risk",
            "require_justification_for_changes",
            "escalate_overdue_reviews",
            "reviewers",
            "lead_reviewer",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "review_type": forms.Select(attrs={"class": "form-select"}),
            "target_identity": forms.Select(attrs={"class": "form-select"}),
            "target_role": forms.Select(attrs={"class": "form-select"}),
            "target_permission": forms.Select(attrs={"class": "form-select"}),
            "started_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "due_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "auto_approve_low_risk": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "require_justification_for_changes": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "escalate_overdue_reviews": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "lead_reviewer": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        started = cleaned_data.get("started_at")
        due = cleaned_data.get("due_date")
        if started and due and due <= started:
            raise ValidationError(_("Due date must be after start date."))
        return cleaned_data


class AccessReviewItemForm(forms.ModelForm):
    """Form for Access Review Item decision."""

    class Meta:
        model = AccessReviewItem
        fields = [
            "decision",
            "justification",
            "new_value",
            "change_reason",
        ]
        widgets = {
            "decision": forms.Select(attrs={"class": "form-select"}),
            "justification": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "new_value": JSONFieldWidget,
            "change_reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def clean_new_value(self):
        value = self.cleaned_data.get("new_value", "{}")
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValidationError(_("Invalid JSON format."))
        return value


class SessionForm(forms.ModelForm):
    """Form for Session (read-only display)."""

    class Meta:
        model = Session
        fields = "__all__"
        widgets = {
            "identity": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "session_key": forms.TextInput(attrs={"class": "form-control font-monospace", "readonly": True}),
            "ip_address": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "user_agent": forms.Textarea(attrs={"class": "form-control font-monospace", "readonly": True, "rows": 2}),
            "status": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "started_at": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "last_activity_at": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "terminated_at": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "idle_timeout_minutes": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "absolute_timeout_minutes": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "is_secure": forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": True}),
            "is_mfa_used": forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": True}),
            "mfa_method": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "device_fingerprint": forms.TextInput(attrs={"class": "form-control font-monospace", "readonly": True}),
        }


class MFAEnrollmentForm(forms.ModelForm):
    """Form for MFA Enrollment."""

    class Meta:
        model = MFAEnrollment
        fields = [
            "identity",
            "method",
            "is_primary",
            "is_backup",
            "secret_key",
            "phone_number",
            "email_address",
            "name",
            "attributes",
        ]
        widgets = {
            "identity": forms.Select(attrs={"class": "form-select"}),
            "method": forms.Select(attrs={"class": "form-select"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_backup": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "secret_key": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email_address": forms.EmailInput(attrs={"class": "form-control"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "attributes": JSONFieldWidget,
        }

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get("method")
        secret_key = cleaned_data.get("secret_key")
        phone_number = cleaned_data.get("phone_number")
        email_address = cleaned_data.get("email_address")

        if method == MFAMethod.TOTP and not secret_key:
            raise ValidationError(_("TOTP requires a secret key."))
        if method == MFAMethod.SMS and not phone_number:
            raise ValidationError(_("SMS requires a phone number."))
        if method == MFAMethod.EMAIL and not email_address:
            raise ValidationError(_("Email requires an email address."))

        return cleaned_data


class MFAVerificationForm(forms.Form):
    """Form for MFA verification challenge."""

    method = forms.ChoiceField(
        choices=[("", _("Select method"))] + MFAMethod.CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    code = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Enter verification code")}),
    )
    use_backup_code = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Use backup code"),
    )
    trust_device = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Trust this device for 30 days"),
    )


class APICredentialForm(forms.ModelForm):
    """Form for API Credential."""

    class Meta:
        model = APICredential
        fields = [
            "name",
            "credential_type",
            "service_name",
            "description",
            "credential_key",
            "credential_secret",
            "service_url",
            "ip_allowlist",
            "allowed_endpoints",
            "allowed_methods",
            "rate_limit_per_hour",
            "rate_limit_per_day",
            "expires_at",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "credential_type": forms.Select(attrs={"class": "form-select"}),
            "service_name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "credential_key": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "credential_secret": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "service_url": forms.URLInput(attrs={"class": "form-control"}),
            "ip_allowlist": JSONFieldWidget,
            "allowed_endpoints": JSONFieldWidget,
            "allowed_methods": JSONFieldWidget,
            "rate_limit_per_hour": forms.NumberInput(attrs={"class": "form-control"}),
            "rate_limit_per_day": forms.NumberInput(attrs={"class": "form-control"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_credential_key(self):
        credential_type = self.cleaned_data.get("credential_type")
        key = self.cleaned_data.get("credential_key")
        if credential_type in ["api_key", "oauth_token", "jwt_token", "bearer_token"] and not key:
            raise ValidationError(_("This credential type requires a key/token."))
        return key


class APIAccessTokenForm(forms.ModelForm):
    """Form for API Access Token."""

    class Meta:
        model = APIAccessToken
        fields = [
            "credential",
            "token",
            "token_type",
            "identity",
            "scopes",
            "permissions",
            "expires_at",
            "not_before",
        ]
        widgets = {
            "credential": forms.Select(attrs={"class": "form-select"}),
            "token": forms.TextInput(attrs={"class": "form-control font-monospace", "readonly": True}),
            "token_type": forms.TextInput(attrs={"class": "form-control"}),
            "identity": forms.Select(attrs={"class": "form-select"}),
            "scopes": JSONFieldWidget,
            "permissions": JSONFieldWidget,
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "not_before": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }


class DatabaseSecurityPolicyForm(forms.ModelForm):
    """Form for Database Security Policy."""

    class Meta:
        model = DatabaseSecurityPolicy
        fields = [
            "name",
            "database_identifier",
            "database_type",
            "host",
            "port",
            "database_name",
            "require_ssl",
            "ssl_cert_path",
            "ssl_key_path",
            "auth_method",
            "use_connection_pooling",
            "max_connections",
            "statement_timeout_ms",
            "lock_timeout_ms",
            "audit_connections",
            "audit_statements",
            "audit_statement_level",
            "encryption_at_rest",
            "encryption_key_identifier",
            "allow_public_access",
            "allowed_networks",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "database_identifier": forms.TextInput(attrs={"class": "form-control"}),
            "database_type": forms.TextInput(attrs={"class": "form-control"}),
            "host": forms.TextInput(attrs={"class": "form-control"}),
            "port": forms.NumberInput(attrs={"class": "form-control"}),
            "database_name": forms.TextInput(attrs={"class": "form-control"}),
            "require_ssl": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ssl_cert_path": forms.TextInput(attrs={"class": "form-control"}),
            "ssl_key_path": forms.TextInput(attrs={"class": "form-control"}),
            "auth_method": forms.TextInput(attrs={"class": "form-control"}),
            "use_connection_pooling": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "max_connections": forms.NumberInput(attrs={"class": "form-control"}),
            "statement_timeout_ms": forms.NumberInput(attrs={"class": "form-control"}),
            "lock_timeout_ms": forms.NumberInput(attrs={"class": "form-control"}),
            "audit_connections": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "audit_statements": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "audit_statement_level": forms.Select(attrs={"class": "form-select"}),
            "encryption_at_rest": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "encryption_key_identifier": forms.TextInput(attrs={"class": "form-control"}),
            "allow_public_access": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "allowed_networks": JSONFieldWidget,
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class DatabaseAccessLogForm(forms.ModelForm):
    """Form for Database Access Log (read-only display)."""

    class Meta:
        model = DatabaseAccessLog
        fields = "__all__"
        widgets = {
            "database_policy": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "session_id": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "username": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "client_ip": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "client_hostname": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "connection_started": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "connection_ended": forms.DateTimeInput(attrs={"class": "form-control", "readonly": True, "type": "datetime-local"}),
            "connection_status": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "statement_type": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
            "statement": forms.Textarea(attrs={"class": "form-control font-monospace", "readonly": True, "rows": 3}),
            "statement_duration_ms": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "rows_affected": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "success": forms.CheckboxInput(attrs={"class": "form-check-input", "disabled": True}),
            "error_message": forms.Textarea(attrs={"class": "form-control", "readonly": True, "rows": 2}),
            "error_code": forms.TextInput(attrs={"class": "form-control", "readonly": True}),
        }


class SecureFileForm(forms.ModelForm):
    """Form for Secure File."""

    allowed_identities = forms.ModelMultipleChoiceField(
        queryset=Identity.objects.filter(status=SecurityStatus.ACTIVE).order_by("display_name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )
    allowed_roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.filter(status="ACTIVE").order_by("name"),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select", "size": "5"}),
    )

    class Meta:
        model = SecureFile
        fields = [
            "filename",
            "original_filename",
            "file_size",
            "content_type",
            "storage_path",
            "storage_bucket",
            "storage_region",
            "owner",
            "uploaded_by",
            "is_public",
            "allowed_identities",
            "allowed_roles",
            "confidentiality",
            "checksum_algorithm",
            "checksum_value",
            "is_encrypted",
            "encryption_algorithm",
            "encryption_key_identifier",
            "retention_date",
            "retention_policy",
        ]
        widgets = {
            "filename": forms.TextInput(attrs={"class": "form-control"}),
            "original_filename": forms.TextInput(attrs={"class": "form-control"}),
            "file_size": forms.NumberInput(attrs={"class": "form-control"}),
            "content_type": forms.TextInput(attrs={"class": "form-control"}),
            "storage_path": forms.TextInput(attrs={"class": "form-control"}),
            "storage_bucket": forms.TextInput(attrs={"class": "form-control"}),
            "storage_region": forms.TextInput(attrs={"class": "form-control"}),
            "owner": forms.Select(attrs={"class": "form-select"}),
            "uploaded_by": forms.Select(attrs={"class": "form-select"}),
            "is_public": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "confidentiality": forms.Select(attrs={"class": "form-select"}),
            "checksum_algorithm": forms.TextInput(attrs={"class": "form-control"}),
            "checksum_value": forms.TextInput(attrs={"class": "form-control font-monospace"}),
            "is_encrypted": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "encryption_algorithm": forms.TextInput(attrs={"class": "form-control"}),
            "encryption_key_identifier": forms.TextInput(attrs={"class": "form-control"}),
            "retention_date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
            "retention_policy": forms.TextInput(attrs={"class": "form-control"}),
        }