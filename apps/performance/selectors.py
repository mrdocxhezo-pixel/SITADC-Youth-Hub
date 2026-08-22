"""Selectors for Performance Optimization & Scalability (Phase 34).

All selectors are fail-closed: a user without the relevant ``performance.*``
permission receives an empty queryset rather than data.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.performance.models import (
    Benchmark,
    CacheConfiguration,
    CacheMetrics,
    DatabaseMetrics,
    DatabaseMonitoring,
    OptimizationRecord,
    PerformanceAlert,
    PerformanceKPI,
    PerformanceMetric,
    PerformanceReport,
    QueueMetrics,
    QueueMonitoring,
)
from apps.performance.permissions import (
    user_can_view_benchmarks,
    user_can_view_cache,
    user_can_view_database,
    user_can_view_kpis,
    user_can_view_metrics,
    user_can_view_optimizations,
    user_can_view_performance,
    user_can_view_queues,
    user_can_view_reports,
)

User = get_user_model()


def get_accessible_metrics(user: User) -> QuerySet[PerformanceMetric]:
    """Performance metrics the user may view (empty queryset when denied)."""
    if not user_can_view_metrics(user):
        return PerformanceMetric.objects.none()
    return PerformanceMetric.objects.all()


def get_accessible_kpis(user: User) -> QuerySet[PerformanceKPI]:
    """KPIs the user may view (empty queryset when denied)."""
    if not user_can_view_kpis(user):
        return PerformanceKPI.objects.none()
    return PerformanceKPI.objects.filter(is_active=True)


def get_accessible_benchmarks(user: User) -> QuerySet[Benchmark]:
    """Benchmarks the user may view (empty queryset when denied)."""
    if not user_can_view_benchmarks(user):
        return Benchmark.objects.none()
    return Benchmark.objects.all()


def get_accessible_optimizations(user: User) -> QuerySet[OptimizationRecord]:
    """Optimizations the user may view (empty queryset when denied)."""
    if not user_can_view_optimizations(user):
        return OptimizationRecord.objects.none()
    return OptimizationRecord.objects.all()


def get_accessible_cache_configs(user: User) -> QuerySet[CacheConfiguration]:
    """Cache configurations the user may view."""
    if not user_can_view_cache(user):
        return CacheConfiguration.objects.none()
    return CacheConfiguration.objects.filter(is_active=True)


def get_accessible_cache_metrics(user: User) -> QuerySet[CacheMetrics]:
    """Cache metrics the user may view."""
    if not user_can_view_cache(user):
        return CacheMetrics.objects.none()
    return CacheMetrics.objects.all()


def get_accessible_queues(user: User) -> QuerySet[QueueMonitoring]:
    """Queue monitoring configurations the user may view."""
    if not user_can_view_queues(user):
        return QueueMonitoring.objects.none()
    return QueueMonitoring.objects.filter(is_active=True)


def get_accessible_queue_metrics(user: User) -> QuerySet[QueueMetrics]:
    """Queue metrics the user may view."""
    if not user_can_view_queues(user):
        return QueueMetrics.objects.none()
    return QueueMetrics.objects.all()


def get_accessible_databases(user: User) -> QuerySet[DatabaseMonitoring]:
    """Database monitoring configurations the user may view."""
    if not user_can_view_database(user):
        return DatabaseMonitoring.objects.none()
    return DatabaseMonitoring.objects.filter(is_active=True)


def get_accessible_database_metrics(user: User) -> QuerySet[DatabaseMetrics]:
    """Database metrics the user may view."""
    if not user_can_view_database(user):
        return DatabaseMetrics.objects.none()
    return DatabaseMetrics.objects.all()


def get_accessible_alerts(user: User) -> QuerySet[PerformanceAlert]:
    """Performance alerts the user may view."""
    if not user_can_view_performance(user):
        return PerformanceAlert.objects.none()
    return PerformanceAlert.objects.all()


def get_accessible_reports(user: User) -> QuerySet[PerformanceReport]:
    """Performance reports the user may view."""
    if not user_can_view_reports(user):
        return PerformanceReport.objects.none()
    return PerformanceReport.objects.all()


def get_unacknowledged_alerts(user: User) -> QuerySet[PerformanceAlert]:
    """Unacknowledged alerts the user may view."""
    if not user_can_view_performance(user):
        return PerformanceAlert.objects.none()
    return PerformanceAlert.objects.filter(
        is_acknowledged=False, resolved_at__isnull=True
    )


def get_critical_alerts(user: User) -> QuerySet[PerformanceAlert]:
    """Critical alerts the user may view."""
    if not user_can_view_performance(user):
        return PerformanceAlert.objects.none()
    from apps.performance.constants import AlertSeverity

    return PerformanceAlert.objects.filter(severity=AlertSeverity.CRITICAL)


def get_recent_metrics(
    user: User, *, component: str | None = None, hours: int = 24, limit: int = 100
) -> QuerySet[PerformanceMetric]:
    """Recent performance metrics."""
    from django.utils import timezone

    qs = get_accessible_metrics(user).filter(
        created_at__gte=timezone.now() - timezone.timedelta(hours=hours)
    )
    if component:
        qs = qs.filter(component=component)
    return qs.order_by("-created_at")[:limit]


def get_kpi_status(user: User) -> dict:
    """Get status of all KPIs for the user."""
    from apps.performance.services import PerformanceKPIService

    service = PerformanceKPIService()
    results = service.evaluate_all_kpis(hours=24)

    return {
        "healthy": [r for r in results if r["status"] == "healthy"],
        "warning": [r for r in results if r["status"] == "warning"],
        "critical": [r for r in results if r["status"] == "critical"],
        "no_data": [r for r in results if r["status"] == "no_data"],
    }


def get_benchmark_summary(user: User) -> dict:
    """Get benchmark summary for the user."""
    from apps.performance.constants import BenchmarkStatus

    benchmarks = get_accessible_benchmarks(user)
    return {
        "total": benchmarks.count(),
        "pending": benchmarks.filter(status=BenchmarkStatus.PENDING).count(),
        "running": benchmarks.filter(status=BenchmarkStatus.RUNNING).count(),
        "completed": benchmarks.filter(status=BenchmarkStatus.COMPLETED).count(),
        "failed": benchmarks.filter(status=BenchmarkStatus.FAILED).count(),
        "passed": benchmarks.filter(passed=True).count(),
    }


def get_optimization_summary(user: User) -> dict:
    """Get optimization summary for the user."""
    from apps.performance.constants import OptimizationStatus

    optimizations = get_accessible_optimizations(user)
    return {
        "total": optimizations.count(),
        "identified": optimizations.filter(
            status=OptimizationStatus.IDENTIFIED
        ).count(),
        "planned": optimizations.filter(status=OptimizationStatus.PLANNED).count(),
        "in_progress": optimizations.filter(
            status=OptimizationStatus.IN_PROGRESS
        ).count(),
        "testing": optimizations.filter(status=OptimizationStatus.TESTING).count(),
        "deployed": optimizations.filter(status=OptimizationStatus.DEPLOYED).count(),
        "verified": optimizations.filter(status=OptimizationStatus.VERIFIED).count(),
        "rejected": optimizations.filter(status=OptimizationStatus.REJECTED).count(),
    }


def get_cache_summary(user: User) -> dict:
    """Get cache summary for the user."""
    caches = get_accessible_cache_configs(user)
    return {
        "total": caches.count(),
        "active": caches.filter(is_active=True).count(),
        "backends": {
            backend: caches.filter(backend=backend).count()
            for backend in [
                "LOCAL_MEMORY",
                "REDIS",
                "DATABASE",
                "FILESYSTEM",
            ]
        },
    }


def get_queue_summary(user: User) -> dict:
    """Get queue summary for the user."""
    queues = get_accessible_queues(user)
    return {
        "total": queues.count(),
        "active": queues.filter(is_active=True).count(),
        "backends": {
            backend: queues.filter(backend=backend).count()
            for backend in ["DATABASE", "REDIS", "RABBITMQ", "AMAZON_SQS"]
        },
    }


def get_database_summary(user: User) -> dict:
    """Get database summary for the user."""
    databases = get_accessible_databases(user)
    return {
        "total": databases.count(),
        "active": databases.filter(is_active=True).count(),
    }
