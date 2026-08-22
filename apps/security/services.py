"""
Business services for the Security Hardening framework.

Every state-changing security operation flows through these services so
that audit history is recorded and invariants are enforced transactionally.
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import string
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.core.services import BaseService
from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role

from .constants import (
    SecurityConfidentialityLevel,
    SecurityStatus,
    MFAMethod,
    SessionStatus,
    AccessReviewStatus,
    AccessReviewDecision,
)
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

User = get_user_model()

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return f"sk_{secrets.token_urlsafe(32)}"


def generate_api_secret() -> str:
    """Generate a secure API secret."""
    return secrets.token_urlsafe(48)


def generate_session_key() -> str:
    """Generate a secure session key."""
    return secrets.token_urlsafe(48)


def generate_totp_secret() -> str:
    """Generate a TOTP secret (base32 encoded)."""
    import base64
    return base64.b32encode(secrets.token_bytes(20)).decode().strip("=")


def generate_backup_codes(count: int = 10, length: int = 8) -> list[str]:
    """Generate backup codes for MFA recovery."""
    alphabet = string.ascii_uppercase + string.digits
    codes = []
    for _ in range(count):
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        # Format as XXXX-XXXX
        formatted = "-".join([code[i:i+4] for i in range(0, len(code), 4)])
        codes.append(formatted)
    return codes


def hash_backup_code(code: str) -> str:
    """Hash a backup code for storage."""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_backup_code(code: str, hashed: str) -> bool:
    """Verify a backup code against its hash."""
    return hash_backup_code(code) == hashed


def record_identity_audit(
    identity: Identity,
    action: str,
    changed_by,
    from_data: dict | None = None,
    to_data: dict | None = None,
    notes: str = "",
) -> None:
    """Record an audit event for an identity."""
    from .models import IdentityAuditLog
    IdentityAuditLog.objects.create(
        identity=identity,
        action=action,
        changed_by=changed_by,
        from_data=from_data or {},
        to_data=to_data or {},
        notes=notes,
    )


class CreateSecurityPolicyService(BaseService):
    """Create an enterprise security policy."""

    def _execute(
        self,
        name: str,
        policy_type: str,
        description: str = "",
        rules: dict | None = None,
        enforcement_level: str = "enforce",
        scope: dict | None = None,
        exceptions: list | None = None,
        effective_date=None,
        expiry_date=None,
    ) -> EnterpriseSecurityPolicy:
        slug = slugify(name)
        if EnterpriseSecurityPolicy.objects.filter(slug=slug).exists():
            raise ValidationError(f"Security policy with slug '{slug}' already exists.")

        policy = EnterpriseSecurityPolicy.objects.create(
            name=name,
            slug=slug,
            description=description,
            policy_type=policy_type,
            rules=rules or {},
            enforcement_level=enforcement_level,
            scope=scope or {},
            exceptions=exceptions or [],
            effective_date=effective_date,
            expiry_date=expiry_date,
            created_by=self.user,
            updated_by=self.user,
        )
        logger.info(f"Created security policy {policy.slug} by {self.user}")
        return policy


class UpdateSecurityPolicyService(BaseService):
    """Update an enterprise security policy."""

    def _execute(
        self,
        policy: EnterpriseSecurityPolicy,
        name: str | None = None,
        description: str | None = None,
        rules: dict | None = None,
        enforcement_level: str | None = None,
        scope: dict | None = None,
        exceptions: list | None = None,
        effective_date=None,
        expiry_date=None,
        is_active: bool | None = None,
    ) -> EnterpriseSecurityPolicy:
        from_data = {
            "name": policy.name,
            "description": policy.description,
            "rules": policy.rules,
            "enforcement_level": policy.enforcement_level,
            "scope": policy.scope,
            "exceptions": policy.exceptions,
            "effective_date": policy.effective_date,
            "expiry_date": policy.expiry_date,
            "is_active": policy.is_active,
        }

        if name is not None:
            new_slug = slugify(name)
            if new_slug != policy.slug and EnterpriseSecurityPolicy.objects.filter(slug=new_slug).exists():
                raise ValidationError(f"Security policy with slug '{new_slug}' already exists.")
            policy.name = name
            policy.slug = new_slug

        if description is not None:
            policy.description = description
        if rules is not None:
            policy.rules = rules
        if enforcement_level is not None:
            policy.enforcement_level = enforcement_level
        if scope is not None:
            policy.scope = scope
        if exceptions is not None:
            policy.exceptions = exceptions
        if effective_date is not None:
            policy.effective_date = effective_date
        if expiry_date is not None:
            policy.expiry_date = expiry_date
        if is_active is not None:
            policy.is_active = is_active

        policy.updated_by = self.user
        policy.full_clean()
        policy.save()

        record_identity_audit(
            policy,
            "policy_updated",
            self.user,
            from_data=from_data,
            to_data={
                "name": policy.name,
                "description": policy.description,
                "rules": policy.rules,
                "enforcement_level": policy.enforcement_level,
                "scope": policy.scope,
                "exceptions": policy.exceptions,
                "effective_date": policy.effective_date,
                "expiry_date": policy.expiry_date,
                "is_active": policy.is_active,
            },
            notes="Security policy updated.",
        )
        logger.info(f"Updated security policy {policy.slug} by {self.user}")
        return policy


class CreateIdentityService(BaseService):
    """Create a core identity."""

    def _execute(
        self,
        identity_type: str,
        identifier: str,
        display_name: str,
        description: str = "",
        owner=None,
        managed_by: list[User] | None = None,
        status: str = SecurityStatus.ACTIVE,
        confidentiality: str = SecurityConfidentialityLevel.INTERNAL,
        expires_at=None,
        tags: list | None = None,
        attributes: dict | None = None,
    ) -> Identity:
        if Identity.objects.filter(identifier=identifier).exists():
            raise ValidationError(f"Identity with identifier '{identifier}' already exists.")

        identity = Identity.objects.create(
            identity_type=identity_type,
            identifier=identifier,
            display_name=display_name,
            description=description,
            owner=owner,
            status=status,
            confidentiality=confidentiality,
            expires_at=expires_at,
            tags=tags or [],
            attributes=attributes or {},
            created_by=self.user,
            updated_by=self.user,
        )
        if managed_by:
            identity.managed_by.set(managed_by)

        record_identity_audit(
            identity,
            "identity_created",
            self.user,
            to_data={
                "identity_type": identity.identity_type,
                "identifier": identity.identifier,
                "display_name": identity.display_name,
            },
            notes="Identity created.",
        )
        logger.info(f"Created identity {identity.identifier} by {self.user}")
        return identity


class CreateServiceIdentityService(BaseService):
    """Create a service account identity."""

    def _execute(
        self,
        identifier: str,
        display_name: str,
        service_type: str,
        description: str = "",
        owner=None,
        managed_by: list[User] | None = None,
        service_account_token: str = "",
        token_expires_at=None,
        ip_allowlist: list | None = None,
        allowed_operations: list | None = None,
        status: str = SecurityStatus.ACTIVE,
        confidentiality: str = SecurityConfidentialityLevel.RESTRICTED,
        expires_at=None,
        tags: list | None = None,
        attributes: dict | None = None,
    ) -> ServiceIdentity:
        if ServiceIdentity.objects.filter(identifier=identifier).exists():
            raise ValidationError(f"Service identity with identifier '{identifier}' already exists.")

        identity = ServiceIdentity.objects.create(
            identity_type="service",
            identifier=identifier,
            display_name=display_name,
            description=description,
            owner=owner,
            status=status,
            confidentiality=confidentiality,
            expires_at=expires_at,
            tags=tags or [],
            attributes=attributes or {},
            service_type=service_type,
            service_account_token=service_account_token,
            token_expires_at=token_expires_at,
            ip_allowlist=ip_allowlist or [],
            allowed_operations=allowed_operations or [],
            created_by=self.user,
            updated_by=self.user,
        )
        if managed_by:
            identity.managed_by.set(managed_by)

        record_identity_audit(
            identity,
            "service_identity_created",
            self.user,
            to_data={
                "identifier": identity.identifier,
                "display_name": identity.display_name,
                "service_type": identity.service_type,
            },
            notes="Service identity created.",
        )
        logger.info(f"Created service identity {identity.identifier} by {self.user}")
        return identity


class CreateOrganizationalIdentityService(BaseService):
    """Create an organizational identity."""

    def _execute(
        self,
        identifier: str,
        display_name: str,
        org_identity_type: str,
        description: str = "",
        owner=None,
        managed_by: list[User] | None = None,
        parent_organization: OrganizationUnit | None = None,
        organization_unit: OrganizationUnit | None = None,
        contact_person: User | None = None,
        status: str = SecurityStatus.ACTIVE,
        confidentiality: str = SecurityConfidentialityLevel.INTERNAL,
        expires_at=None,
        tags: list | None = None,
        attributes: dict | None = None,
    ) -> OrganizationalIdentity:
        if OrganizationalIdentity.objects.filter(identifier=identifier).exists():
            raise ValidationError(f"Organizational identity with identifier '{identifier}' already exists.")

        identity = OrganizationalIdentity.objects.create(
            identity_type="organization",
            identifier=identifier,
            display_name=display_name,
            description=description,
            owner=owner,
            status=status,
            confidentiality=confidentiality,
            expires_at=expires_at,
            tags=tags or [],
            attributes=attributes or {},
            org_identity_type=org_identity_type,
            parent_organization=parent_organization,
            organization_unit=organization_unit,
            contact_person=contact_person,
            created_by=self.user,
            updated_by=self.user,
        )
        if managed_by:
            identity.managed_by.set(managed_by)

        record_identity_audit(
            identity,
            "organizational_identity_created",
            self.user,
            to_data={
                "identifier": identity.identifier,
                "display_name": identity.display_name,
                "org_identity_type": identity.org_identity_type,
            },
            notes="Organizational identity created.",
        )
        logger.info(f"Created organizational identity {identity.identifier} by {self.user}")
        return identity


class UpdateIdentityService(BaseService):
    """Update an identity."""

    def _execute(
        self,
        identity: Identity,
        display_name: str | None = None,
        description: str | None = None,
        owner=None,
        managed_by: list[User] | None = None,
        status: str | None = None,
        confidentiality: str | None = None,
        expires_at=None,
        tags: list | None = None,
        attributes: dict | None = None,
    ) -> Identity:
        from_data = {
            "display_name": identity.display_name,
            "description": identity.description,
            "owner_id": identity.owner_id,
            "status": identity.status,
            "confidentiality": identity.confidentiality,
            "expires_at": identity.expires_at,
            "tags": identity.tags,
            "attributes": identity.attributes,
        }

        if display_name is not None:
            identity.display_name = display_name
        if description is not None:
            identity.description = description
        if owner is not None:
            identity.owner = owner
        if managed_by is not None:
            identity.managed_by.set(managed_by)
        if status is not None:
            identity.status = status
        if confidentiality is not None:
            identity.confidentiality = confidentiality
        if expires_at is not None:
            identity.expires_at = expires_at
        if tags is not None:
            identity.tags = tags
        if attributes is not None:
            identity.attributes = attributes

        identity.updated_by = self.user
        identity.full_clean()
        identity.save()

        record_identity_audit(
            identity,
            "identity_updated",
            self.user,
            from_data=from_data,
            to_data={
                "display_name": identity.display_name,
                "description": identity.description,
                "owner_id": identity.owner_id,
                "status": identity.status,
                "confidentiality": identity.confidentiality,
                "expires_at": identity.expires_at,
                "tags": identity.tags,
                "attributes": identity.attributes,
            },
            notes="Identity updated.",
        )
        logger.info(f"Updated identity {identity.identifier} by {self.user}")
        return identity


class CreatePermissionService(BaseService):
    """Create a granular permission."""

    def _execute(
        self,
        name: str,
        module: str,
        resource_type: str,
        action: str,
        description: str = "",
        is_system: bool = False,
        is_assignable: bool = True,
        requires_approval: bool = False,
        conditions: dict | None = None,
    ) -> Permission:
        slug = slugify(f"{module}-{resource_type}-{action}")
        if Permission.objects.filter(slug=slug).exists():
            raise ValidationError(f"Permission with slug '{slug}' already exists.")

        permission = Permission.objects.create(
            name=name,
            slug=slug,
            description=description,
            module=module,
            resource_type=resource_type,
            action=action,
            is_system=is_system,
            is_assignable=is_assignable,
            requires_approval=requires_approval,
            conditions=conditions or {},
        )
        logger.info(f"Created permission {permission.slug} by {self.user}")
        return permission


class GrantRolePermissionService(BaseService):
    """Grant a permission to a role."""

    def _execute(
        self,
        role: Role,
        permission: Permission,
        granted_by=None,
        expires_at=None,
        conditions: dict | None = None,
        justification: str = "",
    ) -> RolePermission:
        if RolePermission.objects.filter(role=role, permission=permission).exists():
            raise ValidationError(f"Role already has this permission.")

        role_permission = RolePermission.objects.create(
            role=role,
            permission=permission,
            granted_by=granted_by or self.user,
            expires_at=expires_at,
            conditions=conditions or {},
            justification=justification,
        )
        # Sync to Django Group
        if role.group:
            role.group.permissions.add(permission)

        logger.info(f"Granted permission {permission.name} to role {role.name} by {self.user}")
        return role_permission


class RevokeRolePermissionService(BaseService):
    """Revoke a permission from a role."""

    def _execute(
        self,
        role: Role,
        permission: Permission,
    ) -> None:
        RolePermission.objects.filter(role=role, permission=permission).delete()
        # Sync to Django Group
        if role.group:
            role.group.permissions.remove(permission)
        logger.info(f"Revoked permission {permission.name} from role {role.name} by {self.user}")


class AssignIdentityRoleService(BaseService):
    """Assign a role to an identity."""

    def _execute(
        self,
        identity: Identity,
        role: Role,
        assigned_by=None,
        expires_at=None,
        conditions: dict | None = None,
        justification: str = "",
    ) -> IdentityRole:
        if IdentityRole.objects.filter(identity=identity, role=role).exists():
            raise ValidationError(f"Identity already has this role.")

        identity_role = IdentityRole.objects.create(
            identity=identity,
            role=role,
            assigned_by=assigned_by or self.user,
            expires_at=expires_at,
            conditions=conditions or {},
            justification=justification,
        )

        record_identity_audit(
            identity,
            "role_assigned",
            self.user,
            to_data={
                "role": role.name,
                "expires_at": expires_at,
            },
            notes=f"Role {role.name} assigned to {identity.display_name}.",
        )
        logger.info(f"Assigned role {role.name} to identity {identity.identifier} by {self.user}")
        return identity_role


class RevokeIdentityRoleService(BaseService):
    """Revoke a role from an identity."""

    def _execute(
        self,
        identity: Identity,
        role: Role,
    ) -> None:
        IdentityRole.objects.filter(identity=identity, role=role).delete()

        record_identity_audit(
            identity,
            "role_revoked",
            self.user,
            from_data={"role": role.name},
            notes=f"Role {role.name} revoked from {identity.display_name}.",
        )
        logger.info(f"Revoked role {role.name} from identity {identity.identifier} by {self.user}")


class GrantPermissionService(BaseService):
    """Grant a direct permission to an identity."""

    def _execute(
        self,
        identity: Identity,
        permission: Permission,
        granted_by=None,
        expires_at=None,
        conditions: dict | None = None,
        justification: str = "",
    ) -> PermissionGrant:
        if PermissionGrant.objects.filter(identity=identity, permission=permission).exists():
            raise ValidationError(f"Identity already has this permission.")

        grant = PermissionGrant.objects.create(
            identity=identity,
            permission=permission,
            granted_by=granted_by or self.user,
            expires_at=expires_at,
            conditions=conditions or {},
            justification=justification,
        )

        record_identity_audit(
            identity,
            "permission_granted",
            self.user,
            to_data={
                "permission": permission.name,
                "expires_at": expires_at,
            },
            notes=f"Permission {permission.name} granted to {identity.display_name}.",
        )
        logger.info(f"Granted permission {permission.name} to identity {identity.identifier} by {self.user}")
        return grant


class RevokePermissionService(BaseService):
    """Revoke a direct permission from an identity."""

    def _execute(
        self,
        identity: Identity,
        permission: Permission,
    ) -> None:
        PermissionGrant.objects.filter(identity=identity, permission=permission).delete()

        record_identity_audit(
            identity,
            "permission_revoked",
            self.user,
            from_data={"permission": permission.name},
            notes=f"Permission {permission.name} revoked from {identity.display_name}.",
        )
        logger.info(f"Revoked permission {permission.name} from identity {identity.identifier} by {self.user}")


class CreateRoleHierarchyService(BaseService):
    """Create a role hierarchy relationship."""

    def _execute(
        self,
        parent_role: Role,
        child_role: Role,
        inherit_permissions: bool = True,
        inherit_role_permissions: bool = True,
        justification: str = "",
    ) -> RoleHierarchy:
        if parent_role == child_role:
            raise ValidationError("A role cannot be parent of itself.")

        if RoleHierarchy.objects.filter(parent_role=parent_role, child_role=child_role).exists():
            raise ValidationError("This hierarchy relationship already exists.")

        hierarchy = RoleHierarchy.objects.create(
            parent_role=parent_role,
            child_role=child_role,
            inherit_permissions=inherit_permissions,
            inherit_role_permissions=inherit_role_permissions,
            justification=justification,
            created_by=self.user,
        )
        logger.info(f"Created role hierarchy {parent_role.name} -> {child_role.name} by {self.user}")
        return hierarchy


class RemoveRoleHierarchyService(BaseService):
    """Remove a role hierarchy relationship."""

    def _execute(
        self,
        parent_role: Role,
        child_role: Role,
    ) -> None:
        RoleHierarchy.objects.filter(parent_role=parent_role, child_role=child_role).delete()
        logger.info(f"Removed role hierarchy {parent_role.name} -> {child_role.name} by {self.user}")


class RecordLoginAttemptService(BaseService):
    """Record a login attempt for security monitoring."""

    def _execute(
        self,
        username_attempted: str,
        ip_address: str,
        outcome: str,
        identity: Identity | None = None,
        user_agent: str = "",
        failure_reason: str = "",
        risk_score: int = 0,
        is_suspicious: bool = False,
        country_code: str = "",
        city: str = "",
    ) -> LoginAttempt:
        attempt = LoginAttempt.objects.create(
            identity=identity,
            username_attempted=username_attempted,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            failure_reason=failure_reason,
            risk_score=risk_score,
            is_suspicious=is_suspicious,
            country_code=country_code,
            city=city,
        )
        logger.info(f"Recorded login attempt: {username_attempted} from {ip_address} ({outcome})")
        return attempt


class CreateAccessReviewService(BaseService):
    """Create an access review campaign."""

    def _execute(
        self,
        name: str,
        review_type: str,
        started_at,
        due_date,
        description: str = "",
        target_identity: Identity | None = None,
        target_role: Role | None = None,
        target_permission: Permission | None = None,
        auto_approve_low_risk: bool = False,
        require_justification_for_changes: bool = True,
        escalate_overdue_reviews: bool = True,
        reviewers: list[User] | None = None,
        lead_reviewer: User | None = None,
    ) -> AccessReview:
        if due_date <= started_at:
            raise ValidationError("Due date must be after start date.")

        review = AccessReview.objects.create(
            name=name,
            description=description,
            review_type=review_type,
            target_identity=target_identity,
            target_role=target_role,
            target_permission=target_permission,
            started_at=started_at,
            due_date=due_date,
            auto_approve_low_risk=auto_approve_low_risk,
            require_justification_for_changes=require_justification_for_changes,
            escalate_overdue_reviews=escalate_overdue_reviews,
            lead_reviewer=lead_reviewer,
            created_by=self.user,
        )
        if reviewers:
            review.reviewers.set(reviewers)

        logger.info(f"Created access review {review.name} by {self.user}")
        return review


class StartAccessReviewService(BaseService):
    """Start an access review (populate items)."""

    def _execute(
        self,
        review: AccessReview,
    ) -> AccessReview:
        from .selectors import (
            get_active_identity_roles,
            get_active_permission_grants,
            get_active_role_assignments,
        )

        if review.status != AccessReviewStatus.PENDING:
            raise ValidationError("Review is not in pending status.")

        review.status = AccessReviewStatus.IN_PROGRESS
        review.save(update_fields=["status", "updated_at"])

        items_to_create = []

        if review.review_type == "role" and review.target_role:
            assignments = get_active_role_assignments(review.target_role)
            for assignment in assignments:
                items_to_create.append(AccessReviewItem(
                    access_review=review,
                    identity=assignment.identity,
                    role=review.target_role,
                    identity_role=assignment,
                    risk_level="low",
                ))

        elif review.review_type == "permission" and review.target_permission:
            grants = get_active_permission_grants(review.target_permission)
            for grant in grants:
                items_to_create.append(AccessReviewItem(
                    access_review=review,
                    identity=grant.identity,
                    permission=review.target_permission,
                    risk_level="medium",
                ))

        elif review.review_type == "identity" and review.target_identity:
            roles = get_active_identity_roles(review.target_identity)
            for role in roles:
                items_to_create.append(AccessReviewItem(
                    access_review=review,
                    identity=review.target_identity,
                    role=role.role,
                    identity_role=role,
                    risk_level="low",
                ))
            grants = get_active_permission_grants(review.target_identity)
            for grant in grants:
                items_to_create.append(AccessReviewItem(
                    access_review=review,
                    identity=review.target_identity,
                    permission=grant.permission,
                    risk_level="medium",
                ))

        if items_to_create:
            AccessReviewItem.objects.bulk_create(items_to_create)
            review.total_items_reviewed = len(items_to_create)
            review.save(update_fields=["total_items_reviewed", "updated_at"])

        logger.info(f"Started access review {review.name} with {len(items_to_create)} items by {self.user}")
        return review


class ReviewAccessItemService(BaseService):
    """Record a decision on an access review item."""

    def _execute(
        self,
        item: AccessReviewItem,
        decision: str,
        reviewer: User,
        justification: str = "",
        new_value: dict | None = None,
        change_reason: str = "",
    ) -> AccessReviewItem:
        if item.decision:
            raise ValidationError("Item has already been reviewed.")

        if decision not in dict(AccessReviewDecision.CHOICES):
            raise ValidationError("Invalid decision.")

        item.reviewer = reviewer
        item.reviewed_at = timezone.now()
        item.decision = decision
        item.justification = justification
        item.new_value = new_value
        item.change_reason = change_reason
        item.save()

        # Update review counters
        review = item.access_review
        if decision == AccessReviewDecision.APPROVE:
            review.items_approved += 1
        elif decision == AccessReviewDecision.REVOKE:
            review.items_revoked += 1
        elif decision == AccessReviewDecision.MODIFY:
            review.items_modified += 1
        elif decision == AccessReviewDecision.ESCALATE:
            review.items_escalated += 1
        review.save(update_fields=["items_approved", "items_revoked", "items_modified", "items_escalated", "updated_at"])

        logger.info(f"Reviewed item {item.id} with decision {decision} by {reviewer}")
        return item


class CompleteAccessReviewService(BaseService):
    """Complete an access review."""

    def _execute(
        self,
        review: AccessReview,
    ) -> AccessReview:
        if review.status not in [AccessReviewStatus.PENDING, AccessReviewStatus.IN_PROGRESS]:
            raise ValidationError("Review cannot be completed.")

        review.status = AccessReviewStatus.COMPLETED
        review.completed_at = timezone.now()
        review.save(update_fields=["status", "completed_at", "updated_at"])
        logger.info(f"Completed access review {review.name} by {self.user}")
        return review


class CreateSessionService(BaseService):
    """Create a new session."""

    def _execute(
        self,
        identity: Identity,
        ip_address: str,
        user_agent: str = "",
        idle_timeout_minutes: int = 30,
        absolute_timeout_minutes: int = 480,
        is_secure: bool = False,
        is_mfa_used: bool = False,
        mfa_method: str = "",
        device_fingerprint: str = "",
    ) -> Session:
        session_key = generate_session_key()
        now = timezone.now()
        expires_at = now + timedelta(minutes=absolute_timeout_minutes)

        session = Session.objects.create(
            identity=identity,
            session_key=session_key,
            ip_address=ip_address,
            user_agent=user_agent,
            status=SessionStatus.ACTIVE,
            expires_at=expires_at,
            idle_timeout_minutes=idle_timeout_minutes,
            absolute_timeout_minutes=absolute_timeout_minutes,
            is_secure=is_secure,
            is_mfa_used=is_mfa_used,
            mfa_method=mfa_method,
            device_fingerprint=device_fingerprint,
        )
        logger.info(f"Created session for identity {identity.identifier}")
        return session


class TerminateSessionService(BaseService):
    """Terminate a session."""

    def _execute(
        self,
        session: Session,
        terminated_by=None,
        terminated_by_ip: str | None = None,
    ) -> Session:
        session.terminate(terminated_by=terminated_by, terminated_by_ip=terminated_by_ip)
        logger.info(f"Terminated session {session.session_key[:8]}... by {self.user}")
        return session


class ExtendSessionService(BaseService):
    """Extend a session's expiration."""

    def _execute(
        self,
        session: Session,
        extension_minutes: int,
    ) -> Session:
        session.extend(extension_minutes)
        logger.info(f"Extended session {session.session_key[:8]}... by {extension_minutes} minutes")
        return session


