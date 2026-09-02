"""Models for the Export Engine (Phase 27).

The engine tracks the full lifecycle of every export request (``ExportRequest``),
the immutable activity timeline (``ExportActivity``), the centralized
presentation templates (``ExportTemplate``) and the engine configuration
(``ExportConfiguration``).  Generated files are never stored in the public
media tree; they live under ``settings.PRIVATE_MEDIA_ROOT`` and are served
only through the authenticated download endpoint.
"""

from __future__ import annotations

import json
from typing import Any, ClassVar

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import CreatedByModel, TimeStampedModel, UpdatedByModel, UUIDModel

from .constants import (
    DEFAULT_BULK_MAX_ROWS,
    DEFAULT_DOWNLOAD_EXPIRY_HOURS,
    DEFAULT_ENABLED_FORMATS,
    DEFAULT_MAX_COLUMNS,
    DEFAULT_MAX_FILE_SIZE_MB,
    DEFAULT_ORIENTATION,
    DEFAULT_PAGE_SIZE,
    DEFAULT_SENSITIVE_RETENTION_HOURS,
    DEFAULT_STANDARD_RETENTION_HOURS,
    DEFAULT_SYNC_MAX_ROWS,
    ORGANIZATION_EMAIL,
    ORGANIZATION_NAME,
    ORGANIZATION_SHORT_NAME,
    ConfidentialityLevel,
    ExportActivityAction,
    ExportFormat,
    ExportSourceType,
    ExportStatus,
    PageOrientation,
    PageSize,
)

CONFIGURATION_SINGLETON_KEY = "default"

IMMUTABLE_ACTIVITY_MESSAGE = _(
    "Export activity records are immutable and cannot be modified or deleted."
)


