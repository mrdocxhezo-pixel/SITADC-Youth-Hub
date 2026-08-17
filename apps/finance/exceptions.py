"""Finance Engine exceptions."""


class FinanceError(Exception):
    """Base exception for finance engine errors."""


class InsufficientFundsError(FinanceError):
    """Raised when there are insufficient funds for a transaction."""


class InvalidTransactionError(FinanceError):
    """Raised when a transaction is invalid."""


class BudgetExceededError(FinanceError):
    """Raised when a budget is exceeded."""


class InvalidAccountError(FinanceError):
    """Raised when an account is invalid or inaccessible."""


class CurrencyMismatchError(FinanceError):
    """Raised when there is a currency mismatch in financial operations."""


class FinancialPeriodError(FinanceError):
    """Raised when attempting to post to a closed financial period."""
