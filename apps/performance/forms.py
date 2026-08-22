"""Forms for Performance Optimization & Scalability (Phase 34)."""

from __future__ import annotations

from django import forms
from django.forms import DateTimeInput, ModelForm, Textarea

from .models import (
    Benchmark,
    CacheConfiguration,
    CacheMetrics,
    DatabaseMetrics,
    DatabaseMonitoring,
    OptimizationRecord,
    PerformanceAlert,
    PerformanceKPI,
    PerformanceMetric,
    PerformanceReport,
    QueueMetrics,
    QueueMonitoring,
)


class BasePerformanceForm(ModelForm):
    """Base form for performance models."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for _field_name, field in self.fields.items():
            widget_types = (
                forms.TextInput
                | forms.EmailInput
                | forms.URLInput
                | forms.PasswordInput
                | forms.NumberInput
            )
            if isinstance(field.widget, widget_types):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({"class": "form-control", "rows": 3})
            elif isinstance(field.widget, forms.Select | forms.SelectMultiple):
                field.widget.attrs.update({"class": "form-select"})
            elif isinstance(
                field.widget, forms.DateInput | forms.DateTimeInput | forms.FileInput
            ):
                field.widget.attrs.update({"class": "form-control"})
            elif isinstance(field.widget, forms.CheckboxInput | forms.RadioSelect):
                field.widget.attrs.update({"class": "form-check-input"})


class PerformanceMetricForm(BasePerformanceForm):
    class Meta:
        model = PerformanceMetric
        fields = [
            "component",
            "module",
            "metric_name",
            "value",
            "unit",
            "environment",
            "request_path",
            "user_agent",
            "query_params",
            "tags",
            "notes",
        ]
        widgets = {
            "value": forms.NumberInput(attrs={"step": "0.0001"}),
            "query_params": Textarea(attrs={"rows": 3}),
            "tags": Textarea(attrs={"rows": 3}),
        }


class PerformanceKPIForm(BasePerformanceForm):
    class Meta:
        model = PerformanceKPI
        fields = [
            "name",
            "component",
            "metric_name",
            "description",
            "target_value",
            "target_unit",
            "threshold_warning",
            "threshold_critical",
            "direction",
            "aggregation_period",
            "aggregation_method",
            "is_active",
        ]
        widgets = {
            "target_value": forms.NumberInput(attrs={"step": "0.0001"}),
            "threshold_warning": forms.NumberInput(attrs={"step": "0.0001"}),
            "threshold_critical": forms.NumberInput(attrs={"step": "0.0001"}),
            "description": Textarea(attrs={"rows": 3}),
        }


class BenchmarkForm(BasePerformanceForm):
    class Meta:
        model = Benchmark
        fields = [
            "name",
            "description",
            "component",
            "test_scenario",
            "configuration",
            "target_metrics",
            "environment",
        ]
        widgets = {
            "description": Textarea(attrs={"rows": 3}),
            "test_scenario": Textarea(attrs={"rows": 4}),
            "configuration": Textarea(attrs={"rows": 4}),
            "target_metrics": Textarea(attrs={"rows": 4}),
        }


class BenchmarkRunForm(BasePerformanceForm):
    class Meta:
        model = Benchmark
        fields = []


class OptimizationRecordForm(BasePerformanceForm):
    class Meta:
        model = OptimizationRecord
        fields = [
            "title",
            "optimization_type",
            "component",
            "module",
            "description",
            "rationale",
            "baseline_metrics",
            "target_metrics",
            "planned_start",
            "risk_level",
            "rollback_plan",
            "benchmark",
        ]
        widgets = {
            "description": Textarea(attrs={"rows": 4}),
            "rationale": Textarea(attrs={"rows": 4}),
            "baseline_metrics": Textarea(attrs={"rows": 4}),
            "target_metrics": Textarea(attrs={"rows": 4}),
            "rollback_plan": Textarea(attrs={"rows": 3}),
            "planned_start": DateTimeInput(attrs={"type": "datetime-local"}),
        }


class OptimizationStatusForm(BasePerformanceForm):
    """Form for updating optimization status."""

    class Meta:
        model = OptimizationRecord
        fields = [
            "status",
            "actual_metrics",
            "actual_impact",
        ]
        widgets = {
            "actual_metrics": Textarea(attrs={"rows": 4}),
            "actual_impact": Textarea(attrs={"rows": 3}),
        }


class CacheConfigurationForm(BasePerformanceForm):
    class Meta:
        model = CacheConfiguration
        fields = [
            "name",
            "backend",
            "location",
            "timeout",
            "key_prefix",
            "max_entries",
            "options",
            "scope",
            "description",
            "monitor_hit_ratio",
            "alert_threshold_hit_ratio",
            "is_active",
        ]
        widgets = {
            "options": Textarea(attrs={"rows": 4}),
            "description": Textarea(attrs={"rows": 3}),
            "alert_threshold_hit_ratio": forms.NumberInput(attrs={"step": "0.01"}),
        }


class CacheMetricsForm(BasePerformanceForm):
    class Meta:
        model = CacheMetrics
        fields = [
            "cache_config",
            "total_requests",
            "hits",
            "misses",
            "memory_usage_bytes",
            "entry_count",
            "eviction_count",
            "error_count",
        ]


class QueueMonitoringForm(BasePerformanceForm):
    class Meta:
        model = QueueMonitoring
        fields = [
            "name",
            "backend",
            "queue_name",
            "connection_config",
            "monitor_depth",
            "monitor_processing_time",
            "monitor_failure_rate",
            "alert_depth_threshold",
            "alert_processing_time_threshold",
            "alert_failure_rate_threshold",
            "is_active",
        ]
        widgets = {
            "connection_config": Textarea(attrs={"rows": 4}),
            "alert_failure_rate_threshold": forms.NumberInput(attrs={"step": "0.01"}),
        }


class QueueMetricsForm(BasePerformanceForm):
    class Meta:
        model = QueueMetrics
        fields = [
            "queue",
            "depth",
            "pending",
            "processing",
            "completed",
            "failed",
            "avg_processing_time",
            "max_processing_time",
            "throughput_per_minute",
        ]
        widgets = {
            "avg_processing_time": forms.NumberInput(attrs={"step": "0.001"}),
            "max_processing_time": forms.NumberInput(attrs={"step": "0.001"}),
            "throughput_per_minute": forms.NumberInput(attrs={"step": "0.01"}),
        }


class DatabaseMonitoringForm(BasePerformanceForm):
    class Meta:
        model = DatabaseMonitoring
        fields = [
            "name",
            "alias",
            "monitor_query_performance",
            "monitor_connections",
            "monitor_table_sizes",
            "monitor_index_usage",
            "slow_query_threshold_ms",
            "max_connections",
            "alert_connection_usage_threshold",
            "is_active",
        ]
        widgets = {
            "alert_connection_usage_threshold": forms.NumberInput(
                attrs={"step": "0.01"}
            ),
        }


class DatabaseMetricsForm(BasePerformanceForm):
    class Meta:
        model = DatabaseMetrics
        fields = [
            "database",
            "active_connections",
            "idle_connections",
            "max_used_connections",
            "total_queries",
            "slow_queries",
            "avg_query_time",
            "cache_hit_ratio",
            "database_size_bytes",
            "index_size_bytes",
        ]
        widgets = {
            "avg_query_time": forms.NumberInput(attrs={"step": "0.001"}),
            "cache_hit_ratio": forms.NumberInput(attrs={"step": "0.01"}),
        }


class PerformanceAlertForm(BasePerformanceForm):
    class Meta:
        model = PerformanceAlert
        fields = [
            "title",
            "severity",
            "component",
            "metric_name",
            "message",
            "current_value",
            "threshold_value",
            "kpi",
            "cache_config",
            "queue",
            "database",
        ]
        widgets = {
            "message": Textarea(attrs={"rows": 3}),
            "current_value": forms.NumberInput(attrs={"step": "0.0001"}),
            "threshold_value": forms.NumberInput(attrs={"step": "0.0001"}),
        }


class PerformanceAlertAcknowledgeForm(BasePerformanceForm):
    """Form for acknowledging alerts."""

    class Meta:
        model = PerformanceAlert
        fields = ["is_acknowledged"]


class PerformanceReportForm(BasePerformanceForm):
    class Meta:
        model = PerformanceReport
        fields = [
            "title",
            "period_start",
            "period_end",
            "format",
            "recommendations",
        ]
        widgets = {
            "period_start": DateTimeInput(attrs={"type": "datetime-local"}),
            "period_end": DateTimeInput(attrs={"type": "datetime-local"}),
            "recommendations": Textarea(attrs={"rows": 4}),
        }


class PerformanceReportGenerateForm(forms.Form):
    """Form for generating a new performance report."""

    title = forms.CharField(max_length=200)
    period_start = forms.DateTimeField(
        widget=DateTimeInput(attrs={"type": "datetime-local"})
    )
    period_end = forms.DateTimeField(
        widget=DateTimeInput(attrs={"type": "datetime-local"})
    )
    format = forms.ChoiceField(
        choices=[
            ("HTML", "HTML"),
            ("PDF", "PDF"),
            ("XLSX", "XLSX"),
            ("CSV", "CSV"),
        ],
        initial="HTML",
    )

    def clean(self):
        cleaned_data = super().clean()
        period_start = cleaned_data.get("period_start")
        period_end = cleaned_data.get("period_end")
        if period_start and period_end and period_end < period_start:
            raise forms.ValidationError(
                {"period_end": "Period end cannot be before period start."}
            )
        return cleaned_data