class ExportConfiguration(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Singleton engine configuration.

    Only one row may exist (enforced by a unique constraint on a fixed key
    column).  Changes are administrative operations governed by
    ``exports.manage_settings`` and are audit logged.
    """

    singleton_key = models.CharField(
        _("Singleton key"),
        max_length=20,
        default=CONFIGURATION_SINGLETON_KEY,
        unique=True,
    )

    organization_name = models.CharField(
        _("Organization name"), max_length=300, default=ORGANIZATION_NAME
    )
    short_name = models.CharField(
        _("Short name"), max_length=120, default=ORGANIZATION_SHORT_NAME
    )
    contact_email = models.EmailField(_("Contact email"), default=ORGANIZATION_EMAIL)
    website = models.URLField(_("Website"), blank=True)

    default_format = models.CharField(
        _("Default format"),
        max_length=20,
        choices=ExportFormat.choices,
        default=ExportFormat.PDF,
    )
    default_page_size = models.CharField(
        _("Default page size"),
        max_length=10,
        choices=PageSize.choices,
        default=DEFAULT_PAGE_SIZE,
    )
    default_orientation = models.CharField(
        _("Default orientation"),
        max_length=10,
        choices=PageOrientation.choices,
        default=DEFAULT_ORIENTATION,
    )
    logo_enabled = models.BooleanField(_("Branding logo enabled"), default=True)
    enabled_formats = models.JSONField(
        _("Enabled formats"),
        default=list,
        blank=True,
        help_text=_("Formats the engine may produce."),
    )

    max_sync_rows = models.PositiveIntegerField(
        _("Maximum synchronous rows"), default=DEFAULT_SYNC_MAX_ROWS
    )
    max_bulk_rows = models.PositiveIntegerField(
        _("Maximum bulk export rows"), default=DEFAULT_BULK_MAX_ROWS
    )
    max_file_size_mb = models.PositiveIntegerField(
        _("Maximum file size (MB)"), default=DEFAULT_MAX_FILE_SIZE_MB
    )
    max_columns = models.PositiveIntegerField(
        _("Maximum columns"), default=DEFAULT_MAX_COLUMNS
    )
    standard_retention_hours = models.PositiveIntegerField(
        _("Standard retention (hours)"), default=DEFAULT_STANDARD_RETENTION_HOURS
    )
    sensitive_retention_hours = models.PositiveIntegerField(
        _("Sensitive retention (hours)"), default=DEFAULT_SENSITIVE_RETENTION_HOURS
    )
    download_expiry_hours = models.PositiveIntegerField(
        _("Download expiry (hours)"), default=DEFAULT_DOWNLOAD_EXPIRY_HOURS
    )

    class Meta:
        verbose_name = _("Export Configuration")
        verbose_name_plural = _("Export Configuration")
        constraints: ClassVar[list] = [
            models.CheckConstraint(
                check=models.Q(singleton_key=CONFIGURATION_SINGLETON_KEY),
                name="export_configuration_singleton",
            )
        ]

    def __str__(self) -> str:
        return f"Export Configuration ({self.short_name})"

    def save(self, *args, **kwargs) -> None:
        self.singleton_key = CONFIGURATION_SINGLETON_KEY
        super().save(*args, **kwargs)

    @classmethod
    def defaults(cls) -> dict[str, Any]:
        """Return the configuration defaults without touching the database."""
        return {
            "organization_name": ORGANIZATION_NAME,
            "short_name": ORGANIZATION_SHORT_NAME,
            "contact_email": ORGANIZATION_EMAIL,
            "website": "",
            "default_format": ExportFormat.PDF,
            "default_page_size": DEFAULT_PAGE_SIZE,
            "default_orientation": DEFAULT_ORIENTATION,
            "logo_enabled": True,
            "enabled_formats": list(DEFAULT_ENABLED_FORMATS),
            "max_sync_rows": DEFAULT_SYNC_MAX_ROWS,
            "max_bulk_rows": DEFAULT_BULK_MAX_ROWS,
            "max_file_size_mb": DEFAULT_MAX_FILE_SIZE_MB,
            "max_columns": DEFAULT_MAX_COLUMNS,
            "standard_retention_hours": DEFAULT_STANDARD_RETENTION_HOURS,
            "sensitive_retention_hours": DEFAULT_SENSITIVE_RETENTION_HOURS,
            "download_expiry_hours": DEFAULT_DOWNLOAD_EXPIRY_HOURS,
        }

    @classmethod
    def load(cls) -> ExportConfiguration:
        """Return the singleton configuration, creating it when absent."""
        config, _created = cls.objects.get_or_create(
            singleton_key=CONFIGURATION_SINGLETON_KEY,
            defaults=cls.defaults(),
        )
        return config


class ExportTemplate(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """A reusable presentation template for the Export Engine.

    Phase 19 ``ReportTemplate`` defines report *content/schema*; this model
    defines *presentation/output* (page layout, orientation, branding and
    default columns).  Templates are centrally managed by administrators.
    """

    code = models.SlugField(_("Code"), max_length=60, unique=True)
    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)

    source_type = models.CharField(
        _("Source type"),
        max_length=20,
        choices=ExportSourceType.choices,
        default=ExportSourceType.REPORT,
        db_index=True,
    )
    formats = models.JSONField(_("Supported formats"), default=list, blank=True)
    page_size = models.CharField(
        _("Page size"),
        max_length=10,
        choices=PageSize.choices,
        default=DEFAULT_PAGE_SIZE,
    )
    orientation = models.CharField(
        _("Orientation"),
        max_length=10,
        choices=PageOrientation.choices,
        default=DEFAULT_ORIENTATION,
    )
    logo_enabled = models.BooleanField(_("Logo enabled"), default=True)
    header_enabled = models.BooleanField(_("Header enabled"), default=True)
    footer_enabled = models.BooleanField(_("Footer enabled"), default=True)
    show_page_numbers = models.BooleanField(_("Show page numbers"), default=True)
    confidentiality_marking = models.BooleanField(
        _("Confidentiality marking"), default=True
    )
    watermark_text = models.CharField(_("Watermark text"), max_length=80, blank=True)
    default_columns = models.JSONField(_("Default columns"), default=list, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    version = models.PositiveIntegerField(_("Version"), default=1)

    class Meta:
        verbose_name = _("Export Template")
        verbose_name_plural = _("Export Templates")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    @property
    def supported_format_list(self) -> list[str]:
        if not self.formats:
            return []
        return [fmt for fmt in self.formats if fmt in dict(ExportFormat.choices)]

    def bump_version(self, user) -> None:
        self.version += 1
        self.updated_by = user
        self.save(update_fields=["version", "updated_by", "updated_at"])


class ExportRequest(UUIDModel, TimeStampedModel):
    """A single export request and its lifecycle.

    The generated file is written to ``storage_path`` under the private
    export directory.  ``expires_at`` controls secure-download expiry;
    metadata (this row) is always retained for audit/history purposes.
    """

    reference_number = models.CharField(
        _("Export reference"), max_length=80, unique=True, db_index=True
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="export_requests",
        verbose_name=_("Requested by"),
    )

    source_type = models.CharField(
        _("Source type"),
        max_length=20,
        choices=ExportSourceType.choices,
        db_index=True,
    )
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Source content type"),
    )
    source_object_id = models.CharField(
        _("Source object ID"), max_length=100, blank=True
    )
    source_object = GenericForeignKey("source_content_type", "source_object_id")

    format = models.CharField(
        _("Format"),
        max_length=20,
        choices=ExportFormat.choices,
        db_index=True,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ExportStatus.choices,
        default=ExportStatus.PENDING,
        db_index=True,
    )
    filters = models.JSONField(_("Filters"), default=dict, blank=True)
    selected_columns = models.JSONField(_("Selected columns"), default=list, blank=True)

    record_count = models.PositiveIntegerField(_("Record count"), default=0)
    filename = models.CharField(_("Filename"), max_length=255, blank=True)
    storage_path = models.CharField(_("Storage path"), max_length=500, blank=True)
    mime_type = models.CharField(_("MIME type"), max_length=120, blank=True)
    file_size = models.PositiveBigIntegerField(_("File size (bytes)"), default=0)

    confidentiality = models.CharField(
        _("Confidentiality"),
        max_length=30,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.INTERNAL,
        db_index=True,
    )
    is_sensitive = models.BooleanField(_("Sensitive export"), default=False)
    is_bulk = models.BooleanField(_("Bulk export"), default=False)
    confirmed_sensitive = models.BooleanField(
        _("Sensitive export confirmed"), default=False
    )

    # Digital verification
    digital_signature = models.JSONField(
        _("Digital signature"), default=dict, blank=True
    )
    qr_code = models.TextField(_("QR code data"), blank=True)
    barcode = models.CharField(_("Barcode"), max_length=100, blank=True)

    requested_at = models.DateTimeField(_("Requested at"), default=timezone.now)
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    failed_at = models.DateTimeField(_("Failed at"), null=True, blank=True)
    expires_at = models.DateTimeField(_("Expires at"), null=True, blank=True)

    failure_summary = models.TextField(_("Failure summary"), blank=True)
    error_code = models.CharField(_("Error code"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("Export Request")
        verbose_name_plural = _("Export Requests")
        ordering = ("-requested_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["requested_by", "status"]),
            models.Index(fields=["source_type", "status"]),
            models.Index(fields=["format", "status"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["confidentiality"]),
        ]

    def __str__(self) -> str:
        source = self.get_source_type_display()
        format_display = self.get_format_display()
        return f"{self.reference_number} — {source} ({format_display})"

    @property
    def is_downloadable(self) -> bool:
        return (
            self.status == ExportStatus.COMPLETED
            and bool(self.storage_path)
            and (self.expires_at is None or self.expires_at > timezone.now())
        )

    @property
    def is_finished(self) -> bool:
        return self.status in (
            ExportStatus.COMPLETED,
            ExportStatus.FAILED,
            ExportStatus.CANCELLED,
            ExportStatus.EXPIRED,
        )

    def mark_expired(self) -> None:
        """Transition to expired; the metadata is retained, the file is removed."""
        from .services import ExportFileService

        if self.status == ExportStatus.COMPLETED and self.storage_path:
            ExportFileService.delete_export_file(self)
        self.status = ExportStatus.EXPIRED
        self.filename = ""
        self.mime_type = ""
        self.file_size = 0
        self.save(
            update_fields=[
                "status",
                "filename",
                "mime_type",
                "file_size",
                "updated_at",
            ]
        )


class ExportActivity(UUIDModel, TimeStampedModel):
    """Immutable chronological activity timeline for an export request.

    Mirror of the domain-history pattern used by the other modules: created
    rows can never be updated or deleted.
    """

    export_request = models.ForeignKey(
        ExportRequest,
        on_delete=models.CASCADE,
        related_name="activity",
        verbose_name=_("Export request"),
    )
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=ExportActivityAction.choices,
        db_index=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_activities",
        verbose_name=_("Actor"),
    )
    details = models.JSONField(_("Details"), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_("IP address"), null=True, blank=True)
    user_agent = models.CharField(_("User agent"), max_length=500, blank=True)

    class Meta:
        verbose_name = _("Export Activity")
        verbose_name_plural = _("Export Activities")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["export_request", "action"]),
            models.Index(fields=["actor", "action"]),
        ]

    def __str__(self) -> str:
        return f"{self.export_request.reference_number} — {self.get_action_display()}"

    def clean(self) -> None:
        if self.pk:
            raise ValidationError(
                IMMUTABLE_ACTIVITY_MESSAGE,
                code="immutable_export_activity",
            )

    def delete(self, *args, **kwargs) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            IMMUTABLE_ACTIVITY_MESSAGE,
            code="immutable_export_activity",
        )

    def save(self, *args, **kwargs) -> None:
        if self._state.adding is False:
            raise ValidationError(
                IMMUTABLE_ACTIVITY_MESSAGE,
                code="immutable_export_activity",
            )
        super().save(*args, **kwargs)

    @classmethod
    def record(
        cls,
        *,
        request: ExportRequest,
        action: str,
        actor,
        details: dict | None = None,
        request_obj=None,
    ) -> ExportActivity:
        """Append an immutable activity event."""
        ip_address = None
        user_agent = ""
        if request_obj is not None:
            ip_address = request_obj.META.get("REMOTE_ADDR")
            forwarded = request_obj.META.get("HTTP_X_FORWARDED_FOR")
            if forwarded:
                ip_address = forwarded.split(",")[0].strip()
            user_agent = (request_obj.META.get("HTTP_USER_AGENT") or "")[:500]
        return cls.objects.create(
            export_request=request,
            action=action,
            actor=actor,
            details=details or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def to_json(self) -> str:
        """Serialize the activity event (audit-friendly)."""
        return json.dumps(
            {
                "id": str(self.pk),
                "action": self.action,
                "actor_id": str(self.actor_id or ""),
                "details": self.details,
                "timestamp": self.created_at.isoformat() if self.created_at else "",
            },
            default=str,
        )


class ExportQueue(UUIDModel, TimeStampedModel):
    """Queue entry for batch/async export processing."""

    class Status(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        PROCESSING = "PROCESSING", _("Processing")
        COMPLETED = "COMPLETED", _("Completed")
        FAILED = "FAILED", _("Failed")
        CANCELLED = "CANCELLED", _("Cancelled")

    export_request = models.OneToOneField(
        ExportRequest,
        on_delete=models.CASCADE,
        related_name="queue_entry",
        verbose_name=_("Export request"),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    priority = models.IntegerField(_("Priority"), default=0)
    attempts = models.PositiveIntegerField(_("Attempts"), default=0)
    max_attempts = models.PositiveIntegerField(_("Max attempts"), default=3)
    scheduled_for = models.DateTimeField(_("Scheduled for"), null=True, blank=True)
    started_at = models.DateTimeField(_("Started at"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed at"), null=True, blank=True)
    failure_summary = models.TextField(_("Failure summary"), blank=True)
    error_code = models.CharField(_("Error code"), max_length=50, blank=True)

    class Meta:
        verbose_name = _("Export Queue")
        verbose_name_plural = _("Export Queue")
        ordering = ("-priority", "scheduled_for", "created_at")
        indexes: ClassVar[list] = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["scheduled_for"]),
        ]

    def __str__(self) -> str:
        ref = self.export_request.reference_number
        return f"Queue {ref} — {self.get_status_display()}"


class ScheduledExport(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Recurring scheduled export configuration."""

    class Frequency(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        QUARTERLY = "QUARTERLY", _("Quarterly")
        ANNUALLY = "ANNUALLY", _("Annually")
        CUSTOM = "CUSTOM", _("Custom (cron)")

    name = models.CharField(_("Name"), max_length=150)
    description = models.TextField(_("Description"), blank=True)
    source_type = models.CharField(
        _("Source type"),
        max_length=20,
        choices=[
            ("REPORT", "Report"),
            ("REGISTER", "Organizational Register"),
            ("DIRECTORY", "People Directory"),
            ("BENEFICIARY", "Beneficiary"),
            ("PROGRAM", "Program"),
            ("PROJECT", "Project"),
            ("MEAL", "MEAL"),
            ("MEETING", "Meeting"),
            ("DOCUMENT", "Document Metadata"),
            ("SEARCH", "Search Results"),
        ],
    )
    format = models.CharField(
        _("Format"),
        max_length=20,
        choices=[
            ("PDF", "PDF"),
            ("DOCX", "Word (DOCX)"),
            ("XLSX", "Excel (XLSX)"),
            ("CSV", "CSV"),
            ("PRINT_HTML", "Print-ready HTML"),
            ("PNG", "PNG Image"),
            ("JPEG", "JPEG Image"),
        ],
    )
    filters = models.JSONField(_("Filters"), default=dict, blank=True)
    selected_columns = models.JSONField(_("Selected columns"), default=list, blank=True)
    frequency = models.CharField(
        _("Frequency"),
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
    )
    cron_expression = models.CharField(
        _("Cron expression"),
        max_length=100,
        blank=True,
        help_text=_("Used when frequency is CUSTOM"),
    )
    run_at_time = models.TimeField(_("Run at time"), default="02:00")
    day_of_week = models.PositiveSmallIntegerField(
        _("Day of week (1=Mon)"), null=True, blank=True
    )
    day_of_month = models.PositiveSmallIntegerField(
        _("Day of month"), null=True, blank=True
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    last_run_at = models.DateTimeField(_("Last run"), null=True, blank=True)
    next_run_at = models.DateTimeField(_("Next run"), null=True, blank=True)
    notify_on_completion = models.BooleanField(_("Notify on completion"), default=True)
    notify_on_failure = models.BooleanField(_("Notify on failure"), default=True)

    class Meta:
        verbose_name = _("Scheduled Export")
        verbose_name_plural = _("Scheduled Exports")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.get_frequency_display()})"


# ---------------------------------------------------------------------------
# Export Analytics
# ---------------------------------------------------------------------------


class ExportAnalytics(UUIDModel, TimeStampedModel):
    """Aggregated export analytics snapshot.

    Computed periodically by the analytics service; retained for trend analysis
    and dashboard widgets.  Each row represents a time window (e.g., daily,
    weekly, monthly) for a specific dimension combination.
    """

    class Period(models.TextChoices):
        DAILY = "DAILY", _("Daily")
        WEEKLY = "WEEKLY", _("Weekly")
        MONTHLY = "MONTHLY", _("Monthly")
        QUARTERLY = "QUARTERLY", _("Quarterly")
        ANNUALLY = "ANNUALLY", _("Annually")

    period = models.CharField(
        _("Period type"),
        max_length=20,
        choices=Period.choices,
        default=Period.DAILY,
        db_index=True,
    )
    period_start = models.DateTimeField(_("Period start"), db_index=True)
    period_end = models.DateTimeField(_("Period end"), db_index=True)

    # Dimension breakdowns
    source_type = models.CharField(
        _("Source type"),
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("Empty means aggregate across all source types"),
    )
    format = models.CharField(
        _("Format"),
        max_length=20,
        blank=True,
        db_index=True,
        help_text=_("Empty means aggregate across all formats"),
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="export_analytics_agg",
        verbose_name=_("Requested by"),
        help_text=_("Empty means aggregate across all users"),
    )

    # Metrics
    total_exports = models.PositiveIntegerField(_("Total exports"), default=0)
    completed_exports = models.PositiveIntegerField(_("Completed exports"), default=0)
    failed_exports = models.PositiveIntegerField(_("Failed exports"), default=0)
    cancelled_exports = models.PositiveIntegerField(_("Cancelled exports"), default=0)
    expired_exports = models.PositiveIntegerField(_("Expired exports"), default=0)
    total_records_exported = models.PositiveBigIntegerField(
        _("Total records exported"), default=0
    )
    total_file_size_bytes = models.PositiveBigIntegerField(
        _("Total file size (bytes)"), default=0
    )
    avg_generation_time_ms = models.PositiveIntegerField(
        _("Average generation time (ms)"), default=0
    )
    avg_file_size_bytes = models.PositiveIntegerField(
        _("Average file size (bytes)"), default=0
    )

    # Storage
    storage_used_bytes = models.PositiveBigIntegerField(
        _("Storage used (bytes)"), default=0
    )
    storage_expired_bytes = models.PositiveBigIntegerField(
        _("Storage expired (bytes)"), default=0
    )

    # Template usage
    template_usage = models.JSONField(
        _("Template usage"),
        default=dict,
        blank=True,
        help_text=_("Map of template code -> count"),
    )
    user_activity = models.JSONField(
        _("User activity"),
        default=dict,
        blank=True,
        help_text=_("Map of user_id -> export count"),
    )
    format_distribution = models.JSONField(
        _("Format distribution"),
        default=dict,
        blank=True,
        help_text=_("Map of format -> count"),
    )
    source_type_distribution = models.JSONField(
        _("Source type distribution"),
        default=dict,
        blank=True,
        help_text=_("Map of source_type -> count"),
    )

    class Meta:
        verbose_name = _("Export Analytics")
        verbose_name_plural = _("Export Analytics")
        ordering = ("-period_start",)
        indexes: ClassVar[list] = [
            models.Index(fields=["period", "period_start"]),
            models.Index(fields=["source_type", "period_start"]),
            models.Index(fields=["format", "period_start"]),
            models.Index(fields=["requested_by", "period_start"]),
        ]
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=[
                    "period",
                    "period_start",
                    "source_type",
                    "format",
                    "requested_by",
                ],
                name="export_analytics_unique_period_dimensions",
            )
        ]

    def __str__(self) -> str:
        dims = []
        if self.source_type:
            dims.append(self.source_type)
        if self.format:
            dims.append(self.format)
        return f"Analytics {self.get_period_display()} {'/'.join(dims) or 'all'}"

    @property
    def success_rate(self) -> float:
        if self.total_exports == 0:
            return 0.0
        return (self.completed_exports / self.total_exports) * 100

    @property
    def failure_rate(self) -> float:
        if self.total_exports == 0:
            return 0.0
        return (self.failed_exports / self.total_exports) * 100


