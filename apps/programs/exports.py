"""Small CSV export adapter for program and project registers."""

from __future__ import annotations

import csv
import logging
from io import StringIO

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from apps.rbac.authorization import user_has_permission

from .permissions import (
    PROGRAMMES_EXPORT,
    PROGRAMMES_MANAGE,
    PROJECTS_EXPORT,
    PROJECTS_MANAGE,
)
from .selectors import visible_programs, visible_projects

logger = logging.getLogger(__name__)


def formula_safe_csv_value(value) -> str:
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{text}"
    return text


def program_register_csv_response(user) -> HttpResponse:
    if not (
        user_has_permission(user, PROGRAMMES_EXPORT)
        or user_has_permission(user, PROGRAMMES_MANAGE)
    ):
        raise PermissionDenied("Program export permission is required.")

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Program ID",
            "Title",
            "Category",
            "Status",
            "Priority",
            "Program manager",
            "Directorate",
            "Start date",
            "End date",
            "Approved budget",
            "Utilized budget",
            "Currency",
        ]
    )
    row_count = 0
    queryset = visible_programs(user).order_by("reference_number")
    for program in queryset.iterator(chunk_size=500):
        manager = program.program_manager
        row = [
            program.reference_number,
            program.title,
            program.category.name if program.category else "",
            program.get_status_display(),
            program.get_priority_display(),
            manager.full_name if manager else "",
            (
                program.responsible_directorate.name
                if program.responsible_directorate
                else ""
            ),
            program.start_date,
            program.end_date,
            program.budget_approved,
            program.budget_utilized,
            program.currency,
        ]
        writer.writerow([formula_safe_csv_value(value) for value in row])
        row_count += 1

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="program_register.csv"'
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "program_register_exported",
        extra={
            "program_event": {
                "action": "program.register_exported",
                "format": "csv",
                "actor_id": str(user.pk),
                "row_count": row_count,
                "scope": "visible_programs",
            }
        },
    )
    return response


def project_register_csv_response(user) -> HttpResponse:
    if not (
        user_has_permission(user, PROJECTS_EXPORT)
        or user_has_permission(user, PROJECTS_MANAGE)
    ):
        raise PermissionDenied("Project export permission is required.")

    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        [
            "Project ID",
            "Program ID",
            "Title",
            "Category",
            "Status",
            "Project manager",
            "Start date",
            "End date",
            "Approved budget",
            "Utilized budget",
            "Currency",
        ]
    )
    row_count = 0
    queryset = visible_projects(user).order_by("reference_number")
    for project in queryset.iterator(chunk_size=500):
        manager = project.project_manager
        row = [
            project.reference_number,
            project.program.reference_number,
            project.title,
            project.category.name if project.category else "",
            project.get_status_display(),
            manager.full_name if manager else "",
            project.start_date,
            project.end_date,
            project.budget_approved,
            project.budget_utilized,
            project.currency,
        ]
        writer.writerow([formula_safe_csv_value(value) for value in row])
        row_count += 1

    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="project_register.csv"'
    response["Cache-Control"] = "private, no-store"
    response["Pragma"] = "no-cache"
    response["X-Content-Type-Options"] = "nosniff"
    logger.info(
        "project_register_exported",
        extra={
            "program_event": {
                "action": "project.register_exported",
                "format": "csv",
                "actor_id": str(user.pk),
                "row_count": row_count,
                "scope": "visible_projects",
            }
        },
    )
    return response
