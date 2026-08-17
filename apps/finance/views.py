"""Views for Finance and Resource Mobilization (Phase 28)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AssetFinancialTrackingForm,
    BankAccountForm,
    BudgetAllocationForm,
    BudgetForm,
    DonorForm,
    FinancialAccountForm,
    FinancialForecastForm,
    FinancialYearForm,
    FundraisingCampaignForm,
    GrantForm,
    PettyCashForm,
    ProcurementFinancialTrackingForm,
    SponsorForm,
    TransactionForm,
)
from .models import (
    AssetFinancialTracking,
    BankAccount,
    Budget,
    BudgetAllocation,
    Donor,
    FinancialAccount,
    FinancialForecast,
    FinancialYear,
    FundraisingCampaign,
    Grant,
    PettyCash,
    ProcurementFinancialTracking,
    Sponsor,
    Transaction,
)
from .providers.analytics import FinanceAnalyticsProvider
from .providers.budgeting import BudgetingProvider

# Import providers
from .providers.dashboard import FinanceDashboardProvider
from .providers.donors import DonorsProvider
from .providers.fundraising import FundraisingProvider
from .providers.grants import GrantsProvider
from .providers.reports import FinanceReportsProvider
from .providers.sponsors import SponsorsProvider
from .providers.transactions import TransactionsProvider
from .renderers.csv import FinanceCSVRenderer
from .renderers.docx import FinanceDocxRenderer

# Import renderers
from .renderers.pdf import FinancePDFRenderer
from .renderers.print_html import FinancePrintHTMLRenderer
from .renderers.xlsx import FinanceExcelRenderer


# Generic view functions for CRUD operations
def object_list(request, model, template_name, context_name, paginate_by=25):
    """Generic list view for a model."""
    queryset = model.objects.all()
    search_query = request.GET.get("search", "")
    if search_query:
        search_fields = [
            field.name
            for field in model._meta.fields
            if field.name
            in (
                "name",
                "title",
                "code",
                "reference_number",
                "grant_number",
                "donor_number",
                "description",
            )
        ]
        q_objects = Q()
        for field in search_fields:
            q_objects |= Q(**{f"{field}__icontains": search_query})
        if q_objects:
            queryset = queryset.filter(q_objects)
    paginator = Paginator(queryset, paginate_by)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        context_name: page_obj,
        "search_query": search_query,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, template_name, context)


def object_create(
    request,
    model_form,
    success_url,
    success_message,
    template_name="finance/object_form.html",
):
    """Generic create view for a model."""
    if request.method == "POST":
        form = model_form(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "created_by"):
                obj.created_by = request.user
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form()
    context = {
        "form": form,
        "list_url": success_url,
    }
    return render(request, template_name, context)


def object_update(
    request,
    model,
    model_form,
    pk,
    success_url,
    success_message,
    template_name="finance/object_form.html",
):
    """Generic update view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        form = model_form(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            obj.save()
            messages.success(request, success_message)
            return redirect(success_url)
    else:
        form = model_form(instance=obj)
    context = {
        "form": form,
        "object": obj,
        "list_url": success_url,
    }
    return render(request, template_name, context)


def object_delete(
    request,
    model,
    pk,
    success_url,
    success_message,
    template_name="finance/object_confirm_delete.html",
):
    """Generic delete view for a model."""
    obj = get_object_or_404(model, pk=pk)
    if request.method == "POST":
        obj.delete()
        messages.success(request, success_message)
        return redirect(success_url)
    context = {
        "object": obj,
        "list_url": success_url,
    }
    return render(request, template_name, context)


def object_detail(request, model, pk, list_url, template_name, context_name):
    """Generic detail view for a model."""
    obj = get_object_or_404(model, pk=pk)
    context = {
        context_name: obj,
        "list_url": list_url,
    }
    return render(request, template_name, context)


# FinancialAccount Views
@login_required
def financial_account_list(request):
    return object_list(
        request,
        FinancialAccount,
        "finance/financial_account_list.html",
        "financial_accounts",
    )


@login_required
def financial_account_create(request):
    return object_create(
        request,
        FinancialAccountForm,
        "finance:financial_account_list",
        "Financial account created successfully.",
    )


@login_required
def financial_account_update(request, pk):
    return object_update(
        request,
        FinancialAccount,
        FinancialAccountForm,
        pk,
        "finance:financial_account_list",
        "Financial account updated successfully.",
    )


@login_required
def financial_account_delete(request, pk):
    return object_delete(
        request,
        FinancialAccount,
        pk,
        "finance:financial_account_list",
        "Financial account deleted successfully.",
    )


@login_required
def financial_account_detail(request, pk):
    return object_detail(
        request,
        FinancialAccount,
        pk,
        "finance:financial_account_list",
        "finance/financial_account_detail.html",
        "financial_account",
    )


# BankAccount Views
@login_required
def bank_account_list(request):
    return object_list(
        request, BankAccount, "finance/bank_account_list.html", "bank_accounts"
    )


@login_required
def bank_account_create(request):
    return object_create(
        request,
        BankAccountForm,
        "finance:bank_account_list",
        "Bank account created successfully.",
    )


@login_required
def bank_account_update(request, pk):
    return object_update(
        request,
        BankAccount,
        BankAccountForm,
        pk,
        "finance:bank_account_list",
        "Bank account updated successfully.",
    )


@login_required
def bank_account_delete(request, pk):
    return object_delete(
        request,
        BankAccount,
        pk,
        "finance:bank_account_list",
        "Bank account deleted successfully.",
    )


@login_required
def bank_account_detail(request, pk):
    return object_detail(
        request,
        BankAccount,
        pk,
        "finance:bank_account_list",
        "finance/bank_account_detail.html",
        "bank_account",
    )


# PettyCash Views
@login_required
def petty_cash_list(request):
    return object_list(
        request, PettyCash, "finance/petty_cash_list.html", "petty_cashes"
    )


@login_required
def petty_cash_create(request):
    return object_create(
        request,
        PettyCashForm,
        "finance:petty_cash_list",
        "Petty cash created successfully.",
    )


@login_required
def petty_cash_update(request, pk):
    return object_update(
        request,
        PettyCash,
        PettyCashForm,
        pk,
        "finance:petty_cash_list",
        "Petty cash updated successfully.",
    )


@login_required
def petty_cash_delete(request, pk):
    return object_delete(
        request,
        PettyCash,
        pk,
        "finance:petty_cash_list",
        "Petty cash deleted successfully.",
    )


@login_required
def petty_cash_detail(request, pk):
    return object_detail(
        request,
        PettyCash,
        pk,
        "finance:petty_cash_list",
        "finance/petty_cash_detail.html",
        "petty_cash",
    )


# FinancialYear Views
@login_required
def financial_year_list(request):
    return object_list(
        request, FinancialYear, "finance/financial_year_list.html", "financial_years"
    )


@login_required
def financial_year_create(request):
    return object_create(
        request,
        FinancialYearForm,
        "finance:financial_year_list",
        "Financial year created successfully.",
    )


@login_required
def financial_year_update(request, pk):
    return object_update(
        request,
        FinancialYear,
        FinancialYearForm,
        pk,
        "finance:financial_year_list",
        "Financial year updated successfully.",
    )


@login_required
def financial_year_delete(request, pk):
    return object_delete(
        request,
        FinancialYear,
        pk,
        "finance:financial_year_list",
        "Financial year deleted successfully.",
    )


@login_required
def financial_year_detail(request, pk):
    return object_detail(
        request,
        FinancialYear,
        pk,
        "finance:financial_year_list",
        "finance/financial_year_detail.html",
        "financial_year",
    )


# Grant Views
@login_required
def grant_list(request):
    return object_list(request, Grant, "finance/grant_list.html", "grants")


@login_required
def grant_create(request):
    return object_create(
        request, GrantForm, "finance:grant_list", "Grant created successfully."
    )


@login_required
def grant_update(request, pk):
    return object_update(
        request,
        Grant,
        GrantForm,
        pk,
        "finance:grant_list",
        "Grant updated successfully.",
    )


@login_required
def grant_delete(request, pk):
    return object_delete(
        request, Grant, pk, "finance:grant_list", "Grant deleted successfully."
    )


@login_required
def grant_detail(request, pk):
    return object_detail(
        request, Grant, pk, "finance:grant_list", "finance/grant_detail.html", "grant"
    )


# Donor Views
@login_required
def donor_list(request):
    return object_list(request, Donor, "finance/donor_list.html", "donors")


@login_required
def donor_create(request):
    return object_create(
        request, DonorForm, "finance:donor_list", "Donor created successfully."
    )


@login_required
def donor_update(request, pk):
    return object_update(
        request,
        Donor,
        DonorForm,
        pk,
        "finance:donor_list",
        "Donor updated successfully.",
    )


@login_required
def donor_delete(request, pk):
    return object_delete(
        request, Donor, pk, "finance:donor_list", "Donor deleted successfully."
    )


@login_required
def donor_detail(request, pk):
    return object_detail(
        request, Donor, pk, "finance:donor_list", "finance/donor_detail.html", "donor"
    )


# Sponsor Views
@login_required
def sponsor_list(request):
    return object_list(request, Sponsor, "finance/sponsor_list.html", "sponsors")


@login_required
def sponsor_create(request):
    return object_create(
        request, SponsorForm, "finance:sponsor_list", "Sponsor created successfully."
    )


@login_required
def sponsor_update(request, pk):
    return object_update(
        request,
        Sponsor,
        SponsorForm,
        pk,
        "finance:sponsor_list",
        "Sponsor updated successfully.",
    )


@login_required
def sponsor_delete(request, pk):
    return object_delete(
        request, Sponsor, pk, "finance:sponsor_list", "Sponsor deleted successfully."
    )


@login_required
def sponsor_detail(request, pk):
    return object_detail(
        request,
        Sponsor,
        pk,
        "finance:sponsor_list",
        "finance/sponsor_detail.html",
        "sponsor",
    )


# FundraisingCampaign Views
@login_required
def fundraising_campaign_list(request):
    return object_list(
        request,
        FundraisingCampaign,
        "finance/fundraising_campaign_list.html",
        "fundraising_campaigns",
    )


@login_required
def fundraising_campaign_create(request):
    return object_create(
        request,
        FundraisingCampaignForm,
        "finance:fundraising_campaign_list",
        "Fundraising campaign created successfully.",
    )


@login_required
def fundraising_campaign_update(request, pk):
    return object_update(
        request,
        FundraisingCampaign,
        FundraisingCampaignForm,
        pk,
        "finance:fundraising_campaign_list",
        "Fundraising campaign updated successfully.",
    )


@login_required
def fundraising_campaign_delete(request, pk):
    return object_delete(
        request,
        FundraisingCampaign,
        pk,
        "finance:fundraising_campaign_list",
        "Fundraising campaign deleted successfully.",
    )


@login_required
def fundraising_campaign_detail(request, pk):
    return object_detail(
        request,
        FundraisingCampaign,
        pk,
        "finance:fundraising_campaign_list",
        "finance/fundraising_campaign_detail.html",
        "fundraising_campaign",
    )


# ProcurementFinancialTracking Views
@login_required
def procurement_financial_tracking_list(request):
    return object_list(
        request,
        ProcurementFinancialTracking,
        "finance/procurement_financial_tracking_list.html",
        "procurement_financial_trackings",
    )


@login_required
def procurement_financial_tracking_create(request):
    return object_create(
        request,
        ProcurementFinancialTrackingForm,
        "finance:procurement_financial_tracking_list",
        "Procurement financial tracking created successfully.",
    )


@login_required
def procurement_financial_tracking_update(request, pk):
    return object_update(
        request,
        ProcurementFinancialTracking,
        ProcurementFinancialTrackingForm,
        pk,
        "finance:procurement_financial_tracking_list",
        "Procurement financial tracking updated successfully.",
    )


@login_required
def procurement_financial_tracking_delete(request, pk):
    return object_delete(
        request,
        ProcurementFinancialTracking,
        pk,
        "finance:procurement_financial_tracking_list",
        "Procurement financial tracking deleted successfully.",
    )


@login_required
def procurement_financial_tracking_detail(request, pk):
    return object_detail(
        request,
        ProcurementFinancialTracking,
        pk,
        "finance:procurement_financial_tracking_list",
        "finance/procurement_financial_tracking_detail.html",
        "procurement_financial_tracking",
    )


# AssetFinancialTracking Views
@login_required
def asset_financial_tracking_list(request):
    return object_list(
        request,
        AssetFinancialTracking,
        "finance/asset_financial_tracking_list.html",
        "asset_financial_trackings",
    )


@login_required
def asset_financial_tracking_create(request):
    return object_create(
        request,
        AssetFinancialTrackingForm,
        "finance:asset_financial_tracking_list",
        "Asset financial tracking created successfully.",
    )


@login_required
def asset_financial_tracking_update(request, pk):
    return object_update(
        request,
        AssetFinancialTracking,
        AssetFinancialTrackingForm,
        pk,
        "finance:asset_financial_tracking_list",
        "Asset financial tracking updated successfully.",
    )


@login_required
def asset_financial_tracking_delete(request, pk):
    return object_delete(
        request,
        AssetFinancialTracking,
        pk,
        "finance:asset_financial_tracking_list",
        "Asset financial tracking deleted successfully.",
    )


@login_required
def asset_financial_tracking_detail(request, pk):
    return object_detail(
        request,
        AssetFinancialTracking,
        pk,
        "finance:asset_financial_tracking_list",
        "finance/asset_financial_tracking_detail.html",
        "asset_financial_tracking",
    )


# FinancialForecast Views
@login_required
def financial_forecast_list(request):
    return object_list(
        request,
        FinancialForecast,
        "finance/financial_forecast_list.html",
        "financial_forecasts",
    )


@login_required
def financial_forecast_create(request):
    return object_create(
        request,
        FinancialForecastForm,
        "finance:financial_forecast_list",
        "Financial forecast created successfully.",
    )


@login_required
def financial_forecast_update(request, pk):
    return object_update(
        request,
        FinancialForecast,
        FinancialForecastForm,
        pk,
        "finance:financial_forecast_list",
        "Financial forecast updated successfully.",
    )


@login_required
def financial_forecast_delete(request, pk):
    return object_delete(
        request,
        FinancialForecast,
        pk,
        "finance:financial_forecast_list",
        "Financial forecast deleted successfully.",
    )


@login_required
def financial_forecast_detail(request, pk):
    return object_detail(
        request,
        FinancialForecast,
        pk,
        "finance:financial_forecast_list",
        "finance/financial_forecast_detail.html",
        "financial_forecast",
    )


# Budget Views
@login_required
def budget_list(request):
    return object_list(request, Budget, "finance/budget_list.html", "budgets")


@login_required
def budget_create(request):
    return object_create(
        request, BudgetForm, "finance:budget_list", "Budget created successfully."
    )


@login_required
def budget_update(request, pk):
    return object_update(
        request,
        Budget,
        BudgetForm,
        pk,
        "finance:budget_list",
        "Budget updated successfully.",
    )


@login_required
def budget_delete(request, pk):
    return object_delete(
        request, Budget, pk, "finance:budget_list", "Budget deleted successfully."
    )


@login_required
def budget_detail(request, pk):
    return object_detail(
        request,
        Budget,
        pk,
        "finance:budget_list",
        "finance/budget_detail.html",
        "budget",
    )


# Transaction Views
@login_required
def transaction_list(request):
    return object_list(
        request, Transaction, "finance/transaction_list.html", "transactions"
    )


@login_required
def transaction_create(request):
    return object_create(
        request,
        TransactionForm,
        "finance:transaction_list",
        "Transaction created successfully.",
    )


@login_required
def transaction_update(request, pk):
    return object_update(
        request,
        Transaction,
        TransactionForm,
        pk,
        "finance:transaction_list",
        "Transaction updated successfully.",
    )


@login_required
def transaction_delete(request, pk):
    return object_delete(
        request,
        Transaction,
        pk,
        "finance:transaction_list",
        "Transaction deleted successfully.",
    )


@login_required
def transaction_detail(request, pk):
    return object_detail(
        request,
        Transaction,
        pk,
        "finance:transaction_list",
        "finance/transaction_detail.html",
        "transaction",
    )


# Budget Allocation Views
@login_required
def budget_allocation_list(request):
    return object_list(
        request,
        BudgetAllocation,
        "finance/budget_allocation_list.html",
        "budget_allocations",
    )


@login_required
def budget_allocation_create(request):
    return object_create(
        request,
        BudgetAllocationForm,
        "finance:budget_allocation_list",
        "Budget allocation created successfully.",
    )


@login_required
def budget_allocation_update(request, pk):
    return object_update(
        request,
        BudgetAllocation,
        BudgetAllocationForm,
        pk,
        "finance:budget_allocation_list",
        "Budget allocation updated successfully.",
    )


@login_required
def budget_allocation_delete(request, pk):
    return object_delete(
        request,
        BudgetAllocation,
        pk,
        "finance:budget_allocation_list",
        "Budget allocation deleted successfully.",
    )


@login_required
def budget_allocation_detail(request, pk):
    return object_detail(
        request,
        BudgetAllocation,
        pk,
        "finance:budget_allocation_list",
        "finance/budget_allocation_detail.html",
        "budget_allocation",
    )


# Dashboard Views
@login_required
def dashboard(request):
    """Finance dashboard view."""
    provider = FinanceDashboardProvider(request.user)

    context = {
        "financial_summary": provider.get_financial_summary(),
        "budget_overview": provider.get_budget_overview(),
        "funding_overview": provider.get_funding_overview(),
        "recent_transactions": provider.get_recent_transactions(),
        "budget_status": provider.get_budget_status(),
        "funding_sources": provider.get_funding_sources(),
    }

    return render(request, "finance/dashboard.html", context)


# Reporting Views
@login_required
def reports_income_statement(request):
    """Income statement report view."""
    provider = FinanceReportsProvider(request.user)

    # Get date range from request or use default (current year)
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        start_date = timezone.now().replace(month=1, day=1)

    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        end_date = timezone.now()

    data = provider.get_income_statement(start_date, end_date)
    data["title"] = "Income Statement"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "income_statement")

    context = {
        "report_data": data,
        "report_type": "income_statement",
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "finance/report_income_statement.html", context)


