"""Finance Engine sponsors providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from apps.finance.selectors import get_accessible_sponsors

User = get_user_model()


class SponsorsProvider:
    """Provider for sponsors data."""

    def __init__(self, user: Any):
        """
        Initialize the sponsors provider.

        Args:
            user: The user requesting the sponsors data.
        """
        self.user = user

    def get_sponsors_summary(self) -> dict[str, Any]:
        """
        Get sponsors summary data.

        Returns:
            Dict containing sponsors summary information.
        """
        sponsors = get_accessible_sponsors(self.user)

        # Overall sponsor statistics
        sponsored_amount = sponsors.aggregate(total=Sum("sponsored_amount"))[
            "total"
        ] or Decimal("0")
        average_contribution = sponsors.aggregate(avg=Avg("sponsored_amount"))[
            "avg"
        ] or Decimal("0")

        # Sponsors by type (if sponsor_type field exists)
        if hasattr(sponsors.first() if sponsors.exists() else None, "sponsor_type"):
            by_type = (
                sponsors.values("sponsor_type")
                .annotate(count=Count("id"), sponsored_amount=Sum("sponsored_amount"))
                .order_by("-sponsored_amount")
            )
        else:
            by_type = []

        # Top sponsors by contribution
        top_sponsors = sponsors.order_by("-sponsored_amount")[:10]

        # Recently active sponsors (sponsored in last 90 days)
        ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
        # This would require linking sponsorships to transactions - assuming
        # we have a way to track this
        # For now, we'll use a placeholder based on when sponsor records were updated
        recently_active = sponsors.filter(updated_at__gte=ninety_days_ago).order_by(
            "-updated_at"
        )[:5]

        # Sponsors by renewal status
        # This would require tracking sponsorship agreements and renewal dates
        # For now, we'll use a placeholder

        return {
            "summary": {
                "total_sponsors": sponsors.count(),
                "sponsored_amount": sponsored_amount,
                "average_contribution": average_contribution,
            },
            "by_type": (
                [
                    {
                        "type": item["sponsor_type"],
                        "count": item["count"],
                        "sponsored_amount": item["sponsored_amount"],
                        "average_contribution": (
                            item["sponsored_amount"] / item["count"]
                            if item["count"] > 0
                            else Decimal("0")
                        ),
                    }
                    for item in by_type
                ]
                if by_type
                else []
            ),
            "top_sponsors": [
                {
                    "id": sponsor.id,
                    "name": sponsor.name,
                    "type": getattr(sponsor, "sponsor_type", "unspecified"),
                    "sponsored_amount": sponsor.sponsored_amount,
                    "contact_person": sponsor.contact_person,
                    "email": sponsor.email,
                }
                for sponsor in top_sponsors
            ],
            "recently_active": [
                {
                    "id": sponsor.id,
                    "name": sponsor.name,
                    "type": getattr(sponsor, "sponsor_type", "unspecified"),
                    "sponsored_amount": sponsor.sponsored_amount,
                    "last_updated": sponsor.updated_at,
                }
                for sponsor in recently_active
            ],
        }

    def get_sponsorship_trends(self, years: int = 5) -> dict[str, Any]:
        """
        Get sponsorship trends over time.

        Args:
            years: Number of years to look back.

        Returns:
            Dict containing sponsorship trends data.
        """
        # This would require tracking sponsorship dates
        # For now, we'll return a placeholder structure based on sponsor
        # creation/update dates
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=365 * years)

        # Get sponsors in the period (based on creation date)
        sponsors = get_accessible_sponsors(self.user).filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        # Group by year
        yearly_data = defaultdict(
            lambda: {
                "count": 0,
                "sponsored_amount": Decimal("0"),
            }
        )

        for sponsor in sponsors:
            year = sponsor.created_at.year
            yearly_data[year]["count"] += 1
            yearly_data[year]["sponsored_amount"] += sponsor.sponsored_amount

        # Sort by year
        sorted_data = sorted(yearly_data.items())

        return {
            "period_type": "yearly",
            "start_date": start_date,
            "end_date": end_date,
            "data": [
                {
                    "year": year,
                    "sponsor_count": data["count"],
                    "new_sponsors": data["count"],  # Simplified - all counted as new
                    "sponsored_amount": data["sponsored_amount"],
                    "average_contribution": (
                        data["sponsored_amount"] / data["count"]
                        if data["count"] > 0
                        else Decimal("0")
                    ),
                }
                for year, data in sorted_data
            ],
            "summary": {
                "total_new_sponsors": sum(
                    data["count"] for data in yearly_data.values()
                ),
                "sponsored_amount": sum(
                    data["sponsored_amount"] for data in yearly_data.values()
                ),
            },
        }

    def get_sponsorship_benefits_analysis(self) -> dict[str, Any]:
        """
        Get sponsorship benefits analysis.

        Returns:
            Dict containing sponsorship benefits analysis data.
        """
        # This would require tracking what sponsors receive in return for
        # their sponsorship
        # For now, we'll return a placeholder structure
        return {
            "note": (
                "Sponsorship benefits analysis requires tracking of "
                "sponsorship agreements and deliverables."
            ),
            "benefit_types": {},  # Would require benefit type tracking
            "average_benefit_value": None,  # Average value of benefits provided
            "sponsor_satisfaction": None,  # Would require survey data
            "renewal_rate_by_benefit": {},  # Renewal rates by benefit type
        }

    def get_upcoming_renewals(self, days_ahead: int = 90) -> list[dict[str, Any]]:
        """
        Get sponsors with upcoming renewal dates.

        Args:
            days_ahead: Number of days ahead to look for renewals.

        Returns:
            List of sponsors with upcoming renewals.
        """
        # This would require tracking renewal dates in sponsorship agreements
        # For now, we'll return an empty list as a placeholder
        return []
        # In a real implementation, you would:
        # 1. Get sponsorship agreements with renewal dates
        # 2. Filter for renewals within the specified time period
        # 3. Return sponsor information with renewal details
