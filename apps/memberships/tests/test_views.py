"""
View tests for the membership management module.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.memberships.models import MemberProfile, MembershipStatus
from apps.memberships.tests.base import MembershipTestCase

User = get_user_model()


class MembershipViewsTests(MembershipTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def _create_member(self):
        from apps.memberships.models import (
            MembershipCategory,
            MembershipLevel,
            MembershipType,
        )

        return MemberProfile.objects.create(
            user=self.user,
            membership_id="MEM-SITADC-2026-000010",
            category=MembershipCategory.objects.get(code="ordinary"),
            membership_type=MembershipType.objects.get(code="individual"),
            level=MembershipLevel.objects.get(code="national"),
            status=MembershipStatus.objects.get(code="ACTIVE"),
            date_joined="2026-01-01",
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse("memberships:dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_directory_view(self):
        response = self.client.get(reverse("memberships:directory"))
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        member = self._create_member()
        response = self.client.get(
            reverse("memberships:detail", kwargs={"pk": member.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_id_card_view(self):
        member = self._create_member()
        response = self.client.get(
            reverse("memberships:id_card", kwargs={"pk": member.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_application_list_view(self):
        response = self.client.get(reverse("memberships:application_list"))
        self.assertEqual(response.status_code, 200)

    def test_renewal_list_view(self):
        response = self.client.get(reverse("memberships:renewal_list"))
        self.assertEqual(response.status_code, 200)

    def test_transfer_list_view(self):
        response = self.client.get(reverse("memberships:transfer_list"))
        self.assertEqual(response.status_code, 200)

    def test_payment_list_view(self):
        response = self.client.get(reverse("memberships:payment_list"))
        self.assertEqual(response.status_code, 200)

    def test_card_list_view(self):
        response = self.client.get(reverse("memberships:card_list"))
        self.assertEqual(response.status_code, 200)

    def test_leave_list_view(self):
        response = self.client.get(reverse("memberships:leave_list"))
        self.assertEqual(response.status_code, 200)

    def test_exit_list_view(self):
        response = self.client.get(reverse("memberships:exit_list"))
        self.assertEqual(response.status_code, 200)

    def test_reports_view(self):
        response = self.client.get(reverse("memberships:reports"))
        self.assertEqual(response.status_code, 200)

    def test_csv_export(self):
        self._create_member()
        response = self.client.get(reverse("memberships:reports") + "?export=csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_anonymous_user_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse("memberships:directory"))
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_dashboard_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("memberships:dashboard"))
        self.assertEqual(response.status_code, 302)
