"""Constants for the leadership management module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class LeadershipLevel(models.TextChoices):
    """Organizational leadership levels supported by the module.

    The hierarchy follows the official SITADC Youth Organization structure:

    LEVEL 1 — GENERAL ASSEMBLY
    GENERAL_ASSEMBLY: Highest organizational governance level

    LEVEL 2 — BOARD OF DIRECTORS / BOARD OF TRUSTEES
    BOARD_OF_DIRECTORS_TRUSTEES: Board governance level

    LEVEL 3 — NATIONAL EXECUTIVE COMMITTEE (NEC)
    NATIONAL_EXECUTIVE_COMMITTEE: NEC governance level

    LEVEL 4 — EXECUTIVE MANAGEMENT
    EXECUTIVE_MANAGEMENT: Executive Management leadership level
    EXECUTIVE_DIRECTOR: Executive Director position level
    EXECUTIVE_OFFICE: Executive Office leadership

    LEVEL 5 — DIRECTORATES (17 Directorates)
    DIRECTORATE: Directorate leadership level

    LEVEL 6 — DEPARTMENTS (10 Operational Departments)
    DEPARTMENT: Department leadership level

    LEVEL 7 — PROGRAM AND TECHNICAL MANAGEMENT
    PROGRAM_TECHNICAL_MANAGEMENT: Program and Technical Management positions

    LEVEL 8 — REGIONAL LEADERSHIP
    REGIONAL_COORDINATOR: Regional Coordinator leadership level

    LEVEL 9 — DISTRICT LEADERSHIP
    DISTRICT_COORDINATOR: District Coordinator leadership level

    LEVEL 10 — COMMUNITY LEADERSHIP
    COMMUNITY_COORDINATOR: Community Coordinator leadership level

    LEVEL 11 — TEAM LEADERSHIP
    TEAM_LEADER: Team Leader leadership level

    LEVEL 12 — VOLUNTEERS AND MEMBERS
    VOLUNTEER_MEMBER: Volunteer / Member operational level

    OTHER:
    REPORT_AUTHOR: Personnel authorized to author official reports
    """

    # LEVEL 1 — GENERAL ASSEMBLY
    GENERAL_ASSEMBLY = "GENERAL_ASSEMBLY", _("General Assembly")

    # LEVEL 2 — BOARD OF DIRECTORS / BOARD OF TRUSTEES
    BOARD_OF_DIRECTORS_TRUSTEES = (
        "BOARD_OF_DIRECTORS_TRUSTEES",
        _("Board of Directors / Board of Trustees"),
    )

    # LEVEL 3 — NATIONAL EXECUTIVE COMMITTEE
    NATIONAL_EXECUTIVE_COMMITTEE = (
        "NATIONAL_EXECUTIVE_COMMITTEE",
        _("National Executive Committee"),
    )

    # LEVEL 4 — EXECUTIVE MANAGEMENT
    EXECUTIVE_MANAGEMENT = "EXECUTIVE_MANAGEMENT", _("Executive Management")
    EXECUTIVE_DIRECTOR = "EXECUTIVE_DIRECTOR", _("Executive Director")
    EXECUTIVE_OFFICE = "EXECUTIVE_OFFICE", _("Executive Office")

    # LEVEL 5 — DIRECTORATES
    DIRECTORATE = "DIRECTORATE", _("Directorate")

    # LEVEL 6 — DEPARTMENTS
    DEPARTMENT = "DEPARTMENT", _("Department")

    # LEVEL 7 — PROGRAM AND TECHNICAL MANAGEMENT
    PROGRAM_TECHNICAL_MANAGEMENT = "PROGRAM_TECHNICAL_MANAGEMENT", _("Program and Technical Management")

    # LEVEL 8 — REGIONAL LEADERSHIP
    REGIONAL_COORDINATOR = "REGIONAL_COORDINATOR", _("Regional Coordinator")

    # LEVEL 9 — DISTRICT LEADERSHIP
    DISTRICT_COORDINATOR = "DISTRICT_COORDINATOR", _("District Coordinator")

    # LEVEL 10 — COMMUNITY LEADERSHIP
    COMMUNITY_COORDINATOR = "COMMUNITY_COORDINATOR", _("Community Coordinator")

    # LEVEL 11 — TEAM LEADERSHIP
    TEAM_LEADER = "TEAM_LEADER", _("Team Leader")

    # LEVEL 12 — VOLUNTEERS AND MEMBERS
    VOLUNTEER_MEMBER = "VOLUNTEER_MEMBER", _("Volunteers / Members")

    # OTHER
    REPORT_AUTHOR = "REPORT_AUTHOR", _("Report Author")


class LeadershipStatus(models.TextChoices):
    """Lifecycle status for a leadership record."""

    NOMINATED = "NOMINATED", _("Nominated")
    APPLIED = "APPLIED", _("Applied")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    APPOINTED = "APPOINTED", _("Appointed")
    ACTIVE = "ACTIVE", _("Active")
    ACTING = "ACTING", _("Acting")
    PROBATION = "PROBATION", _("Probation")
    ON_LEAVE = "ON_LEAVE", _("On Leave")
    SUSPENDED = "SUSPENDED", _("Suspended")
    COMPLETED_TERM = "COMPLETED_TERM", _("Completed Term")
    RETIRED = "RETIRED", _("Retired")
    RESIGNED = "RESIGNED", _("Resigned")
    REMOVED = "REMOVED", _("Removed")
    ARCHIVED = "ARCHIVED", _("Archived")


class AppointmentType(models.TextChoices):
    """Types of leadership appointment."""

    PERMANENT = "PERMANENT", _("Permanent")
    ACTING = "ACTING", _("Acting")
    INTERIM = "INTERIM", _("Interim")
    TEMPORARY = "TEMPORARY", _("Temporary")
    HONORARY = "HONORARY", _("Honorary")
    CONTRACT = "CONTRACT", _("Contract")


class AppointmentStatus(models.TextChoices):
    """Workflow status for a leadership appointment.

    Follows the roadmap lifecycle: nomination, application, review, approval,
    appointment, active service, performance review, then renewal or exit.
    """

    DRAFT = "DRAFT", _("Draft")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    EXPIRED = "EXPIRED", _("Expired")
    TERMINATED = "TERMINATED", _("Terminated")
    RESIGNED = "RESIGNED", _("Resigned")
    REMOVED = "REMOVED", _("Removed")
    REVOKED = "REVOKED", _("Revoked")
    ARCHIVED = "ARCHIVED", _("Archived")


class TermStatus(models.TextChoices):
    """Status of a leadership term of office."""

    CURRENT = "CURRENT", _("Current")
    EXPIRING = "EXPIRING", _("Expiring")
    EXPIRED = "EXPIRED", _("Expired")
    RENEWED = "RENEWED", _("Renewed")
    COMPLETED = "COMPLETED", _("Completed")


class RenewalStatus(models.TextChoices):
    """Renewal eligibility for a term-based appointment."""

    NOT_ELIGIBLE = "NOT_ELIGIBLE", _("Not Eligible")
    ELIGIBLE = "ELIGIBLE", _("Eligible")
    RENEWED = "RENEWED", _("Renewed")
    NOT_RENEWED = "NOT_RENEWED", _("Not Renewed")


class AttendanceStatus(models.TextChoices):
    """Status for a leadership attendance record."""

    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    LATE = "LATE", _("Late")
    EXCUSED = "EXCUSED", _("Excused")
    REMOTE = "REMOTE", _("Remote")


class AttendanceType(models.TextChoices):
    """Activities for which leadership attendance is recorded."""

    MEETING = "MEETING", _("Meeting")
    TRAINING = "TRAINING", _("Training")
    EVENT = "EVENT", _("Organizational Event")
    COMMUNITY_ACTIVITY = "COMMUNITY_ACTIVITY", _("Community Activity")
    PROGRAM_VISIT = "PROGRAM_VISIT", _("Program Implementation Visit")
    BOARD_MEETING = "BOARD_MEETING", _("Board Meeting")
    EXECUTIVE_MEETING = "EXECUTIVE_MEETING", _("Executive Meeting")


class LeaveType(models.TextChoices):
    """Leadership leave categories."""

    ANNUAL = "ANNUAL", _("Annual Leave")
    COMPASSIONATE = "COMPASSIONATE", _("Compassionate Leave")
    SICK = "SICK", _("Sick Leave")
    OFFICIAL_TRAVEL = "OFFICIAL_TRAVEL", _("Official Travel")
    STUDY = "STUDY", _("Study Leave")
    MATERNITY = "MATERNITY", _("Maternity Leave")
    PATERNITY = "PATERNITY", _("Paternity Leave")
    SPECIAL = "SPECIAL", _("Special Leave")


class LeaveStatus(models.TextChoices):
    """Status for a leadership leave request."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")
    TAKEN = "TAKEN", _("Taken")
    ENDED = "ENDED", _("Ended")


