"""
Read-only retrieval helpers for the reference numbering module.

Selectors never modify data; they only fetch and shape numbering information
for views, services, templates and management commands.
"""

from __future__ import annotations

from django.db.models import Q, QuerySet

from .constants import ReferenceModules, ReferenceNumberStatus
from .models import (
    GeneratedReferenceNumber,
    ReferenceNumberAuditRecord,
    ReferenceNumberScheme,
    ReferenceSequence,
)
from .numbering import current_period_key, render_reference, resolve_scheme


def get_schemes(module: str | None = None) -> QuerySet[ReferenceNumberScheme]:
    """Return reference number schemes, optionally filtered by module."""
    qs: QuerySet[ReferenceNumberScheme] = ReferenceNumberScheme.objects.all()
    if module:
        qs = ReferenceNumberScheme.objects.for_module(module)
    return qs.select_related()


def get_active_schemes() -> QuerySet[ReferenceNumberScheme]:
    """Return schemes currently able to issue numbers."""
    return ReferenceNumberScheme.objects.active()


def get_scheme_by_id(scheme_id) -> ReferenceNumberScheme | None:
    """Return a single scheme by primary key or ``None``."""
    try:
        return ReferenceNumberScheme.objects.get(pk=scheme_id)
    except ReferenceNumberScheme.DoesNotExist:
        return None


def get_scheme_by_code(code: str) -> ReferenceNumberScheme | None:
    """Return a single scheme by code or ``None``."""
    try:
        return ReferenceNumberScheme.objects.get(code=code)
    except ReferenceNumberScheme.DoesNotExist:
        return None


def get_sequences(
    scheme: ReferenceNumberScheme | None = None,
) -> QuerySet[ReferenceSequence]:
    """Return sequence rows, optionally scoped to a scheme."""
    qs = ReferenceSequence.objects.select_related("scheme")
    if scheme is not None:
        qs = qs.filter(scheme=scheme)
    return qs


def get_generated_numbers(
    scheme: ReferenceNumberScheme | None = None,
    status: str | None = None,
    search: str = "",
) -> QuerySet[GeneratedReferenceNumber]:
    """Return the reference registry, optionally filtered."""
    qs = GeneratedReferenceNumber.objects.select_related("scheme")
    if scheme is not None:
        qs = qs.filter(scheme=scheme)
    if status:
        qs = qs.filter(status=status)
    if search:
        qs = qs.filter(
            Q(reference_number__icontains=search)
            | Q(record_id__icontains=search)
            | Q(scheme__name__icontains=search)
        )
    return qs


def search_by_reference_number(
    query: str, status: str | None = None
) -> QuerySet[GeneratedReferenceNumber]:
    """Search the registry by full or partial reference number."""
    qs = GeneratedReferenceNumber.objects.select_related("scheme").filter(
        reference_number__icontains=query
    )
    if status:
        qs = qs.filter(status=status)
    return qs


def validate_existing_reference(reference_number: str) -> bool:
    """
    Return whether a reference number already exists in the registry.

    Used by forms and services to prevent accidental manual conflicts; the
    database uniqueness constraint remains the definitive control.
    """
    return GeneratedReferenceNumber.objects.filter(
        reference_number=reference_number
    ).exists()


def next_reference_number(
    module: str,
    record_type: str | None = None,
    scheme_code: str | None = None,
    context: dict | None = None,
) -> dict:
    """
    Preview the next reference without consuming the sequence.

    Returns a dict with ``scheme``, ``sequence`` (or ``None`` when no sequence
    exists yet), ``next_value`` and ``reference_number``.  The sequence is
    deliberately never incremented here.
    """
    scheme = resolve_scheme(module, record_type, scheme_code)
    period_key = current_period_key(scheme)
    sequence = ReferenceSequence.objects.filter(
        scheme=scheme, period_key=period_key
    ).first()

    next_value = 1
    if sequence is not None:
        next_value = sequence.next_value

    reference_number = render_reference(scheme, next_value, context)
    return {
        "scheme": scheme,
        "sequence": sequence,
        "period_key": period_key,
        "next_value": next_value,
        "reference_number": reference_number,
    }


def get_reference_configuration() -> dict:
    """Return a summary of the numbering configuration for admins."""
    schemes = ReferenceNumberScheme.objects.all()
    return {
        "total_schemes": schemes.count(),
        "active_schemes": schemes.filter(status="ACTIVE", is_active=True).count(),
        "modules": {
            label: ReferenceNumberScheme.objects.filter(module=value).count()
            for value, label in ReferenceModules.choices
        },
        "prefixes": list(
            schemes.values_list("prefix", flat=True).distinct().order_by("prefix")
        ),
    }


def get_reference_summary() -> dict:
    """Return aggregate counters for dashboard cards."""
    generated = GeneratedReferenceNumber.objects.all()
    return {
        "total_schemes": ReferenceNumberScheme.objects.count(),
        "active_schemes": ReferenceNumberScheme.objects.filter(is_active=True).count(),
        "total_generated": generated.count(),
        "assigned": generated.filter(status=ReferenceNumberStatus.ASSIGNED).count(),
        "reserved": generated.filter(status=ReferenceNumberStatus.RESERVED).count(),
        "sequence_rows": ReferenceSequence.objects.count(),
        "modules_in_use": ReferenceNumberScheme.objects.values("module")
        .distinct()
        .count(),
    }


def get_reference_audit_history(
    entity_type: str | None = None,
    entity_id: str | None = None,
) -> QuerySet[ReferenceNumberAuditRecord]:
    """Return the immutable numbering audit trail, optionally filtered."""
    qs = ReferenceNumberAuditRecord.objects.select_related("changed_by")
    if entity_type:
        qs = qs.filter(entity_type=entity_type)
    if entity_id:
        qs = qs.filter(entity_id=entity_id)
    return qs
