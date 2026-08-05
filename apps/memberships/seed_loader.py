"""
Loader for default membership configuration data.

Kept separate from ``seed_data`` (declarative definitions) so the management
command and tests can reuse the same idempotent seeding logic.
"""

from __future__ import annotations

from apps.memberships.models import (
    MembershipBenefit,
    MembershipCategory,
    MembershipLevel,
    MembershipStatus,
    MembershipType,
)
from apps.memberships.seed_data import (
    DEFAULT_MEMBERSHIP_BENEFITS,
    DEFAULT_MEMBERSHIP_CATEGORIES,
    DEFAULT_MEMBERSHIP_LEVELS,
    DEFAULT_MEMBERSHIP_STATUSES,
    DEFAULT_MEMBERSHIP_TYPES,
)


def _upsert(model, seeds) -> int:
    created = 0
    for seed in seeds:
        _, was_created = model.objects.update_or_create(
            code=seed.code,
            defaults={
                "name": seed.name,
                "description": seed.description,
                "sort_order": seed.sort_order,
                **seed.extra,
            },
        )
        if was_created:
            created += 1
    return created


def seed_membership_configuration() -> dict:
    """Idempotently install the default membership configuration rows."""
    return {
        "statuses": _upsert(MembershipStatus, DEFAULT_MEMBERSHIP_STATUSES),
        "categories": _upsert(MembershipCategory, DEFAULT_MEMBERSHIP_CATEGORIES),
        "types": _upsert(MembershipType, DEFAULT_MEMBERSHIP_TYPES),
        "levels": _upsert(MembershipLevel, DEFAULT_MEMBERSHIP_LEVELS),
        "benefits": _upsert(MembershipBenefit, DEFAULT_MEMBERSHIP_BENEFITS),
    }