class TaskPriority(models.TextChoices):
    """Priority for a leadership task."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class TaskStatus(models.TextChoices):
    """Status for a leadership task."""

    NOT_STARTED = "NOT_STARTED", _("Not Started")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    OVERDUE = "OVERDUE", _("Overdue")


class GoalStatus(models.TextChoices):
    """Status for a leadership goal."""

    NOT_STARTED = "NOT_STARTED", _("Not Started")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    ACHIEVED = "ACHIEVED", _("Achieved")
    DELAYED = "DELAYED", _("Delayed")
    CANCELLED = "CANCELLED", _("Cancelled")


class KpiStatus(models.TextChoices):
    """Status for a leadership KPI."""

    ON_TRACK = "ON_TRACK", _("On Track")
    AT_RISK = "AT_RISK", _("At Risk")
    OFF_TRACK = "OFF_TRACK", _("Off Track")
    ACHIEVED = "ACHIEVED", _("Achieved")


class CoachingCategory(models.TextChoices):
    """Categories for leadership coaching records."""

    LEADERSHIP = "LEADERSHIP", _("Leadership")
    PERFORMANCE = "PERFORMANCE", _("Performance")
    CAREER = "CAREER", _("Career Development")
    TECHNICAL = "TECHNICAL", _("Technical")
    COMMUNICATION = "COMMUNICATION", _("Communication")
    OTHER = "OTHER", _("Other")


class MentorshipStatus(models.TextChoices):
    """Status for a leadership mentorship relationship."""

    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    TERMINATED = "TERMINATED", _("Terminated")


class ReviewStatus(models.TextChoices):
    """Status for a leadership performance review."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    RETURNED = "RETURNED", _("Returned")
    APPROVED = "APPROVED", _("Approved")
    ARCHIVED = "ARCHIVED", _("Archived")


