from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls", namespace="core")),
    path("leadership/", include("apps.leadership.urls", namespace="leadership")),
    path("volunteers/", include("apps.volunteers.urls", namespace="volunteers")),
    path("memberships/", include("apps.memberships.urls", namespace="memberships")),
    path("stakeholders/", include("apps.stakeholders.urls", namespace="stakeholders")),
    path("programs/", include("apps.programs.urls", namespace="programs")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)  # type: ignore

handler400 = "django.views.defaults.bad_request"
handler403 = "django.views.defaults.permission_denied"
handler404 = "django.views.defaults.page_not_found"
handler500 = "django.views.defaults.server_error"
