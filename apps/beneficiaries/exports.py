"""CSV export adapter for the Phase 17 beneficiary register."""

from __future__ import annotations

import csv
import logging
from io import StringIO

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from apps.rbac.authorization import user_has_permission

from .permissions import BENEFICIARIES_EXPORT, BENEFICIARIES_MANAGE
from .selectors import visible_beneficiaries

logger = logging.getLogger(__name__)


def formula_safe_csv_value(value) -> str:
    """Prevent spreadsheet programs from interpreting untrusted values as formulas."""
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def beneficiary_register_csv_response(user) -> HttpResponse:
    """Build a scoped, formula-safe beneficiary register response."""
    if not (
        user_has_permission(user, BENEFICIARIES_EXPORT)
        or user_has_permission(user, BENEFICIARIES_MANAGE)
    ):
        raise PermissionDenied("Beneficiary export permission is required.")

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Beneficiary ID",
            "Full name",
            "Category",
            "Classification",
            "Status",
            "Confidentiality",
            "Gender",
            "Date of birth",
            "Is minor",
            "Phone",
            "Email",
            "Country",
            "Province or region",
            "District",
            "Community",
            "Household",
            "Organization unit",
            "Responsible officer",
            "Case manager",
            "Registration date",
            "Consent status",
        ]
    )
    row_count = 0
    queryset = visible_beneficiaries(user).order_by("reference_number")
    for beneficiary in queryset.iterator(chunk_size=500):
        responsible_officer = beneficiary.primary_responsible_officer
        case_manager = beneficiary.case_manager
        household = beneficiary.household
        row = [
            beneficiary.reference_number,
            beneficiary.full_name,
            beneficiary.category.name if beneficiary.category else "",
            beneficiary.classification.name if beneficiary.classification else "",
            beneficiary.get_status_display(),
            beneficiary.get_confidentiality_display(),
            beneficiary.gender.name if beneficiary.gender else "",
            beneficiary.date_of_birth,
            "Yes" if beneficiary.is_minor else "No",
            beneficiary.phone_primary,
            beneficiary.email,
            beneficiary.country,
            beneficiary.province_or_region,
            beneficiary.district,
            beneficiary.community,
            household.reference_number if household else "",
            beneficiary.organization_unit.name if beneficiary.organization_unit else "",
            responsible_officer.full_name if responsible_officer else "",
            case_manager.full_name if case_manager else "",
            beneficiary.registration_date,
            beneficiary.get_consent_status_display(),
        ]
        writer.writerow([formula_safe_csv_value(value) for value in row])
        row_count += 1

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="beneficiary_register.csv"'
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "beneficiary_register_exported",
        extra={
            "beneficiary_event": {
                "action": "beneficiary.register_exported",
                "format": "csv",
                "actor_id": str(user.pk),
                "row_count": row_count,
                "scope": "visible_beneficiaries",
            }
        },
    )
    return response
