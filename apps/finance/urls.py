"""URL configuration for Finance and Resource Mobilization (Phase 28)."""

from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # FinancialAccount URLs
    path('financial-accounts/', views.financial_account_list, name='financial_account_list'),
    path('financial-accounts/create/', views.financial_account_create, name='financial_account_create'),
    path('financial-accounts/<int:pk>/update/', views.financial_account_update, name='financial_account_update'),
    path('financial-accounts/<int:pk>/delete/', views.financial_account_delete, name='financial_account_delete'),
    path('financial-accounts/<int:pk>/', views.financial_account_detail, name='financial_account_detail'),
    
    # BankAccount URLs
    path('bank-accounts/', views.bank_account_list, name='bank_account_list'),
    path('bank-accounts/create/', views.bank_account_create, name='bank_account_create'),
    path('bank-accounts/<int:pk>/update/', views.bank_account_update, name='bank_account_update'),
    path('bank-accounts/<int:pk>/delete/', views.bank_account_delete, name='bank_account_delete'),
    path('bank-accounts/<int:pk>/', views.bank_account_detail, name='bank_account_detail'),
    
    # PettyCash URLs
    path('petty-cash/', views.petty_cash_list, name='petty_cash_list'),
    path('petty-cash/create/', views.petty_cash_create, name='petty_cash_create'),
    path('petty-cash/<int:pk>/update/', views.petty_cash_update, name='petty_cash_update'),
    path('petty-cash/<int:pk>/delete/', views.petty_cash_delete, name='petty_cash_delete'),
    path('petty-cash/<int:pk>/', views.petty_cash_detail, name='petty_cash_detail'),
    
    # FinancialYear URLs
    path('financial-years/', views.financial_year_list, name='financial_year_list'),
    path('financial-years/create/', views.financial_year_create, name='financial_year_create'),
    path('financial-years/<int:pk>/update/', views.financial_year_update, name='financial_year_update'),
    path('financial-years/<int:pk>/delete/', views.financial_year_delete, name='financial_year_delete'),
    path('financial-years/<int:pk>/', views.financial_year_detail, name='financial_year_detail'),
    
    # Grant URLs
    path('grants/', views.grant_list, name='grant_list'),
    path('grants/create/', views.grant_create, name='grant_create'),
    path('grants/<int:pk>/update/', views.grant_update, name='grant_update'),
    path('grants/<int:pk>/delete/', views.grant_delete, name='grant_delete'),
    path('grants/<int:pk>/', views.grant_detail, name='grant_detail'),
    
    # Donor URLs
    path('donors/', views.donor_list, name='donor_list'),
    path('donors/create/', views.donor_create, name='donor_create'),
    path('donors/<int:pk>/update/', views.donor_update, name='donor_update'),
    path('donors/<int:pk>/delete/', views.donor_delete, name='donor_delete'),
    path('donors/<int:pk>/', views.donor_detail, name='donor_detail'),
    
    # Sponsor URLs
    path('sponsors/', views.sponsor_list, name='sponsor_list'),
    path('sponsors/create/', views.sponsor_create, name='sponsor_create'),
    path('sponsors/<int:pk>/update/', views.sponsor_update, name='sponsor_update'),
    path('sponsors/<int:pk>/delete/', views.sponsor_delete, name='sponsor_delete'),
    path('sponsors/<int:pk>/', views.sponsor_detail, name='sponsor_detail'),
    
    # FundraisingCampaign URLs
    path('fundraising-campaigns/', views.fundraising_campaign_list, name='fundraising_campaign_list'),
    path('fundraising-campaigns/create/', views.fundraising_campaign_create, name='fundraising_campaign_create'),
    path('fundraising-campaigns/<int:pk>/update/', views.fundraising_campaign_update, name='fundraising_campaign_update'),
    path('fundraising-campaigns/<int:pk>/delete/', views.fundraising_campaign_delete, name='fundraising_campaign_delete'),
    path('fundraising-campaigns/<int:pk>/', views.fundraising_campaign_detail, name='fundraising_campaign_detail'),
    
    # ProcurementFinancialTracking URLs
    path('procurement-financial-tracking/', views.procurement_financial_tracking_list, name='procurement_financial_tracking_list'),
    path('procurement-financial-tracking/create/', views.procurement_financial_tracking_create, name='procurement_financial_tracking_create'),
    path('procurement-financial-tracking/<int:pk>/update/', views.procurement_financial_tracking_update, name='procurement_financial_tracking_update'),
    path('procurement-financial-tracking/<int:pk>/delete/', views.procurement_financial_tracking_delete, name='procurement_financial_tracking_delete'),
    path('procurement-financial-tracking/<int:pk>/', views.procurement_financial_tracking_detail, name='procurement_financial_tracking_detail'),
    
    # AssetFinancialTracking URLs
    path('asset-financial-tracking/', views.asset_financial_tracking_list, name='asset_financial_tracking_list'),
    path('asset-financial-tracking/create/', views.asset_financial_tracking_create, name='asset_financial_tracking_create'),
    path('asset-financial-tracking/<int:pk>/update/', views.asset_financial_tracking_update, name='asset_financial_tracking_update'),
    path('asset-financial-tracking/<int:pk>/delete/', views.asset_financial_tracking_delete, name='asset_financial_tracking_delete'),
    path('asset-financial-tracking/<int:pk>/', views.asset_financial_tracking_detail, name='asset_financial_tracking_detail'),
    
    # FinancialForecast URLs
    path('financial-forecasts/', views.financial_forecast_list, name='financial_forecast_list'),
    path('financial-forecasts/create/', views.financial_forecast_create, name='financial_forecast_create'),
    path('financial-forecasts/<int:pk>/update/', views.financial_forecast_update, name='financial_forecast_update'),
    path('financial-forecasts/<int:pk>/delete/', views.financial_forecast_delete, name='financial_forecast_delete'),
    path('financial-forecasts/<int:pk>/', views.financial_forecast_detail, name='financial_forecast_detail'),
    
    # Budget URLs
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/update/', views.budget_update, name='budget_update'),
    path('budgets/<int:pk>/delete/', views.budget_delete, name='budget_delete'),
    path('budgets/<int:pk>/', views.budget_detail, name='budget_detail'),
    
    # Transaction URLs
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    
    # Budget Allocation URLs
    path('budget-allocations/', views.budget_allocation_list, name='budget_allocation_list'),
    path('budget-allocations/create/', views.budget_allocation_create, name='budget_allocation_create'),
    path('budget-allocations/<int:pk>/update/', views.budget_allocation_update, name='budget_allocation_update'),
    path('budget-allocations/<int:pk>/delete/', views.budget_allocation_delete, name='budget_allocation_delete'),
    path('budget-allocations/<int:pk>/', views.budget_allocation_detail, name='budget_allocation_detail'),
    
    # Reporting URLs
    path('reports/income-statement/', views.reports_income_statement, name='reports_income_statement'),
    path('reports/balance-sheet/', views.reports_balance_sheet, name='reports_balance_sheet'),
    path('reports/cash-flow/', views.reports_cash_flow, name='reports_cash_flow'),
    path('reports/grant-summary/', views.reports_grant_summary, name='reports_grant_summary'),
    
    # Analytics URLs
    path('analytics/income-trends/', views.analytics_income_trends, name='analytics_income_trends'),
    path('analytics/expense-trends/', views.analytics_expense_trends, name='analytics_expense_trends'),
    path('analytics/budget-variance/', views.analytics_budget_variance, name='analytics_budget_variance'),
    path('analytics/funding-sources/', views.analytics_funding_sources, name='analytics_funding_sources'),
    
    # Budgeting URLs
    path('budgeting/summary/', views.budgeting_summary, name='budgeting_summary'),
    path('budgeting/variance-report/', views.budgeting_variance_report, name='budgeting_variance_report'),
    
    # Transactions URLs
    path('transactions/summary/', views.transactions_summary, name='transactions_summary'),
    path('transactions/income/', views.transactions_income, name='transactions_income'),
    path('transactions/expense/', views.transactions_expense, name='transactions_expense'),
    
    # Grants URLs
    path('grants/summary/', views.grants_summary, name='grants_summary'),
    path('grants/funding-trends/', views.grants_funding_trends, name='grants_funding_trends'),
    
    # Donors URLs
    path('donors/summary/', views.donors_summary, name='donors_summary'),
    path('donors/giving-trends/', views.donors_giving_trends, name='donors_giving_trends'),
    
    # Sponsors URLs
    path('sponsors/summary/', views.sponsors_summary, name='sponsors_summary'),
    path('sponsors/trends/', views.sponsors_trends, name='sponsors_trends'),
    
    # Fundraising URLs
    path('fundraising/summary/', views.fundraising_summary, name='fundraising_summary'),
    path('fundraising/trends/', views.fundraising_trends, name='fundraising_trends'),
    path('fundraising/performance/', views.fundraising_performance, name='fundraising_performance'),
]