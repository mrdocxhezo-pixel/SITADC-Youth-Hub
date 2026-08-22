from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CreatedByModel, TimeStampedModel, UpdatedByModel, UUIDModel
from apps.organizations.models import OrganizationUnit


class ConfigurationCategory(models.TextChoices):
    ORGANIZATION = "organization", _("Organization Settings")
    APPLICATION = "application", _("Application Settings")
    AUTHENTICATION = "authentication", _("Authentication Configuration")
    ROLES_PERMISSIONS = "roles_permissions", _("Roles & Permissions")
    WORKFLOWS = "workflows", _("Workflow Configuration")
    REPORTS = "reports", _("Report Configuration")
    NOTIFICATIONS = "notifications", _("Notification Configuration")
    BRANDING = "branding", _("Branding Configuration")
    NUMBERING = "numbering", _("Reference Numbering Configuration")
    DOCUMENTS = "documents", _("Document Configuration")
    EXPORTS = "exports", _("Export Configuration")
    SECURITY = "security", _("Security Configuration")
    BACKUP = "backup", _("Backup & Restore Configuration")
    INTEGRATIONS = "integrations", _("Integration Configuration")
    MAINTENANCE = "maintenance", _("Maintenance Configuration")
    HEALTH = "health", _("System Health Monitoring")


class ConfigurationStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    VALIDATION = "validation", _("Validation")
    REVIEW = "review", _("Review")
    APPROVAL = "approval", _("Approval")
    ACTIVE = "active", _("Active")
    MONITORING = "monitoring", _("Monitoring")
    ARCHIVED = "archived", _("Archived")
    SUPERSEDED = "superseded", _("Superseded")


class ConfidentialityLevel(models.TextChoices):
    PUBLIC = "public", _("Public")
    INTERNAL = "internal", _("Internal")
    RESTRICTED = "restricted", _("Restricted")
    CONFIDENTIAL = "confidential", _("Confidential")
    HIGHLY_CONFIDENTIAL = "highly_confidential", _("Highly Confidential")


class Configuration(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Base configuration record with lifecycle management."""

    category = models.CharField(
        _("Category"),
        max_length=30,
        choices=ConfigurationCategory.choices,
        db_index=True,
    )
    key = models.SlugField(
        _("Configuration Key"),
        max_length=100,
        unique=True,
        help_text=_("Unique identifier for this configuration record."),
    )
    name = models.CharField(_("Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)

    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ConfigurationStatus.choices,
        default=ConfigurationStatus.DRAFT,
        db_index=True,
    )
    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
    )

    version = models.PositiveIntegerField(_("Version"), default=1)
    effective_date = models.DateTimeField(_("Effective Date"), null=True, blank=True)
    expiry_date = models.DateTimeField(_("Expiry Date"), null=True, blank=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="configurations_reviewed",
        verbose_name=_("Reviewed By"),
    )
    reviewed_at = models.DateTimeField(_("Reviewed At"), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="configurations_approved",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)
    activated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="configurations_activated",
        verbose_name=_("Activated By"),
    )
    activated_at = models.DateTimeField(_("Activated At"), null=True, blank=True)

    organization = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Organization"),
        help_text=_("Organization this configuration applies to (null = global)."),
    )

    class Meta:
        verbose_name = _("Configuration")
        verbose_name_plural = _("Configurations")
        ordering = ("category", "key")
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["status", "effective_date"]),
            models.Index(fields=["organization", "category"]),
        ]

    def __str__(self):
        return f"{self.get_category_display()}: {self.name} (v{self.version})"

    def clean(self):
        if (
            self.expiry_date
            and self.effective_date
            and self.expiry_date <= self.effective_date
        ):
            raise ValidationError(_("Expiry date must be after effective date."))

    def can_transition_to(self, new_status):
        """Validate status transitions according to lifecycle."""
        valid_transitions = {
            ConfigurationStatus.DRAFT: [ConfigurationStatus.VALIDATION],
            ConfigurationStatus.VALIDATION: [
                ConfigurationStatus.REVIEW,
                ConfigurationStatus.DRAFT,
            ],
            ConfigurationStatus.REVIEW: [
                ConfigurationStatus.APPROVAL,
                ConfigurationStatus.DRAFT,
            ],
            ConfigurationStatus.APPROVAL: [
                ConfigurationStatus.ACTIVE,
                ConfigurationStatus.REVIEW,
                ConfigurationStatus.DRAFT,
            ],
            ConfigurationStatus.ACTIVE: [
                ConfigurationStatus.MONITORING,
                ConfigurationStatus.ARCHIVED,
                ConfigurationStatus.SUPERSEDED,
            ],
            ConfigurationStatus.MONITORING: [
                ConfigurationStatus.ARCHIVED,
                ConfigurationStatus.SUPERSEDED,
            ],
            ConfigurationStatus.ARCHIVED: [],
            ConfigurationStatus.SUPERSEDED: [],
        }
        return new_status in valid_transitions.get(self.status, [])

    def transition_to(self, new_status, user, remarks=""):
        """Transition to a new status with audit trail."""
        if not self.can_transition_to(new_status):
            raise ValidationError(
                _("Invalid transition from %(from_status)s to %(to_status)s.")
                % {
                    "from_status": self.get_status_display(),
                    "to_status": dict(ConfigurationStatus.choices)[new_status],
                }
            )
        self.status = new_status
        if new_status == ConfigurationStatus.REVIEW:
            self.reviewed_by = user
            self.reviewed_at = models.functions.Now()
        elif new_status == ConfigurationStatus.APPROVAL:
            self.approved_by = user
            self.approved_at = models.functions.Now()
        elif new_status == ConfigurationStatus.ACTIVE:
            self.activated_by = user
            self.activated_at = models.functions.Now()
            self.effective_date = models.functions.Now()
        self.save()
        ConfigurationTimeline.objects.create(
            configuration=self,
            event_type=f"status_changed_to_{new_status}",
            user=user,
            previous_value=self.status,
            new_value=new_status,
            remarks=remarks,
        )

    @classmethod
    def get_active(cls, category, key=None, organization=None):
        """Get the active configuration for a category/key."""
        qs = cls.objects.filter(category=category, status=ConfigurationStatus.ACTIVE)
        if key:
            qs = qs.filter(key=key)
        if organization:
            qs = qs.filter(
                models.Q(organization=organization)
                | models.Q(organization__isnull=True)
            )
        return qs.order_by("-organization__id", "-version").first()


class ConfigurationValue(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Key-value storage for configuration settings."""

    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name=_("Configuration"),
    )
    key = models.SlugField(_("Key"), max_length=100, db_index=True)
    value = models.JSONField(_("Value"))
    description = models.TextField(_("Description"), blank=True)
    is_sensitive = models.BooleanField(_("Is Sensitive"), default=False)
    encryption_version = models.PositiveIntegerField(_("Encryption Version"), default=0)

    class Meta:
        verbose_name = _("Configuration Value")
        verbose_name_plural = _("Configuration Values")
        unique_together = [["configuration", "key"]]
        ordering = ("configuration", "key")

    def __str__(self):
        return f"{self.configuration.key}.{self.key}"


