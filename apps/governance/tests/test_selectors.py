"""Governance selector tests."""

from __future__ import annotations

from apps.governance.selectors import (
    get_accessible_capas,
    get_accessible_complaints,
    get_accessible_compliance_assessments,
    get_accessible_compliance_requirements,
    get_accessible_conflict_declarations,
    get_accessible_documents,
    get_accessible_ethics_cases,
    get_accessible_incidents,
    get_accessible_internal_controls,
    get_accessible_meetings,
    get_accessible_notifications,
    get_accessible_policies,
    get_accessible_risks,
    get_accessible_safeguarding_cases,
    get_accessible_timeline,
    get_accessible_whistleblower_reports,
    get_critical_risk_count,
    get_high_risk_count,
    get_high_risk_items,
    get_policy_compliance_rate,
    get_recent_complaints,
    get_recent_incidents,
    get_recent_policies,
    get_recent_risks,
    get_unread_notification_count,
    get_upcoming_governance_deadlines,
    get_upcoming_meetings,
)

from .base import GovernanceTestCase


class GovernanceSelectorTests(GovernanceTestCase):
    """Tests for governance selectors."""

    def setUp(self):
        super().setUp()
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role, UserRoleAssignment

        content_type = ContentType.objects.get_for_model(Role)
        perms = []
        for action in [
            "view",
            "create",
            "update",
            "delete",
            "manage",
            "view_confidential",
        ]:
            perm, _ = Permission.objects.get_or_create(
                codename=f"governance.{action}",
                defaults={
                    "name": f"Can {action} governance",
                    "content_type": content_type,
                },
            )
            perms.append(perm)

        role = Role.objects.create(
            name="Test Governance Selector Role",
            slug="test-governance-selector-role",
            description="Test role for governance selectors",
        )
        role.permissions.add(*perms)
        UserRoleAssignment.objects.create(user=self.user, role=role, status="ACTIVE")
        self.create_policy()
        self.create_risk()
        self.create_safeguarding_case()
        self.create_incident()
        self.create_complaint()
        self.create_whistleblower_report()
        self.create_capa()
        self.create_meeting()
        self.create_compliance_requirement()
        self.create_internal_control()
        self.create_ethics_case()
        self.create_conflict_declaration()
        self.create_document()

    def test_get_accessible_policies(self):
        """Test accessible policies selector."""
        policies = get_accessible_policies(self.user)
        self.assertEqual(policies.count(), 1)

    def test_get_accessible_risks(self):
        """Test accessible risks selector."""
        risks = get_accessible_risks(self.user)
        self.assertEqual(risks.count(), 1)

    def test_get_accessible_safeguarding_cases(self):
        """Test accessible safeguarding cases selector."""
        cases = get_accessible_safeguarding_cases(self.user)
        self.assertEqual(cases.count(), 1)

    def test_get_accessible_incidents(self):
        """Test accessible incidents selector."""
        incidents = get_accessible_incidents(self.user)
        self.assertEqual(incidents.count(), 1)

    def test_get_accessible_complaints(self):
        """Test accessible complaints selector."""
        complaints = get_accessible_complaints(self.user)
        self.assertEqual(complaints.count(), 1)

    def test_get_accessible_whistleblower_reports(self):
        """Test accessible whistleblower reports selector."""
        reports = get_accessible_whistleblower_reports(self.user)
        self.assertEqual(reports.count(), 1)

    def test_get_accessible_capas(self):
        """Test accessible CAPAs selector."""
        capas = get_accessible_capas(self.user)
        self.assertEqual(capas.count(), 1)

    def test_get_accessible_documents(self):
        """Test accessible documents selector."""
        docs = get_accessible_documents(self.user)
        self.assertEqual(docs.count(), 1)

    def test_get_accessible_meetings(self):
        """Test accessible meetings selector."""
        meetings = get_accessible_meetings(self.user)
        self.assertEqual(meetings.count(), 1)

    def test_get_accessible_compliance_requirements(self):
        """Test accessible compliance requirements selector."""
        reqs = get_accessible_compliance_requirements(self.user)
        self.assertEqual(reqs.count(), 1)

    def test_get_accessible_compliance_assessments(self):
        """Test accessible compliance assessments selector."""
        req = self.create_compliance_requirement(reference_number="CMP-002")
        self.create_compliance_assessment(requirement=req)
        assessments = get_accessible_compliance_assessments(self.user)
        self.assertEqual(assessments.count(), 1)

    def test_get_accessible_internal_controls(self):
        """Test accessible internal controls selector."""
        controls = get_accessible_internal_controls(self.user)
        self.assertEqual(controls.count(), 1)

    def test_get_accessible_ethics_cases(self):
        """Test accessible ethics cases selector."""
        cases = get_accessible_ethics_cases(self.user)
        self.assertEqual(cases.count(), 1)

    def test_get_accessible_conflict_declarations(self):
        """Test accessible conflict declarations selector."""
        declarations = get_accessible_conflict_declarations(self.user)
        self.assertEqual(declarations.count(), 1)

    def test_get_accessible_notifications(self):
        """Test accessible notifications selector."""
        notifications = get_accessible_notifications(self.user)
        self.assertEqual(notifications.count(), 0)  # No notifications created in setUp

    def test_get_accessible_timeline(self):
        """Test accessible timeline selector."""
        timeline = get_accessible_timeline(self.user)
        self.assertEqual(timeline.count(), 0)  # No timeline events created in setUp

    def test_get_policy_compliance_rate(self):
        """Test policy compliance rate calculation."""
        policy = self.create_policy(status="ACTIVE", reference_number="POL-002")
        self.create_policy_acknowledgement(policy=policy)
        rate = get_policy_compliance_rate(self.user)
        self.assertEqual(rate, 100.0)

    def test_get_high_risk_items(self):
        """Test high risk items selector."""
        self.create_risk(likelihood=4, impact=5, reference_number="RSK-002")  # CRITICAL
        items = get_high_risk_items(self.user)
        self.assertEqual(items.count(), 2)  # MEDIUM + CRITICAL

    def test_get_critical_risk_count(self):
        """Test critical risk count."""
        self.create_risk(likelihood=4, impact=5, reference_number="RSK-002")  # CRITICAL
        count = get_critical_risk_count(self.user)
        self.assertEqual(count, 1)

    def test_get_high_risk_count(self):
        """Test high risk count."""
        self.create_risk(likelihood=4, impact=5, reference_number="RSK-002")  # CRITICAL
        count = get_high_risk_count(self.user)
        self.assertEqual(count, 2)  # MEDIUM + CRITICAL

    def test_get_upcoming_governance_deadlines(self):
        """Test upcoming governance deadlines."""
        deadlines = get_upcoming_governance_deadlines(self.user)
        self.assertIsInstance(deadlines, list)

    def test_get_recent_policies(self):
        """Test recent policies selector."""
        policies = get_recent_policies(self.user)
        self.assertEqual(policies.count(), 1)

    def test_get_recent_risks(self):
        """Test recent risks selector."""
        risks = get_recent_risks(self.user)
        self.assertEqual(risks.count(), 1)

    def test_get_recent_incidents(self):
        """Test recent incidents selector."""
        incidents = get_recent_incidents(self.user)
        self.assertEqual(incidents.count(), 1)

    def test_get_recent_complaints(self):
        """Test recent complaints selector."""
        complaints = get_recent_complaints(self.user)
        self.assertEqual(complaints.count(), 1)

    def test_get_upcoming_meetings(self):
        """Test upcoming meetings selector."""
        meetings = get_upcoming_meetings(self.user)
        self.assertEqual(meetings.count(), 1)

    def test_get_unread_notification_count(self):
        """Test unread notification count."""
        count = get_unread_notification_count(self.user)
        self.assertEqual(count, 0)
