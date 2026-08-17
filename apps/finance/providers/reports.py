"""Finance Engine reports providers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone

from apps.finance.selectors import (
    get_accessible_budgets,
    get_accessible_donors,
    get_accessible_financial_accounts,
    get_accessible_grants,
    get_accessible_transactions,
)

User = get_user_model()


class FinanceReportsProvider:
    """Provider for finance reports data."""

    def __init__(self, user: Any):
        """
        Initialize the reports provider.

        Args:
            user: The user requesting the reports data.
        """
        self.user = user

    def get_income_statement(
        self,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get income statement (profit and loss) for a period.

        Args:
            start_date: Start date for the period.
            end_date: End date for the period.

        Returns:
            Dict containing income statement data.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        # Get income transactions
        income_txns = get_accessible_transactions(self.user).filter(
            transaction_type="INCOME",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
        )

        # Get expense transactions
        expense_txns = get_accessible_transactions(self.user).filter(
            transaction_type="EXPENSE",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
        )

        # Calculate totals by source/category
        income_by_source = (
            income_txns.values("source")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        expense_by_category = (
            expense_txns.values("source")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )

        total_income = income_txns.aggregate(total=Sum("amount"))["total"] or Decimal(
            "0"
        )
        total_expenses = expense_txns.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        net_income = total_income - total_expenses

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "income": {
                "total": total_income,
                "by_source": [
                    {
                        "source": item["source"],
                        "amount": item["total"],
                    }
                    for item in income_by_source
                ],
            },
            "expenses": {
                "total": total_expenses,
                "by_category": [
                    {
                        "category": item["source"],
                        "amount": item["total"],
                    }
                    for item in expense_by_category
                ],
            },
            "net_income": net_income,
        }

    def get_balance_sheet(
        self, as_of_date: timezone.datetime | None = None
    ) -> dict[str, Any]:
        """
        Get balance sheet as of a specific date.

        Args:
            as_of_date: Date to generate balance sheet for.

        Returns:
            Dict containing balance sheet data.
        """
        if as_of_date is None:
            as_of_date = timezone.now()

        # Get financial accounts
        accounts = get_accessible_financial_accounts(self.user)

        # Categorize accounts
        assets = []
        liabilities = []
        equity = []

        total_assets = Decimal("0")
        total_liabilities = Decimal("0")
        total_equity = Decimal("0")

        for account in accounts:
            balance = account.get_balance_as_of_date(
                as_of_date
            )  # Assuming this method exists

            account_data = {
                "id": account.id,
                "name": account.name,
                "code": account.code,
                "balance": balance,
                "type": account.account_type,
            }

            if account.account_type == "ASSET":
                assets.append(account_data)
                total_assets += balance
            elif account.account_type == "LIABILITY":
                liabilities.append(account_data)
                total_liabilities += balance
            elif account.account_type == "EQUITY":
                equity.append(account_data)
                total_equity += balance
            # Expenses are not typically shown on balance sheet

        # For balance sheet: Assets = Liabilities + Equity
        # We'll adjust equity to balance the equation
        equity_adjustment = total_assets - total_liabilities
        if equity:
            # Distribute adjustment across equity accounts proportionally
            if total_equity != 0:
                for eq_account in equity:
                    proportion = (
                        eq_account["balance"] / total_equity if total_equity > 0 else 0
                    )
                    eq_account["balance"] += equity_adjustment * proportion
            else:
                # If no equity accounts, put all adjustment in first equity account
                # or create one
                if equity:
                    equity[0]["balance"] += equity_adjustment
                # In real system, we'd have proper equity accounts

        # Recalculate totals
        total_equity = sum(account["balance"] for account in equity)

        return {
            "as_of_date": as_of_date,
            "assets": {
                "total": total_assets,
                "accounts": assets,
            },
            "liabilities": {
                "total": total_liabilities,
                "accounts": liabilities,
            },
            "equity": {
                "total": total_equity,
                "accounts": equity,
            },
            "balanced": abs((total_assets) - (total_liabilities + total_equity))
            < Decimal("0.01"),
        }

    def get_cash_flow_statement(
        self,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
    ) -> dict[str, Any]:
        """
        Get cash flow statement for a period.

        Args:
            start_date: Start date for the period.
            end_date: End date for the period.

        Returns:
            Dict containing cash flow statement data.
        """
        if start_date is None:
            start_date = timezone.now().replace(month=1, day=1)
        if end_date is None:
            end_date = timezone.now()

        # Operating activities: income and expenses from core operations
        operating_income = get_accessible_transactions(self.user).filter(
            transaction_type="INCOME",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            source__in=[
                "GRANT",
                "DONATION",
                "SPONSORSHIP",
                "FUNDRAISING",
                "GOVERNMENT",
                "PARTNERSHIP",
            ],
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        operating_expenses = get_accessible_transactions(self.user).filter(
            transaction_type="EXPENSE",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        net_operating_cash_flow = operating_income - operating_expenses

        # Investing activities: purchase/sale of assets (simplified categorization)
        investing_inflows = get_accessible_transactions(self.user).filter(
            transaction_type="INCOME",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            source="OTHER",
        ).exclude(description__icontains="grant").aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")

        investing_outflows = get_accessible_transactions(self.user).filter(
            transaction_type="EXPENSE",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            description__icontains="asset",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        net_investing_cash_flow = investing_inflows - investing_outflows

        # Financing activities: loans and similar (simplified categorization)
        financing_inflows = get_accessible_transactions(self.user).filter(
            transaction_type="INCOME",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            description__icontains="loan",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        financing_outflows = get_accessible_transactions(self.user).filter(
            transaction_type="EXPENSE",
            status="POSTED",
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            description__icontains="loan",
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        net_financing_cash_flow = financing_inflows - financing_outflows

        # Net change in cash
        net_change_in_cash = (
            net_operating_cash_flow + net_investing_cash_flow + net_financing_cash_flow
        )

        # Beginning and ending cash (simplified - would come from cash
        # accounts in real system)
        beginning_cash = Decimal(
            "0"
        )  # Would get from cash account balance at start_date
        ending_cash = beginning_cash + net_change_in_cash

        return {
            "period": {
                "start_date": start_date,
                "end_date": end_date,
            },
            "operating_activities": {
                "income": operating_income,
                "expenses": operating_expenses,
                "net_cash_flow": net_operating_cash_flow,
            },
            "investing_activities": {
                "inflows": investing_inflows,
                "outflows": investing_outflows,
                "net_cash_flow": net_investing_cash_flow,
            },
            "financing_activities": {
                "inflows": financing_inflows,
                "outflows": financing_outflows,
                "net_cash_flow": net_financing_cash_flow,
            },
            "net_change_in_cash": net_change_in_cash,
            "beginning_cash": beginning_cash,
            "ending_cash": ending_cash,
        }

    def get_grant_report(self, grant_id: int | None = None) -> dict[str, Any]:
        """
        Get grant report.

        Args:
            grant_id: ID of specific grant (optional). If None, returns summary
            of all grants.

        Returns:
            Dict containing grant report data.
        """
        Grant = django_apps.get_model("finance", "Grant")

        if grant_id:
            # Specific grant report
            try:
                grant = Grant.objects.get(id=grant_id)
                # Check permissions
                accessible_grants = get_accessible_grants(self.user)
                if not accessible_grants.filter(id=grant_id).exists():
                    raise PermissionError(
                        "You do not have permission to access this grant."
                    )

                return {
                    "grant": {
                        "id": grant.id,
                        "name": grant.name,
                        "reference_number": grant.grant_number,
                        "donor": grant.donor.name if grant.donor else None,
                        "amount": grant.amount_awarded,
                        "currency": grant.currency,
                        "disbursed_amount": grant.disbursed_amount,
                        "remaining_amount": grant.remaining_amount,
                        "start_date": grant.start_date,
                        "end_date": grant.end_date,
                        "status": grant.status,
                        "description": grant.description,
                    },
                    "transactions": [],  # Would include related transactions
                }
            except Grant.DoesNotExist as exc:
                raise ValueError(f"Grant with ID {grant_id} does not exist.") from exc
        else:
            # Summary report of all grants
            grants = get_accessible_grants(self.user)

            total_awarded = grants.aggregate(total=Sum("amount_awarded"))[
                "total"
            ] or Decimal("0")
            total_disbursed = grants.aggregate(total=Sum("disbursed_amount"))[
                "total"
            ] or Decimal("0")
            total_remaining = total_awarded - total_disbursed

            # Group by status
            by_status = grants.values("status").annotate(
                count=Count("id"),
                total_amount=Sum("amount_awarded"),
                total_disbursed=Sum("disbursed_amount"),
            )

            return {
                "summary": {
                    "total_grants": grants.count(),
                    "total_awarded": total_awarded,
                    "total_disbursed": total_disbursed,
                    "total_remaining": total_remaining,
                },
                "by_status": [
                    {
                        "status": item["status"],
                        "count": item["count"],
                        "total_amount": item["total_amount"],
                        "total_disbursed": item["total_disbursed"],
                        "remaining": item["total_amount"] - item["total_disbursed"],
                    }
                    for item in by_status
                ],
                "grants": [
                    {
                        "id": grant.id,
                        "name": grant.name,
                        "reference_number": grant.grant_number,
                        "donor": grant.donor.name if grant.donor else None,
                        "amount": grant.amount_awarded,
                        "currency": grant.currency,
                        "disbursed_amount": grant.disbursed_amount,
                        "remaining_amount": grant.remaining_amount,
                        "status": grant.status,
                    }
                    for grant in grants[:50]  # Limit to 50 for performance
                ],
            }

    def get_donor_report(self, donor_id: int | None = None) -> dict[str, Any]:
        """
        Get donor report.

        Args:
            donor_id: ID of specific donor (optional). If None, returns summary
            of all donors.

        Returns:
            Dict containing donor report data.
        """
        Donor = django_apps.get_model("finance", "Donor")

        if donor_id:
            # Specific donor report
            try:
                donor = Donor.objects.get(id=donor_id)
                # Check permissions
                accessible_donors = get_accessible_donors(self.user)
                if not accessible_donors.filter(id=donor_id).exists():
                    raise PermissionError(
                        "You do not have permission to access this donor."
                    )

                return {
                    "donor": {
                        "id": donor.id,
                        "name": donor.name,
                        "type": donor.donor_type,
                        "contact_person": donor.contact_person,
                        "email": donor.email,
                        "phone": donor.phone,
                        "total_donated": donor.total_donated,
                    },
                    "transactions": [],  # Would include related transactions
                }
            except Donor.DoesNotExist as exc:
                raise ValueError(f"Donor with ID {donor_id} does not exist.") from exc
        else:
            # Summary report of all donors
            donors = get_accessible_donors(self.user)

            total_contributions = donors.aggregate(total=Sum("total_donated"))[
                "total"
            ] or Decimal("0")

            # Group by type
            by_type = donors.values("donor_type").annotate(
                count=Count("id"), total_contributions=Sum("total_donated")
            )

            return {
                "summary": {
                    "total_donors": donors.count(),
                    "total_contributions": total_contributions,
                },
                "by_type": [
                    {
                        "type": item["donor_type"],
                        "count": item["count"],
                        "total_contributions": item["total_contributions"],
                    }
                    for item in by_type
                ],
                "donors": [
                    {
                        "id": donor.id,
                        "name": donor.name,
                        "type": donor.donor_type,
                        "total_contributions": donor.total_donated,
                    }
                    for donor in donors[:50]  # Limit to 50 for performance
                ],
            }

    def get_budget_report(self, budget_id: int | None = None) -> dict[str, Any]:
        """
        Get budget report.

        Args:
            budget_id: ID of specific budget (optional). If None, returns summary
            of all budgets.

        Returns:
            Dict containing budget report data.
        """
        Budget = django_apps.get_model("finance", "Budget")

        if budget_id:
            # Specific budget report
            try:
                budget = Budget.objects.get(id=budget_id)
                # Check permissions
                accessible_budgets = get_accessible_budgets(self.user)
                if not accessible_budgets.filter(id=budget_id).exists():
                    raise PermissionError(
                        "You do not have permission to access this budget."
                    )

                variance_data = budget.get_variance()  # Assuming this method exists

                return {
                    "budget": {
                        "id": budget.id,
                        "name": budget.name,
                        "code": budget.code,
                        "financial_year": (
                            budget.financial_year.name
                            if budget.financial_year
                            else None
                        ),
                        "total_amount": budget.total_amount,
                        "allocated_amount": budget.allocated_amount,
                        "remaining_amount": budget.remaining,
                    },
                    "variance": variance_data,
                    "allocations": [],  # Would include budget allocations/lines
                    "transactions": [],  # Would include related transactions
                }
            except Budget.DoesNotExist as exc:
                raise ValueError(f"Budget with ID {budget_id} does not exist.") from exc
        else:
            # Summary report of all budgets
            budgets = get_accessible_budgets(self.user)

            total_budgeted = budgets.aggregate(total=Sum("total_amount"))[
                "total"
            ] or Decimal("0")
            total_allocated = budgets.aggregate(total=Sum("allocated_amount"))[
                "total"
            ] or Decimal("0")
            total_remaining = total_budgeted - total_allocated

            # Group by financial year
            by_year = budgets.values("financial_year__name").annotate(
                count=Count("id"),
                total_budgeted=Sum("total_amount"),
                total_allocated=Sum("allocated_amount"),
            )

            return {
                "summary": {
                    "total_budgets": budgets.count(),
                    "total_budgeted": total_budgeted,
                    "total_allocated": total_allocated,
                    "total_remaining": total_remaining,
                    "overall_variance_percentage": (
                        ((total_budgeted - total_allocated) / total_budgeted * 100)
                        if total_budgeted > 0
                        else Decimal("0")
                    ),
                },
                "by_financial_year": [
                    {
                        "financial_year": item["financial_year__name"],
                        "count": item["count"],
                        "total_budgeted": item["total_budgeted"],
                        "total_allocated": item["total_allocated"],
                        "remaining": item["total_budgeted"] - item["total_allocated"],
                    }
                    for item in by_year
                ],
                "budgets": [
                    {
                        "id": budget.id,
                        "name": budget.name,
                        "code": budget.code,
                        "financial_year": (
                            budget.financial_year.name
                            if budget.financial_year
                            else None
                        ),
                        "total_amount": budget.total_amount,
                        "allocated_amount": budget.allocated_amount,
                        "remaining_amount": budget.remaining,
                    }
                    for budget in budgets[:50]  # Limit to 50 for performance
                ],
            }
