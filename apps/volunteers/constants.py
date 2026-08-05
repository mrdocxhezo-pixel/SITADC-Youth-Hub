"""
Constants and choices for the volunteer management module.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class VolunteerStatus(models.TextChoices):
    """Lifecycle and operational status of a volunteer profile."""

    APPLICANT = "APPLICANT", _("Applicant")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    INTERVIEW_SCHEDULED = "INTERVIEW_SCHEDULED", _("Interview Scheduled")
    APPROVED = "APPROVED", _("Approved")
    REGISTERED = "REGISTERED", _("Registered")
    ONBOARDING = "ONBOARDING", _("Onboarding")
    ACTIVE = "ACTIVE", _("Active")
    ASSIGNED = "ASSIGNED", _("Assigned")
    ON_LEAVE = "ON_LEAVE", _("On Leave")
    SUSPENDED = "SUSPENDED", _("Suspended")
    INACTIVE = "INACTIVE", _("Inactive")
    EXITED = "EXITED", _("Exited")
    ALUMNI = "ALUMNI", _("Alumni")
    ARCHIVED = "ARCHIVED", _("Archived")


class VolunteerCategory(models.TextChoices):
    """Categories defining volunteer engagement context."""

    COMMUNITY = "COMMUNITY", _("Community Volunteer")
    STUDENT = "STUDENT", _("Student Volunteer")
    YOUTH = "YOUTH", _("Youth Volunteer")
    PROFESSIONAL = "PROFESSIONAL", _("Professional Volunteer")
    TECHNICAL = "TECHNICAL", _("Technical Volunteer")
    PROGRAM = "PROGRAM", _("Program Volunteer")
    EVENT = "EVENT", _("Event Volunteer")
    FIELD = "FIELD", _("Field Volunteer")
    REMOTE = "REMOTE", _("Remote Volunteer")
    INTERNATIONAL = "INTERNATIONAL", _("International Volunteer")


class VolunteerType(models.TextChoices):
    """Modes of volunteer service delivery."""

    FULL_TIME = "FULL_TIME", _("Full-Time Volunteer")
    PART_TIME = "PART_TIME", _("Part-Time Volunteer")
    PROJECT_BASED = "PROJECT_BASED", _("Project-Based Volunteer")
    EVENT = "EVENT", _("Event Volunteer")
    ONLINE = "ONLINE", _("Online / Virtual Volunteer")
    FIELD = "FIELD", _("Field Volunteer")
    SPECIALIST = "SPECIALIST", _("Specialist Volunteer")
    MENTOR = "MENTOR", _("Mentor")
    TRAINER = "TRAINER", _("Trainer")
    ADVISORY = "ADVISORY", _("Advisory Volunteer")


class VolunteerLevel(models.TextChoices):
    """Organizational tier of volunteer deployment."""

    NATIONAL = "NATIONAL", _("National Level")
    REGIONAL = "REGIONAL", _("Regional Level")
    DISTRICT = "DISTRICT", _("District Level")
    COMMUNITY = "COMMUNITY", _("Community Level")
    TEAM = "TEAM", _("Team Level")


class AvailabilityType(models.TextChoices):
    """Configurable availability options for scheduling."""

    FULL_TIME = "FULL_TIME", _("Full-Time")
    PART_TIME = "PART_TIME", _("Part-Time")
    WEEKDAYS = "WEEKDAYS", _("Weekdays")
    WEEKENDS = "WEEKENDS", _("Weekends")
    EVENINGS = "EVENINGS", _("Evenings")
    REMOTE = "REMOTE", _("Remote / Online")
    FIELD = "FIELD", _("Field-Based")
    SEASONAL = "SEASONAL", _("Seasonal")


class AttendanceStatus(models.TextChoices):
    """Attendance log status."""

    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    EXCUSED = "EXCUSED", _("Excused")
    LATE = "LATE", _("Late")
    REMOTE = "REMOTE", _("Remote Participation")


class AttendanceCategory(models.TextChoices):
    """Types of activities for attendance tracking."""

    DAILY = "DAILY", _("Daily Service")
    WEEKLY = "WEEKLY", _("Weekly Service")
    MONTHLY = "MONTHLY", _("Monthly Service")
    MEETING = "MEETING", _("Meeting")
    TRAINING = "TRAINING", _("Training Session")
    OUTREACH = "OUTREACH", _("Community Outreach")
    WORKSHOP = "WORKSHOP", _("Workshop")
    CAMPAIGN = "CAMPAIGN", _("Campaign Activity")


class LeaveType(models.TextChoices):
    """Supported volunteer leave types."""

    ANNUAL = "ANNUAL", _("Annual Leave")
    MEDICAL = "MEDICAL", _("Medical / Sick Leave")
    STUDY = "STUDY", _("Study Leave")
    PERSONAL = "PERSONAL", _("Personal Leave")
    COMPASSIONATE = "COMPASSIONATE", _("Compassionate Leave")


class LeaveStatus(models.TextChoices):
    """Workflow status of a leave application."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class ExitReason(models.TextChoices):
    """Reasons for volunteer exit."""

    RESIGNATION = "RESIGNATION", _("Resignation")
    CONTRACT_COMPLETION = "CONTRACT_COMPLETION", _("Contract Completion")
    DISMISSAL = "DISMISSAL", _("Dismissal / Termination")
    RETIREMENT = "RETIREMENT", _("Retirement")
    TRANSFER = "TRANSFER", _("Transfer")
    ALUMNI_TRANSITION = "ALUMNI_TRANSITION", _("Transition to Alumni")
    OTHER = "OTHER", _("Other")


