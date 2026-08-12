"""Controlled domain exceptions for the Calendar & Meetings module."""

from __future__ import annotations


class CalendarManagementError(Exception):
    """Base exception for the Calendar & Meetings module."""


class CalendarAccessDeniedError(CalendarManagementError):
    """Raised when an actor is not authorized for a calendar action."""


class EventValidationError(CalendarManagementError):
    """Raised when event invariants are violated."""


class EventConflictError(EventValidationError):
    """Raised when an event conflicts with an existing booking."""


class MeetingSchedulingError(CalendarManagementError):
    """Raised when a meeting cannot be scheduled."""


class InvalidTransitionError(CalendarManagementError):
    """Raised when a status transition is not permitted."""


class InvitationError(CalendarManagementError):
    """Raised when an invitation cannot be issued."""


class QuorumError(CalendarManagementError):
    """Raised when quorum cannot be evaluated or is not met."""


class MinutesWorkflowError(CalendarManagementError):
    """Raised when a minutes operation violates its workflow."""


class MeetingDocumentError(CalendarManagementError):
    """Raised when a meeting document cannot be linked."""


class MeetingExportError(CalendarManagementError):
    """Raised when an export cannot be produced."""


class ConfidentialAccessError(CalendarManagementError):
    """Raised when a confidential record access cannot be granted."""
