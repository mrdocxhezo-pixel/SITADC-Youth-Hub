"""Admin configuration for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import (
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


@admin.register(PerformanceMetric)
class PerformanceMetricAdmin(admin.ModelAdmin):
    list_display = (
        "component",
        "metric_name",
        "value",
        "unit",
        "module",
        "environment",
        "created_at",
    )
    list_filter = ("component", "unit", "environment", "created_at")
    search_fields = ("component", "metric_name", "module", "notes")
    readonly_fields = ("created_at", "created_by")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # Metrics are created programmatically


@admin.register(PerformanceKPI)
class PerformanceKPIAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "component",
        "metric_name",
        "target_value",
        "target_unit",
        "direction",
        "is_active",
        "created_at",
    )
    list_filter = (
        "component",
        "direction",
        "is_active",
        "aggregation_period",
        "created_at",
    )
    search_fields = ("name", "metric_name", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("component", "name")
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "component",
                    "metric_name",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            _("Target Configuration"),
            {"fields": ("target_value", "target_unit", "direction")},
        ),
        (
            _("Thresholds"),
            {
                "fields": ("threshold_warning", "threshold_critical"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Aggregation"),
            {
                "fields": ("aggregation_period", "aggregation_method"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(Benchmark)
class BenchmarkAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "component",
        "environment",
        "status",
        "passed",
        "version",
        "started_at",
        "completed_at",
        "created_at",
    )
    list_filter = ("component", "environment", "status", "created_at")
    search_fields = ("name", "description", "test_scenario", "version", "git_commit")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "started_at",
        "completed_at",
        "results",
        "passed",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "component",
                    "description",
                    "environment",
                    "version",
                    "git_commit",
                )
            },
        ),
        (
            _("Test Configuration"),
            {"fields": ("test_scenario", "configuration", "target_metrics")},
        ),
        (
            _("Status"),
            {"fields": ("status", "started_at", "completed_at", "passed", "notes")},
        ),
        (_("Results"), {"fields": ("results",), "classes": ("collapse",)}),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(OptimizationRecord)
class OptimizationRecordAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "optimization_type",
        "component",
        "module",
        "status",
        "improvement_percentage",
        "identified_at",
        "completed_at",
    )
    list_filter = (
        "optimization_type",
        "component",
        "status",
        "risk_level",
        "identified_at",
    )
    search_fields = ("title", "description", "rationale", "module")
    readonly_fields = (
        "created_at",
        "updated_at",
        "created_by",
        "updated_by",
        "identified_at",
        "actual_start",
        "completed_at",
        "improvement_percentage",
        "approved_by",
        "approved_at",
    )
    ordering = ("-identified_at",)
    date_hierarchy = "identified_at"
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "title",
                    "optimization_type",
                    "component",
                    "module",
                    "benchmark",
                )
            },
        ),
        (_("Description"), {"fields": ("description", "rationale")}),
        (
            _("Metrics"),
            {
                "fields": ("baseline_metrics", "target_metrics", "actual_metrics"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Status & Timeline"),
            {
                "fields": (
                    "status",
                    "identified_at",
                    "planned_start",
                    "actual_start",
                    "completed_at",
                    "improvement_percentage",
                )
            },
        ),
        (
            _("Impact Assessment"),
            {"fields": ("estimated_impact", "actual_impact"), "classes": ("collapse",)},
        ),
        (
            _("Risk & Rollback"),
            {"fields": ("risk_level", "rollback_plan"), "classes": ("collapse",)},
        ),
        (
            _("Approval"),
            {"fields": ("approved_by", "approved_at"), "classes": ("collapse",)},
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def has_add_permission(self, request):
        return False  # Created via service


@admin.register(CacheConfiguration)
class CacheConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "backend",
        "timeout",
        "key_prefix",
        "max_entries",
        "is_active",
        "created_at",
    )
    list_filter = ("backend", "is_active", "created_at")
    search_fields = ("name", "scope", "description")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("name",)
    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "name",
                    "backend",
                    "location",
                    "scope",
                    "description",
                    "is_active",
                )
            },
        ),
        (
            _("Configuration"),
            {"fields": ("timeout", "key_prefix", "max_entries", "options")},
        ),
        (
            _("Monitoring"),
            {"fields": ("monitor_hit_ratio", "alert_threshold_hit_ratio")},
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(CacheMetrics)
class CacheMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "cache_config",
        "total_requests",
        "hits",
        "misses",
        "hit_ratio",
        "memory_usage_mb",
        "entry_count",
        "created_at",
    )
    list_filter = ("cache_config", "created_at")
    readonly_fields = ("created_at", "hit_rate")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def memory_usage_mb(self, obj):
        return round(obj.memory_usage_bytes / (1024 * 1024), 2)

    memory_usage_mb.short_description = _("Memory Usage (MB)")


@admin.register(QueueMonitoring)
class QueueMonitoringAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "backend",
        "queue_name",
        "is_active",
        "created_at",
    )
    list_filter = ("backend", "is_active", "created_at")
    search_fields = ("name", "queue_name")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("name",)
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "backend", "queue_name", "is_active")},
        ),
        (_("Connection"), {"fields": ("connection_config",)}),
        (
            _("Monitoring"),
            {
                "fields": (
                    "monitor_depth",
                    "monitor_processing_time",
                    "monitor_failure_rate",
                )
            },
        ),
        (
            _("Alerts"),
            {
                "fields": (
                    "alert_depth_threshold",
                    "alert_processing_time_threshold",
                    "alert_failure_rate_threshold",
                )
            },
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(QueueMetrics)
class QueueMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "queue",
        "depth",
        "pending",
        "processing",
        "completed",
        "failed",
        "avg_processing_time",
        "throughput_per_minute",
        "created_at",
    )
    list_filter = ("queue", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False


@admin.register(DatabaseMonitoring)
class DatabaseMonitoringAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "alias",
        "is_active",
        "slow_query_threshold_ms",
        "max_connections",
        "created_at",
    )
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "alias")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    ordering = ("name",)
    fieldsets = (
        (_("Basic Information"), {"fields": ("name", "alias", "is_active")}),
        (
            _("Monitoring"),
            {
                "fields": (
                    "monitor_query_performance",
                    "monitor_connections",
                    "monitor_table_sizes",
                    "monitor_index_usage",
                )
            },
        ),
        (
            _("Thresholds"),
            {
                "fields": (
                    "slow_query_threshold_ms",
                    "max_connections",
                    "alert_connection_usage_threshold",
                )
            },
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "updated_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )


@admin.register(DatabaseMetrics)
class DatabaseMetricsAdmin(admin.ModelAdmin):
    list_display = (
        "database",
        "active_connections",
        "total_queries",
        "slow_queries",
        "avg_query_time",
        "cache_hit_ratio",
        "database_size_mb",
        "created_at",
    )
    list_filter = ("database", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def database_size_mb(self, obj):
        return round(obj.database_size_bytes / (1024 * 1024), 2)

    database_size_mb.short_description = _("Database Size (MB)")


@admin.register(PerformanceAlert)
class PerformanceAlertAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "severity_badge",
        "component",
        "is_acknowledged",
        "created_at",
        "acknowledged_at",
        "resolved_at",
    )
    list_filter = ("severity", "component", "is_acknowledged", "created_at")
    search_fields = ("title", "message", "metric_name")
    readonly_fields = (
        "created_at",
        "acknowledged_at",
        "resolved_at",
        "acknowledged_by",
        "created_by",
        "updated_by",
    )
    ordering = ("-severity", "-created_at")
    date_hierarchy = "created_at"
    fieldsets = (
        (
            _("Alert Information"),
            {"fields": ("title", "severity", "component", "metric_name", "message")},
        ),
        (_("Values"), {"fields": ("current_value", "threshold_value")}),
        (
            _("Related Objects"),
            {
                "fields": ("kpi", "cache_config", "queue", "database"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Status"),
            {
                "fields": (
                    "is_acknowledged",
                    "acknowledged_by",
                    "acknowledged_at",
                    "resolved_at",
                )
            },
        ),
        (
            _("Audit"),
            {
                "fields": ("created_at", "created_by", "updated_by"),
                "classes": ("collapse",),
            },
        ),
    )

    def severity_badge(self, obj):
        colors = {
            "INFO": "info",
            "WARNING": "warning",
            "CRITICAL": "danger",
        }
        color = colors.get(obj.severity, "secondary")
        return format_html(
            '<span class="badge bg-{}">{}</span>', color, obj.get_severity_display()
        )

    severity_badge.short_description = _("Severity")

    def has_add_permission(self, request):
        return False


@admin.register(PerformanceReport)
class PerformanceReportAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "period_start",
        "period_end",
        "format",
        "created_at",
    )
    list_filter = ("format", "created_at")
    search_fields = ("title", "recommendations")
    readonly_fields = (
        "created_at",
        "created_by",
        "summary",
        "metrics",
        "kpi_evaluations",
        "alerts",
        "optimizations",
    )
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("title", "period_start", "period_end", "format")},
        ),
        (
            _("Report Data"),
            {
                "fields": (
                    "summary",
                    "metrics",
                    "kpi_evaluations",
                    "alerts",
                    "optimizations",
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Recommendations"), {"fields": ("recommendations",)}),
        (_("File"), {"fields": ("file",)}),
        (
            _("Audit"),
            {"fields": ("created_at", "created_by"), "classes": ("collapse",)},
        ),
    )

    def has_add_permission(self, request):
        return False