class CreateMFAEnrollmentService(BaseService):
    """Create an MFA enrollment."""

    def _execute(
        self,
        identity: Identity,
        method: str,
        is_primary: bool = False,
        is_backup: bool = False,
        enrolled_by=None,
        secret_key: str = "",
        phone_number: str = "",
        email_address: str = "",
        name: str = "",
        attributes: dict | None = None,
    ) -> MFAEnrollment:
        # Validate method-specific requirements
        if method == MFAMethod.TOTP and not secret_key:
            secret_key = generate_totp_secret()
        if method == MFAMethod.SMS and not phone_number:
            raise ValidationError("SMS requires a phone number.")
        if method == MFAMethod.EMAIL and not email_address:
            raise ValidationError("Email requires an email address.")

        # If this is primary, unset other primary enrollments
        if is_primary:
            MFAEnrollment.objects.filter(identity=identity, is_primary=True).update(is_primary=False)

        enrollment = MFAEnrollment.objects.create(
            identity=identity,
            method=method,
            is_primary=is_primary,
            is_backup=is_backup,
            enrolled_by=enrolled_by or self.user,
            secret_key=secret_key,
            phone_number=phone_number,
            email_address=email_address,
            name=name,
            attributes=attributes or {},
        )

        # Generate backup codes for TOTP
        if method == MFAMethod.TOTP and not enrollment.backup_codes:
            enrollment.backup_codes = [hash_backup_code(code) for code in generate_backup_codes()]
            enrollment.save(update_fields=["backup_codes", "updated_at"])

        logger.info(f"Created MFA enrollment {method} for identity {identity.identifier}")
        return enrollment


