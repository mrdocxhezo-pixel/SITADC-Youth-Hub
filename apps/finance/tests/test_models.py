"""Finance Engine model tests."""

from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.finance.models import (
    Budget,
    BudgetAllocation,
    Donor,
    FinancialAccount,
    FinancialYear,
    Grant,
    Transaction,
)


class FinancialYearModelTests(TestCase):
    def test_create_financial_year(self):
        year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        self.assertEqual(str(year), "2024 Financial Year")
        self.assertTrue(year.is_active)

    def test_financial_year_name_is_unique(self):
        FinancialYear.objects.create(name="2024 Financial Year", start_month=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FinancialYear.objects.create(name="2024 Financial Year", start_month=2)


class BudgetModelTests(TestCase):
    def setUp(self):
        self.year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )

    def test_create_budget(self):
        budget = Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024",
            financial_year=self.year,
            total_amount=Decimal("100000.00"),
            allocated_amount=Decimal("100000.00"),
        )
        self.assertEqual(
            str(budget), "Annual Budget - 2024 Financial Year (Annual Budget)"
        )
        self.assertEqual(budget.remaining, 100000.0)
        self.assertEqual(budget.variance_percentage, -100.0)

    def test_budget_remaining_uses_revised_amount(self):
        budget = Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024-R",
            financial_year=self.year,
            total_amount=Decimal("100000.00"),
            spent_amount=Decimal("40000.00"),
            is_revised=True,
            revised_amount=Decimal("120000.00"),
        )
        self.assertEqual(budget.remaining, 80000.0)

    def test_get_variance(self):
        budget = Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024-V",
            financial_year=self.year,
            total_amount=Decimal("100000.00"),
            allocated_amount=Decimal("80000.00"),
            spent_amount=Decimal("60000.00"),
        )
        variance = budget.get_variance()
        self.assertEqual(variance["budgeted"], Decimal("100000.00"))
        self.assertEqual(variance["actual"], Decimal("60000.00"))
        self.assertEqual(variance["variance"], Decimal("40000.00"))


class TransactionModelTests(TestCase):
    def test_create_transaction(self):
        transaction = Transaction.objects.create(
            reference_number="FIN-2024-001",
            transaction_type="INCOME",
            status="DRAFT",
            source="GRANT",
            amount=Decimal("50000.00"),
            currency="USD",
            description="Grant funding",
            beneficiary="SITADC Youth Organization",
        )
        self.assertEqual(str(transaction), "FIN-2024-001 - Income 50000.00 USD")

    def test_transaction_requires_unique_reference(self):
        Transaction.objects.create(
            reference_number="FIN-2024-002",
            transaction_type="INCOME",
            status="DRAFT",
            source="GRANT",
            amount=Decimal("50000.00"),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transaction.objects.create(
                reference_number="FIN-2024-002",
                transaction_type="INCOME",
                status="DRAFT",
                source="GRANT",
                amount=Decimal("10000.00"),
            )


class FinancialAccountModelTests(TestCase):
    def test_account_balance_after_posted_transactions(self):
        account = FinancialAccount.objects.create(
            name="Main Operations Account",
            code="ACC-001",
            account_type="ASSET",
            currency="USD",
            opening_balance=Decimal("1000.00"),
        )
        Transaction.objects.create(
            reference_number="FIN-2024-010",
            transaction_type="INCOME",
            status="POSTED",
            source="DONATION",
            amount=Decimal("500.00"),
            financial_account=account,
        )
        Transaction.objects.create(
            reference_number="FIN-2024-011",
            transaction_type="EXPENSE",
            status="POSTED",
            source="OTHER",
            amount=Decimal("200.00"),
            financial_account=account,
        )
        Transaction.objects.create(
            reference_number="FIN-2024-012",
            transaction_type="INCOME",
            status="DRAFT",
            source="DONATION",
            amount=Decimal("999.00"),
            financial_account=account,
        )
        self.assertEqual(account.get_current_balance(), Decimal("1300.00"))


class GrantModelTests(TestCase):
    def test_remaining_amount(self):
        grant = Grant.objects.create(
            name="Youth Skills Grant",
            grant_number="GRANT-001",
            funding_agency="Global Fund",
            grant_type="PROJECT",
            amount_awarded=Decimal("50000.00"),
            disbursed_amount=Decimal("15000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
        )
        self.assertEqual(grant.remaining_amount, Decimal("35000.00"))


class BudgetAllocationModelTests(TestCase):
    def setUp(self):
        self.year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        self.budget = Budget.objects.create(
            name="Annual Budget",
            code="BUD-2024",
            financial_year=self.year,
            total_amount=Decimal("100000.00"),
        )

    def test_create_allocation(self):
        allocation = BudgetAllocation.objects.create(
            budget=self.budget,
            program="Education",
            line_item="Textbooks",
            allocated_amount=Decimal("20000.00"),
            spent_amount=Decimal("8000.00"),
            percentage=20,
        )
        self.assertEqual(
            str(allocation),
            "Annual Budget - 2024 Financial Year (Annual Budget) - Education",
        )

    def test_allocation_unique_together(self):
        BudgetAllocation.objects.create(
            budget=self.budget,
            program="Education",
            project="",
            allocated_amount=Decimal("20000.00"),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            BudgetAllocation.objects.create(
                budget=self.budget,
                program="Education",
                project="",
                allocated_amount=Decimal("20000.00"),
            )


class DonorModelTests(TestCase):
    def test_donor_string_representation(self):
        donor = Donor.objects.create(
            name="UNICEF", donor_number="DON-001", donor_type="INTERNATIONAL_ORG"
        )
        self.assertEqual(str(donor), "UNICEF (DON-001)")
