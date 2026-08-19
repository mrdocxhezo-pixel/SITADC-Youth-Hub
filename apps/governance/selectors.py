"""Governance, Risk, Compliance and Safeguarding selectors.

All selectors are fail-closed: a user without the relevant ``governance.*``
permission receives an empty queryset rather than data.  Highly confidential
record types (safeguarding cases, whistleblower reports) additionally require
the ``governance.view_confidential`` permission.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.utils import timezone

from apps.core.constants import StatusConstants
from apps.governance.constants import RISK_MATRIX_CRITICAL_MIN, RISK_MATRIX_MEDIUM_MIN
from apps.governance.models import (
    Complaint,
    ComplianceAssessment,
    ComplianceRequirement,
    ConflictOfInterestDeclaration,
    CorrectivePreventiveAction,
    Document,
    EthicsCase,
    GovernanceMeeting,
    GovernanceNotification,
    GovernanceTimeline,
    IncidentReport,
    InternalControl,
    MeetingAttendance,
    Policy,
    PolicyAcknowledgement,
    PolicyVersion,
    RiskAssessment,
    RiskRegister,
    RiskTreatmentPlan,
    SafeguardingCase,
    WhistleblowerReport,
)
from apps.governance.permissions import (
    user_can_view_capas,
    user_can_view_complaints,
    user_can_view_compliance,
    user_can_view_confidential_governance,
    user_can_view_controls,
    user_can_view_ethics,
    user_can_view_incidents,
    user_can_view_meetings,
    user_can_view_policies,
    user_can_view_risks,
    user_can_view_safeguarding,
    user_can_view_whistleblower,
)

User = get_user_model()


def get_accessible_policies(user: User) -> QuerySet[Policy]:
    """Policies the user may view (empty queryset when denied)."""
    from apps.governance.permissions import user_can_view_policies

    if not user_can_view_policies(user):
        return Policy.objects.none()
    return Policy.objects.all()


def get_accessible_policy_versions(user: User) -> QuerySet[PolicyVersion]:
    """Policy versions the user may view (empty queryset when denied)."""
    if not user_can_view_policies(user):
        return PolicyVersion.objects.none()
    return PolicyVersion.objects.all()


def get_accessible_policy_acknowledgements(
    user: User,
) -> QuerySet[PolicyAcknowledgement]:
    """Policy acknowledgements the user may view (empty queryset when denied)."""
    if not user_can_view_policies(user):
        return PolicyAcknowledgement.objects.none()
    return PolicyAcknowledgement.objects.all()


def get_accessible_risks(user: User) -> QuerySet[RiskRegister]:
    """Risks the user may view (empty queryset when denied)."""
    from apps.governance.permissions import user_can_view_risks

    if not user_can_view_risks(user):
        return RiskRegister.objects.none()
    return RiskRegister.objects.all()


def get_accessible_risk_assessments(user: User) -> QuerySet[RiskAssessment]:
    """Risk assessments the user may view (empty queryset when denied)."""
    if not user_can_view_risks(user):
        return RiskAssessment.objects.none()
    return RiskAssessment.objects.all()


def get_accessible_risk_treatment_plans(user: User) -> QuerySet[RiskTreatmentPlan]:
    """Risk treatment plans the user may view (empty queryset when denied)."""
    if not user_can_view_risks(user):
        return RiskTreatmentPlan.objects.none()
    return RiskTreatmentPlan.objects.all()


def get_accessible_compliance_requirements(
    user: User,
) -> QuerySet[ComplianceRequirement]:
    """Compliance requirements the user may view (empty queryset when denied)."""
    if not user_can_view_compliance(user):
        return ComplianceRequirement.objects.none()
    return ComplianceRequirement.objects.all()


def get_accessible_compliance_assessments(user: User) -> QuerySet[ComplianceAssessment]:
    """Compliance assessments the user may view (empty queryset when denied)."""
    if not user_can_view_compliance(user):
        return ComplianceAssessment.objects.none()
    return ComplianceAssessment.objects.all()


def get_accessible_internal_controls(user: User) -> QuerySet[InternalControl]:
    """Internal controls the user may view (empty queryset when denied)."""
    if not user_can_view_controls(user):
        return InternalControl.objects.none()
    return InternalControl.objects.all()


def get_accessible_ethics_cases(user: User) -> QuerySet[EthicsCase]:
    """Ethics cases the user may view (empty queryset when denied)."""
    if not user_can_view_ethics(user):
        return EthicsCase.objects.none()
    return EthicsCase.objects.all()


def get_accessible_conflict_declarations(
    user: User,
) -> QuerySet[ConflictOfInterestDeclaration]:
    """Conflict of interest declarations the user may view."""
    if not user_can_view_ethics(user):
        return ConflictOfInterestDeclaration.objects.none()
    return ConflictOfInterestDeclaration.objects.all()


def get_accessible_safeguarding_cases(user: User) -> QuerySet[SafeguardingCase]:
    """Safeguarding cases the user may view (empty queryset when denied)."""
    if not user_can_view_safeguarding(user):
        return SafeguardingCase.objects.none()
    return SafeguardingCase.objects.all()


def get_accessible_incidents(user: User) -> QuerySet[IncidentReport]:
    """Incident reports the user may view (empty queryset when denied)."""
    if not user_can_view_incidents(user):
        return IncidentReport.objects.none()
    return IncidentReport.objects.all()


def get_accessible_complaints(user: User) -> QuerySet[Complaint]:
    """Complaints the user may view (empty queryset when denied)."""
    if not user_can_view_complaints(user):
        return Complaint.objects.none()
    return Complaint.objects.all()


def get_accessible_whistleblower_reports(user: User) -> QuerySet[WhistleblowerReport]:
    """Whistleblower reports the user may view (empty queryset when denied)."""
    if not user_can_view_whistleblower(user):
        return WhistleblowerReport.objects.none()
    return WhistleblowerReport.objects.all()


def get_accessible_capas(user: User) -> QuerySet[CorrectivePreventiveAction]:
    """CAPA records the user may view (empty queryset when denied)."""
    if not user_can_view_capas(user):
        return CorrectivePreventiveAction.objects.none()
    return CorrectivePreventiveAction.objects.all()


def get_accessible_documents(user: User) -> QuerySet[Document]:
    """Governance documents the user may view (empty queryset when denied)."""
    if not user_can_view_policies(user):
        return Document.objects.none()
    return Document.objects.all()


def get_accessible_meetings(user: User) -> QuerySet[GovernanceMeeting]:
    """Governance meetings the user may view (empty queryset when denied)."""
    if not user_can_view_meetings(user):
        return GovernanceMeeting.objects.none()
    return GovernanceMeeting.objects.all()


def get_accessible_meeting_attendance(user: User) -> QuerySet[MeetingAttendance]:
    """Meeting attendance records the user may view."""
    if not user_can_view_meetings(user):
        return MeetingAttendance.objects.none()
    return MeetingAttendance.objects.all()


def get_accessible_notifications(user: User) -> QuerySet[GovernanceNotification]:
    """Governance notifications the user may view (empty queryset when denied)."""
    if not user_can_view_meetings(user):
        return GovernanceNotification.objects.none()
    return GovernanceNotification.objects.all()


def get_accessible_timeline(user: User) -> QuerySet[GovernanceTimeline]:
    """Governance timeline events the user may view (empty queryset when denied)."""
    if not user_can_view_meetings(user):
        return GovernanceTimeline.objects.none()
    return GovernanceTimeline.objects.all()


def get_policy_compliance_rate(user: User) -> float:
    """Percentage of active policies that have been acknowledged."""
    policies = get_accessible_policies(user).filter(status=StatusConstants.ACTIVE)
    total = policies.count()
    if total == 0:
        return 0.0
    acknowledged = 0
    for policy in policies:
        if policy.acknowledgements.filter(is_current=True).exists():
            acknowledged += 1
    return round(acknowledged / total * 100, 2)


def get_high_risk_items(user: User) -> QuerySet[RiskRegister]:
    """Active risks rated HIGH or CRITICAL, ordered by risk score."""
    from django.db.models import F

    return (
        get_accessible_risks(user)
        .filter(status=StatusConstants.ACTIVE)
        .annotate(computed_risk_score=F("likelihood") * F("impact"))
        .filter(computed_risk_score__gte=RISK_MATRIX_MEDIUM_MIN)
        .order_by("-computed_risk_score")
    )


def get_critical_risk_count(user: User) -> int:
    """Count of active CRITICAL risks."""
    from django.db.models import F

    return (
        get_accessible_risks(user)
        .filter(status=StatusConstants.ACTIVE)
        .annotate(computed_risk_score=F("likelihood") * F("impact"))
        .filter(computed_risk_score__gte=RISK_MATRIX_CRITICAL_MIN)
        .count()
    )


def get_high_risk_count(user: User) -> int:
    """Count of active HIGH or CRITICAL risks."""
    return get_high_risk_items(user).count()


def get_compliance_status(user: User) -> dict:
    """Aggregate compliance assessment results."""
    assessments = get_accessible_compliance_assessments(user)
    total = assessments.count()
    status = {
        "total": total,
        "compliant": assessments.filter(result="COMPLIANT").count(),
        "partially_compliant": assessments.filter(result="PARTIALLY_COMPLIANT").count(),
        "non_compliant": assessments.filter(result="NON_COMPLIANT").count(),
        "not_applicable": assessments.filter(result="NOT_APPLICABLE").count(),
    }
    if total > 0:
        status["compliance_rate"] = round(status["compliant"] / total * 100, 2)
    else:
        status["compliance_rate"] = 0.0
    return status


def get_upcoming_governance_deadlines(user: User, days: int = 30) -> list[Any]:
    """Upcoming governance review deadlines across policies and risks."""
    now = timezone.now().date()
    horizon = now + timezone.timedelta(days=days)
    deadlines: list[Any] = []

    for policy in get_accessible_policies(user).filter(
        review_date__isnull=False,
        review_date__gte=now,
        review_date__lte=horizon,
        status=StatusConstants.ACTIVE,
    ):
        deadlines.append(
            {
                "type": "Policy Review",
                "title": policy.title,
                "reference_number": policy.reference_number,
                "date": policy.review_date,
            }
        )

    for risk in get_accessible_risks(user).filter(
        review_date__gte=now,
        review_date__lte=horizon,
        status=StatusConstants.ACTIVE,
    ):
        deadlines.append(
            {
                "type": "Risk Review",
                "title": risk.title,
                "reference_number": getattr(risk, "reference_number", ""),
                "date": risk.review_date,
            }
        )

    deadlines.sort(key=lambda item: item["date"])
    return deadlines[:20]


def get_governance_summary(user: User) -> dict:
    """Compact aggregate counts for the governance dashboard."""
    return {
        "total_policies": get_accessible_policies(user).count(),
        "pending_policies": get_accessible_policies(user)
        .filter(status__in=[StatusConstants.DRAFT, StatusConstants.PENDING_REVIEW])
        .count(),
        "total_risks": get_accessible_risks(user)
        .filter(status=StatusConstants.ACTIVE)
        .count(),
        "high_risks": get_high_risk_count(user),
        "critical_risks": get_critical_risk_count(user),
        "total_safeguarding_cases": get_accessible_safeguarding_cases(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_compliance_reqs": get_accessible_compliance_requirements(user)
        .filter(is_active=True)
        .count(),
        "total_controls": get_accessible_internal_controls(user)
        .filter(is_effective=True)
        .count(),
        "total_ethics_cases": get_accessible_ethics_cases(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_incidents": get_accessible_incidents(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_complaints": get_accessible_complaints(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_whistleblower_reports": get_accessible_whistleblower_reports(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_capas": get_accessible_capas(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "total_documents": get_accessible_documents(user).count(),
        "total_meetings": get_accessible_meetings(user)
        .exclude(status=StatusConstants.ARCHIVED)
        .count(),
        "policy_compliance_rate": get_policy_compliance_rate(user),
    }


def get_recent_policies(user: User, limit: int = 5) -> QuerySet[Policy]:
    """Most recently created policies accessible to the user."""
    return get_accessible_policies(user).order_by("-created_at")[:limit]


def get_recent_risks(user: User, limit: int = 5) -> QuerySet[RiskRegister]:
    """Most recently created risks accessible to the user."""
    return get_accessible_risks(user).order_by("-created_at")[:limit]


def get_recent_incidents(user: User, limit: int = 5) -> QuerySet[IncidentReport]:
    """Most recently reported incidents accessible to the user."""
    return get_accessible_incidents(user).order_by("-created_at")[:limit]


def get_recent_complaints(user: User, limit: int = 5) -> QuerySet[Complaint]:
    """Most recently received complaints accessible to the user."""
    return get_accessible_complaints(user).order_by("-created_at")[:limit]


def get_upcoming_meetings(user: User, limit: int = 5) -> QuerySet[GovernanceMeeting]:
    """Upcoming governance meetings accessible to the user."""
    return (
        get_accessible_meetings(user)
        .filter(scheduled_date__gte=timezone.now())
        .order_by("scheduled_date")[:limit]
    )


def get_unread_notification_count(user: User) -> int:
    """Unread governance notifications addressed to the user."""
    return GovernanceNotification.objects.filter(recipient=user, is_read=False).count()


def can_view_confidential(user: User) -> bool:
    """Whether the user may view highly confidential governance records."""
    return user_can_view_confidential_governance(user)
