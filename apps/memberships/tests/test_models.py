"""
Model tests for the membership management module.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.memberships.constants import TerminationReason
from apps.memberships.models import (
    MembershipAuditRecord,
    MembershipStatus,
    MembershipStatusHistory,
    MembershipTermination,
)
from apps.memberships.tests.base import MembershipTestCase

User = get_user_model()


class MemberProfileModelTests(MembershipTestCase):
    def test_member_profile_creation(self):
        profile = self._create_profile()
        self.assertEqual(profile.membership_id, "")
        self.assertTrue(profile.is_active)
        self.assertEqual(profile.status_display, "Active")
        self.assertEqual(profile.full_name, "Member User")

    def test_status_properties(self):
        profile = self._create_profile()
        suspended = MembershipStatus.objects.get(code="SUSPENDED")
        profile.status = suspended
        profile.save()
        self.assertTrue(profile.is_suspended)
        self.assertFalse(profile.is_active)

    def test_membership_id_is_unique(self):
        profile = self._create_profile()
        profile.membership_id = "MEM-SITADC-2026-000001"
        profile.save()
        User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            first_name="Other",
            last_name="User",
        )
        other = self._create_profile(email="other@example.com", username="otheruser")
        other.membership_id = "MEM-SITADC-2026-000001"
        with self.assertRaises(IntegrityError):
            other.save()

    def _create_profile(self, email="member@example.com", username="memberuser"):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        user = User.objects.get(username=username)
        return MemberProfile.objects.create(
            user=user,
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
        )


class ImmutableRecordTests(MembershipTestCase):
    def test_audit_record_is_immutable(self):
        audit = MembershipAuditRecord.objects.create(
            entity_type="MemberProfile",
            entity_id="abc-123",
            action="CREATED",
            changed_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            audit.notes = "tampered"
            audit.save()
        with self.assertRaises(ValidationError):
            audit.delete()

    def test_status_history_is_immutable(self):
        history = MembershipStatusHistory.objects.create(
            member=self._create_member(),
            to_status=MembershipStatus.objects.get(code="ACTIVE"),
            changed_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            history.reason = "tampered"
            history.save()

    def test_termination_is_immutable(self):
        member = self._create_member()
        termination = MembershipTermination.objects.create(
            member=member,
            reason=TerminationReason.VOLUNTARY_RESIGNATION,
            effective_date="2026-05-01",
            authorized_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            termination.reason_detail = "tampered"
            termination.save()

    def _create_member(self):
        from apps.memberships.models import (
            MemberProfile,
            MembershipCategory,
            MembershipLevel,
            MembershipStatus,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
        )