class ConfigurationVersion(UUIDModel, TimeStampedModel, CreatedByModel):
    """Version history for configuration records."""

    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name=_("Configuration"),
    )
    version = models.PositiveIntegerField(_("Version"))
    snapshot = models.JSONField(_("Snapshot"))
    change_summary = models.TextField(_("Change Summary"))
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="configuration_versions_created",
        verbose_name=_("Changed By"),
    )
    is_active_version = models.BooleanField(_("Is Active Version"), default=False)

    class Meta:
        verbose_name = _("Configuration Version")
        verbose_name_plural = _("Configuration Versions")
        unique_together = [["configuration", "version"]]
        ordering = ("-version",)

    def __str__(self):
        return f"{self.configuration.key} v{self.version}"


class ConfigurationTimeline(UUIDModel, TimeStampedModel):
    """Chronological timeline of configuration activities."""

    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="timeline",
        verbose_name=_("Configuration"),
    )
    event_type = models.CharField(_("Event Type"), max_length=50, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("User"),
    )
    previous_value = models.JSONField(_("Previous Value"), null=True, blank=True)
    new_value = models.JSONField(_("New Value"), null=True, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    user_agent = models.TextField(_("User Agent"), blank=True)

    class Meta:
        verbose_name = _("Configuration Timeline Event")
        verbose_name_plural = _("Configuration Timeline Events")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["configuration", "-created_at"]),
            models.Index(fields=["event_type", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.configuration.key} - {self.event_type} by {self.user}"


class OrganizationSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Organization-level settings."""

    organization = models.OneToOneField(
        OrganizationUnit,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name=_("Organization"),
    )
    name = models.CharField(_("Organization Name"), max_length=200)
    short_name = models.CharField(_("Short Name"), max_length=50, blank=True)
    acronym = models.CharField(_("Acronym"), max_length=20, blank=True)
    logo = models.ImageField(_("Logo"), upload_to="org_logos/", blank=True)
    mission = models.TextField(_("Mission"), blank=True)
    vision = models.TextField(_("Vision"), blank=True)
    core_values = models.TextField(_("Core Values"), blank=True)

    registration_number = models.CharField(
        _("Registration Number"), max_length=50, blank=True
    )
    registration_date = models.DateField(_("Registration Date"), null=True, blank=True)
    tax_id = models.CharField(_("Tax ID"), max_length=50, blank=True)

    physical_address = models.TextField(_("Physical Address"), blank=True)
    postal_address = models.TextField(_("Postal Address"), blank=True)
    phone = models.CharField(_("Phone"), max_length=30, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    official_email = models.EmailField(_("Official Email"), blank=True)

    social_media = models.JSONField(_("Social Media Links"), default=dict, blank=True)
    fiscal_year_start = models.DateField(_("Fiscal Year Start"), null=True, blank=True)
    default_language = models.CharField(
        _("Default Language"), max_length=10, default="en"
    )
    default_timezone = models.CharField(
        _("Default Timezone"), max_length=50, default="Africa/Lusaka"
    )
    currency = models.CharField(_("Currency"), max_length=3, default="ZMW")

    class Meta:
        verbose_name = _("Organization Settings")
        verbose_name_plural = _("Organization Settings")

    def __str__(self):
        return self.name


class ApplicationSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Application-wide settings."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    application_name = models.CharField(
        _("Application Name"), max_length=150, default="SITADC Youth Hub"
    )
    application_short_name = models.CharField(
        _("Application Short Name"), max_length=50, default="SITADC Hub"
    )
    application_version = models.CharField(
        _("Application Version"), max_length=20, default="1.0.0"
    )

    SYSTEM_STATUS_CHOICES = [
        ("operational", _("Operational")),
        ("maintenance", _("Maintenance")),
        ("disabled", _("Disabled")),
    ]
    system_status = models.CharField(
        _("System Status"),
        max_length=20,
        choices=SYSTEM_STATUS_CHOICES,
        default="operational",
    )

    default_language = models.CharField(
        _("Default Language"), max_length=10, default="en"
    )
    default_timezone = models.CharField(
        _("Default Timezone"), max_length=50, default="Africa/Lusaka"
    )
    date_format = models.CharField(_("Date Format"), max_length=20, default="Y-m-d")
    time_format = models.CharField(_("Time Format"), max_length=20, default="H:i:s")
    default_pagination_size = models.PositiveIntegerField(
        _("Default Pagination Size"), default=25
    )

    theme_config = models.JSONField(_("Theme Configuration"), default=dict, blank=True)
    light_mode_default = models.BooleanField(_("Light Mode Default"), default=True)
    dark_mode_available = models.BooleanField(_("Dark Mode Available"), default=True)

    session_timeout_minutes = models.PositiveIntegerField(
        _("Session Timeout (minutes)"), default=30
    )
    file_upload_max_size_mb = models.PositiveIntegerField(
        _("Max File Upload Size (MB)"), default=10
    )
    default_storage_path = models.CharField(
        _("Default Storage Path"), max_length=255, blank=True
    )
    default_export_formats = models.JSONField(
        _("Default Export Formats"), default=list, blank=True
    )

    feature_toggles = models.JSONField(_("Feature Toggles"), default=dict, blank=True)
    maintenance_banner = models.TextField(_("Maintenance Banner"), blank=True)
    maintenance_banner_enabled = models.BooleanField(
        _("Maintenance Banner Enabled"), default=False
    )

    class Meta:
        verbose_name = _("Application Settings")
        verbose_name_plural = _("Application Settings")

    def __str__(self):
        return self.application_name

    def clean(self):
        if not self.key:
            self.key = "default"
        if (
            ApplicationSettings.objects.exclude(pk=self.pk)
            .filter(key=self.key)
            .exists()
        ):
            raise ValidationError(
                _("Only one ApplicationSettings instance is allowed.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class AuthenticationSettings(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Authentication and security policies."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")

    LOGIN_METHOD_CHOICES = [
        ("email", _("Email")),
        ("username", _("Username")),
        ("both", _("Email or Username")),
    ]
    login_method = models.CharField(
        _("Login Method"),
        max_length=20,
        choices=LOGIN_METHOD_CHOICES,
        default="email",
    )

    password_min_length = models.PositiveIntegerField(
        _("Minimum Password Length"), default=8
    )
    password_require_uppercase = models.BooleanField(
        _("Require Uppercase"), default=True
    )
    password_require_lowercase = models.BooleanField(
        _("Require Lowercase"), default=True
    )
    password_require_digits = models.BooleanField(_("Require Digits"), default=True)
    password_require_special = models.BooleanField(
        _("Require Special Characters"), default=True
    )
    password_expiry_days = models.PositiveIntegerField(
        _("Password Expiry (days)"), null=True, blank=True
    )
    password_history_count = models.PositiveIntegerField(
        _("Password History Count"), default=5
    )
    password_prevent_common = models.BooleanField(
        _("Prevent Common Passwords"), default=True
    )

    max_login_attempts = models.PositiveIntegerField(_("Max Login Attempts"), default=5)
    lockout_duration_minutes = models.PositiveIntegerField(
        _("Lockout Duration (minutes)"), default=30
    )
    login_attempt_window_minutes = models.PositiveIntegerField(
        _("Login Attempt Window (minutes)"), default=15
    )

    mfa_enabled = models.BooleanField(_("MFA Enabled"), default=False)
    mfa_required_for_admin = models.BooleanField(
        _("MFA Required for Admins"), default=False
    )
    mfa_required_for_staff = models.BooleanField(
        _("MFA Required for Staff"), default=False
    )
    mfa_methods = models.JSONField(_("Allowed MFA Methods"), default=list, blank=True)

    otp_enabled = models.BooleanField(_("OTP Enabled"), default=False)
    otp_delivery_methods = models.JSONField(
        _("OTP Delivery Methods"), default=list, blank=True
    )
    otp_length = models.PositiveIntegerField(_("OTP Length"), default=6)
    otp_expiry_minutes = models.PositiveIntegerField(
        _("OTP Expiry (minutes)"), default=5
    )

    session_timeout_minutes = models.PositiveIntegerField(
        _("Session Timeout (minutes)"), default=30
    )
    session_absolute_timeout_hours = models.PositiveIntegerField(
        _("Absolute Session Timeout (hours)"), default=24
    )
    concurrent_sessions_limit = models.PositiveIntegerField(
        _("Concurrent Sessions Limit"), default=5
    )
    device_trust_enabled = models.BooleanField(_("Device Trust Enabled"), default=False)
    device_trust_duration_days = models.PositiveIntegerField(
        _("Device Trust Duration (days)"), default=30
    )

    invitation_expiry_days = models.PositiveIntegerField(
        _("Invitation Expiry (days)"), default=7
    )
    password_reset_token_expiry_hours = models.PositiveIntegerField(
        _("Password Reset Token Expiry (hours)"), default=1
    )
    email_verification_required = models.BooleanField(
        _("Email Verification Required"), default=True
    )
    email_verification_token_expiry_hours = models.PositiveIntegerField(
        _("Email Verification Token Expiry (hours)"), default=24
    )

    ip_allowlist = models.JSONField(_("IP Allowlist"), default=list, blank=True)
    ip_blocklist = models.JSONField(_("IP Blocklist"), default=list, blank=True)
    geo_blocklist = models.JSONField(
        _("Geographic Blocklist"), default=list, blank=True
    )

    class Meta:
        verbose_name = _("Authentication Settings")
        verbose_name_plural = _("Authentication Settings")

    def __str__(self):
        return _("Authentication Settings")

    def clean(self):
        if not self.key:
            self.key = "default"
        if (
            AuthenticationSettings.objects.exclude(pk=self.pk)
            .filter(key=self.key)
            .exists()
        ):
            raise ValidationError(
                _("Only one AuthenticationSettings instance is allowed.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class RolePermissionConfiguration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Role and permission configuration."""

    role = models.ForeignKey(
        "rbac.Role",
        on_delete=models.CASCADE,
        related_name="permission_configurations",
        verbose_name=_("Role"),
    )
    module = models.CharField(_("Module"), max_length=50)
    permissions = models.JSONField(_("Permissions"), default=list)
    scope = models.CharField(
        _("Scope"),
        max_length=20,
        choices=[
            ("global", _("Global")),
            ("organization", _("Organization")),
            ("department", _("Department")),
            ("team", _("Team")),
            ("self", _("Self Only")),
        ],
        default="organization",
    )
    conditions = models.JSONField(_("Conditions"), default=dict, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Role Permission Configuration")
        verbose_name_plural = _("Role Permission Configurations")
        unique_together = [["role", "module", "scope"]]
        ordering = ("role", "module")

    def __str__(self):
        return f"{self.role.name} - {self.module} ({self.scope})"


class WorkflowConfiguration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Business workflow configuration."""

    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    module = models.CharField(_("Module"), max_length=50)
    entity_type = models.CharField(_("Entity Type"), max_length=50)

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("active", _("Active")),
        ("archived", _("Archived")),
    ]
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="draft"
    )

    stages = models.JSONField(_("Stages"), default=list)
    transitions = models.JSONField(_("Transitions"), default=list)
    escalation_rules = models.JSONField(_("Escalation Rules"), default=list)
    reminder_schedules = models.JSONField(_("Reminder Schedules"), default=list)
    due_date_rules = models.JSONField(_("Due Date Rules"), default=dict, blank=True)
    digital_signature_required = models.BooleanField(
        _("Digital Signature Required"), default=False
    )
    multi_level_approval = models.BooleanField(_("Multi-Level Approval"), default=False)
    approval_chain = models.JSONField(_("Approval Chain"), default=list, blank=True)

    class Meta:
        verbose_name = _("Workflow Configuration")
        verbose_name_plural = _("Workflow Configurations")
        ordering = ("module", "name")

    def __str__(self):
        return f"{self.module}: {self.name}"


class NotificationSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Notification configuration."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")

    email_enabled = models.BooleanField(_("Email Enabled"), default=True)
    email_provider = models.CharField(_("Email Provider"), max_length=50, blank=True)
    email_sender_name = models.CharField(
        _("Email Sender Name"), max_length=150, blank=True
    )
    email_sender_address = models.EmailField(_("Email Sender Address"), blank=True)
    email_footer = models.TextField(_("Email Footer"), blank=True)
    email_templates = models.JSONField(_("Email Templates"), default=dict, blank=True)

    in_app_enabled = models.BooleanField(_("In-App Enabled"), default=True)
    in_app_retention_days = models.PositiveIntegerField(
        _("In-App Retention (days)"), default=30
    )

    sms_enabled = models.BooleanField(_("SMS Enabled"), default=False)
    sms_provider = models.CharField(_("SMS Provider"), max_length=50, blank=True)
    sms_sender_id = models.CharField(_("SMS Sender ID"), max_length=20, blank=True)

    push_enabled = models.BooleanField(_("Push Enabled"), default=False)
    push_provider = models.CharField(_("Push Provider"), max_length=50, blank=True)

    default_reminder_schedule = models.JSONField(
        _("Default Reminder Schedule"), default=list, blank=True
    )
    escalation_alerts = models.JSONField(
        _("Escalation Alerts"), default=list, blank=True
    )
    digest_summary_enabled = models.BooleanField(
        _("Digest Summary Enabled"), default=False
    )
    digest_frequency = models.CharField(
        _("Digest Frequency"),
        max_length=20,
        choices=[
            ("daily", _("Daily")),
            ("weekly", _("Weekly")),
            ("monthly", _("Monthly")),
        ],
        blank=True,
    )
    quiet_hours_start = models.TimeField(_("Quiet Hours Start"), null=True, blank=True)
    quiet_hours_end = models.TimeField(_("Quiet Hours End"), null=True, blank=True)

    class Meta:
        verbose_name = _("Notification Settings")
        verbose_name_plural = _("Notification Settings")

    def __str__(self):
        return _("Notification Settings")

    def clean(self):
        if not self.key:
            self.key = "default"
        if (
            NotificationSettings.objects.exclude(pk=self.pk)
            .filter(key=self.key)
            .exists()
        ):
            raise ValidationError(
                _("Only one NotificationSettings instance is allowed.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class BrandingSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Branding configuration."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")
    organization = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Organization"),
    )

    primary_logo = models.ImageField(
        _("Primary Logo"), upload_to="branding/logos/", blank=True
    )
    secondary_logo = models.ImageField(
        _("Secondary Logo"), upload_to="branding/logos/", blank=True
    )
    favicon = models.ImageField(_("Favicon"), upload_to="branding/", blank=True)

    color_palette = models.JSONField(_("Color Palette"), default=dict, blank=True)
    typography = models.JSONField(_("Typography"), default=dict, blank=True)
    icons_set = models.CharField(_("Icons Set"), max_length=50, default="bootstrap")

    email_header = models.TextField(_("Email Header"), blank=True)
    email_footer = models.TextField(_("Email Footer"), blank=True)
    report_header = models.TextField(_("Report Header"), blank=True)
    report_footer = models.TextField(_("Report Footer"), blank=True)
    dashboard_banner = models.TextField(_("Dashboard Banner"), blank=True)

    watermark_text = models.CharField(_("Watermark Text"), max_length=100, blank=True)
    watermark_opacity = models.PositiveIntegerField(
        _("Watermark Opacity (%)"), default=10
    )
    document_header = models.TextField(_("Document Header"), blank=True)
    document_footer = models.TextField(_("Document Footer"), blank=True)

    custom_css = models.TextField(_("Custom CSS"), blank=True)
    custom_js = models.TextField(_("Custom JavaScript"), blank=True)

    class Meta:
        verbose_name = _("Branding Settings")
        verbose_name_plural = _("Branding Settings")

    def __str__(self):
        return _("Branding Settings")

    def clean(self):
        if not self.key:
            self.key = "default"
        if BrandingSettings.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError(_("Only one BrandingSettings instance is allowed."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls, organization=None):
        qs = cls.objects.filter(key="default")
        if organization:
            qs = qs.filter(
                models.Q(organization=organization)
                | models.Q(organization__isnull=True)
            )
        return qs.order_by("-organization__id").first() or cls.objects.create(
            key="default"
        )


class NumberingConfiguration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """Reference numbering configuration."""

    module = models.CharField(_("Module"), max_length=50)
    prefix = models.CharField(_("Prefix"), max_length=20)
    format = models.CharField(
        _("Format"),
        max_length=50,
        help_text=_("Use {year}, {month}, {day}, {sequence:04d} placeholders."),
    )
    sequence = models.PositiveIntegerField(_("Current Sequence"), default=1)
    reset_frequency = models.CharField(
        _("Reset Frequency"),
        max_length=20,
        choices=[
            ("never", _("Never")),
            ("daily", _("Daily")),
            ("monthly", _("Monthly")),
            ("yearly", _("Yearly")),
        ],
        default="yearly",
    )
    last_reset = models.DateField(_("Last Reset"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)

    class Meta:
        verbose_name = _("Numbering Configuration")
        verbose_name_plural = _("Numbering Configurations")
        unique_together = [["module", "prefix"]]
        ordering = ("module", "prefix")

    def __str__(self):
        return f"{self.module}: {self.prefix}"


class DocumentSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Document management configuration."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")

    allowed_file_types = models.JSONField(
        _("Allowed File Types"), default=list, blank=True
    )
    max_file_size_mb = models.PositiveIntegerField(_("Max File Size (MB)"), default=10)
    version_control_enabled = models.BooleanField(
        _("Version Control Enabled"), default=True
    )
    max_versions = models.PositiveIntegerField(_("Max Versions"), default=10)

    categories = models.JSONField(_("Document Categories"), default=list, blank=True)
    default_retention_days = models.PositiveIntegerField(
        _("Default Retention (days)"), default=2555
    )

    confidentiality_levels = models.JSONField(
        _("Confidentiality Levels"),
        default=list,
        blank=True,
    )
    watermark_enabled = models.BooleanField(_("Watermark Enabled"), default=False)
    watermark_text = models.CharField(_("Watermark Text"), max_length=100, blank=True)
    preview_enabled = models.BooleanField(_("Preview Enabled"), default=True)
    download_permissions = models.JSONField(
        _("Download Permissions"), default=dict, blank=True
    )
    expiry_notification_days = models.PositiveIntegerField(
        _("Expiry Notification (days)"), default=30
    )

    class Meta:
        verbose_name = _("Document Settings")
        verbose_name_plural = _("Document Settings")

    def __str__(self):
        return _("Document Settings")

    def clean(self):
        if not self.key:
            self.key = "default"
        if DocumentSettings.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError(_("Only one DocumentSettings instance is allowed."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class ExportSettings(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Export configuration."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="default")

    supported_formats = models.JSONField(
        _("Supported Formats"),
        default=list,
        blank=True,
    )
    default_format = models.CharField(_("Default Format"), max_length=10, default="pdf")

    templates = models.JSONField(_("Export Templates"), default=dict, blank=True)
    branding_enabled = models.BooleanField(_("Branding Enabled"), default=True)
    headers_enabled = models.BooleanField(_("Headers Enabled"), default=True)
    footers_enabled = models.BooleanField(_("Footers Enabled"), default=True)
    pagination_enabled = models.BooleanField(_("Pagination Enabled"), default=True)
    watermark_enabled = models.BooleanField(_("Watermark Enabled"), default=False)
    security_enabled = models.BooleanField(_("Security Enabled"), default=False)
    password_protection = models.BooleanField(_("Password Protection"), default=False)
    digital_signature = models.BooleanField(_("Digital Signature"), default=False)

    max_rows_csv = models.PositiveIntegerField(_("Max Rows (CSV)"), default=100000)
    max_rows_xlsx = models.PositiveIntegerField(_("Max Rows (XLSX)"), default=50000)
    max_pages_pdf = models.PositiveIntegerField(_("Max Pages (PDF)"), default=500)

    class Meta:
        verbose_name = _("Export Settings")
        verbose_name_plural = _("Export Settings")

    def __str__(self):
        return _("Export Settings")

    def clean(self):
        if not self.key:
            self.key = "default"
        if ExportSettings.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError(_("Only one ExportSettings instance is allowed."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class SecurityPolicy(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Security policies configuration."""

    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
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
    ]
    policy_type = models.CharField(
        _("Policy Type"), max_length=20, choices=POLICY_TYPE_CHOICES
    )

    rules = models.JSONField(_("Rules"), default=dict)
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
    scope = models.JSONField(_("Scope"), default=dict, blank=True)
    exceptions = models.JSONField(_("Exceptions"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True)
    effective_date = models.DateTimeField(_("Effective Date"), null=True, blank=True)
    review_date = models.DateTimeField(_("Review Date"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_policies_reviewed",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="security_policies_approved",
    )

    class Meta:
        verbose_name = _("Security Policy")
        verbose_name_plural = _("Security Policies")
        ordering = ("policy_type", "name")

    def __str__(self):
        return f"{self.get_policy_type_display()}: {self.name}"


class BackupSchedule(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Backup scheduling configuration."""

    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)

    BACKUP_TYPE_CHOICES = [
        ("database", _("Database")),
        ("files", _("File Storage")),
        ("media", _("Media Files")),
        ("configuration", _("Configuration")),
        ("full", _("Full System")),
    ]
    backup_type = models.CharField(
        _("Backup Type"), max_length=20, choices=BACKUP_TYPE_CHOICES
    )

    FREQUENCY_CHOICES = [
        ("hourly", _("Hourly")),
        ("daily", _("Daily")),
        ("weekly", _("Weekly")),
        ("monthly", _("Monthly")),
        ("manual", _("Manual Only")),
    ]
    frequency = models.CharField(
        _("Frequency"), max_length=20, choices=FREQUENCY_CHOICES, default="daily"
    )
    schedule_time = models.TimeField(_("Schedule Time"), default="02:00")
    schedule_days = models.JSONField(_("Schedule Days"), default=list, blank=True)

    retention_days = models.PositiveIntegerField(_("Retention (days)"), default=30)
    max_backups = models.PositiveIntegerField(_("Max Backups"), default=10)
    compression_enabled = models.BooleanField(_("Compression Enabled"), default=True)
    encryption_enabled = models.BooleanField(_("Encryption Enabled"), default=True)
    storage_location = models.CharField(
        _("Storage Location"), max_length=255, blank=True
    )
    notification_on_success = models.BooleanField(_("Notify on Success"), default=False)
    notification_on_failure = models.BooleanField(_("Notify on Failure"), default=True)
    is_active = models.BooleanField(_("Active"), default=True)
    last_run = models.DateTimeField(_("Last Run"), null=True, blank=True)
    last_status = models.CharField(
        _("Last Status"),
        max_length=20,
        choices=[
            ("success", _("Success")),
            ("warning", _("Warning")),
            ("error", _("Error")),
            ("never", _("Never Run")),
        ],
        default="never",
    )
    last_error = models.TextField(_("Last Error"), blank=True)

    class Meta:
        verbose_name = _("Backup Schedule")
        verbose_name_plural = _("Backup Schedules")
        ordering = ("backup_type", "name")

    def __str__(self):
        return f"{self.get_backup_type_display()}: {self.name}"


class BackupHistory(UUIDModel, TimeStampedModel):
    """Backup execution history."""

    schedule = models.ForeignKey(
        BackupSchedule,
        on_delete=models.SET_NULL,
        null=True,
        related_name="history",
        verbose_name=_("Schedule"),
    )
    backup_type = models.CharField(_("Backup Type"), max_length=20)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("running", _("Running")),
            ("success", _("Success")),
            ("warning", _("Warning")),
            ("error", _("Error")),
        ],
        default="pending",
    )
    started_at = models.DateTimeField(_("Started At"))
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    file_path = models.CharField(_("File Path"), max_length=500, blank=True)
    file_size = models.PositiveBigIntegerField(
        _("File Size (bytes)"), null=True, blank=True
    )
    error_message = models.TextField(_("Error Message"), blank=True)
    checksum = models.CharField(_("Checksum"), max_length=128, blank=True)
    verification_status = models.CharField(
        _("Verification Status"),
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("verified", _("Verified")),
            ("failed", _("Failed")),
        ],
        default="pending",
    )
    verified_at = models.DateTimeField(_("Verified At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Backup History")
        verbose_name_plural = _("Backup Histories")
        ordering = ("-started_at",)

    def __str__(self):
        return f"{self.backup_type} - {self.status} - {self.started_at}"


class IntegrationConfiguration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """External integration configuration."""

    name = models.CharField(_("Name"), max_length=150)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)

    INTEGRATION_TYPE_CHOICES = [
        ("email", _("Email Service")),
        ("auth", _("Authentication Provider")),
        ("storage", _("Storage Service")),
        ("notification", _("Notification Service")),
        ("calendar", _("Calendar Service")),
        ("api", _("External API")),
        ("analytics", _("Analytics Service")),
        ("monitoring", _("Monitoring Service")),
        ("other", _("Other")),
    ]
    integration_type = models.CharField(
        _("Integration Type"), max_length=20, choices=INTEGRATION_TYPE_CHOICES
    )

    provider = models.CharField(_("Provider"), max_length=100, blank=True)
    base_url = models.URLField(_("Base URL"), blank=True)
    configuration = models.JSONField(_("Configuration"), default=dict, blank=True)
    credentials_encrypted = models.JSONField(
        _("Credentials (Encrypted)"), default=dict, blank=True
    )

    is_active = models.BooleanField(_("Active"), default=False)
    health_check_enabled = models.BooleanField(_("Health Check Enabled"), default=True)
    health_check_url = models.URLField(_("Health Check URL"), blank=True)
    health_check_interval_minutes = models.PositiveIntegerField(
        _("Health Check Interval (minutes)"), default=60
    )
    last_sync = models.DateTimeField(_("Last Sync"), null=True, blank=True)
    last_status = models.CharField(
        _("Last Status"),
        max_length=20,
        choices=[
            ("success", _("Success")),
            ("warning", _("Warning")),
            ("error", _("Error")),
            ("never", _("Never Synced")),
        ],
        default="never",
    )
    last_error = models.TextField(_("Last Error"), blank=True)
    rate_limit = models.PositiveIntegerField(
        _("Rate Limit (req/min)"), null=True, blank=True
    )
    timeout_seconds = models.PositiveIntegerField(_("Timeout (seconds)"), default=30)
    retry_attempts = models.PositiveIntegerField(_("Retry Attempts"), default=3)

    class Meta:
        verbose_name = _("Integration Configuration")
        verbose_name_plural = _("Integration Configurations")
        ordering = ("integration_type", "name")

    def __str__(self):
        return f"{self.get_integration_type_display()}: {self.name}"


class MaintenanceWindow(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Maintenance window configuration."""

    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)

    MAINTENANCE_TYPE_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("emergency", _("Emergency")),
    ]
    maintenance_type = models.CharField(
        _("Type"), max_length=20, choices=MAINTENANCE_TYPE_CHOICES, default="scheduled"
    )

    start_time = models.DateTimeField(_("Start Time"))
    end_time = models.DateTimeField(_("End Time"))
    timezone = models.CharField(_("Timezone"), max_length=50, default="Africa/Lusaka")

    read_only_mode = models.BooleanField(_("Read-Only Mode"), default=False)
    affected_modules = models.JSONField(_("Affected Modules"), default=list, blank=True)
    allowed_roles = models.JSONField(_("Allowed Roles"), default=list, blank=True)
    notification_banner = models.TextField(_("Notification Banner"), blank=True)
    estimated_restoration = models.DateTimeField(
        _("Estimated Restoration"), null=True, blank=True
    )

    STATUS_CHOICES = [
        ("planned", _("Planned")),
        ("announced", _("Announced")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]
    status = models.CharField(
        _("Status"), max_length=20, choices=STATUS_CHOICES, default="planned"
    )

    notified_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="maintenance_notifications",
        verbose_name=_("Notified Users"),
    )

    class Meta:
        verbose_name = _("Maintenance Window")
        verbose_name_plural = _("Maintenance Windows")
        ordering = ("-start_time",)

    def __str__(self):
        return f"{self.name} ({self.get_maintenance_type_display()})"


class SystemHealthRecord(UUIDModel, TimeStampedModel):
    """System health monitoring records."""

    COMPONENT_CHOICES = [
        ("database", _("Database")),
        ("storage", _("Storage")),
        ("api", _("API")),
        ("auth", _("Authentication")),
        ("queue", _("Queue")),
        ("jobs", _("Scheduled Jobs")),
        ("services", _("Background Services")),
        ("network", _("Network")),
        ("performance", _("Performance")),
    ]
    component = models.CharField(
        _("Component"), max_length=20, choices=COMPONENT_CHOICES, db_index=True
    )
    metric_name = models.CharField(_("Metric Name"), max_length=100)
    value = models.FloatField(_("Value"))
    unit = models.CharField(_("Unit"), max_length=20, blank=True)

    STATUS_CHOICES = [
        ("healthy", _("Healthy")),
        ("warning", _("Warning")),
        ("critical", _("Critical")),
        ("unknown", _("Unknown")),
    ]
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default="healthy",
        db_index=True,
    )
    threshold_warning = models.FloatField(_("Warning Threshold"), null=True, blank=True)
    threshold_critical = models.FloatField(
        _("Critical Threshold"), null=True, blank=True
    )
    details = models.JSONField(_("Details"), default=dict, blank=True)

    class Meta:
        verbose_name = _("System Health Record")
        verbose_name_plural = _("System Health Records")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["component", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.get_component_display()} - {self.metric_name}: {self.value} {self.unit}"


class ConfigurationNotification(UUIDModel, TimeStampedModel):
    """Configuration-related notifications."""

    EVENT_CHOICES = [
        ("created", _("Configuration Created")),
        ("updated", _("Configuration Updated")),
        ("approved", _("Configuration Approved")),
        ("activated", _("Configuration Activated")),
        ("security_changed", _("Security Policy Changed")),
        ("backup_completed", _("Backup Completed")),
        ("backup_failed", _("Backup Failed")),
        ("integration_error", _("Integration Error")),
        ("maintenance_scheduled", _("Maintenance Scheduled")),
        ("maintenance_completed", _("Maintenance Completed")),
        ("health_alert", _("Health Alert")),
        ("rolled_back", _("Configuration Rolled Back")),
    ]
    event_type = models.CharField(
        _("Event Type"), max_length=30, choices=EVENT_CHOICES, db_index=True
    )
    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Configuration"),
    )
    title = models.CharField(_("Title"), max_length=200)
    message = models.TextField(_("Message"))
    recipients = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="configuration_notifications",
        verbose_name=_("Recipients"),
    )
    roles_notified = models.JSONField(_("Roles Notified"), default=list, blank=True)
    is_read = models.BooleanField(_("Read"), default=False)
    read_at = models.DateTimeField(_("Read At"), null=True, blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=[
            ("low", _("Low")),
            ("normal", _("Normal")),
            ("high", _("High")),
            ("critical", _("Critical")),
        ],
        default="normal",
    )

    class Meta:
        verbose_name = _("Configuration Notification")
        verbose_name_plural = _("Configuration Notifications")
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_event_type_display()}: {self.title}"


