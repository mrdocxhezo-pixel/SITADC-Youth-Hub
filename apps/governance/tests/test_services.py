"""Governance service tests."""

from __future__ import annotations

from django.utils import timezone

from apps.governance import services
from apps.governance.constants import GovernanceType, TimelineEventType

from .base import GovernanceTestCase


class GovernanceServiceTests(GovernanceTestCase):
    """Tests for governance services."""

    def test_allocate_reference(self):
        """Test reference number allocation."""
        from apps.governance.models import Policy

        policy = Policy(
            governance_type=GovernanceType.POLICY,
            title="Test Policy",
            policy_category="HR",
            description="Test policy",
            version="1.0",
            status="DRAFT",
            created_by=self.user,
            updated_by=self.user,
        )
        services.allocate_reference(self.user, policy, GovernanceType.POLICY)
        self.assertIsNotNone(policy.reference_number)
        self.assertTrue(policy.reference_number.startswith("SITADC-POL-"))

    def test_policy_service_create(self):
        """Test PolicyService create."""
        policy = services.PolicyService(self.user).execute(
            actor=self.user,
            title="New Policy",
            policy_category="FINANCE",
            description="New finance policy",
            version="1.0",
            status="DRAFT",
        )
        self.assertEqual(policy.title, "New Policy")
        self.assertEqual(policy.policy_category, "FINANCE")
        self.assertIsNotNone(policy.reference_number)
        self.assertEqual(policy.status, "DRAFT")

    def test_risk_service_create(self):
        """Test RiskService create."""
        risk = services.RiskService(self.user).execute(
            actor=self.user,
            title="New Risk",
            risk_category="OPERATIONAL",
            description="New operational risk",
            likelihood=3,
            impact=4,
            mitigation_strategy="Implement controls",
            review_date="2025-12-31",
            status="ACTIVE",
        )
        self.assertEqual(risk.title, "New Risk")
        self.assertEqual(risk.risk_category, "OPERATIONAL")
        self.assertEqual(risk.likelihood, 3)
        self.assertEqual(risk.impact, 4)
        self.assertEqual(risk.risk_rating, "HIGH")
        self.assertIsNotNone(risk.reference_number)

    def test_compliance_service_create(self):
        """Test ComplianceService create."""
        req = services.ComplianceService(self.user).execute(
            actor=self.user,
            title="New Compliance Requirement",
            compliance_type="REGULATORY",
            description="New regulatory requirement",
            effective_date="2025-01-01",
            is_active=True,
        )
        self.assertEqual(req.title, "New Compliance Requirement")
        self.assertEqual(req.compliance_type, "REGULATORY")
        self.assertIsNotNone(req.reference_number)

    def test_safeguarding_service_create(self):
        """Test SafeguardingService create."""
        case = services.SafeguardingService(self.user).execute(
            actor=self.user,
            title="New Safeguarding Case",
            case_category="CHILD_PROTECTION",
            description="New safeguarding case",
            date_reported="2025-01-15",
            actions_taken="Investigation started",
            risk_level="HIGH",
        )
        self.assertEqual(case.title, "New Safeguarding Case")
        self.assertEqual(case.case_category, "CHILD_PROTECTION")
        self.assertEqual(case.confidentiality_level, "HIGHLY_CONFIDENTIAL")
        self.assertIsNotNone(case.reference_number)

    def test_incident_service_create(self):
        """Test IncidentService create."""
        incident = services.IncidentService(self.user).execute(
            actor=self.user,
            title="New Incident",
            incident_category="SECURITY",
            description="Security incident occurred",
            date_occurred=timezone.now(),
            immediate_actions_taken="Secured area",
            severity="HIGH",
        )
        self.assertEqual(incident.title, "New Incident")
        self.assertEqual(incident.incident_category, "SECURITY")
        self.assertIsNotNone(incident.reference_number)

    def test_complaint_service_create(self):
        """Test ComplaintService create."""
        complaint = services.ComplaintService(self.user).execute(
            actor=self.user,
            title="New Complaint",
            complaint_type="STAFF_CONDUCT",
            description="Staff conduct complaint",
            complainant_is_anonymous=False,
            complainant_name="Jane Doe",
        )
        self.assertEqual(complaint.title, "New Complaint")
        self.assertEqual(complaint.complaint_type, "STAFF_CONDUCT")
        self.assertIsNotNone(complaint.reference_number)

    def test_whistleblower_service_create(self):
        """Test WhistleblowerService create."""
        report = services.WhistleblowerService(self.user).execute(
            actor=self.user,
            title="New Whistleblower Report",
            report_type="FRAUD",
            description="Fraud reported",
            reporter_is_anonymous=True,
        )
        self.assertEqual(report.title, "New Whistleblower Report")
        self.assertEqual(report.report_type, "FRAUD")
        self.assertTrue(report.reporter_is_anonymous)
        self.assertEqual(report.confidentiality_level, "HIGHLY_CONFIDENTIAL")
        self.assertIsNotNone(report.reference_number)

    def test_capa_service_create(self):
        """Test CAPAService create."""
        incident = self.create_incident()
        capa = services.CAPAService(self.user).execute(
            actor=self.user,
            title="New CAPA",
            action_type="CORRECTIVE",
            description="Corrective action for incident",
            root_cause="Process failure",
            corrective_action_description="Fix process",
            due_date="2025-12-31",
            source_incident=incident,
        )
        self.assertEqual(capa.title, "New CAPA")
        self.assertEqual(capa.action_type, "CORRECTIVE")
        self.assertEqual(capa.source_incident, incident)
        self.assertIsNotNone(capa.reference_number)

    def test_governance_meeting_service_create(self):
        """Test GovernanceMeetingService create."""
        meeting = services.GovernanceMeetingService(self.user).execute(
            actor=self.user,
            title="New Meeting",
            meeting_type="EXECUTIVE",
            description="Executive committee meeting",
            scheduled_date=timezone.now() + timezone.timedelta(days=7),
        )
        self.assertEqual(meeting.title, "New Meeting")
        self.assertEqual(meeting.meeting_type, "EXECUTIVE")
        self.assertIsNotNone(meeting.reference_number)

    def test_validate_risk_score(self):
        """Test risk score validation."""
        # Valid scores
        services.validate_risk_score(1, 1)
        services.validate_risk_score(3, 4)
        services.validate_risk_score(5, 5)

        # Invalid scores
        from apps.governance.exceptions import InvalidRiskScoreError

        with self.assertRaises(InvalidRiskScoreError):
            services.validate_risk_score(0, 3)
        with self.assertRaises(InvalidRiskScoreError):
            services.validate_risk_score(6, 3)

    def test_get_risk_rating(self):
        """Test risk rating calculation."""
        self.assertEqual(services.get_risk_rating(4), "LOW")  # 1*4=4 <= 5
        self.assertEqual(services.get_risk_rating(10), "MEDIUM")  # <= 10
        self.assertEqual(services.get_risk_rating(12), "HIGH")  # <= 15
        self.assertEqual(services.get_risk_rating(20), "CRITICAL")  # > 15

    def test_record_timeline(self):
        """Test timeline event recording."""
        from apps.governance.models import GovernanceTimeline

        services._record_timeline(
            self.user,
            TimelineEventType.RECORD_CREATED,
            "Test event",
            module="governance",
            reference_number="TEST-001",
            action_performed="create",
            status_after_event="DRAFT",
        )
        event = GovernanceTimeline.objects.first()
        self.assertIsNotNone(event)
        self.assertEqual(event.event_type, "RECORD_CREATED")
        self.assertEqual(event.description, "Test event")
        self.assertEqual(event.reference_number, "TEST-001")

    def test_notify(self):
        """Test notification creation."""
        from apps.governance.models import GovernanceNotification

        services._notify(
            self.user,
            "POLICY_APPROVED",
            "Policy Approved",
            "Your policy has been approved",
        )
        notification = GovernanceNotification.objects.first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.notification_type, "POLICY_APPROVED")
        self.assertEqual(notification.title, "Policy Approved")
        self.assertEqual(notification.recipient, self.user)
