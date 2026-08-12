"""Providers indexing programmes and projects."""

from __future__ import annotations

from apps.programs.models import Program, Project
from apps.programs.selectors import visible_programs, visible_projects

from .base import SearchProvider, register


class ProgramProvider(SearchProvider):
    key = "programs.program"
    label = "Programmes"
    model = Program
    detail_url_name = "programs:program_profile"
    view_permissions = ("programmes.view", "programmes.manage")
    search_fields = (
        "reference_number",
        "title",
        "short_title",
        "description",
        "code",
    )
    title_field = "title"
    subtitle_fields = ("reference_number",)
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return visible_programs(user)


class ProjectProvider(SearchProvider):
    key = "programs.project"
    label = "Projects"
    model = Project
    detail_url_name = "programs:project_profile"
    view_permissions = ("projects.view", "projects.manage", "programmes.manage")
    search_fields = (
        "reference_number",
        "title",
        "short_title",
        "description",
        "district_scope",
    )
    title_field = "title"
    subtitle_fields = ("program__title", "reference_number")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return visible_projects(user).select_related("program")


register(ProgramProvider())
register(ProjectProvider())
