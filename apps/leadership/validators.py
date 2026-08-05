"""
Reusable validation helpers for the leadership management module.

These validators are shared by model ``clean()`` methods, services, forms and
management commands so leadership invariants are enforced consistently.
"""

from __future__ import annotations

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .constants import AppointmentStatus, LeadershipStatus


def coerce_date(value: date | str | None) -> date | None:
    """Normalize a date-like value into a ``date`` object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValidationError(
            _("Invalid date value: %(value)s.") % {"value": value},
            code="invalid_date",
        ) from exc


def validate_date_order(
    start: date | None, end: date | None, field_label: str = ""
) -> None:
    """Raise unless the end date is on or after the start date."""
    start_date = coerce_date(start)
    end_date = coerce_date(end)
    if start_date and end_date and end_date < start_date:
        raise ValidationError(
            _("%(label)sThe end date must be on or after the start date.")
            % {"label": f"{field_label}: " if field_label else ""},
            code="invalid_date_range",
        )


def validate_appointment_dates(
    effective_date: date | str | None,
    term_start: date | str | None,
    term_end: date | str | None,
) -> None:
    """Raise unless appointment dates are internally consistent."""
    effective = coerce_date(effective_date)
    start = coerce_date(term_start)
    end = coerce_date(term_end)
    if start and end and end < start:
        raise ValidationError(
            _("The term end date must be on or after the term start date."),
            code="invalid_term_dates",
        )
    if effective and start and start < effective:
        raise ValidationError(
            _("The term start date must be on or after the effective date."),
            code="term_starts_before_effective",
        )


def validate_profile_dates(
    appointment_date: date | str | None,
    term_expiry_date: date | str | None,
) -> None:
    """Raise unless a profile's appointment and term expiry are consistent."""
    appointment = coerce_date(appointment_date)
    expiry = coerce_date(term_expiry_date)
    if appointment and expiry and expiry < appointment:
        raise ValidationError(
            _("The term expiry date must be on or after the appointment date."),
            code="invalid_profile_term_dates",
        )


def validate_active_profile_has_appointment(profile) -> None:
    """Raise unless an active profile has a current appointment."""
    if (
        profile.status
        in (
            LeadershipStatus.ACTIVE,
            LeadershipStatus.ACTING,
            LeadershipStatus.PROBATION,
        )
        and not profile.appointments.filter(status=AppointmentStatus.ACTIVE).exists()
    ):
        raise ValidationError(
            _(
                "The profile status %(status)s requires at least one active "
                "leadership appointment."
            )
            % {"status": profile.get_status_display()},
            code="active_profile_without_appointment",
        )


def validate_no_overlapping_active_appointment(
    profile, position, exclude_pk=None
) -> None:
    """Raise if the leader already holds an active appointment to a position."""
    from .models import LeadershipAppointment

    queryset = LeadershipAppointment.objects.filter(
        profile=profile,
        position=position,
        status=AppointmentStatus.ACTIVE,
    )
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(
            _("This leader already has an active appointment to the position."),
            code="overlapping_active_appointment",
        )


def validate_appointment_transition(appointment, target_status: str) -> None:
    """Raise unless the requested status transition is permitted."""
    from .constants import VALID_APPOINTMENT_TRANSITIONS

    allowed = VALID_APPOINTMENT_TRANSITIONS.get(appointment.status, ())
    if target_status not in allowed:
        raise ValidationError(
            _(
                "Cannot transition an appointment from %(from_status)s to "
                "%(to_status)s."
            )
            % {
                "from_status": appointment.get_status_display(),
                "to_status": dict(AppointmentStatus.choices).get(
                    target_status, target_status
                ),
            },
            code="invalid_appointment_transition",
        )


def validate_supervisor_not_self(profile, supervisor) -> None:
    """Raise unless the supervisor is a different leader."""
    if (
        supervisor is not None
        and profile.pk is not None
        and profile.pk == supervisor.pk
    ):
        raise ValidationError(
            _("A leader cannot be their own supervisor."), code="self_supervision"
        )


def validate_leave_dates(start_date, end_date, minimum_days: int = 1) -> None:
    """Raise unless leave dates are valid and meet the minimum duration."""
    start = coerce_date(start_date)
    end = coerce_date(end_date)
    if start is None or end is None:
        raise ValidationError(
            _("Leave start and end dates are required."), code="leave_dates_required"
        )
    if end < start:
        raise ValidationError(
            _("The leave end date must be on or after the start date."),
            code="invalid_leave_dates",
        )
    duration = (end - start).days + 1
    if duration < minimum_days:
        raise ValidationError(
            _("Leave must last at least %(days)s day(s).") % {"days": minimum_days},
            code="leave_too_short",
        )


def validate_overlapping_leave(profile, start_date, end_date, exclude_pk=None) -> None:
    """Raise if the leader has overlapping approved leave."""
    from .constants import LeaveStatus
    from .models import LeadershipLeave

    start = coerce_date(start_date)
    end = coerce_date(end_date)
    if start is None or end is None:
        return
    queryset = LeadershipLeave.objects.filter(
        profile=profile,
        status__in=(LeaveStatus.PENDING, LeaveStatus.APPROVED),
        start_date__lte=end,
        end_date__gte=start,
    )
    if exclude_pk is not None:
        queryset = queryset.exclude(pk=exclude_pk)
    if queryset.exists():
        raise ValidationError(
            _("The leader already has leave overlapping this period."),
            code="overlapping_leave",
        )


def validate_scorecard_weights(weights: dict[str, float]) -> None:
    """Raise unless scorecard component weights sum to 100."""
    total = sum(float(value) for value in weights.values())
    if abs(total - 100.0) > 0.01:
        raise ValidationError(
            _("Scorecard weights must sum to 100 (current total: %(total)s).")
            % {"total": total},
            code="invalid_scorecard_weights",
        )


def validate_score_range(value) -> None:
    """Raise unless a score value lies within 0-100."""
    if value is None:
        return
    if not 0 <= float(value) <= 100:
        raise ValidationError(
            _("Scores must be between 0 and 100."), code="invalid_score_range"
        )


def validate_future_date(value, field_label: str) -> None:
    """Raise unless the date is today or in the future."""
    parsed = coerce_date(value)
    if parsed and parsed < timezone.localdate():
        raise ValidationError(
            _("%(label)s cannot be in the past.") % {"label": field_label},
            code="past_date_not_allowed",
        )