class VerifyMFAService(BaseService):
    """Verify an MFA challenge."""

    def _execute(
        self,
        enrollment: MFAEnrollment,
        response: str,
        ip_address: str,
        user_agent: str = "",
        challenge: str = "",
        backup_code_used: bool = False,
        trusted_device: bool = False,
    ) -> MFAVerificationAttempt:
        outcome = MFAVerificationAttempt.FAILED_INVALID_CODE
        is_valid = False

        if enrollment.method == MFAMethod.TOTP:
            import pyotp
            totp = pyotp.TOTP(enrollment.secret_key)
            if totp.verify(response, valid_window=1):
                is_valid = True
                outcome = MFAVerificationAttempt.SUCCESS
            elif backup_code_used and response in enrollment.backup_codes:
                # Check if backup code is valid and not used
                hashed = hash_backup_code(response)
                if hashed in enrollment.backup_codes_used:
                    outcome = MFAVerificationAttempt.FAILED_EXPIRED_CODE
                else:
                    is_valid = True
                    outcome = MFAVerificationAttempt.SUCCESS
                    enrollment.backup_codes_used.append(hashed)
                    enrollment.save(update_fields=["backup_codes_used", "updated_at"])
            else:
                outcome = MFAVerificationAttempt.FAILED_INVALID_CODE

        elif enrollment.method == MFAMethod.EMAIL:
            # In production, verify against sent code
            # For now, placeholder logic
            is_valid = True
            outcome = MFAVerificationAttempt.SUCCESS

        elif enrollment.method == MFAMethod.SMS:
            # In production, verify against sent code
            is_valid = True
            outcome = MFAVerificationAttempt.SUCCESS

        elif enrollment.method == MFAMethod.RECOVERY_CODES:
            hashed = hash_backup_code(response)
            if hashed in enrollment.backup_codes_used:
                outcome = MFAVerificationAttempt.FAILED_EXPIRED_CODE
            elif hashed in enrollment.backup_codes:
                is_valid = True
                outcome = MFAVerificationAttempt.SUCCESS
                enrollment.backup_codes_used.append(hashed)
                enrollment.save(update_fields=["backup_codes_used", "updated_at"])
            else:
                outcome = MFAVerificationAttempt.FAILED_INVALID_CODE

        attempt = MFAVerificationAttempt.objects.create(
            identity=enrollment.identity,
            enrollment=enrollment,
            challenge=challenge,
            response=response,
            ip_address=ip_address,
            user_agent=user_agent,
            outcome=outcome,
            expires_at=timezone.now() + timedelta(minutes=5),
            trusted_device=trusted_device,
            backup_code_used=backup_code_used,
        )

        if is_valid:
            enrollment.record_successful_attempt()
        else:
            enrollment.record_failed_attempt()
            attempt.mark_as_suspicious("Invalid MFA code")

        logger.info(f"MFA verification attempt for {enrollment.identity.identifier}: {outcome}")
        return attempt


