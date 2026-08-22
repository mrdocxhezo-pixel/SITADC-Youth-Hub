"""Constants for the Performance Optimization & Scalability module (Phase 34)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class PerformanceComponent(models.TextChoices):
    """Application components that can be monitored for performance."""

    AUTHENTICATION = "AUTHENTICATION", _("Authentication")
    DASHBOARD = "DASHBOARD", _("Dashboard")
    REPORTS = "REPORTS", _("Reports")
    DOCUMENTS = "DOCUMENTS", _("Documents")
    SEARCH = "SEARCH", _("Search")
    NOTIFICATIONS = "NOTIFICATIONS", _("Notifications")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    MEMBERSHIP = "MEMBERSHIP", _("Membership")
    VOLUNTEERS = "VOLUNTEERS", _("Volunteers")
    BENEFICIARIES = "BENEFICIARIES", _("Beneficiaries")
    PROGRAMS = "PROGRAMS", _("Programs")
    PROJECTS = "PROJECTS", _("Projects")
    MEAL = "MEAL", _("MEAL")
    FINANCE = "FINANCE", _("Finance")
    GOVERNANCE = "GOVERNANCE", _("Governance")
    COMMUNICATION = "COMMUNICATION", _("Communication")
    PROCUREMENT = "PROCUREMENT", _("Procurement")
    INTEGRATIONS = "INTEGRATIONS", _("Integrations")
    APIS = "APIS", _("APIs")
    DATABASE = "DATABASE", _("Database")
    STORAGE = "STORAGE", _("Storage")
    INFRASTRUCTURE = "INFRASTRUCTURE", _("Infrastructure")
    CACHING = "CACHING", _("Caching")
    QUEUES = "QUEUES", _("Background Queues")
    EXPORTS = "EXPORTS", _("Exports")


class OptimizationType(models.TextChoices):
    """Types of performance optimizations."""

    FRONTEND = "FRONTEND", _("Frontend Optimization")
    BACKEND = "BACKEND", _("Backend Optimization")
    DATABASE = "DATABASE", _("Database Optimization")
    QUERY = "QUERY", _("Query Optimization")
    API = "API", _("API Optimization")
    CACHING = "CACHING", _("Caching Optimization")
    BACKGROUND_JOBS = "BACKGROUND_JOBS", _("Background Job Optimization")
    STORAGE = "STORAGE", _("Storage Optimization")
    REPORT = "REPORT", _("Report Optimization")
    DASHBOARD = "DASHBOARD", _("Dashboard Optimization")
    SEARCH = "SEARCH", _("Search Optimization")
    EXPORT = "EXPORT", _("Export Optimization")
    NETWORK = "NETWORK", _("Network Optimization")


class MetricUnit(models.TextChoices):
    """Units for performance metrics."""

    MILLISECONDS = "MS", _("Milliseconds")
    SECONDS = "S", _("Seconds")
    BYTES = "B", _("Bytes")
    KILOBYTES = "KB", _("Kilobytes")
    MEGABYTES = "MB", _("Megabytes")
    PERCENTAGE = "PCT", _("Percentage")
    COUNT = "COUNT", _("Count")
    REQUESTS_PER_SECOND = "RPS", _("Requests per Second")
    QUERIES_PER_SECOND = "QPS", _("Queries per Second")


class BenchmarkStatus(models.TextChoices):
    """Status of performance benchmarks."""

    PENDING = "PENDING", _("Pending")
    RUNNING = "RUNNING", _("Running")
    COMPLETED = "COMPLETED", _("Completed")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class OptimizationStatus(models.TextChoices):
    """Status of optimization records."""

    IDENTIFIED = "IDENTIFIED", _("Identified")
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    TESTING = "TESTING", _("Testing")
    DEPLOYED = "DEPLOYED", _("Deployed")
    VERIFIED = "VERIFIED", _("Verified")
    REJECTED = "REJECTED", _("Rejected")


class CacheBackend(models.TextChoices):
    """Supported cache backends."""

    LOCAL_MEMORY = "LOCAL_MEMORY", _("Local Memory")
    REDIS = "REDIS", _("Redis")
    DATABASE = "DATABASE", _("Database")
    FILESYSTEM = "FILESYSTEM", _("Filesystem")
    DUMMY = "DUMMY", _("Dummy (No Cache)")


class QueueBackend(models.TextChoices):
    """Supported queue backends."""

    DATABASE = "DATABASE", _("Database")
    REDIS = "REDIS", _("Redis")
    RABBITMQ = "RABBITMQ", _("RabbitMQ")
    AMAZON_SQS = "AMAZON_SQS", _("Amazon SQS")


class AlertSeverity(models.TextChoices):
    """Performance alert severity levels."""

    INFO = "INFO", _("Info")
    WARNING = "WARNING", _("Warning")
    CRITICAL = "CRITICAL", _("Critical")


# Performance KPI targets (baseline values for comparison)
KPI_TARGETS: dict[str, dict[str, float | str]] = {
    "page_load_time": {
        "target": 2000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Average page load time",
    },
    "first_contentful_paint": {
        "target": 1000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "First Contentful Paint",
    },
    "largest_contentful_paint": {
        "target": 2500,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Largest Contentful Paint",
    },
    "time_to_interactive": {
        "target": 3000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Time to Interactive",
    },
    "api_latency": {
        "target": 500,
        "unit": MetricUnit.MILLISECONDS,
        "description": "API response latency",
    },
    "database_query_latency": {
        "target": 100,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Database query latency",
    },
    "cache_hit_percentage": {
        "target": 90.0,
        "unit": MetricUnit.PERCENTAGE,
        "description": "Cache hit ratio",
    },
    "report_generation_time": {
        "target": 10000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Report generation time",
    },
    "document_upload_time": {
        "target": 5000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Document upload time",
    },
    "export_generation_time": {
        "target": 15000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Export generation time",
    },
    "search_response_time": {
        "target": 500,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Search response time",
    },
    "dashboard_rendering_time": {
        "target": 1000,
        "unit": MetricUnit.MILLISECONDS,
        "description": "Dashboard rendering time",
    },
    "error_rate": {
        "target": 0.1,
        "unit": MetricUnit.PERCENTAGE,
        "description": "Application error rate",
    },
    "system_uptime": {
        "target": 99.9,
        "unit": MetricUnit.PERCENTAGE,
        "description": "System uptime",
    },
    "concurrent_user_capacity": {
        "target": 1000,
        "unit": MetricUnit.COUNT,
        "description": "Concurrent user capacity",
    },
}

# Default cache configuration
DEFAULT_CACHE_CONFIG = {
    "backend": CacheBackend.LOCAL_MEMORY,
    "timeout": 300,
    "key_prefix": "sitadc_perf",
    "max_entries": 10000,
    "options": {},
}

# Default queue configuration
DEFAULT_QUEUE_CONFIG = {
    "backend": QueueBackend.DATABASE,
    "default_timeout": 300,
    "max_retries": 3,
    "retry_delay": 60,
}
