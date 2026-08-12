"""Domain constants for the Monitoring, Evaluation, Accountability & Learning module."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReferenceDataKind(models.TextChoices):
    """Configurable taxonomies administered through the MEAL reference data registry."""

    INDICATOR_CATEGORY = "INDICATOR_CATEGORY", _("Indicator category")
    REPORTING_FREQUENCY = "REPORTING_FREQUENCY", _("Reporting frequency")
    EVALUATION_TYPE = "EVALUATION_TYPE", _("Evaluation type")
    DATA_SOURCE_TYPE = "DATA_SOURCE_TYPE", _("Data source type")
    COLLECTION_TOOL_TYPE = "COLLECTION_TOOL_TYPE", _("Collection tool type")
    COLLECTION_METHOD = "COLLECTION_METHOD", _("Collection method")
    DISAGGREGATION_DIMENSION = "DISAGGREGATION_DIMENSION", _("Disaggregation dimension")
    DATA_QUALITY_DIMENSION = "DATA_QUALITY_DIMENSION", _("Data quality dimension")
    COMPLAINT_CATEGORY = "COMPLAINT_CATEGORY", _("Complaint category")
    FEEDBACK_CATEGORY = "FEEDBACK_CATEGORY", _("Feedback category")
    SUGGESTION_CHANNEL = "SUGGESTION_CHANNEL", _("Suggestion channel")
    LEARNING_CATEGORY = "LEARNING_CATEGORY", _("Learning category")
    LESSON_CATEGORY = "LESSON_CATEGORY", _("Lesson category")
    SCORECARD_PERIOD = "SCORECARD_PERIOD", _("Scorecard period")
    INDICATOR_UNIT = "INDICATOR_UNIT", _("Indicator unit")
    VERIFICATION_METHOD = "VERIFICATION_METHOD", _("Verification method")
    OUTCOME_CATEGORY = "OUTCOME_CATEGORY", _("Outcome category")
    GEOGRAPHIC_AREA = "GEOGRAPHIC_AREA", _("Geographic area")


class WorkflowStatus(models.TextChoices):
    """Shared approval lifecycle for strategic MEAL documents."""

    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    ARCHIVED = "ARCHIVED", _("Archived")


class IndicatorStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    ARCHIVED = "ARCHIVED", _("Archived")


class IndicatorType(models.TextChoices):
    INPUT = "INPUT", _("Input indicator")
    PROCESS = "PROCESS", _("Process indicator")
    OUTPUT = "OUTPUT", _("Output indicator")
    OUTCOME = "OUTCOME", _("Outcome indicator")
    IMPACT = "IMPACT", _("Impact indicator")
    EFFICIENCY = "EFFICIENCY", _("Efficiency indicator")
    EFFECTIVENESS = "EFFECTIVENESS", _("Effectiveness indicator")
    QUALITY = "QUALITY", _("Quality indicator")
    SUSTAINABILITY = "SUSTAINABILITY", _("Sustainability indicator")
    GOVERNANCE = "GOVERNANCE", _("Governance indicator")
    FINANCIAL = "FINANCIAL", _("Financial indicator")
    INCLUSION = "INCLUSION", _("Inclusion indicator")


class ReportFrequency(models.TextChoices):
    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    SEMI_ANNUAL = "SEMI_ANNUAL", _("Semi-annual")
    ANNUAL = "ANNUAL", _("Annual")
    CONTINUOUS = "CONTINUOUS", _("Continuous")
    EVENT_BASED = "EVENT_BASED", _("Event-based")


class BaselineStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    REVISED = "REVISED", _("Revised")
    ARCHIVED = "ARCHIVED", _("Archived")


class TargetStatus(models.TextChoices):
    PENDING_APPROVAL = "PENDING_APPROVAL", _("Pending approval")
    APPROVED = "APPROVED", _("Approved")
    REVISED = "REVISED", _("Revised")
    CANCELLED = "CANCELLED", _("Cancelled")


class ResultStatus(models.TextChoices):
    NOT_STARTED = "NOT_STARTED", _("Not started")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    PARTIAL = "PARTIAL", _("Partially achieved")
    ACHIEVED = "ACHIEVED", _("Achieved")


class DataCollectionPlanStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    ACTIVE = "ACTIVE", _("Active")
    COMPLETED = "COMPLETED", _("Completed")
    CANCELLED = "CANCELLED", _("Cancelled")
    ARCHIVED = "ARCHIVED", _("Archived")


class DataSubmissionStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    VALIDATED = "VALIDATED", _("Validated")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")


class MonitoringPlanStatus(models.TextChoices):
    ACTIVE = "ACTIVE", _("Active")
    PAUSED = "PAUSED", _("Paused")
    COMPLETED = "COMPLETED", _("Completed")
    ARCHIVED = "ARCHIVED", _("Archived")


class MonitoringVisitStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    FOLLOW_UP_REQUIRED = "FOLLOW_UP_REQUIRED", _("Follow-up required")
    CANCELLED = "CANCELLED", _("Cancelled")


class FindingCategory(models.TextChoices):
    OBSERVATION = "OBSERVATION", _("Observation")
    COMPLIANCE = "COMPLIANCE", _("Compliance")
    RISK = "RISK", _("Risk")
    ISSUE = "ISSUE", _("Issue")
    GOOD_PRACTICE = "GOOD_PRACTICE", _("Good practice")


class EvaluationStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    REPORT_DRAFT = "REPORT_DRAFT", _("Report draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class DQAStatus(models.TextChoices):
    PLANNED = "PLANNED", _("Planned")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    ARCHIVED = "ARCHIVED", _("Archived")


class ComplaintStatus(models.TextChoices):
    RECEIVED = "RECEIVED", _("Received")
    ASSIGNED = "ASSIGNED", _("Assigned")
    UNDER_INVESTIGATION = "UNDER_INVESTIGATION", _("Under investigation")
    RESOLVED = "RESOLVED", _("Resolved")
    CLOSED = "CLOSED", _("Closed")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class FeedbackStatus(models.TextChoices):
    RECEIVED = "RECEIVED", _("Received")
    REVIEWED = "REVIEWED", _("Reviewed")
    RESPONDED = "RESPONDED", _("Responded")
    CLOSED = "CLOSED", _("Closed")


class CorrectiveActionStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    COMPLETED = "COMPLETED", _("Completed")
    VERIFIED = "VERIFIED", _("Verified")
    CLOSED = "CLOSED", _("Closed")
    CANCELLED = "CANCELLED", _("Cancelled")


class OutcomeHarvestStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    VALIDATED = "VALIDATED", _("Validated")
    APPROVED = "APPROVED", _("Approved")
    ARCHIVED = "ARCHIVED", _("Archived")


class LearningLogStatus(models.TextChoices):
    OPEN = "OPEN", _("Open")
    IN_PROGRESS = "IN_PROGRESS", _("In progress")
    IMPLEMENTED = "IMPLEMENTED", _("Implemented")
    CLOSED = "CLOSED", _("Closed")


class BestPracticeStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class LessonStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    REVIEWED = "REVIEWED", _("Reviewed")
    APPROVED = "APPROVED", _("Approved")
    SHARED = "SHARED", _("Shared")
    ARCHIVED = "ARCHIVED", _("Archived")


class ScorecardStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    PUBLISHED = "PUBLISHED", _("Published")
    ARCHIVED = "ARCHIVED", _("Archived")


class ReportStatus(models.TextChoices):
    DRAFT = "DRAFT", _("Draft")
    SUBMITTED = "SUBMITTED", _("Submitted")
    RETURNED = "RETURNED", _("Returned")
    APPROVED = "APPROVED", _("Approved")
    ARCHIVED = "ARCHIVED", _("Archived")


class Priority(models.TextChoices):
    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class ResultLevel(models.TextChoices):
    GOAL = "GOAL", _("Goal")
    INTERMEDIATE_RESULT = "INTERMEDIATE_RESULT", _("Intermediate result")
    OUTPUT = "OUTPUT", _("Output")
    OUTCOME = "OUTCOME", _("Outcome")
    IMPACT = "IMPACT", _("Impact")


class LogframeLevel(models.TextChoices):
    GOAL = "GOAL", _("Goal")
    PURPOSE = "PURPOSE", _("Purpose")
    OUTPUT = "OUTPUT", _("Output")
    ACTIVITY = "ACTIVITY", _("Activity")


class DQADimension(models.TextChoices):
    ACCURACY = "ACCURACY", _("Accuracy")
    COMPLETENESS = "COMPLETENESS", _("Completeness")
    CONSISTENCY = "CONSISTENCY", _("Consistency")
    RELIABILITY = "RELIABILITY", _("Reliability")
    TIMELINESS = "TIMELINESS", _("Timeliness")
    PRECISION = "PRECISION", _("Precision")
    INTEGRITY = "INTEGRITY", _("Integrity")


class ScorecardDimension(models.TextChoices):
    STRATEGIC_OBJECTIVE = "STRATEGIC_OBJECTIVE", _("Strategic objective")
    PROGRAM = "PROGRAM", _("Program performance")
    PROJECT = "PROJECT", _("Project performance")
    DIRECTORATE = "DIRECTORATE", _("Directorate performance")
    LEADERSHIP = "LEADERSHIP", _("Leadership performance")
    INDICATOR_ACHIEVEMENT = "INDICATOR_ACHIEVEMENT", _("Indicator achievement")
    BENEFICIARY_REACH = "BENEFICIARY_REACH", _("Beneficiary reach")
    FINANCIAL_EFFICIENCY = "FINANCIAL_EFFICIENCY", _("Financial efficiency")
    ORGANIZATIONAL_EFFECTIVENESS = "ORGANIZATIONAL_EFFECTIVENESS", _(
        "Organizational effectiveness"
    )


class MEALReportType(models.TextChoices):
    RESULTS_FRAMEWORK = "RESULTS_FRAMEWORK", _("Results Framework Report")
    LOGFRAME = "LOGFRAME", _("Logframe Report")
    INDICATOR_PERFORMANCE = "INDICATOR_PERFORMANCE", _("Indicator Performance Report")
    BASELINE = "BASELINE", _("Baseline Report")
    TARGET_ACHIEVEMENT = "TARGET_ACHIEVEMENT", _("Target Achievement Report")
    DATA_COLLECTION = "DATA_COLLECTION", _("Data Collection Report")
    MONITORING_VISIT = "MONITORING_VISIT", _("Monitoring Visit Report")
    EVALUATION = "EVALUATION", _("Evaluation Report")
    DQA = "DQA", _("Data Quality Assessment Report")
    COMPLAINTS = "COMPLAINTS", _("Complaints Report")
    FEEDBACK = "FEEDBACK", _("Feedback Report")
    OUTCOME_HARVESTING = "OUTCOME_HARVESTING", _("Outcome Harvesting Report")
    LEARNING = "LEARNING", _("Learning Report")
    BEST_PRACTICES = "BEST_PRACTICES", _("Best Practices Report")
    LESSONS_LEARNED = "LESSONS_LEARNED", _("Lessons Learned Report")
    SCORECARD = "SCORECARD", _("Performance Scorecard")
    ORGANIZATIONAL_PERFORMANCE = "ORGANIZATIONAL_PERFORMANCE", _(
        "Organizational Performance Report"
    )


REFERENCE_SCHEME_CODES: dict[str, str] = {
    "theory_of_change": "theory_of_change",
    "results_framework": "results_framework",
    "logframe": "logframe",
    "indicator": "indicator",
    "indicator_baseline": "indicator_baseline",
    "indicator_target": "indicator_target",
    "data_collection_plan": "data_collection_plan",
    "monitoring_plan": "monitoring_plan",
    "monitoring_visit": "monitoring_visit",
    "evaluation": "evaluation",
    "dqa": "dqa",
    "complaint": "complaint",
    "feedback": "feedback",
    "corrective_action": "corrective_action",
    "outcome_harvest": "outcome_harvest",
    "learning_log": "learning_log",
    "best_practice": "best_practice",
    "lesson": "meal_lesson",
    "scorecard": "scorecard",
    "meal_report": "meal_report",
    "organizational_kpi": "organizational_kpi",
}


MEAL_ACTION_PERMISSIONS: dict[str, str] = {
    "view": "meal.view",
    "create": "meal.create",
    "update": "meal.update",
    "delete": "meal.delete",
    "submit": "meal.submit",
    "approve": "meal.approve",
    "archive": "meal.archive",
    "restore": "meal.restore",
    "export": "meal.export",
    "view_confidential": "meal.view_confidential",
    "manage_frameworks": "meal.manage_frameworks",
    "manage_indicators": "meal.manage_indicators",
    "manage_data_collection": "meal.manage_data_collection",
    "manage_monitoring": "meal.manage_monitoring",
    "manage_evaluations": "meal.manage_evaluations",
    "manage_dqa": "meal.manage_dqa",
    "manage_accountability": "meal.manage_accountability",
    "manage_learning": "meal.manage_learning",
    "manage_scorecards": "meal.manage_scorecards",
    "manage_reports": "meal.manage_reports",
    "configure": "meal.configure",
    "manage": "meal.manage",
}

DEFAULT_CURRENCY = "ZMW"
