"""Validation helpers for the Notifications & Announcements module."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import (
    ALLOWED_TEMPLATE_VARIABLES,
    DEFAULT_RETRY_BACKOFF_MINUTES,
    MAX_DELIVERY_RETRIES,
    DeliveryChannel,
    EscalationLevel,
    QuietHoursPolicy,
    ReminderFrequency,
)

_TEMPLATE_VARIABLE_RE = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"

TIME_PATTERN = r"^\d{2}:\d{2}$"


def validate_quiet_hours(start: str, end: str) -> None:
    """Validate quiet hours window format and ordering."""
    import re

    for label, value in (("start", start), ("end", end)):
        if not value:
            continue
        if not re.match(TIME_PATTERN, value):
            raise ValidationError(
                _("%(label)s must be in HH:MM (24-hour) format.") % {"label": label}
            )
    if start and end and start == end:
        raise ValidationError(_("Quiet hours start and end must differ."))


def validate_template_variables(
    subject_template: str = "",
    title_template: str = "",
    message_template: str = "",
    short_message_template: str = "",
) -> None:
    """Raise if any template references a variable outside the allowlist."""
    import re

    for label, text in (
        ("subject", subject_template),
        ("title", title_template),
        ("message", message_template),
        ("short message", short_message_template),
    ):
        if not text:
            continue
        matches = re.findall(_TEMPLATE_VARIABLE_RE, text)
        disallowed = [m for m in matches if m not in ALLOWED_TEMPLATE_VARIABLES]
        if disallowed:
            raise ValidationError(
                _("%(label)s template uses disallowed variables: %(vars)s")
                % {"label": label, "vars": ", ".join(sorted(set(disallowed)))}
            )


def validate_reminder_offsets(offsets: list) -> None:
    """Validate reminder offsets are a list of integers (hours)."""
    if not offsets:
        return
    if not isinstance(offsets, list):
        raise ValidationError(_("Reminder offsets must be a list of hours."))
    for offset in offsets:
        if isinstance(offset, bool) or not isinstance(offset, int):
            raise ValidationError(
                _("Reminder offsets must contain integers only (hours).")
            )


def validate_channels(channels: list) -> None:
    """Validate a channel list only contains known channels."""
    if not channels:
        return
    if not isinstance(channels, list):
        raise ValidationError(_("Channels must be a list."))
    for channel in channels:
        if channel not in DeliveryChannel.values:
            raise ValidationError(
                _("Unknown delivery channel: %(channel)s") % {"channel": channel}
            )


def validate_delivery_retry_policy(
    retry_count: int, max_retries: int = MAX_DELIVERY_RETRIES
) -> None:
    """Validate a retry count against the maximum allowed."""
    if retry_count > max_retries:
        raise ValidationError(
            _("Retry count cannot exceed the maximum of %(max)s.")
            % {"max": max_retries}
        )


def next_retry_backoff_minutes(retry_count: int) -> int:
    """Return the backoff minutes for the next retry attempt."""
    clamped = min(max(retry_count, 0), len(DEFAULT_RETRY_BACKOFF_MINUTES) - 1)
    return DEFAULT_RETRY_BACKOFF_MINUTES[clamped]


def validate_quiet_hours_policy(policy: str) -> None:
    """Validate the quiet hours policy value."""
    if policy not in QuietHoursPolicy.values:
        raise ValidationError(_("Unknown quiet hours policy."))


def validate_reminder_frequency(frequency: str) -> None:
    """Validate the reminder frequency value."""
    if frequency not in ReminderFrequency.values:
        raise ValidationError(_("Unknown reminder frequency."))


def validate_escalation_level(level: str) -> None:
    """Validate the escalation level value."""
    if level not in EscalationLevel.values:
        raise ValidationError(_("Unknown escalation level."))
