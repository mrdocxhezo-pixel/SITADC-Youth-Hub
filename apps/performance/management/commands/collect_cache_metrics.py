"""Management command to collect cache metrics."""

from __future__ import annotations

from django.core.cache import cache
from django.core.management.base import BaseCommand

from apps.performance.models import CacheConfiguration, CacheMetrics


class Command(BaseCommand):
    """Collect cache performance metrics."""

    help = "Collect cache performance metrics from configured caches"

    def handle(self, *args, **options):
        cache_configs = CacheConfiguration.objects.filter(is_active=True)

        if not cache_configs.exists():
            self.stdout.write(
                self.style.WARNING("No active cache configurations found.")
            )
            return

        for config in cache_configs:
            try:
                metrics = self._collect_cache_metrics(config)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Collected metrics for {config.name}: "
                        f"hits={metrics.hits}, misses={metrics.misses}, "
                        f"hit_ratio={metrics.hit_ratio}%"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to collect metrics for {config.name}: {e}"
                    )
                )

    def _collect_cache_metrics(self, config: CacheConfiguration) -> CacheMetrics:
        """Collect metrics for a cache configuration."""
        # Get cache backend
        from django.core.cache import caches

        cache_backend = caches[config.name] if config.name in caches else cache

        # Try to get stats from the cache backend
        # This varies by backend; we'll use a generic approach
        total_requests = 0
        hits = 0
        misses = 0

        # For Redis backend, we can get more detailed stats
        if config.backend == "REDIS":
            try:
                client = cache_backend.client.get_client()
                info = client.info()
                total_requests = info.get("keyspace_hits", 0) + info.get(
                    "keyspace_misses", 0
                )
                hits = info.get("keyspace_hits", 0)
                misses = info.get("keyspace_misses", 0)
                memory_usage = info.get("used_memory", 0)
            except Exception:
                memory_usage = 0
        else:
            # For other backends, we can't easily get stats
            # In production, you'd use cache.monitoring or similar
            memory_usage = 0

        hit_ratio = 0.0
        if total_requests > 0:
            hit_ratio = round(hits / total_requests * 100, 2)

        metrics = CacheMetrics.objects.create(
            cache_config=config,
            total_requests=total_requests,
            hits=hits,
            misses=misses,
            hit_ratio=hit_ratio,
            memory_usage_bytes=memory_usage,
            entry_count=0,  # Not easily available for all backends
        )

        # Check for alerts
        if config.monitor_hit_ratio and hit_ratio < float(
            config.alert_threshold_hit_ratio
        ):
            from apps.performance.constants import AlertSeverity, PerformanceComponent
            from apps.performance.models import PerformanceAlert

            PerformanceAlert.objects.create(
                title=f"Low cache hit ratio: {config.name}",
                severity=AlertSeverity.WARNING,
                component=PerformanceComponent.CACHING,
                metric_name="hit_ratio",
                message=(
                    f"Cache hit ratio ({hit_ratio:.2f}%) is below threshold "
                    f"({config.alert_threshold_hit_ratio}%)"
                ),
                current_value=hit_ratio,
                threshold_value=config.alert_threshold_hit_ratio,
                cache_config=config,
            )

        return metrics
