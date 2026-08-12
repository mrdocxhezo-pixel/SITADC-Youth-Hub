"""Domain constants for the Program & Project Management module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReferenceDataKind(models.TextChoices):
    CATEGORY = "CATEGORY", _("Program category")
    PROJECT_CATEGORY = "PROJECT_CATEGORY", _("Project category")
    PILLAR = "PILLAR", _("Organizational pillar")
    SDG = "SDG", _("Sustainable Development Goal")
    FUNDING_SOURCE = "FUNDING_SOURCE", _("Funding source")
    BENEFICIARY_CATEGORY = "BENEFICIARY_CATEGORY", _("Beneficiary category")
    RISK_CATEGORY = "RISK_CATEGORY", _("Risk category")
    INDICATOR_TYPE = "INDICATOR_TYPE", _("Indicator type")
    RESOURCE_TYPE = "RESOURCE_TYPE", _("Resource type")
    DOCUMENT_TYPE = "DOCUMENT_TYPE", _("Document type")
    LESSON_CATEGORY = "LESSON_CATEGORY", _("Lessons learned category")
    EVIDENCE_TYPE = "EVIDENCE_TYPE", _("Evidence type")
    BUDGET_CATEGORY = "BUDGET_CATEGORY", _("Budget category")
    PROJECT_CLASSIFICATION = "PROJECT_CLASSIFICATION", _("Project classification")


class ProgramStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PROPOSED = "PROPOSED", _("Proposed")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    ACTIVE = "ACTIVE", _("Active")
    ON_HOLD = "ON_HOLD", _("On hold")
    DELAYED = "DELAYED", _("Delayed")
    SUSPENDED = "SUSPENDED", _("Suspended")
    COMPLETED = "COMPLETED", _("Completed")
    CLOSED = "CLOSED", _("Closed")
    ARCHIVED = "ARCHIVED", _("Archived")
    CANCELLED = "CANCELLED", _("Cancelled")


class ProjectStatus(models.TextChoices):
    CONCEPT = "CONCEPT", _("Concept")
    PROPOSAL = "PROPOSAL", _("Proposal")
    PLANNING = "PLANNING", _("Planning")
    APPROVAL = "APPROVAL", _("Approval")
    INITIATION = "INITIATION", _("Initiation")
    EXECUTION = "EXECUTION", _("Execution")
    MONITORING = "MONITORING", _("Monitoring")
    COMPLETION = "COMPLETION", _("Completion")
    CLOSURE = "CLOSURE", _("Closure")
    ARCHIVED = "ARCHIVED", _("Archived")


class PortfolioStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    ARCHIVED = "ARCHIVED", _("Archived")


class Priority(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


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


class IssueStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")
    ARCHIVED = "ARCHIVED", _("Archived")


class ChangeStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    IMPLEMENTED = "IMPLEMENTED", _("Implemented")


class WorkPlanStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    ARCHIVED = "ARCHIVED", _("Archived")


class ActivityStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    DELAYED = "DELAYED", _("Delayed")
    CANCELLED = "CANCELLED", _("Cancelled")


class TaskStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    BLOCKED = "BLOCKED", _("Blocked")
    CANCELLED = "CANCELLED", _("Cancelled")


class MilestoneStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    ACHIEVED = "ACHIEVED", _("Achieved")
    DELAYED = "DELAYED", _("Delayed")
    CANCELLED = "CANCELLED", _("Cancelled")


class DeliverableStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class EvaluationType(models.TextChoices):
    BASELINE = "BASELINE", _("Baseline")
    MIDLINE = "MIDLINE", _("Midline")
    ENDLINE = "ENDLINE", _("Endline")
    OUTCOME = "OUTCOME", _("Outcome evaluation")
    IMPACT = "IMPACT", _("Impact assessment")


class DocumentStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    CURRENT = "CURRENT", _("Current")
    SUPERSEDED = "SUPERSEDED", _("Superseded")
    ARCHIVED = "ARCHIVED", _("Archived")


class BeneficiaryStatus(models.TextChoices):
    ENROLLED = "ENROLLED", _("Enrolled")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    DROPPED = "DROPPED", _("Dropped")
    INACTIVE = "INACTIVE", _("Inactive")


class ProgressStatus(models.TextChoices):
    ON_TRACK = "ON_TRACK", _("On track")
    AT_RISK = "AT_RISK", _("At risk")
    OFF_TRACK = "OFF_TRACK", _("Off track")
    COMPLETED = "COMPLETED", _("Completed")


class ResourceType(models.TextChoices):
    HUMAN = "HUMAN", _("Human resource")
    FINANCIAL = "FINANCIAL", _("Financial resource")
    EQUIPMENT = "EQUIPMENT", _("Equipment")
    VEHICLE = "VEHICLE", _("Vehicle")
    FACILITY = "FACILITY", _("Facility")
    ICT = "ICT", _("ICT resource")
    LEARNING_MATERIAL = "LEARNING_MATERIAL", _("Learning material")
    VOLUNTEER = "VOLUNTEER", _("Volunteer")
    CONSULTANT = "CONSULTANT", _("Consultant")
    PARTNER_CONTRIBUTION = "PARTNER_CONTRIBUTION", _("Partner contribution")
    OTHER = "OTHER", _("Other")


class ProcurementStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ORDERED = "ORDERED", _("Ordered")
    DELIVERED = "DELIVERED", _("Delivered")
    CANCELLED = "CANCELLED", _("Cancelled")


class LessonCategory(models.TextChoices):
    SUCCESS = "SUCCESS", _("Success story")
    BEST_PRACTICE = "BEST_PRACTICE", _("Best practice")
    CHALLENGE = "CHALLENGE", _("Challenge")
    RECOMMENDATION = "RECOMMENDATION", _("Recommendation")
    INNOVATION = "INNOVATION", _("Innovation")
    OTHER = "OTHER", _("Other")


class WBSNodeType(models.TextChoices):
    PHASE = "PHASE", _("Phase")
    WORK_PACKAGE = "WORK_PACKAGE", _("Work package")
    ACTIVITY = "ACTIVITY", _("Activity")
    TASK = "TASK", _("Task")
    SUB_TASK = "SUB_TASK", _("Sub-task")


class WBSNodeStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    DELAYED = "DELAYED", _("Delayed")
    CANCELLED = "CANCELLED", _("Cancelled")


class MilestoneApprovalStatus(models.TextChoices):
    PENDING = "PENDING", _("Pending")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class ResultType(models.TextChoices):
    OUTPUT = "OUTPUT", _("Output")
    OUTCOME = "OUTCOME", _("Outcome")
    IMPACT = "IMPACT", _("Impact")


class ResultStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", _("Not started")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    PARTIAL = "PARTIAL", _("Partially achieved")
    ACHIEVED = "ACHIEVED", _("Achieved")


class TimelineEntryStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    DELAYED = "DELAYED", _("Delayed")


class ProjectClosureStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    VERIFIED = "VERIFIED", _("Verified")
    APPROVED = "APPROVED", _("Approved")
    COMPLETE = "COMPLETE", _("Complete")


class ProjectReportType(models.TextChoices):
    PROGRESS = "PROGRESS", _("Progress report")
    WORK_PLAN = "WORK_PLAN", _("Work plan report")
    ACTIVITY = "ACTIVITY", _("Activity report")
    TASK = "TASK", _("Task report")
    MILESTONE = "MILESTONE", _("Milestone report")
    BUDGET = "BUDGET", _("Budget utilization report")
    RESOURCE = "RESOURCE", _("Resource utilization report")
    BENEFICIARY = "BENEFICIARY", _("Beneficiary report")
    RISK = "RISK", _("Risk register")
    ISSUE = "ISSUE", _("Issue register")
    DELIVERABLE = "DELIVERABLE", _("Deliverables report")
    PROCUREMENT = "PROCUREMENT", _("Procurement report")
    CLOSURE = "CLOSURE", _("Project closure report")
    LESSONS = "LESSONS", _("Lessons learned report")


class ProjectReportStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    ARCHIVED = "ARCHIVED", _("Archived")


REFERENCE_SCHEME_CODES = {
    "program": "program",
    "project": "project",
    "work_plan": "work_plan",
    "activity": "activity",
    "task": "task",
    "milestone": "milestone",
    "deliverable": "deliverable",
    "risk": "risk",
    "issue": "issue",
    "change": "change",
    "evidence": "evidence",
    "beneficiary": "program_beneficiary",
    "procurement": "procurement",
    "resource": "resource_allocation",
    "lesson": "lesson",
    "wbs": "wbs",
}

PROGRAM_ACTION_PERMISSIONS = {
    "view": "programmes.view",
    "create": "programmes.create",
    "update": "programmes.update",
    "delete": "programmes.delete",
    "submit": "programmes.submit",
    "archive": "programmes.archive",
    "restore": "programmes.restore",
    "export": "programmes.export",
    "assign": "programmes.assign",
    "manage": "programmes.manage",
}

PROJECT_ACTION_PERMISSIONS = {
    "view": "projects.view",
    "create": "projects.create",
    "update": "projects.update",
    "delete": "projects.delete",
    "submit": "projects.submit",
    "archive": "projects.archive",
    "restore": "projects.restore",
    "export": "projects.export",
    "assign": "projects.assign",
    "manage": "projects.manage",
}

PROGRAM_ACTIVE_STATUSES = (
    ProgramStatus.ACTIVE,
    ProgramStatus.ON_HOLD,
    ProgramStatus.DELAYED,
    ProgramStatus.SUSPENDED,
)

PROJECT_ACTIVE_STATUSES = (
    ProjectStatus.INITIATION,
    ProjectStatus.EXECUTION,
    ProjectStatus.MONITORING,
)

DEFAULT_CURRENCY = "ZMW"
