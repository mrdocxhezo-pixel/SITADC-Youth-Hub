"""Governance permission tests."""

from __future__ import annotations

from apps.governance.permissions import (
    GOVERNANCE_APPROVE,
    GOVERNANCE_ARCHIVE,
    GOVERNANCE_CREATE,
    GOVERNANCE_DELETE,
    GOVERNANCE_EXPORT,
    GOVERNANCE_MANAGE,
    GOVERNANCE_RESTORE,
    GOVERNANCE_UPDATE,
    GOVERNANCE_VIEW,
    GOVERNANCE_VIEW_CONFIDENTIAL,
    user_can_access_governance,
    user_can_approve_governance,
    user_can_export_governance,
    user_can_manage_capas,
    user_can_manage_complaints,
    user_can_manage_compliance,
    user_can_manage_controls,
    user_can_manage_documents,
    user_can_manage_ethics,
    user_can_manage_governance,
    user_can_manage_incidents,
    user_can_manage_meetings,
    user_can_manage_policies,
    user_can_manage_risks,
    user_can_manage_safeguarding,
    user_can_manage_whistleblower,
    user_can_view_capas,
    user_can_view_complaints,
    user_can_view_compliance,
    user_can_view_confidential_governance,
    user_can_view_controls,
    user_can_view_documents,
    user_can_view_ethics,
    user_can_view_incidents,
    user_can_view_meetings,
    user_can_view_policies,
    user_can_view_risks,
    user_can_view_safeguarding,
    user_can_view_whistleblower,
)

from .base import GovernanceTestCase


