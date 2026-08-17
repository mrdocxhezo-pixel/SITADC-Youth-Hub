"""Finance Engine services."""

from __future__ import annotations

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.finance.constants import TransactionStatus, TransactionType
from apps.finance.exceptions import (
    BudgetExceededError,
    FinancialPeriodError,
    InsufficientFundsError,
    InvalidAccountError,
    InvalidTransactionError,
)
from apps.finance.models import (
    Budget,
    Donor,
    FinancialAccount,
    FinancialYear,
    Grant,
    Transaction,
)

User = get_user_model()


class FinancialAccountService:
    """Service for managing financial accounts."""

    @staticmethod
    def create_account(
        name: str,
        code: str,
        account_type: str,
        currency: str = "USD",
        opening_balance: Decimal = Decimal("0"),
        is_active: bool = True,
        description: str = "",
        created_by: User | None = None,
    ) -> FinancialAccount:
        """
        Create a new financial account.

        Args:
            name: Account name.
            code: Account code (unique).
            account_type: Type of account (ASSET, LIABILITY, EQUITY, INCOME, EXPENSE).
            currency: Currency code (default: USD).
            opening_balance: Opening balance (default: 0).
            is_active: Whether the account is active.
            description: Account description.
            created_by: User who created the account.

        Returns:
            FinancialAccount: The created account.
        """
        return FinancialAccount.objects.create(
            name=name,
            code=code,
            account_type=account_type,
            currency=currency,
            opening_balance=opening_balance,
            is_active=is_active,
            description=description,
            created_by=created_by,
        )

    @staticmethod
    def get_account_balance(
        account_id: int, as_of_date: timezone.datetime | None = None
    ) -> Decimal:
        """
        Get the balance of a financial account as of a specific date.

        Args:
            account_id: ID of the financial account.
            as_of_date: Date to calculate balance as of (default: now).

        Returns:
            Decimal: The account balance.

        Raises:
            InvalidAccountError: If the account does not exist.
        """
        if as_of_date is None:
            as_of_date = timezone.now()

        try:
            account = FinancialAccount.objects.get(id=account_id)
        except FinancialAccount.DoesNotExist as exc:
            raise InvalidAccountError(
                f"Financial account with ID {account_id} does not exist."
            ) from exc

        return account.get_balance_as_of_date(as_of_date)

    @staticmethod
    def deactivate_account(
        account_id: int, deactivated_by: User | None = None
    ) -> FinancialAccount:
        """
        Deactivate a financial account.

        Args:
            account_id: ID of the financial account to deactivate.
            deactivated_by: User who deactivated the account.

        Returns:
            FinancialAccount: The deactivated account.

        Raises:
            InvalidAccountError: If the account does not exist.
        """
        try:
            account = FinancialAccount.objects.get(id=account_id)
        except FinancialAccount.DoesNotExist as exc:
            raise InvalidAccountError(
                f"Financial account with ID {account_id} does not exist."
            ) from exc

        account.is_active = False
        account.updated_by = deactivated_by
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
        allocated_amount: Decimal = Decimal("0"),
        description: str = "",
        created_by: User | None = None,
    ) -> Budget:
        """
        Create a new budget.

        Args:
            name: Budget name.
            code: Budget code (unique).
            financial_year_id: ID of the financial year.
            total_amount: Total budget amount.
            allocated_amount: Already allocated amount (default: 0).
            description: Budget description.
            created_by: User who created the budget.

        Returns:
            Budget: The created budget.

        Raises:
            ValueError: If the financial year does not exist.
        """
        try:
            financial_year = FinancialYear.objects.get(id=financial_year_id)
        except FinancialYear.DoesNotExist as exc:
            raise ValueError(
                f"Financial year with ID {financial_year_id} does not exist."
            ) from exc

        return Budget.objects.create(
            name=name,
            code=code,
            financial_year=financial_year,
            total_amount=total_amount,
            allocated_amount=allocated_amount,
            description=description,
            created_by=created_by,
        )

    @staticmethod
    def allocate_to_budget_line(
        budget_id: int, amount: Decimal, allocated_by: User | None = None
    ) -> bool:
        """
        Allocate amount to a budget.

        Args:
            budget_id: ID of the budget.
            amount: Amount to allocate.
            allocated_by: User performing the allocation.

        Returns:
            bool: True if allocation successful.

        Raises:
            ValueError: If the budget does not exist.
            BudgetExceededError: If the allocation would exceed the budget total.
        """
        try:
            budget = Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist as exc:
            raise ValueError(f"Budget with ID {budget_id} does not exist.") from exc
        if budget.allocated_amount + amount > budget.total_amount:
            raise BudgetExceededError(
                f"Allocation of {amount} would exceed budget total of "
                f"{budget.total_amount}. "
                f"Already allocated: {budget.allocated_amount}, "
                f"Remaining: {budget.remaining}"
            )

        budget.allocated_amount += amount
        budget.updated_by = allocated_by
        budget.save()
        return True

    @staticmethod
    def get_budget_variance(
        budget_id: int, as_of_date: timezone.datetime | None = None
    ) -> dict[str, Decimal]:
        """
        Get budget variance analysis.

        Args:
            budget_id: ID of the budget.
            as_of_date: Unused; kept for API compatibility.

        Returns:
            Dict containing budgeted, actual, variance, and percentage.

        Raises:
            ValueError: If the budget does not exist.
        """
        try:
            budget = Budget.objects.get(id=budget_id)
        except Budget.DoesNotExist as exc:
            raise ValueError(f"Budget with ID {budget_id} does not exist.") from exc
        return budget.get_variance()


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
        financial_account_id: int | None = None,
        budget_id: int | None = None,
        created_by: User | None = None,
    ) -> Transaction:
        """
        Create a new financial transaction.

        Args:
            reference_number: Unique reference number for the transaction.
            transaction_type: Type of transaction (INCOME, EXPENSE, TRANSFER, etc.).
            status: Status of the transaction (DRAFT, SUBMITTED, APPROVED, POSTED,
                etc.).
            source: Source of the transaction (GRANT, DONATION, SPONSORSHIP, etc.).
            amount: Transaction amount.
            currency: Currency code (default: USD).
            description: Transaction description.
            financial_account_id: ID of the financial account (optional).
            budget_id: ID of the budget (optional).
            created_by: User who created the transaction.

        Returns:
            Transaction: The created transaction.

        Raises:
            InvalidAccountError: If the financial account does not exist.
            ValueError: If the budget does not exist.
            InvalidTransactionError: If the reference number is duplicated.
        """
        financial_account = None
        if financial_account_id:
            try:
                financial_account = FinancialAccount.objects.get(
                    id=financial_account_id
                )
            except FinancialAccount.DoesNotExist as exc:
                raise InvalidAccountError(
                    f"Financial account with ID {financial_account_id} does not exist."
                ) from exc

        budget = None
        if budget_id:
            try:
                budget = Budget.objects.get(id=budget_id)
            except Budget.DoesNotExist as exc:
                raise ValueError(f"Budget with ID {budget_id} does not exist.") from exc
        if Transaction.objects.filter(reference_number=reference_number).exists():
            raise InvalidTransactionError(
                "A transaction with reference number "
                f"'{reference_number}' already exists."
            )

        return Transaction.objects.create(
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

    @staticmethod
    def post_transaction(
        transaction_id: int, posted_by: User | None = None
    ) -> Transaction:
        """
        Post a transaction (change status from DRAFT/SUBMITTED/APPROVED to POSTED).

        Args:
            transaction_id: ID of the transaction to post.
            posted_by: User who posted the transaction.

        Returns:
            Transaction: The posted transaction.

        Raises:
            ValueError: If the transaction does not exist.
            InvalidTransactionError: If the transaction cannot be posted.
            FinancialPeriodError: If no active financial year exists.
        """
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist as exc:
            raise ValueError(
                f"Transaction with ID {transaction_id} does not exist."
            ) from exc
        if transaction_obj.status not in [
            TransactionStatus.DRAFT,
            TransactionStatus.SUBMITTED,
            TransactionStatus.APPROVED,
        ]:
            raise InvalidTransactionError(
                f"Transaction cannot be posted from status '{transaction_obj.status}'. "
                f"Only DRAFT, SUBMITTED, or APPROVED transactions can be posted."
            )

        if not FinancialYear.objects.filter(is_active=True).exists():
            raise FinancialPeriodError("No active financial year found.")

        transaction_obj.status = TransactionStatus.POSTED
        transaction_obj.posted_by = posted_by
        transaction_obj.posted_at = timezone.now()
        transaction_obj.updated_by = posted_by
        transaction_obj.save()
        return transaction_obj

    @staticmethod
    def void_transaction(
        transaction_id: int, voided_by: User | None = None, reason: str = ""
    ) -> Transaction:
        """
        Void a posted transaction.

        Args:
            transaction_id: ID of the transaction to void.
            voided_by: User who voided the transaction.
            reason: Reason for voiding the transaction.

        Returns:
            Transaction: The voided transaction.

        Raises:
            ValueError: If the transaction does not exist.
            InvalidTransactionError: If the transaction is not posted.
        """
        try:
            transaction_obj = Transaction.objects.get(id=transaction_id)
        except Transaction.DoesNotExist as exc:
            raise ValueError(
                f"Transaction with ID {transaction_id} does not exist."
            ) from exc
        if transaction_obj.status != TransactionStatus.POSTED:
            raise InvalidTransactionError(
                f"Only posted transactions can be voided. Current status: "
                f"'{transaction_obj.status}'"
            )

        transaction_obj.status = TransactionStatus.VOIDED
        if reason:
            transaction_obj.description = (
                f"{transaction_obj.description} | VOIDED: {reason}"
            )
        transaction_obj.voided_by = voided_by
        transaction_obj.voided_at = timezone.now()
        transaction_obj.updated_by = voided_by
        transaction_obj.save()
        return transaction_obj


class GrantService:
    """Service for managing grants."""

    @staticmethod
    def create_grant(
        name: str,
        grant_number: str,
        funding_agency: str,
        grant_type: str,
        amount_awarded: Decimal,
        currency: str = "USD",
        award_date: timezone.datetime | None = None,
        start_date: timezone.datetime | None = None,
        end_date: timezone.datetime | None = None,
        donor_id: int | None = None,
        description: str = "",
        created_by: User | None = None,
    ) -> Grant:
        """
        Create a new grant.

        Args:
            name: Grant name.
            grant_number: Grant reference number (unique).
            funding_agency: Funding agency name.
            grant_type: Type of grant.
            amount_awarded: Total grant amount.
            currency: Currency code (default: USD).
            award_date: Award date.
            start_date: Grant start date.
            end_date: Grant end date.
            donor_id: ID of the donor providing the grant (optional).
            description: Grant description.
            created_by: User who created the grant.

        Returns:
            Grant: The created grant.

        Raises:
            InvalidTransactionError: If the grant number is duplicated.
            ValueError: If the donor does not exist.
        """
        from apps.finance.models import Donor as DonorModel

        donor = None
        if donor_id:
            try:
                donor = DonorModel.objects.get(id=donor_id)
            except DonorModel.DoesNotExist as exc:
                raise ValueError(f"Donor with ID {donor_id} does not exist.") from exc
        if Grant.objects.filter(grant_number=grant_number).exists():
            raise InvalidTransactionError(
                f"A grant with number '{grant_number}' already exists."
            )

        return Grant.objects.create(
            name=name,
            grant_number=grant_number,
            funding_agency=funding_agency,
            grant_type=grant_type,
            amount_awarded=amount_awarded,
            currency=currency,
            award_date=award_date,
            start_date=start_date,
            end_date=end_date,
            donor=donor,
            description=description,
            created_by=created_by,
        )

    @staticmethod
    def disburse_grant(
        grant_id: int,
        amount: Decimal,
        transaction_reference: str,
        disbursed_by: User | None = None,
    ) -> tuple[Grant, Transaction]:
        """
        Disburse funds from a grant.

        Args:
            grant_id: ID of the grant.
            amount: Amount to disburse.
            transaction_reference: Reference number for the disbursement transaction.
            disbursed_by: User who disbursed the funds.

        Returns:
            Tuple of (Grant, Transaction): The updated grant and disbursement
                transaction.

        Raises:
            ValueError: If the grant does not exist.
            InsufficientFundsError: If the grant has insufficient undisbursed funds.
        """
        try:
            grant = Grant.objects.get(id=grant_id)
        except Grant.DoesNotExist as exc:
            raise ValueError(f"Grant with ID {grant_id} does not exist.") from exc
        if grant.remaining_amount < amount:
            raise InsufficientFundsError(
                f"Insufficient funds in grant. Available: {grant.remaining_amount}, "
                f"Requested: {amount}"
            )

        with transaction.atomic():
            transaction_obj = TransactionService.create_transaction(
                reference_number=transaction_reference,
                transaction_type=TransactionType.EXPENSE,
                status=TransactionStatus.DRAFT,
                source="GRANT",
                amount=amount,
                currency=grant.currency,
                description=f"Disbursement from grant: {grant.name}",
                created_by=disbursed_by,
            )
            grant.disbursed_amount += amount
            grant.updated_by = disbursed_by
            grant.save()

        return grant, transaction_obj


class DonorService:
    """Service for managing donors."""

    @staticmethod
    def create_donor(
        name: str,
        donor_number: str,
        donor_type: str = "INDIVIDUAL",
        contact_person: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        created_by: User | None = None,
    ) -> Donor:
        """
        Create a new donor.

        Args:
            name: Donor name.
            donor_number: Donor number (unique).
            donor_type: Type of donor.
            contact_person: Primary contact person.
            email: Contact email.
            phone: Contact phone number.
            address: Contact address.
            created_by: User who created the donor.

        Returns:
            Donor: The created donor.
        """
        return Donor.objects.create(
            name=name,
            donor_number=donor_number,
            donor_type=donor_type,
            contact_person=contact_person,
            email=email,
            phone=phone,
            address=address,
            created_by=created_by,
        )

    @staticmethod
    def record_donation(
        donor_id: int,
        amount: Decimal,
        transaction_reference: str,
        currency: str = "USD",
        received_by: User | None = None,
    ) -> tuple[Donor, Transaction]:
        """
        Record a donation from a donor.

        Args:
            donor_id: ID of the donor.
            amount: Donation amount.
            currency: Currency code (default: USD).
            transaction_reference: Reference number for the donation transaction.
            received_by: User who recorded the donation.

        Returns:
            Tuple of (Donor, Transaction): The updated donor and donation transaction.

        Raises:
            ValueError: If the donor does not exist.
        """
        try:
            donor = Donor.objects.get(id=donor_id)
        except Donor.DoesNotExist as exc:
            raise ValueError(f"Donor with ID {donor_id} does not exist.") from exc
        with transaction.atomic():
            transaction_obj = TransactionService.create_transaction(
                reference_number=transaction_reference,
                transaction_type=TransactionType.INCOME,
                status=TransactionStatus.DRAFT,
                source="DONATION",
                amount=amount,
                currency=currency,
                description=f"Donation from: {donor.name}",
                created_by=received_by,
            )
            donor.total_donated += amount
            donor.year_to_date_donated += amount
            donor.last_donation_date = timezone.now().date()
            donor.updated_by = received_by
            donor.save()

        return donor, transaction_obj
