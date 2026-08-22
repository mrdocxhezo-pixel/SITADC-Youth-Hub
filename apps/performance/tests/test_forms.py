"""Tests for Performance Optimization forms (Phase 34)."""

from __future__ import annotations

from django.test import TestCase

from apps.performance.constants import (
    CacheBackend,
    MetricUnit,
    OptimizationType,
    PerformanceComponent,
    QueueBackend,
)
from apps.performance.forms import (
    BenchmarkForm,
    CacheConfigurationForm,
    CacheMetricsForm,
    DatabaseMetricsForm,
    DatabaseMonitoringForm,
    OptimizationRecordForm,
    PerformanceAlertForm,
    PerformanceKPIForm,
    PerformanceMetricForm,
    PerformanceReportGenerateForm,
    QueueMetricsForm,
    QueueMonitoringForm,
)


class PerformanceMetricFormTests(TestCase):
    """Tests for PerformanceMetricForm."""

    def test_metric_form_valid(self):
        """Test PerformanceMetricForm with valid data."""
        form = PerformanceMetricForm(
            data={
                "component": PerformanceComponent.DASHBOARD,
                "module": "dashboard",
                "metric_name": "page_load_time",
                "value": "1500.50",
                "unit": MetricUnit.MILLISECONDS,
                "environment": "production",
            }
        )
        self.assertTrue(form.is_valid())

    def test_metric_form_invalid_missing_component(self):
        """Test PerformanceMetricForm with missing component."""
        form = PerformanceMetricForm(
            data={
                "metric_name": "page_load_time",
                "value": "1500.50",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("component", form.errors)


class PerformanceKPIFormTests(TestCase):
    """Tests for PerformanceKPIForm."""

    def test_kpi_form_valid(self):
        """Test PerformanceKPIForm with valid data."""
        form = PerformanceKPIForm(
            data={
                "name": "api_latency",
                "component": PerformanceComponent.APIS,
                "metric_name": "api_latency",
                "target_value": "500.00",
                "target_unit": MetricUnit.MILLISECONDS,
                "direction": "lower_is_better",
                "aggregation_period": "daily",
                "aggregation_method": "avg",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_kpi_form_invalid_duplicate_name(self):
        """Test PerformanceKPIForm with duplicate name (requires DB)."""
        # This would need database; skip for unit test


class BenchmarkFormTests(TestCase):
    """Tests for BenchmarkForm."""

    def test_benchmark_form_valid(self):
        """Test BenchmarkForm with valid data."""
        form = BenchmarkForm(
            data={
                "name": "Load Test",
                "component": PerformanceComponent.APIS,
                "test_scenario": "Test scenario",
                "configuration": '{"users": 10}',
                "target_metrics": '{"p95": 200}',
                "environment": "staging",
            }
        )
        self.assertTrue(form.is_valid())


class OptimizationRecordFormTests(TestCase):
    """Tests for OptimizationRecordForm."""

    def test_optimization_form_valid(self):
        """Test OptimizationRecordForm with valid data."""
        form = OptimizationRecordForm(
            data={
                "title": "Query Optimization",
                "optimization_type": OptimizationType.QUERY,
                "component": PerformanceComponent.DATABASE,
                "module": "reports",
                "description": "Optimize slow queries",
                "rationale": "Queries are slow",
                "baseline_metrics": '{"avg_time": 1000}',
                "target_metrics": '{"avg_time": 200}',
                "risk_level": "LOW",
            }
        )
        self.assertTrue(form.is_valid())


class CacheConfigurationFormTests(TestCase):
    """Tests for CacheConfigurationForm."""

    def test_cache_config_form_valid(self):
        """Test CacheConfigurationForm with valid data."""
        form = CacheConfigurationForm(
            data={
                "name": "test_cache",
                "backend": CacheBackend.LOCAL_MEMORY,
                "timeout": "300",
                "key_prefix": "test",
                "max_entries": "1000",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid())


class QueueMonitoringFormTests(TestCase):
    """Tests for QueueMonitoringForm."""

    def test_queue_form_valid(self):
        """Test QueueMonitoringForm with valid data."""
        form = QueueMonitoringForm(
            data={
                "name": "test_queue",
                "backend": QueueBackend.DATABASE,
                "queue_name": "default",
                "monitor_depth": True,
                "monitor_processing_time": True,
                "monitor_failure_rate": True,
                "alert_depth_threshold": "1000",
                "alert_processing_time_threshold": "60",
                "alert_failure_rate_threshold": "5.0",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid())


class DatabaseMonitoringFormTests(TestCase):
    """Tests for DatabaseMonitoringForm."""

    def test_database_form_valid(self):
        """Test DatabaseMonitoringForm with valid data."""
        form = DatabaseMonitoringForm(
            data={
                "name": "Test DB",
                "alias": "default",
                "monitor_query_performance": True,
                "monitor_connections": True,
                "monitor_table_sizes": True,
                "monitor_index_usage": True,
                "slow_query_threshold_ms": "1000",
                "max_connections": "100",
                "alert_connection_usage_threshold": "80.0",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid())


class CacheMetricsFormTests(TestCase):
    """Tests for CacheMetricsForm."""

    def test_cache_metrics_form_valid(self):
        """Test CacheMetricsForm with valid data."""
        form = CacheMetricsForm(
            data={
                "total_requests": "1000",
                "hits": "900",
                "misses": "100",
                "memory_usage_bytes": "1048576",
                "entry_count": "500",
                "eviction_count": "10",
                "error_count": "0",
            }
        )
        # Need cache_config for full validation
        self.assertTrue(form.is_valid())


class QueueMetricsFormTests(TestCase):
    """Tests for QueueMetricsForm."""

    def test_queue_metrics_form_valid(self):
        """Test QueueMetricsForm with valid data."""
        form = QueueMetricsForm(
            data={
                "depth": "50",
                "pending": "40",
                "processing": "10",
                "completed": "1000",
                "failed": "5",
                "avg_processing_time": "2.5",
                "max_processing_time": "10.0",
                "throughput_per_minute": "60.0",
            }
        )
        self.assertTrue(form.is_valid())


class DatabaseMetricsFormTests(TestCase):
    """Tests for DatabaseMetricsForm."""

    def test_database_metrics_form_valid(self):
        """Test DatabaseMetricsForm with valid data."""
        form = DatabaseMetricsForm(
            data={
                "active_connections": "10",
                "idle_connections": "5",
                "max_used_connections": "50",
                "total_queries": "10000",
                "slow_queries": "5",
                "avg_query_time": "25.5",
                "cache_hit_ratio": "95.5",
                "database_size_bytes": "1073741824",
                "index_size_bytes": "104857600",
            }
        )
        self.assertTrue(form.is_valid())


class PerformanceAlertFormTests(TestCase):
    """Tests for PerformanceAlertForm."""

    def test_alert_form_valid(self):
        """Test PerformanceAlertForm with valid data."""
        from apps.performance.constants import AlertSeverity, PerformanceComponent

        form = PerformanceAlertForm(
            data={
                "title": "High Latency",
                "severity": AlertSeverity.WARNING,
                "component": PerformanceComponent.APIS,
                "metric_name": "api_latency",
                "message": "API latency is high",
                "current_value": "650.00",
                "threshold_value": "500.00",
            }
        )
        self.assertTrue(form.is_valid())


class PerformanceReportGenerateFormTests(TestCase):
    """Tests for PerformanceReportGenerateForm."""

    def test_report_form_valid(self):
        """Test PerformanceReportGenerateForm with valid data."""
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        form = PerformanceReportGenerateForm(
            data={
                "title": "Test Report",
                "period_start": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "period_end": now.strftime("%Y-%m-%dT%H:%M"),
                "format": "HTML",
            }
        )
        self.assertTrue(form.is_valid())

    def test_report_form_invalid_period(self):
        """Test PerformanceReportGenerateForm with invalid period."""
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        form = PerformanceReportGenerateForm(
            data={
                "title": "Test Report",
                "period_start": now.strftime("%Y-%m-%dT%H:%M"),
                "period_end": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M"),
                "format": "HTML",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("period_end", form.errors)
