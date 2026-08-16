from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel, UUIDModel


class UserSettings(UUIDModel, TimeStampedModel):
    """User preferences and settings."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="settings",
        verbose_name=_("User"),
    )

    # Appearance & Personalization
    THEME_CHOICES = [
        ("light", _("Light")),
        ("dark", _("Dark")),
        ("system", _("System Default")),
    ]
    theme = models.CharField(
        _("Theme"),
        max_length=10,
        choices=THEME_CHOICES,
        default="system",
    )
    accent_color = models.CharField(
        _("Accent Color"),
        max_length=20,
        default="primary",
        help_text=_("Bootstrap color token: primary, secondary, success, danger, warning, info"),
    )
    density = models.CharField(
        _("Interface Density"),
        max_length=15,
        choices=[("compact", _("Compact")), ("comfortable", _("Comfortable"))],
        default="comfortable",
    )
    sidebar_collapsed = models.BooleanField(
        _("Sidebar Collapsed"),
        default=False,
    )
    dashboard_layout = models.CharField(
        _("Dashboard Layout"),
        max_length=20,
        choices=[("grid", _("Grid")), ("list", _("List")), ("masonry", _("Masonry"))],
        default="grid",
    )
    animations_enabled = models.BooleanField(
        _("Animations Enabled"),
        default=True,
    )
    reduced_motion = models.BooleanField(
        _("Reduced Motion"),
        default=False,
    )
    high_contrast = models.BooleanField(
        _("High Contrast"),
        default=False,
    )
    larger_text = models.BooleanField(
        _("Larger Text"),
        default=False,
    )
    focus_indicators = models.BooleanField(
        _("Focus Indicators"),
        default=True,
    )

    # Notifications
    email_notifications = models.BooleanField(
        _("Email Notifications"),
        default=True,
    )
    in_app_notifications = models.BooleanField(
        _("In-App Notifications"),
        default=True,
    )
    browser_notifications = models.BooleanField(
        _("Browser Notifications"),
        default=False,
    )
    report_reminders = models.BooleanField(
        _("Report Reminders"),
        default=True,
    )
    report_submission_notifications = models.BooleanField(
        _("Report Submission Notifications"),
        default=True,
    )
    report_review_notifications = models.BooleanField(
        _("Report Review Notifications"),
        default=True,
    )
    approval_notifications = models.BooleanField(
        _("Approval Notifications"),
        default=True,
    )
    meeting_reminders = models.BooleanField(
        _("Meeting Reminders"),
        default=True,
    )
    training_reminders = models.BooleanField(
        _("Training Reminders"),
        default=True,
    )
    task_notifications = models.BooleanField(
        _("Task Notifications"),
        default=True,
    )
    system_announcements = models.BooleanField(
        _("System Announcements"),
        default=True,
    )
    security_alerts = models.BooleanField(
        _("Security Alerts"),
        default=True,
    )
    organizational_announcements = models.BooleanField(
        _("Organizational Announcements"),
        default=True,
    )

    # Privacy
    profile_visibility = models.CharField(
        _("Profile Visibility"),
        max_length=20,
        choices=[
            ("public", _("Public")),
            ("organization", _("Organization Only")),
            ("team", _("Team Only")),
            ("private", _("Private")),
        ],
        default="organization",
    )
    contact_visibility = models.CharField(
        _("Contact Information Visibility"),
        max_length=20,
        choices=[
            ("public", _("Public")),
            ("organization", _("Organization Only")),
            ("team", _("Team Only")),
            ("private", _("Private")),
        ],
        default="organization",
    )
    activity_visibility = models.CharField(
        _("Activity Visibility"),
        max_length=20,
        choices=[
            ("public", _("Public")),
            ("organization", _("Organization Only")),
            ("team", _("Team Only")),
            ("private", _("Private")),
        ],
        default="organization",
    )
    show_online_status = models.BooleanField(
        _("Show Online Status"),
        default=True,
    )
    directory_visibility = models.BooleanField(
        _("Directory Visibility"),
        default=True,
    )
    data_sharing = models.BooleanField(
        _("Data Sharing Preferences"),
        default=False,
    )

    # Language, Region & Time
    language = models.CharField(
        _("Language"),
        max_length=10,
        default="en",
    )
    country = models.CharField(
        _("Country"),
        max_length=2,
        default="ZM",
    )
    timezone = models.CharField(
        _("Timezone"),
        max_length=50,
        default="Africa/Lusaka",
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
    currency_format = models.CharField(
        _("Currency Format"),
        max_length=10,
        default="ZMW",
    )
    first_day_of_week = models.IntegerField(
        _("First Day of Week"),
        default=0,
        choices=[(i, _(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][i])) for i in range(7)],
    )

    class Meta:
        verbose_name = _("User Settings")
        verbose_name_plural = _("User Settings")

    def __str__(self):
        return f"Settings for {self.user.email}"


class SystemSettings(UUIDModel, TimeStampedModel):
    """System-wide settings (admin only)."""

    key = models.SlugField(
        _("Key"),
        max_length=40,
        unique=True,
        default="default",
        help_text=_("Unique key to enforce singleton pattern."),
    )

    # System Configuration
    system_name = models.CharField(_("System Name"), max_length=150, default="SITADC Youth Hub")
    system_short_name = models.CharField(_("System Short Name"), max_length=50, default="SITADC Hub")
    system_email = models.EmailField(_("System Email"), blank=True)
    system_status = models.CharField(
        _("System Status"),
        max_length=20,
        choices=[
            ("operational", _("Operational")),
            ("maintenance", _("Maintenance")),
            ("disabled", _("Disabled")),
        ],
        default="operational",
    )
    maintenance_mode = models.BooleanField(_("Maintenance Mode"), default=False)
    maintenance_message = models.TextField(_("Maintenance Message"), blank=True)
    maintenance_allowed_roles = models.JSONField(_("Allowed Roles During Maintenance"), default=list, blank=True)

    # Session & Security
    session_timeout_minutes = models.PositiveIntegerField(_("Session Timeout (minutes)"), default=30)
    password_min_length = models.PositiveIntegerField(_("Minimum Password Length"), default=8)
    password_require_uppercase = models.BooleanField(_("Require Uppercase"), default=True)
    password_require_lowercase = models.BooleanField(_("Require Lowercase"), default=True)
    password_require_digits = models.BooleanField(_("Require Digits"), default=True)
    password_require_special = models.BooleanField(_("Require Special Characters"), default=True)
    password_expiry_days = models.PositiveIntegerField(_("Password Expiry (days)"), null=True, blank=True)
    max_login_attempts = models.PositiveIntegerField(_("Max Login Attempts"), default=5)
    lockout_duration_minutes = models.PositiveIntegerField(_("Lockout Duration (minutes)"), default=30)
    require_2fa_admin = models.BooleanField(_("Require 2FA for Admins"), default=False)

    # File Upload
    max_upload_size_mb = models.PositiveIntegerField(_("Max Upload Size (MB)"), default=10)
    allowed_file_types = models.JSONField(_("Allowed File Types"), default=list, blank=True)

    # Audit & Logging
    audit_log_enabled = models.BooleanField(_("Audit Logging Enabled"), default=True)
    audit_retention_days = models.PositiveIntegerField(_("Audit Retention (days)"), default=365)

    # Backup
    backup_enabled = models.BooleanField(_("Backup Enabled"), default=True)
    backup_frequency = models.CharField(
        _("Backup Frequency"),
        max_length=20,
        choices=[
            ("daily", _("Daily")),
            ("weekly", _("Weekly")),
            ("monthly", _("Monthly")),
        ],
        default="daily",
    )
    backup_retention_days = models.PositiveIntegerField(_("Backup Retention (days)"), default=30)

    class Meta:
        verbose_name = _("System Settings")
        verbose_name_plural = _("System Settings")

    def __str__(self):
        return _("System Settings")

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.key:
            self.key = "default"
        if SystemSettings.objects.exclude(pk=self.pk).filter(key=self.key).exists():
            raise ValidationError(_("Only one SystemSettings instance is allowed."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="default")[0]


class IntegrationSettings(UUIDModel, TimeStampedModel):
    """External integrations configuration."""

    name = models.CharField(_("Integration Name"), max_length=100)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)

    INTEGRATION_TYPE_CHOICES = [
        ("email", _("Email Service")),
        ("auth", _("Authentication")),
        ("storage", _("Storage")),
        ("notification", _("Notifications")),
        ("api", _("External API")),
        ("other", _("Other")),
    ]
    integration_type = models.CharField(_("Integration Type"), max_length=20, choices=INTEGRATION_TYPE_CHOICES)

    is_active = models.BooleanField(_("Active"), default=False)
    configuration = models.JSONField(_("Configuration"), default=dict, blank=True)
    credentials = models.JSONField(_("Credentials"), default=dict, blank=True)

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

    class Meta:
        verbose_name = _("Integration Settings")
        verbose_name_plural = _("Integration Settings")
        ordering = ("name",)

    def __str__(self):
        return self.name


class UserSettingsDefault(UUIDModel, TimeStampedModel):
    """Default settings for new users."""

    key = models.SlugField(_("Key"), max_length=40, unique=True, default="defaults")

    # Default appearance
    default_theme = models.CharField(_("Default Theme"), max_length=10, choices=UserSettings.THEME_CHOICES, default="system")
    default_density = models.CharField(_("Default Density"), max_length=15, choices=[("compact", _("Compact")), ("comfortable", _("Comfortable"))], default="comfortable")
    default_dashboard_layout = models.CharField(_("Default Dashboard Layout"), max_length=20, choices=[("grid", _("Grid")), ("list", _("List")), ("masonry", _("Masonry"))], default="grid")
    default_animations = models.BooleanField(_("Default Animations Enabled"), default=True)

    # Default notifications
    default_email_notifications = models.BooleanField(_("Default Email Notifications"), default=True)
    default_in_app_notifications = models.BooleanField(_("Default In-App Notifications"), default=True)
    default_browser_notifications = models.BooleanField(_("Default Browser Notifications"), default=False)

    # Default privacy
    default_profile_visibility = models.CharField(_("Default Profile Visibility"), max_length=20, choices=[("public", _("Public")), ("organization", _("Organization Only")), ("team", _("Team Only")), ("private", _("Private"))], default="organization")

    # Default language/region
    default_language = models.CharField(_("Default Language"), max_length=10, default="en")
    default_country = models.CharField(_("Default Country"), max_length=2, default="ZM")
    default_timezone = models.CharField(_("Default Timezone"), max_length=50, default="Africa/Lusaka")

    class Meta:
        verbose_name = _("User Settings Defaults")
        verbose_name_plural = _("User Settings Defaults")

    def __str__(self):
        return _("User Settings Defaults")

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(key="defaults")[0]