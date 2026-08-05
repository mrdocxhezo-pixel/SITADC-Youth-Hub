"""
Domain exceptions for the reference numbering module.

All numbering exceptions extend the shared ``CoreException`` hierarchy so the
rest of the platform can handle them uniformly.
"""

from __future__ import annotations

from apps.core.exceptions import (
    BusinessRuleException,
    ConfigurationException,
    DuplicateRecordException,
)


class ReferenceNumberError(Exception):
    """Base exception for the reference numbering module."""


class InvalidNumberingSchemeError(ReferenceNumberError, ConfigurationException):
    """Raised when a numbering scheme is malformed or does not exist."""


class MissingNumberingContextError(ReferenceNumberError, ConfigurationException):
    """Raised when no numbering scheme can be resolved for a context."""


class ReferenceNumberCollisionError(ReferenceNumberError, DuplicateRecordException):
    """Raised when a duplicate reference number is prevented."""


class InactiveNumberingSchemeError(ReferenceNumberError, BusinessRuleException):
    """Raised when an inactive scheme is used to generate numbers."""
