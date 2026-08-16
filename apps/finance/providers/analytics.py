"""Finance Engine analytics providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from django.utils import timezone

from apps.finance.selectors import (
    get_accessible_budgets,
    get_accessible_donors,
    get_accessible_financial_accounts,
    get_accessible_grants,
    get_accessible_sponsors,
    get_accessible_transactions,
)

User = get_user_model()


class FinanceAnalyticsProvider:
    """Provider for finance analytics data."""

    def __init__(self, user: Any):
        """
        Initialize the analytics provider.

        Args:
            user: The user requesting the analytics data.
        """
        self.user = user

    def get_income_trends(
        self, 
        months: int = 12,
        group_by: str = 'month'
    ) -> Dict[str, Any]:
        """
        Get income trends over time.

        Args:
            months: Number of months to look back.
            group_by: How to group the data ('month', 'quarter', 'year').

        Returns:
            Dict containing income trends data.
        """
        end_date = timezone.now()
        if group_by == 'month':
            start_date = end_date - timezone.timedelta(days=30 * months)
        elif group_by == 'quarter':
            start_date = end_date - timezone.timedelta(days=3 * 30 * months)
        else:  # year
            start_date = end_date - timezone.timedelta(days=365 * months)
            
        # Get income transactions
        income_txns = get_accessible_transactions(self.user).filter(
            transaction_type='INCOME',
            status='POSTED',
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Group by time period
        if group_by == 'month':
            # Group by year-month
            trends = defaultdict(lambda: {'income': Decimal('0'), 'count': 0})
            for txn in income_txns:
                key = txn.transaction_date.strftime('%Y-%m')
                trends[key]['income'] += txn.amount
                trends[key]['count'] += 1
                
            # Sort by date
            sorted_trends = sorted(trends.items())
            
            return {
                'period_type': 'monthly',
                'start_date': start_date,
                'end_date': end_date,
                'data': [
                    {
                        'period': period,
                        'income': data['income'],
                        'transaction_count': data['count'],
                    }
                    for period, data in sorted_trends
                ],
                'total_income': sum(data['income'] for data in trends.values()),
                'average_monthly_income': sum(data['income'] for data in trends.values()) / len(trends) if trends else Decimal('0'),
            }
        elif group_by == 'quarter':
            # Group by year-quarter
            trends = defaultdict(lambda: {'income': Decimal('0'), 'count': 0})
            for txn in income_txns:
                year = txn.transaction_date.year
                month = txn.transaction_date.month
                quarter = (month - 1) // 3 + 1
                key = f"{year}-Q{quarter}"
                trends[key]['income'] += txn.amount
                trends[key]['count'] += 1
                
            # Sort by date
            sorted_trends = sorted(trends.items())
            
            return {
                'period_type': 'quarterly',
                'start_date': start_date,
                'end_date': end_date,
                'data': [
                    {
                        'period': period,
                        'income': data['income'],
                        'transaction_count': data['count'],
                    }
                    for period, data in sorted_trends
                ],
                'total_income': sum(data['income'] for data in trends.values()),
                'average_quarterly_income': sum(data['income'] for data in trends.values()) / len(trends) if trends else Decimal('0'),
            }
        else:  # year
            # Group by year
            trends = defaultdict(lambda: {'income': Decimal('0'), 'count': 0})
            for txn in income_txns:
                key = str(txn.transaction_date.year)
                trends[key]['income'] += txn.amount
                trends[key]['count'] += 1
                
            # Sort by date
            sorted_trends = sorted(trends.items())
            
            return {
                'period_type': 'yearly',
                'start_date': start_date,
                'end_date': end_date,
                'data': [
                    {
                        'period': period,
                        'income': data['income'],
                        'transaction_count': data['count'],
                    }
                    for period, data in sorted_trends
                ],
                'total_income': sum(data['income'] for data in trends.values()),
                'average_yearly_income': sum(data['income'] for data in trends.values()) / len(trends) if trends else Decimal('0'),
            }

    def get_expense_trends(
        self, 
        months: int = 12,
        group_by: str = 'month',
        by_source: bool = False
    ) -> Dict[str, Any]:
        """
        Get expense trends over time.

        Args:
            months: Number of months to look back.
            group_by: How to group the data ('month', 'quarter', 'year').
            by_source: Whether to break down by expense source.

        Returns:
            Dict containing expense trends data.
        """
        end_date = timezone.now()
        if group_by == 'month':
            start_date = end_date - timezone.timedelta(days=30 * months)
        elif group_by == 'quarter':
            start_date = end_date - timezone.timedelta(days=3 * 30 * months)
        else:  # year
            start_date = end_date - timezone.timedelta(days=365 * months)
            
        # Get expense transactions
        expense_txns = get_accessible_transactions(self.user).filter(
            transaction_type='EXPENSE',
            status='POSTED',
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        if by_source:
            # Group by time period and source
            trends = defaultdict(lambda: defaultdict(lambda: {'expense': Decimal('0'), 'count': 0}))
            for txn in expense_txns:
                if group_by == 'month':
                    key = txn.transaction_date.strftime('%Y-%m')
                elif group_by == 'quarter':
                    year = txn.transaction_date.year
                    month = txn.transaction_date.month
                    quarter = (month - 1) // 3 + 1
                    key = f"{year}-Q{quarter}"
                else:  # year
                    key = str(txn.transaction_date.year)
                    
                source = txn.source or 'unspecified'
                trends[key][source]['expense'] += txn.amount
                trends[key][source]['count'] += 1
                
            # Process and sort
            result_data = []
            for period in sorted(trends.keys()):
                period_data = {
                    'period': period,
                    'sources': [],
                    'total_expense': Decimal('0'),
                    'transaction_count': 0,
                }
                for source in sorted(trends[period].keys()):
                    source_data = trends[period][source]
                    period_data['sources'].append({
                        'source': source,
                        'expense': source_data['expense'],
                        'transaction_count': source_data['count'],
                    })
                    period_data['total_expense'] += source_data['expense']
                    period_data['transaction_count'] += source_data['count']
                    
                result_data.append(period_data)
                
            return {
                'period_type': group_by,
                'start_date': start_date,
                'end_date': end_date,
                'data': result_data,
                'total_expense': sum(item['total_expense'] for item in result_data),
            }
        else:
            # Group by time period only
            trends = defaultdict(lambda: {'expense': Decimal('0'), 'count': 0})
            for txn in expense_txns:
                if group_by == 'month':
                    key = txn.transaction_date.strftime('%Y-%m')
                elif group_by == 'quarter':
                    year = txn.transaction_date.year
                    month = txn.transaction_date.month
                    quarter = (month - 1) // 3 + 1
                    key = f"{year}-Q{quarter}"
                else:  # year
                    key = str(txn.transaction_date.year)
                    
                trends[key]['expense'] += txn.amount
                trends[key]['count'] += 1
                
            # Sort by date
            sorted_trends = sorted(trends.items())
            
            return {
                'period_type': group_by,
                'start_date': start_date,
                'end_date': end_date,
                'data': [
                    {
                        'period': period,
                        'expense': data['expense'],
                        'transaction_count': data['count'],
                    }
                    for period, data in sorted_trends
                ],
                'total_expense': sum(data['expense'] for data in trends.values()),
                'average_period_expense': sum(data['expense'] for data in trends.values()) / len(trends) if trends else Decimal('0'),
            }

    def get_budget_variance_analysis(self) -> Dict[str, Any]:
        """
        Get budget variance analysis across all accessible budgets.

        Returns:
            Dict containing budget variance analysis.
        """
        budgets = get_accessible_budgets(self.user)
        
        # Initialize counters
        total_budgeted = Decimal('0')
        total_actual = Decimal('0')
        on_track = 0
        caution = 0
        overrun = 0
        underutilized = 0
        
        budget_details = []
        
        for budget in budgets:
            variance_data = budget.get_variance()  # Assuming this method exists
            budgeted = budget.total_amount
            actual = variance_data.get('actual', Decimal('0'))
            variance = variance_data.get('variance', Decimal('0'))
            variance_pct = variance_data.get('variance_percentage', Decimal('0'))
            
            total_budgeted += budgeted
            total_actual += actual
            
            # Categorize budget performance
            if variance_pct >= -5:  # Within 5% of budget (underspent or overspent by less than 5%)
                on_track += 1
            elif variance_pct >= -15:  # Between 5% and 15% underspent
                caution += 1
            elif variance_pct < -15:  # More than 15% underspent
                underutilized += 1
            # Note: We're not categorizing overspending here as it's handled by the budget service
            
            budget_details.append({
                'id': budget.id,
                'name': budget.name,
                'code': budget.code,
                'budgeted': budgeted,
                'actual': actual,
                'variance': variance,
                'variance_percentage': variance_pct,
                'performance': (
                    'on_track' if variance_pct >= -5 else
                    'caution' if variance_pct >= -15 else
                    'underutilized'
                ),
            })
            
        total_variance = total_budgeted - total_actual
        variance_percentage = (total_variance / total_budgeted * 100) if total_budgeted > 0 else Decimal('0')
        
        # Calculate ratios
        budget_utilization = (total_actual / total_budgeted * 100) if total_budgeted > 0 else Decimal('0')
        
        return {
            'summary': {
                'total_budgeted': total_budgeted,
                'total_actual': total_actual,
                'total_variance': total_variance,
                'variance_percentage': variance_percentage,
                'budget_utilization': budget_utilization,
                'budget_count': budgets.count(),
            },
            'performance_distribution': {
                'on_track': on_track,
                'caution': caution,
                'overrun': overrun,
                'underutilized': underutilized,
            },
            'budgets': budget_details,
        }

    def get_funding_source_analysis(self) -> Dict[str, Any]:
        """
        Get analysis of funding sources.

        Returns:
            Dict containing funding source analysis.
        """
        # Analyze grants
        grants = get_accessible_grants(self.user)
        grant_analysis = {
            'total_awarded': grants.aggregate(total=Sum('amount'))['total'] or Decimal('0'),
            'total_disbursed': grants.aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0'),
            'average_grant_size': grants.aggregate(avg=Avg('amount'))['avg'] or Decimal('0'),
            'count': grants.count(),
            'by_status': list(grants.values('status').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total')),
            'by_donor_type': list(grants.values('donor__donor_type').annotate(
                count=Count('id'),
                total=Sum('amount')
            ).order_by('-total') if grants.exists() else []),
        }
        
        # Analyze donors
        donors = get_accessible_donors(self.user)
        donor_analysis = {
            'total_contributions': donors.aggregate(total=Sum('total_contributions'))['total'] or Decimal('0'),
            'average_donation': donors.aggregate(avg=Avg('total_contributions'))['avg'] or Decimal('0'),
            'count': donors.count(),
            'by_type': list(donors.values('donor_type').annotate(
                count=Count('id'),
                total=Sum('total_contributions')
            ).order_by('-total')),
            'top_donors': list(donors.order_by('-total_contributions')[:10].values(
                'name', 'donor_type', 'total_contributions'
            )),
        }
        
        # Analyze sponsors
        sponsors = get_accessible_sponsors(self.user)
        sponsor_analysis = {
            'total_contributions': sponsors.aggregate(total=Sum('total_contributions'))['total'] or Decimal('0'),
            'average_sponsorship': sponsors.aggregate(avg=Avg('total_contributions'))['avg'] or Decimal('0'),
            'count': sponsors.count(),
            'by_type': list(sponsors.values('sponsor_type').annotate(
                count=Count('id'),
                total=Sum('total_contributions')
            ).order_by('-total') if hasattr(sponsors.first(), 'sponsor_type') else []),
            'top_sponsors': list(sponsors.order_by('-total_contributions')[:10].values(
                'name', 'sponsor_type', 'total_contributions'
            )) if hasattr(sponsors.first(), 'sponsor_type') else [],
        }
        
        # Analyze fundraising campaigns
        campaigns = get_accessible_fundraising_campaigns(self.user)
        campaign_analysis = {
            'total_pledged': campaigns.aggregate(total=Sum('target_amount'))['total'] or Decimal('0'),
            'total_raised': campaigns.aggregate(total=Sum('amount_raised'))['total'] or Decimal('0'),
            'average_target': campaigns.aggregate(avg=Avg('target_amount'))['avg'] or Decimal('0'),
            'count': campaigns.count(),
            'average_progress_percentage': (
                campaigns.aggregate(
                    avg=Avg('amount_raised') * 100 / Avg('target_amount')
                )['avg'] or Decimal('0')
            ) if campaigns.exists() else Decimal('0'),
            'by_status': list(campaigns.values('status').annotate(
                count=Count('id'),
                total_pledged=Sum('target_amount'),
                total_raised=Sum('amount_raised')
            ).order_by('-total_raised')),
        }
        
        # Calculate funding diversification
        funding_sources = []
        if grant_analysis['total_awarded'] > 0:
            funding_sources.append(('grants', grant_analysis['total_awarded']))
        if donor_analysis['total_contributions'] > 0:
            funding_sources.append(('donors', donor_analysis['total_contributions']))
        if sponsor_analysis['total_contributions'] > 0:
            funding_sources.append(('sponsors', sponsor_analysis['total_contributions']))
        if campaign_analysis['total_raised'] > 0:
            funding_sources.append(('fundraising', campaign_analysis['total_raised']))
            
        total_funding = sum(amount for _, amount in funding_sources)
        
        funding_diversification = []
        for source_type, amount in funding_sources:
            percentage = (amount / total_funding * 100) if total_funding > 0 else Decimal('0')
            funding_diversification.append({
                'type': source_type,
                'amount': amount,
                'percentage': percentage,
            })
            
        # Calculate Herfindahl-Hirschman Index for concentration
        hhi = sum((item['percentage'] / 100) ** 2 for item in funding_diversification)
        hhi_score = min(hhi * 10000, 10000)  # Convert to 0-10000 scale
        
        return {
            'grants': grant_analysis,
            'donors': donor_analysis,
            'sponsors': sponsor_analysis,
            'fundraising': campaign_analysis,
            'diversification': funding_diversification,
            'concentration': {
                'hhi': hhi_score,
                'level': (
                    'highly_concentrated' if hhi_score > 2500 else
                    'moderately_concentrated' if hhi_score > 1500 else
                    'well_diversified'
                ),
            },
            'total_funding': total_funding,
        }

    def get_financial_ratios(self) -> Dict[str, Any]:
        """
        Get key financial ratios.

        Returns:
            Dict containing financial ratios.
        """
        # This would typically require balance sheet data
        # For now, we'll return placeholder structure
        return {
            'liquidity_ratios': {
                'current_ratio': None,  # Would require current assets/liabilities
                'quick_ratio': None,    # Would require liquid assets/liabilities
                'cash_ratio': None,     # Would require cash equivalents/liabilities
            },
            'profitability_ratios': {
                'operating_margin': None,  # Would require operating income/revenue
                'return_on_assets': None,  # Would require net income/total assets
                'return_on_equity': None,  # Would require net income/total equity
            },
            'efficiency_ratios': {
                'budget_variance': None,  # Would require budget vs actual
                'expense_ratio': None,    # Would require expenses/total income
                'funding_efficiency': None,  # Would require funds raised/funds requested
            },
            'solvency_ratios': {
                'debt_to_equity': None,   # Would require total debt/total equity
                'debt_to_assets': None,   # Would require total debt/total assets
                'interest_coverage': None,  # Would require EBIT/interest expense
            },
            'note': 'Financial ratios require integration with balance sheet and income statement data.',
        }

    def get_cash_flow_analysis(self) -> Dict[str, Any]:
        """
        Get cash flow analysis.

        Returns:
            Dict containing cash flow analysis.
        """
        # This would require more detailed transaction categorization
        # For now, we'll return placeholder structure
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=90)  # Last 90 days
        
        # Get transactions for the period
        transactions = get_accessible_transactions(self.user).filter(
            status='POSTED',
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Categorize cash flows (simplified)
        inflow_sources = transactions.filter(
            transaction_type='INCOME'
        ).values('source').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        outflow_sources = transactions.filter(
            transaction_type='EXPENSE'
        ).values('source').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        total_inflows = transactions.filter(transaction_type='INCOME').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        total_outflows = transactions.filter(transaction_type='EXPENSE').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        net_cash_flow = total_inflows - total_outflows
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': 90,
            },
            'cash_flow_summary': {
                'total_inflows': total_inflows,
                'total_outflows': total_outflows,
                'net_cash_flow': net_cash_flow,
            },
            'inflow_sources': [
                {
                    'source': item['source'],
                    'amount': item['total'],
                    'count': item['count'],
                    'percentage_of_total': (item['total'] / total_inflows * 100) if total_inflows > 0 else Decimal('0'),
                }
                for item in inflow_sources
            ],
            'outflow_sources': [
                {
                    'source': item['source'],
                    'amount': item['total'],
                    'count': item['count'],
                    'percentage_of_total': (item['total'] / total_outflows * 100) if total_outflows > 0 else Decimal('0'),
                }
                for item in outflow_sources
            ],
            'trend': 'positive' if net_cash_flow > 0 else 'negative' if net_cash_flow < 0 else 'neutral',
            'note': 'Detailed cash flow analysis requires proper transaction categorization and opening/closing cash balances.',
        }