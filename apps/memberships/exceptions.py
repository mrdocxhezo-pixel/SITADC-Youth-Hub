"""
Domain exceptions for the membership management module.
"""

from __future__ import annotations


class MembershipDomainError(Exception):
    """Base class for membership domain errors."""


class ApplicationValidationError(MembershipDomainError):
    """Raised when a membership application fails validation."""


class RegistrationError(MembershipDomainError):
    """Raised when member registration cannot be completed."""


class StatusTransitionError(MembershipDomainError):
    """Raised when an invalid membership status transition is attempted."""


class RenewalError(MembershipDomainError):
    """Raised when a membership renewal cannot be processed."""


class PaymentError(MembershipDomainError):
    """Raised when a membership payment cannot be recorded or verified."""


class CardError(MembershipDomainError):
    """Raised when a membership card cannot be issued or revoked."""


class ExitError(MembershipDomainError):
    """Raised when a membership exit cannot be processed."""
