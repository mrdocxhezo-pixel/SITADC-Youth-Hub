"""Governance view tests."""

from __future__ import annotations

from django.urls import reverse

from .base import GovernanceTestCase


class GovernanceViewTests(GovernanceTestCase):
    """Tests for governance views."""

    def setUp(self):
        super().setUp()
        # Grant governance permissions to test user
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role

        content_type = ContentType.objects.get_for_model(Role)
        perms = []
        for action in ["view", "create", "update", "delete", "manage"]:
            perm, _ = Permission.objects.get_or_create(
                codename=f"governance.{action}",
                defaults={
                    "name": f"Can {action} governance",
                    "content_type": content_type,
                },
            )
            perms.append(perm)

        role = Role.objects.create(
            name="Test Governance Role",
            slug="test-governance-role",
            description="Test role for governance",
        )
        role.permissions.add(*perms)
        from apps.rbac.models import UserRoleAssignment

        UserRoleAssignment.objects.create(user=self.user, role=role, status="ACTIVE")

        # Create test objects
        self.policy = self.create_policy()
        self.risk = self.create_risk()
        self.safeguarding = self.create_safeguarding_case()
        self.incident = self.create_incident()
        self.complaint = self.create_complaint()
        self.whistleblower = self.create_whistleblower_report()
        self.capa = self.create_capa()
        self.meeting = self.create_meeting()

        self.client.force_login(self.user)

    # Dashboard Tests
    def test_governance_dashboard(self):
        """Test governance dashboard view."""
        response = self.client.get(reverse("governance:governance_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Governance Dashboard")
        self.assertContains(response, "Active Policies")
        self.assertContains(response, "Active Risks")

    # Policy Tests
    def test_policy_list(self):
        """Test policy list view."""
        response = self.client.get(reverse("governance:policy_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Policy")

    def test_policy_create(self):
        """Test policy create view."""
        response = self.client.get(reverse("governance:policy_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:policy_create"),
            {
                "title": "New Policy",
                "policy_category": "IT",
                "description": "New IT policy",
                "version": "1.0",
                "status": "DRAFT",
            },
        )
        self.assertEqual(response.status_code, 302)  # Redirect after create

    def test_policy_detail(self):
        """Test policy detail view."""
        response = self.client.get(
            reverse("governance:policy_detail", kwargs={"pk": self.policy.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Policy")

    def test_policy_update(self):
        """Test policy update view."""
        response = self.client.get(
            reverse("governance:policy_update", kwargs={"pk": self.policy.pk})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:policy_update", kwargs={"pk": self.policy.pk}),
            {
                "title": "Updated Policy",
                "policy_category": "HR",
                "description": "Updated policy",
                "version": "1.0",
                "status": "DRAFT",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_policy_delete(self):
        """Test policy delete view."""
        response = self.client.get(
            reverse("governance:policy_delete", kwargs={"pk": self.policy.pk})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:policy_delete", kwargs={"pk": self.policy.pk})
        )
        self.assertEqual(response.status_code, 302)

    # Risk Tests
    def test_risk_register_list(self):
        """Test risk register list view."""
        response = self.client.get(reverse("governance:risk_register_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Risk")

    def test_risk_register_create(self):
        """Test risk register create view."""
        response = self.client.get(reverse("governance:risk_register_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:risk_register_create"),
            {
                "title": "New Risk",
                "risk_category": "FINANCIAL",
                "description": "New financial risk",
                "likelihood": 3,
                "impact": 4,
                "mitigation_strategy": "Implement controls",
                "review_date": "2025-12-31",
                "status": "ACTIVE",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_risk_register_detail(self):
        """Test risk register detail view."""
        response = self.client.get(
            reverse("governance:risk_register_detail", kwargs={"pk": self.risk.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Risk")

    # Safeguarding Tests (require confidential permission)
    def test_safeguarding_case_list(self):
        """Test safeguarding case list view."""
        # Add confidential permission
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role

        content_type = ContentType.objects.get_for_model(Role)
        perm, _ = Permission.objects.get_or_create(
            codename="governance.view_confidential",
            defaults={
                "name": "Can view confidential governance",
                "content_type": content_type,
            },
        )
        from apps.rbac.models import UserRoleAssignment

        assignment = UserRoleAssignment.objects.filter(user=self.user).first()
        if assignment:
            assignment.role.permissions.add(perm)

        response = self.client.get(reverse("governance:safeguarding_case_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Safeguarding Case")

    # Incident Tests
    def test_incident_report_list(self):
        """Test incident report list view."""
        response = self.client.get(reverse("governance:incident_report_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Incident")

    def test_incident_report_create(self):
        """Test incident report create view."""
        response = self.client.get(reverse("governance:incident_report_create"))
        self.assertEqual(response.status_code, 200)

        from django.utils import timezone

        response = self.client.post(
            reverse("governance:incident_report_create"),
            {
                "title": "New Incident",
                "incident_category": "HEALTH_AND_SAFETY",
                "description": "New incident",
                "date_occurred": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "immediate_actions_taken": "Action taken",
                "severity": "MEDIUM",
                "status": "PENDING_REVIEW",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_incident_report_detail(self):
        """Test incident report detail view."""
        response = self.client.get(
            reverse(
                "governance:incident_report_detail",
                kwargs={"pk": self.incident.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Incident")

    # Complaint Tests
    def test_complaint_list(self):
        """Test complaint list view."""
        response = self.client.get(reverse("governance:complaint_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Complaint")

    def test_complaint_create(self):
        """Test complaint create view."""
        response = self.client.get(reverse("governance:complaint_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:complaint_create"),
            {
                "title": "New Complaint",
                "complaint_type": "SERVICE_DELIVERY",
                "description": "New complaint",
                "complainant_name": "John Doe",
                "complainant_contact": "john@example.com",
                "complainant_is_anonymous": False,
                "status": "PENDING_REVIEW",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_complaint_detail(self):
        """Test complaint detail view."""
        response = self.client.get(
            reverse("governance:complaint_detail", kwargs={"pk": self.complaint.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Complaint")

    # Whistleblower Tests (require confidential permission)
    def test_whistleblower_report_list(self):
        """Test whistleblower report list view."""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType

        from apps.rbac.models import Role

        content_type = ContentType.objects.get_for_model(Role)
        perm, _ = Permission.objects.get_or_create(
            codename="governance.view_confidential",
            defaults={
                "name": "Can view confidential governance",
                "content_type": content_type,
            },
        )
        from apps.rbac.models import UserRoleAssignment

        assignment = UserRoleAssignment.objects.filter(user=self.user).first()
        if assignment:
            assignment.role.permissions.add(perm)

        response = self.client.get(reverse("governance:whistleblower_report_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Whistleblower Report")

    # CAPA Tests
    def test_corrective_preventive_action_list(self):
        """Test CAPA list view."""
        response = self.client.get(
            reverse("governance:corrective_preventive_action_list")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test CAPA")

    def test_corrective_preventive_action_create(self):
        """Test CAPA create view."""
        response = self.client.get(
            reverse("governance:corrective_preventive_action_create")
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:corrective_preventive_action_create"),
            {
                "title": "New CAPA",
                "action_type": "BOTH",
                "description": "New CAPA",
                "root_cause": "Root cause",
                "corrective_action_description": "Corrective action",
                "due_date": "2025-12-31",
                "status": "DRAFT",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_corrective_preventive_action_detail(self):
        """Test CAPA detail view."""
        response = self.client.get(
            reverse(
                "governance:corrective_preventive_action_detail",
                kwargs={"pk": self.capa.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test CAPA")

    # Meeting Tests
    def test_governance_meeting_list(self):
        """Test governance meeting list view."""
        response = self.client.get(reverse("governance:governance_meeting_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Meeting")

    def test_governance_meeting_create(self):
        """Test governance meeting create view."""
        response = self.client.get(reverse("governance:governance_meeting_create"))
        self.assertEqual(response.status_code, 200)

        from django.utils import timezone

        response = self.client.post(
            reverse("governance:governance_meeting_create"),
            {
                "title": "New Meeting",
                "meeting_type": "BOARD",
                "governance_type": "GOVERNANCE_MEETING",
                "description": "New meeting",
                "scheduled_date": (
                    timezone.now() + timezone.timedelta(days=7)
                ).strftime("%Y-%m-%dT%H:%M"),
                "status": "DRAFT",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_governance_meeting_detail(self):
        """Test governance meeting detail view."""
        response = self.client.get(
            reverse(
                "governance:governance_meeting_detail",
                kwargs={"pk": self.meeting.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Meeting")

    # Compliance Tests
    def test_compliance_requirement_list(self):
        """Test compliance requirement list view."""
        self.create_compliance_requirement()
        response = self.client.get(reverse("governance:compliance_requirement_list"))
        self.assertEqual(response.status_code, 200)

    def test_compliance_requirement_create(self):
        """Test compliance requirement create view."""
        response = self.client.get(reverse("governance:compliance_requirement_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:compliance_requirement_create"),
            {
                "title": "New Compliance",
                "compliance_type": "REGULATORY",
                "description": "New compliance requirement",
                "effective_date": "2025-01-01",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)

    # Internal Control Tests
    def test_internal_control_list(self):
        """Test internal control list view."""
        self.create_internal_control()
        response = self.client.get(reverse("governance:internal_control_list"))
        self.assertEqual(response.status_code, 200)

    def test_internal_control_create(self):
        """Test internal control create view."""
        response = self.client.get(reverse("governance:internal_control_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:internal_control_create"),
            {
                "title": "New Control",
                "control_type": "FINANCIAL",
                "description": "New control",
                "objective": "Test objective",
                "frequency": "MONTHLY",
                "is_effective": True,
            },
        )
        self.assertEqual(response.status_code, 302)

    # Ethics Tests
    def test_ethics_case_list(self):
        """Test ethics case list view."""
        self.create_ethics_case()
        response = self.client.get(reverse("governance:ethics_case_list"))
        self.assertEqual(response.status_code, 200)

    def test_ethics_case_create(self):
        """Test ethics case create view."""
        response = self.client.get(reverse("governance:ethics_case_create"))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            reverse("governance:ethics_case_create"),
            {
                "title": "New Ethics Case",
                "case_type": "CONFLICT_OF_INTEREST",
                "description": "New ethics case",
                "reported_date": "2025-01-15",
                "status": "PENDING_REVIEW",
            },
        )
        self.assertEqual(response.status_code, 302)

    # Document Tests
    def test_document_list(self):
        """Test document list view."""
        self.create_document()
        response = self.client.get(reverse("governance:document_list"))
        self.assertEqual(response.status_code, 200)

    def test_document_create(self):
        """Test document create view."""
        response = self.client.get(reverse("governance:document_create"))
        self.assertEqual(response.status_code, 200)

    # Notification Tests
    def test_governance_notification_list(self):
        """Test governance notification list view."""
        response = self.client.get(reverse("governance:governance_notification_list"))
        self.assertEqual(response.status_code, 200)

    # Timeline Tests
    def test_governance_timeline_list(self):
        """Test governance timeline list view."""
        response = self.client.get(reverse("governance:governance_timeline_list"))
        self.assertEqual(response.status_code, 200)


class GovernanceViewPermissionTests(GovernanceTestCase):
    """Tests for governance view permissions."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user)

    def test_dashboard_requires_permission(self):
        """Test dashboard requires governance.view permission."""
        response = self.client.get(reverse("governance:governance_dashboard"))
        self.assertEqual(response.status_code, 403)

    def test_list_views_require_permission(self):
        """Test list views require governance.view permission."""
        urls = [
            "governance:policy_list",
            "governance:risk_register_list",
            "governance:incident_report_list",
            "governance:complaint_list",
            "governance:corrective_preventive_action_list",
        ]
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 403)

    def test_safeguarding_requires_confidential_permission(self):
        """Test safeguarding views require governance.view_confidential permission."""
        urls = [
            "governance:safeguarding_case_list",
            "governance:whistleblower_report_list",
        ]
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 403)

    def test_create_requires_create_permission(self):
        """Test create views require governance.create permission."""
        urls = [
            "governance:policy_create",
            "governance:risk_register_create",
            "governance:incident_report_create",
            "governance:complaint_create",
            "governance:corrective_preventive_action_create",
        ]
        for url_name in urls:
            response = self.client.get(reverse(url_name))
            self.assertEqual(response.status_code, 403)
