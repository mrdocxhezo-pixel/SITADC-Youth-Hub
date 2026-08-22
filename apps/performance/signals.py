"""Signals for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

import logging
import time
from functools import wraps

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def record_performance_metric(
    component: str,
    metric_name: str,
    unit: str = "MS",
    module: str = "",
):
    """Decorator to record performance metrics for a function."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.perf_counter() - start_time) * 1000
                logger.debug(
                    "Performance: %s.%s took %.2f %s",
                    component,
                    metric_name,
                    duration_ms,
                    unit,
                )
                # Could save to database here if needed

        return wrapper

    return decorator


# Signal handlers for automatic monitoring
@receiver(post_save, sender="performance.CacheConfiguration")
def cache_config_post_save(sender, instance, created, **kwargs):
    """Handle cache configuration creation/update."""
    if created:
        logger.info("Cache configuration created: %s", instance.name)


@receiver(post_save, sender="performance.QueueMonitoring")
def queue_monitoring_post_save(sender, instance, created, **kwargs):
    """Handle queue monitoring creation/update."""
    if created:
        logger.info("Queue monitoring created: %s", instance.name)


@receiver(post_save, sender="performance.DatabaseMonitoring")
def database_monitoring_post_save(sender, instance, created, **kwargs):
    """Handle database monitoring creation/update."""
    if created:
        logger.info("Database monitoring created: %s", instance.name)


@receiver(post_save, sender="performance.OptimizationRecord")
def optimization_post_save(sender, instance, created, **kwargs):
    """Handle optimization record creation/update."""
    if created:
        logger.info("Optimization record created: %s", instance.title)


# Request/response timing middleware signal
class PerformanceTimingMiddleware:
    """Middleware to record request/response timing."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Record metric if user is authenticated and has performance access
        if hasattr(request, "user") and request.user.is_authenticated:
            try:
                from apps.performance.constants import MetricUnit, PerformanceComponent
                from apps.performance.models import PerformanceMetric

                # Only record for actual views, not static/media
                if not request.path.startswith(("/static/", "/media/")):
                    PerformanceMetric.objects.create(
                        component=PerformanceComponent.APIS,
                        module=(
                            request.resolver_match.namespace
                            if request.resolver_match
                            else ""
                        ),
                        metric_name="request_duration",
                        value=duration_ms,
                        unit=MetricUnit.MILLISECONDS,
                        request_path=request.path,
                        user_agent=request.META.get("HTTP_USER_AGENT", ""),
                        environment="production",
                        created_by=request.user,
                    )
            except Exception:
                # Silently ignore metric recording failures
                pass

        return response
