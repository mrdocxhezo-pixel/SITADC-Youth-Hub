"""
Seed data for the membership management module.

This module is the single source of truth for the default membership
configuration installed by the ``seed_memberships`` management command.
"""

from __future__ import annotations

from decimal import Decimal
from typing import cast

from django.utils.translation import gettext_lazy as _


def _translated(value: str) -> str:
    """Keep lazy translation at runtime while exposing seed text as strings."""
    return cast(str, _(value))


class MembershipSeed:
    """Plain-data description of a default membership configuration row."""

    def __init__(
        self,
        code: str,
        name: str,
        description: str = "",
        sort_order: int = 0,
        **extra,
    ) -> None:
        self.code = code
        self.name = name
        self.description = description
        self.sort_order = sort_order
        self.extra = extra


DEFAULT_MEMBERSHIP_STATUSES: tuple[MembershipSeed, ...] = (
    MembershipSeed(
        "PENDING",
        _translated("Pending"),
        _translated("Application received; not yet active."),
        0,
    ),
    MembershipSeed(
        "ACTIVE",
        _translated("Active"),
        _translated("Full membership active and in good standing."),
        1,
    ),
    MembershipSeed(
        "INACTIVE",
        _translated("Inactive"),
        _translated("Membership temporarily inactive."),
        2,
    ),
    MembershipSeed(
        "SUSPENDED",
        _translated("Suspended"),
        _translated("Membership suspended pending review."),
        3,
    ),
    MembershipSeed(
        "EXPIRED",
        _translated("Expired"),
        _translated("Membership lapsed and requires renewal."),
        4,
    ),
    MembershipSeed(
        "TERMINATED",
        _translated("Terminated"),
        _translated("Membership permanently terminated."),
        5,
    ),
    MembershipSeed(
        "ARCHIVED",
        _translated("Archived"),
        _translated("Membership archived for record keeping."),
        6,
    ),
)

DEFAULT_MEMBERSHIP_CATEGORIES: tuple[MembershipSeed, ...] = (
    MembershipSeed(
        "founding",
        _translated("Founding Member"),
        _translated("Original founding members of the SITADC Youth Organization."),
        0,
        leadership_eligible=True,
        voting_rights=True,
        default_fee_amount=Decimal("150.00"),
        renewal_fee_amount=Decimal("100.00"),
    ),
    MembershipSeed(
        "ordinary",
        _translated("Ordinary Member"),
        _translated("Regular active members of the organization."),
        1,
        leadership_eligible=True,
        voting_rights=True,
        default_fee_amount=Decimal("100.00"),
        renewal_fee_amount=Decimal("80.00"),
    ),
    MembershipSeed(
        "student",
        _translated("Student Member"),
        _translated("Students enrolled in a recognized institution."),
        2,
        leadership_eligible=False,
        voting_rights=True,
        default_fee_amount=Decimal("50.00"),
        renewal_fee_amount=Decimal("40.00"),
    ),
    MembershipSeed(
        "associate",
        _translated("Associate Member"),
        _translated("Associate members with limited rights."),
        3,
        leadership_eligible=False,
        voting_rights=False,
        default_fee_amount=Decimal("60.00"),
        renewal_fee_amount=Decimal("50.00"),
    ),
    MembershipSeed(
        "honorary",
        _translated("Honorary Member"),
        _translated("Honorary members recognized for outstanding contribution."),
        4,
        leadership_eligible=False,
        voting_rights=True,
        default_fee_amount=Decimal("0.00"),
        renewal_fee_amount=Decimal("0.00"),
    ),
)

DEFAULT_MEMBERSHIP_TYPES: tuple[MembershipSeed, ...] = (
    MembershipSeed(
        "individual",
        _translated("Individual"),
        _translated("Individual membership."),
        0,
    ),
    MembershipSeed(
        "institutional",
        _translated("Institutional"),
        _translated("Organization or institution membership."),
        1,
    ),
    MembershipSeed(
        "community",
        _translated("Community"),
        _translated("Community-based membership."),
        2,
    ),
)

DEFAULT_MEMBERSHIP_LEVELS: tuple[MembershipSeed, ...] = (
    MembershipSeed(
        "national",
        _translated("National"),
        _translated("National level membership."),
        0,
    ),
    MembershipSeed(
        "regional",
        _translated("Regional"),
        _translated("Regional level membership."),
        1,
    ),
    MembershipSeed(
        "district",
        _translated("District"),
        _translated("District level membership."),
        2,
    ),
    MembershipSeed(
        "community",
        _translated("Community"),
        _translated("Community level membership."),
        3,
    ),
    MembershipSeed(
        "team", _translated("Team"), _translated("Team level membership."), 4
    ),
)

DEFAULT_MEMBERSHIP_BENEFITS: tuple[MembershipSeed, ...] = (
    MembershipSeed(
        "voting",
        _translated("Voting Rights"),
        _translated("Right to vote in organizational elections."),
        0,
    ),
    MembershipSeed(
        "leadership",
        _translated("Leadership Eligibility"),
        _translated("Eligibility to hold leadership positions."),
        1,
    ),
    MembershipSeed(
        "training",
        _translated("Training Access"),
        _translated("Access to organizational training programs."),
        2,
    ),
    MembershipSeed(
        "networking",
        _translated("Networking Opportunities"),
        _translated("Participation in networking events."),
        3,
    ),
    MembershipSeed(
        "resources",
        _translated("Resource Access"),
        _translated("Access to organizational resources."),
        4,
    ),
    MembershipSeed(
        "mentorship",
        _translated("Mentorship Program"),
        _translated("Access to mentorship programs."),
        5,
    ),
)
