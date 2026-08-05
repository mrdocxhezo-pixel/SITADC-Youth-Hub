"""View tests for the program and project module."""

from __future__ import annotations

from django.urls import reverse

from apps.programs.constants import ProgramStatus
from apps.programs.models import Program, Project, WorkPlan

from .base import ProgramTestCase


class ProgramViewTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "programmes.view",
            "programmes.create",
            "programmes.update",
            "programmes.archive",
            "programmes.restore",
        )
        self.grant_permissions(self.viewer, "programmes.view")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("programs:dashboard"))
        self.assertRedirects(response, f"{reverse('core:login')}?next=/programs/")

    def test_dashboard_requires_permission(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("programs:dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_dashboard_lists_visible_programs(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("programs:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Programs")

    def test_program_directory(self):
        program = self.create_program(created_by=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get(reverse("programs:program_directory"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, program.title)

    def test_create_program_via_view(self):
        self.client.force_login(self.owner)
        category = self.taxonomy("CATEGORY")
        response = self.client.post(
            reverse("programs:program_create"),
            {
                "title": "Created Via View",
                "category": category.pk,
                "description": "from form",
            },
        )
        self.assertEqual(response.status_code, 302)
        program = Program.objects.get(title="Created Via View")
        self.assertTrue(program.reference_number.startswith("PRG-"))

    def test_create_program_invalid_form(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse("programs:program_create"), {"title": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "is-invalid", html=False)

    def test_program_profile(self):
        program = self.create_program(created_by=self.owner)
        self.client.force_login(self.owner)
        response = self.client.get(
            reverse("programs:program_profile", kwargs={"pk": program.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, program.title)

    def test_program_profile_outside_scope(self):
        program = self.create_program(created_by=self.manager)
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("programs:program_profile", kwargs={"pk": program.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_status_transition_via_view(self):
        program = self.create_program(created_by=self.owner)
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("programs:program_status", kwargs={"pk": program.pk}),
            {"new_status": ProgramStatus.PROPOSED, "reason": "via view"},
        )
        self.assertEqual(response.status_code, 302)
        program.refresh_from_db()
        self.assertEqual(program.status, ProgramStatus.PROPOSED)

    def test_archive_restore_via_view(self):
        program = self.create_program(created_by=self.owner)
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("programs:program_archive", kwargs={"pk": program.pk}),
            {"reason": "closing"},
        )
        self.assertEqual(response.status_code, 302)
        program.refresh_from_db()
        self.assertTrue(program.is_archived)
        response = self.client.post(
            reverse("programs:program_restore", kwargs={"pk": program.pk}),
            {"reason": "reopen"},
        )
        self.assertEqual(response.status_code, 302)
        program.refresh_from_db()
        self.assertFalse(program.is_archived)

    def test_work_plan_child_view(self):
        program = self.create_program(
            created_by=self.owner, status=ProgramStatus.ACTIVE
        )
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("programs:work_plans", kwargs={"pk": program.pk}),
            {
                "title": "Annual Plan",
                "reporting_period": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(WorkPlan.objects.filter(program=program).exists())

    def test_child_view_requires_write_permission(self):
        program = self.create_program(
            created_by=self.owner, status=ProgramStatus.ACTIVE
        )
        self.client.force_login(self.viewer)
        response = self.client.post(
            reverse("programs:work_plans", kwargs={"pk": program.pk}),
            {
                "title": "Annual Plan",
                "reporting_period": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        self.assertEqual(response.status_code, 403)


class ProjectViewTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "programmes.view",
            "programmes.update",
            "projects.view",
            "projects.create",
            "projects.update",
        )
        self.client.force_login(self.owner)
        self.program = self.create_program(
            created_by=self.owner, status=ProgramStatus.ACTIVE
        )

    def test_project_directory(self):
        project = self.create_project(self.program, created_by=self.owner)
        response = self.client.get(reverse("programs:project_directory"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.title)

    def test_create_project_via_view(self):
        response = self.client.post(
            reverse("programs:project_create"),
            {
                "program": self.program.pk,
                "title": "Created Project",
                "category": self.taxonomy("PROJECT_CATEGORY").pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Project.objects.filter(title="Created Project").exists())

    def test_project_profile(self):
        project = self.create_project(self.program, created_by=self.owner)
        response = self.client.get(
            reverse("programs:project_profile", kwargs={"pk": project.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, project.title)


class ProgramExportViewTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "programmes.view",
            "programmes.export",
            "projects.view",
            "projects.export",
        )
        self.client.force_login(self.owner)

    def test_program_register_csv(self):
        self.create_program(created_by=self.owner)
        response = self.client.get(reverse("programs:program_register_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("no-store", response["Cache-Control"])

    def test_project_register_csv(self):
        program = self.create_program(
            created_by=self.owner, status=ProgramStatus.ACTIVE
        )
        self.create_project(program, created_by=self.owner)
        response = self.client.get(reverse("programs:project_register_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

    def test_export_requires_export_permission(self):
        self.client.force_login(self.viewer)
        self.grant_permissions(self.viewer, "programmes.view")
        response = self.client.get(reverse("programs:program_register_export"))
        self.assertEqual(response.status_code, 403)