class ReviewCycle(models.TextChoices):
    """Performance review cycles."""

    ANNUAL = "ANNUAL", _("Annual")
    SEMI_ANNUAL = "SEMI_ANNUAL", _("Semi-Annual")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    MONTHLY = "MONTHLY", _("Monthly")
    AD_HOC = "AD_HOC", _("Ad Hoc")


class RatingScale(models.IntegerChoices):
    """1-5 performance rating scale."""

    ONE = 1, _("1 - Unsatisfactory")
    TWO = 2, _("2 - Needs Improvement")
    THREE = 3, _("3 - Meets Expectations")
    FOUR = 4, _("4 - Exceeds Expectations")
    FIVE = 5, _("5 - Outstanding")


class RecognitionCategory(models.TextChoices):
    """Categories for leadership recognition and awards."""

    EXCELLENCE = "EXCELLENCE", _("Excellence")
    SERVICE = "SERVICE", _("Service")
    INNOVATION = "INNOVATION", _("Innovation")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    COMMUNITY = "COMMUNITY", _("Community Impact")
    OTHER = "OTHER", _("Other")


class DisciplinaryType(models.TextChoices):
    """Types of leadership disciplinary record."""

    WRITTEN_WARNING = "WRITTEN_WARNING", _("Written Warning")
    PERFORMANCE_IMPROVEMENT = (
        "PERFORMANCE_IMPROVEMENT",
        _("Performance Improvement Plan"),
    )
    INVESTIGATION = "INVESTIGATION", _("Investigation")
    SUSPENSION = "SUSPENSION", _("Suspension")
    APPEAL = "APPEAL", _("Appeal")
    FINAL_DECISION = "FINAL_DECISION", _("Final Decision")


class DisciplinaryStatus(models.TextChoices):
    """Status for a leadership disciplinary record."""

    OPEN = "OPEN", _("Open")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")


