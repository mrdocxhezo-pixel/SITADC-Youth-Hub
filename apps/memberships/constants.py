"""Constants for the membership management module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class MembershipCategory(models.TextChoices):
    """Membership categories supported by the organization."""

    FOUNDING = "FOUNDING", _("Founding Member")
    ORDINARY = "ORDINARY", _("Ordinary Member")
    STUDENT = "STUDENT", _("Student Member")
    YOUTH = "YOUTH", _("Youth Member")
    VOLUNTEER = "VOLUNTEER", _("Volunteer Member")
    ASSOCIATE = "ASSOCIATE", _("Associate Member")
    HONORARY = "HONORARY", _("Honorary Member")
    LIFE = "LIFE", _("Life Member")
    INSTITUTIONAL = "INSTITUTIONAL", _("Institutional Member")
    PARTNER_REPRESENTATIVE = "PARTNER_REPRESENTATIVE", _("Partner Representative")


class MembershipType(models.TextChoices):
    """Types of membership engagement."""

    INDIVIDUAL = "INDIVIDUAL", _("Individual Membership")
    ORGANIZATIONAL = "ORGANIZATIONAL", _("Organizational Membership")
    INSTITUTIONAL = "INSTITUTIONAL", _("Institutional Membership")
    COMMUNITY = "COMMUNITY", _("Community Membership")
    AFFILIATE = "AFFILIATE", _("Affiliate Membership")
    HONORARY = "HONORARY", _("Honorary Membership")


class MembershipLevel(models.TextChoices):
    """Organizational levels of membership."""

    NATIONAL = "NATIONAL", _("National")
    REGIONAL = "REGIONAL", _("Regional")
    DISTRICT = "DISTRICT", _("District")
    COMMUNITY = "COMMUNITY", _("Community")
    TEAM = "TEAM", _("Team")


class MembershipStatus(models.TextChoices):
    """Lifecycle status for a membership record."""

    PENDING = "PENDING", _("Pending")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    SUSPENDED = "SUSPENDED", _("Suspended")
    EXPIRED = "EXPIRED", _("Expired")
    TERMINATED = "TERMINATED", _("Terminated")
    ARCHIVED = "ARCHIVED", _("Archived")


class ApplicationStatus(models.TextChoices):
    """Workflow status for a membership application."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    RETURNED = "RETURNED", _("Returned for Correction")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class RenewalStatus(models.TextChoices):
    """Status of a membership renewal request."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    EXPIRED = "EXPIRED", _("Expired")


class AttendanceStatus(models.TextChoices):
    """Attendance record status."""

    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    EXCUSED = "EXCUSED", _("Excused")
    LATE = "LATE", _("Late")


class AttendanceType(models.TextChoices):
    """Types of activities for attendance tracking."""

    MEETING = "MEETING", _("Meeting")
    TRAINING = "TRAINING", _("Training")
    WORKSHOP = "WORKSHOP", _("Workshop")
    COMMUNITY_OUTREACH = "COMMUNITY_OUTREACH", _("Community Outreach")
    CONFERENCE = "CONFERENCE", _("Conference")
    PROGRAM_ACTIVITY = "PROGRAM_ACTIVITY", _("Program Activity")
    AGM = "AGM", _("Annual General Meeting")
    OTHER = "OTHER", _("Other")


class TerminationReason(models.TextChoices):
    """Reasons for membership termination."""

    VOLUNTARY_RESIGNATION = "VOLUNTARY_RESIGNATION", _("Voluntary Resignation")
    EXPIRED_MEMBERSHIP = "EXPIRED_MEMBERSHIP", _("Expired Membership")
    POLICY_VIOLATION = "POLICY_VIOLATION", _("Policy Violation")
    DISCIPLINARY_ACTION = "DISCIPLINARY_ACTION", _("Disciplinary Action")
    DEATH = "DEATH", _("Death")
    ORGANIZATIONAL_RESTRUCTURING = (
        "ORGANIZATIONAL_RESTRUCTURING",
        _("Organizational Restructuring"),
    )
    OTHER = "OTHER", _("Other")


class MembershipAuditAction(models.TextChoices):
    """Audit actions for immutable membership audit log."""

    CREATED = "CREATED", _("Created")
    UPDATED = "UPDATED", _("Updated")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    RETURNED = "RETURNED", _("Returned")
    ACTIVATED = "ACTIVATED", _("Activated")
    SUSPENDED = "SUSPENDED", _("Suspended")
    REINSTATED = "REINSTATED", _("Reinstated")
    RENEWED = "RENEWED", _("Renewed")
    UPGRADED = "UPGRADED", _("Upgraded")
    TRANSFERRED = "TRANSFERRED", _("Transferred")
    TERMINATED = "TERMINATED", _("Terminated")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    DELETED = "DELETED", _("Deleted")
    EXPORTED = "EXPORTED", _("Exported")
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED", _("Document Uploaded")
    PAYMENT_RECORDED = "PAYMENT_RECORDED", _("Payment Recorded")
    STATUS_CHANGED = "STATUS_CHANGED", _("Status Changed")
    REVOKED = "REVOKED", _("Card Revoked")
    EXITED = "EXITED", _("Member Exited")
    EXIT_INITIATED = "EXIT_INITIATED", _("Exit Initiated")
    COMMUNICATION_SENT = "COMMUNICATION_SENT", _("Communication Sent")
    CARD_ISSUED = "CARD_ISSUED", _("Card Issued")


class EducationLevel(models.TextChoices):
    """Education level choices."""

    NO_FORMAL_EDUCATION = "NO_FORMAL_EDUCATION", _("No Formal Education")
    PRIMARY = "PRIMARY", _("Primary")
    JUNIOR_SECONDARY = "JUNIOR_SECONDARY", _("Junior Secondary")
    SENIOR_SECONDARY = "SENIOR_SECONDARY", _("Senior Secondary")
    CERTIFICATE = "CERTIFICATE", _("Certificate")
    DIPLOMA = "DIPLOMA", _("Diploma")
    DEGREE = "DEGREE", _("Degree")
    POSTGRADUATE = "POSTGRADUATE", _("Postgraduate")
    DOCTORATE = "DOCTORATE", _("Doctorate")
    OTHER = "OTHER", _("Other")


class Gender(models.TextChoices):
    """Gender choices."""

    MALE = "MALE", _("Male")
    FEMALE = "FEMALE", _("Female")
    NON_BINARY = "NON_BINARY", _("Non-Binary")
    PREFER_NOT_TO_SAY = "PREFER_NOT_TO_SAY", _("Prefer Not to Say")


class PaymentMethod(models.TextChoices):
    """Payment methods for membership fees."""

    CASH = "CASH", _("Cash")
    BANK_TRANSFER = "BANK_TRANSFER", _("Bank Transfer")
    MOBILE_MONEY = "MOBILE_MONEY", _("Mobile Money")
    CHEQUE = "CHEQUE", _("Cheque")
    ONLINE = "ONLINE", _("Online Payment")
    OTHER = "OTHER", _("Other")


class PaymentStatus(models.TextChoices):
    """Payment status for membership fees."""

    PENDING = "PENDING", _("Pending")
    PAID = "PAID", _("Paid")
    PARTIAL = "PARTIAL", _("Partial")
    OVERDUE = "OVERDUE", _("Overdue")
    WAIVED = "WAIVED", _("Waived")
    REFUNDED = "REFUNDED", _("Refunded")


class CardStatus(models.TextChoices):
    """Lifecycle status of a membership card."""

    DRAFT = "DRAFT", _("Draft")
    ISSUED = "ISSUED", _("Issued")
    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    REVOKED = "REVOKED", _("Revoked")
    REPLACED = "REPLACED", _("Replaced")


class ExitType(models.TextChoices):
    """Reasons for exiting the organization's membership."""

    VOLUNTARY_RESIGNATION = "VOLUNTARY_RESIGNATION", _("Voluntary Resignation")
    EXPIRED_MEMBERSHIP = "EXPIRED_MEMBERSHIP", _("Expired Membership")
    POLICY_VIOLATION = "POLICY_VIOLATION", _("Policy Violation")
    DISCIPLINARY_ACTION = "DISCIPLINARY_ACTION", _("Disciplinary Action")
    DEATH = "DEATH", _("Death")
    TRANSFER_OUT = "TRANSFER_OUT", _("Transfer Out")
    ORGANIZATIONAL_RESTRUCTURING = (
        "ORGANIZATIONAL_RESTRUCTURING",
        _("Organizational Restructuring"),
    )
    ALUMNI_TRANSITION = "ALUMNI_TRANSITION", _("Transition to Alumni")
    OTHER = "OTHER", _("Other")


