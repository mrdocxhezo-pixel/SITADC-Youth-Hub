"""Views for Performance Optimization & Scalability (Phase 34).

All views enforce server-side authorization via the ``performance.*``
permission catalogue and remain fail-closed: list/detail data flows through
the selectors, and mutating operations set audit metadata.
"""

from __future__ import annotations

from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.rbac.decorators import any_permission_required

from . import selectors, services
from .constants import PerformanceComponent
from .forms import (
    BenchmarkForm,
    CacheConfigurationForm,
    CacheMetricsForm,
    DatabaseMetricsForm,
    DatabaseMonitoringForm,
    OptimizationRecordForm,
    OptimizationStatusForm,
    PerformanceAlertAcknowledgeForm,
    PerformanceKPIForm,
    PerformanceMetricForm,
    PerformanceReportGenerateForm,
    QueueMetricsForm,
    QueueMonitoringForm,
)
from .permissions import (
    PERFORMANCE_ALERT,
    PERFORMANCE_BENCHMARK,
    PERFORMANCE_CONFIGURE,
    PERFORMANCE_CREATE,
    PERFORMANCE_DELETE,
    PERFORMANCE_MANAGE,
    PERFORMANCE_OPTIMIZE,
    PERFORMANCE_REPORT,
    PERFORMANCE_UPDATE,
    PERFORMANCE_VIEW,
)

# Authorization decorators
_any_view = any_permission_required(PERFORMANCE_VIEW, PERFORMANCE_MANAGE)
_any_configure = any_permission_required(PERFORMANCE_CONFIGURE, PERFORMANCE_MANAGE)
_any_manage = any_permission_required(
    PERFORMANCE_CREATE, PERFORMANCE_UPDATE, PERFORMANCE_MANAGE
)
_any_delete = any_permission_required(PERFORMANCE_DELETE, PERFORMANCE_MANAGE)
_any_benchmark = any_permission_required(PERFORMANCE_BENCHMARK, PERFORMANCE_MANAGE)
_any_optimize = any_permission_required(PERFORMANCE_OPTIMIZE, PERFORMANCE_MANAGE)
_any_alert = any_permission_required(PERFORMANCE_ALERT, PERFORMANCE_MANAGE)
_any_report = any_permission_required(PERFORMANCE_REPORT, PERFORMANCE_MANAGE)


# Generic CRUD helpers
def object_list(
    request,
    template_name,
    context_name,
    queryset,
    search_fields=(),
    paginate_by=25,
):
    """Generic list view fed by an already-authorized queryset."""
    queryset = queryset
    search_query = request.GET.get("search", "")
    if search_query:
        q_objects = None
        for field in search_fields:
            if q_objects is None:
                q_objects = (
                    models.Q(**{f"{field}__icontains": search_query})
                    if "models" in globals()
                    else None
                )
            else:
                q_objects |= (
                    models.Q(**{f"{field}__icontains": search_query})
                    if "models" in globals()
                    else None
                )
        if q_objects:
            queryset = queryset.filter(q_objects)

    from django.core.paginator import Paginator

    paginator = Paginator(queryset, paginate_by)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {
        context_name: page_obj,
        "search_query": search_query,
        "is_paginated": page_obj.has_other_pages(),
    }
    return render(request, template_name, context)


def object_detail(request, queryset, pk, template_name, context_name):
    """Generic detail view fed by an already-authorized queryset."""
    obj = get_object_or_404(queryset, pk=pk)
    context = {context_name: obj}
    return render(request, template_name, context)


