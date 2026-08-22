"""Security Hardening models."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from apps.core.models import CreatedByModel, TimeStampedModel, UpdatedByModel, UUIDModel
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role
from apps.security.constants import (
    SecurityConfidentialityLevel,
    SecurityStatus,
    SecuritySeverity,
    SecurityIncidentCategory,
    VulnerabilityStatus,
    VulnerabilitySource,
    ThreatEventType,
    MFAMethod,
    SessionStatus,
    ComplianceCheckStatus,
    AccessReviewStatus,
    AccessReviewDecision,
    SecurityModule,
)


class EnterpriseSecurityPolicy(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Enterprise security policies."""
    
    name = models.CharField(_("Policy Name"), max_length=150)
    slug = models.SlugField(_("Policy Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    POLICY_TYPE_CHOICES = [
        ("password", _("Password Policy")),
        ("session", _("Session Policy")),
        ("api", _("API Security Policy")),
        ("network", _("Network Policy")),
        ("data", _("Data Protection Policy")),
        ("access", _("Access Control Policy")),
        ("encryption", _("Encryption Policy")),
        ("audit", _("Audit Policy")),
        ("authentication", _("Authentication Policy")),
        ("authorization", _("Authorization Policy")),
    ]
    policy_type = models.CharField(
        _("Policy Type"), max_length=20, choices=POLICY_TYPE_CHOICES
    )
    
    rules = models.JSONField(_("Policy Rules"), default=dict)
    enforcement_level = models.CharField(
        _("Enforcement Level"),
        max_length=20,
        choices=[
            ("advisory", _("Advisory")),
            ("warning", _("Warning")),
            ("enforce", _("Enforce")),
            ("block", _("Block")),
        ],
        default="enforce",
    )
    scope = models.JSONField(_("Policy Scope"), default=dict, blank=True)
    exceptions = models.JSONField(_("Policy Exceptions"), default=list, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    effective_date = models.DateTimeField(_("Effective Date"), null=True, blank=True)
    expiry_date = models.DateTimeField(_("Expiry Date"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enterprise_security_policies_reviewed",
        verbose_name=_("Reviewed By"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enterprise_security_policies_approved",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    
    class Meta:
        verbose_name = _("Enterprise Security Policy")
        verbose_name_plural = _("Enterprise Security Policies")
        ordering = ("policy_type", "name")
    
    def __str__(self):
        return f"{self.get_policy_type_display()}: {self.name}"
    
    def clean(self):
        if (
            self.expiry_date
            and self.effective_date
            and self.expiry_date <= self.effective_date
        ):
            raise ValidationError(_("Expiry date must be after effective date."))
        
        # Validate policy-specific rules
        if self.policy_type == "password":
            self._validate_password_policy_rules()
        elif self.policy_type == "session":
            self._validate_session_policy_rules()
    
    def _validate_password_policy_rules(self):
        """Validate password policy rules."""
        rules = self.rules
        if not isinstance(rules, dict):
            raise ValidationError(_("Password policy rules must be a dictionary."))
        
        # Validate specific fields if they exist
        if "min_length" in rules and not isinstance(rules["min_length"], int):
            raise ValidationError(_("Password policy 'min_length' must be an integer."))
        if "min_length" in rules and rules["min_length"] < 1:
            raise ValidationError(_("Password policy 'min_length' must be at least 1."))
            
        if "max_length" in rules and not isinstance(rules["max_length"], int):
            raise ValidationError(_("Password policy 'max_length' must be an integer."))
        if "max_length" in rules and rules["max_length"] < 1:
            raise ValidationError(_("Password policy 'max_length' must be at least 1."))
            
        if "min_length" in rules and "max_length" in rules:
            if rules["min_length"] > rules["max_length"]:
                raise ValidationError(_("Password policy 'min_length' cannot be greater than 'max_length'."))
        
        if "history_size" in rules and not isinstance(rules["history_size"], int):
            raise ValidationError(_("Password policy 'history_size' must be an integer."))
        if "history_size" in rules and rules["history_size"] < 0:
            raise ValidationError(_("Password policy 'history_size' cannot be negative."))
            
        if "max_age_days" in rules and not isinstance(rules["max_age_days"], int):
            raise ValidationError(_("Password policy 'max_age_days' must be an integer."))
        if "max_age_days" in rules and rules["max_age_days"] < 0:
            raise ValidationError(_("Password policy 'max_age_days' cannot be negative."))
            
        if "lockout_attempts" in rules and not isinstance(rules["lockout_attempts"], int):
            raise ValidationError(_("Password policy 'lockout_attempts' must be an integer."))
        if "lockout_attempts" in rules and rules["lockout_attempts"] < 0:
            raise ValidationError(_("Password policy 'lockout_attempts' cannot be negative."))
            
        if "lockout_duration_minutes" in rules and not isinstance(rules["lockout_duration_minutes"], int):
            raise ValidationError(_("Password policy 'lockout_duration_minutes' must be an integer."))
        if "lockout_duration_minutes" in rules and rules["lockout_duration_minutes"] < 0:
            raise ValidationError(_("Password policy 'lockout_duration_minutes' cannot be negative."))
    
    def _validate_session_policy_rules(self):
        """Validate session policy rules."""
        rules = self.rules
        if not isinstance(rules, dict):
            raise ValidationError(_("Session policy rules must be a dictionary."))
        
        # Validate specific fields if they exist
        if "idle_timeout_minutes" in rules and not isinstance(rules["idle_timeout_minutes"], int):
            raise ValidationError(_("Session policy 'idle_timeout_minutes' must be an integer."))
        if "idle_timeout_minutes" in rules and rules["idle_timeout_minutes"] < 0:
            raise ValidationError(_("Session policy 'idle_timeout_minutes' cannot be negative."))
            
        if "absolute_timeout_minutes" in rules and not isinstance(rules["absolute_timeout_minutes"], int):
            raise ValidationError(_("Session policy 'absolute_timeout_minutes' must be an integer."))
        if "absolute_timeout_minutes" in rules and rules["absolute_timeout_minutes"] < 0:
            raise ValidationError(_("Session policy 'absolute_timeout_minutes' cannot be negative."))
    
    def get_password_policy_rules(self):
        """Get password policy rules with defaults."""
        if self.policy_type != "password":
            return {}
        
        defaults = {
            "min_length": 8,
            "max_length": 128,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_numbers": True,
            "require_special_chars": True,
            "history_size": 5,
            "max_age_days": 90,
            "lockout_attempts": 5,
            "lockout_duration_minutes": 30,
        }
        
        # Update defaults with actual rules
        defaults.update(self.rules)
        return defaults
    
    def get_session_policy_rules(self):
        """Get session policy rules with defaults."""
        if self.policy_type != "session":
            return {}
        
        defaults = {
            "idle_timeout_minutes": 30,
            "absolute_timeout_minutes": 480,  # 8 hours
            "concurrent_sessions_limit": 3,
        }
        
        # Update defaults with actual rules
        defaults.update(self.rules)
        return defaults
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Identity(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Core identity model for users, services, and organizations."""
    
    IDENTITY_TYPE_CHOICES = [
        ("user", _("User")),
        ("service", _("Service Account")),
        ("organization", _("Organization")),
        ("application", _("Application")),
        ("device", _("Device")),
    ]
    identity_type = models.CharField(
        _("Identity Type"), max_length=20, choices=IDENTITY_TYPE_CHOICES
    )
    
    # Core identity fields
    identifier = models.CharField(_("Identifier"), max_length=100, unique=True)
    display_name = models.CharField(_("Display Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    # Status and lifecycle
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SecurityStatus.CHOICES,
        default=SecurityStatus.ACTIVE,
    )
    confidentiality = models.CharField(
        _("Confidentiality Level"),
        max_length=30,
        choices=SecurityConfidentialityLevel.CHOICES,
        default=SecurityConfidentialityLevel.INTERNAL,
    )
    
    # Ownership and management
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_identities",
        verbose_name=_("Owner"),
    )
    managed_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="managed_identities",
        verbose_name=_("Managed By"),
    )
    
    # Timestamps
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated At"), auto_now=True)
    last_used_at = models.DateTimeField(_("Last Used At"), null=True, blank=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    
    # Metadata
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    attributes = models.JSONField(_("Additional Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Identity")
        verbose_name_plural = _("Identities")
        ordering = ("identity_type", "identifier")
        indexes = [
            models.Index(fields=["identity_type", "status"]),
            models.Index(fields=["identifier"]),
            models.Index(fields=["owner"]),
        ]
    
    def __str__(self):
        return f"{self.get_identity_type_display()}: {self.display_name}"
    
    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Identity has expired."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if identity has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def is_active(self):
        """Check if identity is active."""
        return self.status == SecurityStatus.ACTIVE and not self.is_expired


class ServiceIdentity(Identity):
    """Service account identity for automated systems."""
    
    SERVICE_TYPE_CHOICES = [
        ("api", _("API Service")),
        ("integration", _("Integration Service")),
        ("background", _("Background Service")),
        ("scheduled", _("Scheduled Service")),
        ("monitoring", _("Monitoring Service")),
        ("other", _("Other Service")),
    ]
    service_type = models.CharField(
        _("Service Type"), max_length=20, choices=SERVICE_TYPE_CHOICES
    )
    
    # Service-specific fields
    service_account_token = models.CharField(
        _("Service Account Token"), max_length=255, blank=True
    )
    token_expires_at = models.DateTimeField(
        _("Token Expires At"), null=True, blank=True
    )
    ip_allowlist = models.JSONField(_("IP Allowlist"), default=list, blank=True)
    allowed_operations = models.JSONField(
        _("Allowed Operations"), default=list, blank=True
    )
    
    class Meta:
        verbose_name = _("Service Identity")
        verbose_name_plural = _("Service Identities")
    
    def __str__(self):
        return f"{self.get_service_type_display()}: {self.display_name}"
    
    def clean(self):
        super().clean()
        if self.service_type == "api" and not self.service_account_token:
            raise ValidationError(_("API services must have a service account token."))


class OrganizationalIdentity(Identity):
    """Organizational identity for departments, teams, etc."""
    
    ORG_IDENTITY_TYPE_CHOICES = [
        ("department", _("Department")),
        ("team", _("Team")),
        ("division", _("Division")),
        ("unit", _("Unit")),
        ("committee", _("Committee")),
        ("working_group", _("Working Group")),
        ("other", _("Other Organizational")),
    ]
    org_identity_type = models.CharField(
        _("Organizational Identity Type"),
        max_length=20,
        choices=ORG_IDENTITY_TYPE_CHOICES,
    )
    
    # Organizational fields
    parent_organization = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="child_identities",
        verbose_name=_("Parent Organization"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="organizational_identities",
        verbose_name=_("Organization Unit"),
    )
    contact_person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contact_identities",
        verbose_name=_("Contact Person"),
    )
    
    class Meta:
        verbose_name = _("Organizational Identity")
        verbose_name_plural = _("Organizational Identities")
    
    def __str__(self):
        return f"{self.get_org_identity_type_display()}: {self.display_name}"


class Permission(UUIDModel, TimeStampedModel):
    """Granular permission definitions."""
    
    name = models.CharField(_("Permission Name"), max_length=100, unique=True)
    slug = models.SlugField(_("Permission Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    # Permission categorization
    module = models.CharField(
        _("Module"), max_length=50, choices=[(m, m) for m in SecurityModule.__dict__.values() if isinstance(m, str)]
    )
    resource_type = models.CharField(_("Resource Type"), max_length=50)
    action = models.CharField(_("Action"), max_length=50)
    
    # Permission properties
    is_system = models.BooleanField(_("Is System Permission"), default=False)
    is_assignable = models.BooleanField(_("Is Assignable"), default=True)
    requires_approval = models.BooleanField(_("Requires Approval"), default=False)
    
    # Conditions and constraints
    conditions = models.JSONField(_("Permission Conditions"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")
        ordering = ("module", "resource_type", "action", "name")
        indexes = [
            models.Index(fields=["module", "resource_type"]),
            models.Index(fields=["name"]),
        ]
    
    def __str__(self):
        return f"{self.module}: {self.resource_type}.{self.action} ({self.name})"
    
    @property
    def full_name(self):
        """Get the full permission name."""
        return f"{self.module}:{self.resource_type}:{self.action}"


class RolePermission(UUIDModel, TimeStampedModel, CreatedByModel):
    """Role-to-permission mappings with metadata."""
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
        verbose_name=_("Role"),
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
        verbose_name=_("Permission"),
    )
    
    # Permission metadata
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_role_permissions",
        verbose_name=_("Granted By"),
    )
    granted_at = models.DateTimeField(_("Granted At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    # Conditions and constraints
    conditions = models.JSONField(_("Permission Conditions"), default=dict, blank=True)
    justification = models.TextField(_("Justification"), blank=True)
    
    class Meta:
        verbose_name = _("Role Permission")
        verbose_name_plural = _("Role Permissions")
        unique_together = [["role", "permission"]]
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["permission", "is_active"]),
        ]
    
    def __str__(self):
        return f"{self.role.name} -> {self.permission.name}"
    
    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Permission grant has expired."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if permission grant has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def is_valid(self):
        """Check if permission grant is valid."""
        return self.is_active and not self.is_expired


class IdentityRole(UUIDModel, TimeStampedModel, CreatedByModel):
    """Identity-to-role assignments."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="identity_roles",
        verbose_name=_("Identity"),
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="identity_roles",
        verbose_name=_("Role"),
    )
    
    # Assignment metadata
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_identity_roles",
        verbose_name=_("Assigned By"),
    )
    assigned_at = models.DateTimeField(_("Assigned At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    # Conditions and constraints
    conditions = models.JSONField(_("Assignment Conditions"), default=dict, blank=True)
    justification = models.TextField(_("Justification"), blank=True)
    delegation_chain = models.JSONField(
        _("Delegation Chain"), default=list, blank=True
    )  # For tracking delegated roles
    
    class Meta:
        verbose_name = _("Identity Role")
        verbose_name_plural = _("Identity Roles")
        unique_together = [["identity", "role"]]
        indexes = [
            models.Index(fields=["identity", "is_active"]),
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["assigned_by"]),
        ]
    
    def __str__(self):
        return f"{self.identity.display_name} -> {self.role.name}"
    
    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Role assignment has expired."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if role assignment has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def is_valid(self):
        """Check if role assignment is valid."""
        return self.is_active and not self.is_expired


class LoginAttempt(UUIDModel, TimeStampedModel):
    """Login attempt tracking for security monitoring."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="login_attempts",
        verbose_name=_("Identity"),
    )
    
    # Attempt details
    username_attempted = models.CharField(_("Username Attempted"), max_length=255)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    # Attempt outcome
    SUCCESS = "success"
    FAILED_INVALID_CREDENTIALS = "failed_invalid_credentials"
    FAILED_ACCOUNT_LOCKED = "failed_account_locked"
    FAILED_EXPIRED = "failed_expired"
    FAILED_DISABLED = "failed_disabled"
    FAILED_MFA_REQUIRED = "failed_mfa_required"
    FAILED_MFA_INVALID = "failed_mfa_invalid"
    FAILED_OTHER = "failed_other"
    
    ATTEMPT_OUTCOME_CHOICES = [
        (SUCCESS, _("Success")),
        (FAILED_INVALID_CREDENTIALS, _("Invalid Credentials")),
        (FAILED_ACCOUNT_LOCKED, _("Account Locked")),
        (FAILED_EXPIRED, _("Account Expired")),
        (FAILED_DISABLED, _("Account Disabled")),
        (FAILED_MFA_REQUIRED, _("MFA Required")),
        (FAILED_MFA_INVALID, _("Invalid MFA Code")),
        (FAILED_OTHER, _("Other Failure")),
    ]
    outcome = models.CharField(
        _("Outcome"), max_length=30, choices=ATTEMPT_OUTCOME_CHOICES
    )
    
    # Failure details
    failure_reason = models.TextField(_("Failure Reason"), blank=True)
    
    # Security assessment
    risk_score = models.PositiveSmallIntegerField(
        _("Risk Score"), 
        help_text=_("Risk score from 0-100"),
        default=0
    )
    is_suspicious = models.BooleanField(_("Is Suspicious"), default=False)
    
    # Geolocation (if available)
    country_code = models.CharField(_("Country Code"), max_length=2, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _("Login Attempt")
        verbose_name_plural = _("Login Attempts")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["identity", "-created_at"]),
            models.Index(fields=["ip_address", "-created_at"]),
            models.Index(fields=["outcome", "-created_at"]),
            models.Index(fields=["is_suspicious"]),
        ]
    
    def __str__(self):
        return f"Login attempt: {self.username_attempted} from {self.ip_address} ({self.get_outcome_display()})"


class AccessReview(UUIDModel, TimeStampedModel, CreatedByModel):
    """Access review campaigns."""
    
    name = models.CharField(_("Review Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    
    # Review scope
    review_type = models.CharField(
        _("Review Type"),
        max_length=20,
        choices=[
            ("role", _("Role Assignment Review")),
            ("permission", _("Permission Review")),
            ("identity", _("Identity Review")),
            ("session", _("Session Review")),
            ("api_key", _("API Key Review")),
            ("service_account", _("Service Account Review")),
        ],
    )
    target_identity = models.ForeignKey(
        Identity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_reviews_as_target",
        verbose_name=_("Target Identity"),
    )
    target_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_reviews_as_target",
        verbose_name=_("Target Role"),
    )
    target_permission = models.ForeignKey(
        Permission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_reviews_as_target",
        verbose_name=_("Target Permission"),
    )
    
    # Review scheduling
    started_at = models.DateTimeField(_("Started At"))
    due_date = models.DateTimeField(_("Due Date"))
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    
    # Review status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=AccessReviewStatus.CHOICES,
        default=AccessReviewStatus.PENDING,
    )
    
    # Review configuration
    auto_approve_low_risk = models.BooleanField(
        _("Auto-Approve Low Risk"), default=False
    )
    require_justification_for_changes = models.BooleanField(
        _("Require Justification for Changes"), default=True
    )
    escalate_overdue_reviews = models.BooleanField(
        _("Escalate Overdue Reviews"), default=True
    )
    
    # Review results
    total_items_reviewed = models.PositiveIntegerField(
        _("Total Items Reviewed"), default=0
    )
    items_approved = models.PositiveIntegerField(
        _("Items Approved"), default=0
    )
    items_revoked = models.PositiveIntegerField(
        _("Items Revoked"), default=0
    )
    items_modified = models.PositiveIntegerField(
        _("Items Modified"), default=0
    )
    items_escalated = models.PositiveIntegerField(
        _("Items Escalated"), default=0
    )
    
    # Review management
    reviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="access_reviews_as_reviewer",
        verbose_name=_("Reviewers"),
    )
    lead_reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lead_access_reviews",
        verbose_name=_("Lead Reviewer"),
    )
    
    class Meta:
        verbose_name = _("Access Review")
        verbose_name_plural = _("Access Reviews")
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["review_type", "status"]),
            models.Index(fields=["due_date"]),
            models.Index(fields=["started_at"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_review_type_display()})"
    
    def clean(self):
        if self.due_date <= self.started_at:
            raise ValidationError(_("Due date must be after start date."))
        if self.completed_at and self.completed_at < self.started_at:
            raise ValidationError(_("Completion date must be after start date."))
        if self.completed_at and self.due_date and self.completed_at > self.due_date:
            raise ValidationError(_("Completion date cannot be after due date."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if review is overdue."""
        return (
            self.status in [AccessReviewStatus.PENDING, AccessReviewStatus.IN_PROGRESS]
            and self.due_date <= timezone.now()
        )
    
    @property
    def completion_percentage(self):
        """Get completion percentage."""
        if self.total_items_reviewed == 0:
            return 0
        return (
            (self.items_approved + self.items_revoked + self.items_modified + self.items_escalated)
            / self.total_items_reviewed
        ) * 100


class AccessReviewItem(UUIDModel, TimeStampedModel):
    """Individual items being reviewed in an access review."""
    
    access_review = models.ForeignKey(
        AccessReview,
        on_delete=models.CASCADE,
        related_name="review_items",
        verbose_name=_("Access Review"),
    )
    
    # What is being reviewed
    identity = models.ForeignKey(
        Identity,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_review_items",
        verbose_name=_("Identity"),
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_review_items",
        verbose_name=_("Role"),
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_review_items",
        verbose_name=_("Permission"),
    )
    identity_role = models.ForeignKey(
        "IdentityRole",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_review_items",
        verbose_name=_("Identity Role"),
    )
    
    # Review decision
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="access_review_decisions",
        verbose_name=_("Reviewer"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    decision = models.CharField(
        _("Decision"),
        max_length=20,
        choices=AccessReviewDecision.CHOICES,
    )
    justification = models.TextField(_("Justification"), blank=True)
    
    # Review metadata
    risk_level = models.CharField(
        _("Risk Level"),
        max_length=10,
        choices=[
            ("low", _("Low")),
            ("medium", _("Medium")),
            ("high", _("High")),
            ("critical", _("Critical")),
        ],
        default="medium",
    )
    risk_factors = models.JSONField(_("Risk Factors"), default=list, blank=True)
    
    # Previous and new values (for changes)
    previous_value = models.JSONField(_("Previous Value"), null=True, blank=True)
    new_value = models.JSONField(_("New Value"), null=True, blank=True)
    change_reason = models.TextField(_("Change Reason"), blank=True)
    
    class Meta:
        verbose_name = _("Access Review Item")
        verbose_name_plural = _("Access Review Items")
        ordering = ("-reviewed_at",)
        indexes = [
            models.Index(fields=["access_review", "reviewed_at"]),
            models.Index(fields=["decision"]),
            models.Index(fields=["risk_level"]),
        ]
    
    def __str__(self):
        if self.identity:
            return f"Review: {self.identity.display_name} -> {self.get_decision_display()}"
        elif self.role:
            return f"Review: {self.role.name} -> {self.get_decision_display()}"
        elif self.permission:
            return f"Review: {self.permission.name} -> {self.get_decision_display()}"
        return f"Review Item -> {self.get_decision_display()}"
    
    def clean(self):
        if not self.reviewed_at:
            self.reviewed_at = timezone.now()
        if self.decision not in dict(AccessReviewDecision.CHOICES):
            raise ValidationError(_("Invalid decision."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class RoleHierarchy(UUIDModel, TimeStampedModel, CreatedByModel):
    """Role hierarchy definitions for inheritance."""
    
    parent_role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="child_roles",
        verbose_name=_("Parent Role"),
    )
    child_role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="parent_roles",
        verbose_name=_("Child Role"),
    )
    
    # Hierarchy properties
    inherit_permissions = models.BooleanField(_("Inherit Permissions"), default=True)
    inherit_role_permissions = models.BooleanField(_("Inherit Role Permissions"), default=True)
    
    # Metadata
    justification = models.TextField(_("Justification"), blank=True)
    
    class Meta:
        verbose_name = _("Role Hierarchy")
        verbose_name_plural = _("Role Hierarchies")
        unique_together = [["parent_role", "child_role"]]
        indexes = [
            models.Index(fields=["parent_role"]),
            models.Index(fields=["child_role"]),
        ]
    
    def __str__(self):
        return f"{self.parent_role.name} -> {self.child_role.name}"
    
    def clean(self):
        if self.parent_role == self.child_role:
            raise ValidationError(_("A role cannot be parent of itself."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class PermissionGrant(UUIDModel, TimeStampedModel, CreatedByModel):
    """Direct permission grants to identities (bypassing roles when needed)."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="permission_grants",
        verbose_name=_("Identity"),
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="permission_grants",
        verbose_name=_("Permission"),
    )
    
    # Grant metadata
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="granted_permissions",
        verbose_name=_("Granted By"),
    )
    granted_at = models.DateTimeField(_("Granted At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    
    # Conditions and constraints
    conditions = models.JSONField(_("Permission Conditions"), default=dict, blank=True)
    justification = models.TextField(_("Justification"), blank=True)
    
    class Meta:
        verbose_name = _("Permission Grant")
        verbose_name_plural = _("Permission Grants")
        unique_together = [["identity", "permission"]]
        indexes = [
            models.Index(fields=["identity", "is_active"]),
            models.Index(fields=["permission", "is_active"]),
            models.Index(fields=["granted_by"]),
        ]
    
    def __str__(self):
        return f"{self.identity.display_name} -> {self.permission.name}"
    
    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Permission grant has expired."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if permission grant has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def is_valid(self):
        """Check if permission grant is valid."""
        return self.is_active and not self.is_expired


class Session(UUIDModel, TimeStampedModel):
    """User and service sessions."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("Identity"),
    )
    
    # Session identification
    session_key = models.CharField(_("Session Key"), max_length=255, unique=True)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    # Session status
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SessionStatus.CHOICES,
        default=SessionStatus.ACTIVE,
    )
    
    # Timestamps
    started_at = models.DateTimeField(_("Started At"), auto_now_add=True)
    last_activity_at = models.DateTimeField(_("Last Activity At"), auto_now=True)
    expires_at = models.DateTimeField(_("Expires At"))
    terminated_at = models.DateTimeField(_("Terminated At"), null=True, blank=True)
    
    # Session timeout configuration
    idle_timeout_minutes = models.PositiveIntegerField(
        _("Idle Timeout Minutes"),
        help_text=_("Minutes of inactivity before session expires"),
        default=30
    )
    absolute_timeout_minutes = models.PositiveIntegerField(
        _("Absolute Timeout Minutes"),
        help_text=_("Maximum session duration regardless of activity"),
        default=480  # 8 hours
    )
    
    # Session properties
    is_secure = models.BooleanField(_("Is Secure Connection"), default=False)
    is_mfa_used = models.BooleanField(_("MFA Used"), default=False)
    mfa_method = models.CharField(
        _("MFA Method"), max_length=20, choices=MFAMethod.CHOICES, blank=True
    )
    device_fingerprint = models.CharField(
        _("Device Fingerprint"), max_length=255, blank=True
    )
    
    # Concurrent session control
    superseded_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="superseded_by_session",
        verbose_name=_("Superseded By"),
        help_text=_("Session that superseded this one (for concurrent session limits)")
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="supersedes_session",
        verbose_name=_("Supersedes"),
        help_text=_("Session that this one superseded (for concurrent session limits)")
    )
    
    # Metadata
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    attributes = models.JSONField(_("Session Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Session")
        verbose_name_plural = _("Sessions")
        ordering = ("-started_at",)
        indexes = [
            models.Index(fields=["identity", "status"]),
            models.Index(fields=["session_key"]),
            models.Index(fields=["ip_address"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["superseded_by"]),
            models.Index(fields=["supersedes"]),
        ]
    
    def __str__(self):
        return f"{self.identity.display_name} session ({self.session_key[:8]}...)"
    
    def clean(self):
        if self.expires_at <= self.started_at:
            raise ValidationError(_("Expiration time must be after start time."))
        if self.terminated_at and self.terminated_at <= self.started_at:
            raise ValidationError(_("Termination time must be after start time."))
        if self.terminated_at and self.expires_at and self.terminated_at > self.expires_at:
            raise ValidationError(_("Termination time cannot be after expiration time."))
        if self.superseded_by and self.superseded_by == self:
            raise ValidationError(_("Session cannot supersede itself."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if session has expired."""
        return self.expires_at <= timezone.now()
    
    @property
    def is_idle_expired(self):
        """Check if session has expired due to inactivity."""
        idle_expiry = self.last_activity_at + timezone.timedelta(minutes=self.idle_timeout_minutes)
        return idle_expiry <= timezone.now()
    
    @property
    def is_active(self):
        """Check if session is active."""
        return (
            self.status == SessionStatus.ACTIVE
            and not self.is_expired
            and not self.is_idle_expired
            and self.terminated_at is None
        )
    
    @property
    def duration(self):
        """Get session duration."""
        end_time = self.terminated_at or timezone.now()
        return end_time - self.started_at
    
    @property
    def idle_duration(self):
        """Get idle duration (time since last activity)."""
        return timezone.now() - self.last_activity_at
    
    def extend(self, extension_minutes):
        """Extend session expiration."""
        if self.is_expired:
            raise ValidationError(_("Cannot extend expired session."))
        self.expires_at = timezone.now() + timezone.timedelta(minutes=extension_minutes)
        self.save(update_fields=["expires_at", "updated_at"])
    
    def terminate(self, terminated_by=None, terminated_by_ip=None):
        """Terminate session."""
        self.status = SessionStatus.TERMINATED
        self.terminated_at = timezone.now()
        if terminated_by:
            # In a full implementation, we'd record who terminated it
            pass
        if terminated_by_ip:
            # Record terminating IP for security audit
            pass
        self.save(update_fields=["status", "terminated_at", "updated_at"])
    
    def supersede(self, new_session):
        """Mark this session as superseded by another session (for concurrent session limits)."""
        self.status = SessionStatus.SUPERSEDED
        self.superseded_by = new_session
        self.save(update_fields=["status", "superseded_by", "updated_at"])
        
        # Update the new session to reference this one as what it superseded
        new_session.supersedes = self
        new_session.save(update_fields=["supersedes", "updated_at"])
    
    def record_activity(self, ip_address=None, user_agent=None):
        """Record session activity for idle timeout calculation."""
        self.last_activity_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save(update_fields=["last_activity_at", "ip_address", "user_agent", "updated_at"])


class MFAEnrollment(UUIDModel, TimeStampedModel, CreatedByModel):
    """Multi-Factor Authentication enrollment for identities."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="mfa_enrollments",
        verbose_name=_("Identity"),
    )
    
    # MFA method
    method = models.CharField(
        _("MFA Method"), max_length=20, choices=MFAMethod.CHOICES
    )
    
    # Enrollment details
    is_primary = models.BooleanField(_("Is Primary Method"), default=False)
    is_backup = models.BooleanField(_("Is Backup Method"), default=False)
    enrolled_at = models.DateTimeField(_("Enrolled At"), auto_now_add=True)
    enrolled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mfa_enrollments_by",
        verbose_name=_("Enrolled By"),
    )
    
    # Method-specific data (encrypted)
    secret_key = models.CharField(_("Secret Key"), max_length=255, blank=True)  # For TOTP
    phone_number = models.CharField(_("Phone Number"), max_length=20, blank=True)  # For SMS
    email_address = models.EmailField(_("Email Address"), blank=True)  # For Email
    
    # Backup codes (for recovery)
    backup_codes = models.JSONField(_("Backup Codes"), default=list, blank=True)
    backup_codes_used = models.JSONField(_("Used Backup Codes"), default=list, blank=True)
    
    # Trusted device management
    is_trusted_device = models.BooleanField(_("Is Trusted Device"), default=False)
    device_name = models.CharField(_("Device Name"), max_length=100, blank=True)
    device_fingerprint = models.CharField(_("Device Fingerprint"), max_length=255, blank=True)
    trusted_since = models.DateTimeField(_("Trusted Since"), null=True, blank=True)
    trust_expires_at = models.DateTimeField(_("Trust Expires At"), null=True, blank=True)
    
    # Status
    is_enabled = models.BooleanField(_("Is Enabled"), default=True)
    last_used_at = models.DateTimeField(_("Last Used At"), null=True, blank=True)
    usage_count = models.PositiveIntegerField(_("Usage Count"), default=0)
    failed_attempt_count = models.PositiveIntegerField(_("Failed Attempt Count"), default=0)
    locked_until = models.DateTimeField(_("Locked Until"), null=True, blank=True)
    
    # Metadata
    name = models.CharField(_("Friendly Name"), max_length=100, blank=True)  # e.g., "Work Phone"
    attributes = models.JSONField(_("Additional Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("MFA Enrollment")
        verbose_name_plural = _("MFA Enrollments")
        unique_together = [["identity", "method"]]
        indexes = [
            models.Index(fields=["identity", "is_enabled"]),
            models.Index(fields=["method", "is_enabled"]),
            models.Index(fields=["is_trusted_device"]),
            models.Index(fields=["device_fingerprint"]),
        ]
    
    def __str__(self):
        return f"{self.identity.display_name} - {self.get_method_display()}"
    
    def clean(self):
        # Validate method-specific requirements
        if self.method == MFAMethod.TOTP and not self.secret_key:
            raise ValidationError(_("TOTP requires a secret key."))
        if self.method == MFAMethod.SMS and not self.phone_number:
            raise ValidationError(_("SMS requires a phone number."))
        if self.method == MFAMethod.EMAIL and not self.email_address:
            raise ValidationError(_("Email requires an email address."))
        
        # Validate trusted device fields
        if self.is_trusted_device and not self.device_fingerprint:
            raise ValidationError(_("Trusted device requires a device fingerprint."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if enrollment has expired."""
        return self.trust_expires_at and self.trust_expires_at <= timezone.now()
    
    @property
    def is_locked(self):
        """Check if enrollment is locked due to failed attempts."""
        return self.locked_until and self.locked_until > timezone.now()
    
    @property
    def is_trusted(self):
        """Check if device is trusted and trust is valid."""
        return (
            self.is_trusted_device
            and self.trust_expires_at
            and self.trust_expires_at > timezone.now()
        )
    
    def trust_device(self, device_name, device_fingerprint, trust_duration_days=30):
        """Mark device as trusted."""
        self.is_trusted_device = True
        self.device_name = device_name
        self.device_fingerprint = device_fingerprint
        self.trusted_since = timezone.now()
        self.trust_expires_at = timezone.now() + timezone.timedelta(days=trust_duration_days)
        self.save(update_fields=[
            "is_trusted_device", "device_name", "device_fingerprint",
            "trusted_since", "trust_expires_at", "updated_at"
        ])
    
    def revoke_trust(self):
        """Revoke device trust."""
        self.is_trusted_device = False
        self.device_name = ""
        self.device_fingerprint = ""
        self.trusted_since = None
        self.trust_expires_at = None
        self.save(update_fields=[
            "is_trusted_device", "device_name", "device_fingerprint",
            "trusted_since", "trust_expires_at", "updated_at"
        ])
    
    def record_failed_attempt(self):
        """Record a failed MFA attempt."""
        self.failed_attempt_count += 1
        # Lock after 5 failed attempts for 15 minutes
        if self.failed_attempt_count >= 5:
            self.locked_until = timezone.now() + timezone.timedelta(minutes=15)
        self.save(update_fields=["failed_attempt_count", "locked_until", "updated_at"])
    
    def record_successful_attempt(self):
        """Record a successful MFA attempt."""
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.failed_attempt_count = 0  # Reset failed attempts on success
        self.locked_until = None  # Unlock on success
        self.save(update_fields=["last_used_at", "usage_count", "failed_attempt_count", "locked_until", "updated_at"])


class MFAVerificationAttempt(UUIDModel, TimeStampedModel):
    """MFA verification attempts."""
    
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="mfa_verification_attempts",
        verbose_name=_("Identity"),
    )
    enrollment = models.ForeignKey(
        MFAEnrollment,
        on_delete=models.CASCADE,
        related_name="verification_attempts",
        verbose_name=_("MFA Enrollment"),
    )
    
    # Attempt details
    challenge = models.CharField(_("Challenge"), max_length=255, blank=True)
    response = models.CharField(_("Response"), max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(_("IP Address"))
    user_agent = models.TextField(_("User Agent"), blank=True)
    
    # Outcome
    SUCCESS = "success"
    FAILED_INVALID_CODE = "failed_invalid_code"
    FAILED_EXPIRED_CODE = "failed_expired_code"
    FAILED_RATE_LIMITED = "failed_rate_limited"
    FAILED_OTHER = "failed_other"
    
    ATTEMPT_OUTCOME_CHOICES = [
        (SUCCESS, _("Success")),
        (FAILED_INVALID_CODE, _("Invalid Code")),
        (FAILED_EXPIRED_CODE, _("Expired Code")),
        (FAILED_RATE_LIMITED, _("Rate Limited")),
        (FAILED_OTHER, _("Other Failure")),
    ]
    outcome = models.CharField(
        _("Outcome"), max_length=20, choices=ATTEMPT_OUTCOME_CHOICES
    )
    
    # Timestamps
    attempted_at = models.DateTimeField(_("Attempted At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"))  # For time-sensitive challenges
    
    # Metadata
    trusted_device = models.BooleanField(_("Trusted Device"), default=False)
    backup_code_used = models.BooleanField(_("Backup Code Used"), default=False)
    # Risk assessment
    risk_score = models.PositiveSmallIntegerField(
        _("Risk Score"), 
        help_text=_("Risk score from 0-100"),
        default=0
    )
    is_suspicious = models.BooleanField(_("Is Suspicious"), default=False)
    
    # Geolocation (if available)
    country_code = models.CharField(_("Country Code"), max_length=2, blank=True)
    city = models.CharField(_("City"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _("MFA Verification Attempt")
        verbose_name_plural = _("MFA Verification Attempts")
        ordering = ("-attempted_at",)
        indexes = [
            models.Index(fields=["identity", "-attempted_at"]),
            models.Index(fields=["enrollment", "-attempted_at"]),
            models.Index(fields=["outcome", "-attempted_at"]),
            models.Index(fields=["is_suspicious"]),
            models.Index(fields=["trusted_device"]),
        ]
    
    def __str__(self):
        return f"MFA attempt: {self.identity.display_name} ({self.get_outcome_display()})"
    
    def clean(self):
        if self.expires_at <= self.attempted_at:
            raise ValidationError(_("Expiration time must be after attempt time."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if verification attempt has expired."""
        return self.expires_at <= timezone.now()
    
    @property
    def is_successful(self):
        """Check if verification attempt was successful."""
        return self.outcome == self.SUCCESS
    
    def mark_as_suspicious(self, reason=""):
        """Mark verification attempt as suspicious."""
        self.is_suspicious = True
        if reason:
            self.attributes = self.attributes or {}
            self.attributes["suspicious_reason"] = reason
        self.save(update_fields=["is_suspicious", "attributes", "updated_at"])


class APICredential(UUIDModel, TimeStampedModel):
    """API credentials for secure API access."""
    
    name = models.CharField(_("Credential Name"), max_length=150)
    slug = models.SlugField(_("Credential Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    # Associated identity/service
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="api_credentials",
        verbose_name=_("Identity"),
        help_text=_("Identity that owns this credential")
    )
    
    # Credential types
    CREDENTIAL_TYPE_CHOICES = [
        ("api_key", _("API Key")),
        ("oauth_token", _("OAuth Token")),
        ("jwt_token", _("JWT Token")),
        ("basic_auth", _("Basic Auth")),
        ("bearer_token", _("Bearer Token")),
        ("custom", _("Custom")),
    ]
    credential_type = models.CharField(
        _("Credential Type"), max_length=20, choices=CREDENTIAL_TYPE_CHOICES
    )
    
    # Credential data (encrypted in production)
    credential_key = models.CharField(_("Credential Key"), max_length=255)
    credential_secret = models.CharField(_("Credential Secret"), max_length=255, blank=True)
    
    # Associated API/service
    service_name = models.CharField(_("Service Name"), max_length=100)
    service_url = models.URLField(_("Service URL"), blank=True)
    
    # Usage restrictions
    ip_allowlist = models.JSONField(_("IP Allowlist"), default=list, blank=True)
    allowed_endpoints = models.JSONField(_("Allowed Endpoints"), default=list, blank=True)
    allowed_methods = models.JSONField(_("Allowed HTTP Methods"), default=list, blank=True)
    
    # Rate limiting
    rate_limit_per_hour = models.PositiveIntegerField(
        _("Rate Limit Per Hour"), 
        default=1000,
        help_text=_("Maximum API calls per hour")
    )
    rate_limit_per_day = models.PositiveIntegerField(
        _("Rate Limit Per Day"), 
        default=10000,
        help_text=_("Maximum API calls per day")
    )
    
    # Status and lifecycle
    is_active = models.BooleanField(_("Is Active"), default=True)
    expires_at = models.DateTimeField(_("Expires At"), null=True, blank=True)
    last_used_at = models.DateTimeField(_("Last Used At"), null=True, blank=True)
    usage_count = models.PositiveBigIntegerField(_("Usage Count"), default=0)
    
    # Security
    is_compromised = models.BooleanField(_("Is Compromised"), default=False)
    compromised_at = models.DateTimeField(_("Compromised At"), null=True, blank=True)
    compromised_reason = models.TextField(_("Compromised Reason"), blank=True)
    
    # Metadata
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    attributes = models.JSONField(_("Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("API Credential")
        verbose_name_plural = _("API Credentials")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["identity", "is_active"]),
            models.Index(fields=["service_name", "is_active"]),
            models.Index(fields=["credential_type", "is_active"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_compromised"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_credential_type_display()})"
    
    def clean(self):
        if self.expires_at and self.expires_at <= timezone.now():
            raise ValidationError(_("Credential has expired."))
        
        # Validate credential-specific requirements
        if self.credential_type == "api_key" and not self.credential_key:
            raise ValidationError(_("API Key credential requires a key."))
        if self.credential_type in ["oauth_token", "jwt_token", "bearer_token"] and not self.credential_key:
            raise ValidationError(_("{0} credential requires a token.").format(
                self.get_credential_type_display()
            ))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if credential has expired."""
        return self.expires_at and self.expires_at <= timezone.now()
    
    @property
    def is_valid(self):
        """Check if credential is valid for use."""
        return (
            self.is_active
            and not self.is_expired
            and not self.is_compromised
        )
    
    def record_usage(self):
        """Record credential usage."""
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save(update_fields=["last_used_at", "usage_count", "updated_at"])
    
    def mark_compromised(self, reason=""):
        """Mark credential as compromised."""
        self.is_compromised = True
        self.compromised_at = timezone.now()
        if reason:
            self.compromised_reason = reason
        self.is_active = False  # Deactivate when compromised
        self.save(update_fields=[
            "is_compromised", "compromised_at", "compromised_reason", 
            "is_active", "updated_at"
        ])
    
    def rotate_credential(self, new_key, new_secret=""):
        """Rotate credential with new key/secret."""
        # In a full implementation, we would keep history of old credentials
        self.credential_key = new_key
        if new_secret:
            self.credential_secret = new_secret
        # Reset compromise status when rotating
        self.is_compromised = False
        self.compromised_at = None
        self.compromised_reason = ""
        self.save(update_fields=[
            "credential_key", "credential_secret",
            "is_compromised", "compromised_at", "compromised_reason",
            "updated_at"
        ])


class APIAccessToken(UUIDModel, TimeStampedModel):
    """API access tokens for temporary access."""
    
    credential = models.ForeignKey(
        APICredential,
        on_delete=models.CASCADE,
        related_name="access_tokens",
        verbose_name=_("API Credential"),
    )
    
    # Token identification
    token = models.CharField(_("Token"), max_length=255, unique=True)
    token_type = models.CharField(
        _("Token Type"), max_length=50, default="Bearer"
    )
    
    # Associated identity (if different from credential owner)
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_access_tokens",
        verbose_name=_("Identity"),
        help_text=_("Identity associated with this token (if different from credential owner)")
    )
    
    # Token scopes/permissions
    scopes = models.JSONField(_("Token Scopes"), default=list, blank=True)
    permissions = models.JSONField(_("Token Permissions"), default=list, blank=True)
    
    # Validity
    issued_at = models.DateTimeField(_("Issued At"), auto_now_add=True)
    expires_at = models.DateTimeField(_("Expires At"))
    not_before = models.DateTimeField(_("Not Before"), null=True, blank=True)
    
    # Usage tracking
    last_used_at = models.DateTimeField(_("Last Used At"), null=True, blank=True)
    usage_count = models.PositiveIntegerField(_("Usage Count"), default=0)
    
    # Status
    is_revoked = models.BooleanField(_("Is Revoked"), default=False)
    revoked_at = models.DateTimeField(_("Revoked At"), null=True, blank=True)
    revoked_reason = models.TextField(_("Revoked Reason"), blank=True)
    
    class Meta:
        verbose_name = _("API Access Token")
        verbose_name_plural = _("API Access Tokens")
        ordering = ("-issued_at",)
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["credential", "-issued_at"]),
            models.Index(fields=["identity", "-issued_at"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["is_revoked"]),
        ]
    
    def __str__(self):
        return f"{self.token[:20]}... ({self.credential.name})"
    
    def clean(self):
        if self.expires_at <= self.issued_at:
            raise ValidationError(_("Expiration time must be after issue time."))
        if self.not_before and self.not_before < self.issued_at:
            raise ValidationError(_("Not before time must be after issue time."))
        if self.not_before and self.expires_at and self.not_before > self.expires_at:
            raise ValidationError(_("Not before time cannot be after expiration time."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if token has expired."""
        return self.expires_at <= timezone.now()
    
    @property
    def is_valid(self):
        """Check if token is valid for use."""
        now = timezone.now()
        return (
            not self.is_expired
            and not self.is_revoked
            and (not self.not_before or self.not_before <= now)
        )
    
    def record_usage(self):
        """Record token usage."""
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save(update_fields=["last_used_at", "usage_count", "updated_at"])
    
    def revoke(self, reason=""):
        """Revoke token."""
        self.is_revoked = True
        self.revoked_at = timezone.now()
        if reason:
            self.revoked_reason = reason
        self.save(update_fields=["is_revoked", "revoked_at", "revoked_reason", "updated_at"])


class APIRateLimit(UUIDModel, TimeStampedModel):
    """API rate limiting tracking."""
    
    credential = models.ForeignKey(
        APICredential,
        on_delete=models.CASCADE,
        related_name="rate_limits",
        verbose_name=_("API Credential"),
    )
    identity = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_rate_limits",
        verbose_name=_("Identity"),
        help_text=_("Identity making the API calls (if known)")
    )
    
    # Time window
    window_start = models.DateTimeField(_("Window Start"))
    window_end = models.DateTimeField(_("Window End"))
    
    # Request counts
    request_count = models.PositiveIntegerField(_("Request Count"), default=0)
    blocked_count = models.PositiveIntegerField(_("Blocked Count"), default=0)
    
    # Endpoint and method details
    endpoint = models.CharField(_("Endpoint"), max_length=255, blank=True)
    method = models.CharField(_("HTTP Method"), max_length=10, blank=True)
    status_code = models.PositiveSmallIntegerField(_("Status Code"), null=True, blank=True)
    
    # IP address (if available)
    ip_address = models.GenericIPAddressField(_("IP Address"), blank=True, null=True)
    
    class Meta:
        verbose_name = _("API Rate Limit")
        verbose_name_plural = _("API Rate Limits")
        ordering = ("-window_start",)
        unique_together = [["credential", "window_start", "endpoint", "method"]]
        indexes = [
            models.Index(fields=["credential", "-window_start"]),
            models.Index(fields=["identity", "-window_start"]),
            models.Index(fields=["endpoint", "-window_start"]),
            models.Index(fields=["ip_address", "-window_start"]),
        ]
    
    def __str__(self):
        return f"Rate limit: {self.credential.name} - {self.window_start}"
    
    def clean(self):
        if self.window_end <= self.window_start:
            raise ValidationError(_("Window end must be after window start."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_exceeded(self):
        """Check if rate limit is exceeded."""
        return self.request_count >= self.credential.rate_limit_per_hour
    
    def increment(self, count=1):
        """Increment request count."""
        self.request_count += count
        self.save(update_fields=["request_count", "updated_at"])
    
    def block_request(self, count=1):
        """Block request(s) due to rate limiting."""
        self.blocked_count += count
        self.save(update_fields=["blocked_count", "updated_at"])


class DatabaseSecurityPolicy(UUIDModel, TimeStampedModel):
    """Database security policies and configurations."""
    
    name = models.CharField(_("Policy Name"), max_length=150)
    slug = models.SlugField(_("Policy Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    
    # Database association
    database_identifier = models.CharField(_("Database Identifier"), max_length=100)
    database_type = models.CharField(
        _("Database Type"), max_length=50,
        help_text=_("e.g., postgresql, mysql, sqlite")
    )
    host = models.CharField(_("Host"), max_length=255, blank=True)
    port = models.PositiveIntegerField(_("Port"), null=True, blank=True)
    database_name = models.CharField(_("Database Name"), max_length=100, blank=True)
    
    # Security settings
    require_ssl = models.BooleanField(_("Require SSL/TLS"), default=True)
    ssl_cert_path = models.CharField(_("SSL Certificate Path"), max_length=255, blank=True)
    ssl_key_path = models.CharField(_("SSL Key Path"), max_length=255, blank=True)
    
    # Authentication
    auth_method = models.CharField(
        _("Authentication Method"), max_length=50,
        help_text=_("e.g., password, certificate, ldap")
    )
    use_connection_pooling = models.BooleanField(_("Use Connection Pooling"), default=True)
    max_connections = models.PositiveIntegerField(_("Max Connections"), default=100)
    
    # Statement timeout (in milliseconds)
    statement_timeout_ms = models.PositiveIntegerField(
        _("Statement Timeout (ms)"), 
        default=30000,  # 30 seconds
        help_text=_("Maximum time to execute a statement")
    )
    lock_timeout_ms = models.PositiveIntegerField(
        _("Lock Timeout (ms)"), 
        default=1000,  # 1 second
        help_text=_("Maximum time to wait for a lock")
    )
    
    # Audit logging
    audit_connections = models.BooleanField(_("Audit Connections"), default=True)
    audit_statements = models.BooleanField(_("Audit Statements"), default=False)
    audit_statement_level = models.CharField(
        _("Audit Statement Level"), max_length=20,
        choices=[
            ("none", _("None")),
            ("ddl", _("DDL Only")),
            ("dml", _("DML Only")),
            ("all", _("All")),
        ],
        default="none"
    )
    
    # Encryption
    encryption_at_rest = models.BooleanField(_("Encryption at Rest"), default=False)
    encryption_key_identifier = models.CharField(_("Encryption Key Identifier"), max_length=100, blank=True)
    
    # Access control
    allow_public_access = models.BooleanField(_("Allow Public Access"), default=False)
    allowed_networks = models.JSONField(_("Allowed Networks"), default=list, blank=True)
    
    # Status
    is_active = models.BooleanField(_("Is Active"), default=True)
    last_validated_at = models.DateTimeField(_("Last Validated At"), null=True, blank=True)
    validation_status = models.CharField(
        _("Validation Status"), max_length=20,
        choices=[
            ("unknown", _("Unknown")),
            ("valid", _("Valid")),
            ("warning", _("Warning")),
            ("error", _("Error")),
        ],
        default="unknown"
    )
    
    # Metadata
    tags = models.JSONField(_("Tags"), default=list, blank=True)
    attributes = models.JSONField(_("Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Database Security Policy")
        verbose_name_plural = _("Database Security Policies")
        ordering = ("name",)
        indexes = [
            models.Index(fields=["database_identifier", "is_active"]),
            models.Index(fields=["database_type", "is_active"]),
            models.Index(fields=["is_active"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.database_type})"
    
    def clean(self):
        if self.statement_timeout_ms < 100:  # Minimum 100ms
            raise ValidationError(_("Statement timeout must be at least 100ms."))
        if self.lock_timeout_ms < 50:  # Minimum 50ms
            raise ValidationError(_("Lock timeout must be at least 50ms."))
        if self.lock_timeout_ms >= self.statement_timeout_ms:
            raise ValidationError(_("Lock timeout must be less than statement timeout."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if database security policy is valid."""
        return (
            self.is_active
            and self.validation_status == "valid"
        )


class DatabaseAccessLog(UUIDModel, TimeStampedModel):
    """Database access auditing."""
    
    database_policy = models.ForeignKey(
        DatabaseSecurityPolicy,
        on_delete=models.CASCADE,
        related_name="access_logs",
        verbose_name=_("Database Security Policy"),
    )
    
    # Connection details
    session_id = models.CharField(_("Session ID"), max_length=100, blank=True)
    username = models.CharField(_("Username"), max_length=100)
    client_ip = models.GenericIPAddressField(_("Client IP Address"))
    client_hostname = models.CharField(_("Client Hostname"), max_length=255, blank=True)
    
    # Timestamps
    connection_started = models.DateTimeField(_("Connection Started"))
    connection_ended = models.DateTimeField(_("Connection Ended"), null=True, blank=True)
    statement_timestamp = models.DateTimeField(_("Statement Timestamp"), null=True, blank=True)
    
    # Connection status
    CONNECTION_STATUS_CHOICES = [
        ("started", _("Started")),
        ("terminated", _("Terminated")),
        ("idle", _("Idle")),
        ("error", _("Error")),
    ]
    connection_status = models.CharField(
        _("Connection Status"), max_length=20,
        choices=CONNECTION_STATUS_CHOICES,
        default="started"
    )
    
    # Statement details (if applicable)
    statement_type = models.CharField(_("Statement Type"), max_length=20, blank=True)
    statement = models.TextField(_("Statement"), blank=True)
    statement_duration_ms = models.PositiveIntegerField(
        _("Statement Duration (ms)"), null=True, blank=True
    )
    rows_affected = models.PositiveBigIntegerField(
        _("Rows Affected"), null=True, blank=True
    )
    
    # Result
    success = models.BooleanField(_("Success"), default=True)
    error_message = models.TextField(_("Error Message"), blank=True)
    error_code = models.CharField(_("Error Code"), max_length=50, blank=True)
    
    # Metadata
    attributes = models.JSONField(_("Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Database Access Log")
        verbose_name_plural = _("Database Access Logs")
        ordering = ("-connection_started",)
        indexes = [
            models.Index(fields=["database_policy", "-connection_started"]),
            models.Index(fields=["username", "-connection_started"]),
            models.Index(fields=["client_ip", "-connection_started"]),
            models.Index(fields=["connection_status"]),
            models.Index(fields=["statement_timestamp"]),
        ]
    
    def __str__(self):
        return f"DB Access: {self.username} from {self.client_ip} ({self.connection_status})"
    
    def clean(self):
        if self.connection_ended and self.connection_ended < self.connection_started:
            raise ValidationError(_("Connection end time must be after start time."))
        if self.statement_timestamp and self.statement_timestamp < self.connection_started:
            raise ValidationError(_("Statement timestamp must be after connection start."))
        if self.connection_ended and self.statement_timestamp and self.statement_timestamp > self.connection_ended:
            raise ValidationError(_("Statement timestamp cannot be after connection end."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration(self):
        """Get connection duration."""
        if self.connection_ended:
            return self.connection_ended - self.connection_started
        return timezone.now() - self.connection_started


class SecureFile(UUIDModel, TimeStampedModel):
    """Secure file storage with security controls."""
    
    # File identification
    filename = models.CharField(_("Filename"), max_length=255)
    original_filename = models.CharField(_("Original Filename"), max_length=255)
    file_size = models.PositiveBigIntegerField(_("File Size (bytes)"))
    content_type = models.CharField(_("Content Type"), max_length=100)
    
    # Storage location
    storage_path = models.CharField(_("Storage Path"), max_length=500)
    storage_bucket = models.CharField(_("Storage Bucket"), max_length=100, blank=True)
    storage_region = models.CharField(_("Storage Region"), max_length=50, blank=True)
    
    # Ownership and access
    owner = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="owned_files",
        verbose_name=_("Owner")
    )
    uploaded_by = models.ForeignKey(
        Identity,
        on_delete=models.CASCADE,
        related_name="uploaded_files",
        verbose_name=_("Uploaded By")
    )
    
    # Access control
    is_public = models.BooleanField(_("Is Public"), default=False)
    allowed_identities = models.ManyToManyField(
        Identity,
        blank=True,
        related_name="accessible_files",
        verbose_name=_("Allowed Identities")
    )
    allowed_roles = models.ManyToManyField(
        "rbac.Role",
        blank=True,
        related_name="accessible_files",
        verbose_name=_("Allowed Roles")
    )
    
    # Security classifications
    confidentiality = models.CharField(
        _("Confidentiality Level"),
        max_length=30,
        choices=SecurityConfidentialityLevel.CHOICES,
        default=SecurityConfidentialityLevel.INTERNAL
    )
    
    # File integrity
    checksum_algorithm = models.CharField(_("Checksum Algorithm"), max_length=20, default="sha256")
    checksum_value = models.CharField(_("Checksum Value"), max_length=64)
    previous_checksum = models.CharField(_("Previous Checksum"), max_length=64, blank=True)
    
    # Virus/malware scanning
    virus_scan_status = models.CharField(
        _("Virus Scan Status"), max_length=20,
        choices=[
            ("unknown", _("Unknown")),
            ("clean", _("Clean")),
            ("infected", _("Infected")),
            ("quarantined", _("Quarantined")),
            ("scan_failed", _("Scan Failed")),
        ],
        default="unknown"
    )
    virus_scan_at = models.DateTimeField(_("Virus Scan At"), null=True, blank=True)
    virus_scan_details = models.TextField(_("Virus Scan Details"), blank=True)
    
    # Encryption
    is_encrypted = models.BooleanField(_("Is Encrypted"), default=False)
    encryption_algorithm = models.CharField(_("Encryption Algorithm"), max_length=50, blank=True)
    encryption_key_identifier = models.CharField(_("Encryption Key Identifier"), max_length=100, blank=True)
    
    # Versioning
    version = models.PositiveIntegerField(_("Version"), default=1)
    is_latest_version = models.BooleanField(_("Is Latest Version"), default=True)
    replaced_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="replaced_files",
        verbose_name=_("Replaced By")
    )
    
    # Retention and lifecycle
    retention_date = models.DateTimeField(_("Retention Date"), null=True, blank=True)
    retention_policy = models.CharField(_("Retention Policy"), max_length=100, blank=True)
    legal_hold = models.BooleanField(_("Legal Hold"), default=False)
    
    # Status
    is_active = models.BooleanField(_("Is Active"), default=True)
    is_deleted = models.BooleanField(_("Is Deleted"), default=False)
    deleted_at = models.DateTimeField(_("Deleted At"), null=True, blank=True)
    
    # Metadata
    upload_metadata = models.JSONField(_("Upload Metadata"), default=dict, blank=True)
    attributes = models.JSONField(_("Attributes"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _("Secure File")
        verbose_name_plural = _("Secure Files")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["owner", "is_active"]),
            models.Index(fields=["uploaded_by", "is_active"]),
            models.Index(fields=["confidentiality", "is_active"]),
            models.Index(fields=["is_encrypted"]),
            models.Index(fields=["virus_scan_status"]),
            models.Index(fields=["is_latest_version"]),
            models.Index(fields=["filename"]),
        ]
    
    def __str__(self):
        return f"{self.filename} (v{self.version})"
    
    def clean(self):
        if self.file_size < 0:
            raise ValidationError(_("File size cannot be negative."))
        if self.version < 1:
            raise ValidationError(_("File version must be at least 1."))
        if self.retention_date and self.retention_date <= timezone.now():
            raise ValidationError(_("Retention date must be in the future."))
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if file has expired based on retention date."""
        return self.retention_date and self.retention_date <= timezone.now()
    
    @property
    def is_accessible_by(self, identity):
        """Check if file is accessible by given identity."""
        if self.is_public:
            return True
        if self.owner == identity:
            return True
        if self.uploaded_by == identity:
            return True
        if self.allowed_identities.filter(id=identity.id).exists():
            return True
        if self.allowed_roles.filter(identities=identity).exists():
            return True
        return False
    
    def mark_for_deletion(self):
        """Mark file for deletion."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    
    def restore(self):
        """Restore deleted file."""
        self.is_deleted = False
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["is_deleted", "deleted_at", "is_active", "updated_at"])
    
    def new_version(self):
        """Create a new version of this file."""
        self.is_latest_version = False
        self.version += 1
        self.save(update_fields=["is_latest_version", "version", "updated_at"])