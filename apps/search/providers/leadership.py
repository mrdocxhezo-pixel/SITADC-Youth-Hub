"""Provider indexing leadership profiles."""

from __future__ import annotations

from apps.leadership.models import LeadershipProfile
from apps.leadership.permissions import LEADERSHIP_VIEW, user_can_view

from .base import SearchProvider, register


class LeadershipProfileProvider(SearchProvider):
    key = "leadership.profile"
    label = "Leadership Profiles"
    model = LeadershipProfile
    detail_url_name = "leadership:profile_detail"
    view_permissions = (LEADERSHIP_VIEW,)
    search_fields = (
        "reference_number",
        "user__first_name",
        "user__last_name",
        "national_id",
        "phone_number",
        "position__name",
        "organizational_unit__name",
    )
    title_field = "user__full_name"
    subtitle_fields = ("position__name", "organizational_unit__name")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        base = LeadershipProfile.objects.with_supervisor()
        if getattr(user, "is_superuser", False) or user_can_view(user):
            return base
        return base.none()


register(LeadershipProfileProvider())
