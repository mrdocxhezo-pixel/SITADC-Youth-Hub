"""File validators for the Document Management module."""
from __future__ import annotations

import hashlib
import os

from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

try:
    import magic

    HAS_MAGIC = True
except (ImportError, OSError):
    HAS_MAGIC = False

from .constants import (
    ALLOWED_ARCHIVE_EXTENSIONS,
    ALLOWED_DOCUMENT_EXTENSIONS,
    ALLOWED_MIME_TYPES,
    BLOCKED_EXTENSIONS,
    FILE_SIZE_LIMITS,
)
from .exceptions import FileSizeExceededError, UnsafeFileError, UnsupportedFileTypeError


def validate_file_extension(filename: str) -> None:
    """Validate that the file extension is allowed."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext in BLOCKED_EXTENSIONS:
        raise UnsafeFileError(
            _("File type '{ext}' is blocked for security reasons.").format(ext=ext)
        )
    all_allowed = ALLOWED_DOCUMENT_EXTENSIONS | ALLOWED_ARCHIVE_EXTENSIONS
    if ext not in all_allowed:
        raise UnsupportedFileTypeError(
            _("File type '{ext}' is not allowed.").format(ext=ext)
        )


def validate_file_size(file_obj, document_type=None) -> None:
    """Validate that the file size is within limits."""
    file_obj.seek(0, os.SEEK_END)
    size = file_obj.tell()
    file_obj.seek(0)

    ext = os.path.splitext(file_obj.name)[1].lower().lstrip(".")
    max_size = FILE_SIZE_LIMITS.get(ext, 20 * 1024 * 1024)

    if document_type and hasattr(document_type, "max_file_size") and document_type.max_file_size:
        max_size = document_type.max_file_size

    if size > max_size:
        max_mb = max_size / (1024 * 1024)
        raise FileSizeExceededError(
            _("File size exceeds the maximum allowed size of {max_mb:.1f} MB.").format(
                max_mb=max_mb
            )
        )


def validate_mime_type(file_obj) -> str:
    """Validate the MIME type using file signature detection when available."""
    if not HAS_MAGIC:
        return _guess_mime_from_extension(file_obj.name)

    file_obj.seek(0)
    header = file_obj.read(2048)
    file_obj.seek(0)

    try:
        detected = magic.from_buffer(header, mime=True)
    except Exception:
        detected = _guess_mime_from_extension(file_obj.name)

    if detected and detected not in ALLOWED_MIME_TYPES:
        ext = os.path.splitext(file_obj.name)[1].lower().lstrip(".")
        ext_to_mime = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "txt": "text/plain",
            "csv": "text/csv",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "webp": "image/webp",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "mp4": "video/mp4",
            "mov": "video/quicktime",
            "zip": "application/zip",
        }
        expected = ext_to_mime.get(ext)
        if expected and detected != expected:
            raise UnsafeFileError(
                _("File content does not match its extension. Detected: {detected}").format(
                    detected=detected
                )
            )

    return detected or ""


def _guess_mime_from_extension(filename: str) -> str:
    """Fallback MIME type guess from file extension."""
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    ext_to_mime = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "txt": "text/plain",
        "csv": "text/csv",
        "odt": "application/vnd.oasis.opendocument.text",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "zip": "application/zip",
    }
    return ext_to_mime.get(ext, "application/octet-stream")


def generate_checksum(file_obj) -> str:
    """Generate SHA-256 checksum for a file."""
    hasher = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(8192), b""):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()


def safe_filename(filename: str) -> str:
    """Sanitize a filename for safe storage."""
    name, ext = os.path.splitext(filename)
    safe_name = slugify(name)
    if not safe_name:
        safe_name = "document"
    return f"{safe_name}{ext.lower()}"


def detect_duplicate(file_obj, checksum: str, filename: str, file_size: int) -> dict | None:
    """Check for potential duplicate files based on checksum."""
    from .models import DocumentVersion

    existing = DocumentVersion.objects.filter(checksum=checksum).first()
    if existing:
        return {
            "existing_document": existing.document,
            "existing_version": existing,
            "match_type": "checksum",
        }
    return None
