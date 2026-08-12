"""Constants for the Phase 19 Dynamic Report Builder module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReportTemplateStatus(models.TextChoices):
    """Lifecycle status of a report template.

    Templates flow ``DRAFT`` -> ``PUBLISHED`` -> ``ARCHIVED``.  A template
    whose current published version has been superseded by a newer published
    version is marked ``RETIRED``.  Submission and review statuses belong to
    Phase 20 and are intentionally not modelled here.
    """

    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")
    RETIRED = "RETIRED", _("Retired")


class TemplateVersionStatus(models.TextChoices):
    """Lifecycle status of a single template version snapshot."""

    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    SUPERSEDED = "SUPERSEDED", _("Superseded")
    ARCHIVED = "ARCHIVED", _("Archived")


class ReportingFrequency(models.TextChoices):
    """Approved reporting frequencies for a report template."""

    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    BIWEEKLY = "BIWEEKLY", _("Bi-weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    SEMI_ANNUAL = "SEMI_ANNUAL", _("Semi-annual")
    ANNUAL = "ANNUAL", _("Annual")
    ONE_OFF = "ONE_OFF", _("One-off")
    ON_DEMAND = "ON_DEMAND", _("On demand")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality classification applied to templates and sections."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    RESTRICTED = "RESTRICTED", _("Restricted")


class TemplateComponentType(models.TextChoices):
    """Reusable components that make up a report template layout."""

    HEADER = "HEADER", _("Header")
    COVER_PAGE = "COVER_PAGE", _("Cover page")
    METADATA_BLOCK = "METADATA_BLOCK", _("Metadata block")
    INSTRUCTIONS = "INSTRUCTIONS", _("Instructions")
    SECTION = "SECTION", _("Section")
    SUBSECTION = "SUBSECTION", _("Subsection")
    TABLE = "TABLE", _("Table")
    CHART = "CHART", _("Chart")
    ATTACHMENTS = "ATTACHMENTS", _("Attachments")
    SIGNATURE_BLOCK = "SIGNATURE_BLOCK", _("Signature block")
    APPROVAL_BLOCK = "APPROVAL_BLOCK", _("Approval block")
    FOOTER = "FOOTER", _("Footer")


class FieldType(models.TextChoices):
    """Supported dynamic field types (Phase 19 - Part 1 section 13)."""

    # Text
    TEXT = "TEXT", _("Single-line text")
    MULTILINE_TEXT = "MULTILINE_TEXT", _("Multi-line text")
    RICH_TEXT = "RICH_TEXT", _("Rich text")
    # Numbers
    INTEGER = "INTEGER", _("Integer")
    DECIMAL = "DECIMAL", _("Decimal")
    CURRENCY = "CURRENCY", _("Currency")
    PERCENTAGE = "PERCENTAGE", _("Percentage")
    # Date & time
    DATE = "DATE", _("Date")
    TIME = "TIME", _("Time")
    DATETIME = "DATETIME", _("Date & time")
    # Selection
    DROPDOWN = "DROPDOWN", _("Dropdown")
    MULTI_SELECT = "MULTI_SELECT", _("Multi-select")
    RADIO = "RADIO", _("Radio buttons")
    CHECKBOX = "CHECKBOX", _("Checkboxes")
    TOGGLE = "TOGGLE", _("Toggle switch")
    # Media
    IMAGE = "IMAGE", _("Image upload")
    VIDEO = "VIDEO", _("Video upload")
    AUDIO = "AUDIO", _("Audio upload")
    DOCUMENT = "DOCUMENT", _("Document upload")
    # Specialized
    SIGNATURE = "SIGNATURE", _("Signature")
    QR_CODE = "QR_CODE", _("QR code")
    BARCODE = "BARCODE", _("Barcode")
    GPS_COORDINATES = "GPS_COORDINATES", _("GPS coordinates")
    USER_SELECTOR = "USER_SELECTOR", _("User selector")
    ORGANIZATION_SELECTOR = "ORGANIZATION_SELECTOR", _("Organization selector")
    BENEFICIARY_SELECTOR = "BENEFICIARY_SELECTOR", _("Beneficiary selector")
    PROGRAM_SELECTOR = "PROGRAM_SELECTOR", _("Program selector")
    PROJECT_SELECTOR = "PROJECT_SELECTOR", _("Project selector")
    # Advanced
    FORMULA = "FORMULA", _("Formula (calculated)")
    AUTO_REFERENCE = "AUTO_REFERENCE", _("Auto-generated reference number")
    TABLE_GRID = "TABLE_GRID", _("Table / grid")
    REPEATING_GROUP = "REPEATING_GROUP", _("Repeating group")


class FieldDataType(models.TextChoices):
    """Serialized value type used for calculations, export, and comparison."""

    STRING = "STRING", _("String")
    INTEGER = "INTEGER", _("Integer")
    DECIMAL = "DECIMAL", _("Decimal")
    BOOLEAN = "BOOLEAN", _("Boolean")
    DATE = "DATE", _("Date")
    DATETIME = "DATETIME", _("Datetime")
    JSON = "JSON", _("Structured data")


class ValidationRuleType(models.TextChoices):
    """Configurable validation rule types (Phase 19 - Part 1 section 14)."""

    REQUIRED = "REQUIRED", _("Required field")
    MIN_LENGTH = "MIN_LENGTH", _("Minimum length")
    MAX_LENGTH = "MAX_LENGTH", _("Maximum length")
    MIN_VALUE = "MIN_VALUE", _("Numeric minimum")
    MAX_VALUE = "MAX_VALUE", _("Numeric maximum")
    DATE_MIN = "DATE_MIN", _("Earliest date")
    DATE_MAX = "DATE_MAX", _("Latest date")
    REGEX = "REGEX", _("Pattern match")
    EMAIL = "EMAIL", _("Email address")
    URL = "URL", _("URL")
    FILE_TYPE = "FILE_TYPE", _("Allowed file types")
    FILE_SIZE_MAX = "FILE_SIZE_MAX", _("Maximum file size")
    DUPLICATE_PREVENTION = "DUPLICATE_PREVENTION", _("Duplicate prevention")
    CROSS_FIELD = "CROSS_FIELD", _("Cross-field comparison")
    BUSINESS_RULE = "BUSINESS_RULE", _("Business rule")


class ConditionType(models.TextChoices):
    """Actions a conditional logic rule can apply (Phase 19 - Part 1 section 15)."""

    SHOW_FIELD = "SHOW_FIELD", _("Show field")
    HIDE_FIELD = "HIDE_FIELD", _("Hide field")
    ENABLE_FIELD = "ENABLE_FIELD", _("Enable field")
    DISABLE_FIELD = "DISABLE_FIELD", _("Disable field")
    REQUIRE_FIELD = "REQUIRE_FIELD", _("Require field")
    SHOW_SECTION = "SHOW_SECTION", _("Show section")
    HIDE_SECTION = "HIDE_SECTION", _("Hide section")


class ConditionOperator(models.TextChoices):
    """Comparison operators supported by conditional logic."""

    EQUALS = "EQUALS", _("Equals")
    NOT_EQUALS = "NOT_EQUALS", _("Does not equal")
    CONTAINS = "CONTAINS", _("Contains")
    NOT_CONTAINS = "NOT_CONTAINS", _("Does not contain")
    GREATER_THAN = "GREATER_THAN", _("Greater than")
    GREATER_THAN_OR_EQUAL = "GREATER_THAN_OR_EQUAL", _("Greater than or equal")
    LESS_THAN = "LESS_THAN", _("Less than")
    LESS_THAN_OR_EQUAL = "LESS_THAN_OR_EQUAL", _("Less than or equal")
    IS_EMPTY = "IS_EMPTY", _("Is empty")
    IS_NOT_EMPTY = "IS_NOT_EMPTY", _("Is not empty")
    IN = "IN", _("Is one of")
    NOT_IN = "NOT_IN", _("Is none of")
    STARTS_WITH = "STARTS_WITH", _("Starts with")
    ENDS_WITH = "ENDS_WITH", _("Ends with")


class ConditionTargetType(models.TextChoices):
    """What a conditional logic rule targets."""

    FIELD = "FIELD", _("Field")
    SECTION = "SECTION", _("Section")


class SectionVisibilityMode(models.TextChoices):
    """How a section's visibility is determined."""

    ALWAYS = "ALWAYS", _("Always visible")
    CONDITIONAL = "CONDITIONAL", _("Conditional visibility")
    ROLE_BASED = "ROLE_BASED", _("Role-based visibility")
    REPORTING_PERIOD = "REPORTING_PERIOD", _("Reporting-period logic")


