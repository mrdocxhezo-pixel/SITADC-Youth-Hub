"""Permission checks, page rendering, and form workflows for register views."""

from django.urls import reverse

from apps.registers.constants import RegisterApprovalStatus
from apps.registers.models import RegisterCategory, RegisterEntry

from .base import RegistersTestCase


class DashboardViewTests(RegistersTestCase):
    def test_anonymous_redirected(self):
        response = self.client.get(reverse("registers:dashboard"))
        self.assertIn(response.status_code, (302, 403))

    def test_unauthorized_user_forbidden(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("registers:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_can_open_dashboard(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Organizational Registers")


class CategoryViewTests(RegistersTestCase):
    def test_list_shows_categories(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:category_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.category.name)

    def test_create_requires_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:category_create"))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_create_category(self):
        self.client.force_login(self.manager)
        response = self.client.post(
            reverse("registers:category_create"),
            {
                "name": "Volunteer",
                "code": "volunteer",
                "number_prefix": "VOL",
                "default_confidentiality": "INTERNAL",
                "retention_policy": "PERMANENT",
                "sort_order": 0,
                "is_active": "on",
            },
        )
        self.assertIn(response.status_code, (302, 200))
        self.assertTrue(RegisterCategory.objects.filter(code="volunteer").exists())


class RegisterViewTests(RegistersTestCase):
    def test_register_list_lists(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:register_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.register.name)

    def test_register_detail(self):
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("registers:register_detail", kwargs={"pk": self.register.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.register.reference_number)

    def test_create_requires_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:register_create"))
        self.assertEqual(response.status_code, 403)

    def test_archive_requires_archive_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("registers:register_archive", kwargs={"pk": self.register.pk})
        )
        self.assertEqual(response.status_code, 403)


class EntryViewTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.entry = self.create_register_entry()

    def test_entry_list_lists(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:entry_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.entry.title)

    def test_entry_detail(self):
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("registers:entry_detail", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.entry.reference_number)

    def test_confidential_entry_hidden_without_permission(self):
        confidential = self.make_confidential_entry()
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("registers:entry_detail", kwargs={"pk": confidential.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_entry_create_persists(self):
        self.client.force_login(self.officer)
        response = self.client.post(
            reverse(
                "registers:entry_create",
                kwargs={"register_pk": self.register.pk},
            ),
            {
                "register": self.register.pk,
                "title": "Entry via view",
                "description": "From form",
                "owner": self.officer.pk,
                "confidentiality": "INTERNAL",
            },
        )
        self.assertIn(response.status_code, (302, 200))
        self.assertTrue(RegisterEntry.objects.filter(title="Entry via view").exists())

    def test_submit_transition_view(self):
        self.client.force_login(self.officer)
        response = self.client.post(
            reverse("registers:entry_submit", kwargs={"pk": self.entry.pk}),
            {"comment": "Ready for review"},
        )
        self.assertIn(response.status_code, (302, 200))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.approval_status, RegisterApprovalStatus.SUBMITTED)

    def test_approve_workflow_via_views(self):
        self.client.force_login(self.officer)
        self.client.post(
            reverse("registers:entry_submit", kwargs={"pk": self.entry.pk})
        )
        self.client.post(
            reverse("registers:entry_start_review", kwargs={"pk": self.entry.pk})
        )
        response = self.client.post(
            reverse("registers:entry_approve", kwargs={"pk": self.entry.pk}),
            {"comment": "Approved"},
        )
        self.assertIn(response.status_code, (302, 200))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.approval_status, RegisterApprovalStatus.APPROVED)

    def test_return_entry(self):
        self.client.force_login(self.officer)
        self.client.post(
            reverse("registers:entry_submit", kwargs={"pk": self.entry.pk})
        )
        self.client.post(
            reverse("registers:entry_start_review", kwargs={"pk": self.entry.pk})
        )
        response = self.client.post(
            reverse("registers:entry_return", kwargs={"pk": self.entry.pk}),
            {"comment": "Please fix"},
        )
        self.assertIn(response.status_code, (302, 200))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.approval_status, RegisterApprovalStatus.RETURNED)

    def test_reject_entry(self):
        self.client.force_login(self.officer)
        self.client.post(
            reverse("registers:entry_submit", kwargs={"pk": self.entry.pk})
        )
        self.client.post(
            reverse("registers:entry_start_review", kwargs={"pk": self.entry.pk})
        )
        response = self.client.post(
            reverse("registers:entry_reject", kwargs={"pk": self.entry.pk}),
            {"comment": "Rejected"},
        )
        self.assertIn(response.status_code, (302, 200))
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.approval_status, RegisterApprovalStatus.REJECTED)

    def test_archive_entry(self):
        self.client.force_login(self.officer)
        response = self.client.post(
            reverse("registers:entry_archive", kwargs={"pk": self.entry.pk})
        )
        self.assertIn(response.status_code, (302, 200))
        self.entry.refresh_from_db()
        self.assertTrue(self.entry.is_archived)

    def test_export_csv_endpoint(self):
        self.client.force_login(self.officer)
        response = self.client.get(reverse("registers:export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")


class TemplateViewTests(RegistersTestCase):
    def test_template_list(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:template_list"))
        self.assertEqual(response.status_code, 200)

    def test_template_create_requires_permission(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("registers:template_create"))
        self.assertEqual(response.status_code, 403)
