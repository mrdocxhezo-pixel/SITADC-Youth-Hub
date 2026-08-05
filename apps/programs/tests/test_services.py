"""Service layer tests for program and project management."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError

from apps.programs.constants import ProgramStatus, ProjectStatus
from apps.programs.models import (
    Activity,
    ChangeRequest,
    Deliverable,
    Issue,
    Program,
    ProgramStatusHistory,
    Project,
    ProjectStatusHistory,
    Task,
    WorkPlan,
)
from apps.programs.services import (
    PROGRAM_TRANSITIONS,
    ProgramChildRecordService,
    ProgramDocumentService,
    ProgramService,
    ProjectService,
)

from .base import ProgramTestCase


class ProgramServiceTests(ProgramTestCase):
    """Manager (manage) happy paths; owner = writer, viewer = read-only."""

    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "programmes.view",
            "programmes.create",
            "programmes.update",
            "programmes.delete",
            "programmes.archive",
            "programmes.restore",
        )
        self.grant_permissions(self.viewer, "programmes.view")

    def test_create_program_assigns_reference_and_history(self):
        program = ProgramService(user=self.manager).create(
            title="Digital Skills",
            category=self.taxonomy("CATEGORY"),
        )
        self.assertTrue(program.reference_number.startswith("PRG-"))
        self.assertEqual(program.status, ProgramStatus.DRAFT)
        self.assertEqual(program.created_by, self.manager)
        self.assertEqual(
            ProgramStatusHistory.objects.filter(program=program).count(), 1
        )

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            ProgramService(user=self.viewer).create(title="No Access")

    def test_create_rejects_unsupported_fields(self):
        with self.assertRaises(ValidationError):
            ProgramService(user=self.manager).create(title="Bad", made_up_field="x")

    def test_update_changes_field(self):
        program = self.create_program(created_by=self.owner)
        ProgramService(user=self.owner).update(program, description="Updated")
        program.refresh_from_db()
        self.assertEqual(program.description, "Updated")

    def test_update_outside_scope_denied(self):
        program = self.create_program(created_by=self.manager)
        with self.assertRaises(PermissionDenied):
            ProgramService(user=self.owner).update(program, description="x")

    def test_valid_transition_records_history(self):
        program = self.create_program(created_by=self.owner)
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PROPOSED, "moving forward"
        )
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PENDING_APPROVAL, "submitting"
        )
        program.refresh_from_db()
        self.assertEqual(program.status, ProgramStatus.PENDING_APPROVAL)
        self.assertEqual(
            ProgramStatusHistory.objects.filter(program=program).count(), 2
        )

    def test_invalid_transition_rejected(self):
        program = self.create_program(created_by=self.owner)
        with self.assertRaises(ValidationError) as ctx:
            ProgramService(user=self.owner).change_status(
                program, ProgramStatus.ACTIVE, "skip ahead"
            )
        self.assertEqual(ctx.exception.code, "invalid_program_transition")

    def test_transition_requires_reason(self):
        program = self.create_program(created_by=self.owner)
        with self.assertRaises(ValidationError):
            ProgramService(user=self.owner).change_status(
                program, ProgramStatus.PROPOSED, "   "
            )

    def test_self_approval_blocked(self):
        program = self.create_program(created_by=self.owner)
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PROPOSED, "advance"
        )
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PENDING_APPROVAL, "submit"
        )
        with self.assertRaises(ValidationError) as ctx:
            ProgramService(user=self.owner).change_status(
                program, ProgramStatus.APPROVED, "self approve"
            )
        self.assertEqual(ctx.exception.code, "program_self_approval")

    def test_approval_by_other_user_sets_metadata(self):
        program = self.create_program(created_by=self.owner)
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PROPOSED, "advance"
        )
        ProgramService(user=self.owner).change_status(
            program, ProgramStatus.PENDING_APPROVAL, "submit"
        )
        ProgramService(user=self.manager).change_status(
            program, ProgramStatus.APPROVED, "approved by manager"
        )
        program.refresh_from_db()
        self.assertEqual(program.status, ProgramStatus.APPROVED)
        self.assertEqual(program.approved_by, self.manager)
        self.assertIsNotNone(program.approved_at)

    def test_archive_restore_cycle(self):
        program = self.create_program(created_by=self.owner)
        service = ProgramService(user=self.owner)
        service.archive(program, "wind down")
        program.refresh_from_db()
        self.assertTrue(program.is_archived)
        self.assertEqual(program.status, ProgramStatus.ARCHIVED)
        service.restore(program, "revive")
        program.refresh_from_db()
        self.assertFalse(program.is_archived)
        self.assertEqual(program.status, ProgramStatus.DRAFT)

    def test_archive_requires_reason(self):
        program = self.create_program(created_by=self.owner)
        with self.assertRaises(ValidationError):
            ProgramService(user=self.owner).archive(program, "  ")

    def test_soft_delete_hides_program(self):
        program = self.create_program(created_by=self.owner)
        ProgramService(user=self.owner).soft_delete(program)
        self.assertFalse(Program.objects.filter(pk=program.pk).exists())
        self.assertTrue(Program.all_objects.get(pk=program.pk).is_deleted)

    def test_all_transitions_use_valid_statuses(self):
        valid = {choice[0] for choice in ProgramStatus.choices}
        for source, targets in PROGRAM_TRANSITIONS.items():
            self.assertIn(source, valid)
            for target in targets:
                self.assertIn(target, valid)


class ProjectServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.create",
            "projects.update",
            "projects.delete",
            "projects.archive",
            "projects.restore",
        )
        self.grant_permissions(self.viewer, "projects.view")
        self.program = self.create_program(
            status=ProgramStatus.ACTIVE, created_by=self.owner
        )
        self.grant_permissions(
            self.owner,
            "programmes.view",
        )

    def test_create_project_under_active_program(self):
        project = ProjectService(user=self.owner).create(
            self.program,
            title="Wash Campaign",
            category=self.taxonomy("PROJECT_CATEGORY"),
        )
        self.assertTrue(project.reference_number.startswith("PRJ-"))
        self.assertEqual(project.status, ProjectStatus.CONCEPT)
        self.assertEqual(
            ProjectStatusHistory.objects.filter(project=project).count(), 1
        )

    def test_create_under_non_active_program_rejected(self):
        draft = self.create_program(status=ProgramStatus.DRAFT, created_by=self.owner)
        with self.assertRaises(ValidationError):
            ProjectService(user=self.owner).create(draft, title="Too Early")

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            ProjectService(user=self.viewer).create(self.program, title="No Access")

    def test_project_self_approval_blocked(self):
        project = ProjectService(user=self.owner).create(self.program, title="Campaign")
        project = Project.objects.get(pk=project.pk)
        ProjectService(user=self.owner).change_status(
            project, ProjectStatus.PROPOSAL, "to proposal"
        )
        ProjectService(user=self.owner).change_status(
            project, ProjectStatus.PLANNING, "to planning"
        )
        with self.assertRaises(ValidationError) as ctx:
            ProjectService(user=self.owner).change_status(
                project, ProjectStatus.APPROVAL, "self approve"
            )
        self.assertEqual(ctx.exception.code, "project_self_approval")

    def test_project_archive_restore(self):
        project = self.create_project(self.program, created_by=self.owner)
        service = ProjectService(user=self.owner)
        service.archive(project, "closed out")
        project.refresh_from_db()
        self.assertTrue(project.is_archived)
        service.restore(project, "reopen")
        project.refresh_from_db()
        self.assertEqual(project.status, ProjectStatus.CONCEPT)


class ProgramChildRecordServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "programmes.view",
            "programmes.update",
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.viewer, "programmes.view", "projects.view")
        self.program = self.create_program(
            status=ProgramStatus.ACTIVE, created_by=self.owner
        )
        self.project = self.create_project(self.program, created_by=self.owner)

    def test_create_work_plan(self):
        plan = ProgramChildRecordService(user=self.owner).create(
            WorkPlan,
            program=self.program,
            fields={
                "title": "Annual Plan",
                "reporting_period": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        self.assertTrue(plan.reference_number.startswith("WPL-"))
        self.assertEqual(plan.program_id, self.program.pk)

    def test_create_activity_with_task(self):
        plan = ProgramChildRecordService(user=self.owner).create(
            WorkPlan,
            program=self.program,
            fields={
                "title": "Plan",
                "reporting_period": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        activity = ProgramChildRecordService(user=self.owner).create(
            Activity,
            project=self.project,
            fields={
                "work_plan": plan,
                "title": "Training",
                "planned_date": "2026-03-01",
            },
        )
        task = ProgramChildRecordService(user=self.owner).create(
            Task,
            project=self.project,
            fields={"activity": activity, "title": "Prepare materials"},
        )
        self.assertTrue(activity.reference_number.startswith("ACT-"))
        self.assertTrue(task.reference_number.startswith("TSK-"))

    def test_create_issue_change_deliverable(self):
        service = ProgramChildRecordService(user=self.owner)
        issue = service.create(
            Issue,
            project=self.project,
            fields={"title": "Flood", "description": "Road cut"},
        )
        change = service.create(
            ChangeRequest,
            project=self.project,
            fields={"title": "Scope tweak", "reason_for_change": "Funding"},
        )
        deliverable = service.create(
            Deliverable,
            project=self.project,
            fields={"title": "Baseline Report"},
        )
        self.assertTrue(issue.reference_number.startswith("ISS-"))
        self.assertTrue(change.reference_number.startswith("CHG-"))
        self.assertTrue(deliverable.reference_number.startswith("DLV-"))

    def test_requires_parent(self):
        with self.assertRaises(ValidationError):
            ProgramChildRecordService(user=self.owner).create(
                Issue,
                program=None,
                project=None,
                fields={"title": "x", "description": "y"},
            )

    def test_requires_write_permission(self):
        with self.assertRaises(PermissionDenied):
            ProgramChildRecordService(user=self.viewer).create(
                Issue,
                project=self.project,
                fields={"title": "x", "description": "y"},
            )

    def test_update_child_record(self):
        plan = ProgramChildRecordService(user=self.owner).create(
            WorkPlan,
            program=self.program,
            fields={
                "title": "Plan",
                "reporting_period": "2026",
                "start_date": "2026-01-01",
                "end_date": "2026-12-31",
            },
        )
        updated = ProgramChildRecordService(user=self.owner).update(
            plan, {"title": "Revised Plan"}
        )
        self.assertEqual(updated.title, "Revised Plan")

    def test_reference_numbers_are_unique_across_types(self):
        service = ProgramChildRecordService(user=self.owner)
        issue = service.create(
            Issue,
            project=self.project,
            fields={"title": "Issue", "description": "x"},
        )
        change = service.create(
            ChangeRequest,
            project=self.project,
            fields={"title": "Change", "reason_for_change": "y"},
        )
        self.assertNotEqual(issue.reference_number, change.reference_number)


class ProgramDocumentServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(self.owner, "programmes.view", "programmes.update")
        self.grant_permissions(self.viewer, "programmes.view")
        self.program = self.create_program(created_by=self.owner)

    def test_upload_document(self):
        document = ProgramDocumentService(user=self.owner).upload(
            self.program,
            None,
            title="Proposal",
            file=self.pdf_upload(),
        )
        self.assertEqual(document.program_id, self.program.pk)
        self.assertEqual(document.status, "CURRENT")

    def test_upload_requires_parent(self):
        with self.assertRaises(ValidationError):
            ProgramDocumentService(user=self.owner).upload(
                None, None, title="Orphan", file=self.pdf_upload()
            )

    def test_upload_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            ProgramDocumentService(user=self.viewer).upload(
                self.program, None, title="Proposal", file=self.pdf_upload()
            )

    def test_archive_document(self):
        document = ProgramDocumentService(user=self.owner).upload(
            self.program, None, title="Proposal", file=self.pdf_upload()
        )
        ProgramDocumentService(user=self.owner).archive(document)
        document.refresh_from_db()
        self.assertEqual(document.status, "ARCHIVED")

    def test_model_delete_is_protected(self):
        document = ProgramDocumentService(user=self.owner).upload(
            self.program, None, title="Proposal", file=self.pdf_upload()
        )
        with self.assertRaises(Exception) as ctx:
            document.delete()
        self.assertIn("archived", str(ctx.exception).lower())
