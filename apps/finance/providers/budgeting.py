"""Finance Engine budgeting providers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from apps.finance.selectors import (
    get_accessible_budgets,
    get_accessible_transactions,
)

User = get_user_model()


class BudgetingProvider:
    """Provider for budgeting data."""

    def __init__(self, user: Any):
        """
        Initialize the budgeting provider.

        Args:
            user: The user requesting the budgeting data.
        """
        self.user = user

    def get_budget_summary(self) -> Dict[str, Any]:
        """
        Get budget summary data.

        Returns:
            Dict containing budget summary information.
        """
        budgets = get_accessible_budgets(self.user)
        
        # Overall budget statistics
        total_budgeted = budgets.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        total_allocated = budgets.aggregate(total=Sum('allocated_amount'))['total'] or Decimal('0')
        total_available = total_budgeted - total_allocated
        
        # Budget utilization by financial year
        utilization_by_year = budgets.values('financial_year__name').annotate(
            total_budgeted=Sum('total_amount'),
            total_allocated=Sum('allocated_amount'),
            budget_count=Count('id')
        ).order_by('financial_year__name')
        
        # Budget utilization by department/program (if available)
        # This would depend on how budgets are categorized in your system
        
        # Recent budget activity
        recent_budgets = budgets.order_by('-updated_at')[:5]
        
        return {
            'summary': {
                'total_budgeted': total_budgeted,
                'total_allocated': total_allocated,
                'total_available': total_available,
                'utilization_percentage': (total_allocated / total_budgeted * 100) if total_budgeted > 0 else Decimal('0'),
                'budget_count': budgets.count(),
            },
            'by_financial_year': [
                {
                    'financial_year': item['financial_year__name'],
                    'total_budgeted': item['total_budgeted'],
                    'total_allocated': item['total_allocated'],
                    'available': item['total_budgeted'] - item['total_allocated'],
                    'utilization_percentage': (item['total_allocated'] / item['total_budgeted'] * 100) if item['total_budgeted'] > 0 else Decimal('0'),
                    'budget_count': item['budget_count'],
                }
                for item in utilization_by_year
            ],
            'recent_budgets': [
                {
                    'id': budget.id,
                    'name': budget.name,
                    'code': budget.code,
                    'financial_year': budget.financial_year.name if budget.financial_year else None,
                    'total_amount': budget.total_amount,
                    'allocated_amount': budget.allocated_amount,
                    'remaining': budget.remaining,
                    'updated_at': budget.updated_at,
                }
                for budget in recent_budgets
            ],
        }

    def get_budget_variance_report(
        self, 
        budget_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get budget variance report.

        Args:
            budget_id: ID of specific budget (optional). If None, returns summary of all budgets.

        Returns:
            Dict containing budget variance report data.
        """
        Budget = django_apps.get_model("finance", "Budget")
        
        if budget_id:
            # Specific budget variance report
            try:
                budget = Budget.objects.get(id=budget_id)
                # Check permissions
                accessible_budgets = get_accessible_budgets(self.user)
                if not accessible_budgets.filter(id=budget_id).exists():
                    raise PermissionError("You do not have permission to access this budget.")
                    
                variance_data = budget.get_variance()  # Assuming this method exists
                
                # Get budget allocations/lines if available
                # BudgetAllocation = django_apps.get_model("finance", "BudgetAllocation")
                # allocations = BudgetAllocation.objects.filter(budget=budget)
                
                # Get transactions against this budget if available
                # Transaction = django_apps.get_model("finance", "Transaction")
                # transactions = Transaction.objects.filter(budget=budget, status='POSTED')
                
                return {
                    'budget': {
                        'id': budget.id,
                        'name': budget.name,
                        'code': budget.code,
                        'financial_year': budget.financial_year.name if budget.financial_year else None,
                        'total_amount': budget.total_amount,
                        'allocated_amount': budget.allocated_amount,
                        'remaining_amount': budget.remaining,
                    },
                    'variance': variance_data,
                    # 'allocations': [
                    #     {
                    #         'id': alloc.id,
                    #         'line_item': alloc.line_item,
                    #         'budgeted_amount': alloc.budgeted_amount,
                    #         'actual_amount': alloc.actual_amount,
                    #         'variance': alloc.variance,
                    #     }
                    #     for alloc in allocations
                    # ],
                    # 'transactions': [
                    #     {
                    #         'id': txn.id,
                    #         'reference_number': txn.reference_number,
                    #         'date': txn.transaction_date,
                    #         'amount': txn.amount,
                    #         'description': txn.description,
                    #     }
                    #     for txn in transactions
                    # ],
                }
            except Budget.DoesNotExist:
                raise ValueError(f"Budget with ID {budget_id} does not exist.")
        else:
            # Summary variance report of all budgets
            budgets = get_accessible_budgets(self.user)
            
            budget_details = []
            total_budgeted = Decimal('0')
            total_actual = Decimal('0')
            
            for budget in budgets:
                variance_data = budget.get_variance()
                budgeted = budget.total_amount
                actual = variance_data.get('actual', Decimal('0'))
                variance = variance_data.get('variance', Decimal('0'))
                variance_pct = variance_data.get('variance_percentage', Decimal('0'))
                
                total_budgeted += budgeted
                total_actual += actual
                
                budget_details.append({
                    'id': budget.id,
                    'name': budget.name,
                    'code': budget.code,
                    'financial_year': budget.financial_year.name if budget.financial_year else None,
                    'budgeted': budgeted,
                    'actual': actual,
                    'variance': variance,
                    'variance_percentage': variance_pct,
                    'status': (
                        'on_track' if variance_pct >= -5 else
                        'caution' if variance_pct >= -15 else
                        'underutilized' if variance_pct < -15 else
                        'overrun'  # This would be caught by budget service in practice
                    ),
                })
                
            total_variance = total_budgeted - total_actual
            overall_variance_pct = (total_variance / total_budgeted * 100) if total_budgeted > 0 else Decimal('0')
            
            # Categorize budgets
            on_track_count = len([b for b in budget_details if b['status'] == 'on_track'])
            caution_count = len([b for b in budget_details if b['status'] == 'caution'])
            underutilized_count = len([b for b in budget_details if b['status'] == 'underutilized'])
            overrun_count = len([b for b in budget_details if b['status'] == 'overrun'])
            
            return {
                'summary': {
                    'total_budgeted': total_budgeted,
                    'total_actual': total_actual,
                    'total_variance': total_variance,
                    'overall_variance_percentage': overall_variance_pct,
                    'budget_count': budgets.count(),
                },
                'performance_distribution': {
                    'on_track': on_track_count,
                    'caution': caution_count,
                    'underutilized': underutilized_count,
                    'overrun': overrun_count,
                },
                'budgets': budget_details,
            }

    def get_budget_allocations_report(
        self, 
        budget_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get budget allocations report.

        Args:
            budget_id: ID of specific budget (optional). If None, returns summary of all budgets.

        Returns:
            Dict containing budget allocations report data.
        """
        Budget = django_apps.get_model("finance", "Budget")
        BudgetAllocation = django_apps.get_model("finance", "BudgetAllocation")
        
        if budget_id:
            # Specific budget allocations report
            try:
                budget = Budget.objects.get(id=budget_id)
                # Check permissions
                accessible_budgets = get_accessible_budgets(self.user)
                if not accessible_budgets.filter(id=budget_id).exists():
                    raise PermissionError("You do not have permission to access this budget.")
                    
                allocations = BudgetAllocation.objects.filter(budget=budget)
                
                total_allocated = allocations.aggregate(total=Sum('budgeted_amount'))['total'] or Decimal('0')
                total_actual = allocations.aggregate(total=Sum('actual_amount'))['total'] or Decimal('0')
                total_variance = total_allocated - total_actual
                
                return {
                    'budget': {
                        'id': budget.id,
                        'name': budget.name,
                        'code': budget.code,
                        'financial_year': budget.financial_year.name if budget.financial_year else None,
                        'total_amount': budget.total_amount,
                    },
                    'allocations': [
                        {
                            'id': alloc.id,
                            'line_item': alloc.line_item,
                            'budgeted_amount': alloc.budgeted_amount,
                            'actual_amount': alloc.actual_amount,
                            'variance': alloc.variance,
                            'variance_percentage': (alloc.variance / alloc.budgeted_amount * 100) if alloc.budgeted_amount > 0 else Decimal('0'),
                        }
                        for alloc in allocations
                    ],
                    'summary': {
                        'total_allocated': total_allocated,
                        'total_actual': total_actual,
                        'total_variance': total_variance,
                        'utilization_percentage': (total_actual / total_allocated * 100) if total_allocated > 0 else Decimal('0'),
                    },
                }
            except Budget.DoesNotExist:
                raise ValueError(f"Budget with ID {budget_id} does not exist.")
        else:
            # Summary allocations report of all budgets
            # This would be more complex and might be better served by specific budget reports
            return {
                'note': 'For overall budget allocations, please run reports for individual budgets.',
                'total_budgets': get_accessible_budgets(self.user).count(),
            }

    def get_budget_forecast(
        self, 
        budget_id: int,
        months_ahead: int = 3
    ) -> Dict[str, Any]:
        """
        Get budget forecast.

        Args:
            budget_id: ID of the budget.
            months_ahead: Number of months to forecast ahead.

        Returns:
            Dict containing budget forecast data.
        """
        Budget = django_apps.get_model("finance", "Budget")
        
        try:
            budget = Budget.objects.get(id=budget_id)
            # Check permissions
            accessible_budgets = get_accessible_budgets(self.user)
            if not accessible_budgets.filter(id=budget_id).exists():
                raise PermissionError("You do not have permission to access this budget.")
        except Budget.DoesNotExist:
            raise ValueError(f"Budget with ID {budget_id} does not exist.")
            
        # Get historical spending patterns
        # This would require transaction history linked to the budget
        # For now, we'll return a simple forecast based on current allocation
        
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30 * months_ahead)
        
        # In a real implementation, you would:
        # 1. Analyze historical spending patterns
        # 2. Consider seasonal variations
        # 3. Factor in known upcoming expenses
        # 4. Adjust for budget modifications
        
        # Simple forecast: assume even spending of remaining budget
        remaining_budget = budget.remaining
        monthly_forecast = remaining_budget / months_ahead if months_ahead > 0 else Decimal('0')
        
        forecast_periods = []
        cumulative_spent = budget.allocated_amount - remaining_budget  # Amount already spent
        
        for i in range(1, months_ahead + 1):
            period_start = end_date + timezone.timedelta(days=30 * (i-1))
            period_end = end_date + timezone.timedelta(days=30 * i)
            
            forecast_periods.append({
                'period': f"{period_start.strftime('%Y-%m')} to {period_end.strftime('%Y-%m')}",
                'start_date': period_start,
                'end_date': period_end,
                'forecasted_amount': monthly_forecast,
                'cumulative_forecast': cumulative_spent + (monthly_forecast * i),
                'remaining_budget': max(remaining_budget - (monthly_forecast * i), Decimal('0')),
            })
            
        return {
            'budget': {
                'id': budget.id,
                'name': budget.name,
                'code': budget.code,
                'total_amount': budget.total_amount,
                'allocated_amount': budget.allocated_amount,
                'remaining_amount': budget.remaining,
            },
            'forecast_assumptions': [
                'Assumes even spending of remaining budget',
                'Does not account for seasonal variations',
                'Does not factor in known upcoming expenses',
                'Based on current allocation as of forecast date',
            ],
            'forecast_periods': forecast_periods,
            'total_forecast': monthly_forecast * months_ahead,
        }