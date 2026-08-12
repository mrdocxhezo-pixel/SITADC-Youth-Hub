"""Provider indexing volunteer profiles."""

from __future__ import annotations

from apps.volunteers.models import VolunteerProfile
from apps.volunteers.permissions import VOLUNTEERS_VIEW
from apps.volunteers.selectors import visible_volunteer_profiles

from .base import SearchProvider, register


class VolunteerProfileProvider(SearchProvider):
    key = "volunteers.profile"
    label = "Volunteers"
    model = VolunteerProfile
    detail_url_name = "volunteers:detail"
    view_permissions = (VOLUNTEERS_VIEW, "volunteers.manage")
    search_fields = (
        "reference_number",
        "user__first_name",
        "user__last_name",
        "phone_number",
        "email",
        "national_id",
        "membership_number",
        "district",
        "community",
    )
    title_field = "user__full_name"
    subtitle_fields = ("reference_number", "district")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return visible_volunteer_profiles(user).select_related("user")


register(VolunteerProfileProvider())
