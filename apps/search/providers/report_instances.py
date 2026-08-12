"""Provider indexing report instances (report management module)."""

from __future__ import annotations

from django.db.models import Q

from apps.rbac.authorization import user_has_permission
from apps.report_instances.models import Report
from apps.report_instances.permissions import VIEW, VIEW_ALL, VIEW_OWN

from .base import SearchProvider, register

REPORT_INSTANCES_MANAGE = "report_instances.manage"


class ReportInstanceProvider(SearchProvider):
    key = "reports.report"
    label = "Reports"
    model = Report
    detail_url_name = "report_instances:detail"
    view_permissions = (VIEW, VIEW_ALL, VIEW_OWN, REPORT_INSTANCES_MANAGE)
    search_fields = (
        "reference_number",
        "title",
        "department",
    )
    title_field = "title"
    subtitle_fields = ("reference_number", "department")
    reference_field = "reference_number"
    status_field = "status"

    def queryset(self, user):
        base = Report.objects.filter(is_deleted=False).select_related(
            "owner", "template"
        )
        if getattr(user, "is_superuser", False) or user_has_permission(
            user, REPORT_INSTANCES_MANAGE
        ):
            return base
        if user_has_permission(user, VIEW_ALL):
            return base
        if user_has_permission(user, VIEW) or user_has_permission(user, VIEW_OWN):
            return base.filter(
                Q(owner=user) | Q(assigned_reviewer=user), is_deleted=False
            ).select_related("owner", "template")
        return base.none()


register(ReportInstanceProvider())
