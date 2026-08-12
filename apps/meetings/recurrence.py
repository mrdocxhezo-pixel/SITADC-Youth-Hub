"""Bounded, deterministic event recurrence engine.

Occurrences are computed on demand for a date range.  The engine never
materializes unbounded series: every expansion is clamped to a hard bound and
exceptions are handled by the service layer as explicit occurrence records.
"""

from __future__ import annotations

import calendar as _calendar
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from django.utils import timezone

from .constants import RecurrenceFrequency
from .validators import validate_recurrence_rule

# Hard bounds that protect the database from unbounded expansion.
MAX_OCCURRENCES_PER_SERIES = 500
MAX_EXPANSION_RANGE_DAYS = 1095  # ~3 years


def _as_date(value) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _add_months(d: date, months: int) -> date:
    """Add months clamping the day to the target month's length."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    last_day = _calendar.monthrange(year, month)[1]
    return date(year, month, min(d.day, last_day))


def _replace_day(d: date, day: int) -> date:
    last_day = _calendar.monthrange(d.year, d.month)[1]
    return date(d.year, d.month, min(day, last_day))


def _iter_weekday_dates(
    start: date, weekdays: list[int], interval: int, end: date
) -> Iterable[date]:
    """Yield weekly weekday dates at ``interval`` week gaps."""
    week_start = start - timedelta(days=start.weekday())
    week_index = 0
    while True:
        base = week_start + timedelta(weeks=interval * week_index)
        if base > end:
            return
        for day in sorted(weekdays):
            candidate = base + timedelta(days=day)
            if candidate >= start and candidate <= end:
                yield candidate
        week_index += 1


def expand_occurrences(
    *,
    start: datetime,
    end: datetime,
    rule: dict,
    range_start: datetime,
    range_end: datetime,
    timezone_name: str | None = None,
) -> list[dict]:
    """Return occurrence dicts for ``rule`` within ``[range_start, range_end)``.

    Each dict contains ``start``, ``end`` and ``sequence``.  The rule's start
    anchor is ``start``/``end`` (the first occurrence).
    """
    validate_recurrence_rule(rule)
    tz = (
        timezone.get_current_timezone()
        if not timezone_name
        else timezone.pytz.timezone(timezone_name)
    )

    anchor = start if timezone.is_aware(start) else timezone.make_aware(start, tz)
    anchor = anchor.astimezone(tz)
    duration = (end - start) if end else timedelta(0)
    if timezone.is_naive(range_start):
        range_start = timezone.make_aware(range_start, tz)
    if timezone.is_naive(range_end):
        range_end = timezone.make_aware(range_end, tz)
    range_start = range_start.astimezone(tz)
    range_end = range_end.astimezone(tz)

    anchor_date = anchor.date()
    frequency = rule["frequency"]
    interval = int(rule.get("interval", 1))
    weekdays = rule.get("weekdays")
    count = rule.get("count")
    until = _as_date(rule["until"]) if rule.get("until") else None

    if until and until < anchor_date:
        return []
    horizon = min(
        range_end.date(),
        until if until else anchor_date + timedelta(days=MAX_EXPANSION_RANGE_DAYS),
    )

    occurrences: list[dict] = []
    sequence = 0

    if frequency == RecurrenceFrequency.WEEKLY and weekdays:
        for candidate_date in _iter_weekday_dates(
            anchor_date, weekdays, interval, horizon
        ):
            if count is not None and sequence >= count:
                break
            candidate = timezone.make_aware(
                datetime.combine(candidate_date, anchor.timetz()), tz
            )
            if candidate < range_start or candidate >= range_end:
                continue
            if candidate < anchor:
                continue
            occurrences.append(
                {
                    "start": candidate,
                    "end": candidate + duration,
                    "sequence": sequence,
                }
            )
            sequence += 1
        return occurrences

    if frequency == RecurrenceFrequency.DAILY:
        current = anchor_date
        step = timedelta(days=interval)
        while current <= horizon:
            if count is not None and sequence >= count:
                break
            candidate = timezone.make_aware(
                datetime.combine(current, anchor.timetz()), tz
            )
            if (
                candidate >= range_start
                and candidate < range_end
                and candidate >= anchor
            ):
                occurrences.append(
                    {
                        "start": candidate,
                        "end": candidate + duration,
                        "sequence": sequence,
                    }
                )
            sequence += 1
            current += step
        return occurrences

    if frequency in (
        RecurrenceFrequency.MONTHLY,
        RecurrenceFrequency.QUARTERLY,
        RecurrenceFrequency.ANNUALLY,
    ):
        step_months = interval
        if frequency == RecurrenceFrequency.QUARTERLY:
            step_months = interval * 3
        if frequency == RecurrenceFrequency.ANNUALLY:
            step_months = interval * 12
        month_of_year = rule.get("month_of_year")
        day_of_month = rule.get("day_of_month")

        current = anchor_date
        while current <= horizon:
            if count is not None and sequence >= count:
                break
            if month_of_year and current.month != month_of_year:
                diff = (month_of_year - current.month) % 12
                current = _add_months(current, diff)
                continue
            candidate_date = current
            if day_of_month:
                candidate_date = _replace_day(candidate_date, day_of_month)
            if candidate_date < anchor_date:
                current = _add_months(current, step_months)
                continue
            candidate = timezone.make_aware(
                datetime.combine(candidate_date, anchor.timetz()), tz
            )
            if candidate >= range_start and candidate < range_end:
                occurrences.append(
                    {
                        "start": candidate,
                        "end": candidate + duration,
                        "sequence": sequence,
                    }
                )
            sequence += 1
            current = _add_months(current, step_months)
        return occurrences

    return occurrences
