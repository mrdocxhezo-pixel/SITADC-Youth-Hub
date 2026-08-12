"""Constants for the Organizational Registers module.

The module provides a centralized, secure and configurable register management
system for every official organizational register.  Constants define the
register lifecycle, confidentiality framework, retention policy and the
permission codes that guard every action server side.
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _

# Module identifier used by the centralized reference numbering service.
REFERENCE_MODULE = "registers"

# Numbering pattern for register entries: SITADC/REG/MEM/2026/000001.
REGISTER_PATTERN = "{ORG}/REG/{PREFIX}/{YEAR}/{SEQUENCE}"
REGISTER_ORGANIZATION_CODE = "SITADC"
REGISTER_SEQUENCE_LENGTH = 6


class RegisterStatus(models.TextChoices):
    """Lifecycle status for an organizational register."""

    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    ARCHIVED = "ARCHIVED", _("Archived")


class RegisterApprovalStatus(models.TextChoices):
    """Approval state of an individual register entry."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS", _("Approved with Conditions")
    RETURNED = "RETURNED", _("Returned")
    REJECTED = "REJECTED", _("Rejected")


class RegisterEntryStatus(models.TextChoices):
    """Operational lifecycle of a register entry."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PENDING_REVIEW = "PENDING_REVIEW", _("Pending Review")
    UNDER_REVIEW = "UNDER_REVIEW", _("Under Review")
    APPROVED = "APPROVED", _("Approved")
    APPROVED_WITH_CONDITIONS = "APPROVED_WITH_CONDITIONS", _("Approved with Conditions")
    RETURNED = "RETURNED", _("Returned")
    REJECTED = "REJECTED", _("Rejected")
    ACTIVE = "ACTIVE", _("Active")
    ARCHIVED = "ARCHIVED", _("Archived")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality classification applied to registers and entries."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")


class RetentionPolicy(models.TextChoices):
    """Retention policy applied to a register category or register."""

    PERMANENT = "PERMANENT", _("Permanent")
    FIXED_TERM = "FIXED_TERM", _("Fixed Term")
    ARCHIVE_AFTER_INACTIVITY = "ARCHIVE_AFTER_INACTIVITY", _("Archive after Inactivity")
    LEGAL_HOLD = "LEGAL_HOLD", _("Legal Hold")
    SCHEDULED_DISPOSAL = "SCHEDULED_DISPOSAL", _("Scheduled Disposal")


class RelationshipType(models.TextChoices):
    """Types of related records linkable to a register entry."""

    DOCUMENT = "DOCUMENT", _("Document")
    REPORT = "REPORT", _("Report")
    PROGRAM = "PROGRAM", _("Program")
    PROJECT = "PROJECT", _("Project")
    VOLUNTEER = "VOLUNTEER", _("Volunteer")
    MEMBER = "MEMBER", _("Member")
    BENEFICIARY = "BENEFICIARY", _("Beneficiary")
    STAKEHOLDER = "STAKEHOLDER", _("Stakeholder")
    EVENT = "EVENT", _("Event")
    RISK = "RISK", _("Risk")
    ASSET = "ASSET", _("Asset")
    DECISION = "DECISION", _("Decision")
    ENTRY = "ENTRY", _("Register Entry")
    OTHER = "OTHER", _("Other")


class RegisterActivityAction(models.TextChoices):
    """Actions recorded on the activity timeline of a register or entry."""

    CREATED = "CREATED", _("Created")
    UPDATED = "UPDATED", _("Updated")
    VALIDATED = "VALIDATED", _("Validated")
    SUBMITTED = "SUBMITTED", _("Submitted")
    REVIEWED = "REVIEWED", _("Reviewed")
    APPROVED = "APPROVED", _("Approved")
    RETURNED = "RETURNED", _("Returned")
    REJECTED = "REJECTED", _("Rejected")
    ARCHIVED = "ARCHIVED", _("Archived")
    RESTORED = "RESTORED", _("Restored")
    EXPORTED = "EXPORTED", _("Exported")
    RELATIONSHIP_ADDED = "RELATIONSHIP_ADDED", _("Relationship added")
    RELATIONSHIP_REMOVED = "RELATIONSHIP_REMOVED", _("Relationship removed")
    ATTACHMENT_ADDED = "ATTACHMENT_ADDED", _("Attachment added")
    ATTACHMENT_REMOVED = "ATTACHMENT_REMOVED", _("Attachment removed")
    CONFIDENTIALITY_CHANGED = "CONFIDENTIALITY_CHANGED", _("Confidentiality changed")


class TemplateFieldType(models.TextChoices):
    """Supported field types for a configurable register template."""

    TEXT = "TEXT", _("Text")
    TEXTAREA = "TEXTAREA", _("Text Area")
    NUMBER = "NUMBER", _("Number")
    DATE = "DATE", _("Date")
    DATETIME = "DATETIME", _("Date & Time")
    SELECT = "SELECT", _("Select")
    MULTISELECT = "MULTISELECT", _("Multi Select")
    BOOLEAN = "BOOLEAN", _("Boolean")
    EMAIL = "EMAIL", _("Email")
    URL = "URL", _("URL")


# Permission codes (module.action) resolved through the RBAC engine.
REGISTER_ACTION_PERMISSIONS: dict[str, str] = {
    "view": "registers.view",
    "create": "registers.create",
    "update": "registers.update",
    "delete": "registers.delete",
    "export": "registers.export",
    "submit": "registers.submit",
    "review": "registers.review",
    "approve": "registers.approve",
    "archive": "registers.archive",
    "restore": "registers.restore",
    "view_confidential": "registers.view_confidential",
    "manage": "registers.manage",
}
