"""Performance Optimization & Scalability permissions.

The ``performance.*`` catalogue supplements Django model-level permissions.
Every performance view must satisfy the relevant performance permission before
data is exposed.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.http import HttpRequest

from apps.rbac.authorization import user_has_permission

User = get_user_model()

PERFORMANCE_VIEW = "performance.view"
PERFORMANCE_CREATE = "performance.create"
PERFORMANCE_UPDATE = "performance.update"
PERFORMANCE_DELETE = "performance.delete"
PERFORMANCE_MANAGE = "performance.manage"
PERFORMANCE_CONFIGURE = "performance.configure"
PERFORMANCE_BENCHMARK = "performance.benchmark"
PERFORMANCE_EXPORT = "performance.export"
PERFORMANCE_OPTIMIZE = "performance.optimize"
PERFORMANCE_ALERT = "performance.alert"
PERFORMANCE_REPORT = "performance.report"


def _has(user: Any, *codes: str) -> bool:
    """Fail-closed check for any of the given permission codes."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if user.is_superuser:
        return True
    return any(user_has_permission(user, code) for code in codes)


def user_can_access_performance(user) -> bool:
    """Whether the actor may open the performance workspace."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_MANAGE)


def user_can_view_performance(user) -> bool:
    """Whether the actor may view performance data."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_MANAGE)


def user_can_manage_performance(user) -> bool:
    """Whether the actor holds the master performance-management permission."""
    return _has(user, PERFORMANCE_MANAGE)


def user_can_view_metrics(user) -> bool:
    """Whether the actor may view performance metrics."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_MANAGE)


def user_can_manage_metrics(user) -> bool:
    """Whether the actor may create or update performance metrics."""
    return _has(user, PERFORMANCE_CREATE, PERFORMANCE_UPDATE, PERFORMANCE_MANAGE)


def user_can_view_kpis(user) -> bool:
    """Whether the actor may view KPIs."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_MANAGE)


def user_can_manage_kpis(user) -> bool:
    """Whether the actor may create or update KPIs."""
    return _has(user, PERFORMANCE_CREATE, PERFORMANCE_UPDATE, PERFORMANCE_MANAGE)


def user_can_view_benchmarks(user) -> bool:
    """Whether the actor may view benchmarks."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_BENCHMARK, PERFORMANCE_MANAGE)


def user_can_manage_benchmarks(user) -> bool:
    """Whether the actor may create or update benchmarks."""
    return _has(
        user,
        PERFORMANCE_CREATE,
        PERFORMANCE_UPDATE,
        PERFORMANCE_BENCHMARK,
        PERFORMANCE_MANAGE,
    )


def user_can_execute_benchmarks(user) -> bool:
    """Whether the actor may execute benchmarks."""
    return _has(user, PERFORMANCE_BENCHMARK, PERFORMANCE_MANAGE)


def user_can_view_optimizations(user) -> bool:
    """Whether the actor may view optimization records."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_OPTIMIZE, PERFORMANCE_MANAGE)


def user_can_manage_optimizations(user) -> bool:
    """Whether the actor may create or update optimizations."""
    return _has(
        user,
        PERFORMANCE_CREATE,
        PERFORMANCE_UPDATE,
        PERFORMANCE_OPTIMIZE,
        PERFORMANCE_MANAGE,
    )


def user_can_approve_optimizations(user) -> bool:
    """Whether the actor may approve/reject optimizations."""
    return _has(user, PERFORMANCE_MANAGE)


def user_can_view_cache(user) -> bool:
    """Whether the actor may view cache configurations and metrics."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_CONFIGURE, PERFORMANCE_MANAGE)


def user_can_manage_cache(user) -> bool:
    """Whether the actor may create or update cache configurations."""
    return _has(
        user,
        PERFORMANCE_CREATE,
        PERFORMANCE_UPDATE,
        PERFORMANCE_CONFIGURE,
        PERFORMANCE_MANAGE,
    )


def user_can_view_queues(user) -> bool:
    """Whether the actor may view queue monitoring."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_CONFIGURE, PERFORMANCE_MANAGE)


def user_can_manage_queues(user) -> bool:
    """Whether the actor may create or update queue configurations."""
    return _has(
        user,
        PERFORMANCE_CREATE,
        PERFORMANCE_UPDATE,
        PERFORMANCE_CONFIGURE,
        PERFORMANCE_MANAGE,
    )


def user_can_view_database(user) -> bool:
    """Whether the actor may view database monitoring."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_CONFIGURE, PERFORMANCE_MANAGE)


def user_can_manage_database(user) -> bool:
    """Whether the actor may create or update database monitoring."""
    return _has(
        user,
        PERFORMANCE_CREATE,
        PERFORMANCE_UPDATE,
        PERFORMANCE_CONFIGURE,
        PERFORMANCE_MANAGE,
    )


def user_can_view_alerts(user) -> bool:
    """Whether the actor may view performance alerts."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_ALERT, PERFORMANCE_MANAGE)


def user_can_manage_alerts(user) -> bool:
    """Whether the actor may acknowledge/resolve alerts."""
    return _has(user, PERFORMANCE_ALERT, PERFORMANCE_MANAGE)


def user_can_view_reports(user) -> bool:
    """Whether the actor may view performance reports."""
    return _has(user, PERFORMANCE_VIEW, PERFORMANCE_REPORT, PERFORMANCE_MANAGE)


def user_can_generate_reports(user) -> bool:
    """Whether the actor may generate performance reports."""
    return _has(user, PERFORMANCE_REPORT, PERFORMANCE_MANAGE)


def user_can_export_performance(user) -> bool:
    """Whether the actor may export performance data."""
    return _has(user, PERFORMANCE_EXPORT, PERFORMANCE_MANAGE)


def user_can_configure_performance(user) -> bool:
    """Whether the actor may configure performance settings."""
    return _has(user, PERFORMANCE_CONFIGURE, PERFORMANCE_MANAGE)


def get_accessible_metrics(user):
    """Metrics the actor may view (module-level scope)."""
    from apps.performance.models import PerformanceMetric

    if not user_can_view_metrics(user):
        return PerformanceMetric.objects.none()
    return PerformanceMetric.objects.all()


def get_accessible_kpis(user):
    """KPIs the actor may view."""
    from apps.performance.models import PerformanceKPI

    if not user_can_view_kpis(user):
        return PerformanceKPI.objects.none()
    return PerformanceKPI.objects.filter(is_active=True)


def get_accessible_benchmarks(user):
    """Benchmarks the actor may view."""
    from apps.performance.models import Benchmark

    if not user_can_view_benchmarks(user):
        return Benchmark.objects.none()
    return Benchmark.objects.all()


def get_accessible_optimizations(user):
    """Optimizations the actor may view."""
    from apps.performance.models import OptimizationRecord

    if not user_can_view_optimizations(user):
        return OptimizationRecord.objects.none()
    return OptimizationRecord.objects.all()


class PerformancePermissionMixin:
    """Mixin to add performance permission checks to class-based views."""

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        from django.core.exceptions import PermissionDenied

        if not user_can_access_performance(request.user):
            raise PermissionDenied(
                "You do not have permission to access the performance module."
            )
        return super().dispatch(request, *args, **kwargs)
