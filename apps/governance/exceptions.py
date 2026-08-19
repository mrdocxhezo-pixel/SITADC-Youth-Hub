"""Governance, Risk, Compliance and Safeguarding exceptions."""


class GovernanceError(Exception):
    """Base exception for governance engine errors."""


class InvalidStateTransitionError(GovernanceError):
    """Raised when a governance record cannot transition to the target state."""


class InvalidReferenceNumberError(GovernanceError):
    """Raised when a governance reference number is missing or malformed."""


class DuplicateReferenceNumberError(GovernanceError):
    """Raised when a governance reference number already exists."""


class InvalidRiskScoreError(GovernanceError):
    """Raised when risk likelihood or impact fall outside the approved scale."""


class InvalidConfidentialityError(GovernanceError):
    """Raised when a confidentiality level is not permitted for a record type."""
