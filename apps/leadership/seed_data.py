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
    # LEVEL 1 — GENERAL ASSEMBLY
    LeadershipLevelSeed(
        LeadershipLevel.GENERAL_ASSEMBLY,
        "General Assembly",
        "Highest organizational governance level.",
        10,
    ),
    # LEVEL 2 — BOARD OF DIRECTORS / BOARD OF TRUSTEES
    LeadershipLevelSeed(
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Board of Directors / Board of Trustees",
        "Governance body overseeing the organization (16 official positions).",
        20,
    ),
    # LEVEL 3 — NATIONAL EXECUTIVE COMMITTEE
    LeadershipLevelSeed(
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "National Executive Committee",
        "National executive governance and oversight (17 official positions).",
        30,
    ),
    # LEVEL 4 — EXECUTIVE MANAGEMENT
    LeadershipLevelSeed(
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Executive Management",
        "Executive leadership responsible for strategic direction (16 official positions).",
        40,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.EXECUTIVE_DIRECTOR,
        "Executive Director",
        "Chief executive responsible for day-to-day operations.",
        45,
    ),
    LeadershipLevelSeed(
        LeadershipLevel.EXECUTIVE_OFFICE,
        "Executive Office",
        "Executive Office leadership and support.",
        48,
    ),
    # LEVEL 5 — DIRECTORATES
    LeadershipLevelSeed(
        LeadershipLevel.DIRECTORATE,
        "Directorate",
        "Functional directorate leadership (17 Directorates).",
        50,
    ),
    # LEVEL 6 — DEPARTMENTS
    LeadershipLevelSeed(
        LeadershipLevel.DEPARTMENT,
        "Department",
        "Operational department leadership (10 Departments).",
        60,
    ),
    # LEVEL 7 — PROGRAM AND TECHNICAL MANAGEMENT
    LeadershipLevelSeed(
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Program and Technical Management",
        "Program and Technical Management positions beneath Directorates/Departments.",
        70,
    ),
    # LEVEL 8 — REGIONAL LEADERSHIP
    LeadershipLevelSeed(
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Regional Coordinator",
        "Regional leadership overseeing districts (15 official positions per region).",
        80,
    ),
    # LEVEL 9 — DISTRICT LEADERSHIP
    LeadershipLevelSeed(
        LeadershipLevel.DISTRICT_COORDINATOR,
        "District Coordinator",
        "District leadership overseeing communities.",
        90,
    ),
    # LEVEL 10 — COMMUNITY LEADERSHIP
    LeadershipLevelSeed(
        LeadershipLevel.COMMUNITY_COORDINATOR,
        "Community Coordinator",
        "Community leadership supervising team leaders.",
        100,
    ),
    # LEVEL 11 — TEAM LEADERSHIP
    LeadershipLevelSeed(
        LeadershipLevel.TEAM_LEADER,
        "Team Leader",
        "Team leadership supervising operational teams.",
        110,
    ),
    # LEVEL 12 — VOLUNTEERS AND MEMBERS
    LeadershipLevelSeed(
        LeadershipLevel.VOLUNTEER_MEMBER,
        "Volunteers / Members",
        "Operational/community participation level.",
        120,
    ),
    # OTHER
    LeadershipLevelSeed(
        LeadershipLevel.REPORT_AUTHOR,
        "Report Author",
        "Personnel authorized to author official reports.",
        130,
    ),
)


class LeadershipPositionSeed:
    """Plain-data description of a standard leadership position."""

    def __init__(self, title: str, level: str, description: str) -> None:
        self.title = title
        self.level = level
        self.description = description


