"""Permission checks, page rendering, and form workflows for MEAL views."""

from django.urls import reverse

from apps.meal.constants import ComplaintStatus
from apps.meal.models import Complaint, Indicator, MEALStatusHistory, TheoryOfChange

from .base import MEALTestCase


class DashboardViewTests(MEALTestCase):
    def test_anonymous_redirected(self):
        response = self.client.get(reverse("meal:dashboard"))
        self.assertIn(response.status_code, (302, 403))

    def test_unauthorized_user_forbidden(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("meal:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_can_open_dashboard(self):
        self.grant_permissions(self.viewer, "meal.view")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("meal:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MEAL")


class IndicatorViewTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.viewer = self.create_user("indicator_viewer")
        self.grant_permissions(self.viewer, "meal.view")
        self.indicator = self.create_indicator()

    def test_registry_lists_indicators(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("meal:indicator_registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.indicator.code)

    def test_create_requires_create_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("meal:indicator_create"))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_indicator(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("meal:indicator_create"),
            {
                "code": "ind_created_via_view",
                "title": "Created via view",
                "description": "Via form",
                "indicator_type": "OUTPUT",
            },
        )
        self.assertIn(response.status_code, (302, 200))
        self.assertTrue(Indicator.objects.filter(code="ind_created_via_view").exists())

    def test_detail_hidden_from_outside_scope(self):
        self.client.force_login(self.outsider)
        response = self.client.get(
            reverse("meal:indicator_detail", kwargs={"pk": self.indicator.pk})
        )
        self.assertEqual(response.status_code, 403)

    def test_activate_requires_manage_indicators(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("meal:indicator_activate", kwargs={"pk": self.indicator.pk})
        )
        self.assertEqual(response.status_code, 403)


class ComplaintViewTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.manager_viewer = self.create_user("complaint_manager")
        self.grant_permissions(
            self.manager_viewer,
            "meal.view",
            "meal.create",
            "meal.manage_accountability",
            "meal.view_confidential",
        )
        self.complaint = self.create_complaint(is_confidential=True)

    def test_confidential_complaint_hidden_without_permission(self):
        self.grant_permissions(self.viewer, "meal.view")
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("meal:complaint_detail", kwargs={"pk": self.complaint.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_manager_can_resolve_complaint(self):
        self.client.force_login(self.manager_viewer)
        response = self.client.post(
            reverse("meal:complaint_resolve", kwargs={"pk": self.complaint.pk}),
            {"resolution": "Investigated and closed."},
        )
        self.assertIn(response.status_code, (302, 200))
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, ComplaintStatus.RESOLVED)

    def test_complaint_create_persists(self):
        self.client.force_login(self.manager_viewer)
        response = self.client.post(
            reverse("meal:complaint_create"),
            {
                "description": "Created via view",
                "is_confidential": "on",
                "submission_date": "2026-01-05",
                "priority": "MEDIUM",
            },
        )
        self.assertIn(response.status_code, (302, 200))
        self.assertTrue(
            Complaint.objects.filter(description="Created via view").exists()
        )


class TransitionViewTests(MEALTestCase):
    def setUp(self):
        super().setUp()
        self.meal_officer = self.create_user("transition_officer")
        self.grant_permissions(
            self.meal_officer, "meal.view", "meal.submit", "meal.manage_frameworks"
        )
        self.toc = TheoryOfChange.objects.create(
            reference_number="TOC-VIEW-0001",
            title="Strategic ToC",
            strategic_goal="Goal",
            created_by=self.manager,
            updated_by=self.manager,
        )

    def test_transition_posts_update_status(self):
        self.client.force_login(self.meal_officer)
        response = self.client.post(
            reverse("meal:theory_of_change_actions", kwargs={"pk": self.toc.pk}),
            {"to_status": "SUBMITTED", "notes": "Ready for review"},
        )
        self.assertIn(response.status_code, (302, 200))
        self.toc.refresh_from_db()
        self.assertEqual(self.toc.status, "SUBMITTED")
        self.assertTrue(
            MEALStatusHistory.objects.filter(
                entity_type="TheoryOfChange", entity_id=str(self.toc.pk)
            ).exists()
        )