class ExitStatus(models.TextChoices):
    """Lifecycle status of a membership exit record."""

    INITIATED = "INITIATED", _("Initiated")
    INTERVIEW_COMPLETED = "INTERVIEW_COMPLETED", _("Exit Interview Completed")
    CLEARANCE_PENDING = "CLEARANCE_PENDING", _("Clearance Pending")
    APPROVED = "APPROVED", _("Approved")
    EXITED = "EXITED", _("Exited")
    ALUMNI = "ALUMNI", _("Transferred to Alumni")


class LeaveType(models.TextChoices):
    """Supported membership leave types."""

    ANNUAL = "ANNUAL", _("Annual Leave")
    MEDICAL = "MEDICAL", _("Medical / Sick Leave")
    STUDY = "STUDY", _("Study Leave")
    PERSONAL = "PERSONAL", _("Personal Leave")
    COMPASSIONATE = "COMPASSIONATE", _("Compassionate Leave")


class LeaveStatus(models.TextChoices):
    """Workflow status of a membership leave application."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class ParticipationType(models.TextChoices):
    """Types of activities for member participation records."""

    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    CAMPAIGN = "CAMPAIGN", _("Campaign")
    COMMUNITY_ACTIVITY = "COMMUNITY_ACTIVITY", _("Community Activity")
    TRAINING = "TRAINING", _("Training")
    CONFERENCE = "CONFERENCE", _("Conference")
    COMMITTEE = "COMMITTEE", _("Committee")
    WORKING_GROUP = "WORKING_GROUP", _("Working Group")
    EVENT = "EVENT", _("Event")
    VOLUNTEER_ACTIVITY = "VOLUNTEER_ACTIVITY", _("Volunteer Activity")
    OTHER = "OTHER", _("Other")


class ParticipationStatus(models.TextChoices):
    """Status of a participation record."""

    ENROLLED = "ENROLLED", _("Enrolled")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class RecognitionType(models.TextChoices):
    """Types of recognition and awards for members."""

    CERTIFICATE = "CERTIFICATE", _("Certificate of Appreciation")
    APPRECIATION_LETTER = "APPRECIATION_LETTER", _("Appreciation Letter")
    MEMBER_OF_MONTH = "MEMBER_OF_MONTH", _("Member of the Month")
    YEARS_OF_SERVICE = "YEARS_OF_SERVICE", _("Years of Service Award")
    ACHIEVEMENT_BADGE = "ACHIEVEMENT_BADGE", _("Achievement Badge")
    PUBLIC_RECOGNITION = "PUBLIC_RECOGNITION", _("Public Recognition")
    EXCELLENCE_AWARD = "EXCELLENCE_AWARD", _("Excellence Award")
    OTHER = "OTHER", _("Other")


class DocumentCategory(models.TextChoices):
    """Categories of membership documents."""

    APPLICATION_FORM = "APPLICATION_FORM", _("Application Form")
    IDENTIFICATION = "IDENTIFICATION", _("Identification Document")
    MEMBERSHIP_AGREEMENT = "MEMBERSHIP_AGREEMENT", _("Membership Agreement")
    PASSPORT_PHOTO = "PASSPORT_PHOTO", _("Passport Photograph")
    ACADEMIC_CERTIFICATE = "ACADEMIC_CERTIFICATE", _("Academic Certificate")
    PROFESSIONAL_CERTIFICATE = "PROFESSIONAL_CERTIFICATE", _("Professional Certificate")
    MEMBERSHIP_CARD = "MEMBERSHIP_CARD", _("Membership Card")
    PAYMENT_RECEIPT = "PAYMENT_RECEIPT", _("Payment Receipt")
    SIGNED_DECLARATION = "SIGNED_DECLARATION", _("Signed Declaration")
    SUPPORTING_DOCUMENT = "SUPPORTING_DOCUMENT", _("Supporting Document")
    OTHER = "OTHER", _("Other")


class DocumentStatus(models.TextChoices):
    """Status of a membership document record."""

    DRAFT = "DRAFT", _("Draft")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending Approval")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ARCHIVED = "ARCHIVED", _("Archived")


class FeeAdjustmentType(models.TextChoices):
    """Types of membership fee adjustments."""

    DISCOUNT = "DISCOUNT", _("Discount")
    WAIVER = "WAIVER", _("Waiver")
    SURCHARGE = "SURCHARGE", _("Surcharge")
    CORRECTION = "CORRECTION", _("Correction")


class AdjustmentStatus(models.TextChoices):
    """Status of a membership fee adjustment."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class CommunicationType(models.TextChoices):
    """Types of membership communications."""

    EMAIL = "EMAIL", _("Email")
    IN_APP = "IN_APP", _("In-App Notification")
    SMS = "SMS", _("SMS")
    NEWSLETTER = "NEWSLETTER", _("Newsletter")
    ANNOUNCEMENT = "ANNOUNCEMENT", _("Announcement")
    EVENT_INVITATION = "EVENT_INVITATION", _("Event Invitation")
    RENEWAL_REMINDER = "RENEWAL_REMINDER", _("Renewal Reminder")
    OTHER = "OTHER", _("Other")


