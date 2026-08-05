"""Stakeholder seed, validation, deadline, and expiry command tests."""

from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.references.models import ReferenceNumberScheme
from apps.stakeholders.constants import ActionStatus, AgreementStatus
from apps.stakeholders.models import (
    StakeholderActionItem,
    StakeholderPerformanceDimension,
    StakeholderReferenceData,
)

from .base import StakeholderTestCase


class StakeholderSeedCommandTests(StakeholderTestCase):
    def test_seed_command_is_idempotent(self):
        initial_counts = (
            StakeholderReferenceData.objects.count(),
            StakeholderPerformanceDimension.objects.count(),
            ReferenceNumberScheme.objects.filter(module="partners").count(),
        )
        output = StringIO()
        call_command("seed_stakeholder_reference_data", stdout=output)
        call_command("seed_stakeholder_reference_data", stdout=output)
        self.assertEqual(
            (
                StakeholderReferenceData.objects.count(),
                StakeholderPerformanceDimension.objects.count(),
                ReferenceNumberScheme.objects.filter(module="partners").count(),
            ),
            initial_counts,
        )
        self.assertIn("0 reference rows", output.getvalue())


class StakeholderCheckCommandTests(StakeholderTestCase):
    def test_validate_command_accepts_valid_records(self):
        self.create_stakeholder()
        output = StringIO()
        call_command("validate_stakeholder_records", stdout=output)
        self.assertIn("Validated 1 stakeholder records successfully", output.getvalue())

    def test_validate_command_reports_invalid_records(self):
        self.create_stakeholder(
            date_established=timezone.localdate() + timedelta(days=1)
        )
        with self.assertRaises(CommandError):
            call_command(
                "validate_stakeholder_records", stdout=StringIO(), stderr=StringIO()
            )

    def test_overdue_action_command_reports_and_marks_through_service(self):
        stakeholder = self.create_stakeholder(created_by=self.owner)
        action = StakeholderActionItem.objects.create(
            stakeholder=stakeholder,
            title="Late follow-up",
            due_date=timezone.localdate() - timedelta(days=1),
            assigned_to=self.owner,
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.grant_permissions(self.owner, "partners.view", "partners.manage_actions")
        output = StringIO()
        call_command(
            "check_overdue_stakeholder_actions",
            "--mark-overdue",
            f"--actor-email={self.owner.email}",
            stdout=output,
        )
        action.refresh_from_db()
        self.assertEqual(action.status, ActionStatus.OVERDUE)
        self.assertIn("Marked 1 actions overdue", output.getvalue())

    def test_overdue_mark_requires_actor(self):
        with self.assertRaises(CommandError):
            call_command(
                "check_overdue_stakeholder_actions",
                "--mark-overdue",
                stdout=StringIO(),
            )

    def test_expiring_agreement_command_reports_and_marks_elapsed_active(self):
        stakeholder = self.create_stakeholder(created_by=self.owner)
        agreement = self.create_agreement(
            stakeholder,
            status=AgreementStatus.ACTIVE,
            effective_date=date(2025, 1, 1),
            expiry_date=timezone.localdate() - timedelta(days=1),
            approved_by=self.owner,
            approved_at=timezone.now(),
            created_by=self.owner,
            updated_by=self.owner,
        )
        self.grant_permissions(
            self.owner, "partners.view", "partners.manage_agreements"
        )
        output = StringIO()
        call_command(
            "check_expiring_stakeholder_agreements",
            "--mark-expired",
            f"--actor-email={self.owner.email}",
            stdout=output,
        )
        agreement.refresh_from_db()
        self.assertEqual(agreement.status, AgreementStatus.EXPIRED)
        self.assertIn("Marked 1 agreements expired", output.getvalue())

    def test_expiring_command_rejects_negative_days(self):
        with self.assertRaises(CommandError):
            call_command(
                "check_expiring_stakeholder_agreements",
                "--days=-1",
                stdout=StringIO(),
            )
