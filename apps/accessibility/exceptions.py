"""Custom exceptions for the Accessibility Review module."""

from __future__ import annotations


class AccessibilityError(Exception):
    """Base exception for accessibility module."""


class InvalidContrastRatioError(AccessibilityError):
    """Raised when contrast ratio validation fails."""


class InvalidWCAGLevelError(AccessibilityError):
    """Raised when WCAG level is invalid."""


class PreferenceSyncError(AccessibilityError):
    """Raised when preference synchronization fails."""


class AuditValidationError(AccessibilityError):
    """Raised when audit validation fails."""


class FindingValidationError(AccessibilityError):
    """Raised when finding validation fails."""


class IssueValidationError(AccessibilityError):
    """Raised when issue validation fails."""


class ComplianceValidationError(AccessibilityError):
    """Raised when compliance validation fails."""


class ExceptionValidationError(AccessibilityError):
    """Raised when exception validation fails."""


class NotificationError(AccessibilityError):
    """Raised when notification sending fails."""


class AccessibilityConfigurationError(AccessibilityError):
    """Raised when accessibility configuration is invalid."""