class CreateAPICredentialService(BaseService):
    """Create an API credential."""

    def _execute(
        self,
        identity: Identity,
        name: str,
        credential_type: str,
        service_name: str,
        description: str = "",
        credential_key: str | None = None,
        credential_secret: str = "",
        service_url: str = "",
        ip_allowlist: list | None = None,
        allowed_endpoints: list | None = None,
        allowed_methods: list | None = None,
        rate_limit_per_hour: int = 1000,
        rate_limit_per_day: int = 10000,
        expires_at=None,
    ) -> APICredential:
        slug = slugify(name)
        if APICredential.objects.filter(slug=slug).exists():
            raise ValidationError(f"API credential with slug '{slug}' already exists.")

        if credential_key is None:
            credential_key = generate_api_key()

        credential = APICredential.objects.create(
            name=name,
            slug=slug,
            description=description,
            identity=identity,
            credential_type=credential_type,
            credential_key=credential_key,
            credential_secret=credential_secret,
            service_name=service_name,
            service_url=service_url,
            ip_allowlist=ip_allowlist or [],
            allowed_endpoints=allowed_endpoints or [],
            allowed_methods=allowed_methods or [],
            rate_limit_per_hour=rate_limit_per_hour,
            rate_limit_per_day=rate_limit_per_day,
            expires_at=expires_at,
            created_by=self.user,
        )
        logger.info(f"Created API credential {credential.name} for identity {identity.identifier}")
        return credential