class ExportTemplateAnalytics(UUIDModel, TimeStampedModel):
    """Per-template export analytics."""

    template = models.ForeignKey(
        "ExportTemplate",
        on_delete=models.CASCADE,
        related_name="analytics",
        verbose_name=_("Export template"),
    )
    period = models.CharField(
        _("Period type"),
        max_length=20,
        choices=ExportAnalytics.Period.choices,
        default=ExportAnalytics.Period.DAILY,
        db_index=True,
    )
    period_start = models.DateTimeField(_("Period start"), db_index=True)
    period_end = models.DateTimeField(_("Period end"), db_index=True)

    export_count = models.PositiveIntegerField(_("Export count"), default=0)
    completed_count = models.PositiveIntegerField(_("Completed count"), default=0)
    failed_count = models.PositiveIntegerField(_("Failed count"), default=0)
    total_records = models.PositiveBigIntegerField(_("Total records"), default=0)
    total_size_bytes = models.PositiveBigIntegerField(_("Total size (bytes)"), default=0)
    avg_generation_time_ms = models.PositiveIntegerField(
        _("Average generation time (ms)"), default=0
    )

    # Format breakdown for this template
    format_breakdown = models.JSONField(
        _("Format breakdown"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("Export Template Analytics")
        verbose_name_plural = _("Export Template Analytics")
        ordering = ("-period_start",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["template", "period", "period_start"],
                name="export_template_analytics_unique",
            )
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["template", "period_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.template.code} — {self.get_period_display()}"


class ExportUserAnalytics(UUIDModel, TimeStampedModel):
    """Per-user export analytics."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="export_analytics_user",
        verbose_name=_("User"),
    )
    period = models.CharField(
        _("Period type"),
        max_length=20,
        choices=ExportAnalytics.Period.choices,
        default=ExportAnalytics.Period.DAILY,
        db_index=True,
    )
    period_start = models.DateTimeField(_("Period start"), db_index=True)
    period_end = models.DateTimeField(_("Period end"), db_index=True)

    export_count = models.PositiveIntegerField(_("Export count"), default=0)
    completed_count = models.PositiveIntegerField(_("Completed count"), default=0)
    failed_count = models.PositiveIntegerField(_("Failed count"), default=0)
    total_records = models.PositiveBigIntegerField(_("Total records"), default=0)
    total_size_bytes = models.PositiveBigIntegerField(_("Total size (bytes)"), default=0)

    # Breakdowns
    format_breakdown = models.JSONField(
        _("Format breakdown"), default=dict, blank=True
    )
    source_type_breakdown = models.JSONField(
        _("Source type breakdown"), default=dict, blank=True
    )
    template_breakdown = models.JSONField(
        _("Template breakdown"), default=dict, blank=True
    )

    class Meta:
        verbose_name = _("Export User Analytics")
        verbose_name_plural = _("Export User Analytics")
        ordering = ("-period_start",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["user", "period", "period_start"],
                name="export_user_analytics_unique",
            )
        ]
        indexes: ClassVar[list] = [
            models.Index(fields=["user", "period_start"]),
        ]

    def __str__(self) -> str:
        return f"{self.user} — {self.get_period_display()}"