class ExitStatus(models.TextChoices):
    """Lifecycle status of exit processing."""

    INITIATED = "INITIATED", _("Initiated")
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED", _("Exit Interview Completed")
    CLEARANCE_PENDING = "CLEARANCE_PENDING", _("Clearance Pending")
    APPROVED = "APPROVED", _("Approved")
    EXITED = "EXITED", _("Exited")
    ALUMNI = "ALUMNI", _("Transferred to Alumni")


class RecognitionCategory(models.TextChoices):
    """Types of recognition and awards."""

    CERTIFICATE = "CERTIFICATE", _("Certificate of Service")
    APPRECIATION_AWARD = "APPRECIATION_AWARD", _("Appreciation Award")
    VOLUNTEER_OF_MONTH = "VOLUNTEER_OF_MONTH", _("Volunteer of the Month")
    YEARS_OF_SERVICE = "YEARS_OF_SERVICE", _("Years of Service Award")
    ACHIEVEMENT_BADGE = "ACHIEVEMENT_BADGE", _("Achievement Badge")
    PUBLIC_RECOGNITION = "PUBLIC_RECOGNITION", _("Public Recognition")


class DisciplinaryType(models.TextChoices):
    """Categories of disciplinary action."""

    VERBAL_WARNING = "VERBAL_WARNING", _("Verbal Warning")
    WRITTEN_WARNING = "WRITTEN_WARNING", _("Written Warning")
    SUSPENSION = "SUSPENSION", _("Suspension")
    TERMINATION = "TERMINATION", _("Termination")


class DisciplinaryStatus(models.TextChoices):
    """Status of disciplinary record."""

    PENDING = "PENDING", _("Pending Investigation")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPLIED = "APPLIED", _("Action Applied")
    APPEALED = "APPEALED", _("Appealed")
    RESOLVED = "RESOLVED", _("Resolved")
    DISMISSED = "DISMISSED", _("Dismissed")


class WelfareCategory(models.TextChoices):
    """Categories of welfare support."""

    WELFARE_REQUEST = "WELFARE_REQUEST", _("Welfare Request")
    COUNSELING_REFERRAL = "COUNSELING_REFERRAL", _("Counseling Referral")
    MEDICAL_SUPPORT = "MEDICAL_SUPPORT", _("Medical Support")
    EMERGENCY_ASSISTANCE = "EMERGENCY_ASSISTANCE", _("Emergency Assistance")


class SkillProficiency(models.TextChoices):
    """Skill proficiency ratings."""

    BEGINNER = "BEGINNER", _("Beginner")
    INTERMEDIATE = "INTERMEDIATE", _("Intermediate")
    ADVANCED = "ADVANCED", _("Advanced")
    EXPERT = "EXPERT", _("Expert")


class CommunicationChannel(models.TextChoices):
    """Channels used to communicate with volunteers."""

    IN_APP = "IN_APP", _("In-app notification")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    PHONE = "PHONE", _("Phone call")
    LETTER = "LETTER", _("Letter / Post")
    NEWSLETTER = "NEWSLETTER", _("Newsletter")
    OTHER = "OTHER", _("Other")


