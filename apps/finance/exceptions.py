"""Finance Engine exceptions."""


class FinanceError(Exception):
    """Base exception for finance engine errors."""
    pass


class InsufficientFundsError(FinanceError):
    """Raised when there are insufficient funds for a transaction."""
    pass


class InvalidTransactionError(FinanceError):
    """Raised when a transaction is invalid."""
    pass


class BudgetExceededError(FinanceError):
    """Raised when a budget is exceeded."""
    pass


class InvalidAccountError(FinanceError):
    """Raised when an account is invalid or inaccessible."""
    pass


class CurrencyMismatchError(FinanceError):
    """Raised when there is a currency mismatch in financial operations."""
    pass


class FinancialPeriodError(FinanceError):
    """Raised when attempting to post to a closed financial period."""
    pass