class CommunicationStatus(models.TextChoices):
    """Status of a membership communication."""

    DRAFT = "DRAFT", _("Draft")
    SCHEDULED = "SCHEDULED", _("Scheduled")
    SENT = "SENT", _("Sent")
    FAILED = "FAILED", _("Failed")


class ComplaintType(models.TextChoices):
    """Categories of member complaints (confidential)."""

    HARASSMENT = "HARASSMENT", _("Harassment")
    DISCRIMINATION = "DISCRIMINATION", _("Discrimination")
    MISCONDUCT = "MISCONDUCT", _("Misconduct")
    FINANCIAL = "FINANCIAL", _("Financial")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    OTHER = "OTHER", _("Other")


class ComplaintStatus(models.TextChoices):
    """Status of a member complaint record."""

    RECEIVED = "RECEIVED", _("Received")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    INVESTIGATING = "INVESTIGATING", _("Investigating")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")


class DisciplinaryType(models.TextChoices):
    """Categories of disciplinary action against a member."""

    VERBAL_WARNING = "VERBAL_WARNING", _("Verbal Warning")
    WRITTEN_WARNING = "WRITTEN_WARNING", _("Written Warning")
    SUSPENSION = "SUSPENSION", _("Suspension")
    TERMINATION = "TERMINATION", _("Termination")


