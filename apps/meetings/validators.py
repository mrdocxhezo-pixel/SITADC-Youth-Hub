"""Validation helpers for the Calendar & Meetings module."""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import RecurrenceFrequency
from .exceptions import InvalidTransitionError


def validate_time_range(start, end) -> None:
    """Raise ValidationError unless ``end`` is strictly after ``start``."""
    if start and end and end <= start:
        raise ValidationError(_("End time must be after the start time."))


def validate_recurrence_rule(rule: dict | None) -> None:
    """Validate a recurrence rule dict.

    Accepted keys: ``frequency``, ``interval``, ``weekdays`` (list 0-6,
    Monday=0), ``day_of_month``, ``month_of_year``, ``count`` or ``until``.
    Raises ValidationError for malformed rules.
    """
    if not rule:
        return
    if not isinstance(rule, dict):
        raise ValidationError(_("Recurrence rule must be a mapping."))

    frequency = rule.get("frequency")
    if frequency not in RecurrenceFrequency.values:
        raise ValidationError(_("Unsupported recurrence frequency."))

    interval = rule.get("interval", 1)
    if isinstance(interval, bool) or not isinstance(interval, int) or interval < 1:
        raise ValidationError(_("Recurrence interval must be a positive integer."))

    count = rule.get("count")
    if count is not None and (
        isinstance(count, bool) or not isinstance(count, int) or count < 1
    ):
        raise ValidationError(_("Recurrence count must be a positive integer."))

    until = rule.get("until")
    if until is not None and not isinstance(until, str):
        raise ValidationError(_("Recurrence end date must be an ISO date string."))

    weekdays = rule.get("weekdays")
    if weekdays is not None:
        if not isinstance(weekdays, list) or not weekdays:
            raise ValidationError(_("Weekly recurrence requires weekdays."))
        for day in weekdays:
            if not isinstance(day, int) or not 0 <= day <= 6:
                raise ValidationError(_("Weekdays must be integers between 0 and 6."))

    day_of_month = rule.get("day_of_month")
    if day_of_month is not None and (
        isinstance(day_of_month, bool)
        or not isinstance(day_of_month, int)
        or not 1 <= day_of_month <= 31
    ):
        raise ValidationError(_("Day of month must be an integer between 1 and 31."))


def require_transition(
    current: str, target: str, allowed: set[str], label: str
) -> None:
    """Raise InvalidTransitionError unless the transition is allowed."""
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot move {label} from {current!r} to {target!r}."
        )


def default_reminder_lead() -> timedelta:
    """Default reminder lead time before an event."""
    return timedelta(minutes=30)


def now():
    """Timezone-aware now (kept in one place)."""
    return timezone.now()
