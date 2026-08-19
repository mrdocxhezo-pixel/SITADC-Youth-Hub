"""Governance model tests."""

from __future__ import annotations

from django.db import IntegrityError, transaction

from apps.governance.models import SafeguardingCase, WhistleblowerReport

from .base import GovernanceTestCase


class PolicyModelTests(GovernanceTestCase):
    """Tests for the Policy model."""

    def test_create_policy(self):
        """Test creating a policy."""
        policy = self.create_policy()
        self.assertEqual(policy.title, "Test Policy")
        self.assertEqual(policy.reference_number, "POL-001")
        self.assertEqual(policy.policy_category, "HR")
        self.assertEqual(policy.status, "APPROVED")
        self.assertEqual(policy.governance_type, "POLICY")
        self.assertEqual(str(policy), "POL-001 - Test Policy")

    def test_policy_unique_reference(self):
        """Test that policy reference numbers must be unique."""
        self.create_policy()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_policy()

    def test_policy_versioning(self):
        """Test policy version relationships."""
        policy = self.create_policy()
        version = self.create_policy_version(policy=policy)
        self.assertEqual(version.policy, policy)
        self.assertEqual(version.version_number, "1.1")
        self.assertEqual(str(version), "Test Policy v1.1")

    def test_policy_acknowledgement(self):
        """Test policy acknowledgement tracking."""
        policy = self.create_policy()
        ack = self.create_policy_acknowledgement(policy=policy)
        self.assertEqual(ack.policy, policy)
        self.assertEqual(ack.user, self.user)
        self.assertTrue(ack.is_current)


class RiskRegisterModelTests(GovernanceTestCase):
    """Tests for the RiskRegister model."""

    def test_create_risk(self):
        """Test creating a risk register entry."""
        risk = self.create_risk()
        self.assertEqual(risk.title, "Test Risk")
        self.assertEqual(risk.risk_category, "FINANCIAL")
        self.assertEqual(risk.likelihood, 3)
        self.assertEqual(risk.impact, 4)
        self.assertEqual(risk.risk_rating, "HIGH")  # 3*4=12 -> HIGH (<=15)
        self.assertEqual(risk.risk_score, 12)
        self.assertEqual(str(risk), "RSK-001 - Test Risk (FINANCIAL)")

    def test_risk_unique_reference(self):
        """Test that risk reference numbers must be unique."""
        self.create_risk()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_risk()

    def test_risk_critical_rating(self):
        """Test CRITICAL risk rating (score >= 16)."""
        risk = self.create_risk(likelihood=4, impact=5)
        self.assertEqual(risk.risk_score, 20)
        self.assertEqual(risk.risk_rating, "CRITICAL")

    def test_risk_assessments(self):
        """Test risk assessment relationships."""
        risk = self.create_risk()
        assessment = self.create_risk_assessment(risk=risk)
        self.assertEqual(assessment.risk_register, risk)
        self.assertEqual(assessment.risk_score, 12)

    def test_risk_treatment_plans(self):
        """Test risk treatment plan relationships."""
        risk = self.create_risk()
        treatment = self.create_risk_treatment(risk=risk)
        self.assertEqual(treatment.risk_register, risk)
        self.assertEqual(treatment.treatment_type, "MITIGATE")


