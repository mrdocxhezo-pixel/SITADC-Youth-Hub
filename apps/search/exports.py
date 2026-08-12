"""CSV export for Enterprise Search results.

Only the actor's accessible hits are exported; results flow through the
permission-scaled providers so confidentiality is preserved in the payload.
"""

from __future__ import annotations

import csv

from django.http import HttpResponse
from django.utils.translation import gettext as _

from .exceptions import SearchValidationError
from .services import run_search


def _sanitize(value: str | None) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ")
    return text.strip()


def build_csv_response(results) -> HttpResponse:
    """Serialize grouped search results into a CSV download."""
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="search-results.csv"'
    response.write("\ufeff")  # BOM so Excel renders UTF-8 correctly

    writer = csv.writer(response)
    writer.writerow(
        [_("Entity"), _("Title"), _("Reference"), _("Status"), _("Link URL")]
    )
    for group in results.groups:
        for hit in group.hits:
            writer.writerow(
                [
                    _sanitize(hit.label),
                    _sanitize(hit.title),
                    _sanitize(hit.reference),
                    _sanitize(hit.status),
                    _sanitize(hit.url),
                ]
            )
    return response


def export_search_csv(user, query: str, types=None) -> HttpResponse:
    """Permission-scaled convenience wrapper for views."""
    if not query:
        raise SearchValidationError(_("Enter a search term to export."))
    results = run_search(user, query, types, persist=False)
    return build_csv_response(results)
