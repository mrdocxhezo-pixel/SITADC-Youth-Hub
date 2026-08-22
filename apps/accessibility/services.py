"""Service layer for the Accessibility Review module (Phase 33)."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.db.models import Avg, Q
from django.utils import timezone

from apps.core.services import BaseService
from apps.rbac.authorization import user_has_permission
from apps.references.constants import ReferenceModules
from apps.references.services import ReferenceNumberService

from .constants import (
    ACCESSIBILITY_APPROVE,
    ACCESSIBILITY_AUDIT,
    ACCESSIBILITY_CONFIGURE,
    ACCESSIBILITY_CREATE,
    ACCESSIBILITY_MANAGE,
    ACCESSIBILITY_REPORT,
    ACCESSIBILITY_UPDATE,
    AccessibilityIssueStatus,
    AuditType,
    ComplianceStatus,
    SeverityLevel,
    WCAGLevel,
)
from .models import (
    AccessibilityAnalytics,
    AccessibilityAudit,
    AccessibilityComplianceRecord,
    AccessibilityConfiguration,
    AccessibilityException,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityNotification,
    AccessibilityPolicy,
    AccessibilityPreference,
    AccessibilityRecommendation,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
    WCAGCriterion,
)


def _require_permission(user, *codes: str) -> None:
    if user is None or not user.is_authenticated:
        raise PermissionDenied
    if user_has_permission(user, ACCESSIBILITY_MANAGE):
        return
    if any(user_has_permission(user, code) for code in codes):
        return
    raise PermissionDenied


def _log_timeline(
    actor,
    event_type: str,
    description: str,
    *,
    module: str = "",
    component: str = "",
    reference_number: str = "",
    wcag_criterion: str = "",
    severity: str = "",
    status_before: str = "",
    status_after: str = "",
    metadata: dict | None = None,
) -> AccessibilityTimeline:
    return AccessibilityTimeline.objects.create(
        event_type=event_type,
        description=description,
        performed_by=actor,
        module=module,
        component=component,
        reference_number=reference_number,
        wcag_criterion=wcag_criterion,
        severity=severity,
        status_before=status_before,
        status_after=status_after,
        metadata=metadata or {},
        created_by=actor,
        updated_by=actor,
    )


def _send_notification(
    actor,
    recipient,
    event_type: str,
    title: str,
    message: str,
    *,
    related_audit=None,
    related_finding=None,
    related_issue=None,
) -> AccessibilityNotification:
    notification = AccessibilityNotification.objects.create(
        event_type=event_type,
        title=title,
        message=message,
        recipient=recipient,
        related_audit=related_audit,
        related_finding=related_finding,
        related_issue=related_issue,
        sent_via_in_app=True,
        sent_at=timezone.now(),
        created_by=actor,
        updated_by=actor,
    )
    return notification


class AccessibilityBaseService(BaseService):
    """Base service for accessibility operations."""

    def __init__(self, user=None):
        super().__init__(user=user)
        self.actor = user

    def _require(self, *codes: str) -> None:
        _require_permission(self.actor, *codes)

    def _log(self, **kwargs) -> AccessibilityTimeline:
        return _log_timeline(self.actor, **kwargs)

    def _notify(self, **kwargs) -> AccessibilityNotification:
        return _send_notification(self.actor, **kwargs)


def _reserve_reference(actor, record_type: str) -> Any:
    return ReferenceNumberService(user=actor).execute(
        module=ReferenceModules.REPORTS,
        record_type=record_type,
        scheme_code="ACC",
        notes=f"Accessibility {record_type} reference reservation.",
    )


def _confirm_reference(actor, reference, record_id: str, record_type: str) -> None:
    from apps.references.services import ConfirmReferenceAssignmentService
    ConfirmReferenceAssignmentService(user=actor).execute(
        reference=reference,
        record_id=record_id,
        notes=f"Assigned to accessibility {record_type}.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Standard & Policy Services
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityStandardService(AccessibilityBaseService):
    """Manage accessibility standards."""

    def create(self, *, code: str, name: str, standard_type: str = "WCAG_2_2_AA", **kwargs) -> AccessibilityStandardRecord:
        self._require(ACCESSIBILITY_CREATE)
        standard = AccessibilityStandardRecord.objects.create(
            code=code,
            name=name,
            standard_type=standard_type,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        self._log(
            event_type="STANDARD_CREATED",
            description=f"Created accessibility standard: {name}",
            module="accessibility",
            reference_number=standard.code,
        )
        return standard

    def update(self, standard: AccessibilityStandardRecord, **fields) -> AccessibilityStandardRecord:
        self._require(ACCESSIBILITY_UPDATE)
        for name, value in fields.items():
            if value is not None and hasattr(standard, name):
                setattr(standard, name, value)
        standard.updated_by = self.actor
        standard.save()
        self._log(
            event_type="STANDARD_UPDATED",
            description=f"Updated accessibility standard: {standard.name}",
            module="accessibility",
            reference_number=standard.code,
        )
        return standard


class AccessibilityPolicyService(AccessibilityBaseService):
    """Manage accessibility policies."""

    def create(self, *, reference_number: str, title: str, standard: AccessibilityStandardRecord, category: str, **kwargs) -> AccessibilityPolicy:
        self._require(ACCESSIBILITY_CREATE)
        policy = AccessibilityPolicy.objects.create(
            reference_number=reference_number,
            title=title,
            standard=standard,
            category=category,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        self._log(
            event_type="POLICY_CREATED",
            description=f"Created accessibility policy: {title}",
            module="accessibility",
            reference_number=reference_number,
        )
        return policy

    def update(self, policy: AccessibilityPolicy, **fields) -> AccessibilityPolicy:
        self._require(ACCESSIBILITY_UPDATE)
        for name, value in fields.items():
            if value is not None and hasattr(policy, name):
                setattr(policy, name, value)
        policy.updated_by = self.actor
        policy.save()
        self._log(
            event_type="POLICY_UPDATED",
            description=f"Updated accessibility policy: {policy.title}",
            module="accessibility",
            reference_number=policy.reference_number,
        )
        return policy


# ──────────────────────────────────────────────────────────────────────────────
# Configuration & Preference Services
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityConfigurationService(AccessibilityBaseService):
    """Manage the centralized accessibility configuration."""

    def update(self, **fields) -> AccessibilityConfiguration:
        self._require(ACCESSIBILITY_CONFIGURE)
        config = AccessibilityConfiguration.load()
        for name, value in fields.items():
            if value is not None and hasattr(config, name):
                setattr(config, name, value)
        config.updated_by = self.actor
        config.save()
        self._log(
            event_type="CONFIGURATION_CHANGED",
            description="Updated accessibility configuration",
            module="accessibility",
            metadata=fields,
        )
        return config


class AccessibilityPreferenceService(AccessibilityBaseService):
    """Manage user accessibility preferences."""

    def get_or_create_for_user(self, user) -> AccessibilityPreference:
        return AccessibilityPreference.objects.get_or_create(user=user)[0]

    def update_preferences(self, user, **fields) -> AccessibilityPreference:
        if self.actor != user and not user_has_permission(self.actor, ACCESSIBILITY_MANAGE):
            raise PermissionDenied("Cannot modify another user's preferences.")
        prefs = self.get_or_create_for_user(user)
        for name, value in fields.items():
            if value is not None and hasattr(prefs, name):
                setattr(prefs, name, value)
        prefs.updated_by = self.actor
        prefs.save()
        self._log(
            event_type="PREFERENCE_CHANGED",
            description=f"Updated accessibility preferences for {user.get_full_name()}",
            module="accessibility",
            component="user_preferences",
            reference_number=user.username,
            metadata=fields,
        )
        return prefs


# ──────────────────────────────────────────────────────────────────────────────
# WCAG Criterion Service
# ──────────────────────────────────────────────────────────────────────────────

class WCAGCriterionService(AccessibilityBaseService):
    """Manage WCAG criteria."""

    def create(self, *, standard: AccessibilityStandardRecord, guideline_number: str, criterion_number: str, **kwargs) -> WCAGCriterion:
        self._require(ACCESSIBILITY_CONFIGURE)
        criterion = WCAGCriterion.objects.create(
            standard=standard,
            guideline_number=guideline_number,
            criterion_number=criterion_number,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        return criterion

    def get_applicable_criteria(self, standard: AccessibilityStandardRecord, target_level: str) -> models.QuerySet:
        level_order = {"A": 1, "AA": 2, "AAA": 3}
        target = level_order.get(target_level, 2)
        levels = [k for k, v in level_order.items() if v <= target]
        return WCAGCriterion.objects.filter(standard=standard, level__in=levels, is_active=True)


# ──────────────────────────────────────────────────────────────────────────────
# Audit Service
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityAuditService(AccessibilityBaseService):
    """Manage accessibility audits and findings."""

    def create_audit(
        self,
        *,
        name: str,
        audit_type: str,
        scope: str,
        standard: AccessibilityStandardRecord,
        module: str = "",
        component: str = "",
        page_url: str = "",
        auditor=None,
        **kwargs,
    ) -> AccessibilityAudit:
        self._require(ACCESSIBILITY_AUDIT)
        ref = _reserve_reference(self.actor, "audit")
        audit = AccessibilityAudit.objects.create(
            reference_number=ref.reference_number,
            name=name,
            audit_type=audit_type,
            scope=scope,
            module=module,
            component=component,
            page_url=page_url,
            standard=standard,
            auditor=auditor or self.actor,
            started_at=timezone.now(),
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        _confirm_reference(self.actor, ref, str(audit.pk), "audit")
        self._log(
            event_type="AUDIT_STARTED",
            description=f"Started accessibility audit: {name}",
            module=module or "accessibility",
            component=component,
            reference_number=audit.reference_number,
        )
        if auditor and auditor != self.actor:
            self._notify(
                recipient=auditor,
                event_type="ISSUE_ASSIGNED",
                title=f"Assigned to audit: {name}",
                message=f"You have been assigned as auditor for '{name}'.",
                related_audit=audit,
            )
        return audit

    def complete_audit(self, audit: AccessibilityAudit, *, summary: str = "", recommendations: str = "") -> AccessibilityAudit:
        self._require(ACCESSIBILITY_AUDIT)
        if audit.status == ComplianceStatus.COMPLIANT:
            return audit
        audit.completed_at = timezone.now()
        audit.summary = summary
        audit.recommendations = recommendations
        audit.updated_by = self.actor
        audit.save()
        self._log(
            event_type="AUDIT_COMPLETED",
            description=f"Completed accessibility audit: {audit.name} ({audit.get_status_display()})",
            module=audit.module,
            component=audit.component,
            reference_number=audit.reference_number,
        )
        if audit.auditor:
            self._notify(
                recipient=audit.auditor,
                event_type="AUDIT_COMPLETED",
                title=f"Audit completed: {audit.name}",
                message=f"The audit '{audit.name}' has been completed with score {audit.overall_score}%.",
                related_audit=audit,
            )
        return audit

    def add_finding(
        self,
        audit: AccessibilityAudit,
        *,
        criterion: WCAGCriterion,
        component: str,
        page_url: str = "",
        description: str,
        severity: str = SeverityLevel.MEDIUM,
        assigned_to=None,
        **kwargs,
    ) -> AccessibilityFinding:
        self._require(ACCESSIBILITY_AUDIT)
        finding = AccessibilityFinding.objects.create(
            audit=audit,
            criterion=criterion,
            component=component,
            page_url=page_url,
            description=description,
            severity=severity,
            assigned_to=assigned_to,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        audit.non_compliant_count += 1
        audit.save(update_fields=["non_compliant_count", "updated_at"])
        self._log(
            event_type="FINDING_CREATED",
            description=f"Created finding: {criterion} - {component}",
            module=audit.module,
            component=component,
            reference_number=audit.reference_number,
            wcag_criterion=f"{criterion.guideline_number}.{criterion.criterion_number}",
            severity=severity,
        )
        if assigned_to and assigned_to != self.actor:
            self._notify(
                recipient=assigned_to,
                event_type="ISSUE_ASSIGNED",
                title=f"Assigned finding: {criterion.title}",
                message=f"You have been assigned to fix: {description[:100]}",
                related_audit=audit,
                related_finding=finding,
            )
        return finding


# ──────────────────────────────────────────────────────────────────────────────
# Issue & Recommendation Services
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityIssueService(AccessibilityBaseService):
    """Manage accessibility issues reported outside audits."""

    def create_issue(
        self,
        *,
        title: str,
        source: str,
        module: str,
        component: str,
        page_url: str = "",
        description: str,
        severity: str = SeverityLevel.MEDIUM,
        reporter=None,
        assigned_to=None,
        **kwargs,
    ) -> AccessibilityIssue:
        self._require(ACCESSIBILITY_CREATE)
        ref = _reserve_reference(self.actor, "issue")
        issue = AccessibilityIssue.objects.create(
            reference_number=ref.reference_number,
            title=title,
            source=source,
            module=module,
            component=component,
            page_url=page_url,
            description=description,
            severity=severity,
            reporter=reporter or self.actor,
            assigned_to=assigned_to,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        _confirm_reference(self.actor, ref, str(issue.pk), "issue")
        self._log(
            event_type="ISSUE_REPORTED",
            description=f"Reported accessibility issue: {title}",
            module=module,
            component=component,
            reference_number=issue.reference_number,
            wcag_criterion=issue.criterion.criterion_number if issue.criterion else "",
            severity=severity,
        )
        if assigned_to and assigned_to != self.actor:
            self._notify(
                recipient=assigned_to,
                event_type="ISSUE_ASSIGNED",
                title=f"Assigned issue: {title}",
                message=f"You have been assigned to resolve: {description[:100]}",
                related_issue=issue,
            )
        return issue

    def resolve_issue(self, issue: AccessibilityIssue, *, resolution_notes: str, verified: bool = False) -> AccessibilityIssue:
        self._require(ACCESSIBILITY_UPDATE)
        if issue.status in (AccessibilityIssue.ACCESSIBILITY_ISSUE_STATUS.VERIFIED, AccessibilityIssue.ACCESSIBILITY_ISSUE_STATUS.WONT_FIX):
            raise ValidationError("Issue is already closed.")
        issue.status = AccessibilityIssueStatus.VERIFIED if verified else AccessibilityIssueStatus.IN_PROGRESS
        issue.resolution_notes = resolution_notes
        issue.resolved_by = self.actor
        issue.resolved_at = timezone.now()
        issue.updated_by = self.actor
        issue.save()
        self._log(
            event_type="ISSUE_RESOLVED",
            description=f"Resolved accessibility issue: {issue.title}",
            module=issue.module,
            component=issue.component,
            reference_number=issue.reference_number,
            severity=issue.severity,
            status_before=issue.status,
            status_after=issue.status,
        )
        if issue.reporter and issue.reporter != self.actor:
            self._notify(
                recipient=issue.reporter,
                event_type="ISSUE_RESOLVED",
                title=f"Issue resolved: {issue.title}",
                message=f"Your reported issue has been resolved: {resolution_notes[:100]}",
                related_issue=issue,
            )
        return issue


class AccessibilityRecommendationService(AccessibilityBaseService):
    """Manage accessibility improvement recommendations."""

    def create(self, *, title: str, description: str, priority: str = "MEDIUM", **kwargs) -> AccessibilityRecommendation:
        self._require(ACCESSIBILITY_CREATE)
        rec = AccessibilityRecommendation.objects.create(
            title=title,
            description=description,
            priority=priority,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        self._log(
            event_type="RECOMMENDATION_CREATED",
            description=f"Created accessibility recommendation: {title}",
            module="accessibility",
            metadata={"priority": priority},
        )
        return rec

    def implement(self, recommendation: AccessibilityRecommendation, *, notes: str = "") -> AccessibilityRecommendation:
        self._require(ACCESSIBILITY_UPDATE)
        recommendation.status = AccessibilityIssueStatus.VERIFIED
        recommendation.implemented_by = self.actor
        recommendation.implemented_at = timezone.now()
        recommendation.implementation_notes = notes
        recommendation.updated_by = self.actor
        recommendation.save()
        self._log(
            event_type="RECOMMENDATION_IMPLEMENTED",
            description=f"Implemented recommendation: {recommendation.title}",
            module="accessibility",
        )
        return recommendation


# ──────────────────────────────────────────────────────────────────────────────
# Compliance & Exception Services
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityComplianceService(AccessibilityBaseService):
    """Manage compliance records."""

    def get_or_create_record(
        self,
        *,
        module: str,
        component: str = "",
        page_url: str = "",
        standard: AccessibilityStandardRecord,
        target_level: str = WCAGLevel.AA,
    ) -> AccessibilityComplianceRecord:
        record, _ = AccessibilityComplianceRecord.objects.get_or_create(
            module=module,
            component=component,
            page_url=page_url,
            defaults={
                "standard": standard,
                "target_level": target_level,
                "created_by": self.actor,
                "updated_by": self.actor,
            },
        )
        return record

    def update_from_audit(self, audit: AccessibilityAudit) -> AccessibilityComplianceRecord:
        self._require(ACCESSIBILITY_AUDIT)
        record = self.get_or_create_record(
            module=audit.module,
            component=audit.component,
            page_url=audit.page_url,
            standard=audit.standard,
            target_level=audit.target_level,
        )
        record.compliance_status = audit.status
        record.last_audit = audit
        record.last_tested = audit.completed_at
        record.open_findings = audit.findings.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"]).count()
        record.critical_findings = audit.findings.filter(severity=SeverityLevel.CRITICAL, status__in=["OPEN", "IN_PROGRESS"]).count()
        record.updated_by = self.actor
        record.save()
        return record


class AccessibilityExceptionService(AccessibilityBaseService):
    """Manage accessibility exceptions."""

    def create(
        self,
        *,
        module: str,
        criterion: WCAGCriterion,
        reason: str,
        justification: str,
        approved_by,
        expires_on,
        component: str = "",
        **kwargs,
    ) -> AccessibilityException:
        self._require(ACCESSIBILITY_APPROVE)
        exc = AccessibilityException.objects.create(
            module=module,
            component=component,
            criterion=criterion,
            reason=reason,
            justification=justification,
            approved_by=approved_by,
            approved_date=timezone.localdate(),
            expires_on=expires_on,
            created_by=self.actor,
            updated_by=self.actor,
            **kwargs,
        )
        record = AccessibilityComplianceService(user=self.actor).get_or_create_record(
            module=module, component=component, standard=criterion.standard
        )
        record.exception_granted = True
        record.exception_reason = reason
        record.exception_expires = expires_on
        record.exception_approved_by = approved_by
        record.save()
        return exc


# ──────────────────────────────────────────────────────────────────────────────
# Analytics Service
# ──────────────────────────────────────────────────────────────────────────────

class AccessibilityAnalyticsService(AccessibilityBaseService):
    """Generate accessibility analytics snapshots."""

    def generate_snapshot(self, module: str = "") -> AccessibilityAnalytics:
        self._require(ACCESSIBILITY_REPORT)
        today = timezone.localdate()
        findings_qs = AccessibilityFinding.objects.filter(audit__module=module) if module else AccessibilityFinding.objects.all()
        issues_qs = AccessibilityIssue.objects.filter(module=module) if module else AccessibilityIssue.objects.all()

        open_findings = findings_qs.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"])
        open_issues = issues_qs.filter(status__in=["OPEN", "IN_PROGRESS", "NEEDS_REVIEW"])

        snapshot = AccessibilityAnalytics.objects.create(
            snapshot_date=today,
            module=module,
            overall_compliance_score=self._calculate_overall_score(module),
            critical_issues=open_findings.filter(severity=SeverityLevel.CRITICAL).count() + open_issues.filter(severity=SeverityLevel.CRITICAL).count(),
            high_issues=open_findings.filter(severity=SeverityLevel.HIGH).count() + open_issues.filter(severity=SeverityLevel.HIGH).count(),
            medium_issues=open_findings.filter(severity=SeverityLevel.MEDIUM).count() + open_issues.filter(severity=SeverityLevel.MEDIUM).count(),
            low_issues=open_findings.filter(severity=SeverityLevel.LOW).count() + open_issues.filter(severity=SeverityLevel.LOW).count(),
            total_issues=open_findings.count() + open_issues.count(),
            resolved_this_period=findings_qs.filter(resolved_at__date=today).count() + issues_qs.filter(resolved_at__date=today).count(),
            new_this_period=findings_qs.filter(created_at__date=today).count() + issues_qs.filter(created_at__date=today).count(),
            avg_resolution_days=self._calculate_avg_resolution(module),
            audit_coverage_percent=self._calculate_audit_coverage(module),
            keyboard_test_coverage=self._calculate_keyboard_coverage(module),
            screen_reader_test_coverage=self._calculate_sr_coverage(module),
            user_preference_adoption=self._calculate_preference_adoption(),
            regressions_count=issues_qs.filter(is_regression=True, created_at__date=today).count(),
            created_by=self.actor,
            updated_by=self.actor,
        )
        return snapshot

    def _calculate_overall_score(self, module: str) -> float:
        audits = AccessibilityAudit.objects.filter(module=module) if module else AccessibilityAudit.objects.all()
        completed = audits.filter(status__in=[ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT, ComplianceStatus.PARTIAL])
        if not completed.exists():
            return 0.0
        return round(completed.aggregate(avg=Avg("overall_score"))["avg"] or 0, 2)

    def _calculate_avg_resolution(self, module: str) -> float:
        findings = AccessibilityFinding.objects.filter(resolved_at__isnull=False)
        issues = AccessibilityIssue.objects.filter(resolved_at__isnull=False)
        if module:
            findings = findings.filter(audit__module=module)
            issues = issues.filter(module=module)
        all_resolved = list(findings) + list(issues)
        if not all_resolved:
            return 0.0
        total_days = sum((r.resolved_at - r.created_at).total_seconds() / 86400 for r in all_resolved if r.resolved_at)
        return round(total_days / len(all_resolved), 2)

    def _calculate_audit_coverage(self, module: str) -> float:
        total_components = 100  # Placeholder - would integrate with module registry
        audited = AccessibilityAudit.objects.filter(module=module).values("component").distinct().count() if module else 0
        return round(audited / total_components * 100, 2) if total_components > 0 else 0

    def _calculate_keyboard_coverage(self, module: str) -> float:
        audits = AccessibilityAudit.objects.filter(audit_type=AuditType.KEYBOARD)
        if module:
            audits = audits.filter(module=module)
        return round(audits.count() / max(AccessibilityAudit.objects.filter(module=module).count(), 1) * 100, 2)

    def _calculate_sr_coverage(self, module: str) -> float:
        audits = AccessibilityAudit.objects.filter(audit_type=AuditType.SCREEN_READER)
        if module:
            audits = audits.filter(module=module)
        return round(audits.count() / max(AccessibilityAudit.objects.filter(module=module).count(), 1) * 100, 2)

    def _calculate_preference_adoption(self) -> float:
        total_users = settings.AUTH_USER_MODEL.objects.filter(is_active=True).count()
        if total_users == 0:
            return 0.0
        users_with_prefs = AccessibilityPreference.objects.filter(
            Q(high_contrast=True) | Q(reduced_motion=True) | Q(enhanced_focus=True) | Q(font_size__in=["LARGE", "EXTRA_LARGE"])
        ).count()
        return round(users_with_prefs / total_users * 100, 2)
