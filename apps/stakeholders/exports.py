"""Small CSV export adapter pending the later shared export engine."""

from __future__ import annotations

import csv
import logging
from io import StringIO

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from apps.rbac.authorization import user_has_permission

from .permissions import PARTNERS_EXPORT, PARTNERS_MANAGE
from .selectors import visible_stakeholders

logger = logging.getLogger(__name__)


def formula_safe_csv_value(value) -> str:
    """Prevent spreadsheet programs from interpreting untrusted values as formulas."""
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def stakeholder_register_csv_response(user) -> HttpResponse:
    """Build a scoped, formula-safe stakeholder register response."""
    if not (
        user_has_permission(user, PARTNERS_EXPORT)
        or user_has_permission(user, PARTNERS_MANAGE)
    ):
        raise PermissionDenied("Stakeholder export permission is required.")

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Stakeholder ID",
            "Legal or full name",
            "Trading name",
            "Entity type",
            "Relationship type",
            "Classification",
            "Status",
            "Confidentiality",
            "Country",
            "Province or region",
            "District",
            "Organization unit",
            "Responsible officer",
            "Relationship start date",
        ]
    )
    row_count = 0
    queryset = visible_stakeholders(user).order_by("reference_number")
    for stakeholder in queryset.iterator(chunk_size=500):
        responsible_officer = stakeholder.primary_responsible_officer
        row = [
            stakeholder.reference_number,
            stakeholder.legal_name,
            stakeholder.trading_name,
            stakeholder.get_entity_type_display(),
            stakeholder.relationship_type.name if stakeholder.relationship_type else "",
            stakeholder.classification.name if stakeholder.classification else "",
            stakeholder.get_status_display(),
            stakeholder.get_confidentiality_display(),
            stakeholder.country,
            stakeholder.province_or_region,
            stakeholder.district,
            stakeholder.organization_unit.name if stakeholder.organization_unit else "",
            responsible_officer.full_name if responsible_officer else "",
            stakeholder.relationship_start_date,
        ]
        writer.writerow([formula_safe_csv_value(value) for value in row])
        row_count += 1

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="stakeholder_register.csv"'
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "stakeholder_register_exported",
        extra={
            "stakeholder_event": {
                "action": "stakeholder.register_exported",
                "format": "csv",
                "actor_id": str(user.pk),
                "row_count": row_count,
                "scope": "visible_stakeholders",
            }
        },
    )
    return response