class SystemConfigurationDashboard(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel
):
    """System configuration dashboard configuration."""

    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    is_default = models.BooleanField(_("Default Dashboard"), default=False)
    layout = models.JSONField(_("Layout"), default=dict, blank=True)
    widgets = models.JSONField(_("Widgets"), default=list, blank=True)
    refresh_interval_seconds = models.PositiveIntegerField(
        _("Refresh Interval (seconds)"), default=300
    )
    roles = models.ManyToManyField(
        "rbac.Role",
        blank=True,
        related_name="dashboards",
        verbose_name=_("Roles"),
    )

    class Meta:
        verbose_name = _("System Configuration Dashboard")
        verbose_name_plural = _("System Configuration Dashboards")
        ordering = ("-is_default", "name")

    def __str__(self):
        return self.name


class ConfigurationAuditReference(UUIDModel, TimeStampedModel):
    """Cross-reference to audit log entries."""

    configuration = models.ForeignKey(
        Configuration,
        on_delete=models.CASCADE,
        related_name="audit_references",
        verbose_name=_("Configuration"),
    )
    audit_log_id = models.UUIDField(_("Audit Log ID"))
    event_type = models.CharField(_("Event Type"), max_length=50)
    event_timestamp = models.DateTimeField(_("Event Timestamp"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("User"),
    )
    details = models.JSONField(_("Details"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Configuration Audit Reference")
        verbose_name_plural = _("Configuration Audit References")
        ordering = ("-event_timestamp",)
        indexes = [
            models.Index(fields=["configuration", "-event_timestamp"]),
            models.Index(fields=["audit_log_id"]),
        ]

    def __str__(self):
        return f"Audit ref for {self.configuration.key} - {self.event_type}"