class RotateAPICredentialService(BaseService):
    """Rotate an API credential."""

    def _execute(
        self,
        credential: APICredential,
        new_key: str | None = None,
        new_secret: str = "",
    ) -> APICredential:
        if new_key is None:
            new_key = generate_api_key()

        credential.rotate_credential(new_key, new_secret)
        logger.info(f"Rotated API credential {credential.name} by {self.user}")
        return credential


class RevokeAPICredentialService(BaseService):
    """Revoke (deactivate) an API credential."""

    def _execute(
        self,
        credential: APICredential,
        reason: str = "",
    ) -> APICredential:
        credential.is_active = False
        if reason:
            credential.mark_compromised(reason)
        else:
            credential.save(update_fields=["is_active", "updated_at"])
        logger.info(f"Revoked API credential {credential.name} by {self.user}")
        return credential


class CreateAPIAccessTokenService(BaseService):
    """Create an API access token."""

    def _execute(
        self,
        credential: APICredential,
        token: str | None = None,
        token_type: str = "Bearer",
        identity: Identity | None = None,
        scopes: list | None = None,
        permissions: list | None = None,
        expires_at=None,
        not_before=None,
    ) -> APIAccessToken:
        if token is None:
            token = secrets.token_urlsafe(48)

        access_token = APIAccessToken.objects.create(
            credential=credential,
            token=token,
            token_type=token_type,
            identity=identity,
            scopes=scopes or [],
            permissions=permissions or [],
            expires_at=expires_at or (timezone.now() + timedelta(hours=1)),
            not_before=not_before,
        )
        logger.info(f"Created API access token for credential {credential.name}")
        return access_token