# Dashboard
@_any_view
def performance_dashboard(request):
    """Performance optimization dashboard."""
    kpi_status = selectors.get_kpi_status(request.user)
    benchmark_summary = selectors.get_benchmark_summary(request.user)
    optimization_summary = selectors.get_optimization_summary(request.user)
    cache_summary = selectors.get_cache_summary(request.user)
    queue_summary = selectors.get_queue_summary(request.user)
    database_summary = selectors.get_database_summary(request.user)

    # Recent alerts
    unacknowledged_alerts = selectors.get_unacknowledged_alerts(request.user)[:10]
    critical_alerts = selectors.get_critical_alerts(request.user)[:5]

    # Recent metrics by component
    recent_metrics = {}
    for component in PerformanceComponent.values:
        metrics = selectors.get_recent_metrics(
            request.user, component=component, hours=24, limit=10
        )
        if metrics.exists():
            recent_metrics[component] = metrics

    context = {
        "kpi_status": kpi_status,
        "benchmark_summary": benchmark_summary,
        "optimization_summary": optimization_summary,
        "cache_summary": cache_summary,
        "queue_summary": queue_summary,
        "database_summary": database_summary,
        "unacknowledged_alerts": unacknowledged_alerts,
        "critical_alerts": critical_alerts,
        "recent_metrics": recent_metrics,
        "components": PerformanceComponent.choices,
    }
    return render(request, "performance/dashboard.html", context)


# Metrics
@_any_view
def metric_list(request):
    return object_list(
        request,
        "performance/metric_list.html",
        "metrics",
        selectors.get_accessible_metrics(request.user),
        search_fields=("component", "metric_name", "module"),
    )


@_any_manage
def metric_create(request):
    if request.method == "POST":
        form = PerformanceMetricForm(request.POST)
        if form.is_valid():
            metric = form.save(commit=False)
            metric.created_by = request.user
            metric.save()
            messages.success(request, "Performance metric recorded successfully.")
            return redirect("performance:metric_list")
    else:
        form = PerformanceMetricForm()
    return render(request, "performance/metric_form.html", {"form": form})


@_any_view
def metric_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_metrics(request.user),
        pk,
        "performance/metric_detail.html",
        "metric",
    )


# KPIs
@_any_view
def kpi_list(request):
    return object_list(
        request,
        "performance/kpi_list.html",
        "kpis",
        selectors.get_accessible_kpis(request.user),
        search_fields=("name", "component", "metric_name"),
    )


@_any_manage
def kpi_create(request):
    if request.method == "POST":
        form = PerformanceKPIForm(request.POST)
        if form.is_valid():
            kpi = form.save(commit=False)
            kpi.created_by = request.user
            kpi.updated_by = request.user
            kpi.save()
            messages.success(request, "KPI created successfully.")
            return redirect("performance:kpi_list")
    else:
        form = PerformanceKPIForm()
    return render(request, "performance/kpi_form.html", {"form": form})


@_any_manage
def kpi_update(request, pk):
    kpi = get_object_or_404(selectors.get_accessible_kpis(request.user), pk=pk)
    if request.method == "POST":
        form = PerformanceKPIForm(request.POST, instance=kpi)
        if form.is_valid():
            kpi = form.save(commit=False)
            kpi.updated_by = request.user
            kpi.save()
            messages.success(request, "KPI updated successfully.")
            return redirect("performance:kpi_list")
    else:
        form = PerformanceKPIForm(instance=kpi)
    return render(request, "performance/kpi_form.html", {"form": form, "kpi": kpi})


@_any_view
def kpi_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_kpis(request.user),
        pk,
        "performance/kpi_detail.html",
        "kpi",
    )


# Benchmarks
@_any_view
def benchmark_list(request):
    return object_list(
        request,
        "performance/benchmark_list.html",
        "benchmarks",
        selectors.get_accessible_benchmarks(request.user),
        search_fields=("name", "component"),
    )


@_any_manage
def benchmark_create(request):
    if request.method == "POST":
        form = BenchmarkForm(request.POST)
        if form.is_valid():
            benchmark = form.save(commit=False)
            benchmark.created_by = request.user
            benchmark.updated_by = request.user
            benchmark.save()
            messages.success(request, "Benchmark created successfully.")
            return redirect("performance:benchmark_list")
    else:
        form = BenchmarkForm()
    return render(request, "performance/benchmark_form.html", {"form": form})


