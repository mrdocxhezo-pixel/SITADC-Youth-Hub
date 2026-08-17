"""Finance Engine fundraising providers."""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.apps import apps as django_apps
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Avg, Count, ExpressionWrapper, F, Sum
from django.utils import timezone

from apps.finance.selectors import get_accessible_fundraising_campaigns

User = get_user_model()


class FundraisingProvider:
    """Provider for fundraising data."""

    def __init__(self, user: Any):
        """
        Initialize the fundraising provider.

        Args:
            user: The user requesting the fundraising data.
        """
        self.user = user

    def get_fundraising_summary(self) -> dict[str, Any]:
        """
        Get fundraising summary data.

        Returns:
            Dict containing fundraising summary information.
        """
        campaigns = get_accessible_fundraising_campaigns(self.user)

        # Overall fundraising statistics
        total_pledged = campaigns.aggregate(total=Sum("target_amount"))[
            "total"
        ] or Decimal("0")
        total_raised = campaigns.aggregate(total=Sum("amount_raised"))[
            "total"
        ] or Decimal("0")
        total_remaining = total_pledged - total_raised

        # Average campaign size
        average_target = campaigns.aggregate(avg=Avg("target_amount"))[
            "avg"
        ] or Decimal("0")

        # Campaigns by status
        by_status = (
            campaigns.values("status")
            .annotate(
                count=Count("id"),
                total_pledged=Sum("target_amount"),
                total_raised=Sum("amount_raised"),
            )
            .order_by("-total_raised")
        )

        # Recently launched campaigns
        recent_launches = campaigns.filter(status__in=["ACTIVE"]).order_by(
            "-start_date"
        )[:5]

        # Campaigns nearing deadline
        seven_days_from_now = timezone.now() + timezone.timedelta(days=7)
        nearing_deadline = campaigns.filter(
            end_date__lte=seven_days_from_now,
            end_date__gte=timezone.now(),
            status__in=["ACTIVE"],
        ).order_by("end_date")[:5]

        # Top performing campaigns (by percentage of goal reached)
        top_performing = (
            campaigns.annotate(
                progress_percentage=ExpressionWrapper(
                    (F("amount_raised") * 100.0) / F("target_amount"),
                    output_field=models.FloatField(),
                )
            )
            .filter(target_amount__gt=0)
            .order_by("-progress_percentage")[:5]
        )

        return {
            "summary": {
                "total_campaigns": campaigns.count(),
                "total_pledged": total_pledged,
                "total_raised": total_raised,
                "total_remaining": total_remaining,
                "average_target": average_target,
                "overall_progress_percentage": (
                    (total_raised / total_pledged * 100)
                    if total_pledged > 0
                    else Decimal("0")
                ),
            },
            "by_status": [
                {
                    "status": item["status"],
                    "count": item["count"],
                    "total_pledged": item["total_pledged"],
                    "total_raised": item["total_raised"],
                    "remaining": item["total_pledged"] - item["total_raised"],
                    "progress_percentage": (
                        (item["total_raised"] / item["total_pledged"] * 100)
                        if item["total_pledged"] > 0
                        else Decimal("0")
                    ),
                }
                for item in by_status
            ],
            "recent_launches": [
                {
                    "id": campaign.id,
                    "name": campaign.name,
                    "target_amount": campaign.target_amount,
                    "amount_raised": campaign.amount_raised,
                    "start_date": (
                        campaign.start_date if hasattr(campaign, "start_date") else None
                    ),
                    "end_date": (
                        campaign.end_date if hasattr(campaign, "end_date") else None
                    ),
                    "progress_percentage": (
                        (campaign.amount_raised / campaign.target_amount * 100)
                        if campaign.target_amount > 0
                        else Decimal("0")
                    ),
                }
                for campaign in recent_launches
            ],
            "nearing_deadline": [
                {
                    "id": campaign.id,
                    "name": campaign.name,
                    "target_amount": campaign.target_amount,
                    "amount_raised": campaign.amount_raised,
                    "end_date": (
                        campaign.end_date if hasattr(campaign, "end_date") else None
                    ),
                    "days_remaining": (
                        (campaign.end_date - timezone.now().date()).days
                        if hasattr(campaign, "end_date")
                        else None
                    ),
                    "progress_percentage": (
                        (campaign.amount_raised / campaign.target_amount * 100)
                        if campaign.target_amount > 0
                        else Decimal("0")
                    ),
                }
                for campaign in nearing_deadline
            ],
            "top_performing": [
                {
                    "id": campaign.id,
                    "name": campaign.name,
                    "target_amount": campaign.target_amount,
                    "amount_raised": campaign.amount_raised,
                    "progress_percentage": (
                        (campaign.amount_raised / campaign.target_amount * 100)
                        if campaign.target_amount > 0
                        else Decimal("0")
                    ),
                }
                for campaign in top_performing
            ],
        }

    def get_fundraising_trends(self, years: int = 3) -> dict[str, Any]:
        """
        Get fundraising trends over time.

        Args:
            years: Number of years to look back.

        Returns:
            Dict containing fundraising trends data.
        """
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=365 * years)

        # Get campaigns in the period
        campaigns = get_accessible_fundraising_campaigns(self.user).filter(
            start_date__gte=start_date, start_date__lte=end_date
        )  # Assuming start_date field exists

        # Group by year
        yearly_data = defaultdict(
            lambda: {
                "count": 0,
                "total_pledged": Decimal("0"),
                "total_raised": Decimal("0"),
            }
        )

        for campaign in campaigns:
            year = (
                campaign.start_date.year
                if hasattr(campaign, "start_date")
                else campaign.created_at.year
            )
            yearly_data[year]["count"] += 1
            yearly_data[year]["total_pledged"] += campaign.target_amount
            yearly_data[year]["total_raised"] += campaign.amount_raised

        # Sort by year
        sorted_data = sorted(yearly_data.items())

        return {
            "period_type": "yearly",
            "start_date": start_date,
            "end_date": end_date,
            "data": [
                {
                    "year": year,
                    "campaign_count": data["count"],
                    "total_pledged": data["total_pledged"],
                    "total_raised": data["total_raised"],
                    "total_remaining": data["total_pledged"] - data["total_raised"],
                    "average_target": (
                        data["total_pledged"] / data["count"]
                        if data["count"] > 0
                        else Decimal("0")
                    ),
                    "average_raised": (
                        data["total_raised"] / data["count"]
                        if data["count"] > 0
                        else Decimal("0")
                    ),
                    "progress_percentage": (
                        (data["total_raised"] / data["total_pledged"] * 100)
                        if data["total_pledged"] > 0
                        else Decimal("0")
                    ),
                }
                for year, data in sorted_data
            ],
            "summary": {
                "total_campaigns": sum(data["count"] for data in yearly_data.values()),
                "total_pledged": sum(
                    data["total_pledged"] for data in yearly_data.values()
                ),
                "total_raised": sum(
                    data["total_raised"] for data in yearly_data.values()
                ),
                "total_remaining": sum(
                    data["total_pledged"] - data["total_raised"]
                    for data in yearly_data.values()
                ),
            },
        }

    def get_fundraising_performance_analysis(
        self, campaign_id: int | None = None
    ) -> dict[str, Any]:
        """
        Get fundraising performance analysis.

        Args:
            campaign_id: ID of specific campaign (optional). If None, returns
            analysis for all campaigns.

        Returns:
            Dict containing fundraising performance analysis data.
        """
        FundraisingCampaign = django_apps.get_model("finance", "FundraisingCampaign")

        if campaign_id:
            # Specific campaign analysis
            try:
                campaign = FundraisingCampaign.objects.get(id=campaign_id)
                # Check permissions
                accessible_campaigns = get_accessible_fundraising_campaigns(self.user)
                if not accessible_campaigns.filter(id=campaign_id).exists():
                    raise PermissionError(
                        "You do not have permission to access this campaign."
                    )

                # Calculate performance metrics
                progress_percentage = (
                    (campaign.amount_raised / campaign.target_amount * 100)
                    if campaign.target_amount > 0
                    else Decimal("0")
                )
                days_elapsed = (
                    (timezone.now().date() - campaign.start_date).days
                    if campaign.start_date
                    else 0
                )
                days_total = (
                    (campaign.end_date - campaign.start_date).days
                    if campaign.end_date and campaign.start_date
                    else 0
                )
                days_remaining = (
                    (campaign.end_date - timezone.now().date()).days
                    if campaign.end_date
                    else None
                )

                # Calculate daily fundraising rate
                daily_rate = (
                    (campaign.amount_raised / days_elapsed)
                    if days_elapsed > 0
                    else Decimal("0")
                )

                # Calculate required daily rate to reach goal
                required_daily_rate = (
                    (campaign.target_amount - campaign.amount_raised) / days_remaining
                    if days_remaining and days_remaining > 0
                    else Decimal("0")
                )

                return {
                    "campaign": {
                        "id": campaign.id,
                        "name": campaign.name,
                        "target_amount": campaign.target_amount,
                        "amount_raised": campaign.amount_raised,
                        "progress_percentage": progress_percentage,
                        "start_date": (
                            campaign.start_date
                            if hasattr(campaign, "start_date")
                            else None
                        ),
                        "end_date": (
                            campaign.end_date if hasattr(campaign, "end_date") else None
                        ),
                    },
                    "performance": {
                        "days_elapsed": days_elapsed,
                        "days_total": days_total,
                        "days_remaining": days_remaining,
                        "daily_rate": daily_rate,
                        "required_daily_rate": required_daily_rate,
                        "on_track": (
                            daily_rate >= required_daily_rate
                            if days_remaining and days_remaining > 0
                            else None
                        ),
                    },
                    "historical_data": [],  # Would include historical performance data
                    # if available
                }
            except FundraisingCampaign.DoesNotExist as exc:
                raise ValueError(
                    f"Fundraising campaign with ID {campaign_id} does not exist."
                ) from exc
        else:
            # Summary analysis of all campaigns
            campaigns = get_accessible_fundraising_campaigns(self.user)

            # Calculate overall statistics
            total_pledged = campaigns.aggregate(total=Sum("target_amount"))[
                "total"
            ] or Decimal("0")
            total_raised = campaigns.aggregate(total=Sum("amount_raised"))[
                "total"
            ] or Decimal("0")

            # Group by progress percentage ranges
            performance_ranges = [
                ("0-25%", Decimal("0"), Decimal("25")),
                ("26-50%", Decimal("26"), Decimal("50")),
                ("51-75%", Decimal("51"), Decimal("75")),
                ("76-90%", Decimal("76"), Decimal("90")),
                ("91-100%", Decimal("91"), Decimal("100")),
                ("100%+", Decimal("100"), None),  # Over goal
            ]

            range_performance = []
            for range_label, min_pct, max_pct in performance_ranges:
                if max_pct is None:
                    # 100%+ range
                    count = (
                        campaigns.filter(amount_raised__gt=F("target_amount")).count()
                        if hasattr(FundraisingCampaign, "amount_raised")
                        and hasattr(FundraisingCampaign, "target_amount")
                        else 0
                    )
                else:
                    count = (
                        campaigns.filter(
                            amount_raised__gte=(F("target_amount") * min_pct / 100),
                            amount_raised__lt=(F("target_amount") * max_pct / 100),
                        ).count()
                        if hasattr(FundraisingCampaign, "amount_raised")
                        and hasattr(FundraisingCampaign, "target_amount")
                        else 0
                    )

                range_performance.append(
                    {
                        "range": range_label,
                        "count": count,
                    }
                )

            # Calculate average performance metrics
            campaigns_with_dates = (
                campaigns.filter(start_date__isnull=False, end_date__isnull=False)
                if hasattr(FundraisingCampaign, "start_date")
                and hasattr(FundraisingCampaign, "end_date")
                else campaigns
            )

            avg_duration = None
            avg_daily_rate = None

            if campaigns_with_dates.exists():
                # This would require more complex calculations in practice
                pass

            return {
                "summary": {
                    "total_campaigns": campaigns.count(),
                    "total_pledged": total_pledged,
                    "total_raised": total_raised,
                    "total_remaining": total_pledged - total_raised,
                    "overall_progress_percentage": (
                        (total_raised / total_pledged * 100)
                        if total_pledged > 0
                        else Decimal("0")
                    ),
                },
                "performance_ranges": range_performance,
                "averages": {
                    # These would be calculated from actual data in a real
                    # implementation
                    "duration_days": avg_duration,
                    "daily_fundraising_rate": avg_daily_rate,
                },
            }
