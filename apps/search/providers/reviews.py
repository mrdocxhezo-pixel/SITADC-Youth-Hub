"""Provider indexing reviews assigned to the actor."""

from __future__ import annotations

from apps.reviews.models import Review
from apps.reviews.permissions import VIEW as REVIEW_VIEW
from apps.reviews.selectors import get_reviews_for_user

from .base import SearchProvider, register


class ReviewProvider(SearchProvider):
    key = "reviews.review"
    label = "Reviews"
    model = Review
    detail_url_name = "reviews:detail"
    view_permissions = (REVIEW_VIEW,)
    search_fields = (
        "review_number",
        "report__title",
        "report__reference_number",
    )
    title_field = "report__title"
    subtitle_fields = ("review_number", "primary_reviewer__full_name")
    reference_field = "review_number"

    def title_value(self, instance):
        report = getattr(instance, "report", None)
        if report is not None:
            return report.title or f"Review {instance.review_number}"
        return f"Review {instance.review_number}"

    def queryset(self, user):
        return get_reviews_for_user(user).select_related("report", "primary_reviewer")


register(ReviewProvider())
