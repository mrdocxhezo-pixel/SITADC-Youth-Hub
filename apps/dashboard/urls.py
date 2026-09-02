from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),
    path("activity/", views.DashboardActivityLogView.as_view(), name="activity_log"),
    path("personalize/", views.dashboard_personalize_view, name="personalize"),
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
        "preferences/ajax/",
        views.dashboard_preferences_ajax,
        name="preferences_ajax",
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
