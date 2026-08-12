"""Constants for the Document Management module."""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# Document Statuses
# ---------------------------------------------------------------------------


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    UPLOADED = "UPLOADED", _("Uploaded")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    RETURNED_FOR_CORRECTION = "RETURNED_FOR_CORRECTION", _("Returned for Correction")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    PUBLISHED = "PUBLISHED", _("Published")
    ACTIVE = "ACTIVE", _("Active")
    SUPERSEDED = "SUPERSEDED", _("Superseded")
    EXPIRED = "EXPIRED", _("Expired")
    SUSPENDED = "SUSPENDED", _("Suspended")
    ARCHIVED = "ARCHIVED", _("Archived")
    DISPOSAL_PENDING = "DISPOSAL_PENDING", _("Disposal Pending")
    DISPOSED = "DISPOSED", _("Disposed")


# ---------------------------------------------------------------------------
# Approval Statuses
# ---------------------------------------------------------------------------


class ApprovalStatus(models.TextChoices):
    NOT_SUBMITTED = "NOT_SUBMITTED", _("Not Submitted")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    RETURNED = "RETURNED", _("Returned")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS", _("Approved with Conditions")
    REJECTED = "REJECTED", _("Rejected")


# ---------------------------------------------------------------------------
# Publication Statuses
# ---------------------------------------------------------------------------


class PublicationStatus(models.TextChoices):
    NOT_PUBLISHED = "NOT_PUBLISHED", _("Not Published")
    PUBLISHED = "PUBLISHED", _("Published")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


# ---------------------------------------------------------------------------
# Confidentiality Levels
# ---------------------------------------------------------------------------


class ConfidentialityLevel(models.TextChoices):
    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding Restricted")
    FINANCIAL = "FINANCIAL", _("Financial Restricted")
    EXECUTIVE = "EXECUTIVE", _("Executive Restricted")
    BOARD = "BOARD", _("Board Restricted")


# ---------------------------------------------------------------------------
# Version Types
# ---------------------------------------------------------------------------


class VersionType(models.TextChoices):
    MAJOR = "MAJOR", _("Major")
    MINOR = "MINOR", _("Minor")


# ---------------------------------------------------------------------------
# Checkout Statuses
# ---------------------------------------------------------------------------


class CheckoutStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    RETURNED = "RETURNED", _("Returned")
    CANCELLED = "CANCELLED", _("Cancelled")
    EXPIRED = "EXPIRED", _("Expired")
    FORCE_RELEASED = "FORCE_RELEASED", _("Force Released")


# ---------------------------------------------------------------------------
# Share Permission Levels
# ---------------------------------------------------------------------------


class SharePermissionLevel(models.TextChoices):
    VIEW = "VIEW", _("View")
    COMMENT = "COMMENT", _("Comment")
    DOWNLOAD = "DOWNLOAD", _("Download")
    EDIT_METADATA = "EDIT_METADATA", _("Edit Metadata")
    UPLOAD_VERSION = "UPLOAD_VERSION", _("Upload Version")


# ---------------------------------------------------------------------------
# Relationship Types
# ---------------------------------------------------------------------------


class RelationshipType(models.TextChoices):
    REPLACES = "REPLACES", _("Replaces")
    SUPERSEDES = "SUPERSEDES", _("Supersedes")
    AMENDS = "AMENDS", _("Amends")
    SUPPORTS = "SUPPORTS", _("Supports")
    REFERENCES = "REFERENCES", _("References")
    ATTACHED_TO = "ATTACHED_TO", _("Attached to")
    EVIDENCE_FOR = "EVIDENCE_FOR", _("Evidence for")
    DERIVED_FROM = "DERIVED_FROM", _("Derived from")
    RELATED_TO = "RELATED_TO", _("Related to")
    SIGNED_VERSION = "SIGNED_VERSION", _("Signed version of")
    TRANSLATION_OF = "TRANSLATION_OF", _("Translation of")


# ---------------------------------------------------------------------------
# Hold Types
# ---------------------------------------------------------------------------


class HoldType(models.TextChoices):
    LEGAL = "LEGAL", _("Legal Hold")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding Hold")
    REGULATORY = "REGULATORY", _("Regulatory Hold")
    INVESTIGATION = "INVESTIGATION", _("Investigation Hold")
    OTHER = "OTHER", _("Other Hold")


# ---------------------------------------------------------------------------
# Hold Statuses
# ---------------------------------------------------------------------------


class HoldStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    RELEASED = "RELEASED", _("Released")


# ---------------------------------------------------------------------------
# Disposal Statuses
# ---------------------------------------------------------------------------


class DisposalStatus(models.TextChoices):
    REQUESTED = "REQUESTED", _("Requested")
    REVIEWED = "REVIEWED", _("Reviewed")
    APPROVED = "APPROVED", _("Approved")
    COMPLETED = "COMPLETED", _("Completed")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


# ---------------------------------------------------------------------------
# Disposal Methods
# ---------------------------------------------------------------------------


