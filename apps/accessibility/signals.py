"""Signals for the Accessibility Review module."""

from __future__ import annotations

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    AccessibilityAudit,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityNotification,
    AccessibilityPolicy,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
)


@receiver(pre_save, sender=AccessibilityStandardRecord)
def standard_pre_save(sender, instance, **kwargs):
    if not instance.pk:
        # New standard - timeline will be created in service
        pass


@receiver(post_save, sender=AccessibilityStandardRecord)
def standard_post_save(sender, instance, created, **kwargs):
    if created:
        AccessibilityTimeline.objects.create(
            event_type='STANDARD_CREATED',
            description=f'Created accessibility standard: {instance.name}',
            module='accessibility',
            reference_number=instance.code,
            performed_by=instance.created_by,
            status_after='ACTIVE' if instance.is_active else 'INACTIVE',
        )


@receiver(post_save, sender=AccessibilityPolicy)
def policy_post_save(sender, instance, created, **kwargs):
    if created:
        AccessibilityTimeline.objects.create(
            event_type='POLICY_CREATED',
            description=f'Created accessibility policy: {instance.title}',
            module='accessibility',
            reference_number=instance.reference_number,
            performed_by=instance.created_by,
            status_after='ACTIVE' if instance.is_active else 'INACTIVE',
        )
    else:
        AccessibilityTimeline.objects.create(
            event_type='POLICY_UPDATED',
            description=f'Updated accessibility policy: {instance.title}',
            module='accessibility',
            reference_number=instance.reference_number,
            performed_by=instance.updated_by,
        )


@receiver(pre_save, sender=AccessibilityAudit)
def audit_pre_save(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = AccessibilityAudit.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except AccessibilityAudit.DoesNotExist:
            instance._old_status = None


@receiver(post_save, sender=AccessibilityAudit)
def audit_post_save(sender, instance, created, **kwargs):
    if created:
        AccessibilityTimeline.objects.create(
            event_type='AUDIT_STARTED',
            description=f'Started accessibility audit: {instance.name}',
            module=instance.module or 'accessibility',
            component=instance.component,
            reference_number=instance.reference_number,
            performed_by=instance.created_by,
            status_after=instance.status,
        )
    elif hasattr(instance, '_old_status') and instance._old_status != instance.status:
        AccessibilityTimeline.objects.create(
            event_type='AUDIT_COMPLETED' if instance.status in ('COMPLIANT', 'NON_COMPLIANT', 'PARTIAL') else 'AUDIT_UPDATED',
            description=f'Audit status changed: {instance.name}',
            module=instance.module or 'accessibility',
            component=instance.component,
            reference_number=instance.reference_number,
            performed_by=instance.updated_by,
            status_before=instance._old_status,
            status_after=instance.status,
        )


@receiver(post_save, sender=AccessibilityFinding)
def finding_post_save(sender, instance, created, **kwargs):
    if created:
        AccessibilityTimeline.objects.create(
            event_type='FINDING_CREATED',
            description=f'Created finding: {instance.criterion} - {instance.component}',
            module=instance.audit.module,
            component=instance.component,
            reference_number=instance.audit.reference_number,
            wcag_criterion=f'{instance.criterion.guideline_number}.{instance.criterion.criterion_number}',
            severity=instance.severity,
            performed_by=instance.created_by,
        )
    else:
        # Check for status changes
        AccessibilityTimeline.objects.create(
            event_type='FINDING_UPDATED',
            description=f'Updated finding: {instance.criterion}',
            module=instance.audit.module,
            component=instance.component,
            reference_number=instance.audit.reference_number,
            wcag_criterion=f'{instance.criterion.guideline_number}.{instance.criterion.criterion_number}',
            severity=instance.severity,
            performed_by=instance.updated_by,
        )


@receiver(post_save, sender=AccessibilityIssue)
def issue_post_save(sender, instance, created, **kwargs):
    if created:
        AccessibilityTimeline.objects.create(
            event_type='ISSUE_REPORTED',
            description=f'Reported accessibility issue: {instance.title}',
            module=instance.module,
            component=instance.component,
            reference_number=instance.reference_number,
            wcag_criterion=instance.criterion.criterion_number if instance.criterion else '',
            severity=instance.severity,
            performed_by=instance.created_by,
        )
    else:
        AccessibilityTimeline.objects.create(
            event_type='ISSUE_RESOLVED' if instance.status == 'VERIFIED' else 'ISSUE_UPDATED',
            description=f'Issue status changed: {instance.title}',
            module=instance.module,
            component=instance.component,
            reference_number=instance.reference_number,
            severity=instance.severity,
            performed_by=instance.updated_by,
        )


@receiver(post_save, sender=AccessibilityNotification)
def notification_post_save(sender, instance, created, **kwargs):
    if created and instance.sent_via_in_app:
        # Could trigger real-time notification here (WebSocket, etc.)
        pass
