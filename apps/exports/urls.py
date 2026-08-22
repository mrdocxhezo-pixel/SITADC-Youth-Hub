"""URL configuration for the Export Engine (Phase 27)."""

from django.urls import path

from . import views

app_name = "exports"

urlpatterns = [
    path("", views.ExportHomeView.as_view(), name="home"),
    path("create/", views.ExportCreateView.as_view(), name="create"),
    path("history/", views.ExportHistoryView.as_view(), name="history"),
    path("history/<uuid:pk>/", views.ExportDetailView.as_view(), name="detail"),
    path(
        "history/<uuid:pk>/download/",
        views.ExportDownloadView.as_view(),
        name="download",
    ),
    path(
        "history/<uuid:pk>/cancel/",
        views.ExportCancelView.as_view(),
        name="cancel",
    ),
    path(
        "history/<uuid:pk>/regenerate/",
        views.ExportRegenerateView.as_view(),
        name="regenerate",
    ),
    path("settings/", views.ExportSettingsView.as_view(), name="settings"),
    path("templates/", views.ExportTemplateListView.as_view(), name="templates"),
    # Analytics
    path("analytics/", views.ExportAnalyticsView.as_view(), name="analytics"),
    path("analytics/data/", views.ExportAnalyticsDataView.as_view(), name="analytics_data"),
    path(
        "analytics/template/<uuid:pk>/",
        views.ExportTemplateAnalyticsView.as_view(),
        name="template_analytics",
    ),
]