@login_required
def reports_balance_sheet(request):
    """Balance sheet report view."""
    provider = FinanceReportsProvider(request.user)

    # Get date from request or use current date
    date_str = request.GET.get("date")
    if date_str:
        as_of_date = timezone.datetime.strptime(date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        as_of_date = timezone.now()

    data = provider.get_balance_sheet(as_of_date)
    data["title"] = "Balance Sheet"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "balance_sheet")

    context = {
        "report_data": data,
        "report_type": "balance_sheet",
        "as_of_date": as_of_date,
    }

    return render(request, "finance/report_balance_sheet.html", context)


@login_required
def reports_cash_flow(request):
    """Cash flow statement report view."""
    provider = FinanceReportsProvider(request.user)

    # Get date range from request or use default (current year)
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        start_date = timezone.now().replace(month=1, day=1)

    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        end_date = timezone.now()

    data = provider.get_cash_flow_statement(start_date, end_date)
    data["title"] = "Cash Flow Statement"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "cash_flow")

    context = {
        "report_data": data,
        "report_type": "cash_flow",
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "finance/report_cash_flow.html", context)


@login_required
def reports_grant_summary(request):
    """Grant summary report view."""
    provider = FinanceReportsProvider(request.user)

    grant_id = request.GET.get("grant_id")
    if grant_id:
        data = provider.get_grant_report(int(grant_id))
        data["title"] = (
            f'Grant Report: {data.get("grant", {}).get("name", "Unknown Grant")}'
        )
    else:
        data = provider.get_grant_report()
        data["title"] = "Grant Summary Report"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "grant_summary")

    context = {
        "report_data": data,
        "report_type": "grant_summary",
        "grant_id": grant_id,
    }

    return render(request, "finance/report_grant_summary.html", context)


