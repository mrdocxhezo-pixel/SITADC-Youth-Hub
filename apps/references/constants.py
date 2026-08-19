"""Constants for the reference numbering module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class SequenceResetPeriod(models.TextChoices):
    """How often a sequence restarts at its configured start value."""

    NEVER = "NEVER", _("Never")
    ANNUALLY = "ANNUALLY", _("Annually")
    MONTHLY = "MONTHLY", _("Monthly")
    DAILY = "DAILY", _("Daily")
    FISCAL = "FISCAL", _("Fiscal Year")
    CUSTOM = "CUSTOM", _("Custom")


class SchemeStatus(models.TextChoices):
    """Lifecycle status for a reference number scheme."""

    ACTIVE = "ACTIVE", _("Active")
    INACTIVE = "INACTIVE", _("Inactive")
    ARCHIVED = "ARCHIVED", _("Archived")


class ReferenceNumberStatus(models.TextChoices):
    """Lifecycle status of an issued reference number.

    Every issued number follows the reservation lifecycle:
    ``AVAILABLE`` -> ``RESERVED`` -> ``ASSIGNED``, with ``CANCELLED`` and
    ``VOIDED`` used to retire a number without ever reusing it.
    """

    AVAILABLE = "AVAILABLE", _("Available")
    RESERVED = "RESERVED", _("Reserved")
    ASSIGNED = "ASSIGNED", _("Assigned")
    CANCELLED = "CANCELLED", _("Cancelled")
    VOIDED = "VOIDED", _("Voided")


class ReferenceModules(models.TextChoices):
    """Business modules supported by the centralized numbering service."""

    USERS = "users", _("Users")
    MEMBERSHIPS = "memberships", _("Memberships")
    VOLUNTEERS = "volunteers", _("Volunteers")
    LEADERS = "leaders", _("Leaders")
    REPORTS = "reports", _("Reports")
    DOCUMENTS = "documents", _("Documents")
    PROGRAMS = "programs", _("Programs")
    PROJECTS = "projects", _("Projects")
    EVENTS = "events", _("Events")
    ASSETS = "assets", _("Assets")
    FINANCE = "finance", _("Finance")
    MEETINGS = "meetings", _("Meetings")
    GRANTS = "grants", _("Grants")
    PARTNERS = "partners", _("Partners")
    DONORS = "donors", _("Donors")
    BENEFICIARIES = "beneficiaries", _("Beneficiaries")
    MEAL = "meal", _("MEAL")
    REGISTERS = "registers", _("Registers")
    CALENDARS = "calendars", _("Calendars")
    NOTIFICATIONS = "notifications", _("Notifications")
    ANNOUNCEMENTS = "announcements", _("Announcements")
    EXPORTS = "exports", _("Exports")
    GOVERNANCE = "governance", _("Governance")


class ReferenceAuditAction(models.TextChoices):
    """Audited events recorded by the numbering service."""

    CREATED = "CREATED", _("Scheme created")
    UPDATED = "UPDATED", _("Scheme updated")
    ACTIVATED = "ACTIVATED", _("Scheme activated")
    DEACTIVATED = "DEACTIVATED", _("Scheme deactivated")
    ARCHIVED = "ARCHIVED", _("Scheme archived")
    RESTORED = "RESTORED", _("Scheme restored")
    GENERATED = "GENERATED", _("Reference generated")
    RESERVED = "RESERVED", _("Sequence reserved")
    CONFIRMED = "CONFIRMED", _("Reservation confirmed")
    ASSIGNED = "ASSIGNED", _("Reference assigned")
    CANCELLED = "CANCELLED", _("Reservation cancelled")
    VOIDED = "VOIDED", _("Reference voided")
    RESET = "RESET", _("Sequence reset")
    VALIDATION_FAILED = "VALIDATION_FAILED", _("Validation failed")
    DUPLICATE_PREVENTED = "DUPLICATE_PREVENTED", _("Duplicate prevented")
    CORRECTED = "CORRECTED", _("Manual correction")


DEFAULT_ORGANIZATION_CODE = "SITADC"
DEFAULT_SEPARATOR = "-"
DEFAULT_PATTERN = "{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}"
