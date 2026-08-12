"""Domain exceptions for the MEAL module."""

from __future__ import annotations


class MEALServiceError(Exception):
    """Base error raised by MEAL services."""


class InvalidStatusTransition(MEALServiceError):
    """Raised when a workflow transition is not permitted."""


class ConflictingRecordError(MEALServiceError):
    """Raised when a record conflicts with existing MEAL data."""
