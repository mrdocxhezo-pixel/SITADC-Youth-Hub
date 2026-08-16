from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path(
        "widget-data/<int:widget_id>/",
        views.dashboard_widget_data,
        name="widget_data",
    ),
    path(
        "widget-config/<str:config_type>/",
        views.dashboard_widget_config,
        name="widget_config",
    ),
    path(
        "configuration/",
        views.DashboardConfigurationView.as_view(),
        name="configuration",
    ),
    path(
        "widget-management/",
        views.DashboardWidgetManagementView.as_view(),
        name="widget_management",
    ),
]
