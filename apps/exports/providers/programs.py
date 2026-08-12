"""Providers for programmes and projects (source types PROGRAM and PROJECT)."""

from __future__ import annotations

from apps.programs.models import Program, Project
from apps.programs.permissions import PROGRAMMES_MANAGE, PROGRAMMES_VIEW
from apps.programs.selectors import visible_programs, visible_projects

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class ProgramProvider(BaseProvider):
    """Export the programme catalogue."""

    key = "programs.program"
    source_type = ExportSourceType.PROGRAM
    label = "Programmes"
    model = Program
    view_permissions = (PROGRAMMES_VIEW,)
    manage_permissions = (PROGRAMMES_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("title", "Programme Title"),
        ExportColumn("short_title", "Short Title"),
        ExportColumn("status", "Status"),
        ExportColumn("priority", "Priority"),
        ExportColumn("start_date", "Start Date"),
        ExportColumn("end_date", "End Date"),
        ExportColumn("budget_approved", "Approved Budget"),
        ExportColumn("budget_utilized", "Budget Utilized"),
        ExportColumn("currency", "Currency"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_programs(user)


class ProjectProvider(BaseProvider):
    """Export the project catalogue."""

    key = "programs.project"
    source_type = ExportSourceType.PROJECT
    label = "Projects"
    model = Project
    view_permissions = (PROGRAMMES_VIEW,)
    manage_permissions = (PROGRAMMES_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn(
            "program",
            "Programme",
            accessor=lambda obj: obj.program.title if obj.program_id else "",
        ),
        ExportColumn("title", "Project Title"),
        ExportColumn("short_title", "Short Title"),
        ExportColumn("status", "Status"),
        ExportColumn("priority", "Priority"),
        ExportColumn("start_date", "Start Date"),
        ExportColumn("end_date", "End Date"),
        ExportColumn("budget_approved", "Approved Budget"),
        ExportColumn("currency", "Currency"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return visible_projects(user).select_related("program")


register(ProgramProvider())
register(ProjectProvider())
