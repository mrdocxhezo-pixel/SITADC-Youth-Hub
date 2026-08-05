"""
Data models for the reference numbering module.

The module implements the centralized, configurable reference numbering
system: schemes describe the format and sequence policy, sequences track
per-period counters, the registry stores every issued (reserved or assigned)
reference number, and the audit model records every numbering event
immutably.
"""

from __future__ import annotations

from typing import ClassVar, NoReturn

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    CreatedByModel,
    NotesModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)

from .constants import (
    DEFAULT_ORGANIZATION_CODE,
    DEFAULT_PATTERN,
    ReferenceAuditAction,
    ReferenceModules,
    ReferenceNumberStatus,
    SchemeStatus,
    SequenceResetPeriod,
)
from .managers import ReferenceNumberSchemeManager

IMMUTABLE_REFERENCE_RECORD_MESSAGE = _(
    "Reference registry and audit records are immutable and cannot be modified."
)


class ReferenceNumberScheme(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, NotesModel
):
    """
    A configurable reference number scheme.

    A scheme combines the prefix, the tokenized pattern, the organization
    code and the sequence policy.  Every reference number is generated from a
    scheme through the centralized numbering service.
    """

    name = models.CharField(_("Name"), max_length=150)
    code = models.SlugField(_("Code"), max_length=50, unique=True)
    description = models.TextField(_("Description"), blank=True)
    module = models.CharField(
        _("Module"),
        max_length=60,
        choices=ReferenceModules.choices,
        db_index=True,
    )
    record_type = models.CharField(
        _("Record type"),
        max_length=100,
        blank=True,
        help_text=_("Optional narrower type within the module."),
    )
    prefix = models.CharField(_("Prefix"), max_length=10, db_index=True)
    pattern = models.CharField(_("Pattern"), max_length=250, default=DEFAULT_PATTERN)
    organization_code = models.CharField(
        _("Organization code"), max_length=20, default=DEFAULT_ORGANIZATION_CODE
    )
    sequence_length = models.PositiveSmallIntegerField(
        _("Sequence length"),
        default=6,
        help_text=_("Width of the zero-padded sequence token."),
    )
    start_value = models.PositiveIntegerField(_("Start value"), default=1)
    reset_period = models.CharField(
        _("Reset period"),
        max_length=20,
        choices=SequenceResetPeriod.choices,
        default=SequenceResetPeriod.NEVER,
    )
    fiscal_start_month = models.PositiveSmallIntegerField(
        _("Fiscal start month"),
        default=1,
        help_text=_(
            "Month the financial year starts (1-12); used when the reset "
            "period is Fiscal."
        ),
    )
    custom_reset_interval_days = models.PositiveIntegerField(
        _("Custom reset interval (days)"),
        null=True,
        blank=True,
        help_text=_("Interval in days; used when the reset period is Custom."),
    )
    is_default_for_module = models.BooleanField(
        _("Default for module"),
        default=False,
        help_text=_(
            "Fall back to this scheme when a module has no record-type "
            "specific scheme."
        ),
    )
    is_default_for_record_type = models.BooleanField(
        _("Default for record type"),
        default=False,
        help_text=_("Use this scheme for the configured module and record type."),
    )
    is_fallback = models.BooleanField(
        _("Organizational fallback"),
        default=False,
        help_text=_("Catch-all scheme used when no module scheme matches."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=SchemeStatus.choices,
        default=SchemeStatus.ACTIVE,
        db_index=True,
    )
    is_active = models.BooleanField(_("Is active"), default=True, db_index=True)

    objects = ReferenceNumberSchemeManager()

    class Meta:
        verbose_name = _("Reference Number Scheme")
        verbose_name_plural = _("Reference Number Schemes")
        ordering = ("module", "name")
        indexes: ClassVar[list] = [
            models.Index(fields=["module", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.prefix} ({self.name})"

    def clean(self) -> None:
        super().clean()
        from .validators import (
            validate_organization_code,
            validate_pattern,
            validate_prefix,
            validate_sequence_length,
        )

        validate_prefix(self.prefix)
        validate_organization_code(self.organization_code)
        validate_sequence_length(self.sequence_length)
        validate_pattern(self.pattern)

    def save(self, *args, **kwargs) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_usable(self) -> bool:
        """A scheme is usable only while active and not archived."""
        return self.status == SchemeStatus.ACTIVE and self.is_active

    def activate(self) -> None:
        """Mark the scheme as active and usable."""
        self.status = SchemeStatus.ACTIVE
        self.is_active = True
        self.save(update_fields=["status", "is_active"])

    def deactivate(self) -> None:
        """Mark the scheme as inactive so no new numbers are issued."""
        self.status = SchemeStatus.INACTIVE
        self.is_active = False
        self.save(update_fields=["status", "is_active"])


class ReferenceSequence(UUIDModel, TimeStampedModel):
    """
    Per-period sequence counter for a scheme.

    Sequence rows are keyed by scheme and period so resets are achieved simply
    by moving to a new period key; existing references are never reused.
    """

    scheme = models.ForeignKey(
        ReferenceNumberScheme,
        on_delete=models.CASCADE,
        related_name="sequences",
        verbose_name=_("Scheme"),
    )
    period_key = models.CharField(_("Period key"), max_length=40, db_index=True)
    start_value = models.PositiveIntegerField(_("Start value"), default=1)
    current_value = models.PositiveIntegerField(_("Current value"), default=0)
    next_value = models.PositiveIntegerField(_("Next value"), default=1)

    class Meta:
        verbose_name = _("Reference Sequence")
        verbose_name_plural = _("Reference Sequences")
        ordering = ("-updated_at",)
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["scheme", "period_key"],
                name="unique_reference_sequence_per_period",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.scheme.code} [{self.period_key}] next={self.next_value}"


class GeneratedReferenceNumber(UUIDModel, TimeStampedModel, CreatedByModel, NotesModel):
    """
    A reference number issued by the numbering service (the registry).

    Registry rows are immutable after creation: the only permitted state
    changes are lifecycle transitions handled by the service, never direct
    edits of the stored reference or sequence values.
    """

    scheme = models.ForeignKey(
        ReferenceNumberScheme,
        on_delete=models.PROTECT,
        related_name="generated_numbers",
        verbose_name=_("Scheme"),
    )
    reference_number = models.CharField(
        _("Reference number"),
        max_length=200,
        unique=True,
        db_index=True,
        help_text=_("Globally unique, immutable reference number."),
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=ReferenceNumberStatus.choices,
        default=ReferenceNumberStatus.RESERVED,
        db_index=True,
    )
    module = models.CharField(_("Module"), max_length=60, db_index=True)
    record_type = models.CharField(_("Record type"), max_length=100, blank=True)
    record_id = models.UUIDField(_("Record ID"), null=True, blank=True, db_index=True)
    sequence_value = models.PositiveIntegerField(_("Sequence value"))
    period_key = models.CharField(_("Period key"), max_length=40, db_index=True)
    tokens_resolved = models.JSONField(_("Resolved tokens"), default=dict, blank=True)
    reserved_at = models.DateTimeField(_("Reserved at"), default=timezone.now)
    assigned_at = models.DateTimeField(_("Assigned at"), null=True, blank=True)
    cancelled_at = models.DateTimeField(_("Cancelled at"), null=True, blank=True)
    voided_at = models.DateTimeField(_("Voided at"), null=True, blank=True)

    class Meta:
        verbose_name = _("Generated Reference Number")
        verbose_name_plural = _("Generated Reference Numbers")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["scheme", "status"]),
        ]
        constraints: ClassVar[list] = [
            models.UniqueConstraint(
                fields=["scheme", "period_key", "sequence_value"],
                name="unique_sequence_value_per_scheme_period",
            ),
        ]

    def __str__(self) -> str:
        return self.reference_number

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_REFERENCE_RECORD_MESSAGE,
                code="immutable_reference_record",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_REFERENCE_RECORD_MESSAGE,
            code="immutable_reference_record",
        )

    def transition(self, *, status, record_id=None, **timestamps) -> None:
        """
        Apply a lifecycle-only transition without touching stored values.

        Direct edits of the reference, scheme or sequence fields remain
        prohibited; this method updates only status and lifecycle timestamps.
        """
        updates = {"status": status, "updated_at": timezone.now()}
        if record_id is not None:
            updates["record_id"] = record_id
        for field, value in timestamps.items():
            if value is not None:
                updates[field] = value
        GeneratedReferenceNumber.objects.filter(pk=self.pk).update(**updates)
        self.refresh_from_db()


class ReferenceNumberAuditRecord(UUIDModel, TimeStampedModel):
    """Immutable audit trail of every numbering event."""

    entity_type = models.CharField(_("Entity type"), max_length=60, db_index=True)
    entity_id = models.CharField(_("Entity ID"), max_length=60, db_index=True)
    action = models.CharField(
        _("Action"),
        max_length=40,
        choices=ReferenceAuditAction.choices,
        db_index=True,
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reference_audit_records",
        verbose_name=_("Changed by"),
    )
    from_data = models.JSONField(_("From data"), default=dict, blank=True)
    to_data = models.JSONField(_("To data"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Reference Number Audit Record")
        verbose_name_plural = _("Reference Number Audit Records")
        ordering = ("-created_at",)
        indexes: ClassVar[list] = [
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.entity_type} {self.entity_id} - {self.get_action_display()}"

    def save(self, *args, **kwargs) -> None:
        if not self._state.adding:
            raise ValidationError(
                IMMUTABLE_REFERENCE_RECORD_MESSAGE,
                code="immutable_reference_audit",
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs) -> NoReturn:
        raise ValidationError(
            IMMUTABLE_REFERENCE_RECORD_MESSAGE,
            code="immutable_reference_audit",
        )
