"""Finance Engine selectors."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Optional, Tuple

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet, Sum
from django.utils import timezone

from guardian.shortcuts import get_objects_for_user

User = get_user_model()


def get_accessible_financial_accounts(user: User) -> Iterable[Any]:
    """
    Get financial accounts accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Financial accounts the user can access.
    """
    FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
    return get_objects_for_user(user, "finance.view_financialaccount", FinancialAccount)


def get_accessible_bank_accounts(user: User) -> Iterable[Any]:
    """
    Get bank accounts accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Bank accounts the user can access.
    """
    BankAccount = django_apps.get_model("finance", "BankAccount")
    return get_objects_for_user(user, "finance.view_bankaccount", BankAccount)


def get_accessible_petty_cash_accounts(user: User) -> Iterable[Any]:
    """
    Get petty cash accounts accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Petty cash accounts the user can access.
    """
    PettyCash = django_apps.get_model("finance", "PettyCash")
    return get_objects_for_user(user, "finance.view_pettycash", PettyCash)


def get_accessible_budgets(user: User) -> Iterable[Any]:
    """
    Get budgets accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Budgets the user can access.
    """
    Budget = django_apps.get_model("finance", "Budget")
    return get_objects_for_user(user, "finance.view_budget", Budget)


def get_accessible_transactions(user: User) -> Iterable[Any]:
    """
    Get transactions accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Transactions the user can access.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    return get_objects_for_user(user, "finance.view_transaction", Transaction)


def get_accessible_grants(user: User) -> Iterable[Any]:
    """
    Get grants accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Grants the user can access.
    """
    Grant = django_apps.get_model("finance", "Grant")
    return get_objects_for_user(user, "finance.view_grant", Grant)


def get_accessible_donors(user: User) -> Iterable[Any]:
    """
    Get donors accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Donors the user can access.
    """
    Donor = django_apps.get_model("finance", "Donor")
    return get_objects_for_user(user, "finance.view_donor", Donor)


def get_accessible_sponsors(user: User) -> Iterable[Any]:
    """
    Get sponsors accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Sponsors the user can access.
    """
    Sponsor = django_apps.get_model("finance", "Sponsor")
    return get_objects_for_user(user, "finance.view_sponsor", Sponsor)


def get_accessible_fundraising_campaigns(user: User) -> Iterable[Any]:
    """
    Get fundraising campaigns accessible to the user.

    Args:
        user: The user to check permissions for.

    Returns:
        Iterable: Fundraising campaigns the user can access.
    """
    FundraisingCampaign = django_apps.get_model("finance", "FundraisingCampaign")
    return get_objects_for_user(user, "finance.view_fundraisingcampaign", FundraisingCampaign)


def get_financial_account_balance(account_id: int, as_of_date: Optional[timezone.datetime] = None) -> Decimal:
    """
    Get the balance of a financial account as of a specific date.

    Args:
        account_id: ID of the financial account.
        as_of_date: Date to calculate balance as of (default: now).

    Returns:
        Decimal: The account balance.
    """
    if as_of_date is None:
        as_of_date = timezone.now()
        
    FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
    Transaction = django_apps.get_model("finance", "Transaction")
    
    try:
        account = FinancialAccount.objects.get(id=account_id)
    except FinancialAccount.DoesNotExist:
        return Decimal('0')
        
    # Get all transactions for this account up to the specified date
    transactions = Transaction.objects.filter(
        financial_account=account,
        transaction_date__lte=as_of_date,
        status="POSTED"
    )
    
    # Calculate balance based on transaction types
    debit_sum = transactions.filter(transaction_type="DEBIT").aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    credit_sum = transactions.filter(transaction_type="CREDIT").aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0')
    
    # For asset and expense accounts: debit increases balance, credit decreases
    # For liability, equity, and income accounts: credit increases balance, debit decreases
    if account.account_type in ['asset', 'expense']:
        balance = account.opening_balance + debit_sum - credit_sum
    else:  # liability, equity, income
        balance = account.opening_balance + credit_sum - debit_sum
        
    return balance


