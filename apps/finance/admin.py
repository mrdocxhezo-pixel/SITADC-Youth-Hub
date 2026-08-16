"""Admin configuration for the Finance and Resource Mobilization (Phase 28)."""

from django.contrib import admin

from .models import (
    FinancialYear,
    FinancialAccount,
    BankAccount,
    PettyCash,
    Grant,
    Donor,
    Sponsor,
    FundraisingCampaign,
    ProcurementFinancialTracking,
    AssetFinancialTracking,
    FinancialForecast,
    Budget,
    Transaction,
    BudgetAllocation,
)


@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ("name", "start_month", "is_active")
    list_filter = ("is_active", "start_month")
    search_fields = ("name",)


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "account_type", "is_active")
    list_filter = ("account_type", "is_active")
    search_fields = ("name", "code")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "account_number",
        "bank_name",
        "account_type",
        "currency",
        "current_balance",
        "is_active",
    )
    list_filter = ("account_type", "currency", "is_active")
    search_fields = ("name", "account_number", "bank_name")


@admin.register(PettyCash)
class PettyCashAdmin(admin.ModelAdmin):
    list_display = ("name", "custodian", "opening_balance", "current_balance", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "custodian")


@admin.register(Grant)
class GrantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "grant_number",
        "funding_agency",
        "amount_awarded",
        "status",
        "is_active",
    )
    list_filter = ("status", "is_active")
    search_fields = ("name", "grant_number", "funding_agency")
    raw_id_fields = ()


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ("name", "donor_number", "donor_type", "total_donated", "status", "is_active")
    list_filter = ("donor_type", "status", "is_active")
    search_fields = ("name", "donor_number", "contact_person")


@admin.register(Sponsor)
class SponsorAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sponsor_number",
        "sponsor_type",
        "sponsorship_type",
        "sponsored_amount",
        "status",
        "is_active",
    )
    list_filter = ("sponsor_type", "sponsorship_type", "status", "is_active")
    search_fields = ("name", "sponsor_number", "contact_person")


@admin.register(FundraisingCampaign)
class FundraisingCampaignAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "campaign_number",
        "campaign_type",
        "target_amount",
        "amount_raised",
        "status",
        "is_active",
    )
    list_filter = ("campaign_type", "status", "is_active")
    search_fields = ("name", "campaign_number")
    raw_id_fields = ("donor", "sponsor")


@admin.register(ProcurementFinancialTracking)
class ProcurementFinancialTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "procurement_number",
        "estimated_cost",
        "actual_cost",
        "status",
        "is_active",
    )
    list_filter = ("status", "is_active")
    search_fields = ("name", "procurement_number", "supplier_name")


@admin.register(AssetFinancialTracking)
class AssetFinancialTrackingAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "asset_number",
        "asset_type",
        "acquisition_cost",
        "current_value",
        "status",
        "is_active",
    )
    list_filter = ("asset_type", "status", "is_active")
    search_fields = ("name", "asset_number")


@admin.register(FinancialForecast)
class FinancialForecastAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "forecast_number",
        "forecast_type",
        "financial_year",
        "projected_income",
        "projected_expenditure",
        "status",
        "is_active",
    )
    list_filter = ("forecast_type", "status", "is_active", "financial_year")
    search_fields = ("name", "forecast_number")
    raw_id_fields = ("financial_year",)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "financial_year",
        "budget_type",
        "total_amount",
        "allocated_amount",
        "spent_amount",
        "is_active",
    )
    list_filter = ("financial_year", "budget_type", "is_active")
    search_fields = ("name", "code")
    raw_id_fields = ("financial_year",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "reference_number",
        "transaction_type",
        "status",
        "source",
        "amount",
        "currency",
        "created_at",
    )
    list_filter = ("transaction_type", "status", "source")
    search_fields = ("reference_number", "description")
    raw_id_fields = ("approved_by",)


@admin.register(BudgetAllocation)
class BudgetAllocationAdmin(admin.ModelAdmin):
    list_display = (
        "budget",
        "program",
        "project",
        "allocated_amount",
        "spent_amount",
        "percentage",
    )
    list_filter = ("budget",)
    search_fields = ("budget__name", "program", "project")