@_any_manage
def benchmark_update(request, pk):
    benchmark = get_object_or_404(
        selectors.get_accessible_benchmarks(request.user), pk=pk
    )
    if request.method == "POST":
        form = BenchmarkForm(request.POST, instance=benchmark)
        if form.is_valid():
            benchmark = form.save(commit=False)
            benchmark.updated_by = request.user
            benchmark.save()
            messages.success(request, "Benchmark updated successfully.")
            return redirect("performance:benchmark_list")
    else:
        form = BenchmarkForm(instance=benchmark)
    return render(
        request,
        "performance/benchmark_form.html",
        {"form": form, "benchmark": benchmark},
    )


@_any_view
def benchmark_detail(request, pk):
    benchmark = get_object_or_404(
        selectors.get_accessible_benchmarks(request.user), pk=pk
    )
    runs = benchmark.runs.all().order_by("-run_number")[:10]
    return render(
        request,
        "performance/benchmark_detail.html",
        {"benchmark": benchmark, "runs": runs},
    )


@_any_benchmark
def benchmark_execute(request, pk):
    """Execute a benchmark."""
    benchmark = get_object_or_404(
        selectors.get_accessible_benchmarks(request.user), pk=pk
    )
    if request.method == "POST":
        try:
            run = services.BenchmarkService().execute_benchmark(
                actor=request.user, benchmark_id=str(pk)
            )
            messages.success(
                request, f"Benchmark executed successfully (Run #{run.run_number})."
            )
        except Exception as e:
            messages.error(request, f"Benchmark execution failed: {e}")
        return redirect("performance:benchmark_detail", pk=pk)
    return render(
        request, "performance/benchmark_execute.html", {"benchmark": benchmark}
    )


# Optimizations
@_any_view
def optimization_list(request):
    return object_list(
        request,
        "performance/optimization_list.html",
        "optimizations",
        selectors.get_accessible_optimizations(request.user),
        search_fields=("title", "component", "module"),
    )


@_any_manage
def optimization_create(request):
    if request.method == "POST":
        form = OptimizationRecordForm(request.POST)
        if form.is_valid():
            opt = form.save(commit=False)
            opt.created_by = request.user
            opt.updated_by = request.user
            opt.save()
            messages.success(request, "Optimization record created successfully.")
            return redirect("performance:optimization_list")
    else:
        form = OptimizationRecordForm()
    return render(request, "performance/optimization_form.html", {"form": form})


@_any_manage
def optimization_update(request, pk):
    opt = get_object_or_404(selectors.get_accessible_optimizations(request.user), pk=pk)
    if request.method == "POST":
        form = OptimizationRecordForm(request.POST, instance=opt)
        if form.is_valid():
            opt = form.save(commit=False)
            opt.updated_by = request.user
            opt.save()
            messages.success(request, "Optimization updated successfully.")
            return redirect("performance:optimization_list")
    else:
        form = OptimizationRecordForm(instance=opt)
    return render(
        request,
        "performance/optimization_form.html",
        {"form": form, "optimization": opt},
    )


@_any_view
def optimization_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_optimizations(request.user),
        pk,
        "performance/optimization_detail.html",
        "optimization",
    )


@_any_optimize
def optimization_start(request, pk):
    """Start an optimization."""
    get_object_or_404(selectors.get_accessible_optimizations(request.user), pk=pk)
    if request.method == "POST":
        try:
            services.OptimizationService().start_optimization(
                actor=request.user, optimization_id=str(pk)
            )
            messages.success(request, "Optimization started.")
        except Exception as e:
            messages.error(request, f"Failed to start optimization: {e}")
    return redirect("performance:optimization_detail", pk=pk)


@_any_optimize
def optimization_complete(request, pk):
    """Complete an optimization with actual metrics."""
    opt = get_object_or_404(selectors.get_accessible_optimizations(request.user), pk=pk)
    if request.method == "POST":
        form = OptimizationStatusForm(request.POST, instance=opt)
        if form.is_valid():
            opt = form.save(commit=False)
            opt.updated_by = request.user
            try:
                services.OptimizationService().complete_optimization(
                    actor=request.user,
                    optimization_id=str(pk),
                    actual_metrics=opt.actual_metrics or {},
                )
                messages.success(request, "Optimization completed successfully.")
            except Exception as e:
                messages.error(request, f"Failed to complete optimization: {e}")
            return redirect("performance:optimization_detail", pk=pk)
    else:
        form = OptimizationStatusForm(instance=opt)
    return render(
        request,
        "performance/optimization_complete.html",
        {"form": form, "optimization": opt},
    )