class DisposalMethod(models.TextChoices):
    SECURE_DELETE = "SECURE_DELETE", _("Secure Digital Deletion")
    PHYSICAL_DESTRUCTION = "PHYSICAL_DESTRUCTION", _("Physical Destruction")
    TRANSFER = "TRANSFER", _("Transfer to Archive")
    DONATION = "DONATION", _("Donation")
    OTHER = "OTHER", _("Other")


# ---------------------------------------------------------------------------
# Scan Statuses
# ---------------------------------------------------------------------------


class ScanStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending Scan")
    CLEAN = "CLEAN", _("Clean")
    SUSPICIOUS = "SUSPICIOUS", _("Suspicious")
    INFECTED = "INFECTED", _("Infected")
    SCAN_FAILED = "SCAN_FAILED", _("Scan Failed")
    QUARANTINED = "QUARANTINED", _("Quarantined")
    RELEASED = "RELEASED", _("Released")


# ---------------------------------------------------------------------------
# Retention Triggers
# ---------------------------------------------------------------------------


class RetentionTrigger(models.TextChoices):
    CREATION = "CREATION", _("Creation Date")
    APPROVAL = "APPROVAL", _("Approval Date")
    PUBLICATION = "PUBLICATION", _("Publication Date")
    EXPIRY = "EXPIRY", _("Expiry Date")
    PROJECT_CLOSURE = "PROJECT_CLOSURE", _("Project Closure")
    AGREEMENT_TERMINATION = "AGREEMENT_TERMINATION", _("Agreement Termination")
    MEMBERSHIP_EXIT = "MEMBERSHIP_EXIT", _("Membership Exit")
    BENEFICIARY_EXIT = "BENEFICIARY_EXIT", _("Beneficiary Exit")
    LAST_ACTIVITY = "LAST_ACTIVITY", _("Last Activity Date")


# ---------------------------------------------------------------------------
# Disposal Actions
# ---------------------------------------------------------------------------


class DisposalAction(models.TextChoices):
    DELETE = "DELETE", _("Permanent Delete")
    ARCHIVE = "ARCHIVE", _("Move to Archive")
    ANONYMIZE = "ANONYMIZE", _("Anonymize")
    NONE = "NONE", _("No Action Required")


# ---------------------------------------------------------------------------
# Audit Actions
# ---------------------------------------------------------------------------


class AuditAction(models.TextChoices):
    CREATED = "CREATED", _("Created")
    FILE_UPLOADED = "FILE_UPLOADED", _("File Uploaded")
    UPLOAD_REJECTED = "UPLOAD_REJECTED", _("Upload Rejected")
    VIEWED = "VIEWED", _("Viewed")
    PREVIEWED = "PREVIEWED", _("Previewed")
    DOWNLOADED = "DOWNLOADED", _("Downloaded")
    PRINTED = "PRINTED", _("Printed")
    METADATA_CHANGED = "METADATA_CHANGED", _("Metadata Changed")
    NEW_VERSION = "NEW_VERSION", _("New Version Uploaded")
    CHECKED_OUT = "CHECKED_OUT", _("Checked Out")
    CHECKED_IN = "CHECKED_IN", _("Checked In")
    CHECKOUT_CANCELLED = "CHECKOUT_CANCELLED", _("Checkout Cancelled")
    SUBMITTED_FOR_REVIEW = "SUBMITTED_FOR_REVIEW", _("Submitted for Review")
    RETURNED = "RETURNED", _("Returned for Correction")
    APPROVED = "APPROVED", _("Approved")
    PUBLISHED = "PUBLISHED", _("Published")
    UNPUBLISHED = "UNPUBLISHED", _("Unpublished")
    SHARED = "SHARED", _("Shared")
    SHARE_REVOKED = "SHARE_REVOKED", _("Share Revoked")
    CONFIDENTIALITY_CHANGED = "CONFIDENTIALITY_CHANGED", _("Confidentiality Changed")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    RETENTION_CHANGED = "RETENTION_CHANGED", _("Retention Changed")
    HOLD_APPLIED = "HOLD_APPLIED", _("Hold Applied")
    HOLD_RELEASED = "HOLD_RELEASED", _("Hold Released")
    DISPOSAL_REQUESTED = "DISPOSAL_REQUESTED", _("Disposal Requested")
    DISPOSAL_APPROVED = "DISPOSAL_APPROVED", _("Disposal Approved")
    DISPOSED = "DISPOSED", _("Disposed")
    ACCESS_DENIED = "ACCESS_DENIED", _("Access Denied")


# ---------------------------------------------------------------------------
# Timeline Event Types
# ---------------------------------------------------------------------------


class TimelineEventType(models.TextChoices):
    UPLOADED = "UPLOADED", _("Uploaded")
    METADATA_UPDATED = "METADATA_UPDATED", _("Metadata Updated")
    CHECKED_OUT = "CHECKED_OUT", _("Checked Out")
    CHECKED_IN = "CHECKED_IN", _("Checked In")
    REVIEWED = "REVIEWED", _("Reviewed")
    APPROVED = "APPROVED", _("Approved")
    PUBLISHED = "PUBLISHED", _("Published")
    DOWNLOADED = "DOWNLOADED", _("Downloaded")
    SHARED = "SHARED", _("Shared")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    EXPIRED = "EXPIRED", _("Expired")
    DISPOSED = "DISPOSED", _("Disposed")
    VERSION_UPLOADED = "VERSION_UPLOADED", _("Version Uploaded")
    RETURNED = "RETURNED", _("Returned for Correction")
    HOLD_APPLIED = "HOLD_APPLIED", _("Hold Applied")
    HOLD_RELEASED = "HOLD_RELEASED", _("Hold Released")