class GovernancePermissionTests(GovernanceTestCase):
    """Tests for governance permissions."""

    def setUp(self):
        super().setUp()
        # Create a user with governance permissions
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role

        # Get or create governance permissions
        content_type = ContentType.objects.get_for_model(Role)
        perms = []
        for action in [
            GOVERNANCE_VIEW,
            GOVERNANCE_CREATE,
            GOVERNANCE_UPDATE,
            GOVERNANCE_DELETE,
            GOVERNANCE_APPROVE,
            GOVERNANCE_ARCHIVE,
            GOVERNANCE_RESTORE,
            GOVERNANCE_EXPORT,
            GOVERNANCE_MANAGE,
            GOVERNANCE_VIEW_CONFIDENTIAL,
        ]:
            perm, _ = Permission.objects.get_or_create(
                codename=action,
                defaults={
                    "name": f"Can {action.replace('_', ' ')} governance",
                    "content_type": content_type,
                },
            )
            perms.append(perm)

        # Assign permissions to user via a role
        role = Role.objects.create(
            name="Test Governance Role",
            slug="test-governance-role",
            description="Test role for governance",
        )
        role.permissions.add(*perms)
        from apps.rbac.models import UserRoleAssignment

        UserRoleAssignment.objects.create(user=self.user, role=role, status="ACTIVE")

    def test_user_can_access_governance(self):
        """Test user_can_access_governance."""
        self.assertTrue(user_can_access_governance(self.user))

    def test_user_can_manage_governance(self):
        """Test user_can_manage_governance."""
        self.assertTrue(user_can_manage_governance(self.user))

    def test_user_can_view_confidential_governance(self):
        """Test user_can_view_confidential_governance."""
        self.assertTrue(user_can_view_confidential_governance(self.user))

    def test_user_can_view_policies(self):
        """Test user_can_view_policies."""
        self.assertTrue(user_can_view_policies(self.user))

    def test_user_can_manage_policies(self):
        """Test user_can_manage_policies."""
        self.assertTrue(user_can_manage_policies(self.user))

    def test_user_can_view_risks(self):
        """Test user_can_view_risks."""
        self.assertTrue(user_can_view_risks(self.user))

    def test_user_can_manage_risks(self):
        """Test user_can_manage_risks."""
        self.assertTrue(user_can_manage_risks(self.user))

    def test_user_can_view_compliance(self):
        """Test user_can_view_compliance."""
        self.assertTrue(user_can_view_compliance(self.user))

    def test_user_can_manage_compliance(self):
        """Test user_can_manage_compliance."""
        self.assertTrue(user_can_manage_compliance(self.user))

    def test_user_can_view_controls(self):
        """Test user_can_view_controls."""
        self.assertTrue(user_can_view_controls(self.user))

    def test_user_can_manage_controls(self):
        """Test user_can_manage_controls."""
        self.assertTrue(user_can_manage_controls(self.user))

    def test_user_can_view_ethics(self):
        """Test user_can_view_ethics."""
        self.assertTrue(user_can_view_ethics(self.user))

    def test_user_can_manage_ethics(self):
        """Test user_can_manage_ethics."""
        self.assertTrue(user_can_manage_ethics(self.user))

    def test_user_can_view_safeguarding(self):
        """Test user_can_view_safeguarding (requires view_confidential)."""
        self.assertTrue(user_can_view_safeguarding(self.user))

    def test_user_can_manage_safeguarding(self):
        """Test user_can_manage_safeguarding (requires view_confidential)."""
        self.assertTrue(user_can_manage_safeguarding(self.user))

    def test_user_can_view_incidents(self):
        """Test user_can_view_incidents."""
        self.assertTrue(user_can_view_incidents(self.user))

    def test_user_can_manage_incidents(self):
        """Test user_can_manage_incidents."""
        self.assertTrue(user_can_manage_incidents(self.user))

    def test_user_can_view_complaints(self):
        """Test user_can_view_complaints."""
        self.assertTrue(user_can_view_complaints(self.user))

    def test_user_can_manage_complaints(self):
        """Test user_can_manage_complaints."""
        self.assertTrue(user_can_manage_complaints(self.user))

    def test_user_can_view_whistleblower(self):
        """Test user_can_view_whistleblower (requires view_confidential)."""
        self.assertTrue(user_can_view_whistleblower(self.user))

    def test_user_can_manage_whistleblower(self):
        """Test user_can_manage_whistleblower (requires view_confidential)."""
        self.assertTrue(user_can_manage_whistleblower(self.user))

    def test_user_can_view_capas(self):
        """Test user_can_view_capas."""
        self.assertTrue(user_can_view_capas(self.user))

    def test_user_can_manage_capas(self):
        """Test user_can_manage_capas."""
        self.assertTrue(user_can_manage_capas(self.user))

    def test_user_can_view_documents(self):
        """Test user_can_view_documents."""
        self.assertTrue(user_can_view_documents(self.user))

    def test_user_can_manage_documents(self):
        """Test user_can_manage_documents."""
        self.assertTrue(user_can_manage_documents(self.user))

    def test_user_can_view_meetings(self):
        """Test user_can_view_meetings."""
        self.assertTrue(user_can_view_meetings(self.user))

    def test_user_can_manage_meetings(self):
        """Test user_can_manage_meetings."""
        self.assertTrue(user_can_manage_meetings(self.user))

    def test_user_can_export_governance(self):
        """Test user_can_export_governance."""
        self.assertTrue(user_can_export_governance(self.user))

    def test_user_can_approve_governance(self):
        """Test user_can_approve_governance."""
        self.assertTrue(user_can_approve_governance(self.user))

    def test_superuser_permissions(self):
        """Test that superuser has all permissions."""
        self.assertTrue(user_can_access_governance(self.admin_user))
        self.assertTrue(user_can_manage_governance(self.admin_user))
        self.assertTrue(user_can_view_confidential_governance(self.admin_user))

    def test_anonymous_user_denied(self):
        """Test that anonymous users are denied all permissions."""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        self.assertFalse(user_can_access_governance(anon))
        self.assertFalse(user_can_manage_governance(anon))
        self.assertFalse(user_can_view_confidential_governance(anon))
        self.assertFalse(user_can_view_policies(anon))
        self.assertFalse(user_can_manage_policies(anon))
