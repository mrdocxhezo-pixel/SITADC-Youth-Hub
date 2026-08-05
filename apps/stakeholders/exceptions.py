"""Stakeholder domain exceptions."""


class StakeholderError(Exception):
    """Base exception for non-validation stakeholder failures."""


class InvalidStakeholderTransition(StakeholderError):
    """Raised when a stakeholder lifecycle transition is not permitted."""


class ReferenceConfigurationError(StakeholderError):
    """Raised when an expected stakeholder numbering scheme is unavailable."""
