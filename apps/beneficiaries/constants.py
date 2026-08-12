"""Domain constants for the Phase 17 Beneficiary Management module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReferenceDataKind(models.TextChoices):
    CATEGORY = "CATEGORY", _("Beneficiary category")
    CLASSIFICATION = "CLASSIFICATION", _("Classification")
    VULNERABILITY = "VULNERABILITY", _("Vulnerability")
    INCLUSION = "INCLUSION", _("Inclusion barrier")
    DISABILITY = "DISABILITY", _("Disability")
    EDUCATION_LEVEL = "EDUCATION_LEVEL", _("Education level")
    OCCUPATION = "OCCUPATION", _("Occupation")
    SKILL = "SKILL", _("Skill")
    INTEREST = "INTEREST", _("Interest")
    MARITAL_STATUS = "MARITAL_STATUS", _("Marital status")
    GENDER = "GENDER", _("Gender")
    RELATIONSHIP = "RELATIONSHIP", _("Relationship to head")
    HOUSEHOLD_TYPE = "HOUSEHOLD_TYPE", _("Household type")
    GROUP_TYPE = "GROUP_TYPE", _("Group type")
    ENROLLMENT_SOURCE = "ENROLLMENT_SOURCE", _("Enrollment source")
    ENROLLMENT_TYPE = "ENROLLMENT_TYPE", _("Enrollment type")
    EXIT_REASON = "EXIT_REASON", _("Exit reason")
    REFERRAL_TYPE = "REFERRAL_TYPE", _("Referral type")
    SERVICE_TYPE = "SERVICE_TYPE", _("Service type")
    CASE_NOTE_TYPE = "CASE_NOTE_TYPE", _("Case note type")
    FOLLOW_UP_PURPOSE = "FOLLOW_UP_PURPOSE", _("Follow-up purpose")
    SAFEGUARDING_CATEGORY = "SAFEGUARDING_CATEGORY", _("Safeguarding category")
    DOCUMENT_TYPE = "DOCUMENT_TYPE", _("Document type")
    NEED_TYPE = "NEED_TYPE", _("Need type")
    OUTCOME_INDICATOR = "OUTCOME_INDICATOR", _("Outcome indicator")
    ASSESSMENT_TYPE = "ASSESSMENT_TYPE", _("Assessment type")
    COMMUNICATION_TYPE = "COMMUNICATION_TYPE", _("Communication type")


class BeneficiaryStatus(models.TextChoices):
    IDENTIFIED = "IDENTIFIED", _("Identified")
    REGISTERED = "REGISTERED", _("Registered")
    VERIFIED = "VERIFIED", _("Verified")
    ELIGIBLE = "ELIGIBLE", _("Eligible")
    ENROLLED = "ENROLLED", _("Enrolled")
    ACTIVE = "ACTIVE", _("Active")
    SUSPENDED = "SUSPENDED", _("Suspended")
    GRADUATED = "GRADUATED", _("Graduated")
    EXITED = "EXITED", _("Exited")
    ARCHIVED = "ARCHIVED", _("Archived")


class ConfidentialityLevel(models.TextChoices):
    DIRECTORY = "DIRECTORY", _("Directory")
    INTERNAL = "INTERNAL", _("Internal")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    RESTRICTED = "RESTRICTED", _("Restricted")


class HouseholdStatus(models.TextChoices):
    PROSPECTIVE = "PROSPECTIVE", _("Prospective")
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    CLOSED = "CLOSED", _("Closed")


class GroupStatus(models.TextChoices):
    FORMING = "FORMING", _("Forming")
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    DISBANDED = "DISBANDED", _("Disbanded")


class EnrollmentStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    ACTIVE = "ACTIVE", _("Active")
    SUSPENDED = "SUSPENDED", _("Suspended")
    COMPLETED = "COMPLETED", _("Completed")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class ParticipationStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    CONFIRMED = "CONFIRMED", _("Confirmed")
    ATTENDED = "ATTENDED", _("Attended")
    ABSENT = "ABSENT", _("Absent")
    CANCELLED = "CANCELLED", _("Cancelled")


class AttendanceStatus(models.TextChoices):
    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    LATE = "LATE", _("Late")
    EXCUSED = "EXCUSED", _("Excused")


class ServiceDeliveryStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    DELIVERED = "DELIVERED", _("Delivered")
    PARTIAL = "PARTIAL", _("Partially delivered")
    CANCELLED = "CANCELLED", _("Cancelled")
    FAILED = "FAILED", _("Failed")


class ReferralStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    ACCEPTED = "ACCEPTED", _("Accepted")
    REJECTED = "REJECTED", _("Rejected")
    COMPLETED = "COMPLETED", _("Completed")
    CLOSED = "CLOSED", _("Closed")
    CANCELLED = "CANCELLED", _("Cancelled")


class CaseNoteStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    FINALIZED = "FINALIZED", _("Finalized")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")


class FollowUpStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    COMPLETED = "COMPLETED", _("Completed")
    OVERDUE = "OVERDUE", _("Overdue")
    CANCELLED = "CANCELLED", _("Cancelled")


class AssessmentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class PlanStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class ConsentStatus(models.TextChoices):
    GRANTED = "GRANTED", _("Granted")
    DENIED = "DENIED", _("Denied")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")
    EXPIRED = "EXPIRED", _("Expired")


class ConsentType(models.TextChoices):
    DATA_PROCESSING = "DATA_PROCESSING", _("Data processing")
    SERVICE_PROVISION = "SERVICE_PROVISION", _("Service provision")
    COMMUNICATION = "COMMUNICATION", _("Communication")
    PHOTOGRAPHIC = "PHOTOGRAPHIC", _("Photographic or media")
    DISCLOSURE = "DISCLOSURE", _("Information disclosure")
    OTHER = "OTHER", _("Other")


class GuardianRole(models.TextChoices):
    PARENT = "PARENT", _("Parent")
    GRANDPARENT = "GRANDPARENT", _("Grandparent")
    SIBLING = "SIBLING", _("Sibling")
    RELATIVE = "RELATIVE", _("Relative")
    LEGAL_GUARDIAN = "LEGAL_GUARDIAN", _("Legal guardian")
    FOSTER_CARER = "FOSTER_CARER", _("Foster carer")
    OTHER = "OTHER", _("Other")


class SafeguardingStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under review")
    INVESTIGATING = "INVESTIGATING", _("Investigating")
    REFERRED = "REFERRED", _("Referred externally")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")


class OutcomeStatus(models.TextChoices):
    NOT_MET = "NOT_MET", _("Not met")
    PARTIAL = "PARTIAL", _("Partially met")
    MET = "MET", _("Met")
    EXCEEDED = "EXCEEDED", _("Exceeded")


class ExitStatus(models.TextChoices):
    GRADUATED = "GRADUATED", _("Graduated")
    DROPPED = "DROPPED", _("Dropped out")
    TRANSFERRED = "TRANSFERRED", _("Transferred")
    DECEASED = "DECEASED", _("Deceased")
    RELOCATED = "RELOCATED", _("Relocated")
    INELIGIBLE = "INELIGIBLE", _("No longer eligible")
    OTHER = "OTHER", _("Other")


class TransferStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class DuplicateReviewStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE", _("Confirmed duplicate")
    NOT_DUPLICATE = "NOT_DUPLICATE", _("Not a duplicate")
    MERGED = "MERGED", _("Merged")


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    CURRENT = "CURRENT", _("Current")
    SUPERSEDED = "SUPERSEDED", _("Superseded")
    ARCHIVED = "ARCHIVED", _("Archived")


class CommunicationChannel(models.TextChoices):
    EMAIL = "EMAIL", _("Email")
    PHONE = "PHONE", _("Phone call")
    SMS = "SMS", _("SMS")
    WHATSAPP = "WHATSAPP", _("WhatsApp")
    HOME_VISIT = "HOME_VISIT", _("Home visit")
    CENTER = "CENTER", _("At center")
    COMMUNITY = "COMMUNITY", _("Community gathering")
    LETTER = "LETTER", _("Letter")
    OTHER = "OTHER", _("Other")


class CommunicationDirection(models.TextChoices):
    INBOUND = "INBOUND", _("Inbound")
    OUTBOUND = "OUTBOUND", _("Outbound")
    INTERNAL = "INTERNAL", _("Internal")


class FeedbackStatus(models.TextChoices):
    RECEIVED = "RECEIVED", _("Received")
    ACKNOWLEDGED = "ACKNOWLEDGED", _("Acknowledged")
    ACTIONED = "ACTIONED", _("Actioned")
    CLOSED = "CLOSED", _("Closed")


class RiskLevel(models.IntegerChoices):
    VERY_LOW = 1, _("Very low")
    LOW = 2, _("Low")
    MODERATE = 3, _("Moderate")
    HIGH = 4, _("High")
    CRITICAL = 5, _("Critical")


REFERENCE_SCHEME_CODES = {
    "beneficiary": "beneficiary",
    "household": "household",
    "group": "beneficiary_group",
    "enrollment": "beneficiary_enrollment",
    "participation": "beneficiary_participation",
    "assessment": "beneficiary_assessment",
    "referral": "beneficiary_referral",
    "service": "beneficiary_service",
    "case_note": "beneficiary_case_note",
    "support_plan": "beneficiary_support_plan",
    "exit": "beneficiary_exit",
    "transfer": "beneficiary_transfer",
    "document": "beneficiary_document",
    "consent": "beneficiary_consent",
    "safeguarding": "beneficiary_safeguarding",
    "outcome": "beneficiary_outcome",
    "feedback": "beneficiary_feedback",
}

# Every domain action stays in the existing beneficiaries permission namespace.
BENEFICIARY_ACTION_PERMISSIONS = {
    "view": "beneficiaries.view",
    "create": "beneficiaries.create",
    "update": "beneficiaries.update",
    "delete": "beneficiaries.delete",
    "archive": "beneficiaries.archive",
    "restore": "beneficiaries.restore",
    "export": "beneficiaries.export",
    "manage": "beneficiaries.manage",
    "view_confidential": "beneficiaries.view_confidential",
    "submit": "beneficiaries.submit",
    "approve": "beneficiaries.approve",
    "manage_households": "beneficiaries.manage_households",
    "manage_groups": "beneficiaries.manage_groups",
    "manage_enrollments": "beneficiaries.manage_enrollments",
    "manage_participation": "beneficiaries.manage_participation",
    "manage_attendance": "beneficiaries.manage_attendance",
    "manage_services": "beneficiaries.manage_services",
    "manage_referrals": "beneficiaries.manage_referrals",
    "manage_case_notes": "beneficiaries.manage_case_notes",
    "manage_follow_ups": "beneficiaries.manage_follow_ups",
    "manage_assessments": "beneficiaries.manage_assessments",
    "manage_support_plans": "beneficiaries.manage_support_plans",
    "manage_consent": "beneficiaries.manage_consent",
    "manage_guardians": "beneficiaries.manage_guardians",
    "manage_safeguarding": "beneficiaries.manage_safeguarding",
    "manage_outcomes": "beneficiaries.manage_outcomes",
    "manage_exits": "beneficiaries.manage_exits",
    "manage_documents": "beneficiaries.manage_documents",
    "manage_feedback": "beneficiaries.manage_feedback",
    "manage_transfers": "beneficiaries.manage_transfers",
    "manage_duplicates": "beneficiaries.manage_duplicates",
    "analytics": "beneficiaries.analytics",
}

MINOR_AGE = 18
SELF_CONSENT_AGE = 18
CONSENT_DEFAULT_VALID_DAYS = 365
FOLLOW_UP_DEFAULT_DAYS = 30
DEFAULT_CURRENCY = "ZMW"
