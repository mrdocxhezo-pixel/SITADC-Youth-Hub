"""Providers for report templates and report instances (source type REPORT)."""

from __future__ import annotations

from django.db.models import Q

from apps.report_instances.models import Report
from apps.report_instances.permissions import (
    VIEW as REPORT_VIEW,
)
from apps.report_instances.permissions import (
    VIEW_ALL as REPORT_VIEW_ALL,
)
from apps.reports.models import ReportTemplate
from apps.reports.permissions import REPORT_TEMPLATE_MANAGE, REPORT_TEMPLATE_VIEW
from apps.reports.selectors import template_queryset

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


class ReportTemplateProvider(BaseProvider):
    """Export the report template catalogue."""

    key = "reports.template"
    source_type = ExportSourceType.REPORT
    label = "Report Templates"
    model = ReportTemplate
    view_permissions = (REPORT_TEMPLATE_VIEW,)
    manage_permissions = (REPORT_TEMPLATE_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("name", "Template Name"),
        ExportColumn("code", "Code"),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn("status", "Status"),
        ExportColumn("version", "Version"),
        ExportColumn("confidentiality_level", "Confidentiality"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return template_queryset(user).select_related("category")


class ReportInstanceProvider(BaseProvider):
    """Export submitted report instances.

    ``apps.report_instances`` exposes no fail-closed selector, so scoping is
    performed here: full visibility for ``report_instances.view_all``,
    own reports for ``report_instances.view_own``, otherwise nothing.
    """

    key = "reports.instance"
    source_type = ExportSourceType.REPORT
    label = "Reports"
    model = Report
    view_permissions = (REPORT_VIEW, REPORT_VIEW_ALL)
    manage_permissions = ("reports.manage", "report_instances.export")
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("title", "Report Title"),
        ExportColumn(
            "template",
            "Template",
            accessor=lambda obj: obj.template.name if obj.template_id else "",
        ),
        ExportColumn("department", "Department"),
        ExportColumn("status", "Status"),
        ExportColumn("validation_status", "Validation Status"),
        ExportColumn("confidentiality", "Confidentiality"),
        ExportColumn("due_date", "Due Date"),
        ExportColumn("version_number", "Version"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        from apps.rbac.authorization import user_has_permission

        queryset = Report.objects.filter(is_deleted=False, is_archived=False)
        if not user or not getattr(user, "is_authenticated", False):
            return queryset.none()
        if user.is_superuser or user_has_permission(user, "report_instances.view_all"):
            return queryset
        if user_has_permission(user, "report_instances.view_own"):
            return queryset.filter(
                Q(owner_id=user.pk)
                | Q(assigned_reviewer_id=user.pk)
                | Q(created_by_id=user.pk)
            ).distinct()
        return queryset.none()


register(ReportTemplateProvider())
register(ReportInstanceProvider())
