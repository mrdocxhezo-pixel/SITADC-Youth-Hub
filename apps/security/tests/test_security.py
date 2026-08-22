"""
Tests for the Security Hardening framework.
"""

from __future__ import annotations

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.organizations.models import OrganizationUnit
from apps.rbac.models import Role
from apps.security.models import (
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
from apps.security.constants import (
    SecurityConfidentialityLevel,
    SecurityStatus,
    MFAMethod,
    SessionStatus,
    AccessReviewStatus,
    AccessReviewDecision,
)

User = get_user_model()


class SecurityModelTestCase(TestCase):
    """Base test case with common setup."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            first_name="Other",
            last_name="User",
        )
        self.org_unit = OrganizationUnit.objects.create(
            name="Test Unit",
            code="TEST",
            description="Test organizational unit",
        )
        self.role = Role.objects.create(
            name="Test Role",
            slug="test-role",
            description="A test role",
            priority=100,
            created_by=self.user,
            updated_by=self.user,
        )
        self.other_role = Role.objects.create(
            name="Other Role",
            slug="other-role",
            description="Another test role",
            priority=200,
            created_by=self.user,
            updated_by=self.user,
        )


class EnterpriseSecurityPolicyTests(SecurityModelTestCase):
    """Tests for EnterpriseSecurityPolicy model."""

    def test_create_policy(self):
        policy = EnterpriseSecurityPolicy.objects.create(
            name="Password Policy",
            policy_type="password",
            description="Test password policy",
            rules={"min_length": 8, "require_uppercase": True},
            enforcement_level="enforce",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(policy.name, "Password Policy")
        self.assertEqual(policy.policy_type, "password")
        self.assertTrue(policy.is_active)

    def test_password_policy_validation(self):
        policy = EnterpriseSecurityPolicy(
            name="Invalid Password Policy",
            policy_type="password",
            rules={"min_length": "invalid"},
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(Exception):
            policy.full_clean()

    def test_session_policy_validation(self):
        policy = EnterpriseSecurityPolicy(
            name="Invalid Session Policy",
            policy_type="session",
            rules={"idle_timeout_minutes": -1},
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(Exception):
            policy.full_clean()

    def test_get_password_policy_rules(self):
        policy = EnterpriseSecurityPolicy.objects.create(
            name="Password Policy",
            policy_type="password",
            rules={"min_length": 12, "history_size": 10},
            created_by=self.user,
            updated_by=self.user,
        )
        rules = policy.get_password_policy_rules()
        self.assertEqual(rules["min_length"], 12)
        self.assertEqual(rules["history_size"], 10)
        # Check defaults are applied
        self.assertEqual(rules["require_uppercase"], True)

    def test_get_session_policy_rules(self):
        policy = EnterpriseSecurityPolicy.objects.create(
            name="Session Policy",
            policy_type="session",
            rules={"idle_timeout_minutes": 60},
            created_by=self.user,
            updated_by=self.user,
        )
        rules = policy.get_session_policy_rules()
        self.assertEqual(rules["idle_timeout_minutes"], 60)
        self.assertEqual(rules["absolute_timeout_minutes"], 480)


class IdentityTests(SecurityModelTestCase):
    """Tests for Identity models."""

    def test_create_identity(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="test-user-001",
            display_name="Test User",
            owner=self.user,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(identity.identifier, "test-user-001")
        self.assertEqual(identity.identity_type, "user")
        self.assertTrue(identity.is_active)

    def test_identity_expiration(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="expiring-user",
            display_name="Expiring User",
            expires_at=timezone.now() - timedelta(days=1),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertTrue(identity.is_expired)
        self.assertFalse(identity.is_active)

    def test_create_service_identity(self):
        svc_identity = ServiceIdentity.objects.create(
            identity_type="service",
            identifier="api-service",
            display_name="API Service",
            service_type="api",
            service_account_token="test-token",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(svc_identity.service_type, "api")
        self.assertEqual(svc_identity.service_account_token, "test-token")

    def test_service_identity_validation(self):
        svc_identity = ServiceIdentity(
            identity_type="service",
            identifier="invalid-api",
            display_name="Invalid API",
            service_type="api",
            service_account_token="",
            created_by=self.user,
            updated_by=self.user,
        )
        with self.assertRaises(Exception):
            svc_identity.full_clean()

    def test_create_organizational_identity(self):
        org_identity = OrganizationalIdentity.objects.create(
            identity_type="organization",
            identifier="dept-it",
            display_name="IT Department",
            org_identity_type="department",
            organization_unit=self.org_unit,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(org_identity.org_identity_type, "department")
        self.assertEqual(org_identity.organization_unit, self.org_unit)


class PermissionTests(SecurityModelTestCase):
    """Tests for Permission models."""

    def test_create_permission(self):
        perm = Permission.objects.create(
            name="View Reports",
            module="reports",
            resource_type="report",
            action="view",
            description="View reports permission",
        )
        self.assertEqual(perm.module, "reports")
        self.assertEqual(perm.full_name, "reports:report:view")

    def test_permission_conditions_json(self):
        perm = Permission.objects.create(
            name="Conditional Permission",
            module="test",
            resource_type="resource",
            action="action",
            conditions={"ip_allowlist": ["192.168.1.0/24"]},
        )
        self.assertEqual(perm.conditions["ip_allowlist"], ["192.168.1.0/24"])


class RolePermissionTests(SecurityModelTestCase):
    """Tests for RolePermission model."""

    def setUp(self):
        super().setUp()
        self.permission = Permission.objects.create(
            name="Test Permission",
            module="test",
            resource_type="resource",
            action="view",
        )

    def test_grant_role_permission(self):
        rp = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            granted_by=self.user,
        )
        self.assertEqual(rp.role, self.role)
        self.assertEqual(rp.permission, self.permission)
        self.assertTrue(rp.is_valid)

    def test_role_permission_expiration(self):
        rp = RolePermission.objects.create(
            role=self.role,
            permission=self.permission,
            granted_by=self.user,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(rp.is_expired)
        self.assertFalse(rp.is_valid)


class IdentityRoleTests(SecurityModelTestCase):
    """Tests for IdentityRole model."""

    def test_assign_role_to_identity(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="test-user",
            display_name="Test User",
            created_by=self.user,
            updated_by=self.user,
        )
        ir = IdentityRole.objects.create(
            identity=identity,
            role=self.role,
            assigned_by=self.user,
        )
        self.assertEqual(ir.identity, identity)
        self.assertEqual(ir.role, self.role)
        self.assertTrue(ir.is_valid)

    def test_identity_role_expiration(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="test-user",
            display_name="Test User",
            created_by=self.user,
            updated_by=self.user,
        )
        ir = IdentityRole.objects.create(
            identity=identity,
            role=self.role,
            assigned_by=self.user,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(ir.is_expired)
        self.assertFalse(ir.is_valid)


class PermissionGrantTests(SecurityModelTestCase):
    """Tests for PermissionGrant model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="grant-user",
            display_name="Grant User",
            created_by=self.user,
            updated_by=self.user,
        )
        self.permission = Permission.objects.create(
            name="Direct Permission",
            module="test",
            resource_type="resource",
            action="grant",
        )

    def test_grant_permission(self):
        grant = PermissionGrant.objects.create(
            identity=self.identity,
            permission=self.permission,
            granted_by=self.user,
        )
        self.assertEqual(grant.identity, self.identity)
        self.assertEqual(grant.permission, self.permission)
        self.assertTrue(grant.is_valid)

    def test_permission_grant_expiration(self):
        grant = PermissionGrant.objects.create(
            identity=self.identity,
            permission=self.permission,
            granted_by=self.user,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(grant.is_expired)
        self.assertFalse(grant.is_valid)


class RoleHierarchyTests(SecurityModelTestCase):
    """Tests for RoleHierarchy model."""

    def test_create_hierarchy(self):
        hierarchy = RoleHierarchy.objects.create(
            parent_role=self.role,
            child_role=self.other_role,
            inherit_permissions=True,
            inherit_role_permissions=True,
            created_by=self.user,
        )
        self.assertEqual(hierarchy.parent_role, self.role)
        self.assertEqual(hierarchy.child_role, self.other_role)

    def test_hierarchy_self_reference_validation(self):
        hierarchy = RoleHierarchy(
            parent_role=self.role,
            child_role=self.role,
            created_by=self.user,
        )
        with self.assertRaises(Exception):
            hierarchy.full_clean()


class LoginAttemptTests(SecurityModelTestCase):
    """Tests for LoginAttempt model."""

    def test_record_login_attempt(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="login-user",
            display_name="Login User",
            created_by=self.user,
            updated_by=self.user,
        )
        attempt = LoginAttempt.objects.create(
            identity=identity,
            username_attempted="login-user",
            ip_address="192.168.1.100",
            outcome=LoginAttempt.SUCCESS,
        )
        self.assertEqual(attempt.outcome, LoginAttempt.SUCCESS)
        self.assertEqual(attempt.risk_score, 0)

    def test_failed_login_attempt(self):
        attempt = LoginAttempt.objects.create(
            username_attempted="failed-user",
            ip_address="192.168.1.101",
            outcome=LoginAttempt.FAILED_INVALID_CREDENTIALS,
            failure_reason="Invalid password",
            risk_score=50,
            is_suspicious=True,
        )
        self.assertEqual(attempt.outcome, LoginAttempt.FAILED_INVALID_CREDENTIALS)
        self.assertTrue(attempt.is_suspicious)


class AccessReviewTests(SecurityModelTestCase):
    """Tests for AccessReview model."""

    def setUp(self):
        super().setUp()
        self.target_identity = Identity.objects.create(
            identity_type="user",
            identifier="review-target",
            display_name="Review Target",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_access_review(self):
        review = AccessReview.objects.create(
            name="Quarterly Review",
            review_type="identity",
            target_identity=self.target_identity,
            started_at=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            created_by=self.user,
        )
        self.assertEqual(review.status, AccessReviewStatus.PENDING)
        self.assertFalse(review.is_overdue)

    def test_access_review_validation(self):
        review = AccessReview(
            name="Invalid Review",
            review_type="identity",
            started_at=timezone.now(),
            due_date=timezone.now() - timedelta(days=1),  # Due before start
            created_by=self.user,
        )
        with self.assertRaises(Exception):
            review.full_clean()

    def test_completion_percentage(self):
        review = AccessReview.objects.create(
            name="Test Review",
            review_type="identity",
            started_at=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            total_items_reviewed=10,
            items_approved=5,
            items_revoked=2,
            items_modified=1,
            items_escalated=2,
            created_by=self.user,
        )
        self.assertEqual(review.completion_percentage, 100.0)


class AccessReviewItemTests(SecurityModelTestCase):
    """Tests for AccessReviewItem model."""

    def setUp(self):
        super().setUp()
        self.review = AccessReview.objects.create(
            name="Test Review",
            review_type="identity",
            started_at=timezone.now(),
            due_date=timezone.now() + timedelta(days=30),
            created_by=self.user,
        )
        self.target_identity = Identity.objects.create(
            identity_type="user",
            identifier="item-target",
            display_name="Item Target",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_review_item(self):
        item = AccessReviewItem.objects.create(
            access_review=self.review,
            identity=self.target_identity,
            risk_level="medium",
        )
        self.assertEqual(item.access_review, self.review)
        self.assertEqual(item.risk_level, "medium")

    def test_review_decision_validation(self):
        item = AccessReviewItem(
            access_review=self.review,
            identity=self.target_identity,
            decision="invalid_decision",
        )
        with self.assertRaises(Exception):
            item.full_clean()


class SessionTests(SecurityModelTestCase):
    """Tests for Session model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="session-user",
            display_name="Session User",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_session(self):
        session = Session.objects.create(
            identity=self.identity,
            session_key="test-session-key-123",
            ip_address="192.168.1.100",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(session.identity, self.identity)
        self.assertTrue(session.is_active)

    def test_session_expiration(self):
        session = Session.objects.create(
            identity=self.identity,
            session_key="expired-session",
            ip_address="192.168.1.100",
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        self.assertTrue(session.is_expired)
        self.assertFalse(session.is_active)

    def test_session_idle_expiration(self):
        session = Session.objects.create(
            identity=self.identity,
            session_key="idle-session",
            ip_address="192.168.1.100",
            expires_at=timezone.now() + timedelta(hours=1),
            idle_timeout_minutes=5,
            last_activity_at=timezone.now() - timedelta(minutes=10),
        )
        self.assertTrue(session.is_idle_expired)
        self.assertFalse(session.is_active)

    def test_extend_session(self):
        session = Session.objects.create(
            identity=self.identity,
            session_key="extend-session",
            ip_address="192.168.1.100",
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        original_expiry = session.expires_at
        session.extend(60)
        self.assertGreater(session.expires_at, original_expiry)


class MFAEnrollmentTests(SecurityModelTestCase):
    """Tests for MFAEnrollment model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="mfa-user",
            display_name="MFA User",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_totp_enrollment(self):
        enrollment = MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            is_primary=True,
            enrolled_by=self.user,
        )
        self.assertEqual(enrollment.method, MFAMethod.TOTP)
        self.assertTrue(enrollment.is_primary)

    def test_totp_validation(self):
        enrollment = MFAEnrollment(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="",
            enrolled_by=self.user,
        )
        with self.assertRaises(Exception):
            enrollment.full_clean()

    def test_sms_validation(self):
        enrollment = MFAEnrollment(
            identity=self.identity,
            method=MFAMethod.SMS,
            phone_number="",
            enrolled_by=self.user,
        )
        with self.assertRaises(Exception):
            enrollment.full_clean()

    def test_email_validation(self):
        enrollment = MFAEnrollment(
            identity=self.identity,
            method=MFAMethod.EMAIL,
            email_address="",
            enrolled_by=self.user,
        )
        with self.assertRaises(Exception):
            enrollment.full_clean()

    def test_trust_device(self):
        enrollment = MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            enrolled_by=self.user,
        )
        enrollment.trust_device("Test Device", "device-fingerprint-123", 30)
        self.assertTrue(enrollment.is_trusted_device)
        self.assertEqual(enrollment.device_name, "Test Device")
        self.assertTrue(enrollment.is_trusted)

    def test_revoke_trust(self):
        enrollment = MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            is_trusted_device=True,
            device_fingerprint="device-fingerprint-123",
            trusted_since=timezone.now(),
            trust_expires_at=timezone.now() + timedelta(days=30),
            enrolled_by=self.user,
        )
        enrollment.revoke_trust()
        self.assertFalse(enrollment.is_trusted_device)
        self.assertEqual(enrollment.device_fingerprint, "")


