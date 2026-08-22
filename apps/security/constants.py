"""Security Hardening constants."""

from __future__ import annotations


class SecurityConfidentialityLevel:
    """Security confidentiality classification levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    HIGHLY_CONFIDENTIAL = "highly_confidential"

    CHOICES = [
        (PUBLIC, "Public"),
        (INTERNAL, "Internal"),
        (RESTRICTED, "Restricted"),
        (CONFIDENTIAL, "Confidential"),
        (HIGHLY_CONFIDENTIAL, "Highly Confidential"),
    ]


class SecurityStatus:
    """Security entity status values."""

    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"
    UNDER_INVESTIGATION = "under_investigation"
    RESOLVED = "resolved"
    CLOSED = "closed"

    CHOICES = [
        (DRAFT, "Draft"),
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
        (ARCHIVED, "Archived"),
        (PENDING_REVIEW, "Pending Review"),
        (UNDER_INVESTIGATION, "Under Investigation"),
        (RESOLVED, "Resolved"),
        (CLOSED, "Closed"),
    ]


class SecuritySeverity:
    """Security severity levels."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    CHOICES = [
        (INFO, "Info"),
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (CRITICAL, "Critical"),
    ]


class SecurityIncidentCategory:
    """Security incident categories."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_BREACH = "data_breach"
    MALWARE = "malware"
    PHISHING = "phishing"
    BRUTE_FORCE = "brute_force"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    VULNERABILITY_EXPLOIT = "vulnerability_exploit"
    INSIDER_THREAT = "insider_threat"
    CONFIGURATION = "configuration"
    OTHER = "other"

    CHOICES = [
        (AUTHENTICATION, "Authentication"),
        (AUTHORIZATION, "Authorization"),
        (DATA_BREACH, "Data Breach"),
        (MALWARE, "Malware"),
        (PHISHING, "Phishing"),
        (BRUTE_FORCE, "Brute Force"),
        (PRIVILEGE_ESCALATION, "Privilege Escalation"),
        (UNAUTHORIZED_ACCESS, "Unauthorized Access"),
        (VULNERABILITY_EXPLOIT, "Vulnerability Exploit"),
        (INSIDER_THREAT, "Insider Threat"),
        (CONFIGURATION, "Configuration"),
        (OTHER, "Other"),
    ]


class VulnerabilityStatus:
    """Vulnerability status values."""

    IDENTIFIED = "identified"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    PATCHED = "patched"
    MITIGATED = "mitigated"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"
    CLOSED = "closed"

    CHOICES = [
        (IDENTIFIED, "Identified"),
        (TRIAGED, "Triaged"),
        (IN_PROGRESS, "In Progress"),
        (PATCHED, "Patched"),
        (MITIGATED, "Mitigated"),
        (ACCEPTED_RISK, "Accepted Risk"),
        (FALSE_POSITIVE, "False Positive"),
        (CLOSED, "Closed"),
    ]


class VulnerabilitySource:
    """Vulnerability detection sources."""

    SAST = "sast"
    DAST = "dast"
    DEPENDENCY_SCAN = "dependency_scan"
    PENETRATION_TEST = "penetration_test"
    BUG_BOUNTY = "bug_bounty"
    INTERNAL_AUDIT = "internal_audit"
    VENDOR_ADVISORY = "vendor_advisory"
    USER_REPORT = "user_report"
    THREAT_INTELLIGENCE = "threat_intelligence"

    CHOICES = [
        (SAST, "SAST"),
        (DAST, "DAST"),
        (DEPENDENCY_SCAN, "Dependency Scan"),
        (PENETRATION_TEST, "Penetration Test"),
        (BUG_BOUNTY, "Bug Bounty"),
        (INTERNAL_AUDIT, "Internal Audit"),
        (VENDOR_ADVISORY, "Vendor Advisory"),
        (USER_REPORT, "User Report"),
        (THREAT_INTELLIGENCE, "Threat Intelligence"),
    ]


class ThreatEventType:
    """Threat event types."""

    FAILED_LOGIN = "failed_login"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    CREDENTIAL_STUFFING = "credential_stuffing"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PRIVILEGE_ESCALATION_ATTEMPT = "privilege_escalation_attempt"
    UNAUTHORIZED_API_ACCESS = "unauthorized_api_access"
    MALWARE_INDICATOR = "malware_indicator"
    EXCESSIVE_FAILED_REQUESTS = "excessive_failed_requests"
    GEOGRAPHIC_ANOMALY = "geographic_anomaly"
    HIGH_RISK_ADMIN_ACTION = "high_risk_admin_action"
    UNUSUAL_USER_ACTIVITY = "unusual_user_activity"
    SESSION_HIJACKING_ATTEMPT = "session_hijacking_attempt"

    CHOICES = [
        (FAILED_LOGIN, "Failed Login"),
        (BRUTE_FORCE_ATTEMPT, "Brute Force Attempt"),
        (CREDENTIAL_STUFFING, "Credential Stuffing"),
        (SUSPICIOUS_ACTIVITY, "Suspicious Activity"),
        (PRIVILEGE_ESCALATION_ATTEMPT, "Privilege Escalation Attempt"),
        (UNAUTHORIZED_API_ACCESS, "Unauthorized API Access"),
        (MALWARE_INDICATOR, "Malware Indicator"),
        (EXCESSIVE_FAILED_REQUESTS, "Excessive Failed Requests"),
        (GEOGRAPHIC_ANOMALY, "Geographic Anomaly"),
        (HIGH_RISK_ADMIN_ACTION, "High Risk Admin Action"),
        (UNUSUAL_USER_ACTIVITY, "Unusual User Activity"),
        (SESSION_HIJACKING_ATTEMPT, "Session Hijacking Attempt"),
    ]


class MFAMethod:
    """Multi-Factor Authentication methods."""

    TOTP = "totp"
    EMAIL = "email"
    SMS = "sms"
    RECOVERY_CODES = "recovery_codes"
    AUTHENTICATOR_APP = "authenticator_app"
    HARDWARE_TOKEN = "hardware_token"

    CHOICES = [
        (TOTP, "Time-based OTP (TOTP)"),
        (EMAIL, "Email Verification"),
        (SMS, "SMS Verification"),
        (RECOVERY_CODES, "Recovery Codes"),
        (AUTHENTICATOR_APP, "Authenticator App"),
        (HARDWARE_TOKEN, "Hardware Token"),
    ]


class SessionStatus:
    """Session status values."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPICIOUS = "suspicious"
    TERMINATED = "terminated"

    CHOICES = [
        (ACTIVE, "Active"),
        (EXPIRED, "Expired"),
        (REVOKED, "Revoked"),
        (SUSPICIOUS, "Suspicious"),
        (TERMINATED, "Terminated"),
    ]


