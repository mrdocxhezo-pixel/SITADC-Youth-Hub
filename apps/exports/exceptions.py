"""Domain exceptions for the Export Engine (Phase 27).

Controlled exceptions never leak stack traces or filesystem paths to the
user; views translate them into friendly, user-facing error messages.
"""

from __future__ import annotations

from apps.core.exceptions import CoreException


class ExportError(CoreException):
    """Base class for all export engine errors."""


class ExportPermissionDenied(ExportError):
    """The actor is not authorized to perform the export operation."""


class UnsupportedExportFormat(ExportError):
    """The requested format is not supported for the selected source."""


class ExportValidationError(ExportError):
    """The export request payload is invalid (filters, columns, sources)."""


class ExportTooLargeError(ExportError):
    """The export exceeds configured row / file / column limits."""


class ExportGenerationError(ExportError):
    """The output file could not be generated."""


class ExportNotFoundError(ExportError):
    """The export request does not exist."""


class ExportExpiredError(ExportError):
    """The generated file has expired and is no longer downloadable."""


class ExportDownloadDenied(ExportError):
    """The actor is not authorized to download this export."""


class ExportTemplateError(ExportError):
    """An export template is misconfigured or invalid."""


class ExportProviderError(ExportError):
    """A source provider failed to resolve or generate its dataset."""


class ExportConfigurationError(ExportError):
    """The export engine configuration is invalid."""
