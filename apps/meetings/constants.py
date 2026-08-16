"""Constants for the Phase 24 Calendar & Meetings module.

Every status, type and configuration value used by the module is declared here
so models, forms, services, views and exports share a single vocabulary.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

# Reference numbering module identifiers.
REFERENCE_MODULE_CALENDARS = "calendars"
REFERENCE_MODULE_EVENTS = "events"
REFERENCE_MODULE_MEETINGS = "meetings"

# Pattern used for calendar / event / meeting reference numbers, matching the
# Phase 24 specification examples (SITADC-CAL-2026-000001 etc.).
REFERENCE_PATTERN = "{ORG}-{PREFIX}-{YEAR}-{SEQUENCE}"
REFERENCE_ORGANIZATION_CODE = "SITADC"
REFERENCE_SEQUENCE_LENGTH = 6


class CalendarType(models.TextChoices):
    """Type of organizational calendar."""

    PERSONAL = "PERSONAL", _("Personal")
    TEAM = "TEAM", _("Team")
    UNIT = "UNIT", _("Unit")
    DIRECTORATE = "DIRECTORATE", _("Directorate")
    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    GOVERNANCE = "GOVERNANCE", _("Governance")
    ORGANIZATIONAL = "ORGANIZATIONAL", _("Organizational")
    REGIONAL = "REGIONAL", _("Regional")
    DISTRICT = "DISTRICT", _("District")
    COMMUNITY = "COMMUNITY", _("Community")


class CalendarVisibility(models.TextChoices):
    """Who may see a calendar and its events."""

    PRIVATE = "PRIVATE", _("Private")
    TEAM = "TEAM", _("Team")
    UNIT = "UNIT", _("Unit")
    DIRECTORATE = "DIRECTORATE", _("Directorate")
    REGIONAL = "REGIONAL", _("Regional")
    DISTRICT = "DISTRICT", _("District")
    COMMUNITY = "COMMUNITY", _("Community")
    ORGANIZATIONAL = "ORGANIZATIONAL", _("Organizational")
    PUBLIC = "PUBLIC", _("Public")


class CalendarShareLevel(models.TextChoices):
    """Permission level granted by a calendar share."""

    VIEW_AVAILABILITY = "VIEW_AVAILABILITY", _("View availability")
    VIEW_EVENTS = "VIEW_EVENTS", _("View events")
    CREATE_EVENTS = "CREATE_EVENTS", _("Create events")
    EDIT_EVENTS = "EDIT_EVENTS", _("Edit events")
    MANAGE = "MANAGE", _("Manage calendar")


class EventType(models.TextChoices):
    """Type of calendar event."""

    MEETING = "MEETING", _("Meeting")
    TRAINING = "TRAINING", _("Training")
    WORKSHOP = "WORKSHOP", _("Workshop")
    CONFERENCE = "CONFERENCE", _("Conference")
    FIELD_VISIT = "FIELD_VISIT", _("Field Visit")
    MONITORING = "MONITORING", _("Monitoring Visit")
    DEADLINE = "DEADLINE", _("Deadline")
    MILESTONE = "MILESTONE", _("Milestone")
    PUBLIC_EVENT = "PUBLIC_EVENT", _("Public Event")
    FUNDRAISER = "FUNDRAISER", _("Fundraiser")
    MEETING_REVIEW = "MEETING_REVIEW", _("Review Meeting")
    POLICY_DEADLINE = "POLICY_DEADLINE", _("Policy/Governance Deadline")
    REPORT_DEADLINE = "REPORT_DEADLINE", _("Report Deadline")
    PROGRAM_ACTIVITY = "PROGRAM_ACTIVITY", _("Program Activity")
    PROJECT_ACTIVITY = "PROJECT_ACTIVITY", _("Project Activity")
    MEAL_ACTIVITY = "MEAL_ACTIVITY", _("MEAL Activity")
    OTHER = "OTHER", _("Other")


class EventStatus(models.TextChoices):
    """Lifecycle status for a calendar event."""

    DRAFT = "DRAFT", _("Draft")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    COMPLETED = "COMPLETED", _("Completed")
    POSTPONED = "POSTPONED", _("Postponed")
    RESCHEDULED = "RESCHEDULED", _("Rescheduled")
    CANCELLED = "CANCELLED", _("Cancelled")
    ARCHIVED = "ARCHIVED", _("Archived")


class EventPriority(models.TextChoices):
    """Priority levels for calendar events."""

    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


class MeetingType(models.TextChoices):
    """Type of meeting."""

    BOARD = "BOARD", _("Board Meeting")
    EXECUTIVE = "EXECUTIVE", _("Executive Committee Meeting")
    AGM = "AGM", _("Annual General Meeting")
    NEC = "NEC", _("National Executive Committee Meeting")
    STAFF = "STAFF", _("Staff Meeting")
    TEAM = "TEAM", _("Team Meeting")
    PROGRAM = "PROGRAM", _("Program Meeting")
    PROJECT = "PROJECT", _("Project Meeting")
    PARTNER = "PARTNER", _("Partner Meeting")
    DONOR = "DONOR", _("Donor Meeting")
    STAKEHOLDER = "STAKEHOLDER", _("Stakeholder Consultation")
    REGIONAL = "REGIONAL", _("Regional Meeting")
    DISTRICT = "DISTRICT", _("District Meeting")
    COMMUNITY = "COMMUNITY", _("Community Meeting")
    GOVERNANCE = "GOVERNANCE", _("Governance Meeting")
    REVIEW = "REVIEW", _("Review Meeting")
    PLANNING = "PLANNING", _("Planning Meeting")
    REPORTING = "REPORTING", _("Reporting Meeting")
    AD_HOC = "AD_HOC", _("Ad Hoc Meeting")
    EMERGENCY = "EMERGENCY", _("Emergency Meeting")
    DISCIPLINARY = "DISCIPLINARY", _("Disciplinary Meeting")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding Meeting")
    FINANCIAL = "FINANCIAL", _("Financial Review Meeting")


class MeetingStatus(models.TextChoices):
    """Lifecycle status for a meeting."""

    DRAFT = "DRAFT", _("Draft")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    INVITATIONS_SENT = "INVITATIONS_SENT", _("Invitations Sent")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    COMPLETED = "COMPLETED", _("Completed")
    MINUTES_DRAFTED = "MINUTES_DRAFTED", _("Minutes Drafted")
    MINUTES_UNDER_REVIEW = "MINUTES_UNDER_REVIEW", _("Minutes Under Review")
    MINUTES_APPROVED = "MINUTES_APPROVED", _("Minutes Approved")
    CLOSED = "CLOSED", _("Closed")
    POSTPONED = "POSTPONED", _("Postponed")
    RESCHEDULED = "RESCHEDULED", _("Rescheduled")
    CANCELLED = "CANCELLED", _("Cancelled")
    ARCHIVED = "ARCHIVED", _("Archived")


class MeetingMode(models.TextChoices):
    """Delivery mode of a meeting."""

    IN_PERSON = "IN_PERSON", _("In-Person")
    VIRTUAL = "VIRTUAL", _("Virtual/Online")
    HYBRID = "HYBRID", _("Hybrid")


class VirtualMeetingProvider(models.TextChoices):
    """Supported virtual meeting providers (integration hooks)."""

    ZOOM = "ZOOM", _("Zoom")
    GOOGLE_MEET = "GOOGLE_MEET", _("Google Meet")
    MICROSOFT_TEAMS = "MICROSOFT_TEAMS", _("Microsoft Teams")
    WEBEX = "WEBEX", _("Webex")
    JITSI = "JITSI", _("Jitsi")
    OTHER = "OTHER", _("Other")


class ParticipantType(models.TextChoices):
    """Category of meeting participant."""

    INTERNAL = "INTERNAL", _("Internal")
    EXTERNAL = "EXTERNAL", _("External")
    USER = "USER", _("User")
    LEADER = "LEADER", _("Leader")
    MEMBER = "MEMBER", _("Member")
    VOLUNTEER = "VOLUNTEER", _("Volunteer")
    STAKEHOLDER = "STAKEHOLDER", _("Stakeholder")
    PARTNER = "PARTNER", _("Partner")
    DONOR = "DONOR", _("Donor")
    SPONSOR = "SPONSOR", _("Sponsor")
    GOVERNMENT = "GOVERNMENT", _("Government")
    CONSULTANT = "CONSULTANT", _("Consultant")
    GUEST = "GUEST", _("Guest")


class ParticipantRole(models.TextChoices):
    """Role a participant holds within a meeting."""

    CHAIRPERSON = "CHAIRPERSON", _("Chairperson")
    SECRETARY = "SECRETARY", _("Secretary")
    MINUTE_TAKER = "MINUTE_TAKER", _("Minute Taker")
    FACILITATOR = "FACILITATOR", _("Facilitator")
    PRESENTER = "PRESENTER", _("Presenter")
    ATTENDEE = "ATTENDEE", _("Attendee")
    OBSERVER = "OBSERVER", _("Observer")
    EX_OFFICIO = "EX_OFFICIO", _("Ex-Officio")
    ADVISOR = "ADVISOR", _("Advisor")


class ParticipantStatus(models.TextChoices):
    """Lifecycle status of a participant record."""

    PROPOSED = "PROPOSED", _("Proposed")
    INVITED = "INVITED", _("Invited")
    ACCEPTED = "ACCEPTED", _("Accepted")
    DECLINED = "DECLINED", _("Declined")
    PROVISIONAL = "PROVISIONAL", _("Provisional")
    REMOVED = "REMOVED", _("Removed")


class RSVPStatus(models.TextChoices):
    """A participant's response to an invitation."""

    NO_RESPONSE = "NO_RESPONSE", _("No Response")
    ACCEPTED = "ACCEPTED", _("Accepted")
    TENTATIVE = "TENTATIVE", _("Tentative")
    DECLINED = "DECLINED", _("Declined")


