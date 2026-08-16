"""Models for the Finance and Resource Mobilization (Phase 28)."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import CreatedByModel, TimeStampedModel, UpdatedByModel, UUIDModel
from apps.finance.constants import (
    FinancialYear,
    ResourceSource,
    TransactionType,
    TransactionStatus,
    PaymentMethod,
    AccountType,
    BudgetType,
)


class FinancialAccount(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Organizational financial account tracking."""

    name = models.CharField(_("Account name"), max_length=200)
    code = models.CharField(_("Account code"), max_length=50, unique=True)
    account_type = models.CharField(
        _("Account type"), max_length=20, choices=AccountType.choices, default=AccountType.ASSET
    )
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Financial Account")
        verbose_name_plural = _("Financial Accounts")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class BankAccount(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Bank account management."""

    ACCOUNT_TYPE_CHOICES = [
        ("CURRENT", _("Current Account")),
        ("SAVINGS", _("Savings Account")),
        ("FIXED_DEPOSIT", _("Fixed Deposit")),
        ("OTHER", ("Other")),
    ]

    name = models.CharField(_("Account name"), max_length=200)
    account_number = models.CharField(_("Account number"), max_length=50, unique=True)
    bank_name = models.CharField(_("Bank name"), max_length=200)
    bank_branch = models.CharField(_("Bank branch"), max_length=200, blank=True)
    account_type = models.CharField(
        _("Account type"), max_length=20, choices=ACCOUNT_TYPE_CHOICES, default="CURRENT"
    )
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    opening_balance = models.DecimalField(
        _("Opening balance"), max_digits=15, decimal_places=2, default=0
    )
    current_balance = models.DecimalField(
        _("Current balance"), max_digits=15, decimal_places=2, default=0
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    reconciliation_date = models.DateField(
        _("Last reconciliation date"), null=True, blank=True
    )
    swift_code = models.CharField(_("SWIFT code"), max_length=20, blank=True)
    routing_number = models.CharField(_("Routing number"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("Bank Account")
        verbose_name_plural = _("Bank Accounts")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} - {self.bank_name} ({self.account_number})"


class PettyCash(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Petty cash management."""

    name = models.CharField(_("Petty cash name"), max_length=200)
    custodian = models.CharField(_("Custodian"), max_length=200)
    custodian_position = models.CharField(_("Custodian position"), max_length=100, blank=True)
    opening_balance = models.DecimalField(
        _("Opening balance"), max_digits=15, decimal_places=2, default=0
    )
    current_balance = models.DecimalField(
        _("Current balance"), max_digits=15, decimal_places=2, default=0
    )
    max_limit = models.DecimalField(
        _("Maximum limit"), max_digits=15, decimal_places=2, help_text=_("Maximum amount allowed in petty cash")
    )
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)
    last_replenished = models.DateField(_("Last replenished"), null=True, blank=True)
    replenishment_approval_level = models.CharField(
        _("Replenishment approval level"), max_length=50, blank=True
    )

    class Meta:
        verbose_name = _("Petty Cash")
        verbose_name_plural = _("Petty Cash")
        ordering = ("name",)

    def __str__(    ) -> str:
        return f"{self.name} - Custodian: {self.custodian}"


