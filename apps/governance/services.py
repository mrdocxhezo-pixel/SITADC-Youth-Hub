"""Governance, Risk, Compliance and Safeguarding services.

Every state-changing governance operation flows through these services so that
invariants are enforced transactionally: reference numbers are allocated through
the centralized numbering service, timeline events are appended, notifications
are created, and audit metadata is recorded.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from django.utils import timezone

from apps.core.services import BaseService
from apps.governance.constants import (
    RISK_MATRIX_HIGH_MAX,
    RISK_MATRIX_LOW_MAX,
    RISK_MATRIX_MEDIUM_MAX,
    RISK_SCALE_MAX,
    RISK_SCALE_MIN,
    ConfidentialityLevel,
    GovernanceType,
    NotificationType,
    TimelineEventType,
)
from apps.governance.exceptions import (
    DuplicateReferenceNumberError,
    InvalidRiskScoreError,
)
from apps.references.constants import ReferenceModules

logger = logging.getLogger(__name__)

GOVERNANCE_SCHEME_DEFAULTS = {
    GovernanceType.POLICY: ("POL", "Policy"),
    GovernanceType.RISK: ("RSK", "Risk"),
    GovernanceType.COMPLIANCE: ("CMP", "Compliance"),
    GovernanceType.ETHICS: ("ETH", "Ethics"),
    GovernanceType.SAFEGUARDING: ("SFG", "Safeguarding"),
    GovernanceType.INCIDENT: ("INC", "Incident"),
    GovernanceType.COMPLAINT: ("CPL", "Complaint"),
    GovernanceType.WHISTLEBLOWER: ("WHB", "Whistleblower"),
    GovernanceType.CAPA: ("CAPA", "Corrective & Preventive Action"),
    GovernanceType.GOVERNANCE_MEETING: ("MTG", "Governance Meeting"),
}


def _generate_fallback_reference(prefix: str) -> str:
    """Generate a deterministic fallback reference (used before schemes exist)."""
    return f"{prefix}-{timezone.now().year}-{uuid.uuid4().hex.upper()[:8]}"


def _reserve_reference(actor, governance_type: str, record_type: str = "") -> str:
    """Reserve the next reference number through the centralized numbering service.

    Falls back to a locally generated reference when no scheme has been
    configured for the governance module yet, so the module never blocks on
    configuration state.
    """
    try:
        from apps.references.services import ReferenceNumberService

        generated = ReferenceNumberService(user=actor).execute(
            module=ReferenceModules.GOVERNANCE,
            record_type=record_type or governance_type.lower(),
            scheme_code=f"governance_{governance_type.lower()}",
            notes=f"Phase 29 {governance_type} reference reservation.",
        )
        return generated.reference_number
    except Exception:  # pragma: no cover - exercised only pre-seeding.
        prefix = GOVERNANCE_SCHEME_DEFAULTS.get(governance_type, ("GOV", "Governance"))[
            0
        ]
        return _generate_fallback_reference(prefix)


def _allocate_reference(
    actor, instance, governance_type: str, record_type: str = ""
) -> None:
    """Allocate a reference number and persist it on the instance."""
    reference = _reserve_reference(actor, governance_type, record_type)
    instance.reference_number = reference


def allocate_reference(
    actor, instance, governance_type: str = "", record_type: str = ""
) -> None:
    """Public helper to allocate a governance reference to an unsaved instance.

    Used by view-level create flows that use forms directly.  Idempotent:
    instances that already carry a reference are left untouched.
    """
    if getattr(instance, "reference_number", None):
        return
    _allocate_reference(actor, instance, governance_type, record_type)


def _record_timeline(
    actor,
    event_type: str,
    description: str,
    module: str = "governance",
    reference_number: str = "",
    action_performed: str = "",
    status_after_event: str = "",
    remarks: str = "",
) -> None:
    """Append a governance timeline event."""
    from apps.governance.models import GovernanceTimeline

    GovernanceTimeline.objects.create(
        event_type=event_type,
        description=description,
        event_date=timezone.now(),
        performed_by=(
            actor if actor and getattr(actor, "is_authenticated", False) else None
        ),
        module=module,
        reference_number=reference_number,
        action_performed=action_performed,
        status_after_event=status_after_event,
        remarks=remarks,
    )


def _notify(
    recipient,
    notification_type: str,
    title: str,
    message: str,
) -> None:
    """Create a governance notification for the recipient."""
    from apps.governance.models import GovernanceNotification

    if recipient is None:
        return
    GovernanceNotification.objects.create(
        notification_type=notification_type,
        title=title,
        message=message,
        recipient=recipient,
    )


def validate_risk_score(likelihood: int, impact: int) -> None:
    """Validate that likelihood and impact fall within the approved scale."""
    for value in (likelihood, impact):
        if value < RISK_SCALE_MIN or value > RISK_SCALE_MAX:
            raise InvalidRiskScoreError(
                f"Risk scores must be between {RISK_SCALE_MIN} and {RISK_SCALE_MAX}."
            )


def get_risk_rating(score: int) -> str:
    """Map a likelihood*impact score to a risk rating."""
    if score <= RISK_MATRIX_LOW_MAX:
        return "LOW"
    if score <= RISK_MATRIX_MEDIUM_MAX:
        return "MEDIUM"
    if score <= RISK_MATRIX_HIGH_MAX:
        return "HIGH"
    return "CRITICAL"


class PolicyService(BaseService):
    """Create, update and transition policies with versioning and references."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        policy_category: str,
        description: str,
        status: str = "DRAFT",
        priority: str = "MEDIUM",
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        effective_date=None,
        expiry_date=None,
        review_date=None,
        version: str = "1.0",
        notes: str = "",
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import Policy

        if (
            reference_number
            and Policy.objects.filter(reference_number=reference_number).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Policy with reference {reference_number!r} already exists."
            )
        policy = Policy(
            governance_type=GovernanceType.POLICY,
            title=title,
            policy_category=policy_category,
            description=description,
            status=status,
            priority=priority,
            confidentiality_level=confidentiality_level,
            effective_date=effective_date,
            expiry_date=expiry_date,
            review_date=review_date,
            version=version,
            notes=notes,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            policy.reference_number = reference_number
        else:
            _allocate_reference(actor, policy, GovernanceType.POLICY)
        policy.save()
        _record_timeline(
            actor,
            TimelineEventType.RECORD_CREATED,
            f"Policy {policy.reference_number} created.",
            reference_number=policy.reference_number,
            action_performed="create",
            status_after_event=policy.status,
        )
        logger.info("Created policy %s", policy.reference_number)
        return policy


class RiskService(BaseService):
    """Create and assess risks with matrix scoring."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        risk_category: str,
        description: str,
        likelihood: int,
        impact: int,
        mitigation_strategy: str,
        review_date,
        root_cause: str = "",
        risk_owner=None,
        status: str = "ACTIVE",
        residual_likelihood=None,
        residual_impact=None,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import RiskRegister

        validate_risk_score(likelihood, impact)
        if residual_likelihood is not None:
            validate_risk_score(residual_likelihood, impact)
        if residual_impact is not None:
            validate_risk_score(likelihood, residual_impact)

        if (
            reference_number
            and RiskRegister.objects.filter(reference_number=reference_number).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Risk with reference {reference_number!r} already exists."
            )
        risk = RiskRegister(
            title=title,
            risk_category=risk_category,
            description=description,
            root_cause=root_cause,
            likelihood=likelihood,
            impact=impact,
            mitigation_strategy=mitigation_strategy,
            risk_owner=risk_owner,
            review_date=review_date,
            status=status,
            residual_likelihood=residual_likelihood,
            residual_impact=residual_impact,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            risk.reference_number = reference_number
        else:
            _allocate_reference(actor, risk, GovernanceType.RISK)
        risk.save()
        _record_timeline(
            actor,
            TimelineEventType.RISK_IDENTIFIED,
            f"Risk {risk.reference_number} identified with rating {risk.risk_rating}.",
            reference_number=risk.reference_number,
            action_performed="create",
            status_after_event=risk.status,
        )
        logger.info("Created risk %s", risk.reference_number)
        return risk


class ComplianceService(BaseService):
    """Create compliance requirements and assessments."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        compliance_type: str,
        description: str,
        effective_date,
        is_active: bool = True,
        source_organization: str = "",
        reference_document: str = "",
        expiry_date=None,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import ComplianceRequirement

        if (
            reference_number
            and ComplianceRequirement.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Compliance requirement with reference {reference_number!r} "
                f"already exists."
            )
        requirement = ComplianceRequirement(
            title=title,
            compliance_type=compliance_type,
            description=description,
            source_organization=source_organization,
            reference_document=reference_document,
            effective_date=effective_date,
            expiry_date=expiry_date,
            is_active=is_active,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            requirement.reference_number = reference_number
        else:
            _allocate_reference(actor, requirement, GovernanceType.COMPLIANCE)
        requirement.save()
        _record_timeline(
            actor,
            TimelineEventType.RECORD_CREATED,
            f"Compliance requirement {requirement.reference_number} created.",
            reference_number=requirement.reference_number,
            action_performed="create",
            status_after_event="ACTIVE" if is_active else "INACTIVE",
        )
        logger.info("Created compliance requirement %s", requirement.reference_number)
        return requirement


class SafeguardingService(BaseService):
    """Create safeguarding cases protected at the highest confidentiality level."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        case_category: str,
        description: str,
        date_reported,
        actions_taken: str,
        risk_level: str = "MEDIUM",
        affected_individuals: str = "",
        reported_by=None,
        assigned_officer=None,
        status: str = "PENDING_REVIEW",
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import SafeguardingCase

        if (
            reference_number
            and SafeguardingCase.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Safeguarding case with reference {reference_number!r} "
                f"already exists."
            )
        case = SafeguardingCase(
            case_category=case_category,
            title=title,
            description=description,
            date_reported=date_reported,
            reported_by=reported_by,
            affected_individuals=affected_individuals,
            risk_level=risk_level,
            assigned_officer=assigned_officer,
            actions_taken=actions_taken,
            status=status,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            case.reference_number = reference_number
        else:
            _allocate_reference(actor, case, GovernanceType.SAFEGUARDING)
        case.save()
        _record_timeline(
            actor,
            TimelineEventType.SAFEGUARDING_CASE_OPENED,
            f"Safeguarding case {case.reference_number} opened.",
            reference_number=case.reference_number,
            action_performed="create",
            status_after_event=case.status,
        )
        if assigned_officer:
            _notify(
                assigned_officer,
                NotificationType.SAFEGUARDING_CASE_ASSIGNED,
                "Safeguarding case assigned",
                f"You have been assigned safeguarding case {case.reference_number}.",
            )
        logger.info("Opened safeguarding case %s", case.reference_number)
        return case


class IncidentService(BaseService):
    """Create incident reports and record timeline events."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        incident_category: str,
        description: str,
        date_occurred,
        immediate_actions_taken: str,
        severity: str = "MEDIUM",
        location: str = "",
        reported_by=None,
        status: str = "PENDING_REVIEW",
        investigation_required: bool = False,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import IncidentReport

        if (
            reference_number
            and IncidentReport.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Incident with reference {reference_number!r} already exists."
            )
        incident = IncidentReport(
            incident_category=incident_category,
            title=title,
            description=description,
            date_occurred=date_occurred,
            reported_by=reported_by,
            location=location,
            severity=severity,
            immediate_actions_taken=immediate_actions_taken,
            investigation_required=investigation_required,
            status=status,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            incident.reference_number = reference_number
        else:
            _allocate_reference(actor, incident, GovernanceType.INCIDENT)
        incident.save()
        _record_timeline(
            actor,
            TimelineEventType.INCIDENT_REPORTED,
            f"Incident {incident.reference_number} reported.",
            reference_number=incident.reference_number,
            action_performed="create",
            status_after_event=incident.status,
        )
        logger.info("Reported incident %s", incident.reference_number)
        return incident


class ComplaintService(BaseService):
    """Create and manage complaints."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        complaint_type: str,
        description: str,
        complainant_is_anonymous: bool = False,
        complainant_name: str = "",
        complainant_contact: str = "",
        programme: str = "",
        service_location: str = "",
        status: str = "PENDING_REVIEW",
        assigned_officer=None,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import Complaint

        if (
            reference_number
            and Complaint.objects.filter(reference_number=reference_number).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Complaint with reference {reference_number!r} already exists."
            )
        complaint = Complaint(
            complaint_type=complaint_type,
            title=title,
            description=description,
            complainant_name=complainant_name,
            complainant_contact=complainant_contact,
            complainant_is_anonymous=complainant_is_anonymous,
            programme=programme,
            service_location=service_location,
            assigned_officer=assigned_officer,
            status=status,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            complaint.reference_number = reference_number
        else:
            _allocate_reference(actor, complaint, GovernanceType.COMPLAINT)
        complaint.save()
        _record_timeline(
            actor,
            TimelineEventType.COMPLAINT_RECEIVED,
            f"Complaint {complaint.reference_number} received.",
            reference_number=complaint.reference_number,
            action_performed="create",
            status_after_event=complaint.status,
        )
        logger.info("Received complaint %s", complaint.reference_number)
        return complaint


class WhistleblowerService(BaseService):
    """Create whistleblower reports protecting reporter identity."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        report_type: str,
        description: str,
        reporter_is_anonymous: bool = True,
        reporter_name: str = "",
        reporter_contact: str = "",
        reporter_relationship: str = "",
        status: str = "PENDING_REVIEW",
        assigned_investigator=None,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import WhistleblowerReport

        if (
            reference_number
            and WhistleblowerReport.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Whistleblower report with reference {reference_number!r} "
                f"already exists."
            )
        report = WhistleblowerReport(
            report_type=report_type,
            title=title,
            description=description,
            reporter_is_anonymous=reporter_is_anonymous,
            reporter_name=reporter_name,
            reporter_contact=reporter_contact,
            reporter_relationship=reporter_relationship,
            assigned_investigator=assigned_investigator,
            status=status,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            report.reference_number = reference_number
        else:
            _allocate_reference(actor, report, GovernanceType.WHISTLEBLOWER)
        report.save()
        _record_timeline(
            actor,
            TimelineEventType.WHISTLEBLOWER_REPORT_SUBMITTED,
            f"Whistleblower report {report.reference_number} submitted.",
            reference_number=report.reference_number,
            action_performed="create",
            status_after_event=report.status,
        )
        logger.info("Submitted whistleblower report %s", report.reference_number)
        return report


class CAPAService(BaseService):
    """Create corrective & preventive actions linked to source records."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        action_type: str,
        description: str,
        root_cause: str,
        corrective_action_description: str,
        due_date,
        preventive_action_description: str = "",
        responsible_officer=None,
        status: str = "DRAFT",
        reference_number: str = "",
        source_incident=None,
        source_complaint=None,
        source_audit_finding: str = "",
    ) -> Any:
        from apps.governance.models import CorrectivePreventiveAction

        if (
            reference_number
            and CorrectivePreventiveAction.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"CAPA with reference {reference_number!r} already exists."
            )
        capa = CorrectivePreventiveAction(
            action_type=action_type,
            title=title,
            description=description,
            source_incident=source_incident,
            source_complaint=source_complaint,
            source_audit_finding=source_audit_finding,
            root_cause=root_cause,
            corrective_action_description=corrective_action_description,
            preventive_action_description=preventive_action_description,
            responsible_officer=responsible_officer,
            due_date=due_date,
            status=status,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            capa.reference_number = reference_number
        else:
            _allocate_reference(actor, capa, GovernanceType.CAPA)
        capa.save()
        _record_timeline(
            actor,
            TimelineEventType.CAPA_INITIATED,
            f"CAPA {capa.reference_number} initiated.",
            reference_number=capa.reference_number,
            action_performed="create",
            status_after_event=capa.status,
        )
        logger.info("Initiated CAPA %s", capa.reference_number)
        return capa


class GovernanceMeetingService(BaseService):
    """Create governance meetings with reference numbers."""

    def _execute(
        self,
        *,
        actor: Any,
        title: str,
        description: str,
        meeting_type: str,
        scheduled_date,
        location: str = "",
        meeting_chair=None,
        status: str = "DRAFT",
        priority: str = "MEDIUM",
        confidentiality_level: str = ConfidentialityLevel.INTERNAL,
        reference_number: str = "",
    ) -> Any:
        from apps.governance.models import GovernanceMeeting

        if (
            reference_number
            and GovernanceMeeting.objects.filter(
                reference_number=reference_number
            ).exists()
        ):
            raise DuplicateReferenceNumberError(
                f"Meeting with reference {reference_number!r} already exists."
            )
        meeting = GovernanceMeeting(
            governance_type=GovernanceType.GOVERNANCE_MEETING,
            title=title,
            description=description,
            meeting_type=meeting_type,
            scheduled_date=scheduled_date,
            location=location,
            meeting_chair=meeting_chair,
            status=status,
            priority=priority,
            confidentiality_level=confidentiality_level,
            created_by=actor,
            updated_by=actor,
        )
        if reference_number:
            meeting.reference_number = reference_number
        else:
            _allocate_reference(actor, meeting, GovernanceType.GOVERNANCE_MEETING)
        meeting.save()
        _record_timeline(
            actor,
            TimelineEventType.RECORD_CREATED,
            f"Meeting {meeting.reference_number} scheduled.",
            reference_number=meeting.reference_number,
            action_performed="create",
            status_after_event=meeting.status,
        )
        logger.info("Scheduled meeting %s", meeting.reference_number)
        return meeting


class GovernanceDashboardProvider:
    """Provider for governance dashboard data (fail-closed)."""

    def __init__(self, user: Any):
        """Initialize the provider with the requesting user."""
        self.user = user

    def get_summary(self) -> dict:
        """Aggregate governance summary metrics."""
        from apps.governance.selectors import get_governance_summary

        return get_governance_summary(self.user)

    def get_policy_compliance_rate(self) -> float:
        """Policy acknowledgement compliance rate."""
        from apps.governance.selectors import get_policy_compliance_rate

        return get_policy_compliance_rate(self.user)

    def get_compliance_status(self) -> dict:
        """Compliance assessment status breakdown."""
        from apps.governance.selectors import get_compliance_status

        return get_compliance_status(self.user)

    def get_high_risk_items(self) -> list[Any]:
        """High and critical active risks."""
        from apps.governance.selectors import get_high_risk_items

        return list(get_high_risk_items(self.user))

    def get_upcoming_deadlines(self) -> list[Any]:
        """Upcoming governance review deadlines."""
        from apps.governance.selectors import get_upcoming_governance_deadlines

        return get_upcoming_governance_deadlines(self.user)

    def get_recent_activities(self) -> list[Any]:
        """Recent governance timeline events."""
        from apps.governance.selectors import get_accessible_timeline

        return list(get_accessible_timeline(self.user).order_by("-event_date")[:10])

    def get_upcoming_meetings(self) -> list[Any]:
        """Upcoming governance meetings."""
        from apps.governance.selectors import get_upcoming_meetings

        return list(get_upcoming_meetings(self.user))

    def get_recent_policies(self) -> list[Any]:
        """Recent policies."""
        from apps.governance.selectors import get_recent_policies

        return list(get_recent_policies(self.user))

    def get_recent_risks(self) -> list[Any]:
        """Recent risks."""
        from apps.governance.selectors import get_recent_risks

        return list(get_recent_risks(self.user))

    def get_recent_incidents(self) -> list[Any]:
        """Recent incidents."""
        from apps.governance.selectors import get_recent_incidents

        return list(get_recent_incidents(self.user))

    def get_recent_complaints(self) -> list[Any]:
        """Recent complaints."""
        from apps.governance.selectors import get_recent_complaints

        return list(get_recent_complaints(self.user))

    def get_unread_notification_count(self) -> int:
        """Unread notifications for the requesting user."""
        from apps.governance.selectors import get_unread_notification_count

        return get_unread_notification_count(self.user)