# ---------------------------------------------------------------------------
# Allowed File Extensions
# ---------------------------------------------------------------------------


ALLOWED_DOCUMENT_EXTENSIONS = frozenset({
    "pdf", "docx", "xlsx", "pptx", "txt", "csv", "odt",
    "png", "jpg", "jpeg", "webp",
    "mp3", "wav", "mp4", "mov",
})

ALLOWED_ARCHIVE_EXTENSIONS = frozenset({"zip"})

BLOCKED_EXTENSIONS = frozenset({
    "exe", "bat", "cmd", "msi", "dll", "js", "vbs", "scr", "ps1",
    "sh", "php", "py", "rb", "jar", "com", "pif", "application",
})

# ---------------------------------------------------------------------------
# MIME Type Mapping
# ---------------------------------------------------------------------------


ALLOWED_MIME_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/plain",
    "text/csv",
    "application/vnd.oasis.opendocument.text",
    "image/png",
    "image/jpeg",
    "image/webp",
    "audio/mpeg",
    "audio/wav",
    "video/mp4",
    "video/quicktime",
    "application/zip",
})

# ---------------------------------------------------------------------------
# File Size Limits (bytes)
# ---------------------------------------------------------------------------


DEFAULT_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
IMAGE_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
SPREADSHEET_MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
PRESENTATION_MAX_FILE_SIZE = 30 * 1024 * 1024  # 30 MB
VIDEO_MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
AUDIO_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

FILE_SIZE_LIMITS = {
    "pdf": DEFAULT_MAX_FILE_SIZE,
    "docx": DEFAULT_MAX_FILE_SIZE,
    "xlsx": SPREADSHEET_MAX_FILE_SIZE,
    "pptx": PRESENTATION_MAX_FILE_SIZE,
    "txt": DEFAULT_MAX_FILE_SIZE,
    "csv": SPREADSHEET_MAX_FILE_SIZE,
    "odt": DEFAULT_MAX_FILE_SIZE,
    "png": IMAGE_MAX_FILE_SIZE,
    "jpg": IMAGE_MAX_FILE_SIZE,
    "jpeg": IMAGE_MAX_FILE_SIZE,
    "webp": IMAGE_MAX_FILE_SIZE,
    "mp3": AUDIO_MAX_FILE_SIZE,
    "wav": AUDIO_MAX_FILE_SIZE,
    "mp4": VIDEO_MAX_FILE_SIZE,
    "mov": VIDEO_MAX_FILE_SIZE,
    "zip": DEFAULT_MAX_FILE_SIZE,
}

# ---------------------------------------------------------------------------
# Previewable Types
# ---------------------------------------------------------------------------


PREVIEWABLE_MIME_TYPES = frozenset({
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
    "text/plain",
    "text/csv",
})

# ---------------------------------------------------------------------------
# Permission Codenames
# ---------------------------------------------------------------------------


class DocumentPermissions:
    VIEW = "documents.view"
    VIEW_OWN = "documents.view_own"
    VIEW_UNIT = "documents.view_unit"
    VIEW_SENSITIVE = "documents.view_sensitive"
    VIEW_CONFIDENTIAL = "documents.view_confidential"
    UPLOAD = "documents.upload"
    CREATE = "documents.create"
    UPDATE_METADATA = "documents.update"
    UPLOAD_VERSION = "documents.upload_version"
    CHECKOUT = "documents.checkout"
    CHECKIN = "documents.checkin"
    CANCEL_CHECKOUT = "documents.cancel_checkout"
    SUBMIT = "documents.submit"
    REVIEW = "documents.review"
    RETURN_FOR_CORRECTION = "documents.return_for_correction"
    APPROVE = "documents.approve"
    PUBLISH = "documents.publish"
    UNPUBLISH = "documents.unpublish"
    ARCHIVE = "documents.archive"
    RESTORE = "documents.restore"
    REQUEST_DISPOSAL = "documents.request_disposal"
    APPROVE_DISPOSAL = "documents.approve_disposal"
    DOWNLOAD = "documents.download"
    PRINT = "documents.print"
    SHARE_INTERNAL = "documents.share_internal"
    SHARE_EXTERNAL = "documents.share_external"
    MANAGE_CATEGORIES = "documents.manage_categories"
    MANAGE_TYPES = "documents.manage_types"
    MANAGE_FOLDERS = "documents.manage_folders"
    MANAGE_TAGS = "documents.manage_tags"
    MANAGE_RETENTION = "documents.manage_retention"
    VIEW_HISTORY = "documents.view_history"
    VIEW_AUDIT = "documents.view_audit"