# Analytics Views
@login_required
def analytics_income_trends(request):
    """Income trends analytics view."""
    provider = FinanceAnalyticsProvider(request.user)

    months = int(request.GET.get("months", 12))
    group_by = request.GET.get("group_by", "month")

    data = provider.get_income_trends(months=months, group_by=group_by)
    data["title"] = "Income Trends Analysis"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "income_trends")

    context = {
        "analytics_data": data,
        "analytics_type": "income_trends",
        "months": months,
        "group_by": group_by,
    }

    return render(request, "finance/analytics_income_trends.html", context)


@login_required
def analytics_expense_trends(request):
    """Expense trends analytics view."""
    provider = FinanceAnalyticsProvider(request.user)

    months = int(request.GET.get("months", 12))
    group_by = request.GET.get("group_by", "month")
    by_source = request.GET.get("by_source", "false").lower() == "true"

    data = provider.get_expense_trends(
        months=months, group_by=group_by, by_source=by_source
    )
    data["title"] = "Expense Trends Analysis"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "expense_trends")

    context = {
        "analytics_data": data,
        "analytics_type": "expense_trends",
        "months": months,
        "group_by": group_by,
        "by_source": by_source,
    }

    return render(request, "finance/analytics_expense_trends.html", context)


@login_required
def analytics_budget_variance(request):
    """Budget variance analytics view."""
    provider = FinanceAnalyticsProvider(request.user)

    data = provider.get_budget_variance_analysis()
    data["title"] = "Budget Variance Analysis"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "budget_variance")

    context = {
        "analytics_data": data,
        "analytics_type": "budget_variance",
    }

    return render(request, "finance/analytics_budget_variance.html", context)