class SafeguardingCaseModelTests(GovernanceTestCase):
    """Tests for the SafeguardingCase model."""

    def test_create_safeguarding_case(self):
        """Test creating a safeguarding case."""
        case = self.create_safeguarding_case()
        self.assertEqual(case.title, "Test Safeguarding Case")
        self.assertEqual(case.case_category, "CHILD_PROTECTION")
        self.assertEqual(case.risk_level, "HIGH")
        self.assertEqual(case.confidentiality_level, "HIGHLY_CONFIDENTIAL")
        self.assertEqual(
            str(case), "SFG-001 - Test Safeguarding Case (CHILD_PROTECTION)"
        )

    def test_safeguarding_always_highly_confidential(self):
        """Test that safeguarding cases are always highly confidential."""
        case = SafeguardingCase.objects.create(
            title="Test Case",
            reference_number="SFG-002",
            case_category="VULNERABLE_ADULT",
            description="Test case",
            date_reported="2025-01-15",
            risk_level="MEDIUM",
            actions_taken="Action taken",
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(case.confidentiality_level, "HIGHLY_CONFIDENTIAL")


class IncidentReportModelTests(GovernanceTestCase):
    """Tests for the IncidentReport model."""

    def test_create_incident(self):
        """Test creating an incident report."""
        incident = self.create_incident()
        self.assertEqual(incident.title, "Test Incident")
        self.assertEqual(incident.incident_category, "HEALTH_AND_SAFETY")
        self.assertEqual(incident.severity, "MEDIUM")
        self.assertEqual(str(incident), "INC-001 - Test Incident (HEALTH_AND_SAFETY)")

    def test_incident_unique_reference(self):
        """Test that incident reference numbers must be unique."""
        self.create_incident()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_incident()


class ComplaintModelTests(GovernanceTestCase):
    """Tests for the Complaint model."""

    def test_create_complaint(self):
        """Test creating a complaint."""
        complaint = self.create_complaint()
        self.assertEqual(complaint.title, "Test Complaint")
        self.assertEqual(complaint.complaint_type, "SERVICE_DELIVERY")
        self.assertFalse(complaint.complainant_is_anonymous)
        self.assertEqual(str(complaint), "CPL-001 - Test Complaint (SERVICE_DELIVERY)")

    def test_complaint_unique_reference(self):
        """Test that complaint reference numbers must be unique."""
        self.create_complaint()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_complaint()

    def test_anonymous_complaint(self):
        """Test anonymous complaint creation."""
        complaint = self.create_complaint(
            complainant_is_anonymous=True,
            complainant_name="",
            complainant_contact="",
        )
        self.assertTrue(complaint.complainant_is_anonymous)


class WhistleblowerReportModelTests(GovernanceTestCase):
    """Tests for the WhistleblowerReport model."""

    def test_create_whistleblower_report(self):
        """Test creating a whistleblower report."""
        report = self.create_whistleblower_report()
        self.assertEqual(report.title, "Test Whistleblower Report")
        self.assertEqual(report.report_type, "FRAUD")
        self.assertTrue(report.reporter_is_anonymous)
        self.assertEqual(report.confidentiality_level, "HIGHLY_CONFIDENTIAL")
        self.assertEqual(
            str(report),
            "WHB-001 - Test Whistleblower Report - Reporter: Anonymous",
        )

    def test_whistleblower_always_highly_confidential(self):
        """Test that whistleblower reports are always highly confidential."""
        report = WhistleblowerReport.objects.create(
            title="Test Report",
            reference_number="WHB-002",
            report_type="CORRUPTION",
            description="Test report",
            reporter_is_anonymous=True,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(report.confidentiality_level, "HIGHLY_CONFIDENTIAL")


class CAPAModelTests(GovernanceTestCase):
    """Tests for the CorrectivePreventiveAction model."""

    def test_create_capa(self):
        """Test creating a CAPA."""
        capa = self.create_capa()
        self.assertEqual(capa.title, "Test CAPA")
        self.assertEqual(capa.action_type, "BOTH")
        self.assertEqual(
            str(capa), "CAPA-001 - Test CAPA (Both Corrective and Preventive)"
        )

    def test_capa_unique_reference(self):
        """Test that CAPA reference numbers must be unique."""
        self.create_capa()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_capa()

    def test_capa_source_relationships(self):
        """Test CAPA source issue relationships."""
        incident = self.create_incident()
        complaint = self.create_complaint()
        capa = self.create_capa(
            source_incident=incident,
            source_complaint=complaint,
        )
        self.assertEqual(capa.source_incident, incident)
        self.assertEqual(capa.source_complaint, complaint)


class GovernanceMeetingModelTests(GovernanceTestCase):
    """Tests for the GovernanceMeeting model."""

    def test_create_meeting(self):
        """Test creating a governance meeting."""
        meeting = self.create_meeting()
        self.assertEqual(meeting.title, "Test Meeting")
        self.assertEqual(meeting.meeting_type, "BOARD")
        expected_str = (
            f"MTG-001 - Test Meeting - "
            f"{meeting.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
        )
        self.assertEqual(str(meeting), expected_str)

    def test_meeting_unique_reference(self):
        """Test that meeting reference numbers must be unique."""
        self.create_meeting()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_meeting()

    def test_meeting_attendance(self):
        """Test meeting attendance relationships."""
        meeting = self.create_meeting()
        attendance = self.create_meeting_attendance(meeting=meeting)
        self.assertEqual(attendance.meeting, meeting)
        self.assertEqual(attendance.user, self.user)
        self.assertEqual(attendance.attendance_status, "PRESENT")


class ComplianceRequirementModelTests(GovernanceTestCase):
    """Tests for the ComplianceRequirement model."""

    def test_create_compliance_requirement(self):
        """Test creating a compliance requirement."""
        req = self.create_compliance_requirement()
        self.assertEqual(req.title, "Test Compliance Requirement")
        self.assertEqual(req.compliance_type, "REGULATORY")
        self.assertTrue(req.is_active)
        self.assertEqual(str(req), "CMP-001 - Test Compliance Requirement (REGULATORY)")

    def test_compliance_assessments(self):
        """Test compliance assessment relationships."""
        req = self.create_compliance_requirement()
        assessment = self.create_compliance_assessment(requirement=req)
        self.assertEqual(assessment.compliance_requirement, req)
        self.assertEqual(assessment.result, "COMPLIANT")


class InternalControlModelTests(GovernanceTestCase):
    """Tests for the InternalControl model."""

    def test_create_internal_control(self):
        """Test creating an internal control."""
        control = self.create_internal_control()
        self.assertEqual(control.title, "Test Internal Control")
        self.assertEqual(control.control_type, "FINANCIAL")
        self.assertTrue(control.is_effective)
        self.assertEqual(str(control), "CTL-001 - Test Internal Control (FINANCIAL)")

    def test_control_unique_reference(self):
        """Test that control reference numbers must be unique."""
        self.create_internal_control()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_internal_control()


class EthicsCaseModelTests(GovernanceTestCase):
    """Tests for the EthicsCase model."""

    def test_create_ethics_case(self):
        """Test creating an ethics case."""
        case = self.create_ethics_case()
        self.assertEqual(case.title, "Test Ethics Case")
        self.assertEqual(case.case_type, "CONFLICT_OF_INTEREST")
        self.assertEqual(str(case), "ETH-001 - Test Ethics Case (CONFLICT_OF_INTEREST)")

    def test_ethics_case_unique_reference(self):
        """Test that ethics case reference numbers must be unique."""
        self.create_ethics_case()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_ethics_case()


class ConflictOfInterestDeclarationModelTests(GovernanceTestCase):
    """Tests for the ConflictOfInterestDeclaration model."""

    def test_create_conflict_declaration(self):
        """Test creating a conflict of interest declaration."""
        decl = self.create_conflict_declaration()
        self.assertEqual(decl.nature_of_conflict, "Financial interest in vendor")
        self.assertEqual(decl.declaration_type, "FINANCIAL")
        self.assertEqual(decl.approval_status, "PENDING_REVIEW")
        self.assertEqual(str(decl), f"{self.user.get_full_name()} - FINANCIAL")


class DocumentModelTests(GovernanceTestCase):
    """Tests for the Document model."""

    def test_create_document(self):
        """Test creating a governance document."""
        doc = self.create_document()
        self.assertEqual(doc.title, "Test Document")
        self.assertEqual(doc.document_type, "POLICY")
        self.assertEqual(doc.confidentiality_level, "INTERNAL")
        self.assertEqual(str(doc), "DOC-001 - Test Document v1.0")

    def test_document_unique_reference(self):
        """Test that document reference numbers must be unique."""
        self.create_document()
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.create_document()

    def test_document_relationships(self):
        """Test document relationships to other governance records."""
        policy = self.create_policy()
        risk = self.create_risk()
        doc = self.create_document()
        doc.related_policies.add(policy)
        doc.related_risks.add(risk)
        self.assertIn(policy, doc.related_policies.all())
        self.assertIn(risk, doc.related_risks.all())
