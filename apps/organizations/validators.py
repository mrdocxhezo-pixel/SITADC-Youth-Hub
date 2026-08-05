"""
Reusable validation helpers for the organizational structure module.

These validators are shared by forms, services, model ``clean()`` methods and
management commands so organizational invariants are enforced consistently.
"""

from __future__ import annotations

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import AppointmentStatus, UnitStatus


def coerce_date(value: date | str | None) -> date | None:
    """Normalize a date-like value into a ``date`` object.

    Services and forms may hand validators either ``date`` instances or ISO
    ``YYYY-MM-DD`` strings; comparisons against ``date.today()`` and later
    ``isoformat()`` calls require a real ``date``.
    """
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


def validate_reporting_dates(effective_from: date, effective_to: date | None) -> None:
    """Raise if a reporting relationship date range is invalid."""
    if effective_to and effective_from and effective_to < effective_from:
        raise ValidationError(
            _("The effective-to date must be on or after the effective-from date."),
            code="invalid_reporting_dates",
        )


def validate_reporting_cycle(position, supervisor, exclude_pk=None) -> None:
    """
    Raise if making ``position`` report to ``supervisor`` would create a cycle.

    A cycle exists when the supervisor already reports (directly or
    transitively) to the position.  The optional ``exclude_pk`` ignores the
    relationship currently being edited.
    """
    current = supervisor
    seen: set = set()
    while current is not None and current.pk not in seen:
        if current.pk == position.pk:
            raise ValidationError(
                _(
                    "This reporting relationship would create a circular reporting "
                    "structure."
                ),
                code="circular_reporting",
            )
        seen.add(current.pk)
        current = current.primary_supervisor


def validate_unit_status_allows_assignments(unit) -> None:
    """Raise if an archived or inactive unit cannot receive new assignments."""
    if unit.status in (UnitStatus.ARCHIVED, UnitStatus.INACTIVE):
        raise ValidationError(
            _("The unit %(unit)s is %(status)s and cannot receive new assignments.")
            % {"unit": unit.name, "status": unit.get_status_display().lower()},
            code="unit_not_active",
        )


def validate_position_usable(position) -> None:
    """Raise if the position cannot currently hold an appointment."""
    from .constants import PositionStatus

    if position.status != PositionStatus.ACTIVE:
        raise ValidationError(
            _("The position %(position)s is not active.")
            % {"position": position.title},
            code="position_not_active",
        )


def validate_assignment_unique(position, person, exclude_pk=None) -> None:
    """
    Raise if the position already has an active occupant or the person already
    holds an active appointment elsewhere.
    """
    from .models import PositionAssignment

    position_qs = PositionAssignment.objects.filter(
        position=position, status=AppointmentStatus.ACTIVE
    )
    person_qs = PositionAssignment.objects.filter(
        person=person, status=AppointmentStatus.ACTIVE
    )
    if exclude_pk is not None:
        position_qs = position_qs.exclude(pk=exclude_pk)
        person_qs = person_qs.exclude(pk=exclude_pk)
    if position_qs.exists():
        raise ValidationError(
            _("This position already has an active appointment."),
            code="position_already_occupied",
        )
    if person_qs.exists():
        raise ValidationError(
            _("This person already holds an active appointment."),
            code="person_already_assigned",
        )


def validate_acting_dates(effective_from: date | str, end_date: date | str) -> None:
    """Raise if an acting appointment date range is invalid."""
    effective_from_date = coerce_date(effective_from)
    end_date_date = coerce_date(end_date)
    if effective_from_date is None or end_date_date is None:
        raise ValidationError(
            _("Acting appointment dates are required."),
            code="acting_dates_required",
        )
    if end_date_date <= effective_from_date:
        raise ValidationError(
            _("The end date must be after the effective start date."),
            code="invalid_acting_dates",
        )


def validate_no_overlapping_acting(position, exclude_pk=None) -> None:
    """Raise if the position already has an active acting appointment."""
    from .constants import ActingAppointmentStatus
    from .models import ActingAppointment

    qs = ActingAppointment.objects.filter(
        position=position, status=ActingAppointmentStatus.ACTIVE
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    if qs.exists():
        raise ValidationError(
            _("This position already has an active acting appointment."),
            code="overlapping_acting_appointment",
        )


def validate_vacancy_consistency(position, organizational_unit=None) -> None:
    """Raise if a vacancy record would be inconsistent with the position."""
    if position.is_vacant is False:
        raise ValidationError(
            _("A vacancy cannot be opened for an occupied position."),
            code="vacancy_for_occupied_position",
        )
    if organizational_unit is not None and position.organizational_unit_id != (
        organizational_unit.pk
        if hasattr(organizational_unit, "pk")
        else organizational_unit
    ):
        raise ValidationError(
            _("The vacancy organizational unit must match the position's unit."),
            code="vacancy_unit_mismatch",
        )


def validate_transfer_dates(effective_date: date | str) -> None:
    """Raise if a transfer effective date is in the past cannot be processed."""
    effective_date_value = coerce_date(effective_date)
    if effective_date_value is None:
        raise ValidationError(
            _("The transfer effective date is required."),
            code="transfer_date_required",
        )
    if effective_date_value < date.today():
        raise ValidationError(
            _("The transfer effective date cannot be in the past."),
            code="invalid_transfer_date",
        )


def validate_unit_hierarchy(parent, child) -> None:
    """Raise if a parent-child unit pairing is structurally invalid."""
    if parent is None or child is None:
        return
    if parent.pk == child.pk:
        raise ValidationError(_("A unit cannot be its own parent."), code="self_parent")
    if (
        child.parent_id
        and child.parent_id == parent.pk
        and child.level_id
        and parent.level_id
        and parent.level_id != child.level_id
    ):
        raise ValidationError(
            _("A child unit must inherit its parent's organizational level."),
            code="level_mismatch",
        )
