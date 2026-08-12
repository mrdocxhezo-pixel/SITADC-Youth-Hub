"""Domain exceptions for the Document Management module."""
from __future__ import annotations


class DocumentManagementError(Exception):
    """Base exception for document management operations."""


class DocumentUploadError(DocumentManagementError):
    """Raised when document upload fails."""


class UnsupportedFileTypeError(DocumentUploadError):
    """Raised when an unsupported file type is uploaded."""


class FileSizeExceededError(DocumentUploadError):
    """Raised when file size exceeds the configured limit."""


class UnsafeFileError(DocumentUploadError):
    """Raised when a file fails safety validation."""


class DocumentAccessDeniedError(DocumentManagementError):
    """Raised when a user lacks permission for a document operation."""


class SensitiveDocumentAccessError(DocumentAccessDeniedError):
    """Raised when access to a sensitive document is denied."""


class DocumentVersionError(DocumentManagementError):
    """Raised when a version operation fails."""


class DocumentCheckoutError(DocumentManagementError):
    """Raised when a checkout operation fails."""


class DocumentWorkflowError(DocumentManagementError):
    """Raised when a workflow transition is invalid."""


class DocumentApprovalError(DocumentManagementError):
    """Raised when an approval operation fails."""


class DocumentPublicationError(DocumentManagementError):
    """Raised when a publication operation fails."""


class DocumentExpiryError(DocumentManagementError):
    """Raised when an expiry operation fails."""


class DocumentShareError(DocumentManagementError):
    """Raised when a sharing operation fails."""


class DocumentRetentionError(DocumentManagementError):
    """Raised when a retention operation fails."""


class DocumentHoldError(DocumentManagementError):
    """Raised when a hold operation fails."""


class DocumentArchiveError(DocumentManagementError):
    """Raised when an archive operation fails."""


class DocumentDisposalError(DocumentManagementError):
    """Raised when a disposal operation fails."""


class DocumentStorageError(DocumentManagementError):
    """Raised when a storage operation fails."""


class DocumentReferenceError(DocumentManagementError):
    """Raised when reference number generation fails."""


class CircularFolderError(DocumentManagementError):
    """Raised when a folder move would create a circular hierarchy."""