class InvitationStatus(models.TextChoices):
    """Delivery status of an invitation."""

    PENDING = "PENDING", _("Pending")
    QUEUED = "QUEUED", _("Queued")
    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class AttendanceStatus(models.TextChoices):
    """Attendance status for a participant."""

    PRESENT = "PRESENT", _("Present")
    LATE = "LATE", _("Late")
    REMOTE = "REMOTE", _("Remote")
    EXCUSED = "EXCUSED", _("Excused")
    ABSENT = "ABSENT", _("Absent")
    LEFT_EARLY = "LEFT_EARLY", _("Left Early")
    PROXY = "PROXY", _("Proxy")
    NOT_REQUIRED = "NOT_REQUIRED", _("Not Required")


class AttendanceMode(models.TextChoices):
    """How a participant attended."""

    IN_PERSON = "IN_PERSON", _("In-Person")
    ONLINE = "ONLINE", _("Online")
    HYBRID = "HYBRID", _("Hybrid")
    PHONE = "PHONE", _("Phone")
    PROXY = "PROXY", _("Proxy")


class AttendanceVerificationStatus(models.TextChoices):
    """Verification state of an attendance record."""

    UNVERIFIED = "UNVERIFIED", _("Unverified")
    VERIFIED = "VERIFIED", _("Verified")
    REJECTED = "REJECTED", _("Rejected")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")


