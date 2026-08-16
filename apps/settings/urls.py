"""URL configuration for Settings."""

from django.urls import path
from . import views

app_name = "settings"

urlpatterns = [
    # Dashboard
    path("", views.SettingsDashboardView.as_view(), name="settings_dashboard"),

    # User settings
    path("account/", views.AccountSettingsView.as_view(), name="account"),
    path("appearance/", views.AppearanceSettingsView.as_view(), name="appearance"),
    path("notifications/", views.NotificationSettingsView.as_view(), name="notifications"),
    path("security/", views.SecuritySettingsView.as_view(), name="security"),
    path("privacy/", views.PrivacySettingsView.as_view(), name="privacy"),
    path("sessions/", views.SessionsSettingsView.as_view(), name="sessions"),
    path("language-region/", views.LanguageRegionSettingsView.as_view(), name="language_region"),
    path("accessibility/", views.AccessibilitySettingsView.as_view(), name="accessibility"),

    # Admin settings
    path("organization/", views.OrganizationSettingsView.as_view(), name="organization"),
    path("users-roles/", views.UserRoleSettingsView.as_view(), name="users_roles"),
    path("reporting/", views.ReportingSettingsView.as_view(), name="reporting"),
    path("system/", views.SystemSettingsView.as_view(), name="system"),
    path("data-storage/", views.DataStorageSettingsView.as_view(), name="data_storage"),
    path("audit/", views.AuditComplianceSettingsView.as_view(), name="audit"),
    path("integrations/", views.IntegrationsSettingsView.as_view(), name="integrations"),

    # Help
    path("help/", views.HelpSupportSettingsView.as_view(), name="help"),

    # AJAX endpoints
    path("ajax/save/<str:section>/", views.settings_ajax_save, name="ajax_save"),
    path("ajax/section/<str:section>/", views.settings_get_section, name="ajax_section"),
]