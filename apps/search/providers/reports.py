"""Providers indexing report templates."""

from __future__ import annotations

from apps.reports.models import ReportTemplate
from apps.reports.permissions import REPORT_TEMPLATE_MANAGE, REPORT_TEMPLATE_VIEW
from apps.reports.selectors import template_queryset

from .base import SearchProvider, register


class ReportTemplateProvider(SearchProvider):
    key = "reports.template"
    label = "Report Templates"
    model = ReportTemplate
    detail_url_name = "reports:template_detail"
    view_permissions = (REPORT_TEMPLATE_VIEW, REPORT_TEMPLATE_MANAGE)
    search_fields = (
        "reference_number",
        "code",
        "title",
        "description",
        "department",
    )
    title_field = "title"
    subtitle_fields = ("code", "department")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        return template_queryset(user)


register(ReportTemplateProvider())
