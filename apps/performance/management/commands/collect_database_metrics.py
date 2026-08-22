"""Management command to collect database metrics."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection

from apps.performance.models import DatabaseMetrics, DatabaseMonitoring


class Command(BaseCommand):
    """Collect database performance metrics."""

    help = "Collect database performance metrics"

    def handle(self, *args, **options):
        databases = DatabaseMonitoring.objects.filter(is_active=True)

        if not databases.exists():
            self.stdout.write(
                self.style.WARNING(
                    "No active database monitoring configurations found."
                )
            )
            return

        for db_config in databases:
            try:
                metrics = self._collect_database_metrics(db_config)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Collected metrics for {db_config.name}: "
                        f"queries={metrics.total_queries}, "
                        f"slow={metrics.slow_queries}, "
                        f"avg_time={metrics.avg_query_time}ms"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to collect metrics for {db_config.name}: {e}"
                    )
                )

    def _collect_database_metrics(
        self, db_config: DatabaseMonitoring
    ) -> DatabaseMetrics:
        """Collect metrics for a database configuration."""
        # Use the configured database alias
        db_alias = db_config.alias

        # Get connection stats
        with connection.cursor() as cursor:
            # Get active connections (PostgreSQL specific)
            active_connections = 0
            try:
                cursor.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database();"
                )
                active_connections = cursor.fetchone()[0]
            except Exception:
                pass

            # Get cache hit ratio (PostgreSQL specific)
            cache_hit_ratio = 0.0
            try:
                cursor.execute(
                    """
                    SELECT
                        round(
                            sum(blks_hit) * 100.0 / nullif(sum(blks_hit) + sum(blks_read), 0),
                            2
                        ) as cache_hit_ratio
                    FROM pg_stat_database
                    WHERE datname = current_database();
                """
                )
                result = cursor.fetchone()
                if result and result[0] is not None:
                    cache_hit_ratio = float(result[0])
            except Exception:
                pass

            # Get database size
            database_size = 0
            try:
                cursor.execute(
                    """
                    SELECT pg_database_size(current_database());
                """
                )
                database_size = cursor.fetchone()[0]
            except Exception:
                pass

            # Get index size
            index_size = 0
            try:
                cursor.execute(
                    """
                    SELECT sum(pg_relation_size(indexrelid))
                    FROM pg_stat_user_indexes
                    WHERE schemaname = 'public';
                """
                )
                result = cursor.fetchone()
                if result and result[0] is not None:
                    index_size = result[0]
            except Exception:
                pass

        # Note: Django doesn't expose query counts directly without instrumentation
        # In production, you'd use pg_stat_statements or similar

        metrics = DatabaseMetrics.objects.create(
            database=db_config,
            active_connections=active_connections,
            idle_connections=0,
            max_used_connections=active_connections,
            total_queries=0,  # Would need query logging
            slow_queries=0,  # Would need pg_stat_statements
            avg_query_time=0.0,
            cache_hit_ratio=cache_hit_ratio,
            database_size_bytes=database_size,
            index_size_bytes=index_size,
        )

        # Check for alerts
        if db_config.monitor_connections and db_config.max_connections > 0:
            usage_pct = active_connections / db_config.max_connections * 100
            if usage_pct >= float(db_config.alert_connection_usage_threshold):
                from apps.performance.constants import (
                    AlertSeverity,
                    PerformanceComponent,
                )
                from apps.performance.models import PerformanceAlert

                PerformanceAlert.objects.create(
                    title=f"Database connection usage alert: {db_config.name}",
                    severity=AlertSeverity.WARNING,
                    component=PerformanceComponent.DATABASE,
                    metric_name="connection_usage",
                    message=(
                        f"Connection usage ({usage_pct:.1f}%) exceeds threshold "
                        f"({db_config.alert_connection_usage_threshold}%)"
                    ),
                    current_value=usage_pct,
                    threshold_value=db_config.alert_connection_usage_threshold,
                    database=db_config,
                )

        return metrics
