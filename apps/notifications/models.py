"""Data models for the Phase 25 Notifications & Announcements module.

The module provides the single centralized notification infrastructure for the
SITADC Youth Hub: notifications, templates, rules, preferences, delivery
tracking, announcements, and the immutable event timeline.  All state changes
flow through the service layer.
"""

# ruff: noqa: RUF012 - Django Meta options are declarative class attributes.

from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    ArchivableModel,
    CreatedByModel,
    IsActiveModel,
    NotesModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role

from .constants import (
    DEFAULT_ANNOUNCEMENT_EXPIRY_DAYS,
    DEFAULT_NOTIFICATION_EXPIRY_DAYS,
    DEFAULT_RETRY_BACKOFF_MINUTES,
    MAX_DELIVERY_RETRIES,
    AnnouncementAudience,
    AnnouncementType,
    DeliveryChannel,
    DeliveryStatus,
    DigestFrequency,
    EscalationLevel,
    NotificationPriority,
    NotificationSeverity,
    NotificationStatus,
    NotificationType,
    QuietHoursPolicy,
    ReadStatus,
    ReminderFrequency,
)
from .constants import (
    NotificationCategory as NotificationCategoryChoices,
)
from .managers import (
    NotificationDeliveryManager,
    NotificationManager,
    NotificationPreferenceManager,
    NotificationRuleManager,
    NotificationTemplateManager,
    SystemAnnouncementManager,
)
from .validators import (
    validate_reminder_offsets,
    validate_template_variables,
)


class NotificationRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Common actor and timestamp metadata for notification domain rows."""

    class Meta:
        abstract = True


class NotificationEvent(NotificationRecord, NotesModel):
    """
    An immutable record of a domain event that may produce notifications.

    Modules emit events through ``NotificationEventService``; rules decide
    whether notifications are created from each event.  The record is never
    edited after creation so the notification history remains auditable.
    """

    event_type = models.CharField(
        _("Event type"),
        max_length=100,
        db_index=True,
        help_text=_("e.g. report.submitted, meeting.scheduled, action.overdue"),
    )
    source_app = models.CharField(_("Source application"), max_length=50, db_index=True)
    source_model = models.CharField(_("Source model"), max_length=100, blank=True)
    source_object_id = models.CharField(
        _("Source object ID"), max_length=100, blank=True, db_index=True
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_events_created",
        verbose_name=_("Actor"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_events",
        verbose_name=_("Organization unit"),
    )
    payload = models.JSONField(
        _("Payload"),
        default=dict,
        blank=True,
        help_text=_("Safe, non-sensitive event context used for template rendering."),
    )
    deduplication_key = models.CharField(
        _("Deduplication key"),
        max_length=255,
        blank=True,
        db_index=True,
        help_text=_("Optional key used to collapse repeated identical events."),
    )
    processed = models.BooleanField(_("Processed"), default=False, db_index=True)
    processed_at = models.DateTimeField(_("Processed at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Notification Event")
        verbose_name_plural = _("Notification Events")
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=[
                    "event_type",
                    "source_app",
                    "source_model",
                    "source_object_id",
                ]
            ),
            models.Index(fields=["deduplication_key", "processed"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "event_type",
                    "source_app",
                    "source_model",
                    "source_object_id",
                    "deduplication_key",
                ],
                name="uniq_notification_event_source",
            )
        ]

    def __str__(self) -> str:
        return f"{self.event_type} @ {self.created_at:%Y-%m-%d %H:%M}"


class NotificationCategory(NotificationRecord, IsActiveModel, NotesModel):
    """Configurable notification category."""

    code = models.CharField(_("Code"), max_length=50, unique=True)
    name = models.CharField(_("Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(
        _("Icon"), max_length=50, blank=True, help_text=_("Bootstrap Icons class name.")
    )
    color = models.CharField(
        _("Color"), max_length=20, blank=True, help_text=_("Bootstrap color token.")
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    class Meta:
        verbose_name = _("Notification Category")
        verbose_name_plural = _("Notification Categories")
        ordering = ("sort_order", "name")

    def __str__(self) -> str:
        return self.name


class Notification(NotificationRecord, ArchivableModel):
    """
    A single notification addressed to one recipient.

    Delivery state is tracked on ``NotificationDelivery``; ``status`` on this
    row is an aggregate of the individual channel attempts while ``read_status``
    records how the recipient consumed it.
    """

    reference = models.CharField(
        _("Notification reference"),
        max_length=80,
        unique=True,
        blank=True,
        editable=False,
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Recipient"),
        db_index=True,
    )
    category = models.CharField(
        _("Category"),
        max_length=50,
        choices=NotificationCategoryChoices.choices,
        default=NotificationCategoryChoices.GENERAL,
        db_index=True,
    )
    notification_type = models.CharField(
        _("Notification type"),
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.INFORMATION,
        db_index=True,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
        db_index=True,
    )
    severity = models.CharField(
        _("Severity"),
        max_length=20,
        choices=NotificationSeverity.choices,
        default=NotificationSeverity.INFO,
    )
    title = models.CharField(_("Title"), max_length=255)
    message = models.TextField(_("Message"))
    short_message = models.CharField(_("Short message"), max_length=255, blank=True)

    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=NotificationStatus.choices,
        default=NotificationStatus.PENDING,
        db_index=True,
    )
    read_status = models.CharField(
        _("Read status"),
        max_length=20,
        choices=ReadStatus.choices,
        default=ReadStatus.UNREAD,
        db_index=True,
    )
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)

    acknowledgement_required = models.BooleanField(
        _("Acknowledgement required"), default=False
    )
    acknowledged_at = models.DateTimeField(_("Acknowledged at"), null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_acknowledged",
        verbose_name=_("Acknowledged by"),
    )

    source_app = models.CharField(
        _("Source application"), max_length=50, blank=True, db_index=True
    )
    source_model = models.CharField(_("Source model"), max_length=100, blank=True)
    source_object_id = models.CharField(
        _("Source object ID"), max_length=100, blank=True, db_index=True
    )
    source_object_reference = models.CharField(
        _("Source reference"), max_length=80, blank=True
    )

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications_acted",
        verbose_name=_("Actor"),
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Organization unit"),
    )

    deep_link = models.CharField(
        _("Deep link"),
        max_length=500,
        blank=True,
        help_text=_("Internal validated URL or named-route for navigation."),
    )
    action_label = models.CharField(_("Action label"), max_length=100, blank=True)

    scheduled_at = models.DateTimeField(
        _("Scheduled at"), null=True, blank=True, db_index=True
    )
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    expiry_at = models.DateTimeField(
        _("Expires at"), null=True, blank=True, db_index=True
    )

    deduplication_key = models.CharField(
        _("Deduplication key"), max_length=255, blank=True, db_index=True
    )
    event = models.ForeignKey(
        NotificationEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Source event"),
    )
    template = models.ForeignKey(
        "NotificationTemplate",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        verbose_name=_("Template"),
    )

    metadata = models.JSONField(_("Metadata"), default=dict, blank=True)
    is_digest_eligible = models.BooleanField(_("Digest eligible"), default=False)
    digest_sent = models.BooleanField(_("Included in digest"), default=False)

    objects = NotificationManager()
    all_objects = NotificationManager()

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["recipient", "read_status", "created_at"]),
            models.Index(fields=["recipient", "status", "created_at"]),
            models.Index(fields=["status", "scheduled_at"]),
            models.Index(fields=["category", "created_at"]),
            models.Index(fields=["priority", "created_at"]),
            models.Index(fields=["source_app", "source_model", "source_object_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.reference or self.pk} - {self.title}"

    def clean(self) -> None:
        if self.scheduled_at and self.expiry_at and self.scheduled_at > self.expiry_at:
            raise ValidationError(_("Scheduled time cannot be after the expiry time."))
        if self.acknowledged_at and not self.acknowledgement_required:
            raise ValidationError(
                _("Acknowledgement time requires acknowledgement to be required.")
            )

    def save(self, *args, **kwargs) -> None:
        if not self.expiry_at:
            self.expiry_at = timezone.now() + timedelta(
                days=DEFAULT_NOTIFICATION_EXPIRY_DAYS
            )
        super().save(*args, **kwargs)

    def mark_read(self, user=None) -> None:
        """Mark the notification as read by its recipient."""
        if self.read_status != ReadStatus.READ:
            self.read_status = ReadStatus.READ
            self.read_at = timezone.now()
            self.save(update_fields=["read_status", "read_at", "updated_at"])

    def acknowledge(self, user) -> None:
        """Record an acknowledgement where required."""
        if not self.acknowledgement_required:
            return
        self.read_status = ReadStatus.ACKNOWLEDGED
        self.read_at = timezone.now()
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(
            update_fields=[
                "read_status",
                "read_at",
                "acknowledged_at",
                "acknowledged_by",
                "updated_at",
            ]
        )

    def is_expired(self) -> bool:
        return bool(self.expiry_at and self.expiry_at < timezone.now())

    @property
    def icon(self) -> str:
        mapping = {
            NotificationType.INFORMATION: "bi-info-circle",
            NotificationType.SUCCESS: "bi-check-circle",
            NotificationType.WARNING: "bi-exclamation-triangle",
            NotificationType.ACTION_REQUIRED: "bi-clipboard-check",
            NotificationType.REMINDER: "bi-alarm",
            NotificationType.DEADLINE: "bi-hourglass-split",
            NotificationType.OVERDUE: "bi-hourglass-bottom",
            NotificationType.APPROVAL_REQUIRED: "bi-check2-square",
            NotificationType.REVIEW_REQUIRED: "bi-eye",
            NotificationType.RETURNED: "bi-arrow-counterclockwise",
            NotificationType.REJECTED: "bi-x-octagon",
            NotificationType.APPROVED: "bi-check2-circle",
            NotificationType.ASSIGNMENT: "bi-person-plus",
            NotificationType.INVITATION: "bi-envelope-plus",
            NotificationType.MENTION: "bi-at",
            NotificationType.COMMENT: "bi-chat-left-text",
            NotificationType.ANNOUNCEMENT: "bi-megaphone",
            NotificationType.SECURITY_ALERT: "bi-shield-lock",
            NotificationType.SYSTEM_ALERT: "bi-gear",
            NotificationType.ESCALATION: "bi-arrow-up-circle",
        }
        return mapping.get(self.notification_type, "bi-bell")

    @property
    def badge_color(self) -> str:
        mapping = {
            NotificationPriority.LOW: "text-bg-secondary",
            NotificationPriority.NORMAL: "text-bg-primary",
            NotificationPriority.HIGH: "text-bg-warning",
            NotificationPriority.URGENT: "text-bg-danger",
            NotificationPriority.CRITICAL: "text-bg-dark",
        }
        return mapping.get(self.priority, "text-bg-secondary")

    @property
    def delivery_status(self) -> str | None:
        attempts = getattr(self, "delivery_attempts", None)
        if attempts is None or not hasattr(self, "_delivery_status_cache"):
            self._delivery_status_cache = None
            if self.delivery_attempts.count() > 0:
                statuses = set(self.delivery_attempts.values_list("status", flat=True))
                if DeliveryStatus.DELIVERED in statuses:
                    self._delivery_status_cache = DeliveryStatus.DELIVERED
                elif statuses:
                    self._delivery_status_cache = next(iter(statuses))
        return self._delivery_status_cache


class NotificationTemplate(NotificationRecord, IsActiveModel):
    """Safe, allowlisted notification message template."""

    code = models.CharField(_("Code"), max_length=100, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    category = models.CharField(
        _("Category"),
        max_length=50,
        choices=NotificationCategoryChoices.choices,
        default=NotificationCategoryChoices.GENERAL,
    )
    event_type = models.CharField(
        _("Event type"), max_length=100, blank=True, db_index=True
    )
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=DeliveryChannel.choices,
        default=DeliveryChannel.IN_APP,
    )
    subject_template = models.CharField(
        _("Subject template"), max_length=255, blank=True
    )
    title_template = models.CharField(_("Title template"), max_length=255)
    message_template = models.TextField(_("Message template"))
    short_message_template = models.CharField(
        _("Short message template"), max_length=255, blank=True
    )
    action_label = models.CharField(_("Action label"), max_length=100, blank=True)
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    required_variables = models.JSONField(
        _("Required variables"), default=list, blank=True
    )
    version = models.PositiveIntegerField(_("Version"), default=1, editable=False)
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_templates",
        verbose_name=_("Organization scope"),
    )

    objects = NotificationTemplateManager()

    class Meta:
        verbose_name = _("Notification Template")
        verbose_name_plural = _("Notification Templates")
        ordering = ("code",)

    def __str__(self) -> str:
        return self.code

    def clean(self) -> None:
        validate_template_variables(
            subject_template=self.subject_template,
            title_template=self.title_template,
            message_template=self.message_template,
            short_message_template=self.short_message_template,
        )

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)


class NotificationRule(NotificationRecord, IsActiveModel):
    """Configurable rule deciding whether an event produces notifications."""

    name = models.CharField(_("Name"), max_length=150)
    event_type = models.CharField(_("Event type"), max_length=100, db_index=True)
    category = models.CharField(
        _("Category"),
        max_length=50,
        choices=NotificationCategoryChoices.choices,
        default=NotificationCategoryChoices.GENERAL,
    )
    notification_type = models.CharField(
        _("Notification type"),
        max_length=50,
        choices=NotificationType.choices,
        default=NotificationType.INFORMATION,
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    template = models.ForeignKey(
        NotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rules",
        verbose_name=_("Template"),
    )
    channels = models.JSONField(_("Channels"), default=list, blank=True)
    recipient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_rules_specific",
        verbose_name=_("Specific recipient"),
    )
    recipient_role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_rules",
        verbose_name=_("Role recipient"),
    )
    recipient_type = models.CharField(
        _("Recipient type"), max_length=50, default="USER", blank=True
    )
    delay_minutes = models.PositiveIntegerField(_("Delay (minutes)"), default=0)
    reminder_enabled = models.BooleanField(_("Reminder enabled"), default=False)
    reminder_offsets = models.JSONField(
        _("Reminder offsets"),
        default=list,
        blank=True,
        help_text=_("List of offset hours, e.g. [-168, -72, -24, -2, 0, 24, 72]."),
    )
    escalation_enabled = models.BooleanField(_("Escalation enabled"), default=False)
    escalation_level = models.CharField(
        _("Escalation level"),
        max_length=30,
        choices=EscalationLevel.choices,
        blank=True,
    )
    escalation_after_hours = models.PositiveIntegerField(
        _("Escalation after hours"), default=24
    )
    digest_eligible = models.BooleanField(_("Digest eligible"), default=False)
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_rules",
        verbose_name=_("Organization scope"),
    )
    sort_order = models.PositiveIntegerField(_("Sort order"), default=0)

    objects = NotificationRuleManager()

    class Meta:
        verbose_name = _("Notification Rule")
        verbose_name_plural = _("Notification Rules")
        ordering = ("sort_order", "name")
        constraints = [
            models.UniqueConstraint(
                fields=["event_type", "name"], name="uniq_notification_rule_event_name"
            )
        ]

    def __str__(self) -> str:
        return self.name

    def clean(self) -> None:
        validate_reminder_offsets(self.reminder_offsets)


class NotificationPreference(UUIDModel, TimeStampedModel, UpdatedByModel):
    """Per-user channel, category, digest and quiet-hours preferences."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_preference",
        verbose_name=_("User"),
    )
    in_app_enabled = models.BooleanField(_("In-app enabled"), default=True)
    email_enabled = models.BooleanField(_("Email enabled"), default=False)
    sms_enabled = models.BooleanField(_("SMS enabled"), default=False)
    push_enabled = models.BooleanField(_("Push enabled"), default=False)

    digest_frequency = models.CharField(
        _("Digest frequency"),
        max_length=20,
        choices=DigestFrequency.choices,
        default=DigestFrequency.WEEKLY,
    )
    digest_timezone = models.CharField(
        _("Digest timezone"), max_length=64, default="Africa/Lusaka"
    )
    digest_channels = models.JSONField(_("Digest channels"), default=list, blank=True)

    quiet_hours_enabled = models.BooleanField(_("Quiet hours enabled"), default=False)
    quiet_hours_start = models.CharField(
        _("Quiet hours start"), max_length=5, blank=True
    )
    quiet_hours_end = models.CharField(_("Quiet hours end"), max_length=5, blank=True)
    quiet_hours_policy = models.CharField(
        _("Quiet hours policy"),
        max_length=20,
        choices=QuietHoursPolicy.choices,
        default=QuietHoursPolicy.RESPECT,
    )
    timezone = models.CharField(_("Timezone"), max_length=64, default="Africa/Lusaka")

    category_preferences = models.JSONField(
        _("Category preferences"),
        default=dict,
        blank=True,
        help_text=_("Mapping of category to {in_app, email, sms, push} booleans."),
    )
    reminder_frequency = models.CharField(
        _("Reminder frequency"),
        max_length=20,
        choices=ReminderFrequency.choices,
        default=ReminderFrequency.IMMEDIATE,
    )
    marketing_enabled = models.BooleanField(
        _("Marketing/announcements enabled"), default=False
    )
    mandatory_categories = models.JSONField(
        _("Mandatory categories"),
        default=list,
        blank=True,
        help_text=_("Category codes that may not be disabled by the user."),
    )

    objects = NotificationPreferenceManager()

    class Meta:
        verbose_name = _("Notification Preference")
        verbose_name_plural = _("Notification Preferences")

    def __str__(self) -> str:
        return f"Preferences for {self.user}"

    def category_allowed(self, category: str) -> bool:
        """Whether the category is enabled for the user (not muted)."""
        if category in (self.mandatory_categories or []):
            return True
        prefs = self.category_preferences or {}
        if category in prefs:
            return bool(prefs[category].get("in_app", True))
        return True

    def channel_enabled(self, channel: str, category: str = "") -> bool:
        """Whether the given channel is enabled for the category."""
        if channel == DeliveryChannel.IN_APP:
            return self.in_app_enabled and self.category_allowed(category)
        prefs = self.category_preferences or {}
        cat_prefs = prefs.get(category, {})
        if channel == DeliveryChannel.EMAIL:
            return bool(self.email_enabled and cat_prefs.get("email", True))
        if channel == DeliveryChannel.SMS:
            return bool(self.sms_enabled and cat_prefs.get("sms", True))
        if channel == DeliveryChannel.PUSH:
            return bool(self.push_enabled and cat_prefs.get("push", True))
        return False

    def in_quiet_hours(self, when=None) -> bool:
        """Whether ``when`` falls inside the user's quiet hours window."""
        if not self.quiet_hours_enabled:
            return False
        if not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        when = when or timezone.now()
        current_minutes = when.hour * 60 + when.minute
        try:
            start_h, start_m = (int(p) for p in self.quiet_hours_start.split(":"))
            end_h, end_m = (int(p) for p in self.quiet_hours_end.split(":"))
        except ValueError:
            return False
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        if start_minutes <= end_minutes:
            return start_minutes <= current_minutes < end_minutes
        # Window crosses midnight.
        return current_minutes >= start_minutes or current_minutes < end_minutes


