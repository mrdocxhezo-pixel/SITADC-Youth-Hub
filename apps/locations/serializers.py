"""
Lightweight serialization helpers for the geographic models.

These do not require Django REST Framework: they return small, clean
dictionaries suitable for ``JsonResponse`` used by cascading dropdowns.
"""

from django.core.serializers.json import DjangoJSONEncoder

from .models import (
    Constituency,
    Country,
    District,
    Province,
    Ward,
)


def country_json(country) -> dict:
    return {"id": str(country.pk), "name": country.name, "code": country.code}


def province_json(province) -> dict:
    return {"id": str(province.pk), "name": province.name, "code": province.code}


def district_json(district) -> dict:
    return {"id": str(district.pk), "name": district.name, "code": district.code}


def constituency_json(constituency) -> dict:
    return {
        "id": str(constituency.pk),
        "name": constituency.name,
        "code": constituency.code,
    }


def ward_json(ward) -> dict:
    return {"id": str(ward.pk), "name": ward.name, "code": ward.code}


SERIALIZERS = {
    Country: country_json,
    Province: province_json,
    District: district_json,
    Constituency: constituency_json,
    Ward: ward_json,
}


def serialize(model, obj) -> dict:
    """Return the lightweight JSON dict for a geographic object."""
    return SERIALIZERS[model](obj)


class GeographicJSONEncoder(DjangoJSONEncoder):
    """JSON encoder that can handle geographic model instances."""
