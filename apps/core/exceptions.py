class CoreException(Exception):
    """
    Base exception class for the application.
    All custom exceptions should inherit from this.
    """


class ValidationException(CoreException):
    """Raised when data validation fails."""


class BusinessRuleException(CoreException):
    """Raised when a business rule is violated."""


class PermissionDeniedException(CoreException):
    """Raised when authorization fails."""


class WorkflowException(CoreException):
    """Raised when an invalid workflow transition is attempted."""


class ConfigurationException(CoreException):
    """Raised when a system configuration error is detected."""


class DuplicateRecordException(CoreException):
    """Raised when attempting to create a record that already exists."""


class InactiveAccountException(CoreException):
    """Raised when an inactive user attempts to perform an action."""


class DocumentProcessingException(CoreException):
    """Raised when document handling or validation fails."""


class ImportException(CoreException):
    """Raised when bulk import operations fail."""


class ExportException(CoreException):
    """Raised when bulk export operations fail."""
