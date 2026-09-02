"""
Seed data for the organizational structure module.

This module is the single source of truth for the configurable organizational
catalogues (levels, position classifications, official directorates, departments,
program/technical management units, and positions). The ``seed_organization_structure``
management command consumes this module so the seeded state never drifts.
"""

from __future__ import annotations

from typing import NamedTuple


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


class UnitSeed:
    """Plain-data description of a default organizational unit."""

    def __init__(
        self,
        identifier: str,
        name: str,
        short_name: str,
        unit_type: str,
        level_code: str,
        description: str = "",
        parent_identifier: str | None = None,
    ) -> None:
        self.identifier = identifier
        self.name = name
        self.short_name = short_name
        self.unit_type = unit_type
        self.level_code = level_code
        self.description = description
        self.parent_identifier = parent_identifier


DEFAULT_LEVELS: tuple[LevelSeed, ...] = (
    # GOVERNANCE LEVELS
    LevelSeed(
        "general_assembly",
        "General Assembly",
        10,
        "The highest organizational governance level — the General Assembly.",
    ),
    LevelSeed(
        "governance",
        "Governance",
        20,
        "Governance bodies (General Assembly, Board of Directors / Board of Trustees, National Executive Committee).",
    ),
    # EXECUTIVE LEVELS
    LevelSeed(
        "executive",
        "Executive Management",
        30,
        "Executive management and the executive office.",
    ),
    # FUNCTIONAL/TECHNICAL LEVELS
    LevelSeed(
        "directorate",
        "Directorate",
        40,
        "Strategic functional directorates (17 total).",
    ),
    LevelSeed(
        "department",
        "Department",
        50,
        "Departments operating within directorates (10 operational departments).",
    ),
    LevelSeed(
        "program_technical_management",
        "Program and Technical Management",
        60,
        "Program and Technical Management positions beneath Directorates/Departments.",
    ),
    # GEOGRAPHICAL LEVELS
    LevelSeed(
        "region",
        "Region",
        70,
        "Geographical regions with Regional Coordinators.",
    ),
    LevelSeed(
        "district",
        "District",
        80,
        "Geographical districts within a region with District Coordinators.",
    ),
    LevelSeed(
        "community",
        "Community",
        90,
        "Communities within a district with Community Coordinators.",
    ),
    LevelSeed(
        "team",
        "Team",
        100,
        "Operational delivery teams within a community with Team Leaders.",
    ),
    LevelSeed(
        "volunteer_member",
        "Volunteers / Members",
        110,
        "Volunteers and Members — the operational/community participation level.",
    ),
)

DEFAULT_CLASSIFICATIONS: tuple[ClassificationSeed, ...] = (
    ClassificationSeed(
        "executive-leadership",
        "Executive Leadership",
        10,
        "Executive and governance leadership positions (General Assembly, Board, NEC, Executive Management).",
    ),
    ClassificationSeed(
        "directorate-leadership",
        "Directorate Leadership",
        20,
        "Leadership positions at the Directorate level (Directors, Deputy Directors).",
    ),
    ClassificationSeed(
        "department-leadership",
        "Department Leadership",
        30,
        "Leadership positions at the Department level (Heads of Department).",
    ),
    ClassificationSeed(
        "program-technical-management",
        "Program and Technical Management",
        40,
        "Program Coordinators, Technical Managers, Officers, and Assistants.",
    ),
    ClassificationSeed(
        "regional-leadership",
        "Regional Leadership",
        50,
        "Leadership positions at the regional level (Regional Coordinators and functional coordinators).",
    ),
    ClassificationSeed(
        "district-leadership",
        "District Leadership",
        60,
        "Leadership positions at the district level (District Coordinators).",
    ),
    ClassificationSeed(
        "community-leadership",
        "Community Leadership",
        70,
        "Leadership positions at the community level (Community Coordinators).",
    ),
    ClassificationSeed(
        "team-leadership",
        "Team Leadership",
        80,
        "Leadership positions at the team level (Team Leaders).",
    ),
    ClassificationSeed(
        "technical-staff",
        "Technical Staff",
        90,
        "Technical specialist positions.",
    ),
    ClassificationSeed(
        "support-staff",
        "Support Staff",
        100,
        "Administrative and support positions.",
    ),
    ClassificationSeed(
        "volunteer",
        "Volunteer",
        110,
        "Volunteer positions.",
    ),
    ClassificationSeed(
        "member",
        "Member",
        120,
        "Member positions.",
    ),
)

