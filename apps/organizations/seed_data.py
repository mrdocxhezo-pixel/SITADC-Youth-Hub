"""
Seed data for the organizational structure module.

This module is the single source of truth for the configurable organizational
catalogues (levels and position classifications).  The ``seed_organization_structure``
management command consumes this module so the seeded state never drifts.
"""

from __future__ import annotations


class LevelSeed:
    """Plain-data description of a default organizational level."""

    def __init__(self, code: str, name: str, sort_order: int, description: str) -> None:
        self.code = code
        self.name = name
        self.sort_order = sort_order
        self.description = description


class ClassificationSeed:
    """Plain-data description of a default position classification."""

    def __init__(self, code: str, name: str, sort_order: int, description: str) -> None:
        self.code = code
        self.name = name
        self.sort_order = sort_order
        self.description = description


DEFAULT_LEVELS: tuple[LevelSeed, ...] = (
    LevelSeed(
        "national",
        "National",
        10,
        "The national level of the organization.",
    ),
    LevelSeed(
        "governance",
        "Governance",
        20,
        "Governance bodies (General Assembly, Board of Trustees, National "
        "Executive Committee).",
    ),
    LevelSeed(
        "executive",
        "Executive Management",
        30,
        "Executive management and the executive office.",
    ),
    LevelSeed(
        "directorate",
        "Directorate",
        40,
        "Strategic functional directorates.",
    ),
    LevelSeed(
        "department",
        "Department",
        50,
        "Departments operating within directorates.",
    ),
    LevelSeed(
        "region",
        "Region",
        60,
        "Geographical regions.",
    ),
    LevelSeed(
        "district",
        "District",
        70,
        "Geographical districts within a region.",
    ),
    LevelSeed(
        "community",
        "Community",
        80,
        "Communities within a district.",
    ),
    LevelSeed(
        "team",
        "Team",
        90,
        "Operational delivery teams within a community.",
    ),
)

DEFAULT_CLASSIFICATIONS: tuple[ClassificationSeed, ...] = (
    ClassificationSeed(
        "executive-leadership",
        "Executive Leadership",
        10,
        "Executive and governance leadership positions.",
    ),
    ClassificationSeed(
        "senior-management",
        "Senior Management",
        20,
        "Senior management positions.",
    ),
    ClassificationSeed(
        "middle-management",
        "Middle Management",
        30,
        "Middle management positions.",
    ),
    ClassificationSeed(
        "regional-leadership",
        "Regional Leadership",
        40,
        "Leadership positions at the regional level.",
    ),
    ClassificationSeed(
        "district-leadership",
        "District Leadership",
        50,
        "Leadership positions at the district level.",
    ),
    ClassificationSeed(
        "community-leadership",
        "Community Leadership",
        60,
        "Leadership positions at the community level.",
    ),
    ClassificationSeed(
        "team-leadership",
        "Team Leadership",
        70,
        "Leadership positions at the team level.",
    ),
    ClassificationSeed(
        "technical-staff",
        "Technical Staff",
        80,
        "Technical specialist positions.",
    ),
    ClassificationSeed(
        "support-staff",
        "Support Staff",
        90,
        "Administrative and support positions.",
    ),
    ClassificationSeed(
        "volunteer",
        "Volunteer",
        100,
        "Volunteer positions.",
    ),
)
