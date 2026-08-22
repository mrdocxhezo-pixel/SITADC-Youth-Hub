"""Custom managers for the Accessibility Review module."""

from __future__ import annotations

from django.db import models


class AccessibilityStandardManager(models.Manager):
    """Manager for AccessibilityStandardRecord."""

    def active(self):
        return self.filter(is_active=True)

    def by_type(self, standard_type: str):
        return self.filter(standard_type=standard_type)


class AccessibilityPolicyManager(models.Manager):
    """Manager for AccessibilityPolicy."""

    def active(self):
        return self.filter(is_active=True)

    def by_category(self, category: str):
        return self.filter(category=category)


class WCAGCriterionManager(models.Manager):
    """Manager for WCAGCriterion."""

    def active(self):
        return self.filter(is_active=True)

    def by_principle(self, principle: str):
        return self.filter(principle=principle)

    def by_level(self, level: str):
        return self.filter(level=level)

    def applicable_to_level(self, target_level: str):
        """Return criteria applicable to a target WCAG level."""
        level_order = {'A': 1, 'AA': 2, 'AAA': 3}
        target = level_order.get(target_level, 2)
        levels = [k for k, v in level_order.items() if v <= target]
        return self.filter(level__in=levels, is_active=True)


class AccessibilityAuditManager(models.Manager):
    """Manager for AccessibilityAudit."""

    def by_module(self, module: str):
        return self.filter(module=module)

    def by_type(self, audit_type: str):
        return self.filter(audit_type=audit_type)

    def by_status(self, status: str):
        return self.filter(status=status)

    def completed(self):
        return self.filter(status__in=['COMPLIANT', 'NON_COMPLIANT', 'PARTIAL'])

    def in_progress(self):
        return self.filter(status__in=['NOT_TESTED'])


class AccessibilityFindingManager(models.Manager):
    """Manager for AccessibilityFinding."""

    def open(self):
        return self.filter(status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW'])

    def by_severity(self, severity: str):
        return self.filter(severity=severity)

    def critical(self):
        return self.filter(severity='CRITICAL')

    def high(self):
        return self.filter(severity='HIGH')

    def assigned_to(self, user):
        return self.filter(assigned_to=user)

    def overdue(self):
        from django.utils import timezone
        return self.filter(due_date__lt=timezone.localdate(), status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW'])


class AccessibilityIssueManager(models.Manager):
    """Manager for AccessibilityIssue."""

    def open(self):
        return self.filter(status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW'])

    def by_severity(self, severity: str):
        return self.filter(severity=severity)

    def critical(self):
        return self.filter(severity='CRITICAL')

    def high(self):
        return self.filter(severity='HIGH')

    def by_module(self, module: str):
        return self.filter(module=module)

    def assigned_to(self, user):
        return self.filter(assigned_to=user)

    def reported_by(self, user):
        return self.filter(reporter=user)

    def regressions(self):
        return self.filter(is_regression=True)

    def overdue(self):
        from django.utils import timezone
        return self.filter(due_date__lt=timezone.localdate(), status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW'])


class AccessibilityRecommendationManager(models.Manager):
    """Manager for AccessibilityRecommendation."""

    def open(self):
        return self.filter(status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW'])

    def by_priority(self, priority: str):
        return self.filter(priority=priority)

    def immediate(self):
        return self.filter(priority='IMMEDIATE')


class AccessibilityComplianceManager(models.Manager):
    """Manager for AccessibilityComplianceRecord."""

    def compliant(self):
        return self.filter(compliance_status='COMPLIANT')

    def non_compliant(self):
        return self.filter(compliance_status='NON_COMPLIANT')

    def partial(self):
        return self.filter(compliance_status='PARTIAL')

    def by_module(self, module: str):
        return self.filter(module=module)

    def with_exceptions(self):
        return self.filter(exception_granted=True)

    def review_due(self):
        from django.utils import timezone
        return self.filter(next_review_due__lt=timezone.localdate())


class AccessibilityAnalyticsManager(models.Manager):
    """Manager for AccessibilityAnalytics."""

    def latest(self, module: str = ''):
        qs = self.all()
        if module:
            qs = qs.filter(module=module)
        return qs.order_by('-snapshot_date').first()

    def history(self, module: str = '', days: int = 30):
        from datetime import timedelta

        from django.utils import timezone
        since = timezone.localdate() - timedelta(days=days)
        qs = self.filter(snapshot_date__gte=since)
        if module:
            qs = qs.filter(module=module)
        return qs.order_by('-snapshot_date')
