"""Constants for the Export Engine (Phase 27).

Centralized definitions for export formats, lifecycle statuses, source
modules, confidentiality, page layout and configuration defaults.  All
renderers and providers consume these constants so behaviour stays
consistent across the platform.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ExportFormat(models.TextChoices):
    """Supported output formats of the Export Engine."""

    PDF = "PDF", _("PDF")
    DOCX = "DOCX", _("Word (DOCX)")
    XLSX = "XLSX", _("Excel (XLSX)")
    CSV = "CSV", _("CSV")
    PRINT_HTML = "PRINT_HTML", _("Print-ready HTML")


class ExportStatus(models.TextChoices):
    """Lifecycle status of an export request."""

    PENDING = "PENDING", _("Pending")
    QUEUED = "QUEUED", _("Queued")
    PROCESSING = "PROCESSING", _("Processing")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")
    EXPIRED = "EXPIRED", _("Expired")


class ExportSourceType(models.TextChoices):
    """Source modules that expose data through the Export Engine."""

    REPORT = "REPORT", _("Report")
    REGISTER = "REGISTER", _("Organizational Register")
    DIRECTORY = "DIRECTORY", _("People Directory")
    BENEFICIARY = "BENEFICIARY", _("Beneficiary")
    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    MEAL = "MEAL", _("MEAL")
    MEETING = "MEETING", _("Meeting")
    DOCUMENT = "DOCUMENT", _("Document Metadata")
    SEARCH = "SEARCH", _("Search Results")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality classification attached to an export.

    The classification is inherited from the source records; it determines
    watermarking, retention, download authorization and audit behaviour.
    """

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")


class ExportActivityAction(models.TextChoices):
    """Immutable activity events recorded for every export request."""

    REQUESTED = "REQUESTED", _("Export requested")
    GENERATED = "GENERATED", _("Export generated")
    SENSITIVE_GENERATED = "SENSITIVE_GENERATED", _("Sensitive export generated")
    BULK_GENERATED = "BULK_GENERATED", _("Bulk export generated")
    DOWNLOADED = "DOWNLOADED", _("Export downloaded")
    SENSITIVE_DOWNLOADED = "SENSITIVE_DOWNLOADED", _("Sensitive export downloaded")
    CANCELLED = "CANCELLED", _("Export cancelled")
    EXPIRED = "EXPIRED", _("Export expired")
    FAILED = "FAILED", _("Export failed")
    REGENERATED = "REGENERATED", _("Export regenerated")
    PREVIEWED = "PREVIEWED", _("Export previewed")


class PageSize(models.TextChoices):
    """Approved page sizes."""

    A4 = "A4", _("A4")
    LETTER = "LETTER", _("Letter")


class PageOrientation(models.TextChoices):
    """Page orientation for document exports."""

    PORTRAIT = "PORTRAIT", _("Portrait")
    LANDSCAPE = "LANDSCAPE", _("Landscape")


class ExportDirectoryKind(models.TextChoices):
    """People-directory kinds supported by the directory provider."""

    VOLUNTEER = "VOLUNTEER", _("Volunteer Directory")
    MEMBER = "MEMBER", _("Member Directory")
    LEADER = "LEADER", _("Leadership Directory")
    STAKEHOLDER = "STAKEHOLDER", _("Stakeholder Directory")


class ExportMealDataset(models.TextChoices):
    """MEAL datasets supported by the MEAL provider."""

    INDICATORS = "INDICATORS", _("Indicator Register")
    RESULTS = "RESULTS", _("Indicator Results")
    FRAMEWORKS = "FRAMEWORKS", _("Results Frameworks")


# ---------------------------------------------------------------------------
# Reference numbering
# ---------------------------------------------------------------------------

EXPORT_MODULE = "exports"
EXPORT_SCHEME_CODE = "export"
EXPORT_SCHEME_PREFIX = "EXP"
EXPORT_SCHEME_PATTERN = "{ORG}-{PREFIX}-{YEAR}-{SEQUENCE}"

# ---------------------------------------------------------------------------
# Organizational branding (canonical configuration)
# ---------------------------------------------------------------------------

ORGANIZATION_NAME = (
    "Sustainable Initiatives Through Transformative Actions for Development "
    "in Communities — SITADC Youth Organization"
)
ORGANIZATION_SHORT_NAME = "SITADC Youth Organization"
ORGANIZATION_SLOGAN = (
    "Sustainable Initiatives Through Transformative Actions for Development "
    "in Communities"
)
ORGANIZATION_DOMAIN = "sitadc.org"
ORGANIZATION_EMAIL = "info@sitadc.org"

LOGO_STATIC_PATH = "images/app_logo.png"

# ---------------------------------------------------------------------------
# Configuration defaults
# ---------------------------------------------------------------------------

DEFAULT_PAGE_SIZE = PageSize.A4
DEFAULT_ORIENTATION = PageOrientation.PORTRAIT
DEFAULT_SYNC_MAX_ROWS = 5000
DEFAULT_BULK_MAX_ROWS = 25000
DEFAULT_MAX_FILE_SIZE_MB = 25
DEFAULT_MAX_COLUMNS = 60
DEFAULT_STANDARD_RETENTION_HOURS = 24 * 7
DEFAULT_SENSITIVE_RETENTION_HOURS = 48
DEFAULT_DOWNLOAD_EXPIRY_HOURS = 24
DEFAULT_ENABLED_FORMATS = (
    ExportFormat.PDF,
    ExportFormat.DOCX,
    ExportFormat.XLSX,
    ExportFormat.CSV,
    ExportFormat.PRINT_HTML,
)

# ---------------------------------------------------------------------------
# Sensitivity / security
# ---------------------------------------------------------------------------

# Source types that always require elevated (sensitive) authorization.
SENSITIVE_SOURCE_TYPES = (ExportSourceType.BENEFICIARY,)

# Confidentiality levels that require elevated authorization to export.
SENSITIVE_CONFIDENTIALITY_LEVELS = (
    ConfidentialityLevel.RESTRICTED,
    ConfidentialityLevel.CONFIDENTIAL,
    ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
)

NON_SENSITIVE_CONFIDENTIALITY_LEVELS = (
    ConfidentialityLevel.PUBLIC,
    ConfidentialityLevel.INTERNAL,
)

# Characters that can trigger spreadsheet formula injection when a
# user-entered value begins with them.
FORMULA_INJECTION_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# ---------------------------------------------------------------------------
# Formats metadata
# ---------------------------------------------------------------------------

FORMAT_MIME_TYPES = {
    ExportFormat.PDF: "application/pdf",
    ExportFormat.DOCX: (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ),
    ExportFormat.XLSX: (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
    ExportFormat.CSV: "text/csv; charset=utf-8",
    ExportFormat.PRINT_HTML: "text/html; charset=utf-8",
}

FORMAT_EXTENSIONS = {
    ExportFormat.PDF: "pdf",
    ExportFormat.DOCX: "docx",
    ExportFormat.XLSX: "xlsx",
    ExportFormat.CSV: "csv",
    ExportFormat.PRINT_HTML: "html",
}

# Formats that are tabular (render columns/rows) vs document (narrative).
TABULAR_FORMATS = (ExportFormat.XLSX, ExportFormat.CSV)
DOCUMENT_FORMATS = (ExportFormat.PDF, ExportFormat.DOCX, ExportFormat.PRINT_HTML)

# Export file storage directory (relative to settings.PRIVATE_MEDIA_ROOT).
EXPORT_STORAGE_DIRECTORY = "exports"
