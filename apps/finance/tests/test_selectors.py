"""Finance Engine selector tests."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finance.models import FinancialAccount, FinancialYear, Grant, Transaction
from apps.finance.selectors import (
    get_accessible_financial_accounts,
    get_accessible_transactions,
    get_financial_account_balance,
    get_grant_remaining_amount,
    get_recent_transactions,
    search_transactions,
)

User = get_user_model()


class FinanceSelectorTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username="finance-admin", email="admin@test.local", password="pw"
        )
        self.account = FinancialAccount.objects.create(
            name="Operations Account",
            code="ACC-100",
            account_type="ASSET",
            opening_balance=Decimal("5000.00"),
        )
        self.transaction = Transaction.objects.create(
            reference_number="FIN-2024-100",
            transaction_type="INCOME",
            status="POSTED",
            source="GRANT",
            amount=Decimal("1000.00"),
            description="Grant receipt",
            financial_account=self.account,
        )

    def test_superuser_sees_accounts(self):
        self.assertEqual(
            list(get_accessible_financial_accounts(self.superuser)), [self.account]
        )

    def test_anonymous_user_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser

        anonymous = AnonymousUser()
        self.assertFalse(anonymous.is_authenticated)
        self.assertEqual(list(get_accessible_transactions(anonymous)), [])

    def test_get_financial_account_balance(self):
        balance = get_financial_account_balance(self.account.id)
        self.assertEqual(balance, Decimal("6000.00"))

    def test_get_financial_account_balance_missing_account(self):
        self.assertEqual(get_financial_account_balance(99999), Decimal("0"))

    def test_get_recent_transactions(self):
        recent = get_recent_transactions(self.superuser, limit=5)
        self.assertEqual(list(recent), [self.transaction])

    def test_search_transactions_by_description(self):
        results = search_transactions(self.superuser, "grant")
        self.assertEqual(list(results), [self.transaction])

    def test_get_grant_remaining_amount(self):
        grant = Grant.objects.create(
            name="Youth Skills Grant",
            grant_number="GRANT-200",
            funding_agency="Global Fund",
            grant_type="PROJECT",
            amount_awarded=Decimal("10000.00"),
            disbursed_amount=Decimal("4000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
        )
        self.assertEqual(get_grant_remaining_amount(grant.id), Decimal("6000.00"))
        self.assertEqual(get_grant_remaining_amount(99999), Decimal("0"))

    def test_financial_year_for_date(self):
        year = FinancialYear.objects.create(
            name="2025 Financial Year",
            start_month=1,
            start_date="2025-01-01",
            end_date="2025-12-31",
            is_active=True,
        )
        from django.utils import timezone

        from apps.finance.selectors import get_financial_year_for_date

        found = get_financial_year_for_date(timezone.datetime(2025, 6, 15))
        self.assertEqual(found, year)
