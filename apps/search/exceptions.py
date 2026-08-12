"""Exception types for the Enterprise Search module."""

from django.core.exceptions import PermissionDenied, ValidationError


class SearchValidationError(ValidationError):
    """Raised when a search query or filter is malformed."""


class SearchPermissionDenied(PermissionDenied):
    """Raised when an actor is not permitted to perform a search action."""
