"""Validators for beneficiary profile and document data."""

from __future__ import annotations

import re
from datetime import date

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

from .constants import MINOR_AGE

VALID_DOCUMENT_EXTENSIONS = ("pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx")
VALID_IMAGE_EXTENSIONS = ("png", "jpg", "jpeg")

_PHONE_PATTERN = re.compile(r"^\+?[0-9]{9,15}$")
_NATIONAL_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-/]{5,40}$")


def validate_phone_number(value: str) -> None:
    if value and not _PHONE_PATTERN.fullmatch(value.strip()):
        raise ValidationError(_("Enter a valid phone number (digits, optional +)."))


def validate_national_identifier(value: str) -> None:
    if value and not _NATIONAL_ID_PATTERN.fullmatch(value.strip()):
        raise ValidationError(
            _("Enter a valid national identifier (letters, digits, - or /).")
        )


def validate_date_not_future(value: date) -> None:
    if value and value > date.today():
        raise ValidationError(_("Date cannot be in the future."))


def validate_date_of_birth(value: date) -> None:
    validate_date_not_future(value)
    today = date.today()
    age = (
        today.year - value.year - ((today.month, today.day) < (value.month, value.day))
    )
    if age > 120:
        raise ValidationError(_("Date of birth implies an implausible age."))


def validate_date_range(
    start: date | None, end: date | None, *, end_field: str = "end_date"
) -> None:
    if start and end and end < start:
        raise ValidationError(
            {end_field: _("The end date cannot precede the start date.")}
        )


def validate_percentage(value) -> None:
    if value < 0 or value > 100:
        raise ValidationError(_("Percentage must be between 0 and 100."))


validate_beneficiary_document = FileExtensionValidator(
    allowed_extensions=VALID_DOCUMENT_EXTENSIONS
)
validate_beneficiary_image = FileExtensionValidator(
    allowed_extensions=VALID_IMAGE_EXTENSIONS
)


def is_minor(date_of_birth: date | None, today: date | None = None) -> bool:
    """Return whether the person is below the configured minor age."""
    if not date_of_birth:
        return False
    reference = today or date.today()
    age = (
        reference.year
        - date_of_birth.year
        - ((reference.month, reference.day) < (date_of_birth.month, date_of_birth.day))
    )
    return age < MINOR_AGE