class QuorumType(models.TextChoices):
    """How quorum is calculated."""

    FIXED_NUMBER = "FIXED_NUMBER", _("Fixed Number")
    PERCENTAGE = "PERCENTAGE", _("Percentage")
    ROLE_BASED = "ROLE_BASED", _("Required Roles Present")


class AgendaStatus(models.TextChoices):
    """Lifecycle status of a meeting agenda."""

    DRAFT = "DRAFT", _("Draft")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    PUBLISHED = "PUBLISHED", _("Published")
    SUPERSEDED = "SUPERSEDED", _("Superseded")


class AgendaItemType(models.TextChoices):
    """Type of agenda item."""

    INFORMATION = "INFORMATION", _("Information")
    DISCUSSION = "DISCUSSION", _("Discussion")
    DECISION = "DECISION", _("Decision Required")
    PRESENTATION = "PRESENTATION", _("Presentation")
    APPROVAL = "APPROVAL", _("Approval")
    MATTERS_ARISING = "MATTERS_ARISING", _("Matters Arising")
    CLOSING = "CLOSING", _("Closing")


class MinutesStatus(models.TextChoices):
    """Lifecycle status of meeting minutes."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted for Review")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    RETURNED = "RETURNED", _("Returned for Correction")
    APPROVED = "APPROVED", _("Approved")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class MinuteSectionType(models.TextChoices):
    """Section types within minutes."""

    OPENING = "OPENING", _("Opening")
    ATTENDANCE = "ATTENDANCE", _("Attendance")
    QUORUM = "QUORUM", _("Quorum")
    AGENDA_ITEM = "AGENDA_ITEM", _("Agenda Item")
    DECISION = "DECISION", _("Decision")
    ACTION_ITEM = "ACTION_ITEM", _("Action Item")
    ADJOURNMENT = "ADJOURNMENT", _("Adjournment")


class DecisionType(models.TextChoices):
    """Types of recorded decisions."""

    RESOLUTION = "RESOLUTION", _("Resolution")
    APPROVAL = "APPROVAL", _("Approval")
    RECOMMENDATION = "RECOMMENDATION", _("Recommendation")
    DIRECTIVE = "DIRECTIVE", _("Directive")
    DEFERRAL = "DEFERRAL", _("Deferral")
    REJECTION = "REJECTION", _("Rejection")
    ENDORSEMENT = "ENDORSEMENT", _("Endorsement")


class DecisionStatus(models.TextChoices):
    """Lifecycle status of a recorded decision."""

    PROPOSED = "PROPOSED", _("Proposed")
    RECORDED = "RECORDED", _("Recorded")
    APPROVED = "APPROVED", _("Approved")
    IMPLEMENTED = "IMPLEMENTED", _("Implemented")
    DEFERRED = "DEFERRED", _("Deferred")
    REJECTED = "REJECTED", _("Rejected")
    SUPERSEDED = "SUPERSEDED", _("Superseded")


class VotingMethod(models.TextChoices):
    """Voting methods permitted for decisions."""

    VOICE = "VOICE", _("Voice Vote")
    SHOW_OF_HANDS = "SHOW_OF_HANDS", _("Show of Hands")
    RECORDED = "RECORDED", _("Recorded Vote")
    BALLOT = "BALLOT", _("Secret Ballot")
    CONSENSUS = "CONSENSUS", _("Consensus")


class VoteType(models.TextChoices):
    """How an individual voted."""

    FOR = "FOR", _("For")
    AGAINST = "AGAINST", _("Against")
    ABSTAIN = "ABSTAIN", _("Abstain")


class ActionStatus(models.TextChoices):
    """Lifecycle status for action items."""

    NOT_STARTED = "NOT_STARTED", _("Not Started")
    ASSIGNED = "ASSIGNED", _("Assigned")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    BLOCKED = "BLOCKED", _("Blocked")
    COMPLETED = "COMPLETED", _("Completed")
    VERIFIED = "VERIFIED", _("Verified")
    CANCELLED = "CANCELLED", _("Cancelled")
    OVERDUE = "OVERDUE", _("Overdue")


class ActionPriority(models.TextChoices):
    """Priority levels for action items."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


