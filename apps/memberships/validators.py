"""
Validation logic for the membership management module.
"""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .constants import ApplicationStatus, MembershipStatus


def validate_date_range(start_date, end_date) -> None:
    """Validate that start date is before or equal to end date."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            {"end_date": _("End date cannot be earlier than start date.")}
        )


def validate_effective_dates(effective_date, effective_to=None) -> None:
    """Validate effective date windows."""
    if effective_to and effective_date and effective_to < effective_date:
        raise ValidationError(
            _("Effective-to date cannot be earlier than effective-from date.")
        )


def validate_future_date(value) -> None:
    """Ensure a date is not in the past."""
    if value and value < date.today():
        raise ValidationError(_("Date cannot be in the past."))


def validate_membership_status_code(code: str) -> None:
    """Validate a membership status code is a known lifecycle status."""
    if code not in MembershipStatus.values:
        raise ValidationError(
            _("Unknown membership status code: %(code)s") % {"code": code}
        )


def validate_application_transition(current: str, target: str) -> None:
    """Validate allowed membership application status transitions."""
    allowed: dict[ApplicationStatus, set[ApplicationStatus]] = {
        ApplicationStatus.DRAFT: {
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.SUBMITTED: {
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.RETURNED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.UNDER_REVIEW: {
            ApplicationStatus.APPROVED,
            ApplicationStatus.RETURNED,
            ApplicationStatus.REJECTED,
        },
        ApplicationStatus.RETURNED: {
            ApplicationStatus.DRAFT,
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.WITHDRAWN,
        },
        ApplicationStatus.APPROVED: set(),
        ApplicationStatus.REJECTED: set(),
        ApplicationStatus.WITHDRAWN: set(),
    }
    try:
        current_status: ApplicationStatus | None = ApplicationStatus(current)
        target_status: ApplicationStatus | None = ApplicationStatus(target)
    except ValueError:
        current_status = None
        target_status = None
    if (
        current_status is None
        or target_status is None
        or target_status not in allowed.get(current_status, set())
    ):
        raise ValidationError(
            _("Invalid application status transition: %(current)s → %(target)s")
            % {"current": current, "target": target}
        )
