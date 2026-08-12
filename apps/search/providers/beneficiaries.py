"""Provider indexing beneficiary records."""

from __future__ import annotations

from apps.beneficiaries.models import Beneficiary
from apps.beneficiaries.permissions import BENEFICIARIES_VIEW
from apps.beneficiaries.selectors import visible_beneficiaries

from .base import SearchProvider, register


class BeneficiaryProvider(SearchProvider):
    key = "beneficiaries.beneficiary"
    label = "Beneficiaries"
    model = Beneficiary
    detail_url_name = "beneficiaries:profile"
    view_permissions = (BENEFICIARIES_VIEW, "beneficiaries.manage")
    search_fields = (
        "reference_number",
        "first_name",
        "middle_name",
        "last_name",
        "national_id",
    )
    title_field = "full_name"
    subtitle_fields = ("reference_number",)
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return visible_beneficiaries(user)


register(BeneficiaryProvider())
