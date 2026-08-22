"""Tests for Performance Optimization models (Phase 34)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

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
from apps.performance.models import (
    Benchmark,
    CacheConfiguration,
    DatabaseMonitoring,
    OptimizationRecord,
    PerformanceAlert,
    PerformanceKPI,
    PerformanceMetric,
    PerformanceReport,
    QueueMonitoring,
)

User = get_user_model()


class PerformanceMetricModelTests(TestCase):
    """Tests for the PerformanceMetric model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_create_performance_metric(self):
        """Test creating a performance metric."""
        metric = PerformanceMetric.objects.create(
            component=PerformanceComponent.DASHBOARD,
            module="dashboard",
            metric_name="page_load_time",
            value=Decimal("1500.50"),
            unit=MetricUnit.MILLISECONDS,
            environment="production",
            created_by=self.user,
        )
        self.assertEqual(metric.component, PerformanceComponent.DASHBOARD)
        self.assertEqual(metric.metric_name, "page_load_time")
        self.assertEqual(metric.value, Decimal("1500.50"))
        self.assertEqual(metric.unit, MetricUnit.MILLISECONDS)
        self.assertEqual(metric.created_by, self.user)

    def test_metric_str_representation(self):
        """Test metric string representation."""
        metric = PerformanceMetric.objects.create(
            component=PerformanceComponent.APIS,
            metric_name="response_time",
            value=Decimal("250.75"),
            unit=MetricUnit.MILLISECONDS,
            created_by=self.user,
        )
        expected = "APIS - response_time: 250.7500 MS"
        self.assertEqual(str(metric), expected)


