from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    UUIDModel,
    TimeStampedModel,
    CreatedByModel,
    UpdatedByModel,
)
from apps.organizations.models import OrganizationUnit


class SystemConfiguration(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Global system configuration (singleton)."""

    key = models.SlugField(
        _("Key"),
        max_length=40,
        unique=True,
        default="default",
        help_text=_("Unique key to enforce singleton pattern."),
    )

    # General System Configuration
    application_name = models.CharField(
        _("Application Name"),
        max_length=150,
        default="SITADC Youth Hub",
    )
    application_short_name = models.CharField(
        _("Application Short Name"),
        max_length=50,
        default="SITADC Hub",
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
        _("Default Language"),
        max_length=10,
        default="en",
    )
    default_timezone = models.CharField(
        _("Default Timezone"),
        max_length=50,
        default="UTC",
    )
    date_format = models.CharField(
        _("Date Format"),
        max_length=20,
        default="Y-m-d",
    )
    time_format = models.CharField(
        _("Time Format"),
        max_length=20,
        default="H:i:s",
    )
    default_pagination_size = models.PositiveIntegerField(
        _("Default Pagination Size"),
        default=25,
        help_text=_("Number of items per page in lists."),
    )

    # Organizational Configuration (reference to OrganizationUnit)
    organization = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Organization"),
        help_text=_("The organization unit that represents the organization."),
    )

    # Branding Configuration
    branding = models.JSONField(
        _("Branding"),
        default=dict,
        blank=True,
        help_text=_("Branding overrides (logo, favicon, colors, etc.)."),
    )

    # Email Configuration (non-secret)
    email_sender_name = models.CharField(
        _("Email Sender Name"),
        max_length=150,
        blank=True,
    )
    email_sender_address = models.EmailField(
        _("Email Sender Address"),
        blank=True,
    )
    email_footer = models.TextField(
        _("Email Footer"),
        blank=True,
    )

    # Notification Configuration
    notification_retention_days = models.PositiveIntegerField(
        _("Notification Retention (days)"),
        default=30,
        help_text=_("How long to retain notifications before deletion."),
    )
    enable_email_notifications = models.BooleanField(
        _("Enable Email Notifications"),
        default=True,
    )
    enable_sms_notifications = models.BooleanField(
        _("Enable SMS Notifications"),
        default=False,
    )
    enable_push_notifications = models.BooleanField(
        _("Enable Push Notifications"),
        default=False,
    )

    # Security Configuration
    session_timeout_minutes = models.PositiveIntegerField(
        _("Session Timeout (minutes)"),
        default=30,
        help_text=_("Minutes of inactivity before session expires."),
    )
    password_min_length = models.PositiveIntegerField(
        _("Minimum Password Length"),
        default=8,
    )
    password_require_uppercase = models.BooleanField(
        _("Require Uppercase Letter"),
        default=True,
    )
    password_require_lowercase = models.BooleanField(
        _("Require Lowercase Letter"),
        default=True,
    )
    password_require_digits = models.BooleanField(
        _("Require Digit"),
        default=True,
    )
    password_require_special_chars = models.BooleanField(
        _("Require Special Character"),
        default=True,
    )
    max_login_attempts = models.PositiveIntegerField(
        _("Maximum Login Attempts"),
        default=5,
        help_text=_("Failed login attempts before account lockout."),
    )
    lockout_duration_minutes = models.PositiveIntegerField(
        _("Lockout Duration (minutes)"),
        default=30,
        help_text=_("Minutes an account is locked after too many failed attempts."),
    )
    password_validity_days = models.PositiveIntegerField(
        _("Password Validity (days)"),
        null=True,
        blank=True,
        help_text=_("Number of days a password is valid (null for no expiration)."),
    )
    require_2fa_for_admin = models.BooleanField(
        _("Require 2FA for Administrators"),
        default=False,
    )

    # Authentication Configuration
    invitation_expiry_days = models.PositiveIntegerField(
        _("Invitation Expiry (days)"),
        default=7,
        help_text=_("Days before an invitation expires."),
    )
    password_reset_token_expiry_hours = models.PositiveIntegerField(
        _("Password Reset Token Expiry (hours)"),
        default=1,
        help_text=_("Hours before a password reset token expires."),
    )
    login_attempt_threshold = models.PositiveIntegerField(
        _("Login Attempt Threshold"),
        default=5,
        help_text=_("Number of failed login attempts to trigger security actions."),
    )

    # Workflow Configuration
    default_review_deadline_hours = models.PositiveIntegerField(
        _("Default Review Deadline (hours)"),
        default=24,
        help_text=_("Default hours to complete a review."),
    )
    default_approval_deadline_hours = models.PositiveIntegerField(
        _("Default Approval Deadline (hours)"),
        default=24,
        help_text=_("Default hours to complete an approval."),
    )
    default_correction_deadline_hours = models.PositiveIntegerField(
        _("Default Correction Deadline (hours)"),
        default=24,
        help_text=_("Default hours to complete corrections."),
    )
    default_escalation_delay_hours = models.PositiveIntegerField(
        _("Default Escalation Delay (hours)"),
        default=6,
        help_text=_("Default hours before escalating an overdue review or approval."),
    )

    # Audit Configuration
    audit_retention_days = models.PositiveIntegerField(
        _("Audit Retention (days)"),
        default=365,
        help_text=_("How long to retain audit logs before deletion."),
    )
    audit_log_enabled = models.BooleanField(
        _("Enable Audit Logging"),
        default=True,
    )

    # Dashboard Configuration
    DASHBOARD_LANDING_PAGE_CHOICES = [
        ("overview", _("Overview")),
        ("reports", _("Reports")),
        ("tasks", _("Tasks")),
        ("calendar", _("Calendar")),
    ]
    default_dashboard_landing_page = models.CharField(
        _("Default Dashboard Landing Page"),
        max_length=20,
        choices=DASHBOARD_LANDING_PAGE_CHOICES,
        default="overview",
    )
    dashboard_refresh_interval_seconds = models.PositiveIntegerField(
        _("Dashboard Refresh Interval (seconds)"),
        default=300,
        help_text=_("How often to refresh dashboard data (in seconds)."),
    )

    # Maintenance Configuration
    maintenance_mode_enabled = models.BooleanField(
        _("Maintenance Mode Enabled"),
        default=False,
    )
    maintenance_message = models.TextField(
        _("Maintenance Message"),
        blank=True,
        help_text=_("Message to display to users when maintenance mode is enabled."),
    )
    maintenance_start_time = models.DateTimeField(
        _("Maintenance Start Time"),
        null=True,
        blank=True,
    )
    maintenance_end_time = models.DateTimeField(
        _("Maintenance End Time"),
        null=True,
        blank=True,
    )
    maintenance_allowed_roles = models.JSONField(
        _("Allowed Roles During Maintenance"),
        default=list,
        blank=True,
        help_text=_("List of role names or IDs that can access the system during maintenance."),
    )

    class Meta:
        verbose_name = _("System Configuration")
        verbose_name_plural = _("System Configurations")

    def __str__(self) -> str:
        return _("System Configuration")

    def clean(self):
        """Ensure only one instance exists."""
        if not self.key:
            self.key = "default"
        if SystemConfiguration.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError(_("Only one SystemConfiguration instance is allowed."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SystemConfiguration":
        """Return the singleton settings row, creating it if necessary."""
        return cls.objects.get_or_create(key="default")[0]