LEADERSHIP_POSITIONS: tuple[LeadershipPositionSeed, ...] = (
    # LEVEL 1 — GENERAL ASSEMBLY
    LeadershipPositionSeed(
        "General Assembly Member",
        LeadershipLevel.GENERAL_ASSEMBLY,
        "Member of the General Assembly — highest governance body.",
    ),
    # LEVEL 2 — BOARD OF DIRECTORS / BOARD OF TRUSTEES (16 official positions)
    LeadershipPositionSeed(
        "Board Chairperson",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Chairs the Board of Directors / Board of Trustees and leads governance oversight.",
    ),
    LeadershipPositionSeed(
        "Vice Board Chairperson",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Deputizes for the Board Chairperson and supports governance leadership.",
    ),
    LeadershipPositionSeed(
        "Board Secretary",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Records and administers board meetings and governance records.",
    ),
    LeadershipPositionSeed(
        "Vice/Deputy Board Secretary",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Supports the Board Secretary in governance administration.",
    ),
    LeadershipPositionSeed(
        "Board Treasurer",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Oversees financial governance, audit, and fiscal responsibility.",
    ),
    LeadershipPositionSeed(
        "Vice/Deputy Board Treasurer",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Supports the Board Treasurer in financial governance.",
    ),
    LeadershipPositionSeed(
        "Board Member — Governance and Policy",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Provides governance oversight and policy direction.",
    ),
    LeadershipPositionSeed(
        "Board Member — Finance and Audit",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Provides financial oversight and audit governance.",
    ),
    LeadershipPositionSeed(
        "Board Member — Programs and Impact",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Oversees program strategy and impact measurement.",
    ),
    LeadershipPositionSeed(
        "Board Member — Partnerships and Resource Mobilization",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Leads partnership development and resource mobilization strategy.",
    ),
    LeadershipPositionSeed(
        "Board Member — Legal, Risk and Compliance",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Provides legal, risk management, and compliance oversight.",
    ),
    LeadershipPositionSeed(
        "Board Member — Youth Development and Community Engagement",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Oversees youth development and community engagement strategy.",
    ),
    LeadershipPositionSeed(
        "Board Member — Monitoring, Evaluation, Accountability and Learning (MEAL)",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Provides MEAL governance and accountability oversight.",
    ),
    LeadershipPositionSeed(
        "Board Member — Communications, Advocacy and Public Relations",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Leads communications, advocacy, and public relations strategy.",
    ),
    LeadershipPositionSeed(
        "Board Member — Human Resources and Organizational Development",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Oversees HR strategy and organizational development governance.",
    ),
    LeadershipPositionSeed(
        "Board Member — Digital Transformation, Innovation and Technology",
        LeadershipLevel.BOARD_OF_DIRECTORS_TRUSTEES,
        "Leads digital transformation, innovation, and technology governance.",
    ),
    # LEVEL 3 — NATIONAL EXECUTIVE COMMITTEE (17 official positions)
    LeadershipPositionSeed(
        "President",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Overall organizational leadership and representation.",
    ),
    LeadershipPositionSeed(
        "Vice President",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Supports the President and acts in their absence.",
    ),
    LeadershipPositionSeed(
        "Secretary General",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Coordinates the National Executive Committee and secretariat.",
    ),
    LeadershipPositionSeed(
        "Deputy Secretary General",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Supports the Secretary General in NEC coordination.",
    ),
    LeadershipPositionSeed(
        "National Treasurer",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Manages national finances and treasury operations.",
    ),
    LeadershipPositionSeed(
        "Deputy National Treasurer",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Supports the National Treasurer in financial management.",
    ),
    LeadershipPositionSeed(
        "National Organizing Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Coordinates national organizing and mobilization efforts.",
    ),
    LeadershipPositionSeed(
        "Deputy National Organizing Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Supports the National Organizing Secretary.",
    ),
    LeadershipPositionSeed(
        "National Programs Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Oversees national program coordination and implementation.",
    ),
    LeadershipPositionSeed(
        "National Membership and Volunteer Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Manages national membership and volunteer coordination.",
    ),
    LeadershipPositionSeed(
        "National Communications and Public Relations Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Oversees national communications and public relations.",
    ),
    LeadershipPositionSeed(
        "National Partnerships and Resource Mobilization Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Leads national partnerships and resource mobilization.",
    ),
    LeadershipPositionSeed(
        "National Youth Development and Empowerment Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Oversees national youth development and empowerment programs.",
    ),
    LeadershipPositionSeed(
        "National Gender, Inclusion and Safeguarding Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Leads gender equality, inclusion, and safeguarding nationally.",
    ),
    LeadershipPositionSeed(
        "National Monitoring, Evaluation, Accountability and Learning (MEAL) Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Oversees national MEAL frameworks and accountability.",
    ),
    LeadershipPositionSeed(
        "National Research, Innovation and Technology Secretary",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Leads national research, innovation, and technology initiatives.",
    ),
    LeadershipPositionSeed(
        "National Executive Committee Member",
        LeadershipLevel.NATIONAL_EXECUTIVE_COMMITTEE,
        "Provides executive governance and decision-making as NEC member.",
    ),
    # LEVEL 4 — EXECUTIVE MANAGEMENT (16 official positions)
    LeadershipPositionSeed(
        "Executive Director",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Chief executive responsible for day-to-day operations.",
    ),
    LeadershipPositionSeed(
        "Deputy Executive Director",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Deputizes for the Executive Director and oversees operations.",
    ),
    LeadershipPositionSeed(
        "Executive Secretary",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Administrative head supporting executive governance.",
    ),
    LeadershipPositionSeed(
        "Director of Programs and Projects",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Programs and Projects.",
    ),
    LeadershipPositionSeed(
        "Director of Operations and Administration",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Operations and Administration.",
    ),
    LeadershipPositionSeed(
        "Director of Finance and Resource Management",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Finance and Resource Management.",
    ),
    LeadershipPositionSeed(
        "Director of MEAL",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Monitoring, Evaluation, Accountability and Learning.",
    ),
    LeadershipPositionSeed(
        "Director of Partnerships and Resource Mobilization",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Partnerships and Resource Mobilization.",
    ),
    LeadershipPositionSeed(
        "Director of Communications and Media",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Communications, Media and Public Relations.",
    ),
    LeadershipPositionSeed(
        "Director of Membership and Volunteer Management",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Membership and Volunteer Management.",
    ),
    LeadershipPositionSeed(
        "Director of Community Engagement and Outreach",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Community Engagement and Outreach.",
    ),
    LeadershipPositionSeed(
        "Director of Training and Capacity Development",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Training and Capacity Development.",
    ),
    LeadershipPositionSeed(
        "Director of Research, Innovation and Technology",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Research, Innovation and Technology.",
    ),
    LeadershipPositionSeed(
        "Director of Quality Assurance and Compliance",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Quality Assurance and Compliance.",
    ),
    LeadershipPositionSeed(
        "Director of Human Resources and Organizational Development",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Human Resources and Organizational Development.",
    ),
    LeadershipPositionSeed(
        "Director of Risk, Safeguarding and Compliance",
        LeadershipLevel.EXECUTIVE_MANAGEMENT,
        "Leads the Directorate of Risk Management, Safeguarding and Ethics.",
    ),
    # LEVEL 5 — DIRECTORATES (17 Directorates)
    LeadershipPositionSeed(
        "Director",
        LeadershipLevel.DIRECTORATE,
        "Leads a directorate and reports to the Executive Director.",
    ),
    LeadershipPositionSeed(
        "Deputy Director",
        LeadershipLevel.DIRECTORATE,
        "Deputizes for a Director and oversees programmes.",
    ),
    LeadershipPositionSeed(
        "Manager",
        LeadershipLevel.DIRECTORATE,
        "Manages specific directorate functions and operational initiatives.",
    ),
    LeadershipPositionSeed(
        "Coordinator",
        LeadershipLevel.DIRECTORATE,
        "Coordinates activities and workstreams within a directorate.",
    ),
    LeadershipPositionSeed(
        "Officer",
        LeadershipLevel.DIRECTORATE,
        "Executes operational and technical tasks within a directorate.",
    ),
    LeadershipPositionSeed(
        "Assistant",
        LeadershipLevel.DIRECTORATE,
        "Provides administrative and operational support within a directorate.",
    ),
    # LEVEL 6 — DEPARTMENTS (10 Operational Departments)
    LeadershipPositionSeed(
        "Head of Department",
        LeadershipLevel.DEPARTMENT,
        "Leads an operational department within a directorate.",
    ),
    LeadershipPositionSeed(
        "Deputy Head of Department",
        LeadershipLevel.DEPARTMENT,
        "Deputizes for the Head of Department.",
    ),
    # LEVEL 7 — PROGRAM AND TECHNICAL MANAGEMENT
    LeadershipPositionSeed(
        "Program and Project Coordinator",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Coordinates program and project implementation.",
    ),
    LeadershipPositionSeed(
        "Monitoring and Evaluation Officer",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages monitoring, evaluation, accountability and learning.",
    ),
    LeadershipPositionSeed(
        "Finance Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages financial records, budgets and reporting.",
    ),
    LeadershipPositionSeed(
        "Resource Mobilization and Partnership Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Mobilizes financial and non-financial resources and manages partnerships.",
    ),
    LeadershipPositionSeed(
        "Community Engagement Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages community engagement and outreach activities.",
    ),
    LeadershipPositionSeed(
        "Media and Public Relations Officer",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages communications, media and public relations.",
    ),
    LeadershipPositionSeed(
        "Training and Capacity Development Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages training and capacity development programs.",
    ),
    LeadershipPositionSeed(
        "ICT/Digital Systems Officer",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages ICT systems and digital innovation.",
    ),
    LeadershipPositionSeed(
        "Human Resources Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages human resources and organizational development.",
    ),
    LeadershipPositionSeed(
        "Safeguarding and Protection Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages safeguarding, protection and compliance.",
    ),
    LeadershipPositionSeed(
        "Risk and Compliance Manager",
        LeadershipLevel.PROGRAM_TECHNICAL_MANAGEMENT,
        "Manages risk, quality assurance and compliance.",
    ),
    # LEVEL 8 — REGIONAL LEADERSHIP (15 positions per region)
    LeadershipPositionSeed(
        "Regional Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates implementation within an assigned region.",
    ),
    LeadershipPositionSeed(
        "Deputy Regional Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Supports the Regional Coordinator in regional operations.",
    ),
    LeadershipPositionSeed(
        "Regional Secretary",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Administers regional secretariat and documentation.",
    ),
    LeadershipPositionSeed(
        "Regional Programs Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates program implementation at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional MEAL Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates MEAL activities at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Finance and Administration Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates finance and administration at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional HR Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates human resources at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Communications and Media Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates communications and media at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Partnerships and Resource Mobilization Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates partnerships and resource mobilization at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Community Engagement Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates community engagement at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Training and Capacity Development Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates training and capacity development at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Research and Innovation Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates research and innovation at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Safeguarding and Compliance Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates safeguarding and compliance at regional level.",
    ),
    LeadershipPositionSeed(
        "Regional Quality Assurance Coordinator",
        LeadershipLevel.REGIONAL_COORDINATOR,
        "Coordinates quality assurance at regional level.",
    ),
    # LEVEL 9 — DISTRICT LEADERSHIP
    LeadershipPositionSeed(
        "District Coordinator",
        LeadershipLevel.DISTRICT_COORDINATOR,
        "Coordinates implementation within an assigned district.",
    ),
    # LEVEL 10 — COMMUNITY LEADERSHIP
    LeadershipPositionSeed(
        "Community Coordinator",
        LeadershipLevel.COMMUNITY_COORDINATOR,
        "Coordinates implementation within an assigned community.",
    ),
    # LEVEL 11 — TEAM LEADERSHIP
    LeadershipPositionSeed(
        "Team Leader",
        LeadershipLevel.TEAM_LEADER,
        "Leads a delivery team within a community.",
    ),
    # LEVEL 12 — VOLUNTEERS AND MEMBERS
    LeadershipPositionSeed(
        "Volunteer",
        LeadershipLevel.VOLUNTEER_MEMBER,
        "Operational volunteer serving in programs and communities.",
    ),
    LeadershipPositionSeed(
        "Member",
        LeadershipLevel.VOLUNTEER_MEMBER,
        "Registered member of the organization.",
    ),
    # OTHER
    LeadershipPositionSeed(
        "Report Author",
        LeadershipLevel.REPORT_AUTHOR,
        "Personnel authorized to author official reports.",
    ),
)
