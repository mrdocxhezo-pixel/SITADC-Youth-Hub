"""Constants for the Notifications module."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationCategory(models.TextChoices):
    """Standard notification categories."""

    GENERAL = "GENERAL", _("General")
    SYSTEM = "SYSTEM", _("System")
    ADMINISTRATIVE = "ADMINISTRATIVE", _("Administrative")
    SECURITY = "SECURITY", _("Security")
    GOVERNANCE = "GOVERNANCE", _("Governance")
    LEADERSHIP = "LEADERSHIP", _("Leadership")
    MEMBERSHIP = "MEMBERSHIP", _("Membership")
    VOLUNTEER = "VOLUNTEER", _("Volunteer")
    BENEFICIARY = "BENEFICIARY", _("Beneficiary")
    STAKEHOLDER = "STAKEHOLDER", _("Stakeholder")
    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    MEAL = "MEAL", _("MEAL")
    REPORTS = "REPORTS", _("Reports")
    REVIEW_APPROVAL = "REVIEW_APPROVAL", _("Review and Approval")
    DOCUMENTS = "DOCUMENTS", _("Documents")
    ORGANIZATIONAL_REGISTERS = "ORGANIZATIONAL_REGISTERS", _("Organizational Registers")
    CALENDAR = "CALENDAR", _("Calendar")
    MEETINGS = "MEETINGS", _("Meetings")
    TRAINING = "TRAINING", _("Training")
    FINANCE = "FINANCE", _("Finance")
    PARTNERSHIP = "PARTNERSHIP", _("Partnership")
    RISK_COMPLIANCE = "RISK_COMPLIANCE", _("Risk and Compliance")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    DEADLINES = "DEADLINES", _("Deadlines")
    ANNOUNCEMENTS = "ANNOUNCEMENTS", _("Announcements")


class NotificationType(models.TextChoices):
    """Standard notification types."""

    INFORMATION = "INFORMATION", _("Information")
    SUCCESS = "SUCCESS", _("Success")
    WARNING = "WARNING", _("Warning")
    ACTION_REQUIRED = "ACTION_REQUIRED", _("Action Required")
    REMINDER = "REMINDER", _("Reminder")
    DEADLINE = "DEADLINE", _("Deadline")
    OVERDUE = "OVERDUE", _("Overdue")
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED", _("Approval Required")
    REVIEW_REQUIRED = "REVIEW_REQUIRED", _("Review Required")
    RETURNED = "RETURNED", _("Returned")
    REJECTED = "REJECTED", _("Rejected")
    APPROVED = "APPROVED", _("Approved")
    ASSIGNMENT = "ASSIGNMENT", _("Assignment")
    INVITATION = "INVITATION", _("Invitation")
    MENTION = "MENTION", _("Mention")
    COMMENT = "COMMENT", _("Comment")
    ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")
    SECURITY_ALERT = "SECURITY_ALERT", _("Security Alert")
    SYSTEM_ALERT = "SYSTEM_ALERT", _("System Alert")
    ESCALATION = "ESCALATION", _("Escalation")


class NotificationPriority(models.TextChoices):
    """Notification priority levels."""

    LOW = "LOW", _("Low")
    NORMAL = "NORMAL", _("Normal")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")
    CRITICAL = "CRITICAL", _("Critical")


class NotificationSeverity(models.TextChoices):
    """Notification severity levels."""

    INFO = "INFO", _("Info")
    SUCCESS = "SUCCESS", _("Success")
    WARNING = "WARNING", _("Warning")
    ERROR = "ERROR", _("Error")
    CRITICAL = "CRITICAL", _("Critical")


class NotificationStatus(models.TextChoices):
    """Notification lifecycle status."""

    PENDING = "PENDING", _("Pending")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    QUEUED = "QUEUED", _("Queued")
    SENT = "SENT", _("Sent")
    PARTIALLY_DELIVERED = "PARTIALLY_DELIVERED", _("Partially Delivered")
    DELIVERED = "DELIVERED", _("Delivered")
    FAILED = "FAILED", _("Failed")
    CANCELLED = "CANCELLED", _("Cancelled")
    EXPIRED = "EXPIRED", _("Expired")


class ReadStatus(models.TextChoices):
    """Notification read status."""

    UNREAD = "UNREAD", _("Unread")
    READ = "READ", _("Read")
    ACKNOWLEDGED = "ACKNOWLEDGED", _("Acknowledged")


class DeliveryChannel(models.TextChoices):
    """Notification delivery channels."""

    IN_APP = "IN_APP", _("In-App")
    EMAIL = "EMAIL", _("Email")
    SMS = "SMS", _("SMS")
    PUSH = "PUSH", _("Push")


class DeliveryStatus(models.TextChoices):
    """Individual delivery attempt status."""

    QUEUED = "QUEUED", _("Queued")
    SENT = "SENT", _("Sent")
    DELIVERED = "DELIVERED", _("Delivered")
    FAILED = "FAILED", _("Failed")
    BOUNCED = "BOUNCED", _("Bounced")
    BLOCKED = "BLOCKED", _("Blocked")


class AnnouncementType(models.TextChoices):
    """Announcement types."""

    ORGANIZATION_WIDE = "ORGANIZATION_WIDE", _("Organization-wide")
    DIRECTORATE = "DIRECTORATE", _("Directorate")
    REGIONAL = "REGIONAL", _("Regional")
    DISTRICT = "DISTRICT", _("District")
    COMMUNITY = "COMMUNITY", _("Community")
    TEAM = "TEAM", _("Team")
    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    EVENT = "EVENT", _("Event")
    TRAINING = "TRAINING", _("Training")
    EMERGENCY = "EMERGENCY", _("Emergency Notice")
    POLICY = "POLICY", _("Policy Notice")
    MAINTENANCE = "MAINTENANCE", _("Maintenance Notice")


class AnnouncementAudience(models.TextChoices):
    """Announcement target audiences."""

    EVERYONE = "EVERYONE", _("Everyone")
    SPECIFIC_ROLES = "SPECIFIC_ROLES", _("Specific Roles")
    ORGANIZATION_UNITS = "ORGANIZATION_UNITS", _("Organization Units")
    DIRECTORATES = "DIRECTORATES", _("Directorates")
    REGIONS = "REGIONS", _("Regions")
    DISTRICTS = "DISTRICTS", _("Districts")
    PROGRAMS = "PROGRAMS", _("Programs")
    PROJECTS = "PROJECTS", _("Projects")


class ReminderFrequency(models.TextChoices):
    """Reminder frequency options."""

    IMMEDIATE = "IMMEDIATE", _("Immediate")
    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    ANNUAL = "ANNUAL", _("Annual")
    CUSTOM = "CUSTOM", _("Custom")


class DigestFrequency(models.TextChoices):
    """Digest frequency options."""

    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    NEVER = "NEVER", _("Never")


class EscalationLevel(models.TextChoices):
    """Escalation levels."""

    OWNER = "OWNER", _("Owner")
    SUPERVISOR = "SUPERVISOR", _("Supervisor")
    MANAGER = "MANAGER", _("Manager")
    DIRECTOR = "DIRECTOR", _("Director")
    EXECUTIVE = "EXECUTIVE", _("Executive")
    BOARD = "BOARD", _("Board")


class QuietHoursPolicy(models.TextChoices):
    """Quiet hours policy for non-critical channels."""

    RESPECT = "RESPECT", _("Respect Quiet Hours")
    OVERRIDE = "OVERRIDE", _("Override for Critical")
    IGNORE = "IGNORE", _("Ignore Quiet Hours")


# Reference numbering module code for notifications
REFERENCE_MODULE_NOTIFICATIONS = "notifications"
REFERENCE_MODULE_ANNOUNCEMENTS = "announcements"
REFERENCE_PREFIX_NOTIFICATION = "NTF"
REFERENCE_PREFIX_ANNOUNCEMENT = "ANN"

# Default notification preferences
DEFAULT_NOTIFICATION_PREFERENCES = {
    "in_app_enabled": True,
    "email_enabled": False,
    "sms_enabled": False,
    "push_enabled": False,
    "digest_frequency": DigestFrequency.WEEKLY,
    "quiet_hours_start": "22:00",
    "quiet_hours_end": "07:00",
    "timezone": "Africa/Lusaka",
    "categories": {},
}

# Maximum retry attempts for delivery
MAX_DELIVERY_RETRIES = 3

# Default retry backoff in minutes
DEFAULT_RETRY_BACKOFF_MINUTES = [5, 15, 60]

# Notification expiry defaults (in days)
DEFAULT_NOTIFICATION_EXPIRY_DAYS = 30
DEFAULT_ANNOUNCEMENT_EXPIRY_DAYS = 90

# Template variable allowlist
ALLOWED_TEMPLATE_VARIABLES = frozenset(
    [
        "user_name",
        "user_email",
        "report_reference",
        "report_title",
        "meeting_title",
        "meeting_date",
        "meeting_time",
        "meeting_location",
        "document_title",
        "document_reference",
        "due_date",
        "reviewer_name",
        "program_name",
        "project_name",
        "activity_name",
        "task_name",
        "assignee_name",
        "sender_name",
        "organization_name",
        "reference_number",
        "priority",
        "category",
        "deep_link",
        "action_label",
    ]
)
