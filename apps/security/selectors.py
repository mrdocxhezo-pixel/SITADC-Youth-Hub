"""
Read-only retrieval helpers for the Security Hardening framework.

Selectors never modify data; they only fetch and shape it for views,
services and templates.
"""

from __future__ import annotations

from django.db.models import QuerySet, Q, Count
from django.utils import timezone

from apps.accounts.models import User
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role

from .models import (
    EnterpriseSecurityPolicy,
    Identity,
    ServiceIdentity,
    OrganizationalIdentity,
    Permission,
    RolePermission,
    IdentityRole,
    LoginAttempt,
    AccessReview,
    AccessReviewItem,
    RoleHierarchy,
    PermissionGrant,
    Session,
    MFAEnrollment,
    MFAVerificationAttempt,
    APICredential,
    APIAccessToken,
    APIRateLimit,
    DatabaseSecurityPolicy,
    DatabaseAccessLog,
    SecureFile,
)
from .constants import (
    SecurityStatus,
    SecurityConfidentialityLevel,
    MFAMethod,
    SessionStatus,
    AccessReviewStatus,
    AccessReviewDecision,
)


def get_security_policies(
    policy_type: str | None = None,
    is_active: bool | None = True,
) -> QuerySet[EnterpriseSecurityPolicy]:
    """Return security policies with optional filters."""
    queryset = EnterpriseSecurityPolicy.objects.all().order_by("policy_type", "name")
    if policy_type:
        queryset = queryset.filter(policy_type=policy_type)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return queryset


def get_password_policy() -> EnterpriseSecurityPolicy | None:
    """Get the active password policy."""
    return EnterpriseSecurityPolicy.objects.filter(
        policy_type="password", is_active=True
    ).first()


def get_session_policy() -> EnterpriseSecurityPolicy | None:
    """Get the active session policy."""
    return EnterpriseSecurityPolicy.objects.filter(
        policy_type="session", is_active=True
    ).first()


def get_identities(
    identity_type: str | None = None,
    status: str | None = None,
    owner: User | None = None,
) -> QuerySet[Identity]:
    """Return identities with optional filters."""
    queryset = Identity.objects.select_related("owner").prefetch_related("managed_by").order_by("identity_type", "identifier")
    if identity_type:
        queryset = queryset.filter(identity_type=identity_type)
    if status:
        queryset = queryset.filter(status=status)
    if owner:
        queryset = queryset.filter(owner=owner)
    return queryset


def get_active_identities() -> QuerySet[Identity]:
    """Return active, non-expired identities."""
    now = timezone.now()
    return Identity.objects.filter(
        status=SecurityStatus.ACTIVE
    ).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lte=now)
    ).order_by("identity_type", "identifier")


def get_identity_by_id(identity_id) -> Identity:
    """Retrieve a single identity by primary key."""
    return Identity.objects.select_related("owner").prefetch_related("managed_by").get(id=identity_id)


def get_identity_by_identifier(identifier: str) -> Identity:
    """Retrieve a single identity by identifier."""
    return Identity.objects.select_related("owner").prefetch_related("managed_by").get(identifier=identifier)


def get_service_identities(
    service_type: str | None = None,
    is_active: bool | None = True,
) -> QuerySet[ServiceIdentity]:
    """Return service identities with optional filters."""
    queryset = ServiceIdentity.objects.select_related("owner").prefetch_related("managed_by").order_by("service_type", "identifier")
    if service_type:
        queryset = queryset.filter(service_type=service_type)
    if is_active is not None:
        status_filter = SecurityStatus.ACTIVE if is_active else SecurityStatus.INACTIVE
        queryset = queryset.filter(status=status_filter)
    return queryset


def get_organizational_identities(
    org_identity_type: str | None = None,
    organization_unit: OrganizationUnit | None = None,
) -> QuerySet[OrganizationalIdentity]:
    """Return organizational identities with optional filters."""
    queryset = OrganizationalIdentity.objects.select_related(
        "owner", "parent_organization", "organization_unit", "contact_person"
    ).prefetch_related("managed_by").order_by("org_identity_type", "identifier")
    if org_identity_type:
        queryset = queryset.filter(org_identity_type=org_identity_type)
    if organization_unit:
        queryset = queryset.filter(organization_unit=organization_unit)
    return queryset


