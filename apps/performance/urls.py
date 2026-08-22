"""URL configuration for Performance Optimization & Scalability (Phase 34)."""

from django.urls import path

from . import views

app_name = "performance"

urlpatterns = [
    # Dashboard
    path("", views.performance_dashboard, name="dashboard"),
    path("dashboard/api/", views.performance_dashboard_api, name="dashboard_api"),
    # Metrics
    path("metrics/", views.metric_list, name="metric_list"),
    path("metrics/create/", views.metric_create, name="metric_create"),
    path("metrics/<uuid:pk>/", views.metric_detail, name="metric_detail"),
    # KPIs
    path("kpis/", views.kpi_list, name="kpi_list"),
    path("kpis/create/", views.kpi_create, name="kpi_create"),
    path("kpis/<uuid:pk>/", views.kpi_detail, name="kpi_detail"),
    path("kpis/<uuid:pk>/update/", views.kpi_update, name="kpi_update"),
    # Benchmarks
    path("benchmarks/", views.benchmark_list, name="benchmark_list"),
    path("benchmarks/create/", views.benchmark_create, name="benchmark_create"),
    path("benchmarks/<uuid:pk>/", views.benchmark_detail, name="benchmark_detail"),
    path(
        "benchmarks/<uuid:pk>/update/", views.benchmark_update, name="benchmark_update"
    ),
    path(
        "benchmarks/<uuid:pk>/execute/",
        views.benchmark_execute,
        name="benchmark_execute",
    ),
    # Optimizations
    path("optimizations/", views.optimization_list, name="optimization_list"),
    path(
        "optimizations/create/", views.optimization_create, name="optimization_create"
    ),
    path(
        "optimizations/<uuid:pk>/",
        views.optimization_detail,
        name="optimization_detail",
    ),
    path(
        "optimizations/<uuid:pk>/update/",
        views.optimization_update,
        name="optimization_update",
    ),
    path(
        "optimizations/<uuid:pk>/start/",
        views.optimization_start,
        name="optimization_start",
    ),
    path(
        "optimizations/<uuid:pk>/complete/",
        views.optimization_complete,
        name="optimization_complete",
    ),
    path(
        "optimizations/<uuid:pk>/verify/",
        views.optimization_verify,
        name="optimization_verify",
    ),
    # Cache
    path("cache/", views.cache_list, name="cache_list"),
    path("cache/create/", views.cache_create, name="cache_create"),
    path("cache/<uuid:pk>/", views.cache_detail, name="cache_detail"),
    path("cache/<uuid:pk>/update/", views.cache_update, name="cache_update"),
    path(
        "cache/<uuid:pk>/metrics/create/",
        views.cache_metrics_create,
        name="cache_metrics_create",
    ),
    # Queues
    path("queues/", views.queue_list, name="queue_list"),
    path("queues/create/", views.queue_create, name="queue_create"),
    path("queues/<uuid:pk>/", views.queue_detail, name="queue_detail"),
    path("queues/<uuid:pk>/update/", views.queue_update, name="queue_update"),
    path(
        "queues/<uuid:pk>/metrics/create/",
        views.queue_metrics_create,
        name="queue_metrics_create",
    ),
    # Database
    path("databases/", views.database_list, name="database_list"),
    path("databases/create/", views.database_create, name="database_create"),
    path("databases/<uuid:pk>/", views.database_detail, name="database_detail"),
    path("databases/<uuid:pk>/update/", views.database_update, name="database_update"),
    path(
        "databases/<uuid:pk>/metrics/create/",
        views.database_metrics_create,
        name="database_metrics_create",
    ),
    # Alerts
    path("alerts/", views.alert_list, name="alert_list"),
    path("alerts/<uuid:pk>/", views.alert_detail, name="alert_detail"),
    path(
        "alerts/<uuid:pk>/acknowledge/",
        views.alert_acknowledge,
        name="alert_acknowledge",
    ),
    path("alerts/<uuid:pk>/resolve/", views.alert_resolve, name="alert_resolve"),
    # Reports
    path("reports/", views.report_list, name="report_list"),
    path("reports/create/", views.report_create, name="report_create"),
    path("reports/<uuid:pk>/", views.report_detail, name="report_detail"),
    path("reports/<uuid:pk>/download/", views.report_download, name="report_download"),
]