# 17 APPROVED SITADC DIRECTORATES
DEFAULT_DIRECTORATES: tuple[UnitSeed, ...] = (
    UnitSeed(
        "DIR-PROG-PROJ",
        "Directorate of Programs and Projects",
        "DPP",
        "DIRECTORATE",
        "directorate",
        "Oversees all organizational programs and project portfolios.",
    ),
    UnitSeed(
        "DIR-OPS-ADMIN",
        "Directorate of Operations and Administration",
        "DOA",
        "DIRECTORATE",
        "directorate",
        "Coordinates organizational operations, logistics, and administrative support.",
    ),
    UnitSeed(
        "DIR-FIN-RES",
        "Directorate of Finance and Resource",
        "DFR",
        "DIRECTORATE",
        "directorate",
        "Manages financial resources, treasury, accounting, and fiscal compliance.",
    ),
    UnitSeed(
        "DIR-MEAL",
        "Directorate of Monitoring, Evaluation, Accountability and Learning (MEAL)",
        "DMEAL",
        "DIRECTORATE",
        "directorate",
        "Directs monitoring, evaluation, accountability frameworks and organizational learning.",
    ),
    UnitSeed(
        "DIR-PART-RES",
        "Directorate of Partnerships and Resource Mobilization",
        "DPRM",
        "DIRECTORATE",
        "directorate",
        "Leads strategic partnerships, donor engagement, and grant mobilization.",
    ),
    UnitSeed(
        "DIR-COMM-MEDIA",
        "Directorate of Communications, Media and Public Relations",
        "DCMPR",
        "DIRECTORATE",
        "directorate",
        "Directs external communications, media engagement, branding, and PR.",
    ),
    UnitSeed(
        "DIR-MEMB-VOL",
        "Directorate of Membership and Volunteer Management",
        "DMVM",
        "DIRECTORATE",
        "directorate",
        "Oversees membership recruitment, volunteer mobilization, and engagement.",
    ),
    UnitSeed(
        "DIR-COMM-ENGAGE",
        "Directorate of Community Engagement and Outreach",
        "DCEO",
        "DIRECTORATE",
        "directorate",
        "Directs grassroots community engagement, local mobilization, and outreach.",
    ),
    UnitSeed(
        "DIR-TRAIN-CAP",
        "Directorate of Training and Capacity Development",
        "DTCD",
        "DIRECTORATE",
        "directorate",
        "Designs and executes leadership training and capacity building initiatives.",
    ),
    UnitSeed(
        "DIR-RES-INNOV",
        "Directorate of Research, Innovation and Technology",
        "DRIT",
        "DIRECTORATE",
        "directorate",
        "Directs applied research, innovation, and technological advancement.",
    ),
    UnitSeed(
        "DIR-HR-OD",
        "Directorate of Human Resources and Organizational Development",
        "DHROD",
        "DIRECTORATE",
        "directorate",
        "Directs human resource management and institutional strengthening.",
    ),
    UnitSeed(
        "DIR-QA-COMP",
        "Directorate of Quality Assurance and Compliance",
        "DQAC",
        "DIRECTORATE",
        "directorate",
        "Oversees operational quality standards, audits, and statutory compliance.",
    ),
    UnitSeed(
        "DIR-RISK-SAFE",
        "Directorate of Risk Management, Safeguarding and Ethics",
        "DRMSE",
        "DIRECTORATE",
        "directorate",
        "Leads organizational risk mitigation, safeguarding policies, and ethics oversight.",
    ),
    UnitSeed(
        "DIR-EDU-DIGI",
        "Directorate of Education, Digital Literacy and Innovation",
        "DEDLI",
        "DIRECTORATE",
        "directorate",
        "Directs youth education, digital literacy, and technology training.",
    ),
    UnitSeed(
        "DIR-ENTREP-SKILLS",
        "Directorate of Entrepreneurship, Employability and Skills Development",
        "DEESD",
        "DIRECTORATE",
        "directorate",
        "Oversees youth entrepreneurship, vocational training, and employability programs.",
    ),
    UnitSeed(
        "DIR-LEAD-CIVIC",
        "Directorate of Leadership, Civic Engagement and Community Development",
        "DLCECD",
        "DIRECTORATE",
        "directorate",
        "Directs civic engagement, democratic participation, and youth leadership.",
    ),
    UnitSeed(
        "DIR-HEALTH-WELL",
        "Directorate of Health, Well-being and Youth Empowerment",
        "DHWYE",
        "DIRECTORATE",
        "directorate",
        "Directs youth health initiatives, psychosocial well-being, and empowerment.",
    ),
)

