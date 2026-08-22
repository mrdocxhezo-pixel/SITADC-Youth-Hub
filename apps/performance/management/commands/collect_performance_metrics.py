"""Management command to collect performance metrics."""

from __future__ import annotations

import psutil
from django.core.management.base import BaseCommand

from apps.performance.constants import MetricUnit, PerformanceComponent
from apps.performance.models import PerformanceMetric


class Command(BaseCommand):
    """Collect system performance metrics."""

    help = "Collect system performance metrics (CPU, memory, disk, network)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Collection interval in seconds (default: 60)",
        )

    def handle(self, *args, **options):
        interval = options["interval"]

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="cpu_usage",
            value=cpu_percent,
            unit=MetricUnit.PERCENTAGE,
            module="system",
        )

        # Memory metrics
        memory = psutil.virtual_memory()
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="memory_usage",
            value=memory.percent,
            unit=MetricUnit.PERCENTAGE,
            module="system",
        )
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="memory_available_mb",
            value=memory.available / (1024 * 1024),
            unit=MetricUnit.MEGABYTES,
            module="system",
        )

        # Disk metrics
        disk = psutil.disk_usage("/")
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="disk_usage",
            value=disk.percent,
            unit=MetricUnit.PERCENTAGE,
            module="system",
        )
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="disk_free_gb",
            value=disk.free / (1024 * 1024 * 1024),
            unit=MetricUnit.MEGABYTES,
            module="system",
        )

        # Network metrics
        net_io = psutil.net_io_counters()
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="network_bytes_sent",
            value=net_io.bytes_sent,
            unit=MetricUnit.BYTES,
            module="system",
        )
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="network_bytes_recv",
            value=net_io.bytes_recv,
            unit=MetricUnit.BYTES,
            module="system",
        )

        # Process metrics
        process = psutil.Process()
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="process_memory_mb",
            value=process.memory_info().rss / (1024 * 1024),
            unit=MetricUnit.MEGABYTES,
            module="system",
        )
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="process_cpu_percent",
            value=process.cpu_percent(),
            unit=MetricUnit.PERCENTAGE,
            module="system",
        )
        self._record_metric(
            component=PerformanceComponent.INFRASTRUCTURE,
            metric_name="process_threads",
            value=process.num_threads(),
            unit=MetricUnit.COUNT,
            module="system",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Collected system metrics: CPU={cpu_percent}%, "
                f"Memory={memory.percent}%, Disk={disk.percent}%"
            )
        )

    def _record_metric(self, component, metric_name, value, unit, module=""):
        """Record a performance metric."""
        PerformanceMetric.objects.create(
            component=component,
            module=module,
            metric_name=metric_name,
            value=value,
            unit=unit,
            environment="production",
        )
