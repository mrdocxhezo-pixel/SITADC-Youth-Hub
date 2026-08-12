"""Provider for beneficiary records (source type BENEFICIARY).

Beneficiary data is always considered sensitive: the provider only exposes
the identifier and demographic columns unless the actor holds the sensitive
export permission.
"""

from __future__ import annotations

from apps.beneficiaries.models import Beneficiary
from apps.beneficiaries.permissions import BENEFICIARIES_MANAGE, BENEFICIARIES_VIEW
from apps.beneficiaries.selectors import visible_beneficiaries

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class BeneficiaryProvider(BaseProvider):
    """Export the beneficiary register."""

    key = "beneficiaries.profile"
    source_type = ExportSourceType.BENEFICIARY
    label = "Beneficiaries"
    model = Beneficiary
    view_permissions = (BENEFICIARIES_VIEW,)
    manage_permissions = (BENEFICIARIES_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("full_name", "Full Name", accessor=lambda obj: obj.full_name),
        ExportColumn("date_of_birth", "Date of Birth", sensitive=True),
        ExportColumn("gender", "Gender"),
        ExportColumn("nationality", "Nationality"),
        ExportColumn("district", "District"),
        ExportColumn("community", "Community"),
        ExportColumn("status", "Status"),
        ExportColumn("registration_date", "Registration Date"),
        ExportColumn("enrolled_at", "Enrolled At"),
        ExportColumn("is_minor", "Is Minor"),
        ExportColumn("is_in_school", "In School"),
        ExportColumn("national_id_number", "National ID", sensitive=True),
        ExportColumn("phone_primary", "Primary Phone", sensitive=True),
        ExportColumn("email", "Email", sensitive=True),
        ExportColumn("physical_address", "Physical Address", sensitive=True),
    )

    def queryset(self, user):
        return visible_beneficiaries(user)


register(BeneficiaryProvider())
