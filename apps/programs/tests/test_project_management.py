"""Tests for Phase 16 project management features (WBS, approvals, closure)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.programs.constants import (
    MilestoneApprovalStatus,
    ProjectClosureStatus,
    ProjectReportStatus,
    ProjectStatus,
    WBSNodeStatus,
    WBSNodeType,
)
from apps.programs.models import (
    ChangeRequest,
    Deliverable,
    EvidenceVersion,
    Milestone,
    ProjectResult,
)
from apps.programs.services import (
    ChangeRequestService,
    EvidenceService,
    ProjectAnalyticsService,
    ProjectApprovalService,
    ProjectClosureService,
    ProjectReportService,
    ProjectResultService,
    WbsService,
)

from .base import ProgramTestCase


class WbsServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
            "projects.create",
        )
        self.grant_permissions(self.viewer, "projects.view")
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )

    def test_create_root_node_assigns_reference(self):
        node = WbsService(user=self.owner).create_node(
            self.project,
            node_type=WBSNodeType.PHASE,
            title="Implementation",
            code="1.0",
        )
        self.assertTrue(node.reference_number.startswith("WBS-"))
        self.assertIsNone(node.parent)

    def test_create_requires_permission(self):
        with self.assertRaises(PermissionDenied):
            WbsService(user=self.viewer).create_node(self.project, title="Blocked")

    def test_child_rolls_up_completion(self):
        service = WbsService(user=self.owner)
        parent = service.create_node(
            self.project,
            node_type=WBSNodeType.WORK_PACKAGE,
            title="Package",
            code="2.0",
        )
        service.create_node(
            self.project,
            parent=parent,
            node_type=WBSNodeType.TASK,
            title="Task A",
            completion_percentage=Decimal("100.00"),
            status=WBSNodeStatus.COMPLETED,
        )
        service.create_node(
            self.project,
            parent=parent,
            node_type=WBSNodeType.TASK,
            title="Task B",
            completion_percentage=Decimal("0.00"),
        )
        parent.refresh_from_db()
        self.assertEqual(parent.completion_percentage, Decimal("50.00"))

    def test_cross_project_parent_rejected(self):
        other_program = self.create_program(status="ACTIVE", created_by=self.owner)
        other_project = self.create_project(
            other_program, status="EXECUTION", created_by=self.owner
        )
        parent = WbsService(user=self.owner).create_node(
            other_project, title="Other", code="X"
        )
        with self.assertRaises(ValidationError):
            WbsService(user=self.owner).create_node(
                self.project, parent=parent, title="Broken"
            )

    def test_cycle_detection(self):
        service = WbsService(user=self.owner)
        node = service.create_node(self.project, title="N", code="9")
        with self.assertRaises(ValidationError):
            service.update_node(node, parent=node)


class ProjectApprovalServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )
        self.milestone = Milestone.objects.create(
            project=self.project,
            title="Launch",
            target_date="2026-09-01",
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.deliverable = Deliverable.objects.create(
            project=self.project,
            title="Report",
            created_by=self.owner,
            updated_by=self.owner,
        )

    def test_milestone_submit_approve_reject(self):
        service = ProjectApprovalService(user=self.owner)
        service.submit_milestone(self.milestone)
        self.milestone.refresh_from_db()
        self.assertEqual(
            self.milestone.approval_status, MilestoneApprovalStatus.SUBMITTED
        )
        manager = self.manager
        service = ProjectApprovalService(user=manager)
        service.approve_milestone(self.milestone)
        self.milestone.refresh_from_db()
        self.assertEqual(
            self.milestone.approval_status, MilestoneApprovalStatus.APPROVED
        )
        self.assertEqual(self.milestone.approved_by, manager)

    def test_milestone_self_approval_blocked(self):
        service = ProjectApprovalService(user=self.owner)
        service.submit_milestone(self.milestone)
        with self.assertRaises(ValidationError):
            ProjectApprovalService(user=self.owner).approve_milestone(self.milestone)

    def test_milestone_reject_requires_notes(self):
        service = ProjectApprovalService(user=self.manager)
        ProjectApprovalService(user=self.owner).submit_milestone(self.milestone)
        with self.assertRaises(ValidationError):
            service.reject_milestone(self.milestone, "  ")

    def test_deliverable_approval_workflow(self):
        service = ProjectApprovalService(user=self.owner)
        service.submit_deliverable(self.deliverable)
        self.deliverable.refresh_from_db()
        self.assertEqual(self.deliverable.status, "SUBMITTED")
        ProjectApprovalService(user=self.manager).approve_deliverable(self.deliverable)
        self.deliverable.refresh_from_db()
        self.assertEqual(self.deliverable.status, "APPROVED")


class ChangeRequestServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )
        self.change = ChangeRequest.objects.create(
            project=self.project,
            title="Extend end date",
            reason_for_change="Need more time",
            target_model="Project",
            target_field="end_date",
            proposed_value="2027-01-31",
            status="SUBMITTED",
            created_by=self.owner,
            updated_by=self.owner,
        )

    def test_approve_applies_change_to_project(self):
        ChangeRequestService(user=self.manager).decide(
            self.change, "APPROVED", "Agreed"
        )
        self.change.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.change.status, "APPROVED")
        self.assertEqual(str(self.project.end_date), "2027-01-31")

    def test_creator_cannot_decide(self):
        with self.assertRaises(ValidationError):
            ChangeRequestService(user=self.owner).decide(self.change, "APPROVED")

    def test_reject_does_not_apply(self):
        ChangeRequestService(user=self.manager).decide(self.change, "REJECTED", "No")
        self.change.refresh_from_db()
        self.project.refresh_from_db()
        self.assertEqual(self.change.status, "REJECTED")
        self.assertIsNone(self.project.end_date)


class ProjectClosureServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="COMPLETION", created_by=self.owner
        )

    def test_full_closure_workflow(self):
        service = ProjectClosureService(user=self.owner)
        closure = service.create(
            self.project, completion_verification="All outputs delivered"
        )
        self.assertEqual(closure.status, ProjectClosureStatus.DRAFT)
        service.verify(closure, "Verified")
        closure.refresh_from_db()
        self.assertEqual(closure.status, ProjectClosureStatus.VERIFIED)
        ProjectClosureService(user=self.manager).approve(closure, "Approved")
        closure.refresh_from_db()
        self.assertEqual(closure.status, ProjectClosureStatus.APPROVED)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, ProjectStatus.CLOSURE)

    def test_closure_requires_completion_status(self):
        self.project.status = "EXECUTION"
        self.project.save()
        with self.assertRaises(ValidationError):
            ProjectClosureService(user=self.owner).create(
                self.project, completion_verification="x"
            )

    def test_verifier_cannot_approve(self):
        closure = ProjectClosureService(user=self.owner).create(
            self.project, completion_verification="x"
        )
        ProjectClosureService(user=self.owner).verify(closure)
        with self.assertRaises(ValidationError):
            ProjectClosureService(user=self.owner).approve(closure)


class ProjectResultServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )

    def test_create_result(self):
        result = ProjectResultService(user=self.owner).create_result(
            self.project,
            result_type="OUTPUT",
            code="O1",
            description="Trained youth",
            target="100",
        )
        self.assertEqual(result.project, self.project)
        self.assertIsInstance(result, ProjectResult)

    def test_duplicate_code_rejected(self):
        ProjectResultService(user=self.owner).create_result(
            self.project,
            result_type="OUTPUT",
            code="O1",
            description="First",
        )
        with self.assertRaises(ValidationError):
            ProjectResultService(user=self.owner).create_result(
                self.project,
                result_type="OUTPUT",
                code="O1",
                description="Duplicate",
            )


class EvidenceVersionServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )
        self.evidence = self.project.evidence.create(
            title="Photo evidence",
            created_by=self.owner,
            updated_by=self.owner,
        )

    def test_upload_version_increments(self):
        file = SimpleUploadedFile("v1.pdf", b"%PDF-1.4\n", "application/pdf")
        version = EvidenceService(user=self.owner).upload_version(self.evidence, file)
        self.assertEqual(version.version_number, 2)
        self.evidence.refresh_from_db()
        self.assertEqual(self.evidence.version_number, 2)
        self.assertEqual(
            EvidenceVersion.objects.filter(evidence=self.evidence).count(), 1
        )


class ProjectReportServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )

    def test_report_workflow(self):
        service = ProjectReportService(user=self.owner)
        report = service.create(
            self.project, title="Progress report", report_type="PROGRESS"
        )
        self.assertEqual(report.status, ProjectReportStatus.DRAFT)
        service.submit(report, "On track overall")
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectReportStatus.SUBMITTED)
        ProjectReportService(user=self.manager).approve(report)
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectReportStatus.APPROVED)
        ProjectReportService(user=self.manager).archive(report)
        report.refresh_from_db()
        self.assertEqual(report.status, ProjectReportStatus.ARCHIVED)

    def test_self_approval_blocked(self):
        report = ProjectReportService(user=self.owner).create(
            self.project, title="T", report_type="PROGRESS"
        )
        ProjectReportService(user=self.owner).submit(report)
        with self.assertRaises(ValidationError):
            ProjectReportService(user=self.owner).approve(report)


class ProjectAnalyticsServiceTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.owner,
            "projects.view",
            "projects.update",
        )
        self.grant_permissions(self.manager, "projects.manage")
        self.program = self.create_program(status="ACTIVE", created_by=self.owner)
        self.project = self.create_project(
            self.program, status="EXECUTION", created_by=self.owner
        )

    def test_summarize_returns_expected_keys(self):
        analytics = ProjectAnalyticsService(user=self.owner).summarize(self.project)
        self.assertIn("completion_percentage", analytics)
        self.assertIn("tasks_total", analytics)
        self.assertIn("wbs_nodes", analytics)
        self.assertEqual(analytics["tasks_total"], 0)

    def test_dashboard_data(self):
        data = ProjectAnalyticsService(user=self.owner).project_dashboard_data()
        self.assertGreaterEqual(data["total_projects"], 1)
