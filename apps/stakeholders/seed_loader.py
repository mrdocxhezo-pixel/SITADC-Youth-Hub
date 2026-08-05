"""Idempotent loader for stakeholder configuration and numbering schemes."""

from __future__ import annotations

from django.db import transaction

from apps.references.models import ReferenceNumberScheme

from .models import StakeholderPerformanceDimension, StakeholderReferenceData
from .seed_data import (
    DEFAULT_PERFORMANCE_DIMENSIONS,
    DEFAULT_REFERENCE_DATA,
    DEFAULT_REFERENCE_SCHEMES,
    reference_scheme_defaults,
)


@transaction.atomic
def seed_stakeholder_reference_data() -> dict[str, int]:
    """Install defaults without deleting administrator-defined configuration."""
    stats = {"reference_data": 0, "dimensions": 0, "schemes": 0}
    for row in DEFAULT_REFERENCE_DATA:
        _, created = StakeholderReferenceData.objects.update_or_create(
            kind=row["kind"],
            code=row["code"],
            defaults={
                "name": row["name"],
                "metadata": row["metadata"],
                "order": row["order"],
                "active": True,
            },
        )
        stats["reference_data"] += int(created)
    for order, (code, name, weight) in enumerate(
        DEFAULT_PERFORMANCE_DIMENSIONS, start=1
    ):
        _, created = StakeholderPerformanceDimension.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "weight": weight,
                "minimum_score": 0,
                "maximum_score": 100,
                "active": True,
                "order": order,
            },
        )
        stats["dimensions"] += int(created)
    for code, name, prefix in DEFAULT_REFERENCE_SCHEMES:
        _, created = ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults=reference_scheme_defaults(code, name, prefix),
        )
        stats["schemes"] += int(created)
    return stats