class Grant(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Grant management."""

    GRANT_STATUS_CHOICES = [
        ("PROSPECTIVE", _("Prospective")),
        ("APPLIED", _("Applied")),
        ("APPROVED", _("Approved")),
        ("ACTIVE", _("Active")),
        ("COMPLETED", ("Completed")),
        ("TERMINATED", ("Terminated")),
        ("REJECTED", ("Rejected")),
    ]

    name = models.CharField(_("Grant name"), max_length=200)
    grant_number = models.CharField(_("Grant number"), max_length=50, unique=True)
    funding_agency = models.CharField(_("Funding agency"), max_length=200)
    grant_type = models.CharField(_("Grant type"), max_length=100)
    amount_awarded = models.DecimalField(_("Amount awarded"), max_digits=15, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    award_date = models.DateField(_("Award date"))
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    status = models.CharField(
        _("Status"), max_length=20, choices=GRANT_STATUS_CHOICES, default="PROSPECTIVE"
    )
    # Link to budget/programme/project
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    # Reporting requirements
    reporting_frequency = models.CharField(
        _("Reporting frequency"), max_length=50, help_text=_("e.g., Monthly, Quarterly, Annual")
    )
    next_report_due = models.DateField(_("Next report due"), null=True, blank=True)
    # Special conditions
    special_conditions = models.TextField(_("Special conditions"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Grant")
        verbose_name_plural = _("Grants")
        ordering = ("-award_date", "name")

    def __str__(self) -> str:
        return f"{self.name} - {self.funding_agency} ({self.grant_number})"


class Donor(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Donor management."""

    DONOR_TYPE_CHOICES = [
        ("INDIVIDUAL", _("Individual")),
        ("CORPORATE", ("Corporate")),
        ("FOUNDATION", ("Foundation")),
        ("GOVERNMENT", ("Government")),
        ("INTERNATIONAL_ORG", ("International Organization")),
        ("OTHER", ("Other")),
    ]

    DONOR_STATUS_CHOICES = [
        ("ACTIVE", ("Active")),
        ("INACTIVE", ("Inactive")),
        ("LAPSED", ("Lapsed")),
    ]

    name = models.CharField(_("Donor name"), max_length=200)
    donor_number = models.CharField(_("Donor number"), max_length=50, unique=True)
    donor_type = models.CharField(
        ("Donor type"), max_length=20, choices=DONOR_TYPE_CHOICES, default="INDIVIDUAL"
    )
    contact_person = models.CharField(_("Contact person"), max_length=200, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    status = models.CharField(
        _("Status"), max_length=20, choices=DONOR_STATUS_CHOICES, default="ACTIVE"
    )
    # Financial information
    total_donated = models.DecimalField(
        ("Total donated"), max_digits=15, decimal_places=2, default=0
    )
    year_to_date_donated = models.DecimalField(
        ("Year to date donated"), max_digits=15, decimal_places=2, default=0
    )
    last_donation_date = models.DateField(_("Last donation date"), null=True, blank=True)
    # Preferences
    preferred_contact_method = models.CharField(
        ("Preferred contact method"), max_length=50, blank=True
    )
    communication_preferences = models.TextField(_("Communication preferences"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Donor")
        verbose_name_plural = ("Donors")
        ordering = ("-total_donated", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.donor_number})"


class Sponsor(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Sponsorship management."""

    SPONSOR_TYPE_CHOICES = [
        ("CORPORATE", ("Corporate")),
        ("GOVERNMENT", ("Government")),
        ("INSTITUTIONAL", ("Institutional")),
        ("INDIVIDUAL", ("Individual")),
        ("OTHER", ("OTHER")),
    ]

    SPONSORSHIP_TYPE_CHOICES = [
        ("FINANCIAL", ("Financial Support")),
        ("IN_KIND", ("In-Kind Support")),
        ("MEDIA", ("Media Support")),
        ("TECHNICAL", ("Technical Support")),
        ("VENUE", ("VENUE Support")),
        ("OTHER", ("OTHER")),
    ]

    SPONSORSHIP_STATUS_CHOICES = [
        ("PROSPECTIVE", ("Prospective")),
        ("PENDING", ("Pending")),
        ("CONFIRMED", ("Confirmed")),
        ("ACTIVE", ("Active")),
        ("COMPLETED", ("Completed")),
        ("TERMINATED", ("Terminated")),
    ]

    name = models.CharField(_("Sponsor name"), max_length=200)
    sponsor_number = models.CharField(_("Sponsor number"), max_length=50, unique=True)
    sponsor_type = models.CharField(
        ("Sponsor type"), max_length=20, choices=SPONSOR_TYPE_CHOICES, default="CORPORATE"
    )
    sponsorship_type = models.CharField(
        ("Sponsorship type"), max_length=20, choices=SPONSORSHIP_TYPE_CHOICES, default="FINANCIAL"
    )
    contact_person = models.CharField(_("Contact person"), max_length=200, blank=True)
    email = models.EmailField(_("Email"), blank=True)
    phone = models.CharField(_("Phone"), max_length=20, blank=True)
    address = models.TextField(_("Address"), blank=True)
    website = models.URLField(_("Website"), blank=True)
    # Financial information
    sponsored_amount = models.DecimalField(
        ("Sponsored amount"), max_digits=15, decimal_places=2, default=0
    )
    # Dates
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"), blank=True, null=True)
    # Status
    status = models.CharField(
        ("Status"), max_length=20, choices=SPONSORSHIP_STATUS_CHOICES, default="PROSPECTIVE"
    )
    # Linked to programmes/projects/events
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    event = models.CharField(_("Event"), max_length=200, blank=True)
    # Benefits received
    benefits_received = models.TextField(_("Benefits received"), blank=True)
    # Reporting requirements
    reporting_frequency = models.CharField(
        ("Reporting frequency"), max_length=50, help_text=_("e.g., Monthly, Quarterly, Annual")
    )
    next_report_due = models.DateField(_("Next report due"), null=True, blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Sponsor")
        verbose_name_plural = ("Sponsors")
        ordering = ("-sponsored_amount", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.sponsor_number})"


class FundraisingCampaign(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Fundraising campaign management."""

    CAMPAIGN_TYPE_CHOICES = [
        ("ONLINE", ("Online Campaign")),
        ("EVENT", ("Event-Based Campaign")),
        ("MAIL", ("Mail Campaign")),
        ("PHONE", ("Phone Campaign")),
        ("FACE_TO_FACE", ("Face-to-Face Campaign")),
        ("CORPORATE", ("Corporate Partnership")),
        ("GRANT", ("Grant Application")),
        ("OTHER", ("Other")),
    ]

    CAMPAIGN_STATUS_CHOICES = [
        ("PLANNING", ("Planning")),
        ("ACTIVE", ("Active")),
        ("PAUSED", ("Paused")),
        ("COMPLETED", ("Completed")),
        ("CANCELLED", ("Cancelled")),
    ]

    name = models.CharField(_("Campaign name"), max_length=200)
    campaign_number = models.CharField(_("Campaign number"), max_length=50, unique=True)
    campaign_type = models.CharField(
        ("Campaign type"), max_length=20, choices=CAMPAIGN_TYPE_CHOICES, default="ONLINE"
    )
    description = models.TextField(_("Description"))
    start_date = models.DateField(_("Start date"))
    end_date = models.DateField(_("End date"))
    target_amount = models.DecimalField(_("Target amount"), max_digits=15, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    amount_raised = models.DecimalField(
        ("Amount raised"), max_digits=15, decimal_places=2, default=0
    )
    status = models.CharField(
        ("Status"), max_length=20, choices=CAMPAIGN_STATUS_CHOICES, default="PLANNING"
    )
    # Linked to fundraising efforts
    donor = models.ForeignKey(
        Donor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="fundraising_campaigns",
        verbose_name=_("Donor"),
    )
    sponsor = models.ForeignKey(
        Sponsor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="fundraising_campaigns",
        verbose_name=_("Sponsor"),
    )
    # Tracking
    progress_notes = models.TextField(_("Progress notes"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = ("Fundraising Campaign")
        verbose_name_plural = ("Fundraising Campaigns")
        ordering = ("-start_date", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.campaign_number})"

    @property
    def progress_percentage(self) -> float:
        if self.target_amount == 0:
            return 0.0
        return float(self.amount_raised / self.target_amount * 100)


class ProcurementFinancialTracking(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Procurement financial tracking."""

    PROCUREMENT_STATUS_CHOICES = [
        ("PLANNED", ("Planned")),
        ("REQUESTED", ("Requested")),
        ("APPROVED", ("Approved")),
        ("ORDERED", ("Ordered")),
        ("RECEIVED", ("Received")),
        ("PAID", ("Paid")),
        ("CANCELLED", ("Cancelled")),
    ]

    name = models.CharField(_("Procurement name"), max_length=200)
    procurement_number = models.CharField(_("Procurement number"), max_length=50, unique=True)
    description = models.TextField(_("Description"))
    # Financial information
    estimated_cost = models.DecimalField(
        ("Estimated cost"), max_digits=15, decimal_places=2
    )
    actual_cost = models.DecimalField(
        ("Actual cost"), max_digits=15, decimal_places=2, default=0
    )
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    # Dates
    required_date = models.DateField(_("Required date"))
    promised_date = models.DateField(_("Promised date"), blank=True, null=True)
    actual_delivery_date = models.DateField(_("Actual delivery date"), blank=True, null=True)
    # Status
    status = models.CharField(
        ("Status"), max_length=20, choices=PROCUREMENT_STATUS_CHOICES, default="PLANNED"
    )
    # Linked to budget/programme/project
    budget_line = models.CharField(_("Budget line"), max_length=100, blank=True)
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    # Supplier information
    supplier_name = models.CharField(_("Supplier name"), max_length=200, blank=True)
    supplier_contact = models.CharField(_("Supplier contact"), max_length=200, blank=True)
    # Payment terms
    payment_terms = models.CharField(
        ("Payment terms"), max_length=100, help_text=_("e.g., Net 30, Net 60")
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Procurement Financial Tracking")
        verbose_name_plural = _("Procurement Financial Tracking")
        ordering = ("-created_at", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.procurement_number})"

    @property
    def cost_variance(self) -> float:
        if self.estimated_cost == 0:
            return 0.0
        return float((self.actual_cost - self.estimated_cost) / self.estimated_cost * 100)


class AssetFinancialTracking(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Asset financial tracking."""

    ASSET_TYPE_CHOICES = [
        ("BUILDING", ("Building")),
        ("VEHICLE", ("Vehicle")),
        ("EQUIPMENT", ("Equipment")),
        ("FURNITURE", ("Furniture")),
        ("TECHNOLOGY", ("Technology")),
        ("LAND", ("Land")),
        ("OTHER", ("Other")),
    ]

    ASSET_STATUS_CHOICES = [
        ("ACTIVE", ("Active")),
        ("IN_MAINTENANCE", ("In Maintenance")),
        ("RETIRED", ("Retired")),
        ("DISPOSED", ("Disposed")),
    ]

    name = models.CharField(_("Asset name"), max_length=200)
    asset_number = models.CharField(_("Asset number"), max_length=50, unique=True)
    asset_type = models.CharField(
        ("Asset type"), max_length=20, choices=ASSET_TYPE_CHOICES, default="EQUIPMENT"
    )
    description = models.TextField(_("Description"), blank=True)
    # Financial information
    acquisition_cost = models.DecimalField(
        ("Acquisition cost"), max_digits=15, decimal_places=2
    )
    current_value = models.DecimalField(
        ("Current value"), max_digits=15, decimal_places=2, default=0
    )
    acquisition_date = models.DateField(_("Acquisition date"))
    # Depreciation
    depreciation_method = models.CharField(
        ("Depreciation method"), max_length=50, help_text=_("e.g., Straight-line, Declining balance")
    )
    useful_life_years = models.PositiveIntegerField(_("Useful life (years)"), default=5)
    annual_depreciation = models.DecimalField(
        ("Annual depreciation"), max_digits=15, decimal_places=2, default=0
    )
    accumulated_depreciation = models.DecimalField(
        ("Accumulated depreciation"), max_digits=15, decimal_places=2, default=0
    )
    # Status
    status = models.CharField(
        ("Status"), max_length=20, choices=ASSET_STATUS_CHOICES, default="ACTIVE"
    )
    # Location
    location = models.CharField(_("Location"), max_length=200, blank=True)
    # Maintenance
    last_maintenance_date = models.DateField(_("Last maintenance date"), blank=True, null=True)
    next_maintenance_date = models.DateField(_("Next maintenance date"), blank=True, null=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = ("Asset Financial Tracking")
        verbose_name_plural = ("Asset Financial Tracking")
        ordering = ("-acquisition_date", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.asset_number})"

    @property
    def book_value(self) -> float:
        return float(self.acquisition_cost - self.accumulated_depreciation)


class FinancialForecast(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Financial forecasting."""

    FORECAST_TYPE_CHOICES = [
        ("REVENUE", ("Revenue Forecast")),
        ("EXPENDITURE", ("Expenditure Forecast")),
        ("CASH_FLOW", ("Cash Flow Forecast")),
        ("BUDGET", ("Budget Forecast")),
    ]

    FORECAST_STATUS_CHOICES = [
        ("DRAFT", ("Draft")),
        ("APPROVED", ("Approved")),
        ("ACTIVE", ("Active")),
        ("EXPIRED", ("Expired")),
    ]

    name = models.CharField(_("Forecast name"), max_length=200)
    forecast_number = models.CharField(_("Forecast number"), max_length=50, unique=True)
    forecast_type = models.CharField(
        _("Forecast type"), max_length=20, choices=FORECAST_TYPE_CHOICES, default="REVENUE"
    )
    financial_year = models.ForeignKey(
        FinancialYear,
        on_delete=models.CASCADE,
        related_name="financial_forecasts",
        verbose_name=_("Financial year"),
    )
    # Forecast details
    forecast_period_start = models.DateField(_("Forecast period start"))
    forecast_period_end = models.DateField(_("Forecast period end"))
    # Financial projections
    projected_income = models.DecimalField(
        ("Projected income"), max_digits=15, decimal_places=2, default=0
    )
    projected_expenditure = models.DecimalField(
        ("Projected expenditure"), max_digits=15, decimal_places=2, default=0
    )
    projected_surplus_deficit = models.DecimalField(
        ("Projected surplus/deficit"), max_digits=15, decimal_places=2, default=0
    )
    # Assumptions
    assumptions = models.TextField(_("Assumptions"), blank=True)
    # Status
    status = models.CharField(
        ("Status"), max_length=20, choices=FORECAST_STATUS_CHOICES, default="DRAFT"
    )
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = ("Financial Forecast")
        verbose_name_plural = ("Financial Forecasts")
        ordering = ("-forecast_period_start", "name")

    def __str__(self) -> str:
        return f"{self.name} ({self.forecast_number})"


class Budget(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Organizational budget planning."""

    name = models.CharField(_("Budget name"), max_length=200)
    code = models.CharField(_("Budget code"), max_length=50, unique=True)
    budget_type = models.CharField(
        ("Budget type"), max_length=20, choices=BudgetType.choices, default=BudgetType.ANNUAL
    )
    financial_year = models.ForeignKey(
        FinancialYear,
        on_delete=models.CASCADE,
        related_name="budgets",
        verbose_name=_("Financial year"),
    )
    total_amount = models.DecimalField(
        ("Total amount"), max_digits=15, decimal_places=2
    )
    allocated_amount = models.DecimalField(
        ("Allocated amount"), max_digits=15, decimal_places=2, default=0
    )
    spent_amount = models.DecimalField(
        ("Spent amount"), max_digits=15, decimal_places=2, default=0
    )
    # Additional fields for budget monitoring
    start_date = models.DateField(_("Start date"), null=True, blank=True)
    end_date = models.DateField(_("End date"), null=True, blank=True)
    is_revised = models.BooleanField(_("Is revised"), default=False)
    revised_amount = models.DecimalField(
        ("Revised amount"), max_digits=15, decimal_places=2, null=True, blank=True
    )
    # For programme/project/departmental budgets
    programme = models.CharField(_("Programme"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    department = models.CharField(_("Department"), max_length=100, blank=True)
    activity = models.CharField(_("Activity"), max_length=200, blank=True)
    grant = models.CharField(_("Grant"), max_length=200, blank=True)
    description = models.TextField(_("Description"), blank=True)
    is_active = models.BooleanField(_("Active"), default=True, db_index=True)

    class Meta:
        verbose_name = _("Budget")
        verbose_name_plural = ("Budgets")
        ordering = ("-financial_year", "-start_date", "name")

    def __str__(self) -> str:
        return f"{self.name} - {self.financial_year} ({self.get_budget_type_display()})"

    @property
    def remaining(self) -> float:
        budget_amount = self.revised_amount if self.is_revised and self.revised_amount else self.total_amount
        return float(budget_amount - self.spent_amount)

    @property
    def variance_percentage(self) -> float:
        if self.allocated_amount == 0:
            return 0.0
        return float((self.spent_amount - self.allocated_amount) / self.allocated_amount * 100)


class Transaction(UUIDModel, TimeStampedModel):
    """Financial transaction record."""

    STATUS_CHOICES = TransactionStatus.choices

    reference_number = models.CharField(
        ("Reference number"), max_length=80, unique=True, db_index=True
    )
    transaction_type = models.CharField(
        ("Transaction type"), max_length=20, choices=TransactionType.choices
    )
    status = models.CharField(
        ("Status"),
        max_length=20,
        choices=STATUS_CHOICES,
        default=TransactionStatus.DRAFT,
    )
    source = models.CharField(
        ("Resource source"), max_length=20, choices=ResourceSource.choices
    )
    amount = models.DecimalField(_("Amount"), max_digits=15, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=10, default="USD")
    description = models.TextField(_("Description"), blank=True)
    beneficiary = models.CharField(_("Beneficiary"), max_length=200, blank=True)
    program = models.CharField(_("Program"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    approval_status = models.CharField(_("Approval status"), max_length=20, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_transactions",
    )
    payment_method = models.CharField(
        ("Payment method"), max_length=20, choices=PaymentMethod.choices, blank=True
    )
    receipt_date = models.DateField(_("Receipt date"), null=True, blank=True)
    due_date = models.DateField(_("Due date"), null=True, blank=True)
    is_sensitive = models.BooleanField(
        ("Sensitive data"), default=False, db_index=True
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = ("Transactions")
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["transaction_type", "status"]),
            models.Index(fields=["source", "status"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        ref = self.reference_number
        ttype = self.get_transaction_type_display()
        amount = str(self.amount)
        currency = self.currency
        return f"{ref} - {ttype} {amount} {currency}"


class BudgetAllocation(UUIDModel, TimeStampedModel):
    """Budget allocation to programs/projects."""

    budget = models.ForeignKey(
        Budget,
        on_delete=models.CASCADE,
        related_name="allocations",
        verbose_name=_("Budget"),
    )
    program = models.CharField(_("Program"), max_length=200, blank=True)
    project = models.CharField(_("Project"), max_length=200, blank=True)
    allocated_amount = models.DecimalField(
        ("Allocated amount"), max_digits=15, decimal_places=2
    )
    spent_amount = models.DecimalField(
        ("Spent amount"), max_digits=15, decimal_places=2, default=0
    )
    percentage = models.PositiveSmallIntegerField(_("Percentage"), default=0)
    description = models.TextField(_("Description"), blank=True)

    class Meta:
        verbose_name = _("Budget Allocation")
        verbose_name_plural = ("Budget Allocations")
        unique_together = ("budget", "program", "project")

    def __str__(self) -> str:
        return f"{self.budget} - {self.program or self.project}"
