"""Exceptions for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations


class PerformanceError(Exception):
    """Base exception for performance module errors."""


class InvalidConfigurationError(PerformanceError):
    """Raised when a performance configuration is invalid."""


class BenchmarkExecutionError(PerformanceError):
    """Raised when a benchmark execution fails."""


class MetricCollectionError(PerformanceError):
    """Raised when metric collection fails."""


class OptimizationError(PerformanceError):
    """Raised when an optimization operation fails."""


class AlertError(PerformanceError):
    """Raised when an alert operation fails."""


class ReportGenerationError(PerformanceError):
    """Raised when report generation fails."""
