"""Models for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import (
    CreatedByModel,
    IsActiveModel,
    TimeStampedModel,
    UpdatedByModel,
    UUIDModel,
)
from apps.performance.constants import (
    AlertSeverity,
    BenchmarkStatus,
    CacheBackend,
    MetricUnit,
    OptimizationStatus,
    OptimizationType,
    PerformanceComponent,
    QueueBackend,
)


class PerformanceMetric(UUIDModel, TimeStampedModel, CreatedByModel):
    """Individual performance metric measurement."""

    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=PerformanceComponent.choices,
        db_index=True,
    )
    module = models.CharField(_("Module"), max_length=100, blank=True, db_index=True)
    metric_name = models.CharField(_("Metric Name"), max_length=100, db_index=True)
    value = models.DecimalField(
        _("Value"), max_digits=20, decimal_places=4, db_index=True
    )
    unit = models.CharField(
        _("Unit"),
        max_length=10,
        choices=MetricUnit.choices,
        default=MetricUnit.MILLISECONDS,
    )
    environment = models.CharField(
        _("Environment"), max_length=20, default="production", db_index=True
    )

    # Context
    request_path = models.CharField(_("Request Path"), max_length=500, blank=True)
    user_agent = models.CharField(_("User Agent"), max_length=500, blank=True)
    query_params = models.JSONField(_("Query Parameters"), default=dict, blank=True)

    # Metadata
    tags = models.JSONField(_("Tags"), default=dict, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    class Meta:
        verbose_name = _("Performance Metric")
        verbose_name_plural = _("Performance Metrics")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["component", "metric_name", "created_at"]),
            models.Index(fields=["module", "created_at"]),
            models.Index(fields=["environment", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.component} - {self.metric_name}: {self.value} {self.unit}"


class PerformanceKPI(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Key Performance Indicator definitions and tracking."""

    name = models.CharField(_("KPI Name"), max_length=100, unique=True)
    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=PerformanceComponent.choices,
        db_index=True,
    )
    metric_name = models.CharField(_("Metric Name"), max_length=100)
    description = models.TextField(_("Description"), blank=True)

    target_value = models.DecimalField(
        _("Target Value"), max_digits=20, decimal_places=4
    )
    target_unit = models.CharField(
        _("Target Unit"), max_length=10, choices=MetricUnit.choices
    )
    threshold_warning = models.DecimalField(
        _("Warning Threshold"), max_digits=20, decimal_places=4, null=True, blank=True
    )
    threshold_critical = models.DecimalField(
        _("Critical Threshold"), max_digits=20, decimal_places=4, null=True, blank=True
    )

    # Direction: lower_is_better or higher_is_better
    direction = models.CharField(
        _("Direction"),
        max_length=20,
        choices=[
            ("lower_is_better", _("Lower is Better")),
            ("higher_is_better", _("Higher is Better")),
        ],
        default="lower_is_better",
    )

    # Aggregation settings
    aggregation_period = models.CharField(
        _("Aggregation Period"),
        max_length=20,
        choices=[
            ("realtime", _("Real-time")),
            ("hourly", _("Hourly")),
            ("daily", _("Daily")),
            ("weekly", _("Weekly")),
            ("monthly", _("Monthly")),
        ],
        default="daily",
    )
    aggregation_method = models.CharField(
        _("Aggregation Method"),
        max_length=20,
        choices=[
            ("avg", _("Average")),
            ("median", _("Median")),
            ("p95", _("95th Percentile")),
            ("p99", _("99th Percentile")),
            ("min", _("Minimum")),
            ("max", _("Maximum")),
        ],
        default="avg",
    )

    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        verbose_name = _("Performance KPI")
        verbose_name_plural = _("Performance KPIs")
        ordering = ["component", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.component})"

    def evaluate_current_value(self, value: float) -> dict:
        """Evaluate a value against KPI thresholds."""
        if self.direction == "lower_is_better":
            status = "healthy"
            if self.threshold_critical and value >= float(self.threshold_critical):
                status = "critical"
            elif self.threshold_warning and value >= float(self.threshold_warning):
                status = "warning"
        else:
            status = "healthy"
            if self.threshold_critical and value <= float(self.threshold_critical):
                status = "critical"
            elif self.threshold_warning and value <= float(self.threshold_warning):
                status = "warning"

        return {
            "status": status,
            "value": value,
            "target": float(self.target_value),
            "unit": self.target_unit,
            "direction": self.direction,
        }


