"""Tests for Performance Optimization views (Phase 34)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.performance.constants import (
    AlertSeverity,
    BenchmarkStatus,
    CacheBackend,
    MetricUnit,
    OptimizationStatus,
    OptimizationType,
    PerformanceComponent,
)
from apps.performance.models import (
    Benchmark,
    CacheConfiguration,
    OptimizationRecord,
    PerformanceAlert,
    PerformanceKPI,
    PerformanceMetric,
)

User = get_user_model()


class PerformanceViewTests(TestCase):
    """Tests for performance views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="viewuser", password="testpass123"
        )
        # Grant basic performance permissions
        from apps.rbac.authorization import grant_permission
        from apps.rbac.models import Role

        role = Role.objects.create(name="Performance Viewer", code="perf_viewer")
        grant_permission(self.user, "performance.view", role=role)

    def test_dashboard_requires_authentication(self):
        """Test dashboard requires authentication."""
        self.client.logout()
        response = self.client.get(reverse("performance:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_access_with_permission(self):
        """Test dashboard accessible with permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "performance/dashboard.html")

    def test_metric_list_requires_permission(self):
        """Test metric list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:metric_list"))
        self.assertEqual(response.status_code, 200)

    def test_kpi_list_requires_permission(self):
        """Test KPI list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:kpi_list"))
        self.assertEqual(response.status_code, 200)

    def test_benchmark_list_requires_permission(self):
        """Test benchmark list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:benchmark_list"))
        self.assertEqual(response.status_code, 200)

    def test_optimization_list_requires_permission(self):
        """Test optimization list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:optimization_list"))
        self.assertEqual(response.status_code, 200)

    def test_cache_list_requires_permission(self):
        """Test cache list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:cache_list"))
        self.assertEqual(response.status_code, 200)

    def test_queue_list_requires_permission(self):
        """Test queue list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:queue_list"))
        self.assertEqual(response.status_code, 200)

    def test_database_list_requires_permission(self):
        """Test database list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:database_list"))
        self.assertEqual(response.status_code, 200)

    def test_alert_list_requires_permission(self):
        """Test alert list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:alert_list"))
        self.assertEqual(response.status_code, 200)

    def test_report_list_requires_permission(self):
        """Test report list requires permission."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("performance:report_list"))
        self.assertEqual(response.status_code, 200)


class PerformanceModelIntegrationTests(TestCase):
    """Integration tests for performance models."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="integuser", password="testpass123"
        )

    def test_kpi_evaluation_workflow(self):
        """Test full KPI evaluation workflow."""
        # Create KPI
        _kpi = PerformanceKPI.objects.create(
            name="test_kpi",
            component=PerformanceComponent.APIS,
            metric_name="response_time",
            target_value=500,
            target_unit=MetricUnit.MILLISECONDS,
            threshold_warning=400,
            threshold_critical=600,
            direction="lower_is_better",
            created_by=self.user,
            updated_by=self.user,
        )

        # Record some metrics
        PerformanceMetric.objects.create(
            component=PerformanceComponent.APIS,
            metric_name="response_time",
            value=300,
            unit=MetricUnit.MILLISECONDS,
            created_by=self.user,
        )
        PerformanceMetric.objects.create(
            component=PerformanceComponent.APIS,
            metric_name="response_time",
            value=350,
            unit=MetricUnit.MILLISECONDS,
            created_by=self.user,
        )
        PerformanceMetric.objects.create(
            component=PerformanceComponent.APIS,
            metric_name="response_time",
            value=450,
            unit=MetricUnit.MILLISECONDS,
            created_by=self.user,
        )

        # Evaluate KPI
        from apps.performance.services import PerformanceKPIService

        service = PerformanceKPIService()
        results = service.evaluate_all_kpis(hours=1)

        # Find our KPI result
        kpi_result = next((r for r in results if r["kpi"].name == "test_kpi"), None)
        self.assertIsNotNone(kpi_result)
        self.assertEqual(kpi_result["status"], "healthy")  # Average ~367 < 400

    def test_optimization_workflow(self):
        """Test full optimization workflow."""
        # Create optimization
        opt = OptimizationRecord.objects.create(
            title="API Caching",
            optimization_type=OptimizationType.CACHING,
            component=PerformanceComponent.APIS,
            description="Add response caching",
            rationale="Reduce repeated computations",
            baseline_metrics={"avg_response_time": 500},
            target_metrics={"avg_response_time": 100},
            created_by=self.user,
            updated_by=self.user,
        )

        # Start optimization
        from apps.performance.services import OptimizationService

        service = OptimizationService()

        opt = service.start_optimization(actor=self.user, optimization_id=str(opt.pk))
        self.assertEqual(opt.status, OptimizationStatus.IN_PROGRESS)
        self.assertIsNotNone(opt.actual_start)

        # Complete optimization
        opt = service.complete_optimization(
            actor=self.user,
            optimization_id=str(opt.pk),
            actual_metrics={"avg_response_time": 120},
        )
        self.assertEqual(opt.status, OptimizationStatus.TESTING)
        self.assertIsNotNone(opt.completed_at)
        self.assertIsNotNone(opt.improvement_percentage)
        # Improvement: (500-120)/500 * 100 = 76%
        self.assertAlmostEqual(float(opt.improvement_percentage), 76.0, places=1)

        # Verify optimization
        opt = service.verify_optimization(
            actor=self.user, optimization_id=str(opt.pk), verified=True
        )
        self.assertEqual(opt.status, OptimizationStatus.VERIFIED)

    def test_alert_workflow(self):
        """Test alert acknowledgment and resolution."""
        alert = PerformanceAlert.objects.create(
            title="Test Alert",
            severity=AlertSeverity.WARNING,
            component=PerformanceComponent.DATABASE,
            message="Test message",
            created_by=self.user,
            updated_by=self.user,
        )

        self.assertFalse(alert.is_acknowledged)
        self.assertIsNone(alert.resolved_at)

        # Acknowledge
        from apps.performance.services import PerformanceAlertService

        service = PerformanceAlertService()
        alert = service.acknowledge_alert(actor=self.user, alert_id=str(alert.pk))

        self.assertTrue(alert.is_acknowledged)
        self.assertIsNotNone(alert.acknowledged_at)
        self.assertEqual(alert.acknowledged_by, self.user)

        # Resolve
        alert = service.resolve_alert(actor=self.user, alert_id=str(alert.pk))
        self.assertIsNotNone(alert.resolved_at)

    def test_benchmark_execution_workflow(self):
        """Test benchmark creation and execution."""
        benchmark = Benchmark.objects.create(
            name="Integration Test Benchmark",
            component=PerformanceComponent.SEARCH,
            test_scenario="Search 1000 queries",
            configuration={"queries": 1000},
            target_metrics={"avg_time": 50, "p95_time": 100},
            created_by=self.user,
            updated_by=self.user,
        )

        self.assertEqual(benchmark.status, BenchmarkStatus.PENDING)

        # Execute benchmark
        from apps.performance.services import BenchmarkService

        service = BenchmarkService()
        run = service.execute_benchmark(actor=self.user, benchmark_id=str(benchmark.pk))

        self.assertEqual(benchmark.status, BenchmarkStatus.COMPLETED)
        self.assertIsNotNone(benchmark.completed_at)
        self.assertIsNotNone(benchmark.results)
        self.assertEqual(run.run_number, 1)
        self.assertEqual(run.status, BenchmarkStatus.COMPLETED)

    def test_cache_metrics_collection(self):
        """Test cache metrics collection and alerting."""
        cache_config = CacheConfiguration.objects.create(
            name="test_cache",
            backend=CacheBackend.LOCAL_MEMORY,
            timeout=300,
            alert_threshold_hit_ratio=80.0,
            monitor_hit_ratio=True,
            created_by=self.user,
            updated_by=self.user,
        )

        # Record good metrics
        from apps.performance.services import CacheMonitoringService

        service = CacheMonitoringService()
        metrics = service.record_cache_metrics(
            cache_config_id=str(cache_config.pk),
            total_requests=1000,
            hits=950,
            misses=50,
        )

        self.assertEqual(metrics.hit_ratio, Decimal("95.00"))
        self.assertFalse(
            PerformanceAlert.objects.filter(
                cache_config=cache_config, metric_name="hit_ratio"
            ).exists()
        )

        # Record bad metrics (should trigger alert)
        metrics = service.record_cache_metrics(
            cache_config_id=str(cache_config.pk),
            total_requests=1000,
            hits=700,
            misses=300,
        )

        self.assertEqual(metrics.hit_ratio, Decimal("70.00"))
        self.assertTrue(
            PerformanceAlert.objects.filter(
                cache_config=cache_config,
                metric_name="hit_ratio",
                severity=AlertSeverity.WARNING,
            ).exists()
        )

    def test_report_generation(self):
        """Test performance report generation."""
        now = timezone.now()

        # Create some test data
        PerformanceMetric.objects.create(
            component=PerformanceComponent.DASHBOARD,
            metric_name="page_load",
            value=1500,
            unit=MetricUnit.MILLISECONDS,
            created_by=self.user,
        )

        PerformanceKPI.objects.create(
            name="page_load_time",
            component=PerformanceComponent.DASHBOARD,
            metric_name="page_load",
            target_value=2000,
            target_unit=MetricUnit.MILLISECONDS,
            direction="lower_is_better",
            created_by=self.user,
            updated_by=self.user,
        )

        # Generate report
        from apps.performance.services import PerformanceReportService

        service = PerformanceReportService()
        report = service.generate_report(
            actor=self.user,
            title="Test Report",
            period_start=now - timedelta(days=1),
            period_end=now,
        )

        self.assertEqual(report.title, "Test Report")
        self.assertEqual(report.format, "HTML")
        self.assertIn("total_metrics", report.summary)
        self.assertIn("page_load_time", report.kpi_evaluations)