@_any_manage
def optimization_verify(request, pk):
    """Verify (approve/reject) an optimization."""
    opt = get_object_or_404(selectors.get_accessible_optimizations(request.user), pk=pk)
    if request.method == "POST":
        verified = request.POST.get("verified") == "true"
        try:
            services.OptimizationService().verify_optimization(
                actor=request.user, optimization_id=str(pk), verified=verified
            )
            messages.success(
                request,
                f"Optimization {'verified' if verified else 'rejected'}.",
            )
        except Exception as e:
            messages.error(request, f"Failed to verify optimization: {e}")
        return redirect("performance:optimization_detail", pk=pk)
    return render(
        request, "performance/optimization_verify.html", {"optimization": opt}
    )


# Cache
@_any_view
def cache_list(request):
    return object_list(
        request,
        "performance/cache_list.html",
        "caches",
        selectors.get_accessible_cache_configs(request.user),
        search_fields=("name", "backend", "scope"),
    )


@_any_manage
def cache_create(request):
    if request.method == "POST":
        form = CacheConfigurationForm(request.POST)
        if form.is_valid():
            cache = form.save(commit=False)
            cache.created_by = request.user
            cache.updated_by = request.user
            cache.save()
            messages.success(request, "Cache configuration created successfully.")
            return redirect("performance:cache_list")
    else:
        form = CacheConfigurationForm()
    return render(request, "performance/cache_form.html", {"form": form})


@_any_manage
def cache_update(request, pk):
    cache = get_object_or_404(
        selectors.get_accessible_cache_configs(request.user), pk=pk
    )
    if request.method == "POST":
        form = CacheConfigurationForm(request.POST, instance=cache)
        if form.is_valid():
            cache = form.save(commit=False)
            cache.updated_by = request.user
            cache.save()
            messages.success(request, "Cache configuration updated successfully.")
            return redirect("performance:cache_list")
    else:
        form = CacheConfigurationForm(instance=cache)
    return render(
        request, "performance/cache_form.html", {"form": form, "cache": cache}
    )


@_any_view
def cache_detail(request, pk):
    cache = get_object_or_404(
        selectors.get_accessible_cache_configs(request.user), pk=pk
    )
    metrics = cache.metrics.all().order_by("-created_at")[:20]
    return render(
        request,
        "performance/cache_detail.html",
        {"cache": cache, "metrics": metrics},
    )


@_any_manage
def cache_metrics_create(request, pk):
    cache = get_object_or_404(
        selectors.get_accessible_cache_configs(request.user), pk=pk
    )
    if request.method == "POST":
        form = CacheMetricsForm(request.POST)
        if form.is_valid():
            metrics = form.save(commit=False)
            metrics.cache_config = cache
            metrics.save()
            messages.success(request, "Cache metrics recorded successfully.")
            return redirect("performance:cache_detail", pk=pk)
    else:
        form = CacheMetricsForm(initial={"cache_config": cache})
    return render(
        request,
        "performance/cache_metrics_form.html",
        {"form": form, "cache": cache},
    )


# Queues
@_any_view
def queue_list(request):
    return object_list(
        request,
        "performance/queue_list.html",
        "queues",
        selectors.get_accessible_queues(request.user),
        search_fields=("name", "backend", "queue_name"),
    )


@_any_manage
def queue_create(request):
    if request.method == "POST":
        form = QueueMonitoringForm(request.POST)
        if form.is_valid():
            queue = form.save(commit=False)
            queue.created_by = request.user
            queue.updated_by = request.user
            queue.save()
            messages.success(request, "Queue monitoring created successfully.")
            return redirect("performance:queue_list")
    else:
        form = QueueMonitoringForm()
    return render(request, "performance/queue_form.html", {"form": form})


