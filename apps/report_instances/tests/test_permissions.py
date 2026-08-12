"""RBAC permission tests for the ``report_instances`` app."""

from apps.rbac.authorization import user_has_permission
from apps.report_instances.permissions import (
    can_approve_report,
    can_create_report,
    can_submit_report,
    can_validate_report,
    can_view_report,
    check_permission,
)
from apps.report_instances.services import submit_report, validate_report

from .base import ReportInstanceBaseTestCase


class ReportPermissionTest(ReportInstanceBaseTestCase):
    """Seeded roles grant the expected ``report_instances.*`` codes."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.assign_role(cls.owner, "project-officer")
        cls.assign_role(cls.reviewer, "programme-manager")
        cls.assign_role(cls.other, "board-member")

    def test_officer_operational_codes(self):
        for code in (
            "report_instances.view",
            "report_instances.create",
            "report_instances.update_own",
            "report_instances.submit_own",
            "report_instances.comment",
            "report_instances.upload_evidence",
        ):
            self.assertTrue(
                user_has_permission(self.owner, code), f"{code} should be granted"
            )
        for code in (
            "report_instances.approve",
            "report_instances.reject",
            "report_instances.assign",
            "report_instances.manage_reminders",
        ):
            self.assertFalse(
                user_has_permission(self.owner, code), f"{code} should be denied"
            )

    def test_manager_review_codes(self):
        for code in (
            "report_instances.view",
            "report_instances.approve",
            "report_instances.reject",
            "report_instances.validate",
            "report_instances.assign",
            "report_instances.archive",
            "report_instances.restore",
        ):
            self.assertTrue(
                user_has_permission(self.reviewer, code),
                f"{code} should be granted to managers",
            )

    def test_board_member_read_only(self):
        self.assertTrue(user_has_permission(self.other, "report_instances.view"))
        self.assertFalse(user_has_permission(self.other, "report_instances.create"))

    def test_deny_by_default_for_unassigned_user(self):
        self.assertFalse(user_has_permission(self.owner, "report_instances.manage"))
        self.assertFalse(check_permission(_request(None), "report_instances.view"))

    def test_can_create_and_submit(self):
        self.assertTrue(can_create_report(_request(self.owner)))
        self.assertTrue(can_submit_report(_request(self.owner), self.make_report()))

    def test_can_view_own_report(self):
        report = self.make_report()
        self.assertTrue(can_view_report(_request(self.owner), report))

    def test_can_view_assigned_report(self):
        report = self.make_report()
        report.assigned_reviewer = self.reviewer
        report.save()
        self.assertTrue(can_view_report(_request(self.reviewer), report))

    def test_can_view_all_via_management(self):
        report = self.make_report()
        report.owner = self.other
        report.save()
        self.assertTrue(can_view_report(_request(self.reviewer), report))

    def test_can_validate_and_approve(self):
        self.assertTrue(can_validate_report(_request(self.reviewer)))
        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.owner)
        submit_report(report, submitted_by=self.owner)
        report.refresh_from_db()
        self.assertTrue(can_approve_report(_request(self.reviewer)))


def _request(user):
    """Build a lightweight fake request carrying ``user``."""
    from types import SimpleNamespace

    return SimpleNamespace(user=user)
