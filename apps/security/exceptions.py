"""Security Hardening exceptions."""


class SecurityError(Exception):
    """Base exception for security-related errors."""

    pass


class AuthenticationError(SecurityError):
    """Authentication-related errors."""

    pass


class AuthorizationError(SecurityError):
    """Authorization-related errors."""

    pass


class MFAError(SecurityError):
    """Multi-Factor Authentication errors."""

    pass


class SessionError(SecurityError):
    """Session management errors."""

    pass


class EncryptionError(SecurityError):
    """Encryption-related errors."""

    pass


class SecretsError(SecurityError):
    """Secrets management errors."""

    pass


class VulnerabilityError(SecurityError):
    """Vulnerability management errors."""

    pass


class ThreatDetectionError(SecurityError):
    """Threat detection errors."""

    pass


class IncidentError(SecurityError):
    """Security incident errors."""

    pass


class AccessReviewError(SecurityError):
    """Access review errors."""

    pass


class ComplianceError(SecurityError):
    """Compliance errors."""

    pass


class ConfigurationError(SecurityError):
    """Security configuration errors."""

    pass


class PolicyViolationError(SecurityError):
    """Security policy violation errors."""

    pass


class InvalidTokenError(AuthenticationError):
    """Invalid or expired token errors."""

    pass


class RateLimitExceededError(AuthenticationError):
    """Rate limit exceeded errors."""

    pass


class SuspiciousActivityError(SecurityError):
    """Suspicious activity detected errors."""

    pass


class SecurityPolicyError(SecurityError):
    """Security policy configuration errors."""

    pass