class NotificationDelivery(UUIDModel, TimeStampedModel):
    """Per-channel delivery attempt tracking for a notification."""

    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        related_name="delivery_attempts",
        verbose_name=_("Notification"),
    )
    channel = models.CharField(
        _("Channel"), max_length=20, choices=DeliveryChannel.choices, db_index=True
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_deliveries",
        verbose_name=_("Recipient"),
    )
    provider = models.CharField(_("Provider"), max_length=100, blank=True)
    attempt_number = models.PositiveIntegerField(_("Attempt number"), default=1)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.QUEUED,
        db_index=True,
    )
    queued_at = models.DateTimeField(_("Queued at"), auto_now_add=True)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    delivered_at = models.DateTimeField(_("Delivered at"), null=True, blank=True)
    failed_at = models.DateTimeField(_("Failed at"), null=True, blank=True)
    failure_category = models.CharField(
        _("Failure category"), max_length=100, blank=True
    )
    safe_error_summary = models.CharField(
        _("Safe error summary"), max_length=255, blank=True
    )
    provider_reference = models.CharField(
        _("Provider reference"), max_length=255, blank=True
    )
    retry_count = models.PositiveIntegerField(_("Retry count"), default=0)
    next_retry_at = models.DateTimeField(
        _("Next retry at"), null=True, blank=True, db_index=True
    )
    last_error_at = models.DateTimeField(_("Last error at"), null=True, blank=True)
    payload_snapshot = models.JSONField(_("Payload snapshot"), default=dict, blank=True)

    objects = NotificationDeliveryManager()

    class Meta:
        verbose_name = _("Notification Delivery")
        verbose_name_plural = _("Notification Deliveries")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["notification", "channel"]),
            models.Index(fields=["status", "next_retry_at"]),
            models.Index(fields=["channel", "status", "created_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"{self.notification.reference or self.notification_id} / "
            f"{self.channel} / {self.status}"
        )

    def mark_sent(self) -> None:
        self.status = DeliveryStatus.SENT
        self.sent_at = timezone.now()
        self.save(update_fields=["status", "sent_at", "updated_at"])

    def mark_delivered(self) -> None:
        self.status = DeliveryStatus.DELIVERED
        self.delivered_at = timezone.now()
        self.sent_at = self.sent_at or timezone.now()
        self.save(update_fields=["status", "sent_at", "delivered_at", "updated_at"])

    def mark_failed(self, category: str, summary: str, retryable: bool = True) -> None:
        self.status = DeliveryStatus.FAILED
        self.failed_at = timezone.now()
        self.failure_category = category
        self.safe_error_summary = summary[:255]
        self.last_error_at = timezone.now()
        if retryable and self.retry_count < MAX_DELIVERY_RETRIES:
            self.retry_count += 1
            index = min(self.retry_count - 1, len(DEFAULT_RETRY_BACKOFF_MINUTES) - 1)
            self.next_retry_at = timezone.now() + timedelta(
                minutes=DEFAULT_RETRY_BACKOFF_MINUTES[index]
            )
        else:
            self.next_retry_at = None
        self.save(
            update_fields=[
                "status",
                "failed_at",
                "failure_category",
                "safe_error_summary",
                "last_error_at",
                "retry_count",
                "next_retry_at",
                "updated_at",
            ]
        )


class SystemAnnouncement(NotificationRecord):
    """A controlled organizational announcement targeted to an audience."""

    reference = models.CharField(
        _("Announcement reference"),
        max_length=80,
        unique=True,
        blank=True,
        editable=False,
    )
    title = models.CharField(_("Title"), max_length=255)
    message = models.TextField(_("Message"))
    announcement_type = models.CharField(
        _("Announcement type"),
        max_length=30,
        choices=AnnouncementType.choices,
        default=AnnouncementType.ORGANIZATION_WIDE,
    )
    audience_type = models.CharField(
        _("Audience"),
        max_length=30,
        choices=AnnouncementAudience.choices,
        default=AnnouncementAudience.EVERYONE,
    )
    audience_roles = models.ManyToManyField(
        Role,
        blank=True,
        related_name="announcements",
        verbose_name=_("Audience roles"),
    )
    audience_units = models.ManyToManyField(
        OrganizationUnit,
        blank=True,
        related_name="announcements",
        verbose_name=_("Audience organization units"),
    )
    priority = models.CharField(
        _("Priority"),
        max_length=20,
        choices=NotificationPriority.choices,
        default=NotificationPriority.NORMAL,
    )
    category = models.CharField(
        _("Category"),
        max_length=50,
        choices=NotificationCategoryChoices.choices,
        default=NotificationCategoryChoices.ANNOUNCEMENTS,
    )
    publish_at = models.DateTimeField(
        _("Publish at"), default=timezone.now, db_index=True
    )
    expires_at = models.DateTimeField(
        _("Expires at"), null=True, blank=True, db_index=True
    )
    is_published = models.BooleanField(_("Published"), default=False)
    published_at = models.DateTimeField(_("Published at"), null=True, blank=True)
    is_dismissible = models.BooleanField(_("Dismissible"), default=True)
    acknowledgement_required = models.BooleanField(
        _("Acknowledgement required"), default=False
    )
    deep_link = models.CharField(_("Deep link"), max_length=500, blank=True)
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_announcements",
        verbose_name=_("Organization scope"),
    )

    objects = SystemAnnouncementManager()

    class Meta:
        verbose_name = _("System Announcement")
        verbose_name_plural = _("System Announcements")
        ordering = ("-publish_at",)

    def __str__(self) -> str:
        return self.title

    def clean(self) -> None:
        if self.publish_at and self.expires_at and self.publish_at > self.expires_at:
            raise ValidationError(_("Publish time cannot be after the expiry time."))

    def save(self, *args, **kwargs) -> None:
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(
                days=DEFAULT_ANNOUNCEMENT_EXPIRY_DAYS
            )
        super().save(*args, **kwargs)

    def publish(self, user) -> None:
        """Publish the announcement (becomes visible to its audience)."""
        self.is_published = True
        self.published_at = timezone.now()
        self.save(update_fields=["is_published", "published_at", "updated_at"])

    def unpublish(self, user) -> None:
        """Unpublish the announcement (immediately hidden)."""
        self.is_published = False
        self.published_at = None
        self.save(update_fields=["is_published", "published_at", "updated_at"])

    def audience_recipients(self) -> models.QuerySet:
        """Return the queryset of recipients covered by the audience rule."""
        from django.contrib.auth import get_user_model

        User = get_user_model()
        if self.audience_type == AnnouncementAudience.EVERYONE:
            return User.objects.filter(is_active=True)
        if self.audience_type in (
            AnnouncementAudience.SPECIFIC_ROLES,
            AnnouncementAudience.DIRECTORATES,
            AnnouncementAudience.REGIONS,
            AnnouncementAudience.DISTRICTS,
        ):
            role_ids = list(self.audience_roles.values_list("id", flat=True))
            return User.objects.filter(
                role_assignments__role_id__in=role_ids,
                role_assignments__status="ACTIVE",
                is_active=True,
            ).distinct()
        return User.objects.none()


