"""Constants for the organizational structure module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class UnitStatus(models.TextChoices):
    """Lifecycle status for an organizational unit."""

    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    ARCHIVED = "ARCHIVED", _("Archived")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")


class UnitType(models.TextChoices):
    """Functional types of organizational units.

    The hierarchy follows the official SITADC Youth Organization structure:
    
    GOVERNANCE LEVELS (Level 1-3):
    - GENERAL_ASSEMBLY: Highest governance body
    - BOARD_OF_DIRECTORS_TRUSTEES: Board of Directors / Board of Trustees
    - NATIONAL_EXECUTIVE_COMMITTEE: National Executive Committee (NEC)
    
    EXECUTIVE LEVELS (Level 4-5):
    - EXECUTIVE_MANAGEMENT: Executive Management
    - EXECUTIVE_OFFICE: Executive Office
    
    FUNCTIONAL/TECHNICAL LEVELS (Level 6-7):
    - DIRECTORATE: Strategic functional directorates (17 total)
    - DEPARTMENT: Operational departments within directorates (10 total)
    - PROGRAM_TECHNICAL_MANAGEMENT: Program and Technical Management positions
    
    GEOGRAPHICAL LEVELS (Level 8-12):
    - REGION: Regional Coordinators
    - DISTRICT: District Coordinators
    - COMMUNITY: Community Coordinators
    - TEAM: Team Leaders
    - VOLUNTEER_MEMBER: Volunteers / Members
    
    OPERATIONAL UNITS:
    - PROGRAM_UNIT: Program Unit
    - PROJECT_UNIT: Project Unit
    - COMMITTEE: Committee
    - WORKING_GROUP: Working Group
    """

    # GOVERNANCE LEVELS
    GENERAL_ASSEMBLY = "GENERAL_ASSEMBLY", _("General Assembly")
    BOARD_OF_DIRECTORS_TRUSTEES = "BOARD_OF_DIRECTORS_TRUSTEES", _("Board of Directors / Board of Trustees")
    NATIONAL_EXECUTIVE_COMMITTEE = (
        "NATIONAL_EXECUTIVE_COMMITTEE",
        _("National Executive Committee"),
    )

    # EXECUTIVE LEVELS
    EXECUTIVE_MANAGEMENT = "EXECUTIVE_MANAGEMENT", _("Executive Management")
    EXECUTIVE_OFFICE = "EXECUTIVE_OFFICE", _("Executive Office")

    # FUNCTIONAL/TECHNICAL LEVELS
    DIRECTORATE = "DIRECTORATE", _("Directorate")
    DEPARTMENT = "DEPARTMENT", _("Department")
    PROGRAM_TECHNICAL_MANAGEMENT = "PROGRAM_TECHNICAL_MANAGEMENT", _("Program and Technical Management")

    # GEOGRAPHICAL LEVELS
    REGION = "REGION", _("Region")
    DISTRICT = "DISTRICT", _("District")
    COMMUNITY = "COMMUNITY", _("Community")
    TEAM = "TEAM", _("Team")
    VOLUNTEER_MEMBER = "VOLUNTEER_MEMBER", _("Volunteers / Members")

    # OPERATIONAL UNITS
    PROGRAM_UNIT = "PROGRAM_UNIT", _("Program Unit")
    PROJECT_UNIT = "PROJECT_UNIT", _("Project Unit")
    COMMITTEE = "COMMITTEE", _("Committee")
    WORKING_GROUP = "WORKING_GROUP", _("Working Group")


class PositionStatus(models.TextChoices):
    """Lifecycle status for an organizational position."""

    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    ARCHIVED = "ARCHIVED", _("Archived")


class PositionClassification(models.TextChoices):
    """Classification categories used for reporting and administration."""

    EXECUTIVE_LEADERSHIP = "EXECUTIVE_LEADERSHIP", _("Executive Leadership")
    SENIOR_MANAGEMENT = "SENIOR_MANAGEMENT", _("Senior Management")
    MIDDLE_MANAGEMENT = "MIDDLE_MANAGEMENT", _("Middle Management")
    REGIONAL_LEADERSHIP = "REGIONAL_LEADERSHIP", _("Regional Leadership")
    DISTRICT_LEADERSHIP = "DISTRICT_LEADERSHIP", _("District Leadership")
    COMMUNITY_LEADERSHIP = "COMMUNITY_LEADERSHIP", _("Community Leadership")
    TEAM_LEADERSHIP = "TEAM_LEADERSHIP", _("Team Leadership")
    TECHNICAL_STAFF = "TECHNICAL_STAFF", _("Technical Staff")
    SUPPORT_STAFF = "SUPPORT_STAFF", _("Support Staff")
    VOLUNTEER = "VOLUNTEER", _("Volunteer")


class AppointmentType(models.TextChoices):
    """Formal appointment types supported by the organization."""

    PERMANENT = "PERMANENT", _("Permanent")
    ACTING = "ACTING", _("Acting")
    INTERIM = "INTERIM", _("Interim")
    TEMPORARY = "TEMPORARY", _("Temporary")
    VOLUNTEER = "VOLUNTEER", _("Volunteer Appointment")
    CONTRACT = "CONTRACT", _("Contract")
    HONORARY = "HONORARY", _("Honorary")


class AppointmentStatus(models.TextChoices):
    """Lifecycle status for a position assignment."""

    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    ENDED = "ENDED", _("Ended")
    REVOKED = "REVOKED", _("Revoked")


class RenewalStatus(models.TextChoices):
    """Renewal eligibility for term-based appointments."""

    NOT_ELIGIBLE = "NOT_ELIGIBLE", _("Not Eligible")
    ELIGIBLE = "ELIGIBLE", _("Eligible")
    RENEWED = "RENEWED", _("Renewed")
    NOT_RENEWED = "NOT_RENEWED", _("Not Renewed")


class ActingAppointmentStatus(models.TextChoices):
    """Lifecycle status for an acting appointment."""

    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    ENDED = "ENDED", _("Ended")
    REVOKED = "REVOKED", _("Revoked")


class VacancyStatus(models.TextChoices):
    """Lifecycle status for a position vacancy."""

    OPEN = "OPEN", _("Open")
    IN_RECRUITMENT = "IN_RECRUITMENT", _("In Recruitment")
    ON_HOLD = "ON_HOLD", _("On Hold")
    FILLED = "FILLED", _("Filled")
    CANCELLED = "CANCELLED", _("Cancelled")


class TransferStatus(models.TextChoices):
    """Lifecycle status for a personnel transfer."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    COMPLETED = "COMPLETED", _("Completed")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class OrganizationAuditAction(models.TextChoices):
    """Audited actions that may be recorded against organizational entities."""

    CREATED = "CREATED", _("Created")
    UPDATED = "UPDATED", _("Updated")
    ACTIVATED = "ACTIVATED", _("Activated")
    DEACTIVATED = "DEACTIVATED", _("Deactivated")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    PARENT_CHANGED = "PARENT_CHANGED", _("Parent Changed")
    REPORTING_LINE_CHANGED = "REPORTING_LINE_CHANGED", _("Reporting Line Changed")
    APPOINTED = "APPOINTED", _("Appointed")
    APPOINTMENT_ENDED = "APPOINTMENT_ENDED", _("Appointment Ended")
    APPOINTMENT_REVOKED = "APPOINTMENT_REVOKED", _("Appointment Revoked")
    ACTING_APPOINTED = "ACTING_APPOINTED", _("Acting Appointed")
    ACTING_ENDED = "ACTING_ENDED", _("Acting Ended")
    VACANCY_OPENED = "VACANCY_OPENED", _("Vacancy Opened")
    VACANCY_FILLED = "VACANCY_FILLED", _("Vacancy Filled")
    TRANSFERRED = "TRANSFERRED", _("Transferred")


# Positions considered protected (executive/governance) from casual changes.
PROTECTED_POSITION_SLUGS: frozenset[str] = frozenset(
    {
        "president",
        "vice-president",
        "executive-director",
        "executive-secretary",
        "secretary-general",
    }
)