def get_budget_variance(budget_id: int, as_of_date: Optional[timezone.datetime] = None) -> dict:
    """
    Get budget variance analysis.

    Args:
        budget_id: ID of the budget.
        as_of_date: Date to calculate variance as of (default: now).

    Returns:
        Dict containing budget, actual, variance, and percentage.
    """
    if as_of_date is None:
        as_of_date = timezone.now()
        
    Budget = django_apps.get_model("finance", "Budget")
    Transaction = django_apps.get_model("finance", "Transaction")
    
    try:
        budget = Budget.objects.get(id=budget_id)
    except Budget.DoesNotExist:
        return {
            'budgeted': Decimal('0'),
            'actual': Decimal('0'),
            'variance': Decimal('0'),
            'variance_percentage': Decimal('0'),
            'remaining': Decimal('0')
        }
        
    # Get actual spending from transactions
    actual_spending = Transaction.objects.filter(
        budget=budget,
        transaction_date__lte=as_of_date,
        status="POSTED"
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    variance = budget.total_amount - actual_spending
    variance_percentage = (variance / budget.total_amount * 100) if budget.total_amount > 0 else Decimal('0')
    
    return {
        'budgeted': budget.total_amount,
        'actual': actual_spending,
        'variance': variance,
        'variance_percentage': variance_percentage,
        'remaining': budget.remaining
    }


def get_grant_remaining_amount(grant_id: int) -> Decimal:
    """
    Get the remaining amount of a grant.

    Args:
        grant_id: ID of the grant.

    Returns:
        Decimal: The remaining grant amount.
    """
    Grant = django_apps.get_model("finance", "Grant")
    
    try:
        grant = Grant.objects.get(id=grant_id)
    except Grant.DoesNotExist:
        return Decimal('0')
        
    return grant.remaining_amount


def get_donor_total_contributions(donor_id: int) -> Decimal:
    """
    Get the total contributions from a donor.

    Args:
        donor_id: ID of the donor.

    Returns:
        Decimal: The total contributions from the donor.
    """
    Donor = django_apps.get_model("finance", "Donor")
    
    try:
        donor = Donor.objects.get(id=donor_id)
    except Donor.DoesNotExist:
        return Decimal('0')
        
    return donor.total_contributions


def get_financial_year_for_date(date: timezone.datetime) -> Optional[Any]:
    """
    Get the financial year for a given date.

    Args:
        date: The date to check.

    Returns:
        FinancialYear: The financial year containing the date, or None if not found.
    """
    FinancialYear = django_apps.get_model("finance", "FinancialYear")
    
    try:
        return FinancialYear.objects.get(
            start_date__lte=date,
            end_date__gte=date,
            is_active=True
        )
    except FinancialYear.DoesNotExist:
        return None


def get_recent_transactions(user: User, limit: int = 10) -> Iterable[Any]:
    """
    Get recent transactions accessible to the user.

    Args:
        user: The user to check permissions for.
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Recent transactions the user can access.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    accessible_transactions = get_accessible_transactions(user)
    return accessible_transactions.order_by('-transaction_date')[:limit]


def get_budgets_by_financial_year(financial_year_id: int, user: User) -> Iterable[Any]:
    """
    Get budgets for a specific financial year that are accessible to the user.

    Args:
        financial_year_id: ID of the financial year.
        user: The user to check permissions for.

    Returns:
        Iterable: Budgets for the financial year that the user can access.
    """
    Budget = django_apps.get_model("finance", "Budget")
    FinancialYear = django_apps.get_model("finance", "FinancialYear")
    
    try:
        financial_year = FinancialYear.objects.get(id=financial_year_id)
    except FinancialYear.DoesNotExist:
        return Budget.objects.none()
        
    accessible_budgets = get_accessible_budgets(user)
    return accessible_budgets.filter(financial_year=financial_year)


def get_transactions_by_account(account_id: int, user: User, limit: int = 50) -> Iterable[Any]:
    """
    Get transactions for a specific financial account that are accessible to the user.

    Args:
        account_id: ID of the financial account.
        user: The user to check permissions for.
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Transactions for the account that the user can access.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
    
    # Check if user can access the account
    accessible_accounts = get_accessible_financial_accounts(user)
    if not accessible_accounts.filter(id=account_id).exists():
        return Transaction.objects.none()
        
    try:
        account = FinancialAccount.objects.get(id=account_id)
    except FinancialAccount.DoesNotExist:
        return Transaction.objects.none()
        
    accessible_transactions = get_accessible_transactions(user)
    return accessible_transactions.filter(financial_account=account).order_by('-transaction_date')[:limit]


def get_expense_transactions_by_category(
    user: User, 
    start_date: Optional[timezone.datetime] = None,
    end_date: Optional[timezone.datetime] = None,
    limit: int = 100
) -> Iterable[Any]:
    """
    Get expense transactions grouped by category/source.

    Args:
        user: The user to check permissions for.
        start_date: Start date for filtering (optional).
        end_date: End date for filtering (optional).
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Expense transactions accessible to the user.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    accessible_transactions = get_accessible_transactions(user)
    
    queryset = accessible_transactions.filter(transaction_type="EXPENSE")
    
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)
        
    return queryset.order_by('-transaction_date')[:limit]


def get_income_transactions_by_source(
    user: User, 
    start_date: Optional[timezone.datetime] = None,
    end_date: Optional[timezone.datetime] = None,
    limit: int = 100
) -> Iterable[Any]:
    """
    Get income transactions grouped by source.

    Args:
        user: The user to check permissions for.
        start_date: Start date for filtering (optional).
        end_date: End date for filtering (optional).
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Income transactions accessible to the user.
    """
    Transaction = django_apps.get_model("finance", "Transaction")
    accessible_transactions = get_accessible_transactions(user)
    
    queryset = accessible_transactions.filter(transaction_type="INCOME")
    
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)
        
    return queryset.order_by('-transaction_date')[:limit]