def get_permissions(
    module: str | None = None,
    resource_type: str | None = None,
    is_assignable: bool | None = True,
) -> QuerySet[Permission]:
    """Return permissions with optional filters."""
    queryset = Permission.objects.all().order_by("module", "resource_type", "action", "name")
    if module:
        queryset = queryset.filter(module=module)
    if resource_type:
        queryset = queryset.filter(resource_type=resource_type)
    if is_assignable is not None:
        queryset = queryset.filter(is_assignable=is_assignable)
    return queryset


def get_permission_by_slug(slug: str) -> Permission:
    """Retrieve a single permission by slug."""
    return Permission.objects.get(slug=slug)


def get_permissions_by_module(module: str) -> QuerySet[Permission]:
    """Return permissions for a specific module."""
    return get_permissions(module=module)


def get_role_permissions(role: Role) -> QuerySet[RolePermission]:
    """Return the role-permission mappings for a role."""
    return RolePermission.objects.filter(
        role=role, is_active=True
    ).select_related("permission").order_by("permission__module", "permission__resource_type", "permission__action")


def get_permission_roles(permission: Permission) -> QuerySet[RolePermission]:
    """Return the role-permission mappings for a permission."""
    return RolePermission.objects.filter(
        permission=permission, is_active=True
    ).select_related("role").order_by("role__priority", "role__name")


def get_identity_roles(
    identity: Identity,
    is_active: bool | None = True,
) -> QuerySet[IdentityRole]:
    """Return identity-role assignments with optional filters."""
    queryset = IdentityRole.objects.filter(identity=identity).select_related("role", "assigned_by").order_by("-assigned_at")
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return queryset


def get_active_identity_roles(identity: Identity) -> QuerySet[IdentityRole]:
    """Return active, non-expired identity-role assignments."""
    now = timezone.now()
    return IdentityRole.objects.filter(
        identity=identity,
        is_active=True,
    ).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lte=now)
    ).select_related("role", "assigned_by").order_by("-assigned_at")


def get_role_assignments(
    role: Role,
    is_active: bool | None = True,
) -> QuerySet[IdentityRole]:
    """Return role assignments for a role."""
    queryset = IdentityRole.objects.filter(role=role).select_related("identity", "assigned_by").order_by("-assigned_at")
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return queryset


def get_active_role_assignments(role: Role) -> QuerySet[IdentityRole]:
    """Return active, non-expired role assignments."""
    now = timezone.now()
    return IdentityRole.objects.filter(
        role=role,
        is_active=True,
    ).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lte=now)
    ).select_related("identity", "assigned_by").order_by("-assigned_at")


def get_permission_grants(
    identity: Identity,
    is_active: bool | None = True,
) -> QuerySet[PermissionGrant]:
    """Return direct permission grants for an identity."""
    queryset = PermissionGrant.objects.filter(identity=identity).select_related("permission", "granted_by").order_by("-granted_at")
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return queryset


def get_active_permission_grants(identity: Identity) -> QuerySet[PermissionGrant]:
    """Return active, non-expired permission grants."""
    now = timezone.now()
    return PermissionGrant.objects.filter(
        identity=identity,
        is_active=True,
    ).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lte=now)
    ).select_related("permission", "granted_by").order_by("-granted_at")


def get_role_hierarchy(parent_role: Role | None = None) -> QuerySet[RoleHierarchy]:
    """Return role hierarchy, optionally filtered by parent."""
    queryset = RoleHierarchy.objects.select_related("parent_role", "child_role", "created_by").order_by("parent_role__priority", "child_role__priority")
    if parent_role:
        queryset = queryset.filter(parent_role=parent_role)
    return queryset


