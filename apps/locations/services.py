"""
Business logic / service functions for the geographic hierarchy.

These functions are the single authoritative entry point that every module
(forms, views, filters, reports, dashboards) uses to retrieve geographic data,
so that the hierarchy stays database-driven and never hard-coded.
"""

from django.db.models import QuerySet
from django.utils import timezone

from .models import (
    Constituency,
    Country,
    District,
    Province,
    Ward,
)


def get_countries(*, active_only: bool = True) -> QuerySet:
    """Return countries, optionally only active ones."""
    qs = Country.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("sort_order", "name")


def get_provinces(*, country=None, active_only: bool = True) -> QuerySet:
    """Return provinces, optionally filtered by country."""
    qs = Province.objects.select_related("country").all()
    if country is not None:
        qs = qs.filter(country=country)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("sort_order", "name")


def get_districts(*, province=None, active_only: bool = True) -> QuerySet:
    """Return districts, optionally filtered by province."""
    qs = District.objects.select_related("province").all()
    if province is not None:
        qs = qs.filter(province=province)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("sort_order", "name")


def get_constituencies(*, district=None, active_only: bool = True) -> QuerySet:
    """Return constituencies, optionally filtered by district."""
    qs = Constituency.objects.select_related("district").all()
    if district is not None:
        qs = qs.filter(district=district)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("sort_order", "name")


def get_wards(*, constituency=None, active_only: bool = True) -> QuerySet:
    """Return wards, optionally filtered by constituency."""
    qs = Ward.objects.select_related("constituency").all()
    if constituency is not None:
        qs = qs.filter(constituency=constituency)
    if active_only:
        qs = qs.filter(is_active=True)
    return qs.order_by("sort_order", "name")


def resolve_location(province=None, district=None, constituency=None, ward=None):
    """
    Validate that the given hierarchy chain is consistent.

    Each argument may be a model instance, a pk (str/uuid) or None. Returns a
    dict with the resolved objects, or raises ``ValueError`` on mismatch.
    """
    from .resolvers import resolve_location as _resolve

    return _resolve(
        province=province,
        district=district,
        constituency=constituency,
        ward=ward,
    )


def default_country():
    """Return the default country (first active, or the 'ZM' country)."""
    zambia = Country.objects.filter(code__iexact="ZM", is_active=True).first()
    if zambia is not None:
        return zambia
    return get_countries().first()


def default_provinces_for(country=None):
    """Convenience wrapper used by forms when a country-first cascade is needed."""
    country = country or default_country()
    return get_provinces(country=country)
