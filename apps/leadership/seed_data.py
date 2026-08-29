"""
Seed data for the leadership management module.

This module is the single source of truth for the default leadership
reference data installed by the ``seed_leadership_reference_data`` management
command: organizational leadership levels and the standard leadership
positions defined by the Phase 11 roadmap.
"""

from __future__ import annotations

from .constants import LeadershipLevel


class LeadershipLevelSeed:
    """Plain-data description of a leadership level."""

    def __init__(self, code: str, name: str, description: str, sort_order: int) -> None:
        self.code = code
        self.name = name
        self.description = description
        self.sort_order = sort_order


LEADERSHIP_LEVELS: tuple[LeadershipLevelSeed, ...] = (
    LeadershipLevelSeed(
        LeadershipLevel.BOARD_OF_TRUSTEES,
        "Board of Trustees",
        "Highest governance body overseeing the organization.",
        10,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "National Executive Committee",
        "National executive governance and oversight.",
        20,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Executive Management",
        "Executive leadership responsible for strategic direction.",
        30,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.DIRECTORATE,
        "Directorate",
        "Functional directorate leadership.",
        40,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Regional Coordinator",
        "Regional leadership overseeing districts.",
        50,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.DISTRICT_COORDINATOR,
        "District Coordinator",
        "District leadership overseeing communities.",
        60,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.COMMUNITY_COORDINATOR,
        "Community Coordinator",
        "Community leadership supervising team leaders.",
        70,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.TEAM_LEADER,
        "Team Leader",
        "Team leadership supervising operational teams.",
        80,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.REPORT_AUTHOR,
        "Report Author",
        "Personnel authorized to author official reports.",
        90,
    ),
)


class LeadershipPositionSeed:
    """Plain-data description of a standard leadership position."""

    def __init__(self, title: str, level: str, description: str) -> None:
        self.title = title
        self.level = level
        self.description = description


LEADERSHIP_POSITIONS: tuple[LeadershipPositionSeed, ...] = (
    LeadershipPositionSeed(
        "President",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Overall organizational leadership and representation.",
    ),
    LeadershipPositionSeed(
        "Vice President",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Supports the President and acts in their absence.",
    ),
    LeadershipPositionSeed(
        "Executive Director",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Chief executive responsible for day-to-day operations.",
    ),
    LeadershipPositionSeed(
        "Executive Secretary",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Administrative head supporting executive governance.",
    ),
    LeadershipPositionSeed(
        "Secretary General",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Coordinates the National Executive Committee and secretariat.",
    ),
    LeadershipPositionSeed(
        "Board Chairperson",
        LeadershipLevel.BOARD_OF_TRUSTEES,
        "Chairs the Board of Trustees and leads governance oversight.",
    ),
    LeadershipPositionSeed(
        "Board Secretary",
        LeadershipLevel.BOARD_OF_TRUSTEES,
        "Records and administers board meetings and governance records.",
    ),
    LeadershipPositionSeed(
        "Board Member",
        LeadershipLevel.BOARD_OF_TRUSTEES,
        "Provides governance oversight and decision-making.",
    ),
    LeadershipPositionSeed(
        "Director",
        LeadershipLevel.DIRECTORATE,
        "Leads a directorate and reports to the Executive Director.",
    ),
    LeadershipPositionSeed(
        "Deputy Director",
        LeadershipLevel.DIRECTORATE,
        "Deputises for a Director and oversees programmes.",
    ),
    LeadershipPositionSeed(
        "Regional Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates implementation within an assigned region.",
    ),
    LeadershipPositionSeed(
        "District Coordinator",
        LeadershipLevel.DISTRICT_COORDINATOR,
        "Coordinates implementation within an assigned district.",
    ),
    LeadershipPositionSeed(
        "Community Coordinator",
        LeadershipLevel.COMMUNITY_COORDINATOR,
        "Coordinates implementation within an assigned community.",
    ),
    LeadershipPositionSeed(
        "Team Leader",
        LeadershipLevel.TEAM_LEADER,
        "Leads a delivery team within a community.",
    ),
    LeadershipPositionSeed(
        "Program Manager",
        LeadershipLevel.DIRECTORATE,
        "Manages the delivery of one or more programmes.",
    ),
    LeadershipPositionSeed(
        "Project Officer",
        LeadershipLevel.DIRECTORATE,
        "Implements project activities and reports on progress.",
    ),
    LeadershipPositionSeed(
        "Finance Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages financial records, budgets and reporting.",
    ),
    LeadershipPositionSeed(
        "MEAL Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages monitoring, evaluation, accountability and learning.",
    ),
    LeadershipPositionSeed(
        "Communications Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages communications, media and public relations.",
    ),
    LeadershipPositionSeed(
        "Membership Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages membership registration and administration.",
    ),
    LeadershipPositionSeed(
        "Partnerships Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages partners, sponsors, donors and stakeholders.",
    ),
    LeadershipPositionSeed(
        "Research Officer",
        LeadershipLevel.DIRECTORATE,
        "Supports research, innovation and knowledge management.",
    ),
    LeadershipPositionSeed(
        "Training Officer",
        LeadershipLevel.DIRECTORATE,
        "Manages training and capacity development.",
    ),
    LeadershipPositionSeed(
        "Resource Mobilization Officer",
        LeadershipLevel.DIRECTORATE,
        "Mobilizes financial and non-financial resources.",
    ),
    LeadershipPositionSeed(
        "Quality Assurance Officer",
        LeadershipLevel.DIRECTORATE,
        "Ensures quality standards across programmes and operations.",
    ),
)
