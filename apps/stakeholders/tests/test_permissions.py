"""Permission-aware selector tests for stakeholder records."""

from datetime import timedelta

from django.utils import timezone

from apps.stakeholders.constants import ConfidentialityLevel
from apps.stakeholders.models import StakeholderAccessGrant, StakeholderContact
from apps.stakeholders.selectors import (
    user_can_access_stakeholder,
    visible_stakeholder_contacts,
    visible_stakeholder_documents,
    visible_stakeholders,
)

from .base import StakeholderTestCase


class VisibleStakeholderSelectorTests(StakeholderTestCase):
    def test_module_manager_sees_all_non_archived_records(self):
        internal = self.create_stakeholder()
        confidential = self.create_stakeholder(
            confidentiality=ConfidentialityLevel.CONFIDENTIAL
        )
        archived = self.create_stakeholder(is_archived=True)
        visible_ids = set(
            visible_stakeholders(self.manager).values_list("pk", flat=True)
        )
        self.assertEqual(visible_ids, {internal.pk, confidential.pk})
        self.assertIn(
            archived.pk,
            visible_stakeholders(self.manager, include_archived=True).values_list(
                "pk", flat=True
            ),
        )

    def test_assigned_owner_with_view_permission_sees_only_assigned_records(self):
        assigned = self.create_stakeholder(primary_responsible_officer=self.owner)
        self.create_stakeholder()
        self.grant_permissions(self.owner, "partners.view")
        self.assertEqual(list(visible_stakeholders(self.owner)), [assigned])

    def test_directory_permission_excludes_confidential_and_restricted_records(self):
        directory = self.create_stakeholder(
            confidentiality=ConfidentialityLevel.DIRECTORY
        )
        internal = self.create_stakeholder(
            confidentiality=ConfidentialityLevel.INTERNAL
        )
        self.create_stakeholder(confidentiality=ConfidentialityLevel.CONFIDENTIAL)
        self.create_stakeholder(confidentiality=ConfidentialityLevel.RESTRICTED)
        self.grant_permissions(self.viewer, "partners.view_directory")
        self.assertEqual(
            set(visible_stakeholders(self.viewer).values_list("pk", flat=True)),
            {directory.pk, internal.pk},
        )

    def test_active_explicit_grant_allows_view_and_expired_grant_denies(self):
        granted = self.create_stakeholder(
            confidentiality=ConfidentialityLevel.CONFIDENTIAL
        )
        expired = self.create_stakeholder(
            confidentiality=ConfidentialityLevel.CONFIDENTIAL
        )
        self.grant_permissions(self.viewer, "partners.view")
        StakeholderAccessGrant.objects.create(
            stakeholder=granted,
            user=self.viewer,
            reason="Relationship representative",
            starts_at=timezone.now() - timedelta(days=1),
            granted_by=self.manager,
        )
        StakeholderAccessGrant.objects.create(
            stakeholder=expired,
            user=self.viewer,
            reason="Expired assignment",
            starts_at=timezone.now() - timedelta(days=2),
            expires_at=timezone.now() - timedelta(days=1),
            granted_by=self.manager,
        )
        self.assertTrue(user_can_access_stakeholder(self.viewer, granted))
        self.assertFalse(user_can_access_stakeholder(self.viewer, expired))

    def test_no_permission_or_inactive_grant_fails_closed(self):
        stakeholder = self.create_stakeholder()
        StakeholderAccessGrant.objects.create(
            stakeholder=stakeholder,
            user=self.outsider,
            reason="Revoked",
            is_active=False,
            starts_at=timezone.now() - timedelta(days=1),
            granted_by=self.manager,
        )
        self.assertFalse(visible_stakeholders(self.outsider).exists())
        self.assertFalse(user_can_access_stakeholder(self.outsider, stakeholder))


class PrivateRelatedSelectorTests(StakeholderTestCase):
    def setUp(self):
        super().setUp()
        self.stakeholder = self.create_stakeholder(
            primary_responsible_officer=self.viewer
        )
        self.contact = StakeholderContact.objects.create(
            stakeholder=self.stakeholder,
            full_name="Private Contact",
            email="private@example.com",
        )
        self.document = self.create_document(self.stakeholder)
        self.grant_permissions(self.viewer, "partners.view")

    def test_profile_visibility_does_not_reveal_private_contacts(self):
        self.assertTrue(user_can_access_stakeholder(self.viewer, self.stakeholder))
        self.assertFalse(visible_stakeholder_contacts(self.viewer).exists())
        self.grant_permissions(self.viewer, "partners.view_private_contacts")
        self.assertEqual(
            list(visible_stakeholder_contacts(self.viewer)), [self.contact]
        )

    def test_profile_visibility_does_not_reveal_documents(self):
        self.assertFalse(visible_stakeholder_documents(self.viewer).exists())
        self.grant_permissions(self.viewer, "partners.manage_documents")
        self.assertEqual(
            list(visible_stakeholder_documents(self.viewer)), [self.document]
        )
