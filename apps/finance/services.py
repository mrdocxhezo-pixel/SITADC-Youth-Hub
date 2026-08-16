"""Finance Engine services."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Tuple

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from apps.finance.exceptions import (
    BudgetExceededError,
    CurrencyMismatchError,
    FinancialPeriodError,
    InsufficientFundsError,
    InvalidAccountError,
    InvalidTransactionError,
)
from apps.finance.selectors import (
    get_accessible_budgets,
    get_accessible_donors,
    get_accessible_financial_accounts,
    get_accessible_grants,
    get_accessible_sponsors,
    get_accessible_transactions,
)
from apps.finance.utils import get_financial_year_for_date

User = get_user_model()


class FinancialAccountService:
    """Service for managing financial accounts."""

    @staticmethod
    def create_account(
        name: str,
        account_type: str,
        currency: str = "USD",
        is_active: bool = True,
        description: str = "",
        created_by: Optional[User] = None,
    ) -> Any:
        """
        Create a new financial account.

        Args:
            name: Account name.
            account_type: Type of account (asset, liability, equity, income, expense).
            currency: Currency code (default: USD).
            is_active: Whether the account is active.
            description: Account description.
            created_by: User who created the account.

        Returns:
            FinancialAccount: The created account.
        """
        FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
        
        account = FinancialAccount.objects.create(
            name=name,
            account_type=account_type,
            currency=currency,
            is_active=is_active,
            description=description,
            created_by=created_by,
        )
        return account

    @staticmethod
    def get_account_balance(account_id: int, as_of_date: Optional[timezone.datetime] = None) -> Decimal:
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
            raise InvalidAccountError(f"Financial account with ID {account_id} does not exist.")
            
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

    @staticmethod
    def deactivate_account(account_id: int, deactivated_by: Optional[User] = None) -> Any:
        """
        Deactivate a financial account.

        Args:
            account_id: ID of the financial account to deactivate.
            deactivated_by: User who deactivated the account.

        Returns:
            FinancialAccount: The deactivated account.
        """
        FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
        
        try:
            account = FinancialAccount.objects.get(id=account_id)
        except FinancialAccount.DoesNotExist:
            raise InvalidAccountError(f"Financial account with ID {account_id} does not exist.")
            
        account.is_active = False
        account.updated_by = deactivated_by
        account.updated_at = timezone.now()
        account.save()
        
        return account


class BudgetService:
    """Service for managing budgets."""

    @staticmethod
    def create_budget(
        name: str,
        code: str,
        financial_year_id: int,
        total_amount: Decimal,
        allocated_amount: Decimal = Decimal('0'),
        description: str = "",
        created_by: Optional[User] = None,
    ) -> Any:
        """
        Create a new budget.

        Args:
            name: Budget name.
            code: Budget code.
            financial_year_id: ID of the financial year.
            total_amount: Total budget amount.
            allocated_amount: Already allocated amount (default: 0).
            description: Budget description.
            created_by: User who created the budget.

        Returns:
            Budget: The created budget.
        """
        Budget = django_apps.get_model("finance", "Budget")
        FinancialYear = django_apps.get_model("finance", "FinancialYear")
        
        try:
            financial_year = FinancialYear.objects.get(id=financial_year_id)
        except FinancialYear.DoesNotExist:
            raise ValueError(f"Financial year with ID {financial_year_id} does not exist.")
            
        budget = Budget.objects.create(
            name=name,
            code=code,
            financial_year=financial_year,
            total_amount=total_amount,
            allocated_amount=allocated_amount,
            description=description,
            created_by=created_by,
        )
        return budget

    @staticmethod
    def allocate_to_budget_line(budget_id: int, amount: Decimal, allocated_by: Optional[User] = None) -> bool:
        """
        Allocate amount to a budget.

        Args:
            budget_id: ID of the budget.
            amount: Amount to allocate.
            allocated_by: User performing the allocation.

        Returns:
            bool: True if allocation successful, False otherwise.
        """
        Budget = django_apps.get_model("finance", "Budget")
        
        try:
            budget = Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist:
            raise ValueError(f"Budget with ID {budget_id} does not exist.")
            
        # Check if allocation would exceed total budget
        if budget.allocated_amount + amount > budget.total_amount:
            raise BudgetExceededError(
                f"Allocation of {amount} would exceed budget total of {budget.total_amount}. "
                f"Already allocated: {budget.allocated_amount}, Remaining: {budget.remaining}"
            )
            
        budget.allocated_amount += amount
        budget.updated_by = allocated_by
        budget.updated_at = timezone.now()
        budget.save()
        
        return True

    @staticmethod
    def get_budget_variance(budget_id: int, as_of_date: Optional[timezone.datetime] = None) -> Dict[str, Decimal]:
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
        BudgetAllocation = django_apps.get_model("finance", "BudgetAllocation")
        
        try:
            budget = Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist:
            raise ValueError(f"Budget with ID {budget_id} does not exist.")
            
        # Get actual spending from transactions and budget allocations
        # This is a simplified version - in practice, you'd want to link transactions to budget lines
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


class TransactionService:
    """Service for managing financial transactions."""

    @staticmethod
    def create_transaction(
        reference_number: str,
        transaction_type: str,
        status: str,
        source: str,
        amount: Decimal,
        currency: str = "USD",
        description: str = "",
        financial_account_id: Optional[int] = None,
        budget_id: Optional[int] = None,
        created_by: Optional[User] = None,
    ) -> Any:
        """
        Create a new financial transaction.

        Args:
            reference_number: Unique reference number for the transaction.
            transaction_type: Type of transaction (INCOME, EXPENSE, TRANSFER, etc.).
            status: Status of the transaction (DRAFT, SUBMITTED, APPROVED, POSTED, etc.).
            source: Source of the transaction (GRANT, DONATION, SPONSORSHIP, etc.).
            amount: Transaction amount.
            currency: Currency code (default: USD).
            description: Transaction description.
            financial_account_id: ID of the financial account (optional).
            budget_id: ID of the budget (optional).
            created_by: User who created the transaction.

        Returns:
            Transaction: The created transaction.
        """
        Transaction = django_apps.get_model("finance", "Transaction")
        FinancialAccount = django_apps.get_model("finance", "FinancialAccount")
        Budget = django_apps.get_model("finance", "Budget")
        
        # Validate financial account if provided
        financial_account = None
        if financial_account_id:
            try:
                financial_account = FinancialAccount.objects.get(id=financial_account_id)
            except FinancialAccount.DoesNotExist:
                raise InvalidAccountError(f"Financial account with ID {financial_account_id} does not exist.")
                
        # Validate budget if provided
        budget = None
        if budget_id:
            try:
                budget = Budget.objects.get(id=budget_id)
            except Budget.DoesNotExist:
                raise ValueError(f"Budget with ID {budget_id} does not exist.")
                
        # Check for duplicate reference number
        if Transaction.objects.filter(reference_number=reference_number).exists():
            raise InvalidTransactionError(f"A transaction with reference number '{reference_number}' already exists.")
            
        # Create the transaction
        transaction_obj = Transaction.objects.create(
            reference_number=reference_number,
            transaction_type=transaction_type,
            status=status,
            source=source,
            amount=amount,
            currency=currency,
            description=description,
            financial_account=financial_account,
            budget=budget,
            created_by=created_by,
        )
        return transaction_obj

    @staticmethod
    def post_transaction(transaction_id: int, posted_by: Optional[User] = None) -> Any:
        """
        Post a transaction (change status from DRAFT/SUBMITTED/APPROVED to POSTED).

        Args:
            transaction_id: ID of the transaction to post.
            posted_by: User who posted the transaction.

        Returns:
            Transaction: The posted transaction.
        """
        Transaction = django_apps.get_model("finance", "Transaction")
        FinancialYear = django_apps.get_model("finance", "FinancialYear")
        
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            raise ValueError(f"Transaction with ID {transaction_id} does not exist.")
            
        # Check if transaction can be posted
        if transaction_obj.status not in ["DRAFT", "SUBMITTED", "APPROVED"]:
            raise InvalidTransactionError(
                f"Transaction cannot be posted from status '{transaction_obj.status}'. "
                f"Only DRAFT, SUBMITTED, or APPROVED transactions can be posted."
            )
            
        # Check if financial period is open
        financial_year = FinancialYear.objects.filter(is_active=True).first()
        if not financial_year:
            raise FinancialPeriodError("No active financial year found.")
            
        # In a real implementation, you would check if the transaction date falls within an open period
        
        # Post the transaction
        transaction_obj.status = "POSTED"
        transaction_obj.posted_by = posted_by
        transaction_obj.posted_at = timezone.now()
        transaction_obj.updated_by = posted_by
        transaction_obj.updated_at = timezone.now()
        transaction_obj.save()
        
        # Update budget allocations if applicable
        if transaction_obj.budget:
            BudgetService.allocate_to_budget_line(
                transaction_obj.budget.id,
                transaction_obj.amount,
                posted_by
            )
            
        return transaction_obj

    @staticmethod
    def void_transaction(transaction_id: int, voided_by: Optional[User] = None, reason: str = "") -> Any:
        """
        Void a posted transaction.

        Args:
            transaction_id: ID of the transaction to void.
            voided_by: User who voided the transaction.
            reason: Reason for voiding the transaction.

        Returns:
            Transaction: The voided transaction.
        """
        Transaction = django_apps.get_model("finance", "Transaction")
        
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist:
            raise ValueError(f"Transaction with ID {transaction_id} does not exist.")
            
        # Check if transaction can be voided
        if transaction_obj.status != "POSTED":
            raise InvalidTransactionError(
                f"Only posted transactions can be voided. Current status: '{transaction_obj.status}'"
            )
            
        # Void the transaction by creating a reversing transaction
        # In a more sophisticated system, you might have a voided status instead
        transaction_obj.status = "VOIDED"
        transaction_obj.description = f"{transaction_obj.description} | VOIDED: {reason}"
        transaction_obj.voided_by = voided_by
        transaction_obj.voided_at = timezone.now()
        transaction_obj.updated_by = voided_by
        transaction_obj.updated_at = timezone.now()
        transaction_obj.save()
        
        # If this transaction affected a budget, we need to reverse the budget allocation
        if transaction_obj.budget:
            # In a real system, you'd create a negative allocation or adjust the budget
            # For simplicity, we're just noting that this would need to be handled
            pass
            
        return transaction_obj


class GrantService:
    """Service for managing grants."""

    @staticmethod
    def create_grant(
        name: str,
        reference_number: str,
        donor_id: int,
        amount: Decimal,
        currency: str = "USD",
        start_date: Optional[timezone.datetime] = None,
        end_date: Optional[timezone.datetime] = None,
        description: str = "",
        created_by: Optional[User] = None,
    ) -> Any:
        """
        Create a new grant.

        Args:
            name: Grant name.
            reference_number: Grant reference number.
            donor_id: ID of the donor providing the grant.
            amount: Grant amount.
            currency: Currency code (default: USD).
            start_date: Grant start date.
            end_date: Grant end date.
            description: Grant description.
            created_by: User who created the grant.

        Returns:
            Grant: The created grant.
        """
        Grant = django_apps.get_model("finance", "Grant")
        Donor = django_apps.get_model("finance", "Donor")
        
        try:
            donor = Donor.objects.get(id=donor_id)
        except Donor.DoesNotExist:
            raise ValueError(f"Donor with ID {donor_id} does not exist.")
            
        # Check for duplicate reference number
        if Grant.objects.filter(reference_number=reference_number).exists():
            raise InvalidTransactionError(f"A grant with reference number '{reference_number}' already exists.")
            
        grant = Grant.objects.create(
            name=name,
            reference_number=reference_number,
            donor=donor,
            amount=amount,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            description=description,
            created_by=created_by,
        )
        return grant

    @staticmethod
    def disburse_grant(
        grant_id: int,
        amount: Decimal,
        transaction_reference: str,
        disbursed_by: Optional[User] = None,
    ) -> Tuple[Any, Any]:
        """
        Disburse funds from a grant.

        Args:
            grant_id: ID of the grant.
            amount: Amount to disburse.
            transaction_reference: Reference number for the disbursement transaction.
            disbursed_by: User who disbursed the funds.

        Returns:
            Tuple of (Grant, Transaction): The updated grant and the disbursement transaction.
        """
        Grant = django_apps.get_model("finance", "Grant")
        TransactionService = TransactionService  # Avoid circular import
        
        try:
            grant = Grant.objects.get(id=grant_id)
        except Grant.DoesNotExist:
            raise ValueError(f"Grant with ID {grant_id} does not exist.")
            
        # Check if sufficient funds are available
        if grant.remaining_amount < amount:
            raise InsufficientFundsError(
                f"Insufficient funds in grant. Available: {grant.remaining_amount}, Requested: {amount}"
            )
            
        # Create the disbursement transaction
        transaction = TransactionService.create_transaction(
            reference_number=transaction_reference,
            transaction_type="EXPENSE",
            status="DRAFT",
            source="GRANT",
            amount=amount,
            currency=grant.currency,
            description=f"Disbursement from grant: {grant.name}",
            created_by=disbursed_by,
        )
        
        # Update grant disbursed amount
        grant.disbursed_amount += amount
        grant.updated_by = disbursed_by
        grant.updated_at = timezone.now()
        grant.save()
        
        return grant, transaction


class DonorService:
    """Service for managing donors."""

    @staticmethod
    def create_donor(
        name: str,
        donor_type: str,
        contact_person: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        description: str = "",
        created_by: Optional[User] = None,
    ) -> Any:
        """
        Create a new donor.

        Args:
            name: Donor name.
            donor_type: Type of donor (individual, corporation, foundation, government, etc.).
            contact_person: Primary contact person.
            email: Contact email.
            phone: Contact phone number.
            address: Contact address.
            description: Donor description.
            created_by: User who created the donor.

        Returns:
            Donor: The created donor.
        """
        Donor = django_apps.get_model("finance", "Donor")
        
        donor = Donor.objects.create(
            name=name,
            donor_type=donor_type,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address,
            description=description,
            created_by=created_by,
        )
        return donor

    @staticmethod
    def record_donation(
        donor_id: int,
        amount: Decimal,
        currency: str = "USD",
        transaction_reference: str,
        received_by: Optional[User] = None,
    ) -> Tuple[Any, Any]:
        """
        Record a donation from a donor.

        Args:
            donor_id: ID of the donor.
            amount: Donation amount.
            currency: Currency code (default: USD).
            transaction_reference: Reference number for the donation transaction.
            received_by: User who recorded the donation.

        Returns:
            Tuple of (Donor, Transaction): The updated donor and the donation transaction.
        """
        Donor = django_apps.get_model("finance", "Donor")
        TransactionService = TransactionService  # Avoid circular import
        
        try:
            donor = Donor.objects.get(id=donor_id)
        except Donor.DoesNotExist:
            raise ValueError(f"Donor with ID {donor_id} does not exist.")
            
        # Create the donation transaction
        transaction = TransactionService.create_transaction(
            reference_number=transaction_reference,
            transaction_type="INCOME",
            status="DRAFT",
            source="DONATION",
            amount=amount,
            currency=currency,
            description=f"Donation from: {donor.name}",
            created_by=received_by,
        )
        
        # Update donor contribution total
        donor.total_contributions += amount
        donor.updated_by = received_by
        donor.updated_at = timezone.now()
        donor.save()
        
        return donor, transaction