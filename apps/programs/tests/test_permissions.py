"""Permission-aware selector tests for program and project records."""

from apps.programs.models import Program, Project
from apps.programs.selectors import (
    user_can_access_program,
    user_can_access_project,
    visible_programs,
    visible_projects,
)

from .base import ProgramTestCase


class VisibleProgramSelectorTests(ProgramTestCase):
    def test_module_manager_sees_all_non_archived_records(self):
        program = self.create_program()
        archived = self.create_program(is_archived=True)
        visible_ids = set(visible_programs(self.manager).values_list("pk", flat=True))
        self.assertEqual(visible_ids, {program.pk})
        self.assertIn(
            archived.pk,
            visible_programs(self.manager, include_archived=True).values_list(
                "pk", flat=True
            ),
        )

    def test_viewer_sees_created_managed_and_teamed_records(self):
        created = self.create_program(created_by=self.viewer)
        managed = self.create_program(program_manager=self.viewer)
        teamed = self.create_program()
        teamed.team_members.create(user=self.viewer, role_title="Officer")
        self.create_program()
        self.grant_permissions(self.viewer, "programmes.view")
        self.assertEqual(
            set(visible_programs(self.viewer).values_list("pk", flat=True)),
            {created.pk, managed.pk, teamed.pk},
        )

    def test_no_permission_fails_closed(self):
        program = self.create_program(program_manager=self.outsider)
        self.assertFalse(visible_programs(self.outsider).exists())
        self.assertFalse(user_can_access_program(self.outsider, program))

    def test_anonymous_user_never_sees_programs(self):
        self.create_program()
        self.assertFalse(visible_programs(None).exists())

    def test_view_permission_alone_reveals_manager_run_programs(self):
        program = self.create_program(program_manager=self.manager)
        self.grant_permissions(self.viewer, "programmes.view")
        self.assertEqual(
            list(visible_programs(self.viewer).values_list("pk", flat=True)),
            [program.pk],
        )


class VisibleProjectSelectorTests(ProgramTestCase):
    def test_module_manager_sees_all_non_archived_projects(self):
        project = self.create_project()
        archived = self.create_project(is_archived=True)
        visible_ids = set(visible_projects(self.manager).values_list("pk", flat=True))
        self.assertEqual(visible_ids, {project.pk})
        self.assertIn(
            archived.pk,
            visible_projects(self.manager, include_archived=True).values_list(
                "pk", flat=True
            ),
        )

    def test_project_visibility_is_scoped_by_program_visibility(self):
        owned_program = self.create_program(
            created_by=self.viewer, program_manager=self.manager
        )
        hidden_program = self.create_program(created_by=self.manager)
        owned_project = self.create_project(owned_program, created_by=self.viewer)
        self.create_project(hidden_program)
        self.grant_permissions(self.viewer, "programmes.view", "projects.view")
        self.assertEqual(
            set(visible_projects(self.viewer).values_list("pk", flat=True)),
            {owned_project.pk},
        )

    def test_project_manager_sees_own_projects(self):
        program = self.create_program(program_manager=self.manager)
        assigned = self.create_project(program, project_manager=self.viewer)
        self.grant_permissions(self.viewer, "projects.view")
        self.assertEqual(
            list(visible_projects(self.viewer).values_list("pk", flat=True)),
            [assigned.pk],
        )

    def test_no_permission_fails_closed(self):
        project = self.create_project()
        self.assertFalse(visible_projects(self.outsider).exists())
        self.assertFalse(user_can_access_project(self.outsider, project))

    def test_project_access_is_false_when_project_is_none(self):
        self.assertFalse(user_can_access_project(self.manager, None))
        self.assertFalse(user_can_access_program(self.manager, None))


class ProgramScopedAccessTests(ProgramTestCase):
    def test_archived_record_requires_explicit_include(self):
        program = self.create_program(
            created_by=self.manager, program_manager=self.viewer
        )
        project = self.create_project(program, created_by=self.manager)
        self.grant_permissions(self.viewer, "programmes.view", "projects.view")
        self.assertTrue(user_can_access_program(self.viewer, program))
        self.assertTrue(user_can_access_project(self.viewer, project))
        program.is_archived = True
        program.save(update_fields=["is_archived"])
        self.assertFalse(user_can_access_program(self.viewer, program))
        self.assertFalse(user_can_access_project(self.viewer, project))
        self.assertTrue(
            user_can_access_program(self.viewer, program, include_archived=True)
        )

    def test_scope_checks_refuse_deleted_records(self):
        program = self.create_program(
            created_by=self.manager, program_manager=self.viewer
        )
        Program.all_objects.filter(pk=program.pk).update(is_deleted=True)
        self.assertFalse(user_can_access_program(self.manager, program))

    def test_project_is_removed_when_program_is_hidden(self):
        program = self.create_program(created_by=self.manager)
        project = self.create_project(program, created_by=self.manager)
        self.grant_permissions(self.viewer, "programmes.view", "projects.view")
        self.assertFalse(user_can_access_project(self.viewer, project))
        project = Project.objects.get(pk=project.pk)
        self.assertFalse(visible_projects(self.viewer).filter(pk=project.pk).exists())
