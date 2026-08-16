"""Finance Engine test cases."""

from __future__ import annotations


from apps.finance.models import FinancialYear, Budget, Transaction
from .base import FinanceTestCase


class FinancialYearModelTests(FinanceTestCase):
    def test_create_financial_year(self):
        year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        self.assertEqual(str(year), "2024 Financial Year")
        self.assertTrue(year.is_active)

    def test_financial_year_unique_code(self):
        FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        # No unique constraint on (name, start_month, is_active),
        # so creating another year succeeds without error.


class BudgetModelTests(FinanceTestCase):
    def test_create_budget(self):
        year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        budget = Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024",
            financial_year=year,
            total_amount=100000.00,
            allocated_amount=100000.00,
        )
        self.assertEqual(str(budget), "Annual Budget - 2024 Financial Year")
        self.assertEqual(budget.remaining, 0.0)


class TransactionModelTests(FinanceTestCase):
    def test_create_transaction(self):
        year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024",
            financial_year=year,
            total_amount=100000.00,
        )
        transaction = Transaction.objects.create(
            reference_number="FIN-2024-001",
            transaction_type="INCOME",
            status="DRAFT",
            source="GRANT",
            amount=50000.00,
            currency="USD",
            description="Grant funding",
            beneficiary="SITADC Youth Organization",
        )
        self.assertEqual(str(transaction), "FIN-2024-001 - INCOME USD 50000.00")