@_any_manage
def queue_update(request, pk):
    queue = get_object_or_404(selectors.get_accessible_queues(request.user), pk=pk)
    if request.method == "POST":
        form = QueueMonitoringForm(request.POST, instance=queue)
        if form.is_valid():
            queue = form.save(commit=False)
            queue.updated_by = request.user
            queue.save()
            messages.success(request, "Queue monitoring updated successfully.")
            return redirect("performance:queue_list")
    else:
        form = QueueMonitoringForm(instance=queue)
    return render(
        request, "performance/queue_form.html", {"form": form, "queue": queue}
    )


@_any_view
def queue_detail(request, pk):
    queue = get_object_or_404(selectors.get_accessible_queues(request.user), pk=pk)
    metrics = queue.metrics.all().order_by("-created_at")[:20]
    return render(
        request,
        "performance/queue_detail.html",
        {"queue": queue, "metrics": metrics},
    )


@_any_manage
def queue_metrics_create(request, pk):
    queue = get_object_or_404(selectors.get_accessible_queues(request.user), pk=pk)
    if request.method == "POST":
        form = QueueMetricsForm(request.POST)
        if form.is_valid():
            metrics = form.save(commit=False)
            metrics.queue = queue
            metrics.save()
            messages.success(request, "Queue metrics recorded successfully.")
            return redirect("performance:queue_detail", pk=pk)
    else:
        form = QueueMetricsForm(initial={"queue": queue})
    return render(
        request,
        "performance/queue_metrics_form.html",
        {"form": form, "queue": queue},
    )


# Database
@_any_view
def database_list(request):
    return object_list(
        request,
        "performance/database_list.html",
        "databases",
        selectors.get_accessible_databases(request.user),
        search_fields=("name", "alias"),
    )


@_any_manage
def database_create(request):
    if request.method == "POST":
        form = DatabaseMonitoringForm(request.POST)
        if form.is_valid():
            db = form.save(commit=False)
            db.created_by = request.user
            db.updated_by = request.user
            db.save()
            messages.success(request, "Database monitoring created successfully.")
            return redirect("performance:database_list")
    else:
        form = DatabaseMonitoringForm()
    return render(request, "performance/database_form.html", {"form": form})


@_any_manage
def database_update(request, pk):
    db = get_object_or_404(selectors.get_accessible_databases(request.user), pk=pk)
    if request.method == "POST":
        form = DatabaseMonitoringForm(request.POST, instance=db)
        if form.is_valid():
            db = form.save(commit=False)
            db.updated_by = request.user
            db.save()
            messages.success(request, "Database monitoring updated successfully.")
            return redirect("performance:database_list")
    else:
        form = DatabaseMonitoringForm(instance=db)
    return render(
        request, "performance/database_form.html", {"form": form, "database": db}
    )


@_any_view
def database_detail(request, pk):
    db = get_object_or_404(selectors.get_accessible_databases(request.user), pk=pk)
    metrics = db.metrics.all().order_by("-created_at")[:20]
    return render(
        request,
        "performance/database_detail.html",
        {"database": db, "metrics": metrics},
    )


@_any_manage
def database_metrics_create(request, pk):
    db = get_object_or_404(selectors.get_accessible_databases(request.user), pk=pk)
    if request.method == "POST":
        form = DatabaseMetricsForm(request.POST)
        if form.is_valid():
            metrics = form.save(commit=False)
            metrics.database = db
            metrics.save()
            messages.success(request, "Database metrics recorded successfully.")
            return redirect("performance:database_detail", pk=pk)
    else:
        form = DatabaseMetricsForm(initial={"database": db})
    return render(
        request,
        "performance/database_metrics_form.html",
        {"form": form, "database": db},
    )


# Alerts
@_any_view
def alert_list(request):
    return object_list(
        request,
        "performance/alert_list.html",
        "alerts",
        selectors.get_accessible_alerts(request.user),
        search_fields=("title", "component", "metric_name"),
    )