@login_required
def analytics_funding_sources(request):
    """Funding sources analytics view."""
    provider = FinanceAnalyticsProvider(request.user)

    data = provider.get_funding_source_analysis()
    data["title"] = "Funding Sources Analysis"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "funding_sources")

    context = {
        "analytics_data": data,
        "analytics_type": "funding_sources",
    }

    return render(request, "finance/analytics_funding_sources.html", context)


# Budgeting Views
@login_required
def budgeting_summary(request):
    """Budgeting summary view."""
    provider = BudgetingProvider(request.user)

    data = provider.get_budget_summary()
    data["title"] = "Budgeting Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "budget_summary")

    context = {
        "budgeting_data": data,
        "budgeting_type": "summary",
    }

    return render(request, "finance/budgeting_summary.html", context)


@login_required
def budgeting_variance_report(request):
    """Budget variance report view."""
    provider = BudgetingProvider(request.user)

    budget_id = request.GET.get("budget_id")
    if budget_id:
        data = provider.get_budget_variance_report(int(budget_id))
        data["title"] = (
            f"Budget Variance Report: "
            f'{data.get("budget", {}).get("name", "Unknown Budget")}'
        )
    else:
        data = provider.get_budget_variance_report()
        data["title"] = "Budget Variance Report"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "budget_variance_report")

    context = {
        "budgeting_data": data,
        "budgeting_type": "variance_report",
        "budget_id": budget_id,
    }

    return render(request, "finance/budgeting_variance_report.html", context)