class MFAVerificationAttemptTests(SecurityModelTestCase):
    """Tests for MFAVerificationAttempt model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="mfa-verify-user",
            display_name="MFA Verify User",
            created_by=self.user,
            updated_by=self.user,
        )
        self.enrollment = MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            enrolled_by=self.user,
        )

    def test_create_verification_attempt(self):
        attempt = MFAVerificationAttempt.objects.create(
            identity=self.identity,
            enrollment=self.enrollment,
            challenge="123456",
            response="123456",
            ip_address="192.168.1.100",
            outcome=MFAVerificationAttempt.SUCCESS,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        self.assertEqual(attempt.outcome, MFAVerificationAttempt.SUCCESS)
        self.assertTrue(attempt.is_successful)


class APICredentialTests(SecurityModelTestCase):
    """Tests for APICredential model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="service",
            identifier="api-service",
            display_name="API Service",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_api_credential(self):
        credential = APICredential.objects.create(
            name="Test API Key",
            credential_type="api_key",
            service_name="Test Service",
            credential_key="sk_test_123456",
            identity=self.identity,
        )
        self.assertEqual(credential.credential_type, "api_key")
        self.assertTrue(credential.is_valid)

    def test_api_credential_expiration(self):
        credential = APICredential.objects.create(
            name="Expired Key",
            credential_type="api_key",
            service_name="Test Service",
            credential_key="sk_expired",
            identity=self.identity,
            expires_at=timezone.now() - timedelta(days=1),
        )
        self.assertTrue(credential.is_expired)
        self.assertFalse(credential.is_valid)

    def test_mark_compromised(self):
        credential = APICredential.objects.create(
            name="Compromised Key",
            credential_type="api_key",
            service_name="Test Service",
            credential_key="sk_compromised",
            identity=self.identity,
        )
        credential.mark_compromised("Suspected breach")
        self.assertTrue(credential.is_compromised)
        self.assertFalse(credential.is_active)
        self.assertFalse(credential.is_valid)

    def test_rotate_credential(self):
        credential = APICredential.objects.create(
            name="Rotated Key",
            credential_type="api_key",
            service_name="Test Service",
            credential_key="sk_old",
            identity=self.identity,
        )
        credential.rotate_credential("sk_new", "new_secret")
        self.assertEqual(credential.credential_key, "sk_new")
        self.assertEqual(credential.credential_secret, "new_secret")
        self.assertFalse(credential.is_compromised)


