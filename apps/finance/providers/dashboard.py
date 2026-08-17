"""Finance Engine dashboard providers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from apps.finance.selectors import (
    get_accessible_budgets,
    get_accessible_donors,
    get_accessible_financial_accounts,
    get_accessible_fundraising_campaigns,
    get_accessible_grants,
    get_accessible_sponsors,
    get_accessible_transactions,
)

User = get_user_model()


class FinanceDashboardProvider:
    """Provider for finance dashboard data."""

    def __init__(self, user: Any):
        """
        Initialize the dashboard provider.

        Args:
            user: The user requesting the dashboard data.
        """
        self.user = user

    def get_financial_summary(self) -> dict[str, Any]:
        """
        Get financial summary data for the dashboard.

        Returns:
            Dict containing financial summary information.
        """
        # Get accessible financial accounts
        accounts = get_accessible_financial_accounts(self.user)
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")

        for account in accounts:
            balance = account.get_current_balance()
            if account.account_type in ["ASSET"]:
                total_assets += balance
            elif account.account_type in ["LIABILITY"]:
                total_liabilities += balance

        net_position = total_assets - total_liabilities

        # Get recent transactions
        recent_transactions = self.get_recent_transactions(limit=5)

        # Get budget status
        budget_status = self.get_budget_status()

        # Get funding sources
        funding_sources = self.get_funding_sources()

        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "net_position": net_position,
            "recent_transactions": recent_transactions,
            "budget_status": budget_status,
            "funding_sources": funding_sources,
            "last_updated": timezone.now(),
        }

    def get_budget_overview(self) -> dict[str, Any]:
        """
        Get budget overview data for the dashboard.

        Returns:
            Dict containing budget overview information.
        """
        budgets = get_accessible_budgets(self.user)

        total_budgeted = Decimal("0")
        total_actual = Decimal("0")
        budget_details = []

        for budget in budgets:
            variance_data = budget.get_variance()  # Assuming this method exists
            total_budgeted += budget.total_amount
            total_actual += variance_data.get("actual", Decimal("0"))

            budget_details.append(
                {
                    "id": budget.id,
                    "name": budget.name,
                    "code": budget.code,
                    "total_amount": budget.total_amount,
                    "actual_amount": variance_data.get("actual", Decimal("0")),
                    "variance": variance_data.get("variance", Decimal("0")),
                    "variance_percentage": variance_data.get(
                        "variance_percentage", Decimal("0")
                    ),
                    "status": (
                        "on_track"
                        if variance_data.get("variance_percentage", Decimal("0")) >= -5
                        else (
                            "overrun"
                            if variance_data.get("variance_percentage", Decimal("0"))
                            < -10
                            else "caution"
                        )
                    ),
                }
            )

        total_variance = total_budgeted - total_actual
        variance_percentage = (
            (total_variance / total_budgeted * 100)
            if total_budgeted > 0
            else Decimal("0")
        )

        return {
            "total_budgeted": total_budgeted,
            "total_actual": total_actual,
            "total_variance": total_variance,
            "variance_percentage": variance_percentage,
            "budgets": budget_details,
        }

    def get_funding_overview(self) -> dict[str, Any]:
        """
        Get funding overview data for the dashboard.

        Returns:
            Dict containing funding overview information.
        """
        # Get grants
        grants = get_accessible_grants(self.user)
        total_granted = grants.aggregate(total=Sum("amount_awarded"))[
            "total"
        ] or Decimal("0")
        total_disbursed = grants.aggregate(total=Sum("disbursed_amount"))[
            "total"
        ] or Decimal("0")
        total_grant_balance = total_granted - total_disbursed

        # Get donors
        donors = get_accessible_donors(self.user)
        total_donations = donors.aggregate(total=Sum("total_donated"))[
            "total"
        ] or Decimal("0")

        # Get sponsors
        sponsors = get_accessible_sponsors(self.user)
        total_sponsorship = sponsors.aggregate(total=Sum("sponsored_amount"))[
            "total"
        ] or Decimal("0")

        # Get fundraising campaigns
        campaigns = get_accessible_fundraising_campaigns(self.user)
        total_pledged = campaigns.aggregate(total=Sum("target_amount"))[
            "total"
        ] or Decimal("0")
        total_raised = campaigns.aggregate(total=Sum("amount_raised"))[
            "total"
        ] or Decimal("0")

        return {
            "grants": {
                "total_granted": total_granted,
                "total_disbursed": total_disbursed,
                "total_balance": total_grant_balance,
                "count": grants.count(),
            },
            "donors": {
                "total_contributions": total_donations,
                "count": donors.count(),
            },
            "sponsors": {
                "total_contributions": total_sponsorship,
                "count": sponsors.count(),
            },
            "fundraising": {
                "total_pledged": total_pledged,
                "total_raised": total_raised,
                "count": campaigns.count(),
            },
        }

    def get_recent_transactions(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent transactions for the dashboard.

        Args:
            limit: Maximum number of transactions to return.

        Returns:
            List of recent transaction dictionaries.
        """
        transactions = get_accessible_transactions(self.user).order_by(
            "-transaction_date"
        )[:limit]

        transaction_list = []
        for transaction in transactions:
            transaction_list.append(
                {
                    "id": transaction.id,
                    "reference_number": transaction.reference_number,
                    "date": transaction.transaction_date,
                    "type": transaction.get_transaction_type_display(),
                    "source": transaction.get_source_display(),
                    "amount": transaction.amount,
                    "currency": transaction.currency,
                    "status": transaction.get_status_display(),
                    "description": transaction.description[:100]
                    + ("..." if len(transaction.description) > 100 else ""),
                }
            )

        return transaction_list

    def get_budget_status(self) -> dict[str, Any]:
        """
        Get budget status summary.

        Returns:
            Dict containing budget status information.
        """
        budgets = get_accessible_budgets(self.user)

        on_track = 0
        caution = 0
        overrun = 0

        for budget in budgets:
            variance_data = budget.get_variance()
            variance_pct = variance_data.get("variance_percentage", Decimal("0"))

            if variance_pct >= -5:
                on_track += 1
            elif variance_pct >= -10:
                caution += 1
            else:
                overrun += 1

        total = budgets.count()

        return {
            "on_track": on_track,
            "caution": caution,
            "overrun": overrun,
            "total": total,
            "on_track_percentage": (
                (on_track / total * 100) if total > 0 else Decimal("0")
            ),
        }

    def get_funding_sources(self) -> list[dict[str, Any]]:
        """
        Get funding sources breakdown.

        Returns:
            List of funding source dictionaries.
        """
        sources = []

        # Grants
        grants = get_accessible_grants(self.user)
        grant_total = grants.aggregate(total=Sum("amount_awarded"))["total"] or Decimal(
            "0"
        )
        if grant_total > 0:
            sources.append(
                {
                    "type": "grant",
                    "name": "Grants",
                    "amount": grant_total,
                    "count": grants.count(),
                    "color": "#3b82f6",  # Blue
                }
            )

        # Donations
        donors = get_accessible_donors(self.user)
        donation_total = donors.aggregate(total=Sum("total_donated"))[
            "total"
        ] or Decimal("0")
        if donation_total > 0:
            sources.append(
                {
                    "type": "donation",
                    "name": "Donations",
                    "amount": donation_total,
                    "count": donors.count(),
                    "color": "#10b981",  # Green
                }
            )

        # Sponsorships
        sponsors = get_accessible_sponsors(self.user)
        sponsorship_total = sponsors.aggregate(total=Sum("sponsored_amount"))[
            "total"
        ] or Decimal("0")
        if sponsorship_total > 0:
            sources.append(
                {
                    "type": "sponsorship",
                    "name": "Sponsorships",
                    "amount": sponsorship_total,
                    "count": sponsors.count(),
                    "color": "#f59e0b",  # Amber
                }
            )

        # Fundraising
        campaigns = get_accessible_fundraising_campaigns(self.user)
        fundraising_total = campaigns.aggregate(total=Sum("amount_raised"))[
            "total"
        ] or Decimal("0")
        if fundraising_total > 0:
            sources.append(
                {
                    "type": "fundraising",
                    "name": "Fundraising",
                    "amount": fundraising_total,
                    "count": campaigns.count(),
                    "color": "#8b5cf6",  # Violet
                }
            )

        # Income from other sources
        # This would typically come from transactions
        income_transactions = get_accessible_transactions(self.user).filter(
            transaction_type="INCOME", status="POSTED"
        )
        other_income = income_transactions.aggregate(total=Sum("amount"))[
            "total"
        ] or Decimal("0")
        if other_income > 0:
            sources.append(
                {
                    "type": "other_income",
                    "name": "Other Income",
                    "amount": other_income,
                    "count": income_transactions.count(),
                    "color": "#6b7280",  # Gray
                }
            )

        return sources
