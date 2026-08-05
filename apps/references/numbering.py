"""
Reference rendering and resolution engine.

This module converts a scheme plus a resolved token context into a rendered
reference number and resolves which scheme applies to a given module and
record type.  It is intentionally read-only: sequence values are consumed
only by the numbering service.
"""

from __future__ import annotations

from datetime import date

from django.utils import timezone

from .constants import SequenceResetPeriod
from .exceptions import (
    InactiveNumberingSchemeError,
    InvalidNumberingSchemeError,
    MissingNumberingContextError,
)
from .validators import validate_reference_format


def fiscal_year_label(year: int, fiscal_start_month: int) -> str:
    """
    Return a fiscal year label for the given calendar year.

    The label names the period beginning in ``fiscal_start_month`` of
    ``year`` and ending just before that month of ``year + 1`` (e.g. "2025-26").
    """
    return f"{year:04d}-{str((year % 100) + 1).zfill(2)}"


def current_period_key(scheme, when: date | None = None) -> str:
    """
    Compute the sequence period key for a scheme on the given date.

    Schemes that never reset share a single constant period so their sequence
    runs forever; every other reset policy keys the sequence by its period
    (year, year-month, day, fiscal year, or custom interval).
    """
    when = when or timezone.localdate()

    reset_period = scheme.reset_period
    if reset_period == SequenceResetPeriod.NEVER:
        return "always"

    if reset_period == SequenceResetPeriod.ANNUALLY:
        return f"{when.year:04d}"

    if reset_period == SequenceResetPeriod.MONTHLY:
        return f"{when.year:04d}-{when.month:02d}"

    if reset_period == SequenceResetPeriod.DAILY:
        return when.isoformat()

    if reset_period == SequenceResetPeriod.FISCAL:
        start_month = scheme.fiscal_start_month or 1
        label_year = when.year if when.month >= start_month else when.year - 1
        return fiscal_year_label(label_year, start_month)

    if reset_period == SequenceResetPeriod.CUSTOM:
        interval = scheme.custom_reset_interval_days
        if not interval or interval <= 0:
            raise InvalidNumberingSchemeError(
                "Custom reset requires a positive interval in days."
            )
        epoch = date(2000, 1, 1)
        elapsed_days = (when - epoch).days
        if elapsed_days < 0:
            raise InvalidNumberingSchemeError(
                "Custom reset cannot be evaluated before the reference epoch."
            )
        bucket = int(elapsed_days // interval)
        return f"c{bucket:08d}"

    raise InvalidNumberingSchemeError(f"Unsupported reset period: {reset_period!r}.")


def build_token_map(scheme, sequence_value: int, context: dict | None = None) -> dict:
    """
    Resolve every token the scheme's pattern may reference.

    ``context`` may carry date tokens (year/month/day), the organization code
    and organizational scope tokens (unit, directorate, region, district,
    community, team, program, project).  Values must be present for any token
    the pattern actually uses.
    """
    context = dict(context or {})
    when: date = context.get("when") or timezone.localdate()
    if hasattr(when, "date"):
        when = when.date()
    if context.get("year") and "when" not in context:
        year = int(context["year"])
        month = int(context.get("month") or 1)
        day = int(context.get("day") or 1)
        when = date(year, month, day)

    org = context.get("org") or scheme.organization_code
    values: dict = {
        "PREFIX": scheme.prefix,
        "ORG": org,
        "MODULE": scheme.module,
        "TYPE": scheme.record_type or "",
        "UNIT": context.get("unit") or "",
        "DIRECTORATE": context.get("directorate") or "",
        "REGION": context.get("region") or "",
        "DISTRICT": context.get("district") or "",
        "COMMUNITY": context.get("community") or "",
        "TEAM": context.get("team") or "",
        "PROGRAM": context.get("program") or "",
        "PROJECT": context.get("project") or "",
        "YEAR": f"{when.year:04d}",
        "YEAR_SHORT": f"{when.year % 100:02d}",
        "MONTH": f"{when.month:02d}",
        "DAY": f"{when.day:02d}",
        "FY": fiscal_year_label(when.year, scheme.fiscal_start_month or 1),
        "SEQUENCE": str(sequence_value).zfill(scheme.sequence_length),
    }
    return values


def render_reference(scheme, sequence_value: int, context: dict | None = None) -> str:
    """Render a reference number for the scheme and sequence value."""
    values = build_token_map(scheme, sequence_value, context)

    pattern = scheme.pattern or "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}"
    try:
        reference = pattern.format(**values)
    except KeyError as exc:
        raise InvalidNumberingSchemeError(
            f"Pattern references unknown token {exc!r}."
        ) from exc

    validate_reference_format(reference, scheme)
    return reference


def resolve_scheme(
    module: str,
    record_type: str | None = None,
    scheme_code: str | None = None,
    require_active: bool = True,
):
    """
    Resolve the applicable scheme for a module and record type.

    Resolution order:
      1. Explicit scheme by code, when supplied.
      2. Record-type default for the module.
      3. Module default.
      4. Organizational fallback scheme.

    Raises ``MissingNumberingContextError`` when nothing matches, or
    ``InactiveNumberingSchemeError`` when the resolved scheme is unusable and
    ``require_active`` is set.
    """
    from .models import ReferenceNumberScheme

    scheme: ReferenceNumberScheme | None = None
    if scheme_code:
        try:
            scheme = ReferenceNumberScheme.objects.get(code=scheme_code)
        except ReferenceNumberScheme.DoesNotExist as exc:
            raise MissingNumberingContextError(
                f"No reference scheme with code {scheme_code!r} exists."
            ) from exc
    else:
        queryset = ReferenceNumberScheme.objects.filter(module=module)
        scheme = queryset.filter(
            record_type=record_type or "", is_default_for_record_type=True
        ).first()
        if scheme is None:
            scheme = queryset.filter(is_default_for_module=True).first()
        if scheme is None:
            scheme = ReferenceNumberScheme.objects.filter(is_fallback=True).first()
        if scheme is None:
            raise MissingNumberingContextError(
                f"No reference number scheme is configured for module "
                f"{module!r} and record type {record_type!r}."
            )

    if require_active and not scheme.is_usable:
        raise InactiveNumberingSchemeError(
            f"Reference scheme {scheme.code!r} is not active and cannot "
            f"issue numbers."
        )
    return scheme
