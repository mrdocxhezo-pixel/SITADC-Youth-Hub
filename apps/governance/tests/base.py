"""Base test classes and utilities for governance tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.constants import StatusConstants

User = get_user_model()


class GovernanceTestCase(TestCase):
    """Base test case for governance tests with common setup."""

    def setUp(self):
        """Set up test users."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpass123",
        )

    def create_policy(self, **kwargs):
        """Helper to create a policy."""
        from apps.governance.models import Policy

        defaults = {
            "title": "Test Policy",
            "reference_number": "POL-001",
            "policy_category": "HR",
            "description": "This is a test policy.",
            "version": "1.0",
            "status": StatusConstants.APPROVED,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Policy.objects.create(**defaults)

    def create_risk(self, **kwargs):
        """Helper to create a risk register entry."""
        from apps.governance.models import RiskRegister

        defaults = {
            "title": "Test Risk",
            "reference_number": "RSK-001",
            "risk_category": "FINANCIAL",
            "description": "This is a test risk.",
            "root_cause": "Inadequate controls",
            "likelihood": 3,
            "impact": 4,
            "risk_owner": self.user,
            "mitigation_strategy": "Improve controls",
            "review_date": "2025-12-31",
            "status": StatusConstants.ACTIVE,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return RiskRegister.objects.create(**defaults)

    def create_safeguarding_case(self, **kwargs):
        """Helper to create a safeguarding case."""
        from apps.governance.models import SafeguardingCase

        defaults = {
            "title": "Test Safeguarding Case",
            "reference_number": "SFG-001",
            "case_category": "CHILD_PROTECTION",
            "description": "This is a test safeguarding case.",
            "date_reported": "2025-01-15",
            "reported_by": self.user,
            "affected_individuals": "A.B. (minor)",
            "risk_level": "HIGH",
            "assigned_officer": self.user,
            "actions_taken": "Investigation initiated",
            "status": StatusConstants.ACTIVE,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return SafeguardingCase.objects.create(**defaults)

    def create_incident(self, **kwargs):
        """Helper to create an incident report."""
        from django.utils import timezone

        from apps.governance.models import IncidentReport

        defaults = {
            "title": "Test Incident",
            "reference_number": "INC-001",
            "incident_category": "HEALTH_AND_SAFETY",
            "description": "This is a test incident.",
            "date_occurred": timezone.now(),
            "date_reported": timezone.now(),
            "reported_by": self.user,
            "location": "Office",
            "severity": "MEDIUM",
            "immediate_actions_taken": "First aid administered",
            "investigation_required": True,
            "status": StatusConstants.PENDING_REVIEW,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return IncidentReport.objects.create(**defaults)

    def create_complaint(self, **kwargs):
        """Helper to create a complaint."""
        from apps.governance.models import Complaint

        defaults = {
            "title": "Test Complaint",
            "reference_number": "CPL-001",
            "complaint_type": "SERVICE_DELIVERY",
            "description": "This is a test complaint.",
            "complainant_name": "John Doe",
            "complainant_contact": "john@example.com",
            "complainant_is_anonymous": False,
            "assigned_officer": self.user,
            "status": StatusConstants.PENDING_REVIEW,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Complaint.objects.create(**defaults)

    def create_whistleblower_report(self, **kwargs):
        """Helper to create a whistleblower report."""
        from apps.governance.models import WhistleblowerReport

        defaults = {
            "title": "Test Whistleblower Report",
            "reference_number": "WHB-001",
            "report_type": "FRAUD",
            "description": "This is a test whistleblower report.",
            "reporter_is_anonymous": True,
            "assigned_investigator": self.user,
            "status": StatusConstants.PENDING_REVIEW,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return WhistleblowerReport.objects.create(**defaults)

    def create_capa(self, **kwargs):
        """Helper to create a CAPA."""
        from apps.governance.models import CorrectivePreventiveAction

        defaults = {
            "title": "Test CAPA",
            "reference_number": "CAPA-001",
            "action_type": "BOTH",
            "description": "This is a test CAPA.",
            "root_cause": "Inadequate training",
            "corrective_action_description": "Provide training",
            "preventive_action_description": "Implement ongoing training program",
            "responsible_officer": self.user,
            "due_date": "2025-12-31",
            "status": StatusConstants.DRAFT,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return CorrectivePreventiveAction.objects.create(**defaults)

    def create_meeting(self, **kwargs):
        """Helper to create a governance meeting."""
        from django.utils import timezone

        from apps.governance.models import GovernanceMeeting

        defaults = {
            "title": "Test Meeting",
            "reference_number": "MTG-001",
            "meeting_type": "BOARD",
            "description": "This is a test meeting.",
            "scheduled_date": timezone.now() + timezone.timedelta(days=7),
            "meeting_chair": self.user,
            "status": StatusConstants.DRAFT,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return GovernanceMeeting.objects.create(**defaults)

    def create_compliance_requirement(self, **kwargs):
        """Helper to create a compliance requirement."""
        from apps.governance.models import ComplianceRequirement

        defaults = {
            "title": "Test Compliance Requirement",
            "reference_number": "CMP-001",
            "compliance_type": "REGULATORY",
            "description": "This is a test compliance requirement.",
            "effective_date": "2025-01-01",
            "is_active": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return ComplianceRequirement.objects.create(**defaults)

    def create_internal_control(self, **kwargs):
        """Helper to create an internal control."""
        from apps.governance.models import InternalControl

        defaults = {
            "title": "Test Internal Control",
            "reference_number": "CTL-001",
            "control_type": "FINANCIAL",
            "description": "This is a test internal control.",
            "objective": "Ensure financial accuracy",
            "frequency": "MONTHLY",
            "responsible_officer": self.user,
            "is_effective": True,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return InternalControl.objects.create(**defaults)

    def create_ethics_case(self, **kwargs):
        """Helper to create an ethics case."""
        from apps.governance.models import EthicsCase

        defaults = {
            "title": "Test Ethics Case",
            "reference_number": "ETH-001",
            "case_type": "CONFLICT_OF_INTEREST",
            "description": "This is a test ethics case.",
            "reported_date": "2025-01-15",
            "reported_by": self.user,
            "assigned_investigator": self.user,
            "status": StatusConstants.PENDING_REVIEW,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return EthicsCase.objects.create(**defaults)

    def create_conflict_declaration(self, **kwargs):
        """Helper to create a conflict of interest declaration."""
        from apps.governance.models import ConflictOfInterestDeclaration

        defaults = {
            "declarant": self.user,
            "declaration_type": "FINANCIAL",
            "nature_of_conflict": "Financial interest in vendor",
            "related_organization": "Vendor Corp",
            "date_declared": "2025-01-15",
            "review_date": "2026-01-15",
            "mitigation_measures": "Recuse from decisions",
            "approval_status": StatusConstants.PENDING_REVIEW,
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return ConflictOfInterestDeclaration.objects.create(**defaults)

    def create_document(self, **kwargs):
        """Helper to create a governance document."""
        from apps.governance.models import Document

        defaults = {
            "title": "Test Document",
            "reference_number": "DOC-001",
            "document_type": "POLICY",
            "description": "This is a test document.",
            "version": "1.0",
            "confidentiality_level": "INTERNAL",
            "created_by": self.user,
            "updated_by": self.user,
        }
        defaults.update(kwargs)
        return Document.objects.create(**defaults)

    def create_risk_assessment(self, risk=None, **kwargs):
        """Helper to create a risk assessment."""
        from apps.governance.models import RiskAssessment

        if risk is None:
            risk = self.create_risk()

        defaults = {
            "risk_register": risk,
            "assessment_type": "INITIAL",
            "assessed_by": self.user,
            "assessment_date": "2025-06-15",
            "likelihood": 3,
            "impact": 4,
            "assessor_notes": "Initial assessment",
        }
        defaults.update(kwargs)
        return RiskAssessment.objects.create(**defaults)

    def create_risk_treatment(self, risk=None, **kwargs):
        """Helper to create a risk treatment plan."""
        from apps.governance.models import RiskTreatmentPlan

        if risk is None:
            risk = self.create_risk()

        defaults = {
            "risk_register": risk,
            "treatment_type": "MITIGATE",
            "description": "Implement new controls",
            "responsible_officer": self.user,
            "target_completion_date": "2025-12-31",
            "progress_percentage": 0,
        }
        defaults.update(kwargs)
        return RiskTreatmentPlan.objects.create(**defaults)

    def create_compliance_assessment(self, requirement=None, **kwargs):
        """Helper to create a compliance assessment."""
        from apps.governance.models import ComplianceAssessment

        if requirement is None:
            requirement = self.create_compliance_requirement()

        defaults = {
            "compliance_requirement": requirement,
            "assessed_by": self.user,
            "assessment_date": "2025-06-15",
            "assessment_period_start": "2025-01-01",
            "assessment_period_end": "2025-06-30",
            "result": "COMPLIANT",
            "findings": "All requirements met",
        }
        defaults.update(kwargs)
        return ComplianceAssessment.objects.create(**defaults)

    def create_policy_version(self, policy=None, **kwargs):
        """Helper to create a policy version."""
        from apps.governance.models import PolicyVersion

        if policy is None:
            policy = self.create_policy()

        defaults = {
            "policy": policy,
            "version_number": "1.1",
            "effective_date": "2025-07-01",
            "changes_summary": "Updated section 3",
        }
        defaults.update(kwargs)
        return PolicyVersion.objects.create(**defaults)

    def create_policy_acknowledgement(self, policy=None, **kwargs):
        """Helper to create a policy acknowledgement."""
        from apps.governance.models import PolicyAcknowledgement

        if policy is None:
            policy = self.create_policy()

        defaults = {
            "policy": policy,
            "user": self.user,
            "is_current": True,
        }
        defaults.update(kwargs)
        return PolicyAcknowledgement.objects.create(**defaults)

    def create_meeting_attendance(self, meeting=None, **kwargs):
        """Helper to create a meeting attendance record."""
        from apps.governance.models import MeetingAttendance

        if meeting is None:
            meeting = self.create_meeting()

        defaults = {
            "meeting": meeting,
            "user": self.user,
            "attendance_status": "PRESENT",
        }
        defaults.update(kwargs)
        return MeetingAttendance.objects.create(**defaults)