class Benchmark(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel
):
    """Performance benchmark definitions and runs."""

    name = models.CharField(_("Benchmark Name"), max_length=200)
    description = models.TextField(_("Description"), blank=True)
    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=PerformanceComponent.choices,
        db_index=True,
    )

    # Benchmark configuration
    test_scenario = models.TextField(_("Test Scenario"))
    configuration = models.JSONField(_("Configuration"), default=dict)
    environment = models.CharField(_("Environment"), max_length=20, default="staging")

    # Target metrics
    target_metrics = models.JSONField(_("Target Metrics"), default=dict)

    # Status tracking
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BenchmarkStatus.choices,
        default=BenchmarkStatus.PENDING,
        db_index=True,
    )
    started_at = models.DateTimeField(_("Started At"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)

    # Results
    results = models.JSONField(_("Results"), default=dict, blank=True)
    passed = models.BooleanField(_("Passed"), null=True, blank=True)
    notes = models.TextField(_("Notes"), blank=True)

    # Version tracking
    version = models.CharField(_("Application Version"), max_length=50, blank=True)
    git_commit = models.CharField(_("Git Commit"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Benchmark")
        verbose_name_plural = _("Benchmarks")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["component", "status"]),
            models.Index(fields=["status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_status_display()})"

    def duration_seconds(self) -> float | None:
        """Return benchmark duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class BenchmarkRun(UUIDModel, TimeStampedModel):
    """Individual benchmark execution runs."""

    benchmark = models.ForeignKey(
        Benchmark,
        on_delete=models.CASCADE,
        related_name="runs",
        verbose_name=_("Benchmark"),
    )
    run_number = models.PositiveIntegerField(_("Run Number"))

    started_at = models.DateTimeField(_("Started At"))
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=BenchmarkStatus.choices,
        default=BenchmarkStatus.RUNNING,
    )

    results = models.JSONField(_("Results"), default=dict)
    error_message = models.TextField(_("Error Message"), blank=True)

    class Meta:
        verbose_name = _("Benchmark Run")
        verbose_name_plural = _("Benchmark Runs")
        ordering = ["-run_number"]
        unique_together = ("benchmark", "run_number")

    def __str__(self) -> str:
        return f"{self.benchmark.name} - Run #{self.run_number}"


class OptimizationRecord(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Record of performance optimization activities."""

    title = models.CharField(_("Title"), max_length=200)
    optimization_type = models.CharField(
        _("Optimization Type"),
        max_length=20,
        choices=OptimizationType.choices,
        db_index=True,
    )
    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=PerformanceComponent.choices,
        db_index=True,
    )
    module = models.CharField(_("Module"), max_length=100, blank=True, db_index=True)

    description = models.TextField(_("Description"))
    rationale = models.TextField(_("Rationale"))

    # Status and timeline
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=OptimizationStatus.choices,
        default=OptimizationStatus.IDENTIFIED,
        db_index=True,
    )
    identified_at = models.DateTimeField(_("Identified At"), default=timezone.now)
    planned_start = models.DateTimeField(_("Planned Start"), null=True, blank=True)
    actual_start = models.DateTimeField(_("Actual Start"), null=True, blank=True)
    completed_at = models.DateTimeField(_("Completed At"), null=True, blank=True)

    # Baseline and target metrics
    baseline_metrics = models.JSONField(_("Baseline Metrics"), default=dict)
    target_metrics = models.JSONField(_("Target Metrics"), default=dict)
    actual_metrics = models.JSONField(_("Actual Metrics"), default=dict, blank=True)

    # Impact assessment
    improvement_percentage = models.DecimalField(
        _("Improvement Percentage"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    estimated_impact = models.TextField(_("Estimated Impact"), blank=True)
    actual_impact = models.TextField(_("Actual Impact"), blank=True)

    # Risk and rollback
    risk_level = models.CharField(
        _("Risk Level"),
        max_length=10,
        choices=[
            ("LOW", _("Low")),
            ("MEDIUM", _("Medium")),
            ("HIGH", _("High")),
            ("CRITICAL", _("Critical")),
        ],
        default="LOW",
    )
    rollback_plan = models.TextField(_("Rollback Plan"), blank=True)

    # Approval
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_optimizations",
        verbose_name=_("Approved By"),
    )
    approved_at = models.DateTimeField(_("Approved At"), null=True, blank=True)

    # Related benchmark
    benchmark = models.ForeignKey(
        Benchmark,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="optimizations",
        verbose_name=_("Benchmark"),
    )

    class Meta:
        verbose_name = _("Optimization Record")
        verbose_name_plural = _("Optimization Records")
        ordering = ["-identified_at"]
        indexes = [
            models.Index(fields=["optimization_type", "status"]),
            models.Index(fields=["component", "status"]),
            models.Index(fields=["status", "identified_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_optimization_type_display()})"

    def clean(self) -> None:
        super().clean()
        if (
            self.actual_start
            and self.planned_start
            and self.actual_start < self.planned_start
        ):
            raise ValidationError(
                {"actual_start": _("Actual start cannot be before planned start.")}
            )
        if (
            self.completed_at
            and self.actual_start
            and self.completed_at < self.actual_start
        ):
            raise ValidationError(
                {"completed_at": _("Completed date cannot be before actual start.")}
            )


class CacheConfiguration(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel
):
    """Cache configuration management."""

    name = models.CharField(_("Cache Name"), max_length=100, unique=True)
    backend = models.CharField(
        _("Backend"),
        max_length=20,
        choices=CacheBackend.choices,
        default=CacheBackend.LOCAL_MEMORY,
    )
    location = models.CharField(_("Location"), max_length=500, blank=True)

    # Configuration
    timeout = models.PositiveIntegerField(_("Default Timeout (seconds)"), default=300)
    key_prefix = models.CharField(
        _("Key Prefix"), max_length=100, default="sitadc_perf"
    )
    max_entries = models.PositiveIntegerField(_("Max Entries"), default=10000)
    options = models.JSONField(_("Backend Options"), default=dict)

    # Scope
    scope = models.CharField(_("Scope"), max_length=100, blank=True)
    description = models.TextField(_("Description"), blank=True)

    # Monitoring
    monitor_hit_ratio = models.BooleanField(_("Monitor Hit Ratio"), default=True)
    alert_threshold_hit_ratio = models.DecimalField(
        _("Alert Threshold Hit Ratio"),
        max_digits=5,
        decimal_places=2,
        default=80.0,
    )

    class Meta:
        verbose_name = _("Cache Configuration")
        verbose_name_plural = _("Cache Configurations")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_backend_display()})"


class CacheMetrics(UUIDModel, TimeStampedModel):
    """Cache performance metrics."""

    cache_config = models.ForeignKey(
        CacheConfiguration,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name=_("Cache Configuration"),
    )

    # Metrics
    total_requests = models.PositiveBigIntegerField(_("Total Requests"), default=0)
    hits = models.PositiveBigIntegerField(_("Cache Hits"), default=0)
    misses = models.PositiveBigIntegerField(_("Cache Misses"), default=0)
    hit_ratio = models.DecimalField(
        _("Hit Ratio (%)"), max_digits=5, decimal_places=2, default=0.0
    )

    # Memory
    memory_usage_bytes = models.PositiveBigIntegerField(
        _("Memory Usage (bytes)"), default=0
    )
    entry_count = models.PositiveIntegerField(_("Entry Count"), default=0)
    eviction_count = models.PositiveBigIntegerField(_("Eviction Count"), default=0)

    # Errors
    error_count = models.PositiveBigIntegerField(_("Error Count"), default=0)

    class Meta:
        verbose_name = _("Cache Metrics")
        verbose_name_plural = _("Cache Metrics")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["cache_config", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.cache_config.name} - {self.created_at:%Y-%m-%d %H:%M}"

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        total = self.hits + self.misses
        if total == 0:
            return 0.0
        return round(self.hits / total * 100, 2)


class QueueMonitoring(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel
):
    """Background queue monitoring configuration."""

    name = models.CharField(_("Queue Name"), max_length=100, unique=True)
    backend = models.CharField(
        _("Backend"),
        max_length=20,
        choices=QueueBackend.choices,
        default=QueueBackend.DATABASE,
    )
    queue_name = models.CharField(_("Queue Name (backend)"), max_length=200)

    # Connection
    connection_config = models.JSONField(_("Connection Configuration"), default=dict)

    # Monitoring settings
    monitor_depth = models.BooleanField(_("Monitor Queue Depth"), default=True)
    monitor_processing_time = models.BooleanField(
        _("Monitor Processing Time"), default=True
    )
    monitor_failure_rate = models.BooleanField(_("Monitor Failure Rate"), default=True)

    # Alerts
    alert_depth_threshold = models.PositiveIntegerField(
        _("Alert Depth Threshold"), default=1000
    )
    alert_processing_time_threshold = models.PositiveIntegerField(
        _("Alert Processing Time Threshold (seconds)"), default=60
    )
    alert_failure_rate_threshold = models.DecimalField(
        _("Alert Failure Rate Threshold (%)"),
        max_digits=5,
        decimal_places=2,
        default=5.0,
    )

    class Meta:
        verbose_name = _("Queue Monitoring")
        verbose_name_plural = _("Queue Monitorings")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_backend_display()})"


class QueueMetrics(UUIDModel, TimeStampedModel):
    """Queue performance metrics."""

    queue = models.ForeignKey(
        QueueMonitoring,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name=_("Queue"),
    )

    # Queue depth
    depth = models.PositiveIntegerField(_("Queue Depth"), default=0)
    pending = models.PositiveIntegerField(_("Pending Jobs"), default=0)
    processing = models.PositiveIntegerField(_("Processing Jobs"), default=0)
    completed = models.PositiveBigIntegerField(_("Completed Jobs"), default=0)
    failed = models.PositiveBigIntegerField(_("Failed Jobs"), default=0)

    # Processing time
    avg_processing_time = models.DecimalField(
        _("Average Processing Time (seconds)"),
        max_digits=10,
        decimal_places=3,
        default=0.0,
    )
    max_processing_time = models.DecimalField(
        _("Max Processing Time (seconds)"),
        max_digits=10,
        decimal_places=3,
        default=0.0,
    )

    # Throughput
    throughput_per_minute = models.DecimalField(
        _("Throughput (jobs/minute)"),
        max_digits=10,
        decimal_places=2,
        default=0.0,
    )

    class Meta:
        verbose_name = _("Queue Metrics")
        verbose_name_plural = _("Queue Metrics")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["queue", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.queue.name} - {self.created_at:%Y-%m-%d %H:%M}"


class DatabaseMonitoring(
    UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel, IsActiveModel
):
    """Database performance monitoring configuration."""

    name = models.CharField(_("Database Name"), max_length=100, unique=True)
    alias = models.CharField(_("Database Alias"), max_length=100, default="default")

    # Monitoring settings
    monitor_query_performance = models.BooleanField(
        _("Monitor Query Performance"), default=True
    )
    monitor_connections = models.BooleanField(_("Monitor Connections"), default=True)
    monitor_table_sizes = models.BooleanField(_("Monitor Table Sizes"), default=True)
    monitor_index_usage = models.BooleanField(_("Monitor Index Usage"), default=True)

    # Slow query threshold
    slow_query_threshold_ms = models.PositiveIntegerField(
        _("Slow Query Threshold (ms)"), default=1000
    )

    # Connection pool
    max_connections = models.PositiveIntegerField(_("Max Connections"), default=100)
    alert_connection_usage_threshold = models.DecimalField(
        _("Alert Connection Usage Threshold (%)"),
        max_digits=5,
        decimal_places=2,
        default=80.0,
    )

    class Meta:
        verbose_name = _("Database Monitoring")
        verbose_name_plural = _("Database Monitorings")
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.alias})"


