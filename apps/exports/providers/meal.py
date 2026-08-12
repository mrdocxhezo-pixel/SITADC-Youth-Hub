"""Providers for MEAL datasets (source type MEAL).

Exports the indicator register, indicator results and results frameworks,
scoped through the MEAL module's fail-closed ``meal_queryset`` helper.
"""

from __future__ import annotations

from apps.meal.models import Indicator, IndicatorResult, ResultsFramework
from apps.meal.permissions import MEAL_MANAGE, MEAL_VIEW
from apps.meal.selectors import meal_queryset

from ..constants import ExportSourceType
from ..renderers.base import ExportColumn
from .base import BaseProvider, register


def _baseline_value(obj):
    baseline = obj.latest_approved_baseline
    return str(baseline.value) if baseline else ""


def _target_value(obj):
    target = obj.latest_target
    return str(target.value) if target else ""


class IndicatorProvider(BaseProvider):
    """Export the indicator register."""

    key = "meal.indicators"
    source_type = ExportSourceType.MEAL
    label = "Indicator Register"
    model = Indicator
    view_permissions = (MEAL_VIEW,)
    manage_permissions = (MEAL_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("code", "Indicator Code"),
        ExportColumn("title", "Indicator Title"),
        ExportColumn(
            "category",
            "Category",
            accessor=lambda obj: obj.category.name if obj.category_id else "",
        ),
        ExportColumn("indicator_type", "Type"),
        ExportColumn("baseline", "Baseline", accessor=_baseline_value),
        ExportColumn("target", "Target", accessor=_target_value),
        ExportColumn("status", "Status"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return meal_queryset(user, Indicator).select_related("category")


class IndicatorResultProvider(BaseProvider):
    """Export reported indicator results."""

    key = "meal.results"
    source_type = ExportSourceType.MEAL
    label = "Indicator Results"
    model = IndicatorResult
    view_permissions = (MEAL_VIEW,)
    manage_permissions = (MEAL_MANAGE,)
    status_field = "status"

    columns_catalogue = (
        ExportColumn(
            "indicator",
            "Indicator",
            accessor=lambda obj: f"{obj.indicator.code} - {obj.indicator.title}",
        ),
        ExportColumn("period_label", "Period"),
        ExportColumn("submission_date", "Submission Date"),
        ExportColumn("value", "Actual Value"),
        ExportColumn(
            "target",
            "Target",
            accessor=lambda obj: str(obj.target.value) if obj.target_id else "",
        ),
        ExportColumn(
            "data_source",
            "Data Source",
            accessor=lambda obj: obj.data_source.name if obj.data_source_id else "",
        ),
        ExportColumn("status", "Status"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return meal_queryset(user, IndicatorResult).select_related(
            "indicator", "target", "data_source"
        )


class ResultsFrameworkProvider(BaseProvider):
    """Export MEAL results frameworks."""

    key = "meal.frameworks"
    source_type = ExportSourceType.MEAL
    label = "Results Frameworks"
    model = ResultsFramework
    view_permissions = (MEAL_VIEW,)
    manage_permissions = (MEAL_MANAGE,)
    reference_field = "reference_number"
    status_field = "status"

    columns_catalogue = (
        ExportColumn("reference_number", "Reference Number"),
        ExportColumn("title", "Framework Title"),
        ExportColumn("strategic_objective", "Strategic Objective"),
        ExportColumn("version", "Version"),
        ExportColumn("status", "Status"),
        ExportColumn("effective_from", "Effective From"),
        ExportColumn("effective_to", "Effective To"),
        ExportColumn("created_at", "Created At"),
    )

    def queryset(self, user):
        return meal_queryset(user, ResultsFramework)


register(IndicatorProvider())
register(IndicatorResultProvider())
register(ResultsFrameworkProvider())