class PerformanceKPIModelTests(TestCase):
    """Tests for the PerformanceKPI model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser2", password="testpass123"
        )

    def test_create_kpi(self):
        """Test creating a KPI."""
        kpi = PerformanceKPI.objects.create(
            name="page_load_time",
            component=PerformanceComponent.DASHBOARD,
            metric_name="page_load_time",
            target_value=Decimal("2000.00"),
            target_unit=MetricUnit.MILLISECONDS,
            direction="lower_is_better",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(kpi.name, "page_load_time")
        self.assertEqual(kpi.target_value, Decimal("2000.00"))
        self.assertTrue(kpi.is_active)

    def test_kpi_evaluation_lower_is_better(self):
        """Test KPI evaluation for lower-is-better metrics."""
        kpi = PerformanceKPI.objects.create(
            name="api_latency",
            component=PerformanceComponent.APIS,
            metric_name="api_latency",
            target_value=Decimal("500.00"),
            target_unit=MetricUnit.MILLISECONDS,
            threshold_warning=Decimal("400.00"),
            threshold_critical=Decimal("600.00"),
            direction="lower_is_better",
            created_by=self.user,
            updated_by=self.user,
        )

        # Healthy value
        result = kpi.evaluate_current_value(300)
        self.assertEqual(result["status"], "healthy")

        # Warning value
        result = kpi.evaluate_current_value(450)
        self.assertEqual(result["status"], "warning")

        # Critical value
        result = kpi.evaluate_current_value(650)
        self.assertEqual(result["status"], "critical")

    def test_kpi_evaluation_higher_is_better(self):
        """Test KPI evaluation for higher-is-better metrics."""
        kpi = PerformanceKPI.objects.create(
            name="cache_hit_ratio",
            component=PerformanceComponent.CACHING,
            metric_name="cache_hit_ratio",
            target_value=Decimal("95.00"),
            target_unit=MetricUnit.PERCENTAGE,
            threshold_warning=Decimal("90.00"),
            threshold_critical=Decimal("80.00"),
            direction="higher_is_better",
            created_by=self.user,
            updated_by=self.user,
        )

        # Healthy value
        result = kpi.evaluate_current_value(96)
        self.assertEqual(result["status"], "healthy")

        # Warning value
        result = kpi.evaluate_current_value(85)
        self.assertEqual(result["status"], "warning")

        # Critical value
        result = kpi.evaluate_current_value(75)
        self.assertEqual(result["status"], "critical")


class BenchmarkModelTests(TestCase):
    """Tests for the Benchmark model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser3", password="testpass123"
        )

    def test_create_benchmark(self):
        """Test creating a benchmark."""
        benchmark = Benchmark.objects.create(
            name="API Load Test",
            component=PerformanceComponent.APIS,
            test_scenario="POST /api/v1/reports with 100 concurrent users",
            configuration={"users": 100, "duration": 60},
            target_metrics={"p95_latency_ms": 200, "error_rate": 0.01},
            environment="staging",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(benchmark.name, "API Load Test")
        self.assertEqual(benchmark.status, BenchmarkStatus.PENDING)
        self.assertIsNone(benchmark.started_at)
        self.assertIsNone(benchmark.completed_at)

    def test_benchmark_str_representation(self):
        """Test benchmark string representation."""
        benchmark = Benchmark.objects.create(
            name="Search Benchmark",
            component=PerformanceComponent.SEARCH,
            test_scenario="Search queries",
            configuration={},
            target_metrics={},
            created_by=self.user,
            updated_by=self.user,
        )
        expected = "Search Benchmark (Pending)"
        self.assertEqual(str(benchmark), expected)


class OptimizationRecordModelTests(TestCase):
    """Tests for the OptimizationRecord model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser4", password="testpass123"
        )

    def test_create_optimization(self):
        """Test creating an optimization record."""
        opt = OptimizationRecord.objects.create(
            title="Database Index Optimization",
            optimization_type=OptimizationType.DATABASE,
            component=PerformanceComponent.DATABASE,
            module="reports",
            description="Add composite indexes for report queries",
            rationale="Report queries are slow due to missing indexes",
            baseline_metrics={"avg_query_time": 1500, "p95_query_time": 3000},
            target_metrics={"avg_query_time": 200, "p95_query_time": 500},
            risk_level="LOW",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(opt.title, "Database Index Optimization")
        self.assertEqual(opt.status, OptimizationStatus.IDENTIFIED)
        self.assertEqual(opt.risk_level, "LOW")

    def test_optimization_clean_validation(self):
        """Test optimization date validation."""
        opt = OptimizationRecord(
            title="Test Optimization",
            optimization_type=OptimizationType.BACKEND,
            component=PerformanceComponent.BACKEND,
            description="Test",
            rationale="Test",
            baseline_metrics={},
            target_metrics={},
            planned_start=timezone.now() + timedelta(days=1),
            actual_start=timezone.now(),  # Before planned start
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(Exception) as cm:
            opt.clean()
        self.assertIn("Actual start cannot be before planned start", str(cm.exception))


class CacheConfigurationModelTests(TestCase):
    """Tests for the CacheConfiguration model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser5", password="testpass123"
        )

    def test_create_cache_config(self):
        """Test creating a cache configuration."""
        config = CacheConfiguration.objects.create(
            name="report_cache",
            backend=CacheBackend.REDIS,
            location="redis://localhost:6379/1",
            timeout=600,
            key_prefix="reports",
            max_entries=5000,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(config.name, "report_cache")
        self.assertEqual(config.backend, CacheBackend.REDIS)
        self.assertTrue(config.is_active)


class QueueMonitoringModelTests(TestCase):
    """Tests for the QueueMonitoring model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser6", password="testpass123"
        )

    def test_create_queue_monitoring(self):
        """Test creating a queue monitoring configuration."""
        queue = QueueMonitoring.objects.create(
            name="report_generation_queue",
            backend=QueueBackend.REDIS,
            queue_name="reports:generation",
            connection_config={"host": "localhost", "port": 6379},
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(queue.name, "report_generation_queue")
        self.assertEqual(queue.backend, QueueBackend.REDIS)
        self.assertTrue(queue.is_active)


class DatabaseMonitoringModelTests(TestCase):
    """Tests for the DatabaseMonitoring model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser7", password="testpass123"
        )

    def test_create_database_monitoring(self):
        """Test creating a database monitoring configuration."""
        db = DatabaseMonitoring.objects.create(
            name="Primary PostgreSQL",
            alias="default",
            slow_query_threshold_ms=500,
            max_connections=100,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(db.name, "Primary PostgreSQL")
        self.assertEqual(db.alias, "default")
        self.assertTrue(db.is_active)


class PerformanceAlertModelTests(TestCase):
    """Tests for the PerformanceAlert model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser8", password="testpass123"
        )

    def test_create_alert(self):
        """Test creating a performance alert."""
        alert = PerformanceAlert.objects.create(
            title="High API Latency",
            severity=AlertSeverity.WARNING,
            component=PerformanceComponent.APIS,
            metric_name="api_latency",
            message="API p95 latency exceeded 500ms",
            current_value=Decimal("650.00"),
            threshold_value=Decimal("500.00"),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(alert.title, "High API Latency")
        self.assertEqual(alert.severity, AlertSeverity.WARNING)
        self.assertFalse(alert.is_acknowledged)
        self.assertIsNone(alert.resolved_at)


class PerformanceReportModelTests(TestCase):
    """Tests for the PerformanceReport model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser9", password="testpass123"
        )

    def test_create_report(self):
        """Test creating a performance report."""
        now = timezone.now()
        report = PerformanceReport.objects.create(
            title="Daily Performance Report",
            period_start=now - timedelta(days=1),
            period_end=now,
            summary={"total_metrics": 1000},
            metrics={},
            kpi_evaluations={},
            alerts=[],
            optimizations=[],
            format="HTML",
            created_by=self.user,
        )
        self.assertEqual(report.title, "Daily Performance Report")
        self.assertEqual(report.format, "HTML")

    def test_report_clean_validation(self):
        """Test report period validation."""
        now = timezone.now()
        report = PerformanceReport(
            title="Invalid Report",
            period_start=now,
            period_end=now - timedelta(days=1),  # End before start
            format="HTML",
            created_by=self.user,
        )
        with self.assertRaises(Exception) as cm:
            report.clean()
        self.assertIn("Period end cannot be before period start", str(cm.exception))