def get_login_attempts(
    identity: Identity | None = None,
    ip_address: str | None = None,
    outcome: str | None = None,
    is_suspicious: bool | None = None,
    days: int = 30,
) -> QuerySet[LoginAttempt]:
    """Return login attempts with optional filters."""
    since = timezone.now() - timezone.timedelta(days=days)
    queryset = LoginAttempt.objects.filter(created_at__gte=since).select_related("identity").order_by("-created_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    if ip_address:
        queryset = queryset.filter(ip_address=ip_address)
    if outcome:
        queryset = queryset.filter(outcome=outcome)
    if is_suspicious is not None:
        queryset = queryset.filter(is_suspicious=is_suspicious)
    return queryset


def get_suspicious_login_attempts(days: int = 7) -> QuerySet[LoginAttempt]:
    """Return suspicious login attempts."""
    return get_login_attempts(is_suspicious=True, days=days)


def get_failed_login_attempts(
    identity: Identity | None = None,
    days: int = 7,
) -> QuerySet[LoginAttempt]:
    """Return failed login attempts."""
    failed_outcomes = [
        LoginAttempt.FAILED_INVALID_CREDENTIALS,
        LoginAttempt.FAILED_ACCOUNT_LOCKED,
        LoginAttempt.FAILED_EXPIRED,
        LoginAttempt.FAILED_DISABLED,
        LoginAttempt.FAILED_MFA_REQUIRED,
        LoginAttempt.FAILED_MFA_INVALID,
        LoginAttempt.FAILED_OTHER,
    ]
    since = timezone.now() - timezone.timedelta(days=days)
    queryset = LoginAttempt.objects.filter(
        created_at__gte=since,
        outcome__in=failed_outcomes,
    ).select_related("identity").order_by("-created_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    return queryset


def get_access_reviews(
    review_type: str | None = None,
    status: str | None = None,
    reviewer: User | None = None,
) -> QuerySet[AccessReview]:
    """Return access reviews with optional filters."""
    queryset = AccessReview.objects.select_related(
        "target_identity", "target_role", "target_permission", "lead_reviewer"
    ).prefetch_related("reviewers").order_by("-started_at")
    if review_type:
        queryset = queryset.filter(review_type=review_type)
    if status:
        queryset = queryset.filter(status=status)
    if reviewer:
        queryset = queryset.filter(reviewers=reviewer)
    return queryset


def get_pending_access_reviews(reviewer: User | None = None) -> QuerySet[AccessReview]:
    """Return pending access reviews, optionally for a specific reviewer."""
    queryset = AccessReview.objects.filter(status=AccessReviewStatus.PENDING)
    if reviewer:
        queryset = queryset.filter(reviewers=reviewer)
    return queryset.order_by("due_date")


def get_overdue_access_reviews() -> QuerySet[AccessReview]:
    """Return overdue access reviews."""
    now = timezone.now()
    return AccessReview.objects.filter(
        status__in=[AccessReviewStatus.PENDING, AccessReviewStatus.IN_PROGRESS],
        due_date__lt=now,
    ).order_by("due_date")


def get_access_review_items(
    access_review: AccessReview,
    decision: str | None = None,
) -> QuerySet[AccessReviewItem]:
    """Return items for an access review."""
    queryset = AccessReviewItem.objects.filter(access_review=access_review).select_related(
        "identity", "role", "permission", "identity_role", "reviewer"
    ).order_by("-reviewed_at")
    if decision:
        queryset = queryset.filter(decision=decision)
    return queryset


def get_review_items_by_reviewer(access_review: AccessReview, reviewer: User) -> QuerySet[AccessReviewItem]:
    """Return review items assigned to a specific reviewer."""
    return AccessReviewItem.objects.filter(
        access_review=access_review,
        reviewer=reviewer,
    ).select_related("identity", "role", "permission", "identity_role").order_by("-reviewed_at")


def get_sessions(
    identity: Identity | None = None,
    status: str | None = None,
    ip_address: str | None = None,
) -> QuerySet[Session]:
    """Return sessions with optional filters."""
    queryset = Session.objects.select_related("identity").order_by("-started_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    if status:
        queryset = queryset.filter(status=status)
    if ip_address:
        queryset = queryset.filter(ip_address=ip_address)
    return queryset


def get_active_sessions(identity: Identity | None = None) -> QuerySet[Session]:
    """Return active, non-expired sessions."""
    now = timezone.now()
    queryset = Session.objects.filter(
        status=SessionStatus.ACTIVE,
    ).exclude(
        Q(expires_at__lte=now) | Q(terminated_at__isnull=False)
    ).select_related("identity").order_by("-started_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    return queryset


def get_session_by_key(session_key: str) -> Session:
    """Retrieve a session by session key."""
    return Session.objects.select_related("identity").get(session_key=session_key)


def get_mfa_enrollments(
    identity: Identity,
    is_enabled: bool | None = True,
) -> QuerySet[MFAEnrollment]:
    """Return MFA enrollments for an identity."""
    queryset = MFAEnrollment.objects.filter(identity=identity).order_by("-is_primary", "-enrolled_at")
    if is_enabled is not None:
        queryset = queryset.filter(is_enabled=is_enabled)
    return queryset


def get_primary_mfa_enrollment(identity: Identity) -> MFAEnrollment | None:
    """Get the primary MFA enrollment for an identity."""
    return MFAEnrollment.objects.filter(
        identity=identity,
        is_primary=True,
        is_enabled=True,
    ).first()


def get_mfa_enrollment_by_method(identity: Identity, method: str) -> MFAEnrollment | None:
    """Get MFA enrollment by method for an identity."""
    try:
        return MFAEnrollment.objects.get(identity=identity, method=method)
    except MFAEnrollment.DoesNotExist:
        return None


def get_mfa_verification_attempts(
    identity: Identity | None = None,
    enrollment: MFAEnrollment | None = None,
    outcome: str | None = None,
    days: int = 30,
) -> QuerySet[MFAVerificationAttempt]:
    """Return MFA verification attempts with optional filters."""
    since = timezone.now() - timezone.timedelta(days=days)
    queryset = MFAVerificationAttempt.objects.filter(attempted_at__gte=since).select_related("identity", "enrollment").order_by("-attempted_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    if enrollment:
        queryset = queryset.filter(enrollment=enrollment)
    if outcome:
        queryset = queryset.filter(outcome=outcome)
    return queryset


def get_failed_mfa_attempts(
    identity: Identity | None = None,
    days: int = 7,
) -> QuerySet[MFAVerificationAttempt]:
    """Return failed MFA verification attempts."""
    failed_outcomes = [
        MFAVerificationAttempt.FAILED_INVALID_CODE,
        MFAVerificationAttempt.FAILED_EXPIRED_CODE,
        MFAVerificationAttempt.FAILED_RATE_LIMITED,
        MFAVerificationAttempt.FAILED_OTHER,
    ]
    since = timezone.now() - timezone.timedelta(days=days)
    queryset = MFAVerificationAttempt.objects.filter(
        attempted_at__gte=since,
        outcome__in=failed_outcomes,
    ).select_related("identity", "enrollment").order_by("-attempted_at")
    if identity:
        queryset = queryset.filter(identity=identity)
    return queryset


def get_api_credentials(
    identity: Identity,
    is_active: bool | None = True,
    credential_type: str | None = None,
) -> QuerySet[APICredential]:
    """Return API credentials for an identity."""
    queryset = APICredential.objects.filter(identity=identity).order_by("-created_at")
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    if credential_type:
        queryset = queryset.filter(credential_type=credential_type)
    return queryset


def get_valid_api_credentials(identity: Identity) -> QuerySet[APICredential]:
    """Return valid (active, non-expired, non-compromised) API credentials."""
    now = timezone.now()
    return APICredential.objects.filter(
        identity=identity,
        is_active=True,
    ).exclude(
        Q(expires_at__isnull=False) & Q(expires_at__lte=now) | Q(is_compromised=True)
    ).order_by("-created_at")


def get_api_access_tokens(
    credential: APICredential,
    is_revoked: bool | None = False,
) -> QuerySet[APIAccessToken]:
    """Return API access tokens for a credential."""
    queryset = APIAccessToken.objects.filter(credential=credential).select_related("identity").order_by("-issued_at")
    if is_revoked is not None:
        queryset = queryset.filter(is_revoked=is_revoked)
    return queryset


def get_valid_api_access_tokens(credential: APICredential) -> QuerySet[APIAccessToken]:
    """Return valid (non-expired, non-revoked) API access tokens."""
    now = timezone.now()
    return APIAccessToken.objects.filter(
        credential=credential,
        is_revoked=False,
    ).exclude(
        Q(expires_at__lte=now) | Q(not_before__isnull=False) & Q(not_before__gt=now)
    ).select_related("identity").order_by("-issued_at")


def get_api_rate_limits(
    credential: APICredential | None = None,
    identity: Identity | None = None,
    hours: int = 24,
) -> QuerySet[APIRateLimit]:
    """Return API rate limit records."""
    since = timezone.now() - timezone.timedelta(hours=hours)
    queryset = APIRateLimit.objects.filter(window_start__gte=since).select_related("credential", "identity").order_by("-window_start")
    if credential:
        queryset = queryset.filter(credential=credential)
    if identity:
        queryset = queryset.filter(identity=identity)
    return queryset


def get_database_security_policies(
    database_type: str | None = None,
    is_active: bool | None = True,
) -> QuerySet[DatabaseSecurityPolicy]:
    """Return database security policies."""
    queryset = DatabaseSecurityPolicy.objects.all().order_by("name")
    if database_type:
        queryset = queryset.filter(database_type=database_type)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active)
    return queryset


def get_database_access_logs(
    database_policy: DatabaseSecurityPolicy,
    username: str | None = None,
    client_ip: str | None = None,
    days: int = 7,
) -> QuerySet[DatabaseAccessLog]:
    """Return database access logs."""
    since = timezone.now() - timezone.timedelta(days=days)
    queryset = DatabaseAccessLog.objects.filter(
        database_policy=database_policy,
        connection_started__gte=since,
    ).order_by("-connection_started")
    if username:
        queryset = queryset.filter(username=username)
    if client_ip:
        queryset = queryset.filter(client_ip=client_ip)
    return queryset


def get_secure_files(
    owner: Identity | None = None,
    uploaded_by: Identity | None = None,
    confidentiality: str | None = None,
    is_encrypted: bool | None = None,
    is_active: bool | None = True,
) -> QuerySet[SecureFile]:
    """Return secure files with optional filters."""
    queryset = SecureFile.objects.select_related("owner", "uploaded_by").prefetch_related("allowed_identities", "allowed_roles").order_by("-created_at")
    if owner:
        queryset = queryset.filter(owner=owner)
    if uploaded_by:
        queryset = queryset.filter(uploaded_by=uploaded_by)
    if confidentiality:
        queryset = queryset.filter(confidentiality=confidentiality)
    if is_encrypted is not None:
        queryset = queryset.filter(is_encrypted=is_encrypted)
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active, is_deleted=False)
    return queryset


def get_latest_file_versions() -> QuerySet[SecureFile]:
    """Return only the latest version of each file."""
    return SecureFile.objects.filter(is_latest_version=True, is_deleted=False).order_by("-created_at")


def get_files_accessible_by(identity: Identity) -> QuerySet[SecureFile]:
    """Return files accessible by a given identity."""
    return SecureFile.objects.filter(
        Q(is_public=True) |
        Q(owner=identity) |
        Q(uploaded_by=identity) |
        Q(allowed_identities=identity) |
        Q(allowed_roles__identities=identity)
    ).filter(is_deleted=False).distinct().order_by("-created_at")


def get_security_dashboard_stats() -> dict:
    """Get statistics for the security dashboard."""
    now = timezone.now()
    last_7_days = now - timezone.timedelta(days=7)
    last_30_days = now - timezone.timedelta(days=30)

    return {
        "total_identities": Identity.objects.count(),
        "active_identities": get_active_identities().count(),
        "service_identities": ServiceIdentity.objects.filter(status=SecurityStatus.ACTIVE).count(),
        "total_sessions": Session.objects.count(),
        "active_sessions": get_active_sessions().count(),
        "failed_logins_7d": get_failed_login_attempts(days=7).count(),
        "suspicious_logins_7d": get_suspicious_login_attempts(days=7).count(),
        "mfa_enrolled_identities": MFAEnrollment.objects.filter(is_enabled=True).values("identity").distinct().count(),
        "pending_access_reviews": AccessReview.objects.filter(status=AccessReviewStatus.PENDING).count(),
        "overdue_access_reviews": get_overdue_access_reviews().count(),
        "active_api_credentials": APICredential.objects.filter(is_active=True).exclude(
            Q(expires_at__isnull=False) & Q(expires_at__lte=now) | Q(is_compromised=True)
        ).count(),
        "compromised_credentials": APICredential.objects.filter(is_compromised=True).count(),
        "secure_files": SecureFile.objects.filter(is_active=True, is_deleted=False).count(),
        "encrypted_files": SecureFile.objects.filter(is_encrypted=True, is_active=True, is_deleted=False).count(),
    }


def get_identity_risk_score(identity: Identity) -> int:
    """Calculate a risk score for an identity based on security events."""
    score = 0
    last_30_days = timezone.now() - timezone.timedelta(days=30)

    # Failed login attempts
    failed_logins = get_failed_login_attempts(identity=identity, days=30).count()
    score += min(failed_logins * 2, 30)

    # Suspicious login attempts
    suspicious_logins = get_login_attempts(identity=identity, is_suspicious=True, days=30).count()
    score += min(suspicious_logins * 5, 25)

    # Failed MFA attempts
    failed_mfa = get_failed_mfa_attempts(identity=identity, days=30).count()
    score += min(failed_mfa * 3, 20)

    # Expired/old sessions
    old_sessions = Session.objects.filter(
        identity=identity,
        status__in=[SessionStatus.EXPIRED, SessionStatus.REVOKED, SessionStatus.TERMINATED],
        created_at__gte=last_30_days,
    ).count()
    score += min(old_sessions, 10)

    # Compromised credentials
    compromised = APICredential.objects.filter(
        identity=identity,
        is_compromised=True,
        compromised_at__gte=last_30_days,
    ).count()
    score += compromised * 15

    return min(score, 100)