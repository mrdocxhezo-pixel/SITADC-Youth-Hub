"""Constants for the Governance, Risk, Compliance and Safeguarding (Phase 29)."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class GovernanceType(models.TextChoices):
    """Governance domains supported by the GRCS module."""

    POLICY = "POLICY", _("Policy")
    RISK = "RISK", _("Risk")
    COMPLIANCE = "COMPLIANCE", _("Compliance")
    ETHICS = "ETHICS", _("Ethics")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    INCIDENT = "INCIDENT", _("Incident")
    COMPLAINT = "COMPLAINT", _("Complaint")
    WHISTLEBLOWER = "WHISTLEBLOWER", _("Whistleblower")
    CAPA = "CAPA", _("Corrective & Preventive Action")
    GOVERNANCE_MEETING = "GOVERNANCE_MEETING", _("Governance Meeting")


class Priority(models.TextChoices):
    """Priority levels applied to governance records."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class ConfidentialityLevel(models.TextChoices):
    """Confidentiality classifications inherited by governance records."""

    PUBLIC = "PUBLIC", _("Public")
    INTERNAL = "INTERNAL", _("Internal")
    RESTRICTED = "RESTRICTED", _("Restricted")
    CONFIDENTIAL = "CONFIDENTIAL", _("Confidential")
    HIGHLY_CONFIDENTIAL = "HIGHLY_CONFIDENTIAL", _("Highly Confidential")


class PolicyCategory(models.TextChoices):
    """Policy categories."""

    HR = "HR", _("Human Resources")
    FINANCE = "FINANCE", _("Finance")
    OPERATIONS = "OPERATIONS", _("Operations")
    IT = "IT", _("Information Technology")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    ETHICS = "ETHICS", _("Ethics")
    COMPLIANCE = "COMPLIANCE", _("Compliance")
    GOVERNANCE = "GOVERNANCE", _("Governance")
    OTHER = "OTHER", _("Other")


class RiskCategory(models.TextChoices):
    """Enterprise risk categories."""

    STRATEGIC = "STRATEGIC", _("Strategic")
    OPERATIONAL = "OPERATIONAL", _("Operational")
    FINANCIAL = "FINANCIAL", _("Financial")
    COMPLIANCE = "COMPLIANCE", _("Compliance")
    REPUTATIONAL = "REPUTATIONAL", _("Reputational")
    INFORMATION_SECURITY = "INFORMATION_SECURITY", _("Information Security")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    PROJECT = "PROJECT", _("Project")
    PROGRAMME = "PROGRAMME", _("Programme")
    ENVIRONMENTAL = "ENVIRONMENTAL", _("Environmental")
    LEGAL = "LEGAL", _("Legal")