class DatabaseMetrics(UUIDModel, TimeStampedModel):
    """Database performance metrics."""

    database = models.ForeignKey(
        DatabaseMonitoring,
        on_delete=models.CASCADE,
        related_name="metrics",
        verbose_name=_("Database"),
    )

    # Connections
    active_connections = models.PositiveIntegerField(_("Active Connections"), default=0)
    idle_connections = models.PositiveIntegerField(_("Idle Connections"), default=0)
    max_used_connections = models.PositiveIntegerField(
        _("Max Used Connections"), default=0
    )

    # Query performance
    total_queries = models.PositiveBigIntegerField(_("Total Queries"), default=0)
    slow_queries = models.PositiveIntegerField(_("Slow Queries"), default=0)
    avg_query_time = models.DecimalField(
        _("Average Query Time (ms)"),
        max_digits=10,
        decimal_places=3,
        default=0.0,
    )

    # Cache
    cache_hit_ratio = models.DecimalField(
        _("Cache Hit Ratio (%)"), max_digits=5, decimal_places=2, default=0.0
    )

    # Size
    database_size_bytes = models.PositiveBigIntegerField(
        _("Database Size (bytes)"), default=0
    )
    index_size_bytes = models.PositiveBigIntegerField(
        _("Index Size (bytes)"), default=0
    )

    class Meta:
        verbose_name = _("Database Metrics")
        verbose_name_plural = _("Database Metrics")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["database", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.database.name} - {self.created_at:%Y-%m-%d %H:%M}"