class AnnouncementDelivery(UUIDModel, TimeStampedModel):
    """Tracks delivery of an announcement to an individual user."""

    announcement = models.ForeignKey(
        SystemAnnouncement,
        on_delete=models.CASCADE,
        related_name="deliveries",
        verbose_name=_("Announcement"),
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="announcement_deliveries",
        verbose_name=_("Recipient"),
    )
    delivered_at = models.DateTimeField(_("Delivered at"), null=True, blank=True)
    read_at = models.DateTimeField(_("Read at"), null=True, blank=True)
    dismissed_at = models.DateTimeField(_("Dismissed at"), null=True, blank=True)
    acknowledged_at = models.DateTimeField(_("Acknowledged at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Announcement Delivery")
        verbose_name_plural = _("Announcement Deliveries")
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "recipient"],
                name="uniq_announcement_recipient",
            )
        ]

    def __str__(self) -> str:
        return f"{self.announcement.title} -> {self.recipient}"


class AnnouncementDismissal(UUIDModel, TimeStampedModel):
    """Tracks that a user dismissed a dismissible announcement."""

    announcement = models.ForeignKey(
        SystemAnnouncement,
        on_delete=models.CASCADE,
        related_name="dismissals",
        verbose_name=_("Announcement"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dismissed_announcements",
        verbose_name=_("User"),
    )
    dismissed_at = models.DateTimeField(_("Dismissed at"), auto_now_add=True)

    class Meta:
        verbose_name = _("Announcement Dismissal")
        verbose_name_plural = _("Announcement Dismissals")
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "user"],
                name="uniq_announcement_dismissal",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user} dismissed {self.announcement}"


class NotificationAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable administrative audit trail for notification operations."""

    action = models.CharField(_("Action"), max_length=100)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notification_audit_records",
        verbose_name=_("Actor"),
    )
    target_type = models.CharField(_("Target type"), max_length=100, blank=True)
    target_id = models.CharField(_("Target ID"), max_length=100, blank=True)
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Notification Audit Record")
        verbose_name_plural = _("Notification Audit Records")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["action", "created_at"])]

    def __str__(self) -> str:
        return f"{self.action} @ {self.created_at:%Y-%m-%d %H:%M}"


class NotificationDigest(UUIDModel, TimeStampedModel):
    """A generated digest summarizing pending notifications for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_digests",
        verbose_name=_("User"),
    )
    frequency = models.CharField(
        _("Frequency"),
        max_length=20,
        choices=DigestFrequency.choices,
        default=DigestFrequency.WEEKLY,
    )
    period_start = models.DateTimeField(_("Period start"))
    period_end = models.DateTimeField(_("Period end"))
    summary = models.JSONField(_("Summary"), default=dict, blank=True)
    notification_count = models.PositiveIntegerField(_("Notification count"), default=0)
    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)
    sent_via = models.CharField(_("Sent via"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("Notification Digest")
        verbose_name_plural = _("Notification Digests")
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Digest for {self.user} ({self.frequency})"


# Backwards-compatible alias kept so templates and selectors referencing the
# legacy name continue to work while the canonical model is ``SystemAnnouncement``.
class Announcement(SystemAnnouncement):
    """Deprecated alias for ``SystemAnnouncement``.

    Kept so older views/tests referencing ``Announcement`` keep resolving;
    new code should use ``SystemAnnouncement`` directly.
    """

    class Meta:
        proxy = True
        verbose_name = _("Announcement")
        verbose_name_plural = _("Announcements")
