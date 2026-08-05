"""
Validation logic for the volunteer management module.
"""

from __future__ import annotations

from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

DOCUMENT_CONTENT_TYPES = {
    "doc": {"application/msword", "application/octet-stream"},
    "docx": {
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "pdf": {"application/pdf"},
}
IMAGE_CONTENT_TYPES = {
    "jpeg": {"image/jpeg"},
    "jpg": {"image/jpeg"},
    "png": {"image/png"},
}


def validate_date_range(start_date, end_date) -> None:
    """Validate that start date is before or equal to end date."""
    if start_date and end_date and start_date > end_date:
        raise ValidationError(
            {"end_date": _("End date cannot be earlier than start date.")}
        )


def validate_file_extension_and_size(
    value,
    allowed_extensions=None,
    max_mb=10,
    allowed_content_types=None,
) -> None:
    """Validate an upload's extension, size, MIME type, and basic signature."""
    if not value:
        return

    ext = Path(value.name).suffix.lower().lstrip(".")
    if allowed_extensions and ext not in allowed_extensions:
        raise ValidationError(
            _("File extension '.%(ext)s' is not allowed. Allowed: %(allowed)s")
            % {"ext": ext, "allowed": ", ".join(allowed_extensions)}
        )

    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(
            _("File size must not exceed %(max_mb)d MB.") % {"max_mb": max_mb}
        )

    content_type = getattr(value, "content_type", "")
    expected_content_types = (allowed_content_types or {}).get(ext, set())
    if (
        content_type
        and expected_content_types
        and content_type not in expected_content_types
    ):
        raise ValidationError(
            _("The uploaded file content does not match its extension."),
            code="invalid_file_content_type",
        )

    position = value.tell() if hasattr(value, "tell") else None
    header = value.read(8) if hasattr(value, "read") else b""
    if position is not None and hasattr(value, "seek"):
        value.seek(position)

    valid_signature = {
        "pdf": header.startswith(b"%PDF-"),
        "doc": header.startswith(b"\xd0\xcf\x11\xe0"),
        "docx": header.startswith(b"PK\x03\x04"),
        "jpg": header.startswith(b"\xff\xd8\xff"),
        "jpeg": header.startswith(b"\xff\xd8\xff"),
        "png": header.startswith(b"\x89PNG\r\n\x1a\n"),
    }.get(ext, True)
    if header and not valid_signature:
        raise ValidationError(
            _("The uploaded file has an invalid file signature."),
            code="invalid_file_signature",
        )


def validate_volunteer_document(value) -> None:
    validate_file_extension_and_size(
        value,
        allowed_extensions=DOCUMENT_CONTENT_TYPES,
        allowed_content_types=DOCUMENT_CONTENT_TYPES,
        max_mb=10,
    )


def validate_volunteer_image(value) -> None:
    validate_file_extension_and_size(
        value,
        allowed_extensions=IMAGE_CONTENT_TYPES,
        allowed_content_types=IMAGE_CONTENT_TYPES,
        max_mb=5,
    )


def validate_rating(rating: int, min_val: int = 1, max_val: int = 5) -> None:
    """Validate performance rating range."""
    if rating < min_val or rating > max_val:
        raise ValidationError(
            _("Rating must be between %(min_val)d and %(max_val)d.")
            % {"min_val": min_val, "max_val": max_val}
        )