class RevokeAPIAccessTokenService(BaseService):
    """Revoke an API access token."""

    def _execute(
        self,
        token: APIAccessToken,
        reason: str = "",
    ) -> APIAccessToken:
        token.revoke(reason)
        logger.info(f"Revoked API access token for credential {token.credential.name}")
        return token


class RecordAPIRateLimitService(BaseService):
    """Record API rate limit usage."""

    def _execute(
        self,
        credential: APICredential,
        window_start,
        window_end,
        endpoint: str = "",
        method: str = "",
        identity: Identity | None = None,
        ip_address: str | None = None,
        request_count: int = 1,
        blocked_count: int = 0,
        status_code: int | None = None,
    ) -> APIRateLimit:
        rate_limit, created = APIRateLimit.objects.get_or_create(
            credential=credential,
            window_start=window_start,
            endpoint=endpoint,
            method=method,
            defaults={
                "identity": identity,
                "window_end": window_end,
                "ip_address": ip_address,
                "request_count": request_count,
                "blocked_count": blocked_count,
                "status_code": status_code,
            },
        )
        if not created:
            rate_limit.increment(request_count)
            if blocked_count:
                rate_limit.block_request(blocked_count)
        return rate_limit


class CreateDatabaseSecurityPolicyService(BaseService):
    """Create a database security policy."""

    def _execute(
        self,
        name: str,
        database_identifier: str,
        database_type: str,
        host: str = "",
        port: int | None = None,
        database_name: str = "",
        require_ssl: bool = True,
        auth_method: str = "password",
        statement_timeout_ms: int = 30000,
        lock_timeout_ms: int = 1000,
        audit_connections: bool = True,
        audit_statements: bool = False,
        audit_statement_level: str = "none",
        encryption_at_rest: bool = False,
        allowed_networks: list | None = None,
    ) -> DatabaseSecurityPolicy:
        slug = slugify(name)
        if DatabaseSecurityPolicy.objects.filter(slug=slug).exists():
            raise ValidationError(f"Database security policy with slug '{slug}' already exists.")

        policy = DatabaseSecurityPolicy.objects.create(
            name=name,
            slug=slug,
            database_identifier=database_identifier,
            database_type=database_type,
            host=host,
            port=port,
            database_name=database_name,
            require_ssl=require_ssl,
            auth_method=auth_method,
            statement_timeout_ms=statement_timeout_ms,
            lock_timeout_ms=lock_timeout_ms,
            audit_connections=audit_connections,
            audit_statements=audit_statements,
            audit_statement_level=audit_statement_level,
            encryption_at_rest=encryption_at_rest,
            allowed_networks=allowed_networks or [],
            created_by=self.user,
        )
        logger.info(f"Created database security policy {policy.name} by {self.user}")
        return policy


