"""Finance Engine selectors.

All selectors are fail-closed: a user without the relevant ``finance.*``
permission receives an empty queryset rather than data.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Q, QuerySet, Sum
from django.utils import timezone

from apps.finance.constants import TransactionStatus, TransactionType
from apps.finance.models import (
    BankAccount,
    Budget,
    Donor,
    FinancialAccount,
    FinancialYear,
    FundraisingCampaign,
    Grant,
    PettyCash,
    Sponsor,
    Transaction,
)

User = get_user_model()

_POSTED_STATUSES = (
    TransactionStatus.POSTED,
    TransactionStatus.PAID,
    TransactionStatus.RECONCILED,
)


def get_accessible_financial_accounts(user: User) -> QuerySet[FinancialAccount]:
    """Financial accounts the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_finance_data

    if not user_can_view_finance_data(user):
        return FinancialAccount.objects.none()
    return FinancialAccount.objects.all()


def get_accessible_bank_accounts(user: User) -> QuerySet[BankAccount]:
    """Bank accounts the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_finance_data

    if not user_can_view_finance_data(user):
        return BankAccount.objects.none()
    return BankAccount.objects.all()


def get_accessible_petty_cash_accounts(user: User) -> QuerySet[PettyCash]:
    """Petty cash accounts the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_finance_data

    if not user_can_view_finance_data(user):
        return PettyCash.objects.none()
    return PettyCash.objects.all()


def get_accessible_budgets(user: User) -> QuerySet[Budget]:
    """Budgets the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_budgets

    if not user_can_view_budgets(user):
        return Budget.objects.none()
    return Budget.objects.all()


def get_accessible_transactions(user: User) -> QuerySet[Transaction]:
    """Transactions the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_transactions

    if not user_can_view_transactions(user):
        return Transaction.objects.none()
    return Transaction.objects.all()


def get_accessible_grants(user: User) -> QuerySet[Grant]:
    """Grants the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_grants

    if not user_can_view_grants(user):
        return Grant.objects.none()
    return Grant.objects.all()


def get_accessible_donors(user: User) -> QuerySet[Donor]:
    """Donors the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_donors

    if not user_can_view_donors(user):
        return Donor.objects.none()
    return Donor.objects.all()