# Transactions Views
@login_required
def transactions_summary(request):
    """Transactions summary view."""
    provider = TransactionsProvider(request.user)

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")

    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        start_date = timezone.now().replace(month=1, day=1)

    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        end_date = timezone.now()

    data = provider.get_transaction_summary(start_date=start_date, end_date=end_date)
    data["title"] = "Transactions Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "transactions_summary")

    context = {
        "transactions_data": data,
        "transactions_type": "summary",
        "start_date": start_date,
        "end_date": end_date,
    }

    return render(request, "finance/transactions_summary.html", context)


@login_required
def transactions_income(request):
    """Income transactions view."""
    provider = TransactionsProvider(request.user)

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    limit = int(request.GET.get("limit", 100))

    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        start_date = timezone.now().replace(month=1, day=1)

    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        end_date = timezone.now()

    data = provider.get_income_transactions(
        start_date=start_date, end_date=end_date, limit=limit
    )

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "income_transactions")

    context = {
        "transactions_data": data,
        "transactions_type": "income",
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
    }

    return render(request, "finance/transactions_income.html", context)


@login_required
def transactions_expense(request):
    """Expense transactions view."""
    provider = TransactionsProvider(request.user)

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    limit = int(request.GET.get("limit", 100))

    if start_date_str:
        start_date = timezone.datetime.strptime(start_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        start_date = timezone.now().replace(month=1, day=1)

    if end_date_str:
        end_date = timezone.datetime.strptime(end_date_str, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    else:
        end_date = timezone.now()

    data = provider.get_expense_transactions(
        start_date=start_date, end_date=end_date, limit=limit
    )

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "expense_transactions")

    context = {
        "transactions_data": data,
        "transactions_type": "expense",
        "start_date": start_date,
        "end_date": end_date,
        "limit": limit,
    }

    return render(request, "finance/transactions_expense.html", context)


# Grants Views
@login_required
def grants_summary(request):
    """Grants summary view."""
    provider = GrantsProvider(request.user)

    data = provider.get_grants_summary()
    data["title"] = "Grants Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "grants_summary")

    context = {
        "grants_data": data,
        "grants_type": "summary",
    }

    return render(request, "finance/grants_summary.html", context)


@login_required
def grants_funding_trends(request):
    """Grants funding trends view."""
    provider = GrantsProvider(request.user)

    years = int(request.GET.get("years", 5))

    data = provider.get_grant_funding_trends(years=years)
    data["title"] = "Grants Funding Trends"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "grants_funding_trends")

    context = {
        "grants_data": data,
        "grants_type": "funding_trends",
        "years": years,
    }

    return render(request, "finance/grants_funding_trends.html", context)