class DisciplinaryStatus(models.TextChoices):
    """Status of a disciplinary record."""

    PENDING = "PENDING", _("Pending Investigation")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPLIED = "APPLIED", _("Action Applied")
    APPEALED = "APPEALED", _("Appealed")
    RESOLVED = "RESOLVED", _("Resolved")
    DISMISSED = "DISMISSED", _("Dismissed")


class UpgradeStatus(models.TextChoices):
    """Status of a membership upgrade request."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class TransferStatus(models.TextChoices):
    """Status of a membership transfer request."""

    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    CANCELLED = "CANCELLED", _("Cancelled")


class BenefitStatus(models.TextChoices):
    """Status of a member benefit assignment."""

    ACTIVE = "ACTIVE", _("Active")
    EXPIRED = "EXPIRED", _("Expired")
    REVOKED = "REVOKED", _("Revoked")


class MemberResponsibility(models.TextChoices):
    """Documented member responsibilities acknowledged at registration."""

    POLICY_COMPLIANCE = "POLICY_COMPLIANCE", _("Comply with organizational policies")
    FEE_PAYMENT = "FEE_PAYMENT", _("Pay applicable membership fees")
    ACTIVE_PARTICIPATION = "ACTIVE_PARTICIPATION", _("Participate actively")
    ORGANIZATIONAL_VALUES = "ORGANIZATIONAL_VALUES", _("Respect organizational values")
    TIMELY_REPORTING = "TIMELY_REPORTING", _("Report timely where applicable")
    ETHICAL_CONDUCT = "ETHICAL_CONDUCT", _("Maintain ethical conduct")
    COMMUNITY_ENGAGEMENT = "COMMUNITY_ENGAGEMENT", _("Engage with the community")
    ASSET_PROTECTION = "ASSET_PROTECTION", _("Protect organizational assets")
