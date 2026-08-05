"""Domain constants for stakeholder and partnership management."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReferenceDataKind(models.TextChoices):
    CATEGORY = "CATEGORY", _("Category")
    TYPE = "TYPE", _("Relationship type")
    CLASSIFICATION = "CLASSIFICATION", _("Classification")
    SECTOR = "SECTOR", _("Sector")
    FOCUS_AREA = "FOCUS_AREA", _("Focus area")
    SDG = "SDG", _("Sustainable Development Goal")
    ENGAGEMENT_LEVEL = "ENGAGEMENT_LEVEL", _("Engagement level")
    CONTRIBUTION_TYPE = "CONTRIBUTION_TYPE", _("Contribution type")
    AGREEMENT_TYPE = "AGREEMENT_TYPE", _("Agreement type")
    RISK_CATEGORY = "RISK_CATEGORY", _("Risk category")
    DUE_DILIGENCE_CHECK = "DUE_DILIGENCE_CHECK", _("Due diligence check")
    STATUS = "STATUS", _("Stakeholder status")
    PRIORITY = "PRIORITY", _("Priority")
    RELATIONSHIP_LEVEL = "RELATIONSHIP_LEVEL", _("Relationship level")
    CONFIDENTIALITY_LEVEL = "CONFIDENTIALITY_LEVEL", _("Confidentiality level")
    OWNERSHIP_TYPE = "OWNERSHIP_TYPE", _("Ownership type")
    ENGAGEMENT_TYPE = "ENGAGEMENT_TYPE", _("Engagement type")
    COMMUNICATION_TYPE = "COMMUNICATION_TYPE", _("Communication type")
    CONTACT_ROLE = "CONTACT_ROLE", _("Contact role")
    COMMITMENT_STATUS = "COMMITMENT_STATUS", _("Commitment status")
    AGREEMENT_STATUS = "AGREEMENT_STATUS", _("Agreement status")
    RISK_LEVEL = "RISK_LEVEL", _("Risk level")
    ASSESSMENT_SCALE = "ASSESSMENT_SCALE", _("Assessment rating scale")
    PERFORMANCE_SCALE = "PERFORMANCE_SCALE", _("Performance rating scale")


class StakeholderEntityType(models.TextChoices):
    ORGANIZATION = "ORGANIZATION", _("Organization")
    INDIVIDUAL = "INDIVIDUAL", _("Individual")
    NETWORK = "NETWORK", _("Network or coalition")


class StakeholderStatus(models.TextChoices):
    PROSPECT = "PROSPECT", _("Prospect")
    IDENTIFIED = "IDENTIFIED", _("Identified")
    UNDER_ASSESSMENT = "UNDER_ASSESSMENT", _("Under assessment")
    CONTACTED = "CONTACTED", _("Contacted")
    ENGAGED = "ENGAGED", _("Engaged")
    NEGOTIATING = "NEGOTIATING", _("Negotiating")
    PENDING_AGREEMENT = "PENDING_AGREEMENT", _("Pending agreement")
    ACTIVE = "ACTIVE", _("Active")
    DORMANT = "DORMANT", _("Dormant")
    INACTIVE = "INACTIVE", _("Inactive")
    SUSPENDED = "SUSPENDED", _("Suspended")
    COMPLETED = "COMPLETED", _("Completed")
    CLOSED = "CLOSED", _("Closed")
    BLACKLISTED = "BLACKLISTED", _("Blacklisted")
    ARCHIVED = "ARCHIVED", _("Archived")


class ConfidentialityLevel(models.TextChoices):
    DIRECTORY = "DIRECTORY", _("Directory")
    INTERNAL = "INTERNAL", _("Internal")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    RESTRICTED = "RESTRICTED", _("Restricted")


class AssessmentClassification(models.TextChoices):
    MANAGE_CLOSELY = "MANAGE_CLOSELY", _("Manage closely")
    KEEP_SATISFIED = "KEEP_SATISFIED", _("Keep satisfied")
    KEEP_INFORMED = "KEEP_INFORMED", _("Keep informed")
    MONITOR = "MONITOR", _("Monitor")
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA", _("Insufficient data")


class PlanStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    ARCHIVED = "ARCHIVED", _("Archived")


class EngagementType(models.TextChoices):
    MEETING = "MEETING", _("Meeting")
    CONSULTATION = "CONSULTATION", _("Consultation")
    WORKSHOP = "WORKSHOP", _("Workshop")
    EVENT = "EVENT", _("Event")
    SITE_VISIT = "SITE_VISIT", _("Site visit")
    TRAINING = "TRAINING", _("Training")
    OTHER = "OTHER", _("Other")


class EngagementStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    POSTPONED = "POSTPONED", _("Postponed")


class CommunicationChannel(models.TextChoices):
    EMAIL = "EMAIL", _("Email")
    LETTER = "LETTER", _("Letter")
    PHONE = "PHONE", _("Phone call")
    SMS = "SMS", _("SMS")
    MEETING = "MEETING", _("Meeting")
    VIRTUAL = "VIRTUAL", _("Virtual meeting")
    NEWSLETTER = "NEWSLETTER", _("Newsletter")
    IN_APP = "IN_APP", _("In-app")
    OTHER = "OTHER", _("Other")


class CommunicationDirection(models.TextChoices):
    INBOUND = "INBOUND", _("Inbound")
    OUTBOUND = "OUTBOUND", _("Outbound")
    INTERNAL = "INTERNAL", _("Internal")


class CommitmentStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    OVERDUE = "OVERDUE", _("Overdue")
    CANCELLED = "CANCELLED", _("Cancelled")


class ContributionStatus(models.TextChoices):
    PLEDGED = "PLEDGED", _("Pledged")
    RECEIVED = "RECEIVED", _("Received")
    VERIFIED = "VERIFIED", _("Verified")
    RETURNED = "RETURNED", _("Returned")
    CANCELLED = "CANCELLED", _("Cancelled")


class AgreementStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under review")
    RETURNED = "RETURNED", _("Returned for correction")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    PENDING_SIGNATURE = "PENDING_SIGNATURE", _("Pending signature")
    ACTIVE = "ACTIVE", _("Active")
    EXPIRING = "EXPIRING", _("Expiring")
    EXPIRED = "EXPIRED", _("Expired")
    COMPLETED = "COMPLETED", _("Completed")
    TERMINATED = "TERMINATED", _("Terminated")
    RENEWED = "RENEWED", _("Renewed or extended")
    ARCHIVED = "ARCHIVED", _("Archived")


class RenewalStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")


class DueDiligenceStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    PASSED = "PASSED", _("Passed")
    CONDITIONAL = "CONDITIONAL", _("Conditional")
    FAILED = "FAILED", _("Failed")
    EXPIRED = "EXPIRED", _("Expired")


class ConflictStatus(models.TextChoices):
    DECLARED = "DECLARED", _("Declared")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under review")
    MITIGATED = "MITIGATED", _("Mitigated")
    ACCEPTED = "ACCEPTED", _("Accepted")
    CLOSED = "CLOSED", _("Closed")


class RiskLevel(models.IntegerChoices):
    VERY_LOW = 1, _("Very low")
    LOW = 2, _("Low")
    MODERATE = 3, _("Moderate")
    HIGH = 4, _("High")
    CRITICAL = 5, _("Critical")


class RiskStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    MONITORING = "MONITORING", _("Monitoring")
    MITIGATED = "MITIGATED", _("Mitigated")
    ACCEPTED = "ACCEPTED", _("Accepted")
    CLOSED = "CLOSED", _("Closed")


class ReviewStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    FINALIZED = "FINALIZED", _("Finalized")
    ACKNOWLEDGED = "ACKNOWLEDGED", _("Acknowledged")


class ActionStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    BLOCKED = "BLOCKED", _("Blocked")
    COMPLETED = "COMPLETED", _("Completed")
    OVERDUE = "OVERDUE", _("Overdue")
    CANCELLED = "CANCELLED", _("Cancelled")


class ActionPriority(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    URGENT = "URGENT", _("Urgent")


class NoteStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    FINALIZED = "FINALIZED", _("Finalized")
    ARCHIVED = "ARCHIVED", _("Archived")


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    CURRENT = "CURRENT", _("Current")
    SUPERSEDED = "SUPERSEDED", _("Superseded")
    EXPIRED = "EXPIRED", _("Expired")
    ARCHIVED = "ARCHIVED", _("Archived")


class DuplicateReviewStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    CONFIRMED_DUPLICATE = "CONFIRMED_DUPLICATE", _("Confirmed duplicate")
    NOT_DUPLICATE = "NOT_DUPLICATE", _("Not a duplicate")
    MERGED = "MERGED", _("Merged")


class AccessLevel(models.TextChoices):
    VIEW = "VIEW", _("View")
    CONTRIBUTE = "CONTRIBUTE", _("Contribute")
    MANAGE = "MANAGE", _("Manage")


REFERENCE_SCHEME_CODES = {
    "stakeholder": "stakeholder",
    "engagement": "stakeholder_engagement",
    "agreement": "stakeholder_agreement",
    "commitment": "stakeholder_commitment",
    "contribution": "stakeholder_contribution",
    "assessment": "stakeholder_assessment",
    "performance": "stakeholder_performance",
    "due_diligence": "stakeholder_due_diligence",
}

# Every domain action stays in the existing partners permission namespace.
STAKEHOLDER_ACTION_PERMISSIONS = {
    "view": "partners.view",
    "view_directory": "partners.view_directory",
    "view_profile": "partners.view_profile",
    "view_private_contacts": "partners.view_private_contacts",
    "view_due_diligence": "partners.view_due_diligence",
    "view_financial": "partners.view_financial",
    "view_confidential": "partners.view_confidential",
    "create": "partners.create",
    "update": "partners.update",
    "archive": "partners.archive",
    "restore": "partners.restore",
    "assign": "partners.assign",
    "manage_categories": "partners.manage_categories",
    "manage_contacts": "partners.manage_contacts",
    "assess": "partners.assess",
    "manage_engagements": "partners.manage_engagements",
    "manage_communications": "partners.manage_communications",
    "manage_commitments": "partners.manage_commitments",
    "manage_contributions": "partners.manage_contributions",
    "manage_agreements": "partners.manage_agreements",
    "review_agreements": "partners.review_agreements",
    "approve_agreements": "partners.approve_agreements",
    "manage_due_diligence": "partners.manage_due_diligence",
    "manage_risk": "partners.manage_risk",
    "manage_performance": "partners.manage_performance",
    "review_performance": "partners.review_performance",
    "manage_actions": "partners.manage_actions",
    "manage_notes": "partners.manage_notes",
    "manage_documents": "partners.manage_documents",
    "manage_access": "partners.manage_access",
    "analytics": "partners.analytics",
    "export": "partners.export",
    "manage": "partners.manage",
}

ASSESSMENT_HIGH_THRESHOLD = 3
ASSESSMENT_FORMULA_VERSION = "power-interest-v1"
DEFAULT_CURRENCY = "ZMW"
