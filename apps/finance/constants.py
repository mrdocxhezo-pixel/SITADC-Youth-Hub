"""Constants for the Finance and Resource Mobilization (Phase 28)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class FinancialYear(models.Model):
    """Financial year configuration."""

    name = models.CharField(_("Name"), max_length=90, unique=True)
    start_month = models.PositiveSmallIntegerField(
        _("Start month"), help_text=_("1=January, 12=December")
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Financial Year")
        verbose_name_plural = _("Financial Years")

    def __str__(self) -> str:
        return self.name


class TransactionType(models.TextChoices):
    """Types of financial transactions."""

    INCOME = "INCOME", _("Income")
    EXPENSE = "EXPENSE", _("Expense")
    TRANSFER = "TRANSFER", _("Transfer")
    ADJUSTMENT = "ADJUSTMENT", _("Adjustment")


class TransactionStatus(models.TextChoices):
    """Status of a financial transaction."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    PAID = "PAID", _("Paid")
    RECONCILED = "RECONCILED", _("Reconciled")
    ARCHIVED = "ARCHIVED", _("Archived")


class PaymentMethod(models.TextChoices):
    """Payment methods for transactions."""

    CASH = "CASH", _("Cash")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    MOBILE_MONEY = "MOBILE_MONEY", _("Mobile Money")
    CHEQUE = "CHEQUE", _("Cheque")
    CREDIT_CARD = "CREDIT_CARD", _("Credit Card")
    DIRECT_DEBIT = "DIRECT_DEBIT", _("Direct Debit")


class AccountType(models.TextChoices):
    """Types of accounts in the chart of accounts."""

    ASSET = "ASSET", _("Asset")
    LIABILITY = "LIABILITY", _("Liability")
    EQUITY = "EQUITY", _("Equity/Fund Balance")
    INCOME = "INCOME", _("Income")
    EXPENSE = "EXPENSE", _("Expense")


class BudgetType(models.TextChoices):
    """Types of budgets."""

    ANNUAL = "ANNUAL", _("Annual Budget")
    QUARTERLY = "QUARTERLY", _("Quarterly Budget")
    MONTHLY = "MONTHLY", _("Monthly Budget")
    PROGRAMME = "PROGRAMME", _("Programme Budget")
    PROJECT = "PROJECT", _("Project Budget")
    DEPARTMENTAL = "DEPARTMENTAL", _("Departmental Budget")
    ACTIVITY = "ACTIVITY", _("Activity Budget")
    GRANT = "GRANT", _("Grant Budget")
    REVISED = "REVISED", _("Revised Budget")


class ResourceSource(models.TextChoices):
    """Sources of resource mobilization."""

    GRANT = "GRANT", _("Grant")
    DONATION = "DONATION", _("Donation")
    SPONSORSHIP = "SPONSORSHIP", _("Sponsorship")
    FEE = "FEE", _("Fee")
    FUNDRAISING = "FUNDRAISING", _("Fundraising")
    PARTNERSHIP = "PARTNERSHIP", _("Partnership")
    GOVERNMENT = "GOVERNMENT", _("Government")
    OTHER = "OTHER", _("Other")
