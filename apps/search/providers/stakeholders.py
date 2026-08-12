"""Provider indexing stakeholders and partners."""

from __future__ import annotations

from apps.stakeholders.models import Stakeholder
from apps.stakeholders.selectors import visible_stakeholders

from .base import SearchProvider, register


class StakeholderProvider(SearchProvider):
    key = "stakeholders.partner"
    label = "Stakeholders & Partners"
    model = Stakeholder
    detail_url_name = "stakeholders:profile"
    view_permissions = ("partners.view", "partners.view_directory", "partners.manage")
    search_fields = (
        "reference_number",
        "legal_name",
        "trading_name",
        "display_name",
        "acronym",
        "former_names",
        "description",
    )
    title_field = "display_name"
    subtitle_fields = ("legal_name", "acronym")
    reference_field = "reference_number"
    status_field = "status"

    def title_value(self, instance):
        title = getattr(instance, "display_name", "") or ""
        if not title:
            title = getattr(instance, "legal_name", "") or ""
        return title or str(instance)

    def queryset(self, user):
        return visible_stakeholders(user)


register(StakeholderProvider())