class EscalationStatus(models.TextChoices):
    """Escalation state of an action item."""

    NOT_ESCALATED = "NOT_ESCALATED", _("Not Escalated")
    ESCALATED = "ESCALATED", _("Escalated")
    RESOLVED = "RESOLVED", _("Resolved")


class FollowUpType(models.TextChoices):
    """Types of follow-up records on an action item."""

    COMMENT = "COMMENT", _("Comment")
    PROGRESS = "PROGRESS", _("Progress Update")
    REASSIGN = "REASSIGN", _("Reassignment")
    EXTENSION = "EXTENSION", _("Deadline Extension")
    ESCALATION = "ESCALATION", _("Escalation")
    COMPLETION = "COMPLETION", _("Completion")
    VERIFICATION = "VERIFICATION", _("Verification")


class MatterStatus(models.TextChoices):
    """Status of a matter arising from previous minutes."""

    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In Progress")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")


class ReminderType(models.TextChoices):
    """Business triggers for reminders."""

    INVITATION = "INVITATION", _("Meeting Invitation")
    RSVP_DEADLINE = "RSVP_DEADLINE", _("RSVP Deadline")
    MEETING_START = "MEETING_START", _("Meeting Start")
    AGENDA_SUBMISSION = "AGENDA_SUBMISSION", _("Agenda Submission")
    AGENDA_PUBLICATION = "AGENDA_PUBLICATION", _("Agenda Publication")
    DOCUMENT_SUBMISSION = "DOCUMENT_SUBMISSION", _("Document Submission")
    MINUTES_PREPARATION = "MINUTES_PREPARATION", _("Minutes Preparation")
    MINUTES_REVIEW = "MINUTES_REVIEW", _("Minutes Review")
    MINUTES_APPROVAL = "MINUTES_APPROVAL", _("Minutes Approval")
    ACTION_DEADLINE = "ACTION_DEADLINE", _("Action-Item Deadline")
    DECISION_FOLLOW_UP = "DECISION_FOLLOW_UP", _("Decision Follow-Up")
    RECURRING_MEETING = "RECURRING_MEETING", _("Recurring Meeting")