@_any_view
def alert_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_alerts(request.user),
        pk,
        "performance/alert_detail.html",
        "alert",
    )


@_any_alert
def alert_acknowledge(request, pk):
    """Acknowledge an alert."""
    alert = get_object_or_404(selectors.get_accessible_alerts(request.user), pk=pk)
    if request.method == "POST":
        form = PerformanceAlertAcknowledgeForm(request.POST, instance=alert)
        if form.is_valid():
            services.PerformanceAlertService().acknowledge_alert(
                actor=request.user, alert_id=str(pk)
            )
            messages.success(request, "Alert acknowledged.")
            return redirect("performance:alert_list")
    else:
        form = PerformanceAlertAcknowledgeForm(instance=alert)
    return render(
        request, "performance/alert_acknowledge.html", {"form": form, "alert": alert}
    )


@_any_alert
def alert_resolve(request, pk):
    """Resolve an alert."""
    alert = get_object_or_404(selectors.get_accessible_alerts(request.user), pk=pk)
    if request.method == "POST":
        services.PerformanceAlertService().resolve_alert(
            actor=request.user, alert_id=str(pk)
        )
        messages.success(request, "Alert resolved.")
        return redirect("performance:alert_list")
    return render(request, "performance/alert_resolve.html", {"alert": alert})


# Reports
@_any_report
def report_list(request):
    return object_list(
        request,
        "performance/report_list.html",
        "reports",
        selectors.get_accessible_reports(request.user),
        search_fields=("title",),
    )


@_any_report
def report_create(request):
    if request.method == "POST":
        form = PerformanceReportGenerateForm(request.POST)
        if form.is_valid():
            report = services.PerformanceReportService().generate_report(
                actor=request.user,
                title=form.cleaned_data["title"],
                period_start=form.cleaned_data["period_start"],
                period_end=form.cleaned_data["period_end"],
                format=form.cleaned_data["format"],
            )
            messages.success(request, "Performance report generated successfully.")
            return redirect("performance:report_detail", pk=report.pk)
    else:
        form = PerformanceReportGenerateForm()
    return render(request, "performance/report_form.html", {"form": form})


@_any_report
def report_detail(request, pk):
    return object_detail(
        request,
        selectors.get_accessible_reports(request.user),
        pk,
        "performance/report_detail.html",
        "report",
    )


@_any_report
def report_download(request, pk):
    """Download a performance report."""
    report = get_object_or_404(selectors.get_accessible_reports(request.user), pk=pk)
    if report.file:
        from django.http import FileResponse

        return FileResponse(report.file.open(), as_attachment=True)
    messages.error(request, "Report file not available.")
    return redirect("performance:report_detail", pk=pk)


# API endpoints for real-time dashboard
@_any_view
def performance_dashboard_api(request):
    """API endpoint for real-time dashboard data."""
    from apps.performance.services import PerformanceKPIService

    kpi_service = PerformanceKPIService()
    kpi_results = kpi_service.evaluate_all_kpis(hours=1)

    # Get recent metrics for charts
    recent = {}
    for component in PerformanceComponent.values:
        metrics = selectors.get_recent_metrics(
            request.user, component=component, hours=1, limit=60
        ).order_by("created_at")
        recent[component] = [
            {
                "metric_name": m.metric_name,
                "value": float(m.value),
                "unit": m.unit,
                "timestamp": m.created_at.isoformat(),
            }
            for m in metrics
        ]

    return JsonResponse(
        {
            "kpi_results": [
                {
                    "name": r["kpi"].name,
                    "component": r["kpi"].component,
                    "status": r["status"],
                    "value": r["value"],
                    "target": r["evaluation"]["target"] if r["evaluation"] else None,
                }
                for r in kpi_results
            ],
            "recent_metrics": recent,
            "alerts": {
                "unacknowledged_count": selectors.get_unacknowledged_alerts(
                    request.user
                ).count(),
                "critical_count": selectors.get_critical_alerts(request.user).count(),
            },
            "timestamp": timezone.now().isoformat(),
        }
    )
