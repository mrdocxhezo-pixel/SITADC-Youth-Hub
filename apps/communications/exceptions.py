"""Communication and Media exceptions."""


class CommunicationError(Exception):
    """Base exception for communication engine errors."""


class InvalidStateTransitionError(CommunicationError):
    """Raised when a communication record cannot transition to the target state."""


class InvalidReferenceNumberError(CommunicationError):
    """Raised when a communication reference number is missing or malformed."""


class DuplicateReferenceNumberError(CommunicationError):
    """Raised when a communication reference number already exists."""


class InvalidConfidentialityError(CommunicationError):
    """Raised when a confidentiality level is not permitted for a record type."""
