from django.urls import include, path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("accounts/", include("apps.accounts.urls")),
    path("rbac/", include("apps.rbac.urls")),
    path("organizations/", include("apps.organizations.urls")),
    path("references/", include("apps.references.urls")),
]
