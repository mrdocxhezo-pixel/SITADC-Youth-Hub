"""URL configuration for the geographic locations module."""

from django.urls import path

from . import views

app_name = "locations"

# JSON API endpoints for cascading dropdowns (used across the whole system)
api_patterns = [
    path("api/countries/", views.CountriesJsonView.as_view(), name="api_countries"),
    path("api/provinces/", views.ProvincesJsonView.as_view(), name="api_provinces"),
    path("api/districts/", views.DistrictsJsonView.as_view(), name="api_districts"),
    path(
        "api/constituencies/",
        views.ConstituenciesJsonView.as_view(),
        name="api_constituencies",
    ),
    path("api/wards/", views.WardsJsonView.as_view(), name="api_wards"),
]

# Management interface
management_patterns = [
    path("", views.CountryListView.as_view(), name="country_list"),
    path("countries/new/", views.CountryCreateView.as_view(), name="country_create"),
    path(
        "countries/<uuid:pk>/edit/",
        views.CountryUpdateView.as_view(),
        name="country_update",
    ),
    path("provinces/", views.ProvinceListView.as_view(), name="province_list"),
    path("provinces/new/", views.ProvinceCreateView.as_view(), name="province_create"),
    path(
        "provinces/<uuid:pk>/edit/",
        views.ProvinceUpdateView.as_view(),
        name="province_update",
    ),
    path("districts/", views.DistrictListView.as_view(), name="district_list"),
    path("districts/new/", views.DistrictCreateView.as_view(), name="district_create"),
    path(
        "districts/<uuid:pk>/edit/",
        views.DistrictUpdateView.as_view(),
        name="district_update",
    ),
    path(
        "constituencies/",
        views.ConstituencyListView.as_view(),
        name="constituency_list",
    ),
    path(
        "constituencies/new/",
        views.ConstituencyCreateView.as_view(),
        name="constituency_create",
    ),
    path(
        "constituencies/<uuid:pk>/edit/",
        views.ConstituencyUpdateView.as_view(),
        name="constituency_update",
    ),
    path("wards/", views.WardListView.as_view(), name="ward_list"),
    path("wards/new/", views.WardCreateView.as_view(), name="ward_create"),
    path(
        "wards/<uuid:pk>/edit/",
        views.WardUpdateView.as_view(),
        name="ward_update",
    ),
]

urlpatterns = api_patterns + management_patterns
