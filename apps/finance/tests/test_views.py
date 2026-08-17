"""Finance Engine URL and view smoke tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class FinanceViewSmokeTests(TestCase):
    """All finance list and report URLs must render for a privileged user."""

    URL_NAMES = (
        "dashboard",
        "financial_account_list",
        "financial_account_create",
        "bank_account_list",
        "petty_cash_list",
        "financial_year_list",
        "grant_list",
        "donor_list",
        "sponsor_list",
        "fundraising_campaign_list",
        "procurement_financial_tracking_list",
        "asset_financial_tracking_list",
        "financial_forecast_list",
        "budget_list",
        "transaction_list",
        "budget_allocation_list",
        "reports_income_statement",
        "reports_balance_sheet",
        "reports_cash_flow",
        "reports_grant_summary",
        "analytics_income_trends",
        "analytics_expense_trends",
        "analytics_budget_variance",
        "analytics_funding_sources",
        "budgeting_summary",
        "budgeting_variance_report",
        "transactions_summary",
        "transactions_income",
        "transactions_expense",
        "grants_summary",
        "grants_funding_trends",
        "donors_summary",
        "donors_giving_trends",
        "sponsors_summary",
        "sponsors_trends",
        "fundraising_summary",
        "fundraising_trends",
        "fundraising_performance",
    )

    def setUp(self):
        self.user = User.objects.create_superuser(
            username="view-admin", email="view@test.local", password="pw"
        )
        self.client.force_login(self.user)

    def test_all_finance_urls_render(self):
        for name in self.URL_NAMES:
            with self.subTest(url=name):
                url = reverse(f"finance:{name}")
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code, 200, f"{name} returned {response.status_code}"
                )

    def test_login_required(self):
        self.client.logout()
        url = reverse("finance:financial_account_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
