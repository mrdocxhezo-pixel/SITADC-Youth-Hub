"""Model and validator tests for the program module."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.programs.models import (
    Activity,
    BeneficiaryRecord,
    Deliverable,
    Issue,
    Program,
    ProgramDocument,
    ProgramReferenceData,
    WorkPlan,
)

from .base import ProgramTestCase


class ProgramReferenceDataTests(ProgramTestCase):
    def test_kind_code_uniqueness(self):
        with self.assertRaises(IntegrityError):
            ProgramReferenceData.objects.create(
                kind="CATEGORY", code="education-digital", name="Duplicate"
            )


class ProgramModelTests(ProgramTestCase):
    def test_budget_remaining_and_utilization(self):
        program = self.create_program(
            budget_approved=Decimal("1000"), budget_utilized=Decimal("250")
        )
        self.assertEqual(program.budget_remaining, Decimal("750"))
        self.assertEqual(program.budget_utilization_percentage, Decimal("25.00"))

    def test_zero_budget_utilization_returns_zero(self):
        program = self.create_program(
            budget_approved=Decimal("0"), budget_utilized=Decimal("0")
        )
        self.assertEqual(program.budget_utilization_percentage, Decimal("0.00"))

    def test_invalid_date_range_rejected(self):
        program = self.create_program(start_date="2026-01-01", end_date="2025-01-01")
        with self.assertRaises(ValidationError):
            program.full_clean()

    def test_utilized_exceeds_approved_rejected(self):
        program = self.create_program(
            budget_approved=Decimal("100"), budget_utilized=Decimal("200")
        )
        with self.assertRaises(ValidationError):
            program.full_clean()

    def test_manager_excludes_archived(self):
        self.create_program()
        self.create_program()
        archived = self.create_program()
        archived.is_archived = True
        archived.save()
        self.assertEqual(Program.objects.count(), 2)
        self.assertEqual(Program.all_objects.count(), 3)

    def test_soft_delete_hides_record(self):
        program = self.create_program()
        program.delete(deleted_by=self.manager)
        self.assertTrue(Program.all_objects.get(pk=program.pk).is_deleted)
        self.assertEqual(Program.objects.count(), 0)


class ProjectModelTests(ProgramTestCase):
    def test_project_within_program_dates(self):
        program = self.create_program(start_date="2026-01-01", end_date="2026-12-31")
        project = self.create_project(
            program=program, start_date="2025-06-01", end_date="2026-06-01"
        )
        with self.assertRaises(ValidationError):
            project.full_clean()

    def test_project_budget_remaining(self):
        project = self.create_project(
            budget_approved=Decimal("500"), budget_utilized=Decimal("100")
        )
        self.assertEqual(project.budget_remaining, Decimal("400"))


class ChildRecordModelTests(ProgramTestCase):
    def test_work_plan_requires_parent(self):
        with self.assertRaises(ValidationError):
            WorkPlan(
                title="Orphan plan",
                reporting_period="2026 Q1",
                start_date="2026-01-01",
                end_date="2026-03-31",
            ).full_clean()

    def test_activity_requires_work_plan(self):
        work_plan = WorkPlan.objects.create(
            program=self.create_program(),
            reference_number="WPL-TEST-0001",
            title="Plan",
            reporting_period="2026 Q1",
            start_date="2026-01-01",
            end_date="2026-03-31",
        )
        activity = Activity(
            work_plan=work_plan,
            reference_number="ACT-TEST-0001",
            title="Activity",
            planned_date="2026-01-10",
        )
        activity.full_clean()
        self.assertEqual(activity.work_plan_id, work_plan.pk)

    def test_issue_requires_parent(self):
        issue = Issue(
            reference_number="ISS-TEST-0001", title="No parent", description="x"
        )
        with self.assertRaises(ValidationError):
            issue.full_clean()

    def test_deliverable_due_after_completion_rejected(self):
        project = self.create_project()
        deliverable = Deliverable(
            project=project,
            reference_number="DLV-TEST-0001",
            title="Report",
            due_date="2026-05-01",
            completion_date="2026-04-01",
        )
        with self.assertRaises(ValidationError):
            deliverable.full_clean()

    def test_beneficiary_requires_parent(self):
        beneficiary = BeneficiaryRecord(reference_number="BNF-TEST-0001", name="Group")
        with self.assertRaises(ValidationError):
            beneficiary.full_clean()


class ProgramDocumentModelTests(ProgramTestCase):
    def test_delete_raises_protected_error(self):
        program = self.create_program()
        document = ProgramDocument.objects.create(
            program=program,
            title="Evidence",
            file="programs/documents/x.pdf",
            original_filename="x.pdf",
            file_size=20,
        )
        with self.assertRaises(ValidationError):
            document.delete()


class ValidatorTests(TestCase):
    def test_percentage_bounds(self):
        from apps.programs.validators import validate_percentage

        validate_percentage(Decimal("0.00"))
        validate_percentage(Decimal("100.00"))
        with self.assertRaises(ValidationError):
            validate_percentage(Decimal("101"))
        with self.assertRaises(ValidationError):
            validate_percentage(Decimal("-1"))

    def test_positive_amount(self):
        from apps.programs.validators import validate_positive_amount

        validate_positive_amount(Decimal("0"))
        with self.assertRaises(ValidationError):
            validate_positive_amount(Decimal("-5"))
