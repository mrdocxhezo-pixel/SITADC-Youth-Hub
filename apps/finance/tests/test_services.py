"""Finance Engine service tests."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.finance.constants import TransactionStatus, TransactionType
from apps.finance.exceptions import (
    BudgetExceededError,
    InsufficientFundsError,
    InvalidAccountError,
    InvalidTransactionError,
)
from apps.finance.models import FinancialYear
from apps.finance.services import (
    BudgetService,
    DonorService,
    FinancialAccountService,
    GrantService,
    TransactionService,
)

User = get_user_model()


class FinancialAccountServiceTests(TestCase):
    def test_create_account(self):
        account = FinancialAccountService.create_account(
            name="Petty Cash",
            code="ACC-300",
            account_type="ASSET",
            currency="USD",
            opening_balance=Decimal("200.00"),
        )
        self.assertEqual(account.name, "Petty Cash")
        self.assertEqual(account.get_current_balance(), Decimal("200.00"))

    def test_get_account_balance_raises_for_missing(self):
        with self.assertRaises(InvalidAccountError):
            FinancialAccountService.get_account_balance(99999)

    def test_deactivate_account(self):
        account = FinancialAccountService.create_account(
            name="Savings", code="ACC-301", account_type="ASSET"
        )
        result = FinancialAccountService.deactivate_account(account.id)
        self.assertFalse(result.is_active)


class BudgetServiceTests(TestCase):
    def setUp(self):
        self.year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )

    def test_create_budget(self):
        budget = BudgetService.create_budget(
            name="Annual Budget",
            code="BUD-SVC-001",
            financial_year_id=self.year.id,
            total_amount=Decimal("100000.00"),
        )
        self.assertEqual(budget.code, "BUD-SVC-001")

    def test_create_budget_raises_for_missing_year(self):
        with self.assertRaises(ValueError):
            BudgetService.create_budget(
                name="Annual Budget",
                code="BUD-SVC-002",
                financial_year_id=99999,
                total_amount=Decimal("100000.00"),
            )

    def test_allocate_to_budget_line(self):
        budget = BudgetService.create_budget(
            name="Annual Budget",
            code="BUD-SVC-003",
            financial_year_id=self.year.id,
            total_amount=Decimal("100000.00"),
        )
        BudgetService.allocate_to_budget_line(budget.id, Decimal("30000.00"))
        budget.refresh_from_db()
        self.assertEqual(budget.allocated_amount, Decimal("30000.00"))

    def test_allocate_exceeding_budget_raises(self):
        budget = BudgetService.create_budget(
            name="Annual Budget",
            code="BUD-SVC-004",
            financial_year_id=self.year.id,
            total_amount=Decimal("1000.00"),
        )
        with self.assertRaises(BudgetExceededError):
            BudgetService.allocate_to_budget_line(budget.id, Decimal("2000.00"))


class TransactionServiceTests(TestCase):
    def setUp(self):
        self.year = FinancialYear.objects.create(
            name="2024 Financial Year", start_month=1, is_active=True
        )
        self.user = User.objects.create_superuser(
            username="finance-user", email="u@test.local", password="pw"
        )

    def test_create_transaction(self):
        tx = TransactionService.create_transaction(
            reference_number="FIN-SVC-001",
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.DRAFT,
            source="GRANT",
            amount=Decimal("5000.00"),
            created_by=self.user,
        )
        self.assertEqual(tx.status, TransactionStatus.DRAFT)
        self.assertEqual(tx.created_by, self.user)

    def test_create_transaction_duplicate_reference_raises(self):
        TransactionService.create_transaction(
            reference_number="FIN-SVC-002",
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.DRAFT,
            source="GRANT",
            amount=Decimal("5000.00"),
        )
        with self.assertRaises(InvalidTransactionError):
            TransactionService.create_transaction(
                reference_number="FIN-SVC-002",
                transaction_type=TransactionType.INCOME,
                status=TransactionStatus.DRAFT,
                source="GRANT",
                amount=Decimal("5000.00"),
            )

    def test_create_transaction_invalid_account_raises(self):
        with self.assertRaises(InvalidAccountError):
            TransactionService.create_transaction(
                reference_number="FIN-SVC-003",
                transaction_type=TransactionType.INCOME,
                status=TransactionStatus.DRAFT,
                source="GRANT",
                amount=Decimal("5000.00"),
                financial_account_id=99999,
            )

    def test_post_transaction(self):
        tx = TransactionService.create_transaction(
            reference_number="FIN-SVC-004",
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.DRAFT,
            source="GRANT",
            amount=Decimal("5000.00"),
        )
        posted = TransactionService.post_transaction(tx.id, posted_by=self.user)
        self.assertEqual(posted.status, TransactionStatus.POSTED)
        self.assertEqual(posted.posted_by, self.user)
        self.assertIsNotNone(posted.posted_at)

    def test_post_non_postable_transaction_raises(self):
        tx = TransactionService.create_transaction(
            reference_number="FIN-SVC-005",
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.VOIDED,
            source="GRANT",
            amount=Decimal("5000.00"),
        )
        with self.assertRaises(InvalidTransactionError):
            TransactionService.post_transaction(tx.id)

    def test_void_transaction(self):
        tx = TransactionService.create_transaction(
            reference_number="FIN-SVC-006",
            transaction_type=TransactionType.EXPENSE,
            status=TransactionStatus.DRAFT,
            source="OTHER",
            amount=Decimal("100.00"),
        )
        TransactionService.post_transaction(tx.id)
        voided = TransactionService.void_transaction(
            tx.id, voided_by=self.user, reason="Duplicate"
        )
        self.assertEqual(voided.status, TransactionStatus.VOIDED)
        self.assertIn("VOIDED: Duplicate", voided.description)
        self.assertIsNotNone(voided.voided_at)

    def test_void_non_posted_transaction_raises(self):
        tx = TransactionService.create_transaction(
            reference_number="FIN-SVC-007",
            transaction_type=TransactionType.INCOME,
            status=TransactionStatus.DRAFT,
            source="GRANT",
            amount=Decimal("5000.00"),
        )
        with self.assertRaises(InvalidTransactionError):
            TransactionService.void_transaction(tx.id)


class GrantServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username="grant-user", email="g@test.local", password="pw"
        )

    def test_create_grant(self):
        grant = GrantService.create_grant(
            name="Youth Skills Grant",
            grant_number="GRANT-SVC-001",
            funding_agency="Global Fund",
            grant_type="PROJECT",
            amount_awarded=Decimal("50000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
            created_by=self.user,
        )
        self.assertEqual(grant.grant_number, "GRANT-SVC-001")
        self.assertEqual(grant.remaining_amount, Decimal("50000.00"))

    def test_create_grant_duplicate_number_raises(self):
        GrantService.create_grant(
            name="Grant A",
            grant_number="GRANT-SVC-002",
            funding_agency="Agency",
            grant_type="PROJECT",
            amount_awarded=Decimal("10000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
        )
        with self.assertRaises(InvalidTransactionError):
            GrantService.create_grant(
                name="Grant B",
                grant_number="GRANT-SVC-002",
                funding_agency="Agency",
                grant_type="PROJECT",
                amount_awarded=Decimal("10000.00"),
                award_date="2024-01-15",
                start_date="2024-02-01",
                end_date="2025-01-31",
            )

    def test_disburse_grant(self):
        grant = GrantService.create_grant(
            name="Youth Skills Grant",
            grant_number="GRANT-SVC-003",
            funding_agency="Global Fund",
            grant_type="PROJECT",
            amount_awarded=Decimal("10000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
        )
        updated_grant, tx = GrantService.disburse_grant(
            grant.id,
            amount=Decimal("2500.00"),
            transaction_reference="FIN-DISB-001",
            disbursed_by=self.user,
        )
        self.assertEqual(updated_grant.disbursed_amount, Decimal("2500.00"))
        self.assertEqual(tx.transaction_type, TransactionType.EXPENSE)
        self.assertEqual(tx.amount, Decimal("2500.00"))

    def test_disburse_grant_insufficient_funds_raises(self):
        grant = GrantService.create_grant(
            name="Youth Skills Grant",
            grant_number="GRANT-SVC-004",
            funding_agency="Global Fund",
            grant_type="PROJECT",
            amount_awarded=Decimal("1000.00"),
            award_date="2024-01-15",
            start_date="2024-02-01",
            end_date="2025-01-31",
        )
        with self.assertRaises(InsufficientFundsError):
            GrantService.disburse_grant(
                grant.id,
                amount=Decimal("5000.00"),
                transaction_reference="FIN-DISB-002",
            )


class DonorServiceTests(TestCase):
    def test_record_donation(self):
        donor = DonorService.create_donor(
            name="UNICEF", donor_number="DON-SVC-001", donor_type="INTERNATIONAL_ORG"
        )
        updated, tx = DonorService.record_donation(
            donor.id,
            amount=Decimal("7500.00"),
            transaction_reference="FIN-DON-001",
        )
        self.assertEqual(updated.total_donated, Decimal("7500.00"))
        self.assertEqual(updated.year_to_date_donated, Decimal("7500.00"))
        self.assertIsNotNone(updated.last_donation_date)
        self.assertEqual(tx.source, "DONATION")
        self.assertEqual(tx.amount, Decimal("7500.00"))