class APIAccessTokenTests(SecurityModelTestCase):
    """Tests for APIAccessToken model."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="service",
            identifier="token-service",
            display_name="Token Service",
            created_by=self.user,
            updated_by=self.user,
        )
        self.credential = APICredential.objects.create(
            name="Test Credential",
            credential_type="api_key",
            service_name="Test Service",
            credential_key="sk_test",
            identity=self.identity,
        )

    def test_create_access_token(self):
        token = APIAccessToken.objects.create(
            credential=self.credential,
            token="test-access-token-123",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.assertEqual(token.credential, self.credential)
        self.assertTrue(token.is_valid)

    def test_token_expiration(self):
        token = APIAccessToken.objects.create(
            credential=self.credential,
            token="expired-token",
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        self.assertTrue(token.is_expired)
        self.assertFalse(token.is_valid)

    def test_token_revocation(self):
        token = APIAccessToken.objects.create(
            credential=self.credential,
            token="revoked-token",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        token.revoke("Security policy violation")
        self.assertTrue(token.is_revoked)
        self.assertFalse(token.is_valid)


class DatabaseSecurityPolicyTests(SecurityModelTestCase):
    """Tests for DatabaseSecurityPolicy model."""

    def test_create_database_policy(self):
        policy = DatabaseSecurityPolicy.objects.create(
            name="PostgreSQL Policy",
            database_identifier="prod-db",
            database_type="postgresql",
            host="db.example.com",
            port=5432,
            database_name="production",
            require_ssl=True,
            statement_timeout_ms=30000,
            lock_timeout_ms=1000,
        )
        self.assertEqual(policy.database_type, "postgresql")
        self.assertTrue(policy.is_valid)

    def test_policy_validation(self):
        policy = DatabaseSecurityPolicy(
            name="Invalid Policy",
            database_identifier="test-db",
            database_type="postgresql",
            statement_timeout_ms=50,  # Too low
            lock_timeout_ms=1000,
        )
        with self.assertRaises(Exception):
            policy.full_clean()

    def test_lock_timeout_validation(self):
        policy = DatabaseSecurityPolicy(
            name="Invalid Lock Timeout",
            database_identifier="test-db",
            database_type="postgresql",
            statement_timeout_ms=1000,
            lock_timeout_ms=2000,  # Greater than statement timeout
        )
        with self.assertRaises(Exception):
            policy.full_clean()


class SecureFileTests(SecurityModelTestCase):
    """Tests for SecureFile model."""

    def setUp(self):
        super().setUp()
        self.owner = Identity.objects.create(
            identity_type="user",
            identifier="file-owner",
            display_name="File Owner",
            created_by=self.user,
            updated_by=self.user,
        )
        self.uploader = Identity.objects.create(
            identity_type="user",
            identifier="file-uploader",
            display_name="File Uploader",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_secure_file(self):
        file = SecureFile.objects.create(
            filename="test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf",
            storage_path="/files/test.pdf",
            owner=self.owner,
            uploaded_by=self.uploader,
            checksum_value="abc123",
        )
        self.assertEqual(file.filename, "test.pdf")
        self.assertTrue(file.is_accessible_by(self.owner))
        self.assertTrue(file.is_accessible_by(self.uploader))

    def test_file_access_control(self):
        other_identity = Identity.objects.create(
            identity_type="user",
            identifier="other-user",
            display_name="Other User",
            created_by=self.user,
            updated_by=self.user,
        )
        file = SecureFile.objects.create(
            filename="private.pdf",
            original_filename="private.pdf",
            file_size=2048,
            content_type="application/pdf",
            storage_path="/files/private.pdf",
            owner=self.owner,
            uploaded_by=self.uploader,
            checksum_value="def456",
            is_public=False,
        )
        file.allowed_identities.add(other_identity)
        self.assertTrue(file.is_accessible_by(other_identity))

        another_identity = Identity.objects.create(
            identity_type="user",
            identifier="another-user",
            display_name="Another User",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertFalse(file.is_accessible_by(another_identity))

    def test_file_versioning(self):
        file = SecureFile.objects.create(
            filename="v1.pdf",
            original_filename="document.pdf",
            file_size=1024,
            content_type="application/pdf",
            storage_path="/files/v1.pdf",
            owner=self.owner,
            uploaded_by=self.uploader,
            checksum_value="v1checksum",
        )
        file.new_version()
        self.assertFalse(file.is_latest_version)
        self.assertEqual(file.version, 2)


class SecuritySelectorsTests(SecurityModelTestCase):
    """Tests for security selectors."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="selector-user",
            display_name="Selector User",
            status=SecurityStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user,
        )
        self.service_identity = ServiceIdentity.objects.create(
            identity_type="service",
            identifier="selector-service",
            display_name="Selector Service",
            service_type="api",
            status=SecurityStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user,
        )

    def test_get_identities(self):
        identities = selectors.get_identities()
        self.assertGreaterEqual(identities.count(), 1)

    def test_get_active_identities(self):
        active = selectors.get_active_identities()
        self.assertIn(self.identity, active)

    def test_get_service_identities(self):
        services = selectors.get_service_identities()
        self.assertIn(self.service_identity, services)

    def test_get_security_policies(self):
        policy = EnterpriseSecurityPolicy.objects.create(
            name="Test Policy",
            policy_type="password",
            created_by=self.user,
            updated_by=self.user,
        )
        policies = selectors.get_security_policies()
        self.assertIn(policy, policies)

    def test_get_login_attempts(self):
        LoginAttempt.objects.create(
            identity=self.identity,
            username_attempted="selector-user",
            ip_address="192.168.1.100",
            outcome=LoginAttempt.SUCCESS,
        )
        attempts = selectors.get_login_attempts(identity=self.identity)
        self.assertEqual(attempts.count(), 1)

    def test_get_failed_login_attempts(self):
        LoginAttempt.objects.create(
            identity=self.identity,
            username_attempted="selector-user",
            ip_address="192.168.1.101",
            outcome=LoginAttempt.FAILED_INVALID_CREDENTIALS,
        )
        failed = selectors.get_failed_login_attempts(identity=self.identity)
        self.assertEqual(failed.count(), 1)

    def test_get_sessions(self):
        Session.objects.create(
            identity=self.identity,
            session_key="test-session-1",
            ip_address="192.168.1.100",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        sessions = selectors.get_sessions(identity=self.identity)
        self.assertEqual(sessions.count(), 1)

    def test_get_active_sessions(self):
        Session.objects.create(
            identity=self.identity,
            session_key="active-session",
            ip_address="192.168.1.100",
            status=SessionStatus.ACTIVE,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        Session.objects.create(
            identity=self.identity,
            session_key="expired-session",
            ip_address="192.168.1.100",
            status=SessionStatus.EXPIRED,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        active = selectors.get_active_sessions(identity=self.identity)
        self.assertEqual(active.count(), 1)

    def test_get_mfa_enrollments(self):
        MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            is_primary=True,
            enrolled_by=self.user,
        )
        enrollments = selectors.get_mfa_enrollments(self.identity)
        self.assertEqual(enrollments.count(), 1)

    def test_get_primary_mfa_enrollment(self):
        enrollment = MFAEnrollment.objects.create(
            identity=self.identity,
            method=MFAMethod.TOTP,
            secret_key="JBSWY3DPEHPK3PXP",
            is_primary=True,
            enrolled_by=self.user,
        )
        primary = selectors.get_primary_mfa_enrollment(self.identity)
        self.assertEqual(primary, enrollment)

    def test_get_api_credentials(self):
        APICredential.objects.create(
            name="Test Cred",
            credential_type="api_key",
            service_name="Test",
            credential_key="sk_test",
            identity=self.identity,
        )
        credentials = selectors.get_api_credentials(self.identity)
        self.assertEqual(credentials.count(), 1)

    def test_get_secure_files(self):
        SecureFile.objects.create(
            filename="test.pdf",
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf",
            storage_path="/files/test.pdf",
            owner=self.identity,
            uploaded_by=self.identity,
            checksum_value="abc123",
        )
        files = selectors.get_secure_files(owner=self.identity)
        self.assertEqual(files.count(), 1)

    def test_get_security_dashboard_stats(self):
        stats = selectors.get_security_dashboard_stats()
        self.assertIn("total_identities", stats)
        self.assertIn("active_sessions", stats)
        self.assertIn("failed_logins_7d", stats)

    def test_get_identity_risk_score(self):
        LoginAttempt.objects.create(
            identity=self.identity,
            username_attempted="selector-user",
            ip_address="192.168.1.100",
            outcome=LoginAttempt.FAILED_INVALID_CREDENTIALS,
        )
        score = selectors.get_identity_risk_score(self.identity)
        self.assertGreater(score, 0)


class SecurityServicesTests(SecurityModelTestCase):
    """Tests for security services."""

    def setUp(self):
        super().setUp()
        self.identity = Identity.objects.create(
            identity_type="user",
            identifier="service-user",
            display_name="Service User",
            created_by=self.user,
            updated_by=self.user,
        )

    def test_create_identity_service(self):
        from apps.security.services import CreateIdentityService
        service = CreateIdentityService(user=self.user)
        identity = service.execute(
            identity_type="user",
            identifier="new-user",
            display_name="New User",
        )
        self.assertEqual(identity.identifier, "new-user")

    def test_create_service_identity_service(self):
        from apps.security.services import CreateServiceIdentityService
        service = CreateServiceIdentityService(user=self.user)
        identity = service.execute(
            identifier="new-service",
            display_name="New Service",
            service_type="api",
            identity_type="service",
        )
        self.assertEqual(identity.service_type, "api")

    def test_create_permission_service(self):
        from apps.security.services import CreatePermissionService
        service = CreatePermissionService(user=self.user)
        perm = service.execute(
            name="Service Permission",
            module="service",
            resource_type="resource",
            action="test",
        )
        self.assertEqual(perm.module, "service")

    def test_record_login_attempt_service(self):
        from apps.security.services import RecordLoginAttemptService
        service = RecordLoginAttemptService(user=self.user)
        attempt = service.execute(
            username_attempted="service-test",
            ip_address="192.168.1.200",
            outcome=LoginAttempt.SUCCESS,
        )
        self.assertEqual(attempt.username_attempted, "service-test")

    def test_create_api_credential_service(self):
        from apps.security.services import CreateAPICredentialService
        service = CreateAPICredentialService(user=self.user)
        credential = service.execute(
            identity=self.identity,
            name="Service Credential",
            credential_type="api_key",
            service_name="Service API",
        )
        self.assertEqual(credential.name, "Service Credential")

    def test_rotate_api_credential_service(self):
        from apps.security.services import CreateAPICredentialService, RotateAPICredentialService
        create_service = CreateAPICredentialService(user=self.user)
        credential = create_service.execute(
            identity=self.identity,
            name="Rotate Test",
            credential_type="api_key",
            service_name="Test",
        )
        rotate_service = RotateAPICredentialService(user=self.user)
        rotated = rotate_service.execute(credential=credential)
        self.assertNotEqual(rotated.credential_key, credential.credential_key)


class SecurityViewsTests(SecurityModelTestCase):
    """Tests for security views."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_security_dashboard_view(self):
        response = self.client.get("/security/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Security Dashboard")

    def test_policy_list_view(self):
        response = self.client.get("/security/policies/")
        self.assertEqual(response.status_code, 200)

    def test_identity_list_view(self):
        response = self.client.get("/security/identities/")
        self.assertEqual(response.status_code, 200)

    def test_permission_list_view(self):
        response = self.client.get("/security/permissions/")
        self.assertEqual(response.status_code, 200)

    def test_login_attempt_list_view(self):
        response = self.client.get("/security/login-attempts/")
        self.assertEqual(response.status_code, 200)

    def test_session_list_view(self):
        response = self.client.get("/security/sessions/")
        self.assertEqual(response.status_code, 200)

    def test_access_review_list_view(self):
        response = self.client.get("/security/access-reviews/")
        self.assertEqual(response.status_code, 200)

    def test_database_policy_list_view(self):
        response = self.client.get("/security/database-policies/")
        self.assertEqual(response.status_code, 200)

    def test_secure_file_list_view(self):
        response = self.client.get("/security/secure-files/")
        self.assertEqual(response.status_code, 200)

    def test_dashboard_api(self):
        response = self.client.get("/security/dashboard/api/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_identities", data)


class SecurityAdminTests(SecurityModelTestCase):
    """Tests for security admin."""

    def setUp(self):
        super().setUp()
        self.admin_user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        self.client.force_login(self.admin_user)

    def test_admin_changelist(self):
        response = self.client.get("/admin/security/enterprisesecuritypolicy/")
        self.assertEqual(response.status_code, 200)

    def test_identity_admin(self):
        identity = Identity.objects.create(
            identity_type="user",
            identifier="admin-test",
            display_name="Admin Test",
            created_by=self.user,
            updated_by=self.user,
        )
        response = self.client.get(f"/admin/security/identity/{identity.pk}/change/")
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    import django
    django.setup()
    from django.test.utils import get_runner
    from django.conf import settings
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.security.tests"])