class RecordDatabaseAccessService(BaseService):
    """Record a database access event."""

    def _execute(
        self,
        database_policy: DatabaseSecurityPolicy,
        session_id: str,
        username: str,
        client_ip: str,
        connection_status: str = "started",
        client_hostname: str = "",
        statement_type: str = "",
        statement: str = "",
        statement_duration_ms: int | None = None,
        rows_affected: int | None = None,
        success: bool = True,
        error_message: str = "",
        error_code: str = "",
    ) -> DatabaseAccessLog:
        log = DatabaseAccessLog.objects.create(
            database_policy=database_policy,
            session_id=session_id,
            username=username,
            client_ip=client_ip,
            client_hostname=client_hostname,
            connection_started=timezone.now(),
            connection_status=connection_status,
            statement_type=statement_type,
            statement=statement,
            statement_duration_ms=statement_duration_ms,
            rows_affected=rows_affected,
            success=success,
            error_message=error_message,
            error_code=error_code,
        )
        return log


class CreateSecureFileService(BaseService):
    """Create a secure file record."""

    def _execute(
        self,
        filename: str,
        original_filename: str,
        file_size: int,
        content_type: str,
        storage_path: str,
        owner: Identity,
        uploaded_by: Identity,
        storage_bucket: str = "",
        storage_region: str = "",
        is_public: bool = False,
        allowed_identities: list[Identity] | None = None,
        allowed_roles: list[Role] | None = None,
        confidentiality: str = SecurityConfidentialityLevel.INTERNAL,
        checksum_value: str = "",
        checksum_algorithm: str = "sha256",
        is_encrypted: bool = False,
        encryption_algorithm: str = "",
        encryption_key_identifier: str = "",
        retention_date=None,
        retention_policy: str = "",
    ) -> SecureFile:
        secure_file = SecureFile.objects.create(
            filename=filename,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            storage_path=storage_path,
            storage_bucket=storage_bucket,
            storage_region=storage_region,
            owner=owner,
            uploaded_by=uploaded_by,
            is_public=is_public,
            confidentiality=confidentiality,
            checksum_algorithm=checksum_algorithm,
            checksum_value=checksum_value,
            is_encrypted=is_encrypted,
            encryption_algorithm=encryption_algorithm,
            encryption_key_identifier=encryption_key_identifier,
            retention_date=retention_date,
            retention_policy=retention_policy,
            created_by=self.user,
            updated_by=self.user,
        )
        if allowed_identities:
            secure_file.allowed_identities.set(allowed_identities)
        if allowed_roles:
            secure_file.allowed_roles.set(allowed_roles)

        logger.info(f"Created secure file {secure_file.filename} by {self.user}")
        return secure_file


