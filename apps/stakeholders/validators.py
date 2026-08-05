"""Local validation for stakeholder dates, scores, documents, and images."""

from __future__ import annotations

from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

DOCUMENT_CONTENT_TYPES = {
    "csv": {"text/csv", "text/plain", "application/vnd.ms-excel"},
    "doc": {"application/msword", "application/octet-stream"},
    "docx": {
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    "pdf": {"application/pdf"},
    "ppt": {"application/vnd.ms-powerpoint", "application/octet-stream"},
    "pptx": {
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
    "txt": {"text/plain"},
    "xls": {"application/vnd.ms-excel", "application/octet-stream"},
    "xlsx": {
        "application/octet-stream",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
}
IMAGE_CONTENT_TYPES = {
    "jpeg": {"image/jpeg"},
    "jpg": {"image/jpeg"},
    "png": {"image/png"},
    "webp": {"image/webp"},
}


def validate_date_range(start_date, end_date, *, end_field: str = "end_date") -> None:
    if start_date and end_date and start_date > end_date:
        raise ValidationError({end_field: _("End date cannot precede start date.")})


def validate_percentage(value) -> None:
    if value is not None and not 0 <= value <= 100:
        raise ValidationError(_("Value must be between 0 and 100."))


def validate_positive_weight(value) -> None:
    if value is not None and value <= 0:
        raise ValidationError(_("Weight must be greater than zero."))


def _read_header(value, size: int = 12) -> bytes:
    if not hasattr(value, "read"):
        return b""
    position = value.tell() if hasattr(value, "tell") else None
    header = value.read(size)
    if position is not None and hasattr(value, "seek"):
        value.seek(position)
    return header


def validate_upload(
    value,
    *,
    allowed_content_types: dict[str, set[str]],
    max_mb: int,
) -> None:
    """Validate filename, extension, size, declared MIME type, and signature."""
    if not value:
        return
    name = str(getattr(value, "name", ""))
    if (
        not name
        or "\x00" in name
        or Path(name).name != name.replace("\\", "/").split("/")[-1]
    ):
        raise ValidationError(_("The uploaded filename is invalid."))
    extension = Path(name).suffix.lower().lstrip(".")
    if extension not in allowed_content_types:
        raise ValidationError(
            _("File extension '.%(extension)s' is not allowed.")
            % {"extension": extension or "(none)"}
        )
    if getattr(value, "size", 0) > max_mb * 1024 * 1024:
        raise ValidationError(
            _("File size must not exceed %(max_mb)d MB.") % {"max_mb": max_mb}
        )
    content_type = str(getattr(value, "content_type", "") or "").lower()
    if content_type and content_type not in allowed_content_types[extension]:
        raise ValidationError(
            _("The uploaded file content type does not match its extension."),
            code="invalid_content_type",
        )
    header = _read_header(value)
    signatures = {
        "pdf": header.startswith(b"%PDF-"),
        "doc": header.startswith(b"\xd0\xcf\x11\xe0"),
        "xls": header.startswith(b"\xd0\xcf\x11\xe0"),
        "ppt": header.startswith(b"\xd0\xcf\x11\xe0"),
        "docx": header.startswith(b"PK\x03\x04"),
        "xlsx": header.startswith(b"PK\x03\x04"),
        "pptx": header.startswith(b"PK\x03\x04"),
        "jpg": header.startswith(b"\xff\xd8\xff"),
        "jpeg": header.startswith(b"\xff\xd8\xff"),
        "png": header.startswith(b"\x89PNG\r\n\x1a\n"),
        "webp": header.startswith(b"RIFF") and header[8:12] == b"WEBP",
    }
    if header and extension in signatures and not signatures[extension]:
        raise ValidationError(
            _("The uploaded file has an invalid signature."),
            code="invalid_file_signature",
        )


def validate_stakeholder_document(value) -> None:
    validate_upload(
        value,
        allowed_content_types=DOCUMENT_CONTENT_TYPES,
        max_mb=20,
    )


def validate_stakeholder_image(value) -> None:
    validate_upload(value, allowed_content_types=IMAGE_CONTENT_TYPES, max_mb=5)
