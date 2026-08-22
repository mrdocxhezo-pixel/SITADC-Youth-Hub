"""Template tags for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def format_bytes(value: int) -> str:
    """Format bytes into human-readable string."""
    if value is None:
        return "N/A"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(value) < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{value:.2f} PB"


@register.filter
def format_duration_ms(value: float) -> str:
    """Format duration in milliseconds to human-readable string."""
    if value is None:
        return "N/A"
    if value < 1000:
        return f"{value:.2f} ms"
    elif value < 60000:
        return f"{value / 1000:.2f} s"
    elif value < 3600000:
        return f"{value / 60000:.2f} min"
    else:
        return f"{value / 3600000:.2f} h"


@register.filter
def format_percentage(value: float) -> str:
    """Format percentage with 2 decimal places."""
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


@register.filter
def metric_status_class(status: str) -> str:
    """Get Bootstrap class for metric status."""
    classes = {
        "healthy": "success",
        "warning": "warning",
        "critical": "danger",
        "no_data": "secondary",
    }
    return classes.get(status, "secondary")


@register.filter
def alert_severity_class(severity: str) -> str:
    """Get Bootstrap class for alert severity."""
    classes = {
        "INFO": "info",
        "WARNING": "warning",
        "CRITICAL": "danger",
    }
    return classes.get(severity, "secondary")


@register.inclusion_tag("performance/includes/metric_card.html")
def metric_card(title, value, unit="", status="healthy", trend=None):
    """Render a metric card for dashboards."""
    return {
        "title": title,
        "value": value,
        "unit": unit,
        "status": status,
        "trend": trend,
    }


@register.inclusion_tag("performance/includes/kpi_badge.html")
def kpi_badge(kpi, status, value=None):
    """Render a KPI status badge."""
    return {
        "kpi": kpi,
        "status": status,
        "value": value,
    }


@register.simple_tag
def performance_trend(current, previous):
    """Calculate trend direction between two values."""
    if previous is None or previous == 0:
        return "neutral"
    if current < previous:
        return "improving"  # Lower is better for most metrics
    elif current > previous:
        return "degrading"
    return "neutral"
