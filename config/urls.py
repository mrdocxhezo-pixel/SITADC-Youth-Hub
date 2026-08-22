from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls", namespace="core")),
    path("dashboard/", include("apps.dashboard.urls", namespace="dashboard")),
    path("leadership/", include("apps.leadership.urls", namespace="leadership")),
    path("volunteers/", include("apps.volunteers.urls", namespace="volunteers")),
    path("memberships/", include("apps.memberships.urls", namespace="memberships")),
    path("stakeholders/", include("apps.stakeholders.urls", namespace="stakeholders")),
    path("programs/", include("apps.programs.urls", namespace="programs")),
    path(
        "beneficiaries/", include("apps.beneficiaries.urls", namespace="beneficiaries")
    ),
    path("meal/", include("apps.meal.urls", namespace="meal")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
    path(
        "report-instances/",
        include("apps.report_instances.urls", namespace="report_instances"),
    ),
    path("reviews/", include("apps.reviews.urls", namespace="reviews")),
    path("documents/", include("apps.documents.urls", namespace="documents")),
    path("registers/", include("apps.registers.urls", namespace="registers")),
    path("meetings/", include("apps.meetings.urls", namespace="meetings")),
    path(
        "notifications/", include("apps.notifications.urls", namespace="notifications")
    ),
    path("governance/", include("apps.governance.urls", namespace="governance")),
    path(
        "communications/",
        include("apps.communications.urls", namespace="communications"),
    ),
    path("system-settings/", include("apps.system_settings.urls", namespace="system_settings")),
    path("settings/", include("apps.settings.urls", namespace="settings")),
    path("configuration/", include("apps.configuration.urls", namespace="configuration")),
    path("organizations/", include("apps.organizations.urls", namespace="organizations")),
    path("references/", include("apps.references.urls", namespace="references")),
    path("rbac/", include("apps.rbac.urls", namespace="rbac")),
    path("search/", include("apps.search.urls", namespace="search")),
    path("exports/", include("apps.exports.urls", namespace="exports")),
    path("finance/", include("apps.finance.urls", namespace="finance")),
    path("security/", include("apps.security.urls", namespace="security")),
    path("accessibility/", include("apps.accessibility.urls", namespace="accessibility")),
    path("performance/", include("apps.performance.urls", namespace="performance")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # type: ignore

handler400 = "django.views.defaults.bad_request"
handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"