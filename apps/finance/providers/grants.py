"""Finance Engine grants providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from apps.finance.selectors import get_accessible_grants

User = get_user_model()


class GrantsProvider:
    """Provider for grants data."""

    def __init__(self, user: Any):
        """
        Initialize the grants provider.

        Args:
            user: The user requesting the grants data.
        """
        self.user = user

    def get_grants_summary(self) -> Dict[str, Any]:
        """
        Get grants summary data.

        Returns:
            Dict containing grants summary information.
        """
        grants = get_accessible_grants(self.user)
        
        # Overall grant statistics
        total_awarded = grants.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        total_disbursed = grants.aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0')
        total_remaining = total_awarded - total_disbursed
        
        # Average grant size
        average_grant = grants.aggregate(avg=Avg('amount'))['avg'] or Decimal('0')
        
        # Grants by status
        by_status = grants.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_disbursed=Sum('disbursed_amount')
        ).order_by('-total_amount')
        
        # Grants by donor
        by_donor = grants.values('donor__name', 'donor__id').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_disbursed=Sum('disbursed_amount')
        ).order_by('-total_amount')[:10]  # Top 10 donors
        
        # Recently awarded grants
        recent_awards = grants.filter(
            status__in=['awarded', 'active']
        ).order_by('-award_date')[:5]  # Assuming award_date field exists
        
        # Grants ending soon (within 90 days)
        ninety_days_from_now = timezone.now() + timezone.timedelta(days=90)
        ending_soon = grants.filter(
            end_date__lte=ninety_days_from_now,
            end_date__gte=timezone.now(),
            status__in=['active', 'awarded']
        ).order_by('end_date')[:5]
        
        return {
            'summary': {
                'total_grants': grants.count(),
                'total_awarded': total_awarded,
                'total_disbursed': total_disbursed,
                'total_remaining': total_remaining,
                'average_grant_size': average_grant,
                'disbursement_rate': (total_disbursed / total_awarded * 100) if total_awarded > 0 else Decimal('0'),
            },
            'by_status': [
                {
                    'status': item['status'],
                    'count': item['count'],
                    'total_amount': item['total_amount'],
                    'total_disbursed': item['total_disbursed'],
                    'remaining': item['total_amount'] - item['total_disbursed'],
                    'disbursement_rate': (item['total_disbursed'] / item['total_amount'] * 100) if item['total_amount'] > 0 else Decimal('0'),
                }
                for item in by_status
            ],
            'by_donor': [
                {
                    'donor_name': item['donor__name'],
                    'donor_id': item['donor__id'],
                    'grant_count': item['count'],
                    'total_amount': item['total_amount'],
                    'total_disbursed': item['total_disbursed'],
                    'remaining': item['total_amount'] - item['total_disbursed'],
                }
                for item in by_donor
            ],
            'recent_awards': [
                {
                    'id': grant.id,
                    'name': grant.name,
                    'reference_number': grant.reference_number,
                    'donor': grant.donor.name if grant.donor else None,
                    'amount': grant.amount,
                    'award_date': grant.award_date if hasattr(grant, 'award_date') else None,
                    'end_date': grant.end_date if has(grant, 'end_date') else None,
                }
                for grant in recent_awards
            ],
            'ending_soon': [
                {
                    'id': grant.id,
                    'name': grant.name,
                    'reference_number': grant.reference_number,
                    'donor': grant.donor.name if grant.donor else None,
                    'amount': grant.amount,
                    'end_date': grant.end_date,
                    'days_remaining': (grant.end_date - timezone.now()).days if hasattr(grant, 'end_date') else None,
                }
                for grant in ending_soon
            ],
        }

    def get_grant_funding_trends(
        self, 
        years: int = 5
    ) -> Dict[str, Any]:
        """
        Get grant funding trends over time.

        Args:
            years: Number of years to look back.

        Returns:
            Dict containing grant funding trends data.
        """
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=365 * years)
        
        # Get grants in the period
        grants = get_accessible_grants(self.user).filter(
            award_date__gte=start_date,
            award_date__lte=end_date
        )  # Assuming award_date field exists
        
        # Group by year
        yearly_data = defaultdict(lambda: {
            'count': 0,
            'total_awarded': Decimal('0'),
            'total_disbursed': Decimal('0'),
        })
        
        for grant in grants:
            year = grant.award_date.year if hasattr(grant, 'award_date') else grant.created_at.year
            yearly_data[year]['count'] += 1
            yearly_data[year]['total_awarded'] += grant.amount
            yearly_data[year]['total_disbursed'] += grant.disbursed_amount
            
        # Sort by year
        sorted_data = sorted(yearly_data.items())
        
        return {
            'period_type': 'yearly',
            'start_date': start_date,
            'end_date': end_date,
            'data': [
                {
                    'year': year,
                    'grant_count': data['count'],
                    'total_awarded': data['total_awarded'],
                    'total_disbursed': data['total_disbursed'],
                    'total_remaining': data['total_awarded'] - data['total_disbursed'],
                    'average_grant_size': data['total_awarded'] / data['count'] if data['count'] > 0 else Decimal('0'),
                    'disbursement_rate': (data['total_disbursed'] / data['total_awarded'] * 100) if data['total_awarded'] > 0 else Decimal('0'),
                }
                for year, data in sorted_data
            ],
            'summary': {
                'total_grants': sum(data['count'] for data in yearly_data.values()),
                'total_awarded': sum(data['total_awarded'] for data in yearly_data.values()),
                'total_disbursed': sum(data['total_disbursed'] for data in yearly_data.values()),
                'total_remaining': sum(data['total_awarded'] - data['total_disbursed'] for data in yearly_data.values()),
            },
        }

    def get_donor_grant_analysis(
        self, 
        donor_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get grant analysis for a specific donor or all donors.

        Args:
            donor_id: ID of specific donor (optional). If None, returns analysis for all donors.

        Returns:
            Dict containing donor grant analysis data.
        """
        Donor = django_apps.get_model("finance", "Donor")
        Grant = django_apps.get_model("finance", "Grant")
        
        if donor_id:
            # Specific donor analysis
            try:
                donor = Donor.objects.get(id=donor_id)
                # Check permissions
                accessible_donors = get_accessible_donors(self.user)
                if not accessible_donors.filter(id=donor_id).exists():
                    raise PermissionError("You do not have permission to access this donor.")
                    
                grants = Grant.objects.filter(donor=donor)
                # Check if user can access these grants
                accessible_grants = get_accessible_grants(self.user)
                grants = grants.filter(id__in=accessible_grants.values_list('id', flat=True))
                
                total_awarded = grants.aggregate(total=Sum('amount'))['total'] or Decimal('0')
                total_disbursed = grants.aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0')
                total_remaining = total_awarded - total_disbursed
                
                return {
                    'donor': {
                        'id': donor.id,
                        'name': donor.name,
                        'type': donor.donor_type,
                    },
                    'grants': {
                        'total_count': grants.count(),
                        'total_awarded': total_awarded,
                        'total_disbursed': total_disbursed,
                        'total_remaining': total_remaining,
                        'average_grant_size': grants.aggregate(avg=Avg('amount'))['avg'] or Decimal('0'),
                    },
                    'by_status': [
                        {
                            'status': item['status'],
                            'count': item['count'],
                            'total_amount': item['total_amount'],
                            'total_disbursed': item['total_disbursed'],
                            'remaining': item['total_amount'] - item['total_disbursed'],
                        }
                        for item in grants.values('status').annotate(
                            count=Count('id'),
                            total_amount=Sum('amount'),
                            total_disbursed=Sum('disbursed_amount')
                        )
                    ],
                    'timeline': [
                        {
                            'id': grant.id,
                            'name': grant.name,
                            'reference_number': grant.reference_number,
                            'amount': grant.amount,
                            'award_date': grant.award_date if hasattr(grant, 'award_date') else None,
                            'end_date': grant.end_date if hasattr(grant, 'end_date') else None,
                            'status': grant.status,
                        }
                        for grant in grants.order_by('-award_date')  # Most recent first
                    ],
                }
            except Donor.DoesNotExist:
                raise ValueError(f"Donor with ID {donor_id} does not exist.")
        else:
            # Summary analysis of all donors
            donors = get_accessible_donors(self.user)
            
            donor_analysis = []
            for donor in donors:
                grants = Grant.objects.filter(donor=donor)
                # Check if user can access these grants
                accessible_grants = get_accessible_grants(self.user)
                grants = grants.filter(id__in=accessible_grants.values_list('id', flat=True))
                
                if grants.exists():
                    total_awarded = grants.aggregate(total=Sum('amount'))['total'] or Decimal('0')
                    total_disbursed = grants.aggregate(total=Sum('disbursed_amount'))['total'] or Decimal('0')
                    
                    donor_analysis.append({
                        'donor_id': donor.id,
                        'donor_name': donor.name,
                        'donor_type': donor.donor_type,
                        'grant_count': grants.count(),
                        'total_awarded': total_awarded,
                        'total_disbursed': total_disbursed,
                        'total_remaining': total_awarded - total_disbursed,
                        'average_grant_size': grants.aggregate(avg=Avg('amount'))['avg'] or Decimal('0'),
                        'disbursement_rate': (total_disbursed / total_awarded * 100) if total_awarded > 0 else Decimal('0'),
                    })
            
            # Sort by total awarded
            donor_analysis.sort(key=lambda x: x['total_awarded'], reverse=True)
            
            return {
                'donors': donor_analysis,
                'summary': {
                    'total_donors_with_grants': len(donor_analysis),
                    'total_grants': sum(d['grant_count'] for d in donor_analysis),
                    'total_awarded': sum(d['total_awarded'] for d in donor_analysis),
                    'total_disbursed': sum(d['total_disbursed'] for d in donor_analysis),
                    'total_remaining': sum(d['total_remaining'] for d in donor_analysis),
                },
            }

    def get_grant_probability_analysis(self) -> Dict[str, Any]:
        """
        Get grant probability/success rate analysis.

        Returns:
            Dict containing grant probability analysis.
        """
        # This would require tracking grant applications vs awards
        # For now, we'll return a placeholder structure
        return {
            'note': 'Grant probability analysis requires tracking of grant applications and outcomes.',
            'application_to_award_ratio': None,
            'average_approval_time': None,  # Days from application to award
            'success_rate_by_type': {},  # Would require grant types/categories
            'success_rate_by_donor_type': {},  # Would require donor type tracking
            'trend': 'insufficient_data',
        }