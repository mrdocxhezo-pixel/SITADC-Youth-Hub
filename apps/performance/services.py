"""Services for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

import logging
import time
from datetime import timedelta
from typing import Any

from django.db import transaction
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone

from apps.core.services import BaseService
from apps.performance.constants import (
    KPI_TARGETS,
    AlertSeverity,
    BenchmarkStatus,
    MetricUnit,
    OptimizationStatus,
    PerformanceComponent,
)
from apps.performance.exceptions import (
    BenchmarkExecutionError,
    InvalidConfigurationError,
)
from apps.references.constants import ReferenceModules
from apps.references.services import ReferenceNumberService

logger = logging.getLogger(__name__)


def _generate_reference(user: Any, scheme_code: str) -> str:
    """Generate a reference number using the centralized service."""
    try:
        generated = ReferenceNumberService(user=user).execute(
            module=ReferenceModules.PERFORMANCE,
            scheme_code=scheme_code,
            notes=f"Performance module {scheme_code} reference.",
        )
        return generated.reference_number
    except Exception:  # pragma: no cover - fallback only
        return f"{scheme_code.upper()}-{timezone.now().year}-{int(time.time() * 1000)}"


class PerformanceMetricService(BaseService):
    """Service for recording and querying performance metrics."""

    def record_metric(
        self,
        *,
        actor: Any,
        component: str,
        metric_name: str,
        value: float,
        unit: str = MetricUnit.MILLISECONDS,
        module: str = "",
        environment: str = "production",
        request_path: str = "",
        user_agent: str = "",
        query_params: dict | None = None,
        tags: dict | None = None,
        notes: str = "",
    ) -> Any:
        """Record a single performance metric."""
        from apps.performance.models import PerformanceMetric

        metric = PerformanceMetric(
            component=component,
            module=module,
            metric_name=metric_name,
            value=value,
            unit=unit,
            environment=environment,
            request_path=request_path,
            user_agent=user_agent,
            query_params=query_params or {},
            tags=tags or {},
            notes=notes,
            created_by=actor,
        )
        metric.save()
        logger.info(
            "Recorded metric %s for %s: %s %s", metric_name, component, value, unit
        )
        return metric

    def record_batch(self, *, actor: Any, metrics: list[dict[str, Any]]) -> list[Any]:
        """Record multiple metrics in a single transaction."""
        from apps.performance.models import PerformanceMetric

        with transaction.atomic():
            created = []
            for m in metrics:
                metric = PerformanceMetric(
                    component=m["component"],
                    module=m.get("module", ""),
                    metric_name=m["metric_name"],
                    value=m["value"],
                    unit=m.get("unit", MetricUnit.MILLISECONDS),
                    environment=m.get("environment", "production"),
                    request_path=m.get("request_path", ""),
                    user_agent=m.get("user_agent", ""),
                    query_params=m.get("query_params", {}),
                    tags=m.get("tags", {}),
                    notes=m.get("notes", ""),
                    created_by=actor,
                )
                created.append(metric)
            PerformanceMetric.objects.bulk_create(created)
            logger.info("Recorded batch of %d metrics", len(created))
            return created

    def get_metrics_summary(
        self,
        *,
        component: str | None = None,
        module: str | None = None,
        metric_name: str | None = None,
        hours: int = 24,
        aggregation: str = "avg",
    ) -> dict:
        """Get aggregated metrics summary."""
        from apps.performance.models import PerformanceMetric

        since = timezone.now() - timedelta(hours=hours)
        qs = PerformanceMetric.objects.filter(created_at__gte=since)

        if component:
            qs = qs.filter(component=component)
        if module:
            qs = qs.filter(module=module)
        if metric_name:
            qs = qs.filter(metric_name=metric_name)

        agg_func = {
            "avg": Avg("value"),
            "min": Min("value"),
            "max": Max("value"),
            "count": Count("id"),
        }.get(aggregation, Avg("value"))

        return qs.aggregate(
            value=agg_func,
            count=Count("id"),
        )


class PerformanceKPIService(BaseService):
    """Service for managing and evaluating KPIs."""

    def create_kpi(
        self,
        *,
        actor: Any,
        name: str,
        component: str,
        metric_name: str,
        target_value: float,
        target_unit: str,
        description: str = "",
        threshold_warning: float | None = None,
        threshold_critical: float | None = None,
        direction: str = "lower_is_better",
        aggregation_period: str = "daily",
        aggregation_method: str = "avg",
    ) -> Any:
        """Create a new KPI definition."""
        from apps.performance.models import PerformanceKPI

        if PerformanceKPI.objects.filter(name=name).exists():
            raise InvalidConfigurationError(f"KPI with name '{name}' already exists.")

        kpi = PerformanceKPI(
            name=name,
            component=component,
            metric_name=metric_name,
            description=description,
            target_value=target_value,
            target_unit=target_unit,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            direction=direction,
            aggregation_period=aggregation_period,
            aggregation_method=aggregation_method,
            created_by=actor,
            updated_by=actor,
        )
        kpi.save()
        logger.info("Created KPI %s for %s", name, component)
        return kpi

    def seed_default_kpis(self, actor: Any) -> list[Any]:
        """Seed default KPIs from KPI_TARGETS constants."""
        from apps.performance.models import PerformanceKPI

        created = []
        for metric_key, config in KPI_TARGETS.items():
            if not PerformanceKPI.objects.filter(name=metric_key).exists():
                kpi = PerformanceKPI(
                    name=metric_key,
                    component=PerformanceComponent.DASHBOARD,
                    metric_name=metric_key,
                    description=config.get("description", ""),
                    target_value=config["target"],
                    target_unit=config["unit"],
                    direction=(
                        "lower_is_better"
                        if config["unit"] != MetricUnit.PERCENTAGE
                        else "higher_is_better"
                    ),
                    created_by=actor,
                    updated_by=actor,
                )
                created.append(kpi)
        if created:
            PerformanceKPI.objects.bulk_create(created)
            logger.info("Seeded %d default KPIs", len(created))
        return created

    def evaluate_all_kpis(self, *, hours: int = 24) -> list[dict]:
        """Evaluate all active KPIs against recent metrics."""
        from apps.performance.models import PerformanceKPI, PerformanceMetric

        since = timezone.now() - timedelta(hours=hours)
        results = []

        for kpi in PerformanceKPI.objects.filter(is_active=True):
            qs = PerformanceMetric.objects.filter(
                component=kpi.component,
                metric_name=kpi.metric_name,
                created_at__gte=since,
            )

            if not qs.exists():
                results.append(
                    {
                        "kpi": kpi,
                        "status": "no_data",
                        "value": None,
                        "evaluation": None,
                    }
                )
                continue

            # Apply aggregation
            if kpi.aggregation_method == "avg":
                value = qs.aggregate(avg=Avg("value"))["avg"]
            elif kpi.aggregation_method == "min":
                value = qs.aggregate(min=Min("value"))["min"]
            elif kpi.aggregation_method == "max":
                value = qs.aggregate(max=Max("value"))["max"]
            else:
                value = qs.aggregate(avg=Avg("value"))["avg"]

            if value is not None:
                evaluation = kpi.evaluate_current_value(float(value))
                results.append(
                    {
                        "kpi": kpi,
                        "status": evaluation["status"],
                        "value": float(value),
                        "evaluation": evaluation,
                    }
                )
            else:
                results.append(
                    {
                        "kpi": kpi,
                        "status": "no_data",
                        "value": None,
                        "evaluation": None,
                    }
                )

        return results


class BenchmarkService(BaseService):
    """Service for managing and executing benchmarks."""

    def create_benchmark(
        self,
        *,
        actor: Any,
        name: str,
        component: str,
        test_scenario: str,
        configuration: dict,
        target_metrics: dict,
        environment: str = "staging",
        description: str = "",
    ) -> Any:
        """Create a new benchmark definition."""
        from apps.performance.models import Benchmark

        benchmark = Benchmark(
            name=name,
            component=component,
            test_scenario=test_scenario,
            configuration=configuration,
            target_metrics=target_metrics,
            environment=environment,
            description=description,
            created_by=actor,
            updated_by=actor,
        )
        benchmark.save()
        logger.info("Created benchmark %s for %s", name, component)
        return benchmark

    def execute_benchmark(self, *, actor: Any, benchmark_id: str) -> Any:
        """Execute a benchmark and record results."""
        from apps.performance.models import Benchmark, BenchmarkRun

        benchmark = Benchmark.objects.get(pk=benchmark_id)
        benchmark.status = BenchmarkStatus.RUNNING
        benchmark.started_at = timezone.now()
        benchmark.save()

        run_number = BenchmarkRun.objects.filter(benchmark=benchmark).count() + 1
        run = BenchmarkRun.objects.create(
            benchmark=benchmark,
            run_number=run_number,
            started_at=timezone.now(),
            status=BenchmarkStatus.RUNNING,
        )

        try:
            # Execute the benchmark scenario
            results = self._run_benchmark_scenario(benchmark)

            run.completed_at = timezone.now()
            run.results = results
            run.status = BenchmarkStatus.COMPLETED
            run.save()

            benchmark.completed_at = timezone.now()
            benchmark.results = results
            benchmark.passed = self._evaluate_benchmark_results(
                benchmark.target_metrics, results
            )
            benchmark.status = BenchmarkStatus.COMPLETED
            benchmark.save()

            logger.info("Benchmark %s completed successfully", benchmark.name)
            return run

        except Exception as e:
            run.completed_at = timezone.now()
            run.status = BenchmarkStatus.FAILED
            run.error_message = str(e)
            run.save()

            benchmark.completed_at = timezone.now()
            benchmark.status = BenchmarkStatus.FAILED
            benchmark.save()

            logger.error("Benchmark %s failed: %s", benchmark.name, e)
            raise BenchmarkExecutionError(f"Benchmark execution failed: {e}") from e

    def _run_benchmark_scenario(self, benchmark: Any) -> dict:
        """Run the actual benchmark scenario. Override for specific implementations."""
        # This is a placeholder - actual implementation would run the scenario
        # For now, return simulated results
        return {
            "duration_ms": 1500,
            "requests_per_second": 100,
            "error_rate": 0.01,
            "p95_latency_ms": 200,
            "p99_latency_ms": 500,
        }

    def _evaluate_benchmark_results(
        self, target_metrics: dict, actual_results: dict
    ) -> bool:
        """Evaluate if benchmark results meet targets."""
        for metric, target in target_metrics.items():
            if metric in actual_results:
                actual = actual_results[metric]
                if isinstance(target, dict):
                    target_value = target.get("value", target)
                    direction = target.get("direction", "lower_is_better")
                else:
                    target_value = target
                    direction = "lower_is_better"

                if (
                    direction == "lower_is_better"
                    and actual > target_value
                    or direction == "higher_is_better"
                    and actual < target_value
                ):
                    return False
        return True


class OptimizationService(BaseService):
    """Service for managing optimization records."""

    def create_optimization(
        self,
        *,
        actor: Any,
        title: str,
        optimization_type: str,
        component: str,
        description: str,
        rationale: str,
        baseline_metrics: dict,
        target_metrics: dict,
        module: str = "",
        planned_start: Any = None,
        risk_level: str = "LOW",
        rollback_plan: str = "",
        benchmark_id: str | None = None,
    ) -> Any:
        """Create a new optimization record."""
        from apps.performance.models import Benchmark, OptimizationRecord

        optimization = OptimizationRecord(
            title=title,
            optimization_type=optimization_type,
            component=component,
            module=module,
            description=description,
            rationale=rationale,
            baseline_metrics=baseline_metrics,
            target_metrics=target_metrics,
            risk_level=risk_level,
            rollback_plan=rollback_plan,
            planned_start=planned_start,
            created_by=actor,
            updated_by=actor,
        )

        if benchmark_id:
            try:
                optimization.benchmark = Benchmark.objects.get(pk=benchmark_id)
            except Benchmark.DoesNotExist:
                pass

        optimization.save()
        logger.info("Created optimization record %s", title)
        return optimization

    def start_optimization(self, *, actor: Any, optimization_id: str) -> Any:
        """Mark an optimization as in progress."""
        from apps.performance.models import OptimizationRecord

        optimization = OptimizationRecord.objects.get(pk=optimization_id)
        if optimization.status not in [
            OptimizationStatus.IDENTIFIED,
            OptimizationStatus.PLANNED,
        ]:
            raise InvalidConfigurationError(
                f"Cannot start optimization in status {optimization.status}"
            )

        optimization.status = OptimizationStatus.IN_PROGRESS
        optimization.actual_start = timezone.now()
        optimization.updated_by = actor
        optimization.save()
        logger.info("Started optimization %s", optimization.title)
        return optimization

    def complete_optimization(
        self, *, actor: Any, optimization_id: str, actual_metrics: dict
    ) -> Any:
        """Complete an optimization and record actual metrics."""
        from apps.performance.models import OptimizationRecord

        optimization = OptimizationRecord.objects.get(pk=optimization_id)
        optimization.status = OptimizationStatus.TESTING
        optimization.actual_metrics = actual_metrics
        optimization.updated_by = actor
        optimization.save()

        # Calculate improvement
        improvement = self._calculate_improvement(
            optimization.baseline_metrics, actual_metrics
        )
        optimization.improvement_percentage = improvement
        optimization.completed_at = timezone.now()
        optimization.save()
        logger.info(
            "Completed optimization %s with %s%% improvement",
            optimization.title,
            improvement,
        )
        return optimization

    def verify_optimization(
        self, *, actor: Any, optimization_id: str, verified: bool = True
    ) -> Any:
        """Verify (approve/reject) an optimization."""
        from apps.performance.models import OptimizationRecord

        optimization = OptimizationRecord.objects.get(pk=optimization_id)
        if verified:
            optimization.status = OptimizationStatus.VERIFIED
        else:
            optimization.status = OptimizationStatus.REJECTED
        optimization.approved_by = actor
        optimization.approved_at = timezone.now()
        optimization.save()
        logger.info(
            "Optimization %s %s",
            optimization.title,
            "verified" if verified else "rejected",
        )
        return optimization

    def _calculate_improvement(self, baseline: dict, actual: dict) -> float | None:
        """Calculate improvement percentage between baseline and actual metrics."""
        if not baseline or not actual:
            return None

        improvements = []
        for key, base_value in baseline.items():
            if key in actual and base_value != 0:
                actual_value = actual[key]
                # Assuming lower is better for most metrics
                pct = ((base_value - actual_value) / base_value) * 100
                improvements.append(pct)

        if not improvements:
            return None

        return round(sum(improvements) / len(improvements), 2)


class CacheMonitoringService(BaseService):
    """Service for cache monitoring and metrics collection."""

    def create_cache_config(
        self,
        *,
        actor: Any,
        name: str,
        backend: str,
        location: str = "",
        timeout: int = 300,
        key_prefix: str = "sitadc_perf",
        max_entries: int = 10000,
        options: dict | None = None,
        scope: str = "",
        description: str = "",
        monitor_hit_ratio: bool = True,
        alert_threshold_hit_ratio: float = 80.0,
    ) -> Any:
        """Create a cache configuration."""
        from apps.performance.models import CacheConfiguration

        config = CacheConfiguration(
            name=name,
            backend=backend,
            location=location,
            timeout=timeout,
            key_prefix=key_prefix,
            max_entries=max_entries,
            options=options or {},
            scope=scope,
            description=description,
            monitor_hit_ratio=monitor_hit_ratio,
            alert_threshold_hit_ratio=alert_threshold_hit_ratio,
            created_by=actor,
            updated_by=actor,
        )
        config.save()
        logger.info("Created cache configuration %s", name)
        return config

    def record_cache_metrics(
        self,
        *,
        cache_config_id: str,
        total_requests: int,
        hits: int,
        misses: int,
        memory_usage_bytes: int = 0,
        entry_count: int = 0,
        eviction_count: int = 0,
        error_count: int = 0,
    ) -> Any:
        """Record cache metrics."""
        from apps.performance.models import CacheConfiguration, CacheMetrics

        cache_config = CacheConfiguration.objects.get(pk=cache_config_id)
        hit_ratio = 0.0
        if total_requests > 0:
            hit_ratio = round(hits / total_requests * 100, 2)

        metrics = CacheMetrics(
            cache_config=cache_config,
            total_requests=total_requests,
            hits=hits,
            misses=misses,
            hit_ratio=hit_ratio,
            memory_usage_bytes=memory_usage_bytes,
            entry_count=entry_count,
            eviction_count=eviction_count,
            error_count=error_count,
        )
        metrics.save()

        # Check for alerts
        if cache_config.monitor_hit_ratio and hit_ratio < float(
            cache_config.alert_threshold_hit_ratio
        ):
            self._create_cache_alert(cache_config, hit_ratio)

        logger.debug(
            "Recorded cache metrics for %s: hit_ratio=%.2f%%",
            cache_config.name,
            hit_ratio,
        )
        return metrics

    def _create_cache_alert(self, cache_config: Any, hit_ratio: float) -> None:
        """Create a performance alert for low cache hit ratio."""
        from apps.performance.models import PerformanceAlert

        alert = PerformanceAlert(
            title=f"Low cache hit ratio: {cache_config.name}",
            severity=AlertSeverity.WARNING,
            component=PerformanceComponent.CACHING,
            metric_name="hit_ratio",
            message=f"Cache hit ratio ({hit_ratio:.2f}%) is below threshold ({cache_config.alert_threshold_hit_ratio}%)",
            current_value=hit_ratio,
            threshold_value=cache_config.alert_threshold_hit_ratio,
            cache_config=cache_config,
        )
        alert.save()


class QueueMonitoringService(BaseService):
    """Service for queue monitoring and metrics collection."""

    def create_queue_monitoring(
        self,
        *,
        actor: Any,
        name: str,
        backend: str,
        queue_name: str,
        connection_config: dict | None = None,
        monitor_depth: bool = True,
        monitor_processing_time: bool = True,
        monitor_failure_rate: bool = True,
        alert_depth_threshold: int = 1000,
        alert_processing_time_threshold: int = 60,
        alert_failure_rate_threshold: float = 5.0,
    ) -> Any:
        """Create a queue monitoring configuration."""
        from apps.performance.models import QueueMonitoring

        queue = QueueMonitoring(
            name=name,
            backend=backend,
            queue_name=queue_name,
            connection_config=connection_config or {},
            monitor_depth=monitor_depth,
            monitor_processing_time=monitor_processing_time,
            monitor_failure_rate=monitor_failure_rate,
            alert_depth_threshold=alert_depth_threshold,
            alert_processing_time_threshold=alert_processing_time_threshold,
            alert_failure_rate_threshold=alert_failure_rate_threshold,
            created_by=actor,
            updated_by=actor,
        )
        queue.save()
        logger.info("Created queue monitoring %s", name)
        return queue

    def record_queue_metrics(
        self,
        *,
        queue_id: str,
        depth: int = 0,
        pending: int = 0,
        processing: int = 0,
        completed: int = 0,
        failed: int = 0,
        avg_processing_time: float = 0.0,
        max_processing_time: float = 0.0,
        throughput_per_minute: float = 0.0,
    ) -> Any:
        """Record queue metrics."""
        from apps.performance.models import QueueMetrics, QueueMonitoring

        queue = QueueMonitoring.objects.get(pk=queue_id)

        metrics = QueueMetrics(
            queue=queue,
            depth=depth,
            pending=pending,
            processing=processing,
            completed=completed,
            failed=failed,
            avg_processing_time=avg_processing_time,
            max_processing_time=max_processing_time,
            throughput_per_minute=throughput_per_minute,
        )
        metrics.save()

        # Check for alerts
        self._check_queue_alerts(queue, metrics)

        logger.debug("Recorded queue metrics for %s: depth=%d", queue.name, depth)
        return metrics

    def _check_queue_alerts(self, queue: Any, metrics: Any) -> None:
        """Check queue metrics and create alerts if needed."""
        from apps.performance.models import PerformanceAlert

        if queue.monitor_depth and metrics.depth >= queue.alert_depth_threshold:
            PerformanceAlert.objects.create(
                title=f"Queue depth alert: {queue.name}",
                severity=AlertSeverity.WARNING,
                component=PerformanceComponent.QUEUES,
                metric_name="depth",
                message=f"Queue depth ({metrics.depth}) exceeds threshold ({queue.alert_depth_threshold})",
                current_value=metrics.depth,
                threshold_value=queue.alert_depth_threshold,
                queue=queue,
            )

        if (
            queue.monitor_processing_time
            and metrics.avg_processing_time >= queue.alert_processing_time_threshold
        ):
            PerformanceAlert.objects.create(
                title=f"Queue processing time alert: {queue.name}",
                severity=AlertSeverity.WARNING,
                component=PerformanceComponent.QUEUES,
                metric_name="avg_processing_time",
                message=f"Average processing time ({metrics.avg_processing_time}s) exceeds threshold ({queue.alert_processing_time_threshold}s)",
                current_value=metrics.avg_processing_time,
                threshold_value=queue.alert_processing_time_threshold,
                queue=queue,
            )


class DatabaseMonitoringService(BaseService):
    """Service for database monitoring and metrics collection."""

    def create_database_monitoring(
        self,
        *,
        actor: Any,
        name: str,
        alias: str = "default",
        monitor_query_performance: bool = True,
        monitor_connections: bool = True,
        monitor_table_sizes: bool = True,
        monitor_index_usage: bool = True,
        slow_query_threshold_ms: int = 1000,
        max_connections: int = 100,
        alert_connection_usage_threshold: float = 80.0,
    ) -> Any:
        """Create a database monitoring configuration."""
        from apps.performance.models import DatabaseMonitoring

        db = DatabaseMonitoring(
            name=name,
            alias=alias,
            monitor_query_performance=monitor_query_performance,
            monitor_connections=monitor_connections,
            monitor_table_sizes=monitor_table_sizes,
            monitor_index_usage=monitor_index_usage,
            slow_query_threshold_ms=slow_query_threshold_ms,
            max_connections=max_connections,
            alert_connection_usage_threshold=alert_connection_usage_threshold,
            created_by=actor,
            updated_by=actor,
        )
        db.save()
        logger.info("Created database monitoring %s", name)
        return db

    def record_database_metrics(
        self,
        *,
        database_id: str,
        active_connections: int = 0,
        idle_connections: int = 0,
        max_used_connections: int = 0,
        total_queries: int = 0,
        slow_queries: int = 0,
        avg_query_time: float = 0.0,
        cache_hit_ratio: float = 0.0,
        database_size_bytes: int = 0,
        index_size_bytes: int = 0,
    ) -> Any:
        """Record database metrics."""
        from apps.performance.models import DatabaseMetrics, DatabaseMonitoring

        db = DatabaseMonitoring.objects.get(pk=database_id)

        metrics = DatabaseMetrics(
            database=db,
            active_connections=active_connections,
            idle_connections=idle_connections,
            max_used_connections=max_used_connections,
            total_queries=total_queries,
            slow_queries=slow_queries,
            avg_query_time=avg_query_time,
            cache_hit_ratio=cache_hit_ratio,
            database_size_bytes=database_size_bytes,
            index_size_bytes=index_size_bytes,
        )
        metrics.save()

        # Check for alerts
        self._check_database_alerts(db, metrics)

        logger.debug("Recorded database metrics for %s", db.name)
        return metrics

    def _check_database_alerts(self, db: Any, metrics: Any) -> None:
        """Check database metrics and create alerts if needed."""
        from apps.performance.models import PerformanceAlert

        if (
            db.monitor_connections
            and db.max_connections > 0
            and (metrics.active_connections / db.max_connections * 100)
            >= float(db.alert_connection_usage_threshold)
        ):
            usage_pct = metrics.active_connections / db.max_connections * 100
            PerformanceAlert.objects.create(
                title=f"Database connection usage alert: {db.name}",
                severity=AlertSeverity.WARNING,
                component=PerformanceComponent.DATABASE,
                metric_name="connection_usage",
                message=f"Connection usage ({usage_pct:.1f}%) exceeds threshold ({db.alert_connection_usage_threshold}%)",
                current_value=usage_pct,
                threshold_value=db.alert_connection_usage_threshold,
                database=db,
            )


class PerformanceAlertService(BaseService):
    """Service for managing performance alerts."""

    def acknowledge_alert(self, *, actor: Any, alert_id: str) -> Any:
        """Acknowledge a performance alert."""
        from apps.performance.models import PerformanceAlert

        alert = PerformanceAlert.objects.get(pk=alert_id)
        alert.is_acknowledged = True
        alert.acknowledged_by = actor
        alert.acknowledged_at = timezone.now()
        alert.save()
        logger.info("Alert %s acknowledged by %s", alert.title, actor)
        return alert

    def resolve_alert(self, *, actor: Any, alert_id: str) -> Any:
        """Resolve a performance alert."""
        from apps.performance.models import PerformanceAlert

        alert = PerformanceAlert.objects.get(pk=alert_id)
        alert.resolved_at = timezone.now()
        alert.save()
        logger.info("Alert %s resolved by %s", alert.title, actor)
        return alert

    def get_unacknowledged_alerts(self, *, severity: str | None = None) -> Any:
        """Get unacknowledged alerts, optionally filtered by severity."""
        from apps.performance.models import PerformanceAlert

        qs = PerformanceAlert.objects.filter(
            is_acknowledged=False, resolved_at__isnull=True
        )
        if severity:
            qs = qs.filter(severity=severity)
        return qs.order_by("-severity", "-created_at")


class PerformanceReportService(BaseService):
    """Service for generating performance reports."""

    def generate_report(
        self,
        *,
        actor: Any,
        title: str,
        period_start: Any,
        period_end: Any,
        format: str = "HTML",
    ) -> Any:
        """Generate a performance report for the given period."""
        from apps.performance.models import (
            PerformanceAlert,
            PerformanceMetric,
            PerformanceReport,
        )

        # Collect metrics
        metrics_qs = PerformanceMetric.objects.filter(
            created_at__gte=period_start, created_at__lte=period_end
        )

        # Aggregate by component
        metrics_summary = {}
        for metric in metrics_qs:
            key = f"{metric.component}.{metric.metric_name}"
            if key not in metrics_summary:
                metrics_summary[key] = {"values": [], "unit": metric.unit}
            metrics_summary[key]["values"].append(float(metric.value))

        # Calculate statistics
        metrics_stats = {}
        for key, data in metrics_summary.items():
            values = data["values"]
            if values:
                metrics_stats[key] = {
                    "count": len(values),
                    "avg": round(sum(values) / len(values), 2),
                    "min": round(min(values), 2),
                    "max": round(max(values), 2),
                    "unit": data["unit"],
                }

        # Evaluate KPIs
        kpi_service = PerformanceKPIService()
        kpi_results = kpi_service.evaluate_all_kpis(
            hours=int((period_end - period_start).total_seconds() / 3600)
        )
        kpi_evaluations = {r["kpi"].name: r for r in kpi_results}

        # Get alerts
        alerts_qs = PerformanceAlert.objects.filter(
            created_at__gte=period_start, created_at__lte=period_end
        )
        alerts_data = [
            {
                "title": a.title,
                "severity": a.severity,
                "component": a.component,
                "created_at": a.created_at.isoformat(),
                "is_acknowledged": a.is_acknowledged,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            }
            for a in alerts_qs
        ]

        # Create report
        report = PerformanceReport(
            title=title,
            period_start=period_start,
            period_end=period_end,
            summary={
                "total_metrics": metrics_qs.count(),
                "components_covered": list(
                    metrics_qs.values_list("component", flat=True).distinct()
                ),
                "alert_count": alerts_qs.count(),
                "critical_alerts": alerts_qs.filter(
                    severity=AlertSeverity.CRITICAL
                ).count(),
            },
            metrics=metrics_stats,
            kpi_evaluations=kpi_evaluations,
            alerts=alerts_data,
            format=format,
            created_by=actor,
        )
        report.save()

        logger.info("Generated performance report %s", title)
        return report