class ReminderRecipientType(models.TextChoices):
    """Who receives a reminder."""

    ORGANIZER = "ORGANIZER", _("Organizer")
    CHAIRPERSON = "CHAIRPERSON", _("Chairperson")
    SECRETARY = "SECRETARY", _("Secretary")
    PARTICIPANTS = "PARTICIPANTS", _("Participants")
    REQUIRED_ATTENDEES = "REQUIRED_ATTENDEES", _("Required Attendees")
    ACTION_OWNER = "ACTION_OWNER", _("Action Owner")
    ALL = "ALL", _("All")


class ReminderChannel(models.TextChoices):
    """Delivery channel for reminders."""

    IN_APP = "IN_APP", _("In-App")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    PUSH = "PUSH", _("Push Notification")


class ReminderStatus(models.TextChoices):
    """Delivery state of a reminder."""

    PENDING = "PENDING", _("Pending")
    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")


class RecurrenceFrequency(models.TextChoices):
    """Supported event recurrence frequencies."""

    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    ANNUALLY = "ANNUALLY", _("Annually")


class VenueType(models.TextChoices):
    """Type of meeting venue."""

    BOARDROOM = "BOARDROOM", _("Boardroom")
    OFFICE = "OFFICE", _("Office")
    TRAINING_ROOM = "TRAINING_ROOM", _("Training Room")
    COMMUNITY_HALL = "COMMUNITY_HALL", _("Community Hall")
    SCHOOL = "SCHOOL", _("School")
    CHURCH = "CHURCH", _("Church")
    ONLINE = "ONLINE", _("Virtual")
    OTHER = "OTHER", _("Other")


class VenueReservationStatus(models.TextChoices):
    """Status of a venue reservation."""

    REQUESTED = "REQUESTED", _("Requested")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    RELEASED = "RELEASED", _("Released")
    CANCELLED = "CANCELLED", _("Cancelled")


class MeetingDocumentType(models.TextChoices):
    """Kind of document linked to a meeting."""

    INVITATION = "INVITATION", _("Invitation")
    AGENDA = "AGENDA", _("Agenda")
    PRESENTATION = "PRESENTATION", _("Presentation")
    REPORT = "REPORT", _("Report")
    BRIEFING = "BRIEFING", _("Briefing Note")
    ATTENDANCE_SHEET = "ATTENDANCE_SHEET", _("Attendance Sheet")
    MINUTES = "MINUTES", _("Minutes")
    DECISION = "DECISION", _("Decision Document")
    RESOLUTION = "RESOLUTION", _("Signed Resolution")
    RECORDING = "RECORDING", _("Recording")
    OTHER = "OTHER", _("Other")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality levels (shared with registers module)."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")


class PublicationStatus(models.TextChoices):
    """Publication scope for meeting outputs."""

    PRIVATE = "PRIVATE", _("Private")
    PARTICIPANTS_ONLY = "PARTICIPANTS_ONLY", _("Participants Only")
    ORGANIZATIONAL = "ORGANIZATIONAL", _("Organizational")
    PUBLIC = "PUBLIC", _("Public")


SENSITIVE_LEVELS = (
    ConfidentialityLevel.RESTRICTED,
    ConfidentialityLevel.CONFIDENTIAL,
    ConfidentialityLevel.HIGHLY_CONFIDENTIAL,
)

NON_SENSITIVE_LEVELS = (
    ConfidentialityLevel.PUBLIC,
    ConfidentialityLevel.INTERNAL,
)

# Meeting statuses that no longer allow scheduling changes.
LOCKED_MEETING_STATUSES = (
    MeetingStatus.COMPLETED,
    MeetingStatus.MINUTES_DRAFTED,
    MeetingStatus.MINUTES_UNDER_REVIEW,
    MeetingStatus.MINUTES_APPROVED,
    MeetingStatus.CLOSED,
    MeetingStatus.CANCELLED,
    MeetingStatus.ARCHIVED,
)

# Meeting statuses that lock attendance changes.
ATTENDANCE_LOCKED_STATUSES = (
    MeetingStatus.MINUTES_DRAFTED,
    MeetingStatus.MINUTES_UNDER_REVIEW,
    MeetingStatus.MINUTES_APPROVED,
    MeetingStatus.CLOSED,
    MeetingStatus.ARCHIVED,
)
