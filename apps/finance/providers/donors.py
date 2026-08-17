"""Finance Engine donors providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from apps.finance.selectors import get_accessible_donors

User = get_user_model()


class DonorsProvider:
    """Provider for donors data."""

    def __init__(self, user: Any):
        """
        Initialize the donors provider.

        Args:
            user: The user requesting the donors data.
        """
        self.user = user

    def get_donors_summary(self) -> dict[str, Any]:
        """
        Get donors summary data.

        Returns:
            Dict containing donors summary information.
        """
        donors = get_accessible_donors(self.user)

        # Overall donor statistics
        total_donated = donors.aggregate(total=Sum("total_donated"))[
            "total"
        ] or Decimal("0")
        average_contribution = donors.aggregate(avg=Avg("total_donated"))[
            "avg"
        ] or Decimal("0")

        # Donors by type
        by_type = (
            donors.values("donor_type")
            .annotate(count=Count("id"), total_donated=Sum("total_donated"))
            .order_by("-total_donated")
        )

        # Top donors by contribution
        top_donors = donors.order_by("-total_donated")[:10]

        # Recently active donors (donated in last 90 days)
        ninety_days_ago = timezone.now() - timezone.timedelta(days=90)
        # This would require linking donations to transactions - assuming
        # we have a way to track this
        # For now, we'll use a placeholder based on when donor records were updated
        recently_active = donors.filter(updated_at__gte=ninety_days_ago).order_by(
            "-updated_at"
        )[:5]

        # Donors by retention (those who have donated multiple times)
        # This would require tracking donation history
        # For now, we'll use a placeholder

        return {
            "summary": {
                "total_donors": donors.count(),
                "total_donated": total_donated,
                "average_contribution": average_contribution,
            },
            "by_type": [
                {
                    "type": item["donor_type"],
                    "count": item["count"],
                    "total_donated": item["total_donated"],
                    "average_contribution": (
                        item["total_donated"] / item["count"]
                        if item["count"] > 0
                        else Decimal("0")
                    ),
                }
                for item in by_type
            ],
            "top_donors": [
                {
                    "id": donor.id,
                    "name": donor.name,
                    "type": donor.donor_type,
                    "total_donated": donor.total_donated,
                    "contact_person": donor.contact_person,
                    "email": donor.email,
                }
                for donor in top_donors
            ],
            "recently_active": [
                {
                    "id": donor.id,
                    "name": donor.name,
                    "type": donor.donor_type,
                    "total_donated": donor.total_donated,
                    "last_updated": donor.updated_at,
                }
                for donor in recently_active
            ],
        }

    def get_donor_giving_trends(self, years: int = 5) -> dict[str, Any]:
        """
        Get donor giving trends over time.

        Args:
            years: Number of years to look back.

        Returns:
            Dict containing donor giving trends data.
        """
        # This would require tracking donation dates
        # For now, we'll return a placeholder structure based on donor
        # creation/update dates
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=365 * years)

        # Get donors in the period (based on creation date)
        donors = get_accessible_donors(self.user).filter(
            created_at__gte=start_date, created_at__lte=end_date
        )

        # Group by year
        yearly_data = defaultdict(
            lambda: {
                "count": 0,
                "total_donated": Decimal("0"),
            }
        )

        for donor in donors:
            year = donor.created_at.year
            yearly_data[year]["count"] += 1
            yearly_data[year]["total_donated"] += donor.total_donated

        # Sort by year
        sorted_data = sorted(yearly_data.items())

        return {
            "period_type": "yearly",
            "start_date": start_date,
            "end_date": end_date,
            "data": [
                {
                    "year": year,
                    "donor_count": data["count"],
                    "new_donors": data["count"],  # Simplified - all counted as new
                    "total_donated": data["total_donated"],
                    "average_contribution": (
                        data["total_donated"] / data["count"]
                        if data["count"] > 0
                        else Decimal("0")
                    ),
                }
                for year, data in sorted_data
            ],
            "summary": {
                "total_new_donors": sum(data["count"] for data in yearly_data.values()),
                "total_donated": sum(
                    data["total_donated"] for data in yearly_data.values()
                ),
            },
        }

    def get_donor_retention_analysis(self) -> dict[str, Any]:
        """
        Get donor retention analysis.

        Returns:
            Dict containing donor retention analysis data.
        """
        # This would require tracking donation history over time
        # For now, we'll return a placeholder structure
        return {
            "note": (
                "Donor retention analysis requires tracking of "
                "donation history over time."
            ),
            "retention_rate": None,  # Percentage of donors who give again
            "average_giving_duration": None,  # Average years a donor continues giving
            "lapse_rate": None,  # Percentage of donors who stop giving
            "reactivation_rate": None,  # % of lapsed donors who give again
            "donor_value_distribution": {},  # Distribution of donor lifetime values
        }

    def get_donor_demographics_analysis(self) -> dict[str, Any]:
        """
        Get donor demographics analysis.

        Returns:
            Dict containing donor demographics analysis data.
        """
        donors = get_accessible_donors(self.user)

        # By donor type
        by_type = donors.values("donor_type").annotate(count=Count("id"))

        # By geography (if address information is available)
        # This would require parsing address data
        by_geography = {}  # Placeholder

        # By organization size/type (for institutional donors)
        # This would require additional fields
        by_organization = {}  # Placeholder

        return {
            "by_type": [
                {
                    "type": item["donor_type"],
                    "count": item["count"],
                    "percentage": (
                        (item["count"] / donors.count() * 100)
                        if donors.count() > 0
                        else Decimal("0")
                    ),
                }
                for item in by_type
            ],
            "by_geography": by_geography,
            "by_organization": by_organization,
            "note": "Demographics analysis limited by available data fields.",
        }

    def get_large_donors(
        self, threshold_amount: Decimal, time_period_years: int = 1
    ) -> list[dict[str, Any]]:
        """
        Get donors who have contributed above a certain threshold.

        Args:
            threshold_amount: Minimum contribution amount to include.
            time_period_years: Number of years to look back for contributions.

        Returns:
            List of large donor dictionaries.
        """
        donors = get_accessible_donors(self.user).filter(
            total_donated__gte=threshold_amount
        )

        # If we wanted to look at contributions within a specific time period,
        # we would need to track donation history with dates

        return [
            {
                "id": donor.id,
                "name": donor.name,
                "type": donor.donor_type,
                "total_donated": donor.total_donated,
                "contact_person": donor.contact_person,
                "email": donor.email,
            }
            for donor in donors.order_by("-total_donated")
        ]