class ActivityCategory(models.TextChoices):
    """Categories for volunteer activity logs."""

    MEETING = "MEETING", _("Meeting")
    TRAINING = "TRAINING", _("Training Session")
    OUTREACH = "OUTREACH", _("Community Outreach")
    PROGRAM = "PROGRAM", _("Program Implementation")
    WORKSHOP = "WORKSHOP", _("Workshop")
    CONFERENCE = "CONFERENCE", _("Conference")
    CAMPAIGN = "CAMPAIGN", _("Campaign Activity")
    SERVICE_DAY = "SERVICE_DAY", _("Volunteer Service Day")
    OTHER = "OTHER", _("Other")


class VolunteerDocumentStatus(models.TextChoices):
    """Lifecycle status of a volunteer document."""

    DRAFT = "DRAFT", _("Draft")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ARCHIVED = "ARCHIVED", _("Archived")


class DisciplinaryDecision(models.TextChoices):
    """Outcome decisions for a disciplinary record."""

    NO_ACTION = "NO_ACTION", _("No Further Action")
    VERBAL_WARNING = "VERBAL_WARNING", _("Verbal Warning")
    WRITTEN_WARNING = "WRITTEN_WARNING", _("Written Warning")
    SUSPENSION = "SUSPENSION", _("Suspension")
    TERMINATION = "TERMINATION", _("Termination")


class RecruitmentStatus(models.TextChoices):
    """Recruitment campaign status."""

    DRAFT = "DRAFT", _("Draft")
    OPEN = "OPEN", _("Open for Applications")
    CLOSED = "CLOSED", _("Closed")
    CANCELLED = "CANCELLED", _("Cancelled")


class ApplicationStatus(models.TextChoices):
    """Individual application status."""

    SUBMITTED = "SUBMITTED", _("Submitted")
    RETURNED = "RETURNED", _("Returned for correction")
    UNDER_SCREENING = "UNDER_SCREENING", _("Under Screening")
    SHORTLISTED = "SHORTLISTED", _("Shortlisted for Interview")
    INTERVIEWED = "INTERVIEWED", _("Interviewed")
    APPROVED = "APPROVED", _("Approved for Onboarding")
    REJECTED = "REJECTED", _("Rejected")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class VolunteerAuditAction(models.TextChoices):
    """Audited actions for immutable volunteer audit log."""

    CREATED = "CREATED", _("Volunteer profile created")
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED", _("Application submitted")
    APPLICATION_REVIEWED = "APPLICATION_REVIEWED", _("Application reviewed")
    SCREENING_COMPLETED = "SCREENING_COMPLETED", _("Screening completed")
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED", _("Interview completed")
    ONBOARDING_COMPLETED = "ONBOARDING_COMPLETED", _("Onboarding completed")
    UPDATED = "UPDATED", _("Volunteer profile updated")
    STATUS_CHANGED = "STATUS_CHANGED", _("Volunteer status changed")
    DEPLOYED = "DEPLOYED", _("Volunteer deployed")
    ATTENDANCE_LOGGED = "ATTENDANCE_LOGGED", _("Attendance logged")
    TRAINING_COMPLETED = "TRAINING_COMPLETED", _("Training recorded")
    REVIEWED = "REVIEWED", _("Performance review completed")
    AWARDED = "AWARDED", _("Recognition awarded")
    LEAVE_APPROVED = "LEAVE_APPROVED", _("Leave approved")
    LEAVE_REJECTED = "LEAVE_REJECTED", _("Leave rejected")
    EXPORTED = "EXPORTED", _("Volunteer data exported")
    DOCUMENT_DOWNLOADED = "DOCUMENT_DOWNLOADED", _("Document downloaded")
    EXITED = "EXITED", _("Volunteer exited")
    ARCHIVED = "ARCHIVED", _("Volunteer profile archived")
    RESTORED = "RESTORED", _("Volunteer profile restored")
    ACTIVITY_LOGGED = "ACTIVITY_LOGGED", _("Volunteer activity logged")
    DISCIPLINARY_OPENED = "DISCIPLINARY_OPENED", _("Disciplinary record opened")
    DISCIPLINARY_DECIDED = "DISCIPLINARY_DECIDED", _("Disciplinary record decided")
    DISCIPLINARY_REOPENED = "DISCIPLINARY_REOPENED", _("Disciplinary record reopened")
    COMMUNICATION_SENT = "COMMUNICATION_SENT", _("Volunteer communication recorded")
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", _("Volunteer document uploaded")
    DOCUMENT_APPROVED = "DOCUMENT_APPROVED", _("Volunteer document approved")
    DOCUMENT_REJECTED = "DOCUMENT_REJECTED", _("Volunteer document rejected")
    DOCUMENT_ARCHIVED = "DOCUMENT_ARCHIVED", _("Volunteer document archived")