# Donors Views
@login_required
def donors_summary(request):
    """Donors summary view."""
    provider = DonorsProvider(request.user)

    data = provider.get_donors_summary()
    data["title"] = "Donors Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "donors_summary")

    context = {
        "donors_data": data,
        "donors_type": "summary",
    }

    return render(request, "finance/donors_summary.html", context)


@login_required
def donors_giving_trends(request):
    """Donors giving trends view."""
    provider = DonorsProvider(request.user)

    years = int(request.GET.get("years", 5))

    data = provider.get_donor_giving_trends(years=years)
    data["title"] = "Donors Giving Trends"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "donors_giving_trends")

    context = {
        "donors_data": data,
        "donors_type": "giving_trends",
        "years": years,
    }

    return render(request, "finance/donors_giving_trends.html", context)


# Sponsors Views
@login_required
def sponsors_summary(request):
    """Sponsors summary view."""
    provider = SponsorsProvider(request.user)

    data = provider.get_sponsors_summary()
    data["title"] = "Sponsors Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "sponsors_summary")

    context = {
        "sponsors_data": data,
        "sponsors_type": "summary",
    }

    return render(request, "finance/sponsors_summary.html", context)


@login_required
def sponsors_trends(request):
    """Sponsors trends view."""
    provider = SponsorsProvider(request.user)

    years = int(request.GET.get("years", 5))

    data = provider.get_sponsorship_trends(years=years)
    data["title"] = "Sponsorship Trends"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "sponsors_trends")

    context = {
        "sponsors_data": data,
        "sponsors_type": "trends",
        "years": years,
    }

    return render(request, "finance/sponsors_trends.html", context)