class ScanFileForVirusService(BaseService):
    """Scan a secure file for viruses/malware."""

    def _execute(
        self,
        secure_file: SecureFile,
        scan_result: str,
        details: str = "",
    ) -> SecureFile:
        """
        Update virus scan status.
        scan_result should be one of: clean, infected, quarantined, scan_failed
        """
        secure_file.virus_scan_status = scan_result
        secure_file.virus_scan_at = timezone.now()
        secure_file.virus_scan_details = details
        secure_file.save(update_fields=["virus_scan_status", "virus_scan_at", "virus_scan_details", "updated_at"])

        if scan_result == "infected":
            logger.warning(f"Virus detected in file {secure_file.filename}: {details}")
        else:
            logger.info(f"Virus scan completed for file {secure_file.filename}: {scan_result}")

        return secure_file


class EncryptFileService(BaseService):
    """Mark a file as encrypted."""

    def _execute(
        self,
        secure_file: SecureFile,
        encryption_algorithm: str,
        encryption_key_identifier: str,
    ) -> SecureFile:
        secure_file.is_encrypted = True
        secure_file.encryption_algorithm = encryption_algorithm
        secure_file.encryption_key_identifier = encryption_key_identifier
        secure_file.save(update_fields=["is_encrypted", "encryption_algorithm", "encryption_key_identifier", "updated_at"])
        logger.info(f"Marked file {secure_file.filename} as encrypted")
        return secure_file


class CreateFileVersionService(BaseService):
    """Create a new version of a secure file."""

    def _execute(
        self,
        secure_file: SecureFile,
        new_filename: str,
        new_file_size: int,
        new_content_type: str,
        new_storage_path: str,
        new_checksum: str,
        uploaded_by: Identity,
        previous_checksum: str = "",
    ) -> SecureFile:
        # Mark old version as not latest
        secure_file.is_latest_version = False
        secure_file.save(update_fields=["is_latest_version", "updated_at"])

        # Create new version
        new_version = SecureFile.objects.create(
            filename=new_filename,
            original_filename=secure_file.original_filename,
            file_size=new_file_size,
            content_type=new_content_type,
            storage_path=new_storage_path,
            storage_bucket=secure_file.storage_bucket,
            storage_region=secure_file.storage_region,
            owner=secure_file.owner,
            uploaded_by=uploaded_by,
            is_public=secure_file.is_public,
            confidentiality=secure_file.confidentiality,
            checksum_algorithm=secure_file.checksum_algorithm,
            checksum_value=new_checksum,
            previous_checksum=previous_checksum or secure_file.checksum_value,
            is_encrypted=secure_file.is_encrypted,
            encryption_algorithm=secure_file.encryption_algorithm,
            encryption_key_identifier=secure_file.encryption_key_identifier,
            retention_date=secure_file.retention_date,
            retention_policy=secure_file.retention_policy,
            version=secure_file.version + 1,
            is_latest_version=True,
            created_by=self.user,
            updated_by=self.user,
        )

        # Copy access controls
        new_version.allowed_identities.set(secure_file.allowed_identities.all())
        new_version.allowed_roles.set(secure_file.allowed_roles.all())

        # Link old version to new
        secure_file.replaced_by = new_version
        secure_file.save(update_fields=["replaced_by", "updated_at"])

        logger.info(f"Created new version {new_version.version} of file {secure_file.filename}")
        return new_version