class RiskRating(models.TextChoices):
    """Risk ratings derived from likelihood and impact."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class RiskAssessmentType(models.TextChoices):
    """Types of risk assessments."""

    INITIAL = "INITIAL", _("Initial Assessment")
    REVIEW = "REVIEW", _("Review")
    POST_INCIDENT = "POST_INCIDENT", _("Post-Incident")
    AUDIT_FINDING = "AUDIT_FINDING", _("Audit Finding")


class RiskTreatmentType(models.TextChoices):
    """Risk treatment strategies."""

    AVOID = "AVOID", _("Avoid")
    TRANSFER = "TRANSFER", _("Transfer")
    MITIGATE = "MITIGATE", _("Mitigate")
    ACCEPT = "ACCEPT", _("Accept")


class ComplianceType(models.TextChoices):
    """Compliance requirement sources."""

    REGULATORY = "REGULATORY", _("Regulatory")
    DONOR = "DONOR", _("Donor Requirements")
    GRANT = "GRANT", _("Grant Conditions")
    INTERNAL_POLICY = "INTERNAL_POLICY", _("Internal Policy")
    CONTRACTUAL = "CONTRACTUAL", _("Contractual")
    INDUSTRY_STANDARD = "INDUSTRY_STANDARD", _("Industry Standard")
    LEGAL = "LEGAL", _("Legal")


class ComplianceAssessmentResult(models.TextChoices):
    """Compliance assessment results."""

    COMPLIANT = "COMPLIANT", _("Compliant")
    PARTIALLY_COMPLIANT = "PARTIALLY_COMPLIANT", _("Partially Compliant")
    NON_COMPLIANT = "NON_COMPLIANT", _("Non-Compliant")
    NOT_APPLICABLE = "NOT_APPLICABLE", _("Not Applicable")


class ControlType(models.TextChoices):
    """Internal control categories."""

    FINANCIAL = "FINANCIAL", _("Financial")
    OPERATIONAL = "OPERATIONAL", _("Operational")
    ADMINISTRATIVE = "ADMINISTRATIVE", _("Administrative")
    IT = "IT", _("IT/Technology")
    PROCUREMENT = "PROCUREMENT", _("Procurement")
    HR = "HR", _("Human Resources")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")


class ControlFrequency(models.TextChoices):
    """Internal control review frequency."""

    CONTINUOUS = "CONTINUOUS", _("Continuous")
    REAL_TIME = "REAL_TIME", _("Real-time")
    DAILY = "DAILY", _("Daily")
    WEEKLY = "WEEKLY", _("Weekly")
    MONTHLY = "MONTHLY", _("Monthly")
    QUARTERLY = "QUARTERLY", _("Quarterly")
    ANNUALLY = "ANNUALLY", _("Annually")
    AS_NEEDED = "AS_NEEDED", _("As needed")


class EthicsCaseType(models.TextChoices):
    """Ethics case categories."""

    CONFLICT_OF_INTEREST = "CONFLICT_OF_INTEREST", _("Conflict of Interest")
    CODE_OF_CONDUCT_VIOLATION = "CODE_OF_CONDUCT_VIOLATION", _(
        "Code of Conduct Violation"
    )
    FRAUD = "FRAUD", _("Fraud")
    CORRUPTION = "CORRUPTION", _("Corruption")
    HARASSMENT = "HARASSMENT", _("Harassment")
    DISCRIMINATION = "DISCRIMINATION", _("Discrimination")
    OTHER = "OTHER", _("Other Ethics Issue")


class DeclarationType(models.TextChoices):
    """Conflict of interest declaration types."""

    FINANCIAL = "FINANCIAL", _("Financial Interest")
    PERSONAL = "PERSONAL", _("Personal Relationship")
    PROFESSIONAL = "PROFESSIONAL", _("Professional Affiliation")
    FAMILY = "FAMILY", _("Family Connection")
    BUSINESS = "BUSINESS", _("Business Interest")
    OTHER = "OTHER", _("Other Interest")


class SafeguardingCategory(models.TextChoices):
    """Safeguarding case categories."""

    CHILD_PROTECTION = "CHILD_PROTECTION", _("Child Protection")
    VULNERABLE_ADULT = "VULNERABLE_ADULT", _("Vulnerable Adult Protection")
    WORKPLACE_SAFEGUARDING = "WORKPLACE_SAFEGUARDING", _("Workplace Safeguarding")
    ONLINE_SAFETY = "ONLINE_SAFETY", _("Online Safety")
    OTHER = "OTHER", _("Other Safeguarding Concern")


class IncidentCategory(models.TextChoices):
    """Incident categories."""

    HEALTH_AND_SAFETY = "HEALTH_AND_SAFETY", _("Health and Safety")
    SECURITY = "SECURITY", _("Security")
    PROGRAMME = "PROGRAMME", _("Programme Incident")
    OPERATIONAL = "OPERATIONAL", _("Operational")
    FINANCIAL = "FINANCIAL", _("Financial")
    TECHNOLOGY = "TECHNOLOGY", _("Technology")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    ENVIRONMENTAL = "ENVIRONMENTAL", _("Environmental")
    REPUTATIONAL = "REPUTATIONAL", _("Reputational")
    OTHER = "OTHER", _("Other")


class IncidentSeverity(models.TextChoices):
    """Incident severity levels."""

    LOW = "LOW", _("Low")
    MEDIUM = "MEDIUM", _("Medium")
    HIGH = "HIGH", _("High")
    CRITICAL = "CRITICAL", _("Critical")


class ComplaintType(models.TextChoices):
    """Complaint categories."""

    SERVICE_DELIVERY = "SERVICE_DELIVERY", _("Service Delivery")
    STAFF_CONDUCT = "STAFF_CONDUCT", _("Staff Conduct")
    POLICY_ISSUE = "POLICY_ISSUE", _("Policy Issue")
    FACILITIES = "FACILITIES", _("Facilities")
    PROGRAMME = "PROGRAMME", _("Programme")
    FINANCIAL = "FINANCIAL", _("Financial")
    OTHER = "OTHER", _("Other")


class ResolutionType(models.TextChoices):
    """Complaint resolution outcomes."""

    RESOLVED = "RESOLVED", _("Resolved")
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED", _("Partially Resolved")
    UNRESOLVED = "UNRESOLVED", _("Unresolved")
    REFERRED = "REFERRED", _("Referred to altro")
    WITHDRAWN = "WITHDRAWN", _("Withdrawn")


class WhistleblowerReportType(models.TextChoices):
    """Whistleblower report categories."""

    FRAUD = "FRAUD", _("Fraud")
    CORRUPTION = "CORRUPTION", _("Corruption")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding")
    ETHICS_VIOLATION = "ETHICS_VIOLATION", _("Ethics Violation")
    POLICY_VIOLATION = "POLICY_VIOLATION", _("Policy Violation")
    FINANCIAL_MISMANAGEMENT = "FINANCIAL_MISMANAGEMENT", _("Financial Mismanagement")
    OTHER = "OTHER", _("Other")


class CAPPAActionType(models.TextChoices):
    """Corrective & Preventive Action types."""

    CORRECTIVE = "CORRECTIVE", _("Corrective Action")
    PREVENTIVE = "PREVENTIVE", _("Preventive Action")
    BOTH = "BOTH", _("Both Corrective and Preventive")


class GovernanceDocumentType(models.TextChoices):
    """Governance document types."""

    POLICY = "POLICY", _("Policy")
    PROCEDURE = "PROCEDURE", _("Procedure")
    GUIDELINE = "GUIDELINE", _("Guideline")
    FORM = "FORM", _("Form")
    TEMPLATE = "TEMPLATE", _("Template")
    REPORT = "REPORT", _("Report")
    EVIDENCE = "EVIDENCE", _("Evidence")
    INVESTIGATION = "INVESTIGATION", _("Investigation Report")
    AUDIT = "AUDIT", _("Audit Report")
    LEGAL = "LEGAL", _("Legal Document")
    OTHER = "OTHER", _("Other")


class MeetingType(models.TextChoices):
    """Governance meeting types."""

    BOARD = "BOARD", _("Board Meeting")
    EXECUTIVE = "EXECUTIVE", _("Executive Committee")
    AUDIT = "AUDIT", _("Audit Committee")
    RISK = "RISK", _("Risk Committee")
    COMPLIANCE = "COMPLIANCE", _("Compliance Committee")
    SAFEGUARDING = "SAFEGUARDING", _("Safeguarding Committee")
    ETHICS = "ETHICS", _("Ethics Committee")
    OTHER = "OTHER", _("Other Governance Meeting")


class AttendanceStatus(models.TextChoices):
    """Meeting attendance statuses."""

    PRESENT = "PRESENT", _("Present")
    ABSENT = "ABSENT", _("Absent")
    APOLOGIES = "APOLOGIES", _("Apologies")
    LATE = "LATE", _("Late")
    LEFT_EARLY = "LEFT_EARLY", _("Left early")


class NotificationType(models.TextChoices):
    """Governance notification event types."""

    POLICY_REVIEW_DUE = "POLICY_REVIEW_DUE", _("Policy Review Due")
    POLICY_APPROVED = "POLICY_APPROVED", _("Policy Approved")
    RISK_REVIEW_DUE = "RISK_REVIEW_DUE", _("Risk Review Due")
    HIGH_RISK_ALERT = "HIGH_RISK_ALERT", _("High Risk Alert")
    COMPLIANCE_ISSUE_DETECTED = "COMPLIANCE_ISSUE_DETECTED", _(
        "Compliance Issue Detected"
    )
    SAFEGUARDING_CASE_ASSIGNED = "SAFEGUARDING_CASE_ASSIGNED", _(
        "Safeguarding Case Assigned"
    )
    INCIDENT_REPORTED = "INCIDENT_REPORTED", _("Incident Reported")
    COMPLAINT_RECEIVED = "COMPLAINT_RECEIVED", _("Complaint Received")
    WHISTLEBLOWER_REPORT_RECEIVED = "WHISTLEBLOWER_REPORT_RECEIVED", _(
        "Whistleblower Report Received"
    )
    CAPA_OVERDUE = "CAPA_OVERDUE", _("CAPA Overdue")
    GOVERNANCE_MEETING_REMINDER = "GOVERNANCE_MEETING_REMINDER", _(
        "Governance Meeting Reminder"
    )
    RISK_ASSESSMENT_COMPLETED = "RISK_ASSESSMENT_COMPLETED", _(
        "Risk Assessment Completed"
    )
    COMPLIANCE_ASSESSMENT_COMPLETED = "COMPLIANCE_ASSESSMENT_COMPLETED", _(
        "Compliance Assessment Completed"
    )
    ETHICS_CASE_RESOLVED = "ETHICS_CASE_RESOLVED", _("Ethics Case Resolved")


class TimelineEventType(models.TextChoices):
    """Governance timeline event types."""

    RECORD_CREATED = "RECORD_CREATED", _("Governance Record Created")
    POLICY_APPROVED = "POLICY_APPROVED", _("Policy Approved")
    RISK_IDENTIFIED = "RISK_IDENTIFIED", _("Risk Identified")
    RISK_ASSESSED = "RISK_ASSESSED", _("Risk Assessed")
    COMPLIANCE_REVIEW_COMPLETED = "COMPLIANCE_REVIEW_COMPLETED", _(
        "Compliance Review Completed"
    )
    SAFEGUARDING_CASE_OPENED = "SAFEGUARDING_CASE_OPENED", _("Safeguarding Case Opened")
    INCIDENT_REPORTED = "INCIDENT_REPORTED", _("Incident Reported")
    COMPLAINT_RECEIVED = "COMPLAINT_RECEIVED", _("Complaint Received")
    WHISTLEBLOWER_REPORT_SUBMITTED = "WHISTLEBLOWER_REPORT_SUBMITTED", _(
        "Whistleblower Report Submitted"
    )
    CAPA_INITIATED = "CAPA_INITIATED", _("CAPA Initiated")
    GOVERNANCE_RECORD_ARCHIVED = "GOVERNANCE_RECORD_ARCHIVED", _(
        "Governance Record Archived"
    )
    MEETING_HELD = "MEETING_HELD", _("Governance Meeting Held")
    DECISION_MADE = "DECISION_MADE", _("Decision Made")


# Risk scoring boundaries used by the risk matrix (likelihood * impact).
RISK_MATRIX_LOW_MAX = 5
RISK_MATRIX_MEDIUM_MAX = 10
RISK_MATRIX_HIGH_MAX = 15
RISK_MATRIX_MEDIUM_MIN = 6
RISK_MATRIX_HIGH_MIN = 11
RISK_MATRIX_CRITICAL_MIN = 16

# Likelihood / impact scale bounds.
RISK_SCALE_MIN = 1
RISK_SCALE_MAX = 5