# Fundraising Views
@login_required
def fundraising_summary(request):
    """Fundraising summary view."""
    provider = FundraisingProvider(request.user)

    data = provider.get_fundraising_summary()
    data["title"] = "Fundraising Summary"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "fundraising_summary")

    context = {
        "fundraising_data": data,
        "fundraising_type": "summary",
    }

    return render(request, "finance/fundraising_summary.html", context)


@login_required
def fundraising_trends(request):
    """Fundraising trends view."""
    provider = FundraisingProvider(request.user)

    years = int(request.GET.get("years", 3))

    data = provider.get_fundraising_trends(years=years)
    data["title"] = "Fundraising Trends"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "fundraising_trends")

    context = {
        "fundraising_data": data,
        "fundraising_type": "trends",
        "years": years,
    }

    return render(request, "finance/fundraising_trends.html", context)


@login_required
def fundraising_performance(request):
    """Fundraising performance view."""
    provider = FundraisingProvider(request.user)

    campaign_id = request.GET.get("campaign_id")
    if campaign_id:
        data = provider.get_fundraising_performance_analysis(int(campaign_id))
        data["title"] = (
            f"Fundraising Performance: "
            f'{data.get("campaign", {}).get("name", "Unknown Campaign")}'
        )
    else:
        data = provider.get_fundraising_performance_analysis()
        data["title"] = "Fundraising Performance Analysis"

    # Check if export is requested
    export_format = request.GET.get("export")
    if export_format:
        return _export_report(data, export_format, "fundraising_performance")

    context = {
        "fundraising_data": data,
        "fundraising_type": "performance",
        "campaign_id": campaign_id,
    }

    return render(request, "finance/fundraising_performance.html", context)


# Export Helper Function
def _export_report(data, export_format, report_type):
    """Export report data in the specified format."""
    timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{report_type}_{timestamp}"

    if export_format == "pdf":
        renderer = FinancePDFRenderer(data)
        return renderer.get_http_response(f"{filename}.pdf")
    elif export_format == "xlsx":
        renderer = FinanceExcelRenderer(data)
        return renderer.get_http_response(f"{filename}.xlsx")
    elif export_format == "csv":
        renderer = FinanceCSVRenderer(data)
        return renderer.get_http_response(f"{filename}.csv")
    elif export_format == "docx":
        renderer = FinanceDocxRenderer(data)
        return renderer.get_http_response(f"{filename}.docx")
    elif export_format == "html":
        renderer = FinancePrintHTMLRenderer(data)
        return renderer.get_http_response(f"{filename}.html")
    else:
        # Default to PDF
        renderer = FinancePDFRenderer(data)
        return renderer.get_http_response(f"{filename}.pdf")