class ReferenceSourceModule(models.TextChoices):
    """Data source modules that a referenced field can pull from."""

    USERS = "users", _("Users")
    ORGANIZATIONS = "organizations", _("Organizations")
    LEADERSHIP = "leadership", _("Leadership")
    MEMBERSHIPS = "memberships", _("Memberships")
    VOLUNTEERS = "volunteers", _("Volunteers")
    STAKEHOLDERS = "stakeholders", _("Stakeholders")
    PROGRAMS = "programs", _("Programs")
    PROJECTS = "projects", _("Projects")
    BENEFICIARIES = "beneficiaries", _("Beneficiaries")
    MEAL = "meal", _("MEAL")
    FINANCE = "finance", _("Finance")


class ReportTemplateAuditAction(models.TextChoices):
    """Audited events recorded by the report builder services."""

    CREATED = "CREATED", _("Template created")
    UPDATED = "UPDATED", _("Template updated")
    DELETED = "DELETED", _("Template deleted")
    RESTORED = "RESTORED", _("Template restored")
    PUBLISHED = "PUBLISHED", _("Template published")
    UNPUBLISHED = "UNPUBLISHED", _("Template unpublished")
    ARCHIVED = "ARCHIVED", _("Template archived")
    CLONED = "CLONED", _("Template cloned")
    IMPORTED = "IMPORTED", _("Template imported")
    EXPORTED = "EXPORTED", _("Template exported")
    VERSION_CREATED = "VERSION_CREATED", _("Version created")
    VERSION_RESTORED = "VERSION_RESTORED", _("Version restored")
    SCHEMA_UPDATED = "SCHEMA_UPDATED", _("Schema updated")
    VALIDATION_FAILED = "VALIDATION_FAILED", _("Schema validation failed")
    PREVIEWED = "PREVIEWED", _("Template previewed")
    CATEGORY_CREATED = "CATEGORY_CREATED", _("Category created")
    CATEGORY_UPDATED = "CATEGORY_UPDATED", _("Category updated")
    CATEGORY_ACTIVATED = "CATEGORY_ACTIVATED", _("Category activated")
    CATEGORY_DEACTIVATED = "CATEGORY_DEACTIVATED", _("Category deactivated")
    SETTINGS_UPDATED = "SETTINGS_UPDATED", _("Report builder settings updated")


