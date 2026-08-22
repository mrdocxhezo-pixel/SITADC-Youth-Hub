"""Management command to send accessibility notifications."""

from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accessibility.models import (
    AccessibilityAudit,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityNotification,
)


class Command(BaseCommand):
    help = "Send accessibility notifications for due items and overdue findings/issues."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what notifications would be sent without sending',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        now = timezone.now()

        if dry_run:
            self.stdout.write(self.style.NOTICE("DRY RUN - No notifications will be sent"))

        notifications_sent = 0

        # 1. Overdue findings
        overdue_findings = AccessibilityFinding.objects.filter(
            due_date__lt=timezone.localdate(),
            status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW']
        ).select_related('assigned_to', 'audit')

        for finding in overdue_findings:
            if finding.assigned_to:
                self._create_notification(
                    recipient=finding.assigned_to,
                    event_type='ISSUE_ASSIGNED',  # Reuse for overdue
                    title=f"Overdue Accessibility Finding: {finding.criterion}",
                    message=f"Finding '{finding.description[:100]}...' was due on {finding.due_date}.",
                    related_finding=finding,
                    dry_run=dry_run,
                )
                notifications_sent += 1

        # 2. Overdue issues
        overdue_issues = AccessibilityIssue.objects.filter(
            due_date__lt=timezone.localdate(),
            status__in=['OPEN', 'IN_PROGRESS', 'NEEDS_REVIEW']
        ).select_related('assigned_to')

        for issue in overdue_issues:
            if issue.assigned_to:
                self._create_notification(
                    recipient=issue.assigned_to,
                    event_type='ISSUE_ASSIGNED',
                    title=f"Overdue Accessibility Issue: {issue.title}",
                    message=f"Issue '{issue.title}' was due on {issue.due_date}.",
                    related_issue=issue,
                    dry_run=dry_run,
                )
                notifications_sent += 1

        # 3. Audits due for review (older than 30 days without completion)
        stale_audits = AccessibilityAudit.objects.filter(
            status='NOT_TESTED',
            created_at__lt=now - timedelta(days=30)
        ).select_related('auditor')

        for audit in stale_audits:
            if audit.auditor:
                self._create_notification(
                    recipient=audit.auditor,
                    event_type='AUDIT_COMPLETED',  # Reuse
                    title=f"Stale Audit: {audit.name}",
                    message=f"Audit '{audit.name}' has been in progress for over 30 days without completion.",
                    related_audit=audit,
                    dry_run=dry_run,
                )
                notifications_sent += 1

        # 4. Compliance reviews due
        from apps.accessibility.models import AccessibilityComplianceRecord
        due_reviews = AccessibilityComplianceRecord.objects.filter(
            next_review_due__lt=timezone.localdate()
        )

        for record in due_reviews:
            # Notify module owner or accessibility team
            self._create_notification(
                recipient=record.exception_approved_by,  # Fallback
                event_type='REVIEW_DUE',
                title=f"Compliance Review Due: {record.module}",
                message=f"Compliance review for {record.module}/{record.component} is due.",
                dry_run=dry_run,
            )
            notifications_sent += 1

        # 5. New regressions detected (issues marked as regression in last 24h)
        recent_regressions = AccessibilityIssue.objects.filter(
            is_regression=True,
            created_at__gte=now - timedelta(hours=24)
        ).select_related('assigned_to')

        for issue in recent_regressions:
            if issue.assigned_to:
                self._create_notification(
                    recipient=issue.assigned_to,
                    event_type='REGRESSION_DETECTED',
                    title=f"Regression Detected: {issue.title}",
                    message=f"A regression was detected in '{issue.module}/{issue.component}'.",
                    related_issue=issue,
                    dry_run=dry_run,
                )
                notifications_sent += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"DRY RUN: Would send {notifications_sent} notifications"))
        else:
            self.stdout.write(self.style.SUCCESS(f"Sent {notifications_sent} notifications"))

    def _create_notification(self, recipient, event_type, title, message, **kwargs):
        dry_run = kwargs.pop('dry_run', False)
        related_audit = kwargs.pop('related_audit', None)
        related_finding = kwargs.pop('related_finding', None)
        related_issue = kwargs.pop('related_issue', None)

        if not recipient:
            return

        if dry_run:
            self.stdout.write(f"  [DRY RUN] Would notify {recipient.get_full_name()}: {title}")
            return

        AccessibilityNotification.objects.create(
            event_type=event_type,
            title=title,
            message=message,
            recipient=recipient,
            related_audit=related_audit,
            related_finding=related_finding,
            related_issue=related_issue,
            sent_via_in_app=True,
            sent_at=timezone.now(),
        )
