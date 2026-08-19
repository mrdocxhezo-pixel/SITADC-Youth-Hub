"""Governance form tests."""

from __future__ import annotations

from apps.governance.forms import (
    ComplaintForm,
    ComplianceAssessmentForm,
    ComplianceRequirementForm,
    ConflictOfInterestDeclarationForm,
    CorrectivePreventiveActionForm,
    DocumentForm,
    EthicsCaseForm,
    GovernanceMeetingForm,
    IncidentReportForm,
    InternalControlForm,
    MeetingAttendanceForm,
    PolicyAcknowledgementForm,
    PolicyForm,
    PolicyVersionForm,
    RiskAssessmentForm,
    RiskRegisterForm,
    RiskTreatmentPlanForm,
    SafeguardingCaseForm,
    WhistleblowerReportForm,
)

from .base import GovernanceTestCase


class GovernanceFormTests(GovernanceTestCase):
    """Tests for governance forms."""

    def test_policy_form_valid(self):
        """Test PolicyForm with valid data."""
        form = PolicyForm(
            data={
                "title": "Test Policy",
                "policy_category": "HR",
                "description": "Test policy description",
                "version": "1.0",
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid())

    def test_policy_form_invalid_missing_title(self):
        """Test PolicyForm with missing title."""
        form = PolicyForm(
            data={
                "policy_category": "HR",
                "description": "Test policy",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_risk_register_form_valid(self):
        """Test RiskRegisterForm with valid data."""
        form = RiskRegisterForm(
            data={
                "title": "Test Risk",
                "risk_category": "FINANCIAL",
                "description": "Test risk",
                "likelihood": 3,
                "impact": 4,
                "mitigation_strategy": "Mitigate",
                "review_date": "2025-12-31",
                "status": "ACTIVE",
            }
        )
        self.assertTrue(form.is_valid())

    def test_risk_register_form_invalid_likelihood(self):
        """Test RiskRegisterForm with invalid likelihood."""
        form = RiskRegisterForm(
            data={
                "title": "Test Risk",
                "risk_category": "FINANCIAL",
                "description": "Test risk",
                "likelihood": 6,  # Invalid: > 5
                "impact": 4,
                "mitigation_strategy": "Mitigate",
                "review_date": "2025-12-31",
                "status": "ACTIVE",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("likelihood", form.errors)

    def test_risk_assessment_form_valid(self):
        """Test RiskAssessmentForm with valid data."""
        risk = self.create_risk()
        form = RiskAssessmentForm(
            data={
                "risk_register": risk.pk,
                "assessment_type": "INITIAL",
                "assessed_by": self.user.pk,
                "assessment_date": "2025-06-15",
                "likelihood": 3,
                "impact": 4,
                "assessor_notes": "Notes",
            }
        )
        self.assertTrue(form.is_valid())

    def test_risk_treatment_form_valid(self):
        """Test RiskTreatmentPlanForm with valid data."""
        risk = self.create_risk()
        form = RiskTreatmentPlanForm(
            data={
                "risk_register": risk.pk,
                "treatment_type": "MITIGATE",
                "description": "Treatment plan",
                "responsible_officer": self.user.pk,
                "target_completion_date": "2025-12-31",
                "progress_percentage": 0,
            }
        )
        self.assertTrue(form.is_valid())

    def test_compliance_requirement_form_valid(self):
        """Test ComplianceRequirementForm with valid data."""
        form = ComplianceRequirementForm(
            data={
                "title": "Test Compliance",
                "compliance_type": "REGULATORY",
                "description": "Test compliance",
                "effective_date": "2025-01-01",
                "is_active": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_compliance_assessment_form_valid(self):
        """Test ComplianceAssessmentForm with valid data."""
        req = self.create_compliance_requirement()
        form = ComplianceAssessmentForm(
            data={
                "compliance_requirement": req.pk,
                "assessed_by": self.user.pk,
                "assessment_date": "2025-06-15",
                "assessment_period_start": "2025-01-01",
                "assessment_period_end": "2025-06-30",
                "result": "COMPLIANT",
                "findings": "All good",
            }
        )
        self.assertTrue(form.is_valid())

    def test_internal_control_form_valid(self):
        """Test InternalControlForm with valid data."""
        form = InternalControlForm(
            data={
                "title": "Test Control",
                "control_type": "FINANCIAL",
                "description": "Test control",
                "objective": "Ensure accuracy",
                "frequency": "MONTHLY",
                "is_effective": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_ethics_case_form_valid(self):
        """Test EthicsCaseForm with valid data."""
        form = EthicsCaseForm(
            data={
                "title": "Test Ethics Case",
                "case_type": "CONFLICT_OF_INTEREST",
                "description": "Test case",
                "reported_date": "2025-01-15",
                "status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_conflict_declaration_form_valid(self):
        """Test ConflictOfInterestDeclarationForm with valid data."""
        form = ConflictOfInterestDeclarationForm(
            data={
                "declarant": self.user.pk,
                "declaration_type": "FINANCIAL",
                "nature_of_conflict": "Financial interest",
                "date_declared": "2025-01-15",
                "review_date": "2026-01-15",
                "mitigation_measures": "Recuse",
                "approval_status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_safeguarding_case_form_valid(self):
        """Test SafeguardingCaseForm with valid data."""
        form = SafeguardingCaseForm(
            data={
                "title": "Test Safeguarding",
                "case_category": "CHILD_PROTECTION",
                "description": "Test case",
                "affected_individuals": "A.B.",
                "date_reported": "2025-01-15",
                "risk_level": "HIGH",
                "actions_taken": "Investigation",
                "status": "ACTIVE",
            }
        )
        self.assertTrue(form.is_valid())

    def test_incident_report_form_valid(self):
        """Test IncidentReportForm with valid data."""
        from django.utils import timezone

        form = IncidentReportForm(
            data={
                "title": "Test Incident",
                "incident_category": "HEALTH_AND_SAFETY",
                "description": "Test incident",
                "date_occurred": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "immediate_actions_taken": "Action taken",
                "severity": "MEDIUM",
                "status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_complaint_form_valid(self):
        """Test ComplaintForm with valid data."""
        form = ComplaintForm(
            data={
                "title": "Test Complaint",
                "complaint_type": "SERVICE_DELIVERY",
                "description": "Test complaint",
                "complainant_name": "John Doe",
                "complainant_contact": "john@example.com",
                "complainant_is_anonymous": False,
                "status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_complaint_form_anonymous(self):
        """Test ComplaintForm with anonymous complainant."""
        form = ComplaintForm(
            data={
                "title": "Anonymous Complaint",
                "complaint_type": "STAFF_CONDUCT",
                "description": "Anonymous complaint",
                "complainant_is_anonymous": True,
                "status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_whistleblower_report_form_valid(self):
        """Test WhistleblowerReportForm with valid data."""
        form = WhistleblowerReportForm(
            data={
                "title": "Test Report",
                "report_type": "FRAUD",
                "description": "Test report",
                "reporter_is_anonymous": True,
                "status": "PENDING_REVIEW",
            }
        )
        self.assertTrue(form.is_valid())

    def test_capa_form_valid(self):
        """Test CorrectivePreventiveActionForm with valid data."""
        incident = self.create_incident()
        form = CorrectivePreventiveActionForm(
            data={
                "title": "Test CAPA",
                "action_type": "BOTH",
                "description": "Test CAPA",
                "root_cause": "Root cause",
                "corrective_action_description": "Corrective action",
                "preventive_action_description": "Preventive action",
                "due_date": "2025-12-31",
                "source_incident": incident.pk,
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid())

    def test_document_form_valid(self):
        """Test DocumentForm with valid data."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        form = DocumentForm(
            data={
                "title": "Test Document",
                "document_type": "POLICY",
                "description": "Test document",
                "version": "1.0",
                "confidentiality_level": "INTERNAL",
            },
            files={
                "file": SimpleUploadedFile(
                    "test.pdf", b"%PDF-1.4 test", content_type="application/pdf"
                )
            },
        )
        self.assertTrue(form.is_valid())

    def test_governance_meeting_form_valid(self):
        """Test GovernanceMeetingForm with valid data."""
        from django.utils import timezone

        scheduled_date = (timezone.now() + timezone.timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M"
        )
        form = GovernanceMeetingForm(
            data={
                "title": "Test Meeting",
                "meeting_type": "BOARD",
                "governance_type": "GOVERNANCE_MEETING",
                "description": "Test meeting",
                "scheduled_date": scheduled_date,
                "status": "DRAFT",
            }
        )
        self.assertTrue(form.is_valid())

    def test_meeting_attendance_form_valid(self):
        """Test MeetingAttendanceForm with valid data."""
        meeting = self.create_meeting()
        form = MeetingAttendanceForm(
            data={
                "meeting": meeting.pk,
                "user": self.user.pk,
                "attendance_status": "PRESENT",
            }
        )
        self.assertTrue(form.is_valid())

    def test_policy_version_form_valid(self):
        """Test PolicyVersionForm with valid data."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        policy = self.create_policy()
        form = PolicyVersionForm(
            data={
                "policy": policy.pk,
                "version_number": "1.1",
                "effective_date": "2025-07-01",
                "changes_summary": "Updated section",
            },
            files={
                "document": SimpleUploadedFile(
                    "policy.pdf", b"%PDF-1.4 test", content_type="application/pdf"
                )
            },
        )
        self.assertTrue(form.is_valid())

    def test_policy_acknowledgement_form_valid(self):
        """Test PolicyAcknowledgementForm with valid data."""
        policy = self.create_policy()
        form = PolicyAcknowledgementForm(
            data={
                "policy": policy.pk,
                "user": self.user.pk,
                "is_current": True,
            }
        )
        self.assertTrue(form.is_valid())

    def test_form_css_classes(self):
        """Test that forms have proper CSS classes."""
        form = PolicyForm()
        for field in form.fields.values():
            self.assertIn("class", field.widget.attrs)
            self.assertTrue(
                "form-control" in field.widget.attrs["class"]
                or "form-select" in field.widget.attrs["class"]
                or "form-check-input" in field.widget.attrs["class"]
            )
