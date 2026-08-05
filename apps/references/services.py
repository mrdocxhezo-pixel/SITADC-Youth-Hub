"""
Business services for the reference numbering module.

Every state-changing numbering operation flows through these services so that
invariants are enforced transactionally:

* the sequence is locked (``select_for_update``), incremented and written in
  the same transaction as the registry row,
* duplicate generation is retried transparently and then prevented by the
  database uniqueness constraints,
* issued numbers are immutable (reserved / assigned / cancelled / voided),
* every event is appended to the immutable audit trail.

Business modules must request numbers only through ``ReferenceNumberService``.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission

from .constants import (
    DEFAULT_ORGANIZATION_CODE,
    DEFAULT_PATTERN,
    ReferenceAuditAction,
    ReferenceNumberStatus,
)
from .exceptions import ReferenceNumberCollisionError
from .models import (
    GeneratedReferenceNumber,
    ReferenceNumberAuditRecord,
    ReferenceNumberScheme,
    ReferenceSequence,
)
from .numbering import (
    build_token_map,
    current_period_key,
    render_reference,
    resolve_scheme,
)
from .permissions import (
    REFERENCE_NUMBERS_CREATE,
    REFERENCE_NUMBERS_RESET,
    REFERENCE_NUMBERS_UPDATE,
)

logger = logging.getLogger(__name__)

MAX_GENERATION_ATTEMPTS = 5


def record_reference_audit(
    entity_type: str,
    entity_id,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> ReferenceNumberAuditRecord:
    """Append an immutable audit record for a numbering event."""
    return ReferenceNumberAuditRecord.objects.create(
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


def _require_permission(user, permission_code: str) -> None:
    """Raise PermissionDenied unless the user holds the permission."""
    if not user_has_permission(user, permission_code):
        raise PermissionDenied


def _scheme_changed_fields(scheme, **fields) -> dict:
    """Return only the field names whose value actually changed.

    The ``updated_by`` audit field is intentionally excluded so it never
    leaks into serialized audit JSON.
    """
    changed: dict = {}
    for field, value in fields.items():
        if field == "updated_by":
            continue
        if getattr(scheme, field) != value:
            changed[field] = value
    return changed


class CreateReferenceNumberSchemeService(BaseService):
    """Create a new reference number scheme."""

    def _execute(
        self,
        name: str,
        code: str,
        module: str,
        record_type: str = "",
        description: str = "",
        prefix: str = "",
        pattern: str | None = None,
        organization_code: str | None = None,
        sequence_length: int = 6,
        start_value: int = 1,
        reset_period: str = "NEVER",
        fiscal_start_month: int = 1,
        custom_reset_interval_days: int | None = None,
        is_default_for_module: bool = False,
        is_default_for_record_type: bool = False,
        is_fallback: bool = False,
        notes: str = "",
    ) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_CREATE)

        scheme = ReferenceNumberScheme.objects.create(
            name=name,
            code=code,
            module=module,
            record_type=record_type,
            description=description,
            prefix=prefix,
            pattern=pattern or DEFAULT_PATTERN,
            organization_code=organization_code or DEFAULT_ORGANIZATION_CODE,
            sequence_length=sequence_length,
            start_value=start_value,
            reset_period=reset_period,
            fiscal_start_month=fiscal_start_month,
            custom_reset_interval_days=custom_reset_interval_days,
            is_default_for_module=is_default_for_module,
            is_default_for_record_type=is_default_for_record_type,
            is_fallback=is_fallback,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.CREATED,
            self.user,
            to_data={"name": scheme.name, "code": scheme.code, "module": scheme.module},
            notes="Reference number scheme created.",
        )
        logger.info(f"Created reference scheme {scheme.code} by {self.user}")
        return scheme


class UpdateReferenceNumberSchemeService(BaseService):
    """Update an existing reference number scheme."""

    def _execute(
        self,
        scheme: ReferenceNumberScheme,
        name: str,
        description: str = "",
        record_type: str | None = None,
        prefix: str | None = None,
        pattern: str | None = None,
        organization_code: str | None = None,
        sequence_length: int | None = None,
        start_value: int | None = None,
        reset_period: str | None = None,
        fiscal_start_month: int | None = None,
        custom_reset_interval_days: int | None = None,
        is_default_for_module: bool | None = None,
        is_default_for_record_type: bool | None = None,
        is_fallback: bool | None = None,
        notes: str | None = None,
    ) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_UPDATE)

        from_data = {
            "name": scheme.name,
            "description": scheme.description,
            "record_type": scheme.record_type,
            "prefix": scheme.prefix,
            "pattern": scheme.pattern,
            "organization_code": scheme.organization_code,
            "sequence_length": scheme.sequence_length,
            "start_value": scheme.start_value,
            "reset_period": scheme.reset_period,
            "fiscal_start_month": scheme.fiscal_start_month,
            "custom_reset_interval_days": scheme.custom_reset_interval_days,
            "is_default_for_module": scheme.is_default_for_module,
            "is_default_for_record_type": scheme.is_default_for_record_type,
            "is_fallback": scheme.is_fallback,
            "notes": scheme.notes,
        }

        updates = {
            "name": name,
            "description": description,
            "record_type": (
                record_type if record_type is not None else scheme.record_type
            ),
            "prefix": prefix if prefix is not None else scheme.prefix,
            "pattern": pattern if pattern is not None else scheme.pattern,
            "organization_code": (
                organization_code
                if organization_code is not None
                else scheme.organization_code
            ),
            "sequence_length": (
                sequence_length
                if sequence_length is not None
                else scheme.sequence_length
            ),
            "start_value": (
                start_value if start_value is not None else scheme.start_value
            ),
            "reset_period": (
                reset_period if reset_period is not None else scheme.reset_period
            ),
            "fiscal_start_month": (
                fiscal_start_month
                if fiscal_start_month is not None
                else scheme.fiscal_start_month
            ),
            "custom_reset_interval_days": (
                custom_reset_interval_days
                if custom_reset_interval_days is not None
                else scheme.custom_reset_interval_days
            ),
            "is_default_for_module": (
                is_default_for_module
                if is_default_for_module is not None
                else scheme.is_default_for_module
            ),
            "is_default_for_record_type": (
                is_default_for_record_type
                if is_default_for_record_type is not None
                else scheme.is_default_for_record_type
            ),
            "is_fallback": (
                is_fallback if is_fallback is not None else scheme.is_fallback
            ),
            "notes": notes if notes is not None else scheme.notes,
        }

        changed = _scheme_changed_fields(scheme, **updates)
        for field, value in changed.items():
            setattr(scheme, field, value)
        scheme.updated_by = self.user
        scheme.full_clean()
        scheme.save()
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.UPDATED,
            self.user,
            from_data={field: from_data.get(field) for field in changed},
            to_data=changed,
            notes="Reference number scheme updated.",
        )
        logger.info(f"Updated reference scheme {scheme.code} by {self.user}")
        return scheme


class ActivateReferenceNumberSchemeService(BaseService):
    """Activate a scheme so it can issue numbers again."""

    def _execute(self, scheme: ReferenceNumberScheme) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_UPDATE)
        scheme.activate()
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.ACTIVATED,
            self.user,
            notes="Reference number scheme activated.",
        )
        return scheme


class DeactivateReferenceNumberSchemeService(BaseService):
    """Deactivate a scheme; no new numbers are issued while inactive."""

    def _execute(self, scheme: ReferenceNumberScheme) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_UPDATE)
        scheme.deactivate()
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.DEACTIVATED,
            self.user,
            notes="Reference number scheme deactivated.",
        )
        return scheme


class ArchiveReferenceNumberSchemeService(BaseService):
    """Archive a scheme to preserve configuration without deletion."""

    def _execute(self, scheme: ReferenceNumberScheme) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_UPDATE)
        if scheme.status == "ARCHIVED":
            raise ValidationError(_("Scheme is already archived."))
        scheme.status = "ARCHIVED"
        scheme.is_active = False
        scheme.save(update_fields=["status", "is_active"])
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.ARCHIVED,
            self.user,
            notes="Reference number scheme archived.",
        )
        return scheme


class RestoreReferenceNumberSchemeService(BaseService):
    """Restore an archived scheme back to active use."""

    def _execute(self, scheme: ReferenceNumberScheme) -> ReferenceNumberScheme:
        _require_permission(self.user, REFERENCE_NUMBERS_UPDATE)
        scheme.activate()
        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.RESTORED,
            self.user,
            notes="Reference number scheme restored.",
        )
        return scheme


class ReferenceNumberService(BaseService):
    """
    The centralized numbering service.

    Allocates the next sequence value under a row lock, renders the reference
    and writes the immutable registry row.  Duplicate allocation is retried
    transparently; the database uniqueness constraints guarantee that no two
    references can ever collide.
    """

    def _execute(
        self,
        module: str,
        record_type: str | None = None,
        scheme_code: str | None = None,
        context: dict | None = None,
        notes: str = "",
    ) -> GeneratedReferenceNumber:
        context = dict(context or {})
        scheme = resolve_scheme(module, record_type, scheme_code)
        period_key = current_period_key(scheme)

        reference = None
        for attempt in range(MAX_GENERATION_ATTEMPTS):
            try:
                with transaction.atomic():
                    next_value = self._allocate_next_value(scheme, period_key)
                    reference_number = render_reference(scheme, next_value, context)
                    reference = GeneratedReferenceNumber.objects.create(
                        scheme=scheme,
                        reference_number=reference_number,
                        status=ReferenceNumberStatus.RESERVED,
                        module=scheme.module,
                        record_type=scheme.record_type or record_type or "",
                        sequence_value=next_value,
                        period_key=period_key,
                        tokens_resolved=build_token_map(scheme, next_value, context),
                        reserved_at=timezone.now(),
                        created_by=self.user,
                        notes=notes,
                    )
                    break
            except IntegrityError:
                logger.warning(
                    "Reference collision on attempt %s for scheme %s; retrying.",
                    attempt + 1,
                    scheme.code,
                )
                continue

        if reference is None:
            raise ReferenceNumberCollisionError(
                f"Could not allocate a unique reference number for scheme "
                f"{scheme.code!r} after {MAX_GENERATION_ATTEMPTS} attempts."
            )

        record_reference_audit(
            "GeneratedReferenceNumber",
            reference.pk,
            ReferenceAuditAction.RESERVED,
            self.user,
            to_data={"reference_number": reference.reference_number},
            notes="Reference number reserved.",
        )
        logger.info(
            "Reserved reference %s (scheme %s) by %s",
            reference.reference_number,
            scheme.code,
            self.user,
        )
        return reference

    def _allocate_next_value(
        self, scheme: ReferenceNumberScheme, period_key: str
    ) -> int:
        """Lock the sequence row, increment it and return the new value."""
        (
            sequence,
            _created,
        ) = ReferenceSequence.objects.select_for_update().get_or_create(
            scheme=scheme,
            period_key=period_key,
            defaults={
                "start_value": scheme.start_value,
                "current_value": scheme.start_value - 1,
                "next_value": scheme.start_value,
            },
        )
        next_value = sequence.next_value
        ReferenceSequence.objects.filter(pk=sequence.pk).update(
            current_value=next_value,
            next_value=next_value + 1,
            updated_at=timezone.now(),
        )
        return next_value


class ConfirmReferenceAssignmentService(BaseService):
    """Confirm a reserved reference against a persisted record."""

    def _execute(
        self,
        reference: GeneratedReferenceNumber,
        record_id,
        notes: str = "",
    ) -> GeneratedReferenceNumber:
        if reference.status != ReferenceNumberStatus.RESERVED:
            raise ValidationError(_("Only reserved references can be assigned."))
        reference.transition(
            status=ReferenceNumberStatus.ASSIGNED,
            record_id=record_id,
            assigned_at=timezone.now(),
        )
        record_reference_audit(
            "GeneratedReferenceNumber",
            reference.pk,
            ReferenceAuditAction.ASSIGNED,
            self.user,
            to_data={
                "reference_number": reference.reference_number,
                "record_id": str(record_id),
            },
            notes=notes or "Reference confirmed and assigned.",
        )
        return reference


class CancelReferenceReservationService(BaseService):
    """Cancel a reservation without reusing the reserved value."""

    def _execute(
        self,
        reference: GeneratedReferenceNumber,
        notes: str = "",
    ) -> GeneratedReferenceNumber:
        if reference.status != ReferenceNumberStatus.RESERVED:
            raise ValidationError(_("Only reserved references can be cancelled."))
        reference.transition(
            status=ReferenceNumberStatus.CANCELLED,
            cancelled_at=timezone.now(),
        )
        record_reference_audit(
            "GeneratedReferenceNumber",
            reference.pk,
            ReferenceAuditAction.CANCELLED,
            self.user,
            to_data={"reference_number": reference.reference_number},
            notes=notes or "Reservation cancelled; value will not be reused.",
        )
        return reference


class VoidReferenceService(BaseService):
    """Void an assigned reference; the value is never reused."""

    def _execute(
        self,
        reference: GeneratedReferenceNumber,
        notes: str = "",
    ) -> GeneratedReferenceNumber:
        if reference.status != ReferenceNumberStatus.ASSIGNED:
            raise ValidationError(_("Only assigned references can be voided."))
        reference.transition(
            status=ReferenceNumberStatus.VOIDED,
            voided_at=timezone.now(),
        )
        record_reference_audit(
            "GeneratedReferenceNumber",
            reference.pk,
            ReferenceAuditAction.VOIDED,
            self.user,
            to_data={"reference_number": reference.reference_number},
            notes=notes or "Reference voided.",
        )
        return reference


class ManualReferenceCorrectionService(BaseService):
    """
    Authorized manual correction of a misassigned reference.

    The original number is voided (never reused) and a fresh replacement is
    issued from the same scheme so the corrected reference stays valid.
    """

    def _execute(
        self,
        generated: GeneratedReferenceNumber,
        reason: str = "",
    ) -> GeneratedReferenceNumber:
        if not reason.strip():
            raise ValidationError(
                _("A reason is required for manual reference correction.")
            )
        VoidReferenceService(user=self.user).execute(
            reference=generated, notes=f"Manual correction: {reason}"
        )
        replacement = ReferenceNumberService(user=self.user).execute(
            module=generated.module,
            record_type=generated.record_type or None,
            scheme_code=generated.scheme.code,
            context=dict(generated.tokens_resolved or {}),
            notes=f"Replacement for corrected reference {generated.reference_number}.",
        )
        replacement.transition(
            status=ReferenceNumberStatus.ASSIGNED,
            record_id=generated.record_id,
            assigned_at=timezone.now(),
        )
        record_reference_audit(
            "GeneratedReferenceNumber",
            replacement.pk,
            ReferenceAuditAction.CORRECTED,
            self.user,
            from_data={"reference_number": generated.reference_number},
            to_data={"reference_number": replacement.reference_number},
            notes=f"Manual correction: {reason}",
        )
        return replacement


class ResetReferenceSequenceService(BaseService):
    """Reset a scheme's sequence to a new starting value."""

    def _execute(
        self,
        scheme: ReferenceNumberScheme,
        start_value: int,
        notes: str = "",
    ) -> ReferenceSequence:
        _require_permission(self.user, REFERENCE_NUMBERS_RESET)

        if start_value < 1:
            raise ValidationError(_("Start value must be at least 1."))

        period_key = current_period_key(scheme)
        with transaction.atomic():
            (
                sequence,
                _created,
            ) = ReferenceSequence.objects.select_for_update().get_or_create(
                scheme=scheme,
                period_key=period_key,
                defaults={
                    "start_value": start_value,
                    "current_value": start_value - 1,
                    "next_value": start_value,
                },
            )
            # The sequence never goes backwards: resuming one past the highest
            # value already issued takes precedence over the requested start.
            next_value = max(start_value, sequence.current_value + 1)
            ReferenceSequence.objects.filter(pk=sequence.pk).update(
                start_value=start_value,
                current_value=next_value - 1,
                next_value=next_value,
                updated_at=timezone.now(),
            )
            sequence.refresh_from_db()

        record_reference_audit(
            "ReferenceNumberScheme",
            scheme.pk,
            ReferenceAuditAction.RESET,
            self.user,
            to_data={"start_value": start_value, "next_value": sequence.next_value},
            notes=notes or "Sequence reset by administrator.",
        )
        logger.info(
            "Reset reference sequence for %s to %s by %s",
            scheme.code,
            next_value,
            self.user,
        )
        return sequence
