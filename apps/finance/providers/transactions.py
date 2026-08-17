"""Finance Engine transactions providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from apps.finance.selectors import (
    get_accessible_financial_accounts,
    get_accessible_transactions,
)

User = get_user_model()


class TransactionsProvider:
    """Provider for transactions data."""

    def __init__(self, user: Any):
        """
        Initialize the transactions provider.

        Args:
            user: The user requesting the transactions data.
        """
        self.user = user

    def get_transaction_summary(
        self,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get transaction summary for a period.

        Args:
            start_date: Start date for the period (optional).
            end_date: End date for the period (optional).

        Returns:
            Dict containing transaction summary data.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        # Get transactions for the period
        transactions = get_accessible_transactions(self.user).filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            status="POSTED",  # Only count posted transactions for financial reporting
        )

        # Overall statistics
        total_income = transactions.filter(transaction_type="INCOME").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        total_expenses = transactions.filter(transaction_type="EXPENSE").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

        net_income = total_income - total_expenses

        transaction_count = transactions.count()
        income_count = transactions.filter(transaction_type="INCOME").count()
        expense_count = transactions.filter(transaction_type="EXPENSE").count()

        # By transaction type
        by_type = (
            transactions.values("transaction_type")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        # By source
        by_source = (
            transactions.values("source")
            .annotate(total=Sum("amount"), count=Count("id"))
            .order_by("-total")
        )

        # Monthly trend
        monthly_data = []
        current_date = start_date
        while current_date <= end_date:
            period_start = current_date
            period_end = min(current_date + timezone.timedelta(days=30), end_date)

            period_transactions = transactions.filter(
                transaction_date__gte=period_start, transaction_date__lte=period_end
            )

            period_income = period_transactions.filter(
                transaction_type="INCOME"
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            period_expenses = period_transactions.filter(
                transaction_type="EXPENSE"
            ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

            monthly_data.append(
                {
                    "month": period_start.strftime("%Y-%m"),
                    "income": period_income,
                    "expenses": period_expenses,
                    "net": period_income - period_expenses,
                    "transaction_count": period_transactions.count(),
                }
            )

            current_date = period_end + timezone.timedelta(days=1)

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "summary": {
                "total_income": total_income,
                "total_expenses": total_expenses,
                "net_income": net_income,
                "transaction_count": transaction_count,
                "income_count": income_count,
                "expense_count": expense_count,
            },
            "by_type": [
                {
                    "type": item["transaction_type"],
                    "total": item["total"],
                    "count": item["count"],
                }
                for item in by_type
            ],
            "by_source": [
                {
                    "source": item["source"],
                    "total": item["total"],
                    "count": item["count"],
                }
                for item in by_source
            ],
            "monthly_trend": monthly_data,
        }

    def get_income_transactions(
        self,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get income transactions.

        Args:
            start_date: Start date for filtering (optional).
            end_date: End date for filtering (optional).
            limit: Maximum number of transactions to return.

        Returns:
            List of income transaction dictionaries.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        transactions = (
            get_accessible_transactions(self.user)
            .filter(
                transaction_type="INCOME",
                status="POSTED",
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
            )
            .order_by("-transaction_date")[:limit]
        )

        return [
            {
                "id": txn.id,
                "reference_number": txn.reference_number,
                "date": txn.transaction_date,
                "source": txn.get_source_display(),
                "amount": txn.amount,
                "currency": txn.currency,
                "description": txn.description,
                "financial_account": (
                    txn.financial_account.name if txn.financial_account else None
                ),
                "budget": txn.budget.name if txn.budget else None,
            }
            for txn in transactions
        ]

    def get_expense_transactions(
        self,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get expense transactions.

        Args:
            start_date: Start date for filtering (optional).
            end_date: End date for filtering (optional).
            limit: Maximum number of transactions to return.

        Returns:
            List of expense transaction dictionaries.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        transactions = (
            get_accessible_transactions(self.user)
            .filter(
                transaction_type="EXPENSE",
                status="POSTED",
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
            )
            .order_by("-transaction_date")[:limit]
        )

        return [
            {
                "id": txn.id,
                "reference_number": txn.reference_number,
                "date": txn.transaction_date,
                "source": txn.get_source_display(),
                "amount": txn.amount,
                "currency": txn.currency,
                "description": txn.description,
                "financial_account": (
                    txn.financial_account.name if txn.financial_account else None
                ),
                "budget": txn.budget.name if txn.budget else None,
            }
            for txn in transactions
        ]

    def get_transactions_by_account(
        self,
        account_id: int,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Get transactions for a specific financial account.

        Args:
            account_id: ID of the financial account.
            start_date: Start date for filtering (optional).
            end_date: End date for filtering (optional).
            limit: Maximum number of transactions to return.

        Returns:
            List of transaction dictionaries for the account.
        """
        FinancialAccount = django_apps.get_model("finance", "FinancialAccount")

        # Check if user can access the account
        accessible_accounts = get_accessible_financial_accounts(self.user)
        if not accessible_accounts.filter(id=account_id).exists():
            raise PermissionError(
                "You do not have permission to access this financial account."
            )

        if not FinancialAccount.objects.filter(id=account_id).exists():
            raise ValueError(f"Financial account with ID {account_id} does not exist.")

        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        # Get transactions for this account
        # Assuming there's a way to link transactions to financial accounts
        # This would depend on your specific implementation
        transactions = (
            get_accessible_transactions(self.user)
            .filter(
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
                status="POSTED",
            )
            .order_by("-transaction_date")[:limit]
        )

        # Filter transactions that belong to this account
        # This is a simplified version - in practice, you'd have a direct relationship
        account_transactions = []
        for txn in transactions:
            # Check if this transaction is related to the account
            # This would depend on your data model
            if (
                hasattr(txn, "financial_account")
                and txn.financial_account_id == account_id
            ):
                account_transactions.append(
                    {
                        "id": txn.id,
                        "reference_number": txn.reference_number,
                        "date": txn.transaction_date,
                        "source": txn.get_source_display(),
                        "amount": txn.amount,
                        "currency": txn.currency,
                        "description": txn.description,
                        "budget": txn.budget.name if txn.budget else None,
                    }
                )

        return account_transactions[:limit]

    def get_recent_transactions(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent transactions.

        Args:
            limit: Maximum number of transactions to return.

        Returns:
            List of recent transaction dictionaries.
        """
        transactions = (
            get_accessible_transactions(self.user)
            .filter(status="POSTED")
            .order_by("-transaction_date")[:limit]
        )

        return [
            {
                "id": txn.id,
                "reference_number": txn.reference_number,
                "date": txn.transaction_date,
                "type": txn.get_transaction_type_display(),
                "source": txn.get_source_display(),
                "amount": txn.amount,
                "currency": txn.currency,
                "description": txn.description[:100]
                + ("..." if len(txn.description) > 100 else ""),
                "financial_account": (
                    txn.financial_account.name if txn.financial_account else None
                ),
                "budget": txn.budget.name if txn.budget else None,
            }
            for txn in transactions
        ]

    def get_large_transactions(
        self,
        threshold_amount: Decimal,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Get transactions above a certain amount threshold.

        Args:
            threshold_amount: Minimum transaction amount to include.
            start_date: Start date for filtering (optional).
            end_date: End date for filtering (optional).
            limit: Maximum number of transactions to return.

        Returns:
            List of large transaction dictionaries.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        transactions = (
            get_accessible_transactions(self.user)
            .filter(
                amount__gte=threshold_amount,
                transaction_date__gte=start_date,
                transaction_date__lte=end_date,
                status="POSTED",
            )
            .order_by("-amount")[:limit]
        )

        return [
            {
                "id": txn.id,
                "reference_number": txn.reference_number,
                "date": txn.transaction_date,
                "type": txn.get_transaction_type_display(),
                "source": txn.get_source_display(),
                "amount": txn.amount,
                "currency": txn.currency,
                "description": txn.description,
                "financial_account": (
                    txn.financial_account.name if txn.financial_account else None
                ),
                "budget": txn.budget.name if txn.budget else None,
            }
            for txn in transactions
        ]

    def get_transaction_trends(
        self, months: int = 12, transaction_type: str | None = None
    ) -> dict[str, Any]:
        """
        Get transaction trends over time.

        Args:
            months: Number of months to look back.
            transaction_type: Type of transaction to filter by (optional).

        Returns:
            Dict containing transaction trends data.
        """
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30 * months)

        # Base queryset
        transactions_qs = get_accessible_transactions(self.user).filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            status="POSTED",
        )

        # Filter by transaction type if specified
        if transaction_type:
            transactions_qs = transactions_qs.filter(transaction_type=transaction_type)

        # Group by month
        monthly_data = defaultdict(lambda: {"amount": Decimal("0"), "count": 0})

        for txn in transactions_qs:
            key = txn.transaction_date.strftime("%Y-%m")
            monthly_data[key]["amount"] += txn.amount
            monthly_data[key]["count"] += 1

        # Sort by date
        sorted_data = sorted(monthly_data.items())

        return {
            "period_type": "monthly",
            "transaction_type": transaction_type or "all",
            "start_date": start_date,
            "end_date": end_date,
            "data": [
                {
                    "month": month,
                    "amount": data["amount"],
                    "transaction_count": data["count"],
                }
                for month, data in sorted_data
            ],
            "total_amount": sum(data["amount"] for data in monthly_data.values()),
            "average_monthly_amount": (
                sum(data["amount"] for data in monthly_data.values())
                / len(monthly_data)
                if monthly_data
                else Decimal("0")
            ),
        }