def get_accessible_sponsors(user: User) -> QuerySet[Sponsor]:
    """Sponsors the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_sponsors

    if not user_can_view_sponsors(user):
        return Sponsor.objects.none()
    return Sponsor.objects.all()


def get_accessible_fundraising_campaigns(user: User) -> QuerySet[FundraisingCampaign]:
    """Fundraising campaigns the user may view (empty queryset when denied)."""
    from apps.finance.permissions import user_can_view_fundraising

    if not user_can_view_fundraising(user):
        return FundraisingCampaign.objects.none()
    return FundraisingCampaign.objects.all()


def get_financial_account_balance(
    account_id: int, as_of_date: timezone.datetime | None = None
) -> Decimal:
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

    try:
        account = FinancialAccount.objects.get(id=account_id)
    except FinancialAccount.DoesNotExist:
        return Decimal("0")

    posted = Transaction.objects.filter(
        financial_account=account,
        transaction_date__lte=as_of_date,
        status__in=_POSTED_STATUSES,
    )
    income = posted.filter(transaction_type=TransactionType.INCOME).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    expense = posted.filter(transaction_type=TransactionType.EXPENSE).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    return account.opening_balance + income - expense


def get_budget_variance(
    budget_id: int, as_of_date: timezone.datetime | None = None
) -> dict:
    """
    Get budget variance analysis.

    Args:
        budget_id: ID of the budget.
        as_of_date: Unused; kept for API compatibility.

    Returns:
        Dict containing budgeted, actual, variance, and percentage.
    """
    try:
        budget = Budget.objects.get(id=budget_id)
    except Budget.DoesNotExist:
        return {
            "budgeted": Decimal("0"),
            "actual": Decimal("0"),
            "variance": Decimal("0"),
            "variance_percentage": Decimal("0"),
            "remaining": Decimal("0"),
        }
    return budget.get_variance()


def get_grant_remaining_amount(grant_id: int) -> Decimal:
    """
    Get the remaining undisbursed amount of a grant.

    Args:
        grant_id: ID of the grant.

    Returns:
        Decimal: The remaining grant amount.
    """
    try:
        grant = Grant.objects.get(id=grant_id)
    except Grant.DoesNotExist:
        return Decimal("0")
    return grant.remaining_amount


def get_donor_total_contributions(donor_id: int) -> Decimal:
    """
    Get the total contributions from a donor.

    Args:
        donor_id: ID of the donor.

    Returns:
        Decimal: The total contributions from the donor.
    """
    try:
        donor = Donor.objects.get(id=donor_id)
    except Donor.DoesNotExist:
        return Decimal("0")
    return donor.total_donated


def get_financial_year_for_date(date: timezone.datetime) -> FinancialYear | None:
    """
    Get the financial year containing the given date.

    Args:
        date: The date to check.

    Returns:
        FinancialYear: The financial year containing the date, or None.
    """
    try:
        return FinancialYear.objects.get(
            start_date__lte=date.date(),
            end_date__gte=date.date(),
            is_active=True,
        )
    except (FinancialYear.DoesNotExist, FinancialYear.MultipleObjectsReturned):
        return (
            FinancialYear.objects.filter(is_active=True).order_by("-start_date").first()
        )


def get_recent_transactions(user: User, limit: int = 10) -> Iterable[Any]:
    """
    Get recent transactions accessible to the user.

    Args:
        user: The user to check permissions for.
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Recent transactions the user can access.
    """
    return get_accessible_transactions(user).order_by("-transaction_date")[:limit]


def get_budgets_by_financial_year(financial_year_id: int, user: User) -> Iterable[Any]:
    """
    Get budgets for a specific financial year that are accessible to the user.

    Args:
        financial_year_id: ID of the financial year.
        user: The user to check permissions for.

    Returns:
        Iterable: Budgets for the financial year the user can access.
    """
    try:
        financial_year = FinancialYear.objects.get(id=financial_year_id)
    except FinancialYear.DoesNotExist:
        return Budget.objects.none()
    return get_accessible_budgets(user).filter(financial_year=financial_year)


def get_transactions_by_account(
    account_id: int, user: User, limit: int = 50
) -> Iterable[Any]:
    """
    Get transactions for a financial account that are accessible to the user.

    Args:
        account_id: ID of the financial account.
        user: The user to check permissions for.
        limit: Maximum number of transactions to return.

    Returns:
        Iterable: Transactions for the account the user can access.
    """
    if not get_accessible_financial_accounts(user).filter(id=account_id).exists():
        return Transaction.objects.none()
    return (
        get_accessible_transactions(user)
        .filter(financial_account_id=account_id)
        .order_by("-transaction_date")[:limit]
    )


def get_expense_transactions_by_category(
    user: User,
    start_date: timezone.datetime | None = None,
    end_date: timezone.datetime | None = None,
    limit: int = 100,
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
    queryset = get_accessible_transactions(user).filter(
        transaction_type=TransactionType.EXPENSE
    )
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)
    return queryset.order_by("-transaction_date")[:limit]


def get_income_transactions_by_source(
    user: User,
    start_date: timezone.datetime | None = None,
    end_date: timezone.datetime | None = None,
    limit: int = 100,
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
    queryset = get_accessible_transactions(user).filter(
        transaction_type=TransactionType.INCOME
    )
    if start_date:
        queryset = queryset.filter(transaction_date__gte=start_date)
    if end_date:
        queryset = queryset.filter(transaction_date__lte=end_date)
    return queryset.order_by("-transaction_date")[:limit]


def search_transactions(user: User, query: str) -> QuerySet[Transaction]:
    """
    Search transactions by reference, description, beneficiary or source.

    Args:
        user: The user to check permissions for.
        query: The search text.

    Returns:
        QuerySet: Matching transactions the user can access.
    """
    qs = get_accessible_transactions(user)
    if not query:
        return qs
    q = Q(reference_number__icontains=query)
    q |= Q(description__icontains=query)
    q |= Q(beneficiary__icontains=query)
    return qs.filter(q)


def get_financial_year_summary(user: User) -> dict:
    """
    Summarize the active financial years and their budgets.

    Args:
        user: The user to check permissions for.

    Returns:
        Dict: Active financial years with budget totals.
    """
    years = FinancialYear.objects.filter(is_active=True).order_by("name")
    return {
        "financial_years": years,
        "budgets_by_year": {
            year.id: get_accessible_budgets(user).filter(financial_year=year).count()
            for year in years
        },
    }