class ComplianceCheckStatus:
    """Compliance check status values."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    PENDING = "pending"

    CHOICES = [
        (PASS, "Pass"),
        (FAIL, "Fail"),
        (WARNING, "Warning"),
        (NOT_APPLICABLE, "Not Applicable"),
        (PENDING, "Pending"),
    ]


class AccessReviewStatus:
    """Access review status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

    CHOICES = [
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (OVERDUE, "Overdue"),
        (CANCELLED, "Cancelled"),
    ]


class AccessReviewDecision:
    """Access review decisions."""

    APPROVE = "approve"
    REVOKE = "revoke"
    MODIFY = "modify"
    ESCALATE = "escalate"

    CHOICES = [
        (APPROVE, "Approve"),
        (REVOKE, "Revoke"),
        (MODIFY, "Modify"),
        (ESCALATE, "Escalate"),
    ]


class SecurityModule:
    """Security module domains."""

    IDENTITY = "identity"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SESSION = "session"
    ACCOUNTS = "accounts"
    API = "api"
    DATABASE = "database"
    STORAGE = "storage"
    DOCUMENTS = "documents"
    COMMUNICATIONS = "communications"
    INFRASTRUCTURE = "infrastructure"
    CLOUD = "cloud"
    INTEGRATIONS = "integrations"
    ENCRYPTION = "encryption"
    SECRETS = "secrets"
    MONITORING = "monitoring"
    INCIDENT_RESPONSE = "incident_response"
    VULNERABILITY = "vulnerability"
    COMPLIANCE = "compliance"