class PerformanceAlert(UUIDModel, TimeStampedModel, CreatedByModel, UpdatedByModel):
    """Performance alerts and notifications."""

    title = models.CharField(_("Alert Title"), max_length=200)
    severity = models.CharField(
        _("Severity"),
        max_length=10,
        choices=AlertSeverity.choices,
        default=AlertSeverity.WARNING,
        db_index=True,
    )

    # Source
    component = models.CharField(
        _("Component"),
        max_length=30,
        choices=PerformanceComponent.choices,
        db_index=True,
    )
    metric_name = models.CharField(_("Metric Name"), max_length=100, blank=True)

    # Alert details
    message = models.TextField(_("Message"))
    current_value = models.DecimalField(
        _("Current Value"), max_digits=20, decimal_places=4, null=True, blank=True
    )
    threshold_value = models.DecimalField(
        _("Threshold Value"), max_digits=20, decimal_places=4, null=True, blank=True
    )

    # Related objects
    kpi = models.ForeignKey(
        PerformanceKPI,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name=_("Related KPI"),
    )
    cache_config = models.ForeignKey(
        CacheConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name=_("Related Cache"),
    )
    queue = models.ForeignKey(
        QueueMonitoring,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name=_("Related Queue"),
    )
    database = models.ForeignKey(
        DatabaseMonitoring,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alerts",
        verbose_name=_("Related Database"),
    )

    # Status
    is_acknowledged = models.BooleanField(_("Acknowledged"), default=False)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
        verbose_name=_("Acknowledged By"),
    )
    acknowledged_at = models.DateTimeField(_("Acknowledged At"), null=True, blank=True)
    resolved_at = models.DateTimeField(_("Resolved At"), null=True, blank=True)

    class Meta:
        verbose_name = _("Performance Alert")
        verbose_name_plural = _("Performance Alerts")
        ordering = ["-severity", "-created_at"]
        indexes = [
            models.Index(fields=["severity", "is_acknowledged"]),
            models.Index(fields=["component", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"[{self.get_severity_display()}] {self.title}"


class PerformanceReport(UUIDModel, TimeStampedModel, CreatedByModel):
    """Generated performance reports."""

    title = models.CharField(_("Report Title"), max_length=200)
    period_start = models.DateTimeField(_("Period Start"))
    period_end = models.DateTimeField(_("Period End"))

    # Report data
    summary = models.JSONField(_("Summary"), default=dict)
    metrics = models.JSONField(_("Metrics"), default=dict)
    kpi_evaluations = models.JSONField(_("KPI Evaluations"), default=dict)
    alerts = models.JSONField(_("Alerts"), default=list)
    optimizations = models.JSONField(_("Optimizations"), default=list)
    recommendations = models.TextField(_("Recommendations"), blank=True)

    # Export
    format = models.CharField(
        _("Format"),
        max_length=10,
        choices=[
            ("HTML", "HTML"),
            ("PDF", "PDF"),
            ("XLSX", "XLSX"),
            ("CSV", "CSV"),
        ],
        default="HTML",
    )
    file = models.FileField(
        _("Report File"), upload_to="performance_reports/", null=True, blank=True
    )

    class Meta:
        verbose_name = _("Performance Report")
        verbose_name_plural = _("Performance Reports")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return (
            f"{self.title} ({self.period_start:%Y-%m-%d} to {self.period_end:%Y-%m-%d})"
        )

    def clean(self) -> None:
        super().clean()
        if (
            self.period_end
            and self.period_start
            and self.period_end < self.period_start
        ):
            raise ValidationError(
                {"period_end": _("Period end cannot be before period start.")}
            )