# 10 APPROVED OPERATIONAL DEPARTMENTS
DEFAULT_DEPARTMENTS: tuple[UnitSeed, ...] = (
    UnitSeed(
        "DEPT-PPM",
        "Programs and Project Management Department",
        "PPMD",
        "DEPARTMENT",
        "department",
        "Operational department for program planning, project execution and field delivery.",
        parent_identifier="DIR-PROG-PROJ",
    ),
    UnitSeed(
        "DEPT-OAD",
        "Operations and Administration Department",
        "OAD",
        "DEPARTMENT",
        "department",
        "Operational department handling administration, facilities, assets, and logistics.",
        parent_identifier="DIR-OPS-ADMIN",
    ),
    UnitSeed(
        "DEPT-FGRM",
        "Finance, Grants and Resource Mobilization Department",
        "FGRMD",
        "DEPARTMENT",
        "department",
        "Operational department for budgeting, grants management, and financial accounting.",
        parent_identifier="DIR-FIN-RES",
    ),
    UnitSeed(
        "DEPT-MEAL",
        "Monitoring, Evaluation, Accountability and Learning (MEAL) Department",
        "MEALD",
        "DEPARTMENT",
        "department",
        "Operational department conducting data collection, impact analysis, and reporting.",
        parent_identifier="DIR-MEAL",
    ),
    UnitSeed(
        "DEPT-PCE",
        "Partnerships and Community Engagement Department",
        "PCED",
        "DEPARTMENT",
        "department",
        "Operational department managing stakeholder partnerships and community relations.",
        parent_identifier="DIR-PART-RES",
    ),
    UnitSeed(
        "DEPT-CMKM",
        "Communications, Media and Knowledge Management Department",
        "CMKMD",
        "DEPARTMENT",
        "department",
        "Operational department managing publications, media outreach, and institutional knowledge.",
        parent_identifier="DIR-COMM-MEDIA",
    ),
    UnitSeed(
        "DEPT-MVHR",
        "Membership, Volunteers and Human Resources Department",
        "MVHRD",
        "DEPARTMENT",
        "department",
        "Operational department administering staff, volunteer corps, and member rosters.",
        parent_identifier="DIR-MEMB-VOL",
    ),
    UnitSeed(
        "DEPT-ETDI",
        "Education, Training and Digital Innovation Department",
        "ETDID",
        "DEPARTMENT",
        "department",
        "Operational department delivering training curriculum, digital tools, and innovation labs.",
        parent_identifier="DIR-EDU-DIGI",
    ),
    UnitSeed(
        "DEPT-YEHCD",
        "Youth Empowerment, Health and Community Development Department",
        "YEHCDD",
        "DEPARTMENT",
        "department",
        "Operational department executing health outreach, youth empowerment, and local development.",
        parent_identifier="DIR-HEALTH-WELL",
    ),
    UnitSeed(
        "DEPT-QARS",
        "Quality Assurance, Risk, Safeguarding and Compliance Department",
        "QARSD",
        "DEPARTMENT",
        "department",
        "Operational department ensuring standards compliance, child safeguarding, and risk mitigation.",
        parent_identifier="DIR-QA-COMP",
    ),
)

# 11 APPROVED PROGRAM AND TECHNICAL MANAGEMENT UNITS
DEFAULT_PTM_UNITS: tuple[UnitSeed, ...] = (
    UnitSeed(
        "PTM-PPC",
        "Program and Project Coordinator",
        "PPC",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Program and project coordination function.",
        parent_identifier="DEPT-PPM",
    ),
    UnitSeed(
        "PTM-MEO",
        "Monitoring and Evaluation Officer",
        "MEO",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Monitoring, evaluation, and data reporting function.",
        parent_identifier="DEPT-MEAL",
    ),
    UnitSeed(
        "PTM-FM",
        "Finance Manager",
        "FM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Financial management and budgetary administration function.",
        parent_identifier="DEPT-FGRM",
    ),
    UnitSeed(
        "PTM-RMP",
        "Resource Mobilization and Partnership Manager",
        "RMPM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Resource mobilization, grant proposal, and partner coordination function.",
        parent_identifier="DEPT-FGRM",
    ),
    UnitSeed(
        "PTM-CEM",
        "Community Engagement Manager",
        "CEM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Community engagement, dialogue, and field mobilization function.",
        parent_identifier="DEPT-PCE",
    ),
    UnitSeed(
        "PTM-MPRO",
        "Media and Public Relations Officer",
        "MPRO",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Media liaison, public relations, and communications output function.",
        parent_identifier="DEPT-CMKM",
    ),
    UnitSeed(
        "PTM-TCD",
        "Training and Capacity Development Manager",
        "TCDM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Training curriculum development and workshop coordination function.",
        parent_identifier="DEPT-ETDI",
    ),
    UnitSeed(
        "PTM-ICT",
        "ICT/Digital Systems Officer",
        "ICTO",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "ICT infrastructure, software systems, and digital support function.",
        parent_identifier="DEPT-ETDI",
    ),
    UnitSeed(
        "PTM-HRM",
        "Human Resources Manager",
        "HRM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Human resources, volunteer onboarding, and staff welfare function.",
        parent_identifier="DEPT-MVHR",
    ),
    UnitSeed(
        "PTM-SPM",
        "Safeguarding and Protection Manager",
        "SPM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Safeguarding, child protection, and whistleblowing oversight function.",
        parent_identifier="DEPT-QARS",
    ),
    UnitSeed(
        "PTM-RCM",
        "Risk and Compliance Manager",
        "RCM",
        "PROGRAM_TECHNICAL_MANAGEMENT",
        "program_technical_management",
        "Risk assessment, audit compliance, and statutory alignment function.",
        parent_identifier="DEPT-QARS",
    ),
)

