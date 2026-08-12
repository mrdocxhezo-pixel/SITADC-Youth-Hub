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
                condition=models.Q(singleton_key=CONFIGURATION_SINGLETON_KEY),
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
