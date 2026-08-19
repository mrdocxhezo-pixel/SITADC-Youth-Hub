"""Communication permission tests."""

from __future__ import annotations

from apps.communications.permissions import (
    COMMUNICATIONS_APPROVE,
    COMMUNICATIONS_ARCHIVE,
    COMMUNICATIONS_CREATE,
    COMMUNICATIONS_DELETE,
    COMMUNICATIONS_EXPORT,
    COMMUNICATIONS_MANAGE,
    COMMUNICATIONS_PUBLISH,
    COMMUNICATIONS_RESTORE,
    COMMUNICATIONS_UPDATE,
    COMMUNICATIONS_VIEW,
    COMMUNICATIONS_VIEW_CONFIDENTIAL,
    user_can_access_communications,
    user_can_approve_communications,
    user_can_archive_communications,
    user_can_create_communications,
    user_can_delete_communications,
    user_can_export_communications,
    user_can_manage_communications,
    user_can_publish_communications,
    user_can_restore_communications,
    user_can_update_communications,
    user_can_view_confidential_communications,
)

from .base import CommunicationsTestCase


class CommunicationsPermissionTests(CommunicationsTestCase):
    """Tests for communications permissions."""

    def setUp(self):
        super().setUp()
        self.grant_communications_permissions(self.user)

    def test_user_can_access_communications(self):
        """Test user_can_access_communications."""
        self.assertTrue(user_can_access_communications(self.user))

    def test_user_can_manage_communications(self):
        """Test user_can_manage_communications."""
        self.assertTrue(user_can_manage_communications(self.user))

    def test_user_can_view_confidential_communications(self):
        """Test user_can_view_confidential_communications."""
        self.assertTrue(user_can_view_confidential_communications(self.user))

    def test_user_can_create_communications(self):
        """Test user_can_create_communications."""
        self.assertTrue(user_can_create_communications(self.user))

    def test_user_can_update_communications(self):
        """Test user_can_update_communications."""
        self.assertTrue(user_can_update_communications(self.user))

    def test_user_can_delete_communications(self):
        """Test user_can_delete_communications."""
        self.assertTrue(user_can_delete_communications(self.user))

    def test_user_can_approve_communications(self):
        """Test user_can_approve_communications."""
        self.assertTrue(user_can_approve_communications(self.user))

    def test_user_can_publish_communications(self):
        """Test user_can_publish_communications."""
        self.assertTrue(user_can_publish_communications(self.user))

    def test_user_can_archive_communications(self):
        """Test user_can_archive_communications."""
        self.assertTrue(user_can_archive_communications(self.user))

    def test_user_can_restore_communications(self):
        """Test user_can_restore_communications."""
        self.assertTrue(user_can_restore_communications(self.user))

    def test_user_can_export_communications(self):
        """Test user_can_export_communications."""
        self.assertTrue(user_can_export_communications(self.user))

    def test_permission_constants_are_prefixed(self):
        """Test permission codes carry the communications module prefix."""
        for code in [
            COMMUNICATIONS_VIEW,
            COMMUNICATIONS_VIEW_CONFIDENTIAL,
            COMMUNICATIONS_CREATE,
            COMMUNICATIONS_UPDATE,
            COMMUNICATIONS_DELETE,
            COMMUNICATIONS_APPROVE,
            COMMUNICATIONS_PUBLISH,
            COMMUNICATIONS_ARCHIVE,
            COMMUNICATIONS_RESTORE,
            COMMUNICATIONS_EXPORT,
            COMMUNICATIONS_MANAGE,
        ]:
            self.assertTrue(code.startswith("communications."), code)

    def test_superuser_permissions(self):
        """Test that superuser has all permissions."""
        self.assertTrue(user_can_access_communications(self.admin_user))
        self.assertTrue(user_can_manage_communications(self.admin_user))
        self.assertTrue(user_can_view_confidential_communications(self.admin_user))

    def test_anonymous_user_denied(self):
        """Test that anonymous users are denied all permissions."""
        from django.contrib.auth.models import AnonymousUser

        anon = AnonymousUser()
        self.assertFalse(user_can_access_communications(anon))
        self.assertFalse(user_can_manage_communications(anon))
        self.assertFalse(user_can_view_confidential_communications(anon))
        self.assertFalse(user_can_create_communications(anon))
        self.assertFalse(user_can_approve_communications(anon))

    def test_partial_permissions_deny_high_privilege(self):
        """Test that a view-only user is denied manage/approve."""
        self.user.role_assignments.all().delete()
        # Grant only the view permission
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role, UserRoleAssignment

        content_type = ContentType.objects.get_for_model(Role)
        perm, _ = Permission.objects.get_or_create(
            codename=COMMUNICATIONS_VIEW,
            defaults={
                "name": "Can view communications",
                "content_type": content_type,
            },
        )
        role = Role.objects.create(
            name="View Only Role",
            slug="view-only-role",
            description="View only",
        )
        role.permissions.add(perm)
        UserRoleAssignment.objects.create(user=self.user, role=role, status="ACTIVE")
        self.assertTrue(user_can_access_communications(self.user))
        self.assertFalse(user_can_manage_communications(self.user))
        self.assertFalse(user_can_approve_communications(self.user))
        self.assertFalse(user_can_create_communications(self.user))
