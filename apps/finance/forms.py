"""Forms for the Finance and Resource Mobilization (Phase 28)."""

from __future__ import annotations

from django import forms

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


class FinancialYearForm(forms.ModelForm):
    """Create/update a financial year."""

    class Meta:
        model = FinancialYear
        fields = ["name", "start_month", "is_active"]
        widgets = {
            "start_month": forms.NumberInput(attrs={"min": 1, "max": 12}),
        }


class FinancialAccountForm(forms.ModelForm):
    """Create/update a financial account."""

    class Meta:
        model = FinancialAccount
        fields = ["name", "code", "account_type", "description", "is_active"]


class BankAccountForm(forms.ModelForm):
    """Create/update a bank account."""

    class Meta:
        model = BankAccount
        fields = [
            "name",
            "account_number",
            "bank_name",
            "bank_branch",
            "account_type",
            "currency",
            "opening_balance",
            "current_balance",
            "is_active",
            "reconciliation_date",
            "swift_code",
            "routing_number",
        ]
        widgets = {
            "opening_balance": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "current_balance": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "reconciliation_date": forms.DateInput(attrs={"type": "date"}),
        }


class PettyCashForm(forms.ModelForm):
    """Create/update a petty cash."""

    class Meta:
        model = PettyCash
        fields = [
            "name",
            "custodian",
            "custodian_position",
            "opening_balance",
            "current_balance",
            "max_limit",
            "currency",
            "is_active",
            "last_replenished",
            "replenishment_approval_level",
        ]
        widgets = {
            "opening_balance": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "current_balance": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "max_limit": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "last_replenished": forms.DateInput(attrs={"type": "date"}),
        }


class GrantForm(forms.ModelForm):
    """Create/update a grant."""

    class Meta:
        model = Grant
        fields = [
            "name",
            "grant_number",
            "funding_agency",
            "grant_type",
            "amount_awarded",
            "currency",
            "award_date",
            "start_date",
            "end_date",
            "status",
            "programme",
            "project",
            "reporting_frequency",
            "next_report_due",
            "special_conditions",
            "is_active",
        ]
        widgets = {
            "amount_awarded": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "award_date": forms.DateInput(attrs={"type": "date"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "next_report_due": forms.DateInput(attrs={"type": "date"}),
        }


class DonorForm(forms.ModelForm):
    """Create/update a donor."""

    class Meta:
        model = Donor
        fields = [
            "name",
            "donor_number",
            "donor_type",
            "contact_person",
            "email",
            "phone",
            "address",
            "website",
            "status",
            "total_donated",
            "year_to_date_donated",
            "last_donation_date",
            "preferred_contact_method",
            "communication_preferences",
            "is_active",
        ]
        widgets = {
            "total_donated": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "year_to_date_donated": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "last_donation_date": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(),
            "website": forms.URLInput(),
        }


class SponsorForm(forms.ModelForm):
    """Create/update a sponsor."""

    class Meta:
        model = Sponsor
        fields = [
            "name",
            "sponsor_number",
            "sponsor_type",
            "sponsorship_type",
            "contact_person",
            "email",
            "phone",
            "address",
            "website",
            "sponsored_amount",
            "start_date",
            "end_date",
            "status",
            "programme",
            "project",
            "event",
            "benefits_received",
            "reporting_frequency",
            "next_report_due",
            "is_active",
        ]
        widgets = {
            "sponsored_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "next_report_due": forms.DateInput(attrs={"type": "date"}),
            "email": forms.EmailInput(),
            "website": forms.URLInput(),
        }


class FundraisingCampaignForm(forms.ModelForm):
    """Create/update a fundraising campaign."""

    class Meta:
        model = FundraisingCampaign
        fields = [
            "name",
            "campaign_number",
            "campaign_type",
            "description",
            "start_date",
            "end_date",
            "target_amount",
            "currency",
            "amount_raised",
            "status",
            "donor",
            "sponsor",
            "progress_notes",
            "is_active",
        ]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "target_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "amount_raised": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
        }


class ProcurementFinancialTrackingForm(forms.ModelForm):
    """Create/update procurement financial tracking."""

    class Meta:
        model = ProcurementFinancialTracking
        fields = [
            "name",
            "procurement_number",
            "description",
            "estimated_cost",
            "actual_cost",
            "currency",
            "required_date",
            "promised_date",
            "actual_delivery_date",
            "status",
            "budget_line",
            "programme",
            "project",
            "supplier_name",
            "supplier_contact",
            "payment_terms",
            "is_active",
        ]
        widgets = {
            "estimated_cost": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "actual_cost": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "required_date": forms.DateInput(attrs={"type": "date"}),
            "promised_date": forms.DateInput(attrs={"type": "date"}),
            "actual_delivery_date": forms.DateInput(attrs={"type": "date"}),
        }


class AssetFinancialTrackingForm(forms.ModelForm):
    """Create/update asset financial tracking."""

    class Meta:
        model = AssetFinancialTracking
        fields = [
            "name",
            "asset_number",
            "asset_type",
            "description",
            "acquisition_cost",
            "current_value",
            "acquisition_date",
            "depreciation_method",
            "useful_life_years",
            "annual_depreciation",
            "accumulated_depreciation",
            "status",
            "location",
            "last_maintenance_date",
            "next_maintenance_date",
            "is_active",
        ]
        widgets = {
            "acquisition_cost": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "current_value": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "acquisition_date": forms.DateInput(attrs={"type": "date"}),
            "annual_depreciation": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "accumulated_depreciation": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "last_maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "next_maintenance_date": forms.DateInput(attrs={"type": "date"}),
            "useful_life_years": forms.NumberInput(attrs={"min": "1"}),
        }


class FinancialForecastForm(forms.ModelForm):
    """Create/update a financial forecast."""

    class Meta:
        model = FinancialForecast
        fields = [
            "name",
            "forecast_number",
            "forecast_type",
            "financial_year",
            "forecast_period_start",
            "forecast_period_end",
            "projected_income",
            "projected_expenditure",
            "projected_surplus_deficit",
            "assumptions",
            "status",
            "is_active",
        ]
        widgets = {
            "forecast_period_start": forms.DateInput(attrs={"type": "date"}),
            "forecast_period_end": forms.DateInput(attrs={"type": "date"}),
            "projected_income": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "projected_expenditure": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "projected_surplus_deficit": forms.NumberInput(attrs={"step": "0.01"}),
        }


class BudgetForm(forms.ModelForm):
    """Create/update a budget."""

    class Meta:
        model = Budget
        fields = [
            "name",
            "code",
            "budget_type",
            "financial_year",
            "total_amount",
            "allocated_amount",
            "spent_amount",
            "start_date",
            "end_date",
            "is_revised",
            "revised_amount",
            "programme",
            "project",
            "department",
            "activity",
            "grant",
            "description",
            "is_active",
        ]
        widgets = {
            "total_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "allocated_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "spent_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "revised_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
        }


class TransactionForm(forms.ModelForm):
    """Create/update a financial transaction."""

    class Meta:
        model = Transaction
        fields = [
            "reference_number",
            "transaction_type",
            "status",
            "source",
            "amount",
            "currency",
            "description",
            "beneficiary",
            "program",
            "project",
            "approval_status",
            "approved_by",
            "payment_method",
            "receipt_date",
            "due_date",
            "is_sensitive",
        ]
        widgets = {
            "receipt_date": forms.DateInput(attrs={"type": "date"}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }


class BudgetAllocationForm(forms.ModelForm):
    """Create/update a budget allocation."""

    class Meta:
        model = BudgetAllocation
        fields = ["budget", "program", "project", "allocated_amount", "description"]