class DocumentCategory(models.TextChoices):
    """Categories for leadership documents."""

    APPOINTMENT_LETTER = "APPOINTMENT_LETTER", _("Appointment Letter")
    CONTRACT = "CONTRACT", _("Contract")
    IDENTIFICATION = "IDENTIFICATION", _("Identification Document")
    CURRICULUM_VITAE = "CURRICULUM_VITAE", _("Curriculum Vitae")
    ACADEMIC_CERTIFICATE = "ACADEMIC_CERTIFICATE", _("Academic Certificate")
    PROFESSIONAL_CERTIFICATION = (
        "PROFESSIONAL_CERTIFICATION",
        _("Professional Certification"),
    )
    PERFORMANCE_REVIEW = "PERFORMANCE_REVIEW", _("Performance Review Report")
    DECLARATION = "DECLARATION", _("Signed Declaration")
    POLICY_ACKNOWLEDGEMENT = "POLICY_ACKNOWLEDGEMENT", _("Policy Acknowledgement")
    OTHER = "OTHER", _("Other")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality levels for leadership records and documents."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    RESTRICTED = "RESTRICTED", _("Restricted")


class SuccessionReadiness(models.TextChoices):
    """Readiness levels for succession planning candidates."""

    NOT_READY = "NOT_READY", _("Not Ready")
    DEVELOPING = "DEVELOPING", _("Developing")
    READY = "READY", _("Ready")
    IMMEDIATE = "IMMEDIATE", _("Immediate")


class SuccessionRisk(models.TextChoices):
    """Risk level for a succession plan."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class ScorecardStatus(models.TextChoices):
    """Status for a leadership performance scorecard."""

    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class LeadershipAuditAction(models.TextChoices):
    """Audited events recorded by the leadership module."""

    CREATED = "CREATED", _("Created")
    UPDATED = "UPDATED", _("Updated")
    STATUS_CHANGED = "STATUS_CHANGED", _("Status Changed")
    APPOINTED = "APPOINTED", _("Appointed")
    APPOINTMENT_APPROVED = "APPOINTMENT_APPROVED", _("Appointment Approved")
    APPOINTMENT_ACTIVATED = "APPOINTMENT_ACTIVATED", _("Appointment Activated")
    APPOINTMENT_COMPLETED = "APPOINTMENT_COMPLETED", _("Appointment Completed")
    APPOINTMENT_TERMINATED = "APPOINTMENT_TERMINATED", _("Appointment Terminated")
    APPOINTMENT_RENEWED = "APPOINTMENT_RENEWED", _("Appointment Renewed")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    SUPERVISOR_CHANGED = "SUPERVISOR_CHANGED", _("Supervisor Changed")
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", _("Document Uploaded")
    REVIEW_SUBMITTED = "REVIEW_SUBMITTED", _("Review Submitted")
    REVIEW_APPROVED = "REVIEW_APPROVED", _("Review Approved")
    REVIEW_RETURNED = "REVIEW_RETURNED", _("Review Returned")


# Appointment workflow transitions considered valid by the services.
VALID_APPOINTMENT_TRANSITIONS: dict[str, tuple[str, ...]] = {
    AppointmentStatus.DRAFT: (
        AppointmentStatus.PENDING_REVIEW,
        AppointmentStatus.ARCHIVED,
    ),
    AppointmentStatus.PENDING_REVIEW: (
        AppointmentStatus.PENDING_APPROVAL,
        AppointmentStatus.DRAFT,
        AppointmentStatus.ARCHIVED,
    ),
    AppointmentStatus.PENDING_APPROVAL: (
        AppointmentStatus.APPROVED,
        AppointmentStatus.PENDING_REVIEW,
        AppointmentStatus.ARCHIVED,
    ),
    AppointmentStatus.APPROVED: (
        AppointmentStatus.ACTIVE,
        AppointmentStatus.ARCHIVED,
    ),
    AppointmentStatus.ACTIVE: (
        AppointmentStatus.COMPLETED,
        AppointmentStatus.EXPIRED,
        AppointmentStatus.TERMINATED,
        AppointmentStatus.RESIGNED,
        AppointmentStatus.REMOVED,
        AppointmentStatus.ARCHIVED,
    ),
    AppointmentStatus.COMPLETED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.EXPIRED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.TERMINATED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.RESIGNED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.REMOVED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.REVOKED: (AppointmentStatus.ARCHIVED,),
    AppointmentStatus.ARCHIVED: (),
}
