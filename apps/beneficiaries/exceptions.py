"""Domain-specific exceptions for beneficiary management."""

from __future__ import annotations


class BeneficiaryDomainError(Exception):
    """Base class for beneficiary domain errors."""


class BeneficiaryNotFoundError(BeneficiaryDomainError):
    """The requested beneficiary record does not exist."""


class BeneficiaryDuplicateError(BeneficiaryDomainError):
    """A likely duplicate beneficiary already exists."""


class BeneficiaryValidationError(BeneficiaryDomainError):
    """The supplied data failed beneficiary validation."""


class ConsentRequiredError(BeneficiaryDomainError):
    """An operation requires recorded, unexpired consent."""


class MinorConsentError(BeneficiaryDomainError):
    """A minor beneficiary requires recorded guardian consent or assent."""


class SafeguardingRequiredError(BeneficiaryDomainError):
    """A safeguarding review must exist before the operation can proceed."""


class LifecycleTransitionError(BeneficiaryDomainError):
    """The requested lifecycle transition is not allowed."""
