"""
Resolution and consistency helpers for the geographic hierarchy.

Ensures that a province -> district -> constituency -> ward chain is valid,
so records can never be assigned to a child that belongs to a different parent.
"""

from django.core.exceptions import ObjectDoesNotExist

from .models import (
    Constituency,
    District,
    Province,
    Ward,
)


def _coerce(model, value):
    if value is None:
        return None
    if isinstance(value, model):
        return value
    try:
        return model.objects.get(pk=value)
    except (ObjectDoesNotExist, TypeError, ValueError):
        return None


def resolve_location(province=None, district=None, constituency=None, ward=None):
    """
    Resolve and validate a location chain.

    Returns ``{"province": ..., "district": ..., "constituency": ..., "ward": ...}``
    with each resolved object or ``None``. Raises ``ValueError`` when a child
    does not belong to its given parent.
    """
    province_obj = _coerce(Province, province)
    district_obj = _coerce(District, district)
    constituency_obj = _coerce(Constituency, constituency)
    ward_obj = _coerce(Ward, ward)

    if district_obj and province_obj and district_obj.province_id != province_obj.pk:
        raise ValueError("District does not belong to the selected province.")

    if (
        constituency_obj
        and district_obj
        and constituency_obj.district_id != district_obj.pk
    ):
        raise ValueError("Constituency does not belong to the selected district.")

    if (
        ward_obj
        and constituency_obj
        and ward_obj.constituency_id != constituency_obj.pk
    ):
        raise ValueError("Ward does not belong to the selected constituency.")

    return {
        "province": province_obj,
        "district": district_obj,
        "constituency": constituency_obj,
        "ward": ward_obj,
    }
