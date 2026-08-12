"""Idempotent loader for beneficiary configuration and numbering schemes."""

from __future__ import annotations

from django.db import transaction

from apps.references.models import ReferenceNumberScheme

from .models import BeneficiaryReferenceData
from .seed_data import (
    DEFAULT_REFERENCE_DATA,
    DEFAULT_REFERENCE_SCHEME_MODULE,
    DEFAULT_REFERENCE_SCHEMES,
)


@transaction.atomic
def seed_beneficiary_reference_data() -> dict[str, int]:
    """Install defaults without deleting administrator-defined configuration."""
    stats = {"reference_data": 0, "schemes": 0}
    for row in DEFAULT_REFERENCE_DATA:
        _, created = BeneficiaryReferenceData.objects.update_or_create(
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
    for code, name, prefix in DEFAULT_REFERENCE_SCHEMES:
        _, created = ReferenceNumberScheme.objects.update_or_create(
            code=code,
            defaults=_scheme_defaults(code, name, prefix),
        )
        stats["schemes"] += int(created)
    return stats


def _scheme_defaults(code: str, name: str, prefix: str) -> dict:
    return {
        "name": name,
        "module": DEFAULT_REFERENCE_SCHEME_MODULE,
        "record_type": code,
        "description": f"Centralized references for {name.lower()} records.",
        "prefix": prefix,
        "pattern": "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        "organization_code": "SITADC",
        "sequence_length": 6,
        "start_value": 1,
        "reset_period": "NEVER",
        "status": "ACTIVE",
        "is_default_for_module": False,
        "is_default_for_record_type": True,
        "is_fallback": False,
        "is_active": True,
    }
