"""Tests for Governance, Risk, Compliance and Safeguarding models."""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.governance.models import (
    Policy,
    RiskRegister,
    ComplianceRequirement,
    InternalControl,
    EthicsCase,
    SafeguardingCase,
    IncidentReport,
    Complaint,
    WhistleblowerReport,
    CorrectivePreventiveAction,
    GovernanceMeeting,
)

User = get_user_model()


class GovernanceModelTest(TestCase):
    """Test cases for governance models."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_policy_creation(self):
        """Test creating a policy."""
        policy = Policy.objects.create(
            title='Test Policy',
            reference_number='POL-001',
            policy_category='HR',
            description='This is a test policy.',
            version='1.0',
            effective_date=timezone.now().date(),
            expiry_date=timezone.now().date() + timezone.timedelta(days=365),
            review_date=timezone.now().date() + timezone.timedelta(days=180),
            responsible_officer=self.user,
            status=Policy.StatusConstants.APPROVED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(policy.title, 'Test Policy')
        self.assertEqual(policy.reference_number, 'POL-001')
        self.assertEqual(policy.policy_category, 'HR')
        self.assertEqual(policy.status, Policy.StatusConstants.APPROVED)
        self.assertEqual(policy.governance_type, 'POLICY')
        self.assertEqual(str(policy), 'POL-001 - Test Policy')
    
    def test_risk_register_creation(self):
        """Test creating a risk register entry."""
        risk = RiskRegister.objects.create(
            title='Test Risk',
            risk_category='FINANCIAL',
            description='This is a test risk.',
            root_cause='Inadequate controls',
            likelihood=3,
            impact=4,
            risk_owner=self.user,
            mitigation_strategy='Improve controls',
            review_date=timezone.now().date() + timezone.timedelta(days=90),
            status=RiskRegister.StatusConstants.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(risk.title, 'Test Risk')
        self.assertEqual(risk.risk_category, 'FINANCIAL')
        self.assertEqual(risk.likelihood, 3)
        self.assertEqual(risk.impact, 4)
        self.assertEqual(risk.risk_rating, 'MEDIUM')  # 3*4=12 -> MEDIUM
        self.assertEqual(str(risk), 'Test Risk (FINANCIAL)')
    
    def test_safeguarding_case_creation(self):
        """Test creating a safeguarding case."""
        case = SafeguardingCase.objects.create(
            title='Test Safeguarding Case',
            case_category='CHILD_PROTECTION',
            description='This is a test safeguarding case.',
            date_reported=timezone.now().date(),
            reported_by=self.user,
            risk_level='HIGH',
            assigned_officer=self.user,
            status=SafeguardingCase.StatusConstants.ACTIVE,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(case.title, 'Test Safeguarding Case')
        self.assertEqual(case.case_category, 'CHILD_PROTECTION')
        self.assertEqual(case.risk_level, 'HIGH')
        self.assertEqual(case.confidentiality_level, 'HIGHLY_CONFIDENTIAL')
        self.assertEqual(str(case), 'Test Safeguarding Case (CHILD_PROTECTION)')
    
    def test_incident_report_creation(self):
        """Test creating an incident report."""
        incident = IncidentReport.objects.create(
            title='Test Incident',
            incident_category='HEALTH_AND_SAFETY',
            description='This is a test incident.',
            date_occurred=timezone.now(),
            date_reported=timezone.now(),
            reported_by=self.user,
            location='Office',
            severity='MEDIUM',
            immediate_actions_taken='First aid administered',
            investigation_required=True,
            status=IncidentReport.StatusConstants.REPORTED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(incident.title, 'Test Incident')
        self.assertEqual(incident.incident_category, 'HEALTH_AND_SAFETY')
        self.assertEqual(incident.severity, 'MEDIUM')
        self.assertEqual(str(incident), 'Test Incident (HEALTH_AND_SAFETY)')
    
    def test_complaint_creation(self):
        """Test creating a complaint."""
        complaint = Complaint.objects.create(
            title='Test Complaint',
            complaint_type='SERVICE_DELIVERY',
            description='This is a test complaint.',
            complainant_name='John Doe',
            complainant_contact='john@example.com',
            complainant_is_anonymous=False,
            reported_by=self.user,
            assigned_officer=self.user,
            status=Complaint.StatusConstants.OPEN,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(complaint.title, 'Test Complaint')
        self.assertEqual(complaint.complaint_type, 'SERVICE_DELIVERY')
        self.assertEqual(str(complaint), 'Test Complaint (SERVICE_DELIVERY)')
    
    def test_whistleblower_report_creation(self):
        """Test creating a whistleblower report."""
        report = WhistleblowerReport.objects.create(
            title='Test Whistleblower Report',
            report_type='FRAUD',
            description='This is a test whistleblower report.',
            reporter_is_anonymous=True,
            reported_by=self.user,
            assigned_investigator=self.user,
            status=WhistleblowerReport.StatusConstants.OPEN,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(report.title, 'Test Whistleblower Report')
        self.assertEqual(report.report_type, 'FRAUD')
        self.assertEqual(report.confidentiality_level, 'HIGHLY_CONFIDENTIAL')
        self.assertEqual(str(report), 'Test Whistleblower Report - Reporter: Anonymous')
    
    def test_capa_creation(self):
        """Test creating a CAPA."""
        capa = CorrectivePreventiveAction.objects.create(
            title='Test CAPA',
            action_type='BOTH',
            description='This is a test CAPA.',
            root_cause='Inadequate training',
            corrective_action_description='Provide training',
            preventive_action_description='Implement ongoing training program',
            responsible_officer=self.user,
            due_date=timezone.now().date() + timezone.timedelta(days=30),
            status=CorrectivePreventiveAction.StatusConstants.DRAFT,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(capa.title, 'Test CAPA')
        self.assertEqual(capa.action_type, 'BOTH')
        self.assertEqual(str(capa), 'Test CAPA (Both Corrective and Preventive)')
    
    def test_governance_meeting_creation(self):
        """Test creating a governance meeting."""
        meeting = GovernanceMeeting.objects.create(
            title='Test Meeting',
            meeting_type='BOARD',
            description='This is a test meeting.',
            scheduled_date=timezone.now() + timezone.timedelta(days=7),
            meeting_chair=self.user,
            status=GovernanceMeeting.StatusConstants.SCHEDULED,
            created_by=self.user,
            updated_by=self.user
        )
        
        self.assertEqual(meeting.title, 'Test Meeting')
        self.assertEqual(meeting.meeting_type, 'BOARD')
        self.assertEqual(str(meeting), 'Test Meeting - ' + meeting.scheduled_date.strftime('%Y-%m-%d %H:%M'))