"""URL configuration for the Enterprise Search module."""

from django.urls import path

from . import views

app_name = "search"

urlpatterns = [
    path("", views.SearchHomeView.as_view(), name="home"),
    path("export/", views.ExportSearchView.as_view(), name="export"),
    path("saved/", views.SavedSearchListView.as_view(), name="saved_list"),
    path("saved/save/", views.SavedSearchCreateView.as_view(), name="saved_create"),
    path(
        "saved/<uuid:pk>/delete/",
        views.SavedSearchDeleteView.as_view(),
        name="saved_delete",
    ),
    path(
        "saved/<uuid:pk>/run/",
        views.SavedSearchRunView.as_view(),
        name="saved_run",
    ),
    path("audit/", views.SearchAuditView.as_view(), name="audit"),
]