DEFAULT_REPORT_SCHEME_PREFIX = "RPT"
DEFAULT_VERSION = "1.0"

# ---------------------------------------------------------------------------
# Phase 20 — Report Management Constants
# ---------------------------------------------------------------------------

class ReportStatus(models.TextChoices):
    """Lifecycle status of a report instance."""

    DRAFT = "DRAFT", _("Draft")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    AWAITING_VALIDATION = "AWAITING_VALIDATION", _("Awaiting Validation")
    VALIDATION_FAILED = "VALIDATION_FAILED", _("Validation Failed")
    READY_FOR_SUBMISSION = "READY_FOR_SUBMISSION", _("Ready for Submission")
    SUBMITTED = "SUBMITTED", _("Submitted")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION", _("Returned for Correction")
    RESUBMITTED = "RESUBMITTED", _("Resubmitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    FINALIZED = "FINALIZED", _("Finalized")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")


class ReportValidationStatus(models.TextChoices):
    """Validation state of a report."""

    NOT_VALIDATED = "NOT_VALIDATED", _("Not Validated")
    VALIDATING = "VALIDATING", _("Validating")
    PASSED = "PASSED", _("Passed")
    FAILED = "FAILED", _("Failed")


class SubmissionStatus(models.TextChoices):
    """Status of a report submission."""

    PENDING = "PENDING", _("Pending")
    SUBMITTED = "SUBMITTED", _("Submitted")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")
    RETURNED = "RETURNED", _("Returned")
    RESUBMITTED = "RESUBMITTED", _("Resubmitted")


class EvidenceType(models.TextChoices):
    """Type of evidence attached to a report."""

    PHOTOGRAPH = "PHOTOGRAPH", _("Photograph")
    VIDEO = "VIDEO", _("Video")
    AUDIO = "AUDIO", _("Audio Recording")
    DOCUMENT = "DOCUMENT", _("Document")
    SPREADSHEET = "SPREADSHEET", _("Spreadsheet")
    PDF = "PDF", _("PDF")
    SIGNED_DOCUMENT = "SIGNED_DOCUMENT", _("Signed Document")
    ATTENDANCE_SHEET = "ATTENDANCE_SHEET", _("Attendance Sheet")
    FINANCIAL_RECORD = "FINANCIAL_RECORD", _("Financial Record")
    RECEIPT = "RECEIPT", _("Receipt")
    BENEFICIARY_LIST = "BENEFICIARY_LIST", _("Beneficiary List")
    MONITORING_TOOL = "MONITORING_TOOL", _("Monitoring Tool")
    EVALUATION_TOOL = "EVALUATION_TOOL", _("Evaluation Tool")
    GPS_COORDINATES = "GPS_COORDINATES", _("GPS Coordinates")
    QR_CODE = "QR_CODE", _("QR Code")
    OTHER = "OTHER", _("Other")


# ---------------------------------------------------------------------------
# Permission mapping
# ---------------------------------------------------------------------------

REPORT_TEMPLATE_ACTION_PERMISSIONS: dict[str, str] = {
    "view": "report_templates.view",
    "create": "report_templates.create",
    "update": "report_templates.update",
    "delete": "report_templates.delete",
    "preview": "report_templates.preview",
    "publish": "report_templates.publish",
    "archive": "report_templates.archive",
    "restore": "report_templates.restore",
    "clone": "report_templates.clone",
    "import": "report_templates.import",
    "export": "report_templates.export",
    "configure": "report_templates.configure",
    "manage": "report_templates.manage",
}