# APPROVED RELATIONSHIP MAPS FOR CASCADING AND VALIDATION
# Directorate Identifier -> tuple of compatible Department Identifiers
DIRECTORATE_TO_DEPARTMENT_MAP: dict[str, tuple[str, ...]] = {
    "DIR-PROG-PROJ": ("DEPT-PPM",),
    "DIR-OPS-ADMIN": ("DEPT-OAD",),
    "DIR-FIN-RES": ("DEPT-FGRM",),
    "DIR-MEAL": ("DEPT-MEAL",),
    "DIR-PART-RES": ("DEPT-PCE", "DEPT-FGRM"),
    "DIR-COMM-MEDIA": ("DEPT-CMKM",),
    "DIR-MEMB-VOL": ("DEPT-MVHR",),
    "DIR-COMM-ENGAGE": ("DEPT-PCE", "DEPT-YEHCD"),
    "DIR-TRAIN-CAP": ("DEPT-ETDI",),
    "DIR-RES-INNOV": ("DEPT-ETDI", "DEPT-CMKM"),
    "DIR-HR-OD": ("DEPT-MVHR",),
    "DIR-QA-COMP": ("DEPT-QARS",),
    "DIR-RISK-SAFE": ("DEPT-QARS",),
    "DIR-EDU-DIGI": ("DEPT-ETDI",),
    "DIR-ENTREP-SKILLS": ("DEPT-YEHCD", "DEPT-ETDI"),
    "DIR-LEAD-CIVIC": ("DEPT-PCE", "DEPT-YEHCD"),
    "DIR-HEALTH-WELL": ("DEPT-YEHCD",),
}

# Department Identifier -> tuple of compatible PTM Identifiers
DEPARTMENT_TO_PTM_MAP: dict[str, tuple[str, ...]] = {
    "DEPT-PPM": ("PTM-PPC",),
    "DEPT-OAD": ("PTM-PPC",),
    "DEPT-FGRM": ("PTM-FM", "PTM-RMP"),
    "DEPT-MEAL": ("PTM-MEO",),
    "DEPT-PCE": ("PTM-CEM", "PTM-RMP"),
    "DEPT-CMKM": ("PTM-MPRO", "PTM-ICT"),
    "DEPT-MVHR": ("PTM-HRM",),
    "DEPT-ETDI": ("PTM-TCD", "PTM-ICT"),
    "DEPT-YEHCD": ("PTM-CEM", "PTM-PPC"),
    "DEPT-QARS": ("PTM-SPM", "PTM-RCM"),
}

# Directorate Identifier -> tuple of directly compatible PTM Identifiers
DIRECTORATE_TO_PTM_MAP: dict[str, tuple[str, ...]] = {
    "DIR-PROG-PROJ": ("PTM-PPC",),
    "DIR-OPS-ADMIN": ("PTM-PPC",),
    "DIR-FIN-RES": ("PTM-FM", "PTM-RMP"),
    "DIR-MEAL": ("PTM-MEO",),
    "DIR-PART-RES": ("PTM-RMP", "PTM-CEM"),
    "DIR-COMM-MEDIA": ("PTM-MPRO",),
    "DIR-MEMB-VOL": ("PTM-HRM",),
    "DIR-COMM-ENGAGE": ("PTM-CEM",),
    "DIR-TRAIN-CAP": ("PTM-TCD",),
    "DIR-RES-INNOV": ("PTM-ICT",),
    "DIR-HR-OD": ("PTM-HRM",),
    "DIR-QA-COMP": ("PTM-RCM",),
    "DIR-RISK-SAFE": ("PTM-SPM", "PTM-RCM"),
    "DIR-EDU-DIGI": ("PTM-ICT", "PTM-TCD"),
    "DIR-ENTREP-SKILLS": ("PTM-TCD",),
    "DIR-LEAD-CIVIC": ("PTM-CEM",),
    "DIR-HEALTH-WELL": ("PTM-CEM", "PTM-PPC"),
}
