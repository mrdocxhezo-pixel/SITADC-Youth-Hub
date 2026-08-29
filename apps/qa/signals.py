from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.qa.models import (
    Defect,
    QAAuditReference,
    QualityMetric,
    ReleaseCandidate,
    TestCase,
    TestExecution,
    TestPlan,
    TestSuite,
)

User = get_user_model()


@receiver(post_save, sender=TestPlan)
def test_plan_post_save(sender, instance, created, **kwargs):
    """Handle test plan post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-TPL-{instance.pk}-{instance.test_id}",
            event_type="TEST_PLAN_CREATED",
            module="qa",
            user=instance.created_by,
            after_values={"name": instance.name, "status": instance.status},
        )


@receiver(post_save, sender=TestSuite)
def test_suite_post_save(sender, instance, created, **kwargs):
    """Handle test suite post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-TSU-{instance.pk}",
            event_type="TEST_SUITE_CREATED",
            module="qa",
            user=instance.created_by,
            after_values={
                "name": instance.name,
                "test_plan": str(instance.test_plan.pk),
            },
        )


@receiver(post_save, sender=TestCase)
def test_case_post_save(sender, instance, created, **kwargs):
    """Handle test case post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-TCS-{instance.pk}-{instance.test_id}",
            event_type="TEST_CASE_CREATED",
            module="qa",
            user=instance.created_by,
            after_values={"test_id": instance.test_id, "title": instance.title},
        )


@receiver(post_save, sender=TestExecution)
def test_execution_post_save(sender, instance, created, **kwargs):
    """Handle test execution post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-TEX-{instance.pk}",
            event_type="TEST_EXECUTION_STARTED",
            module="qa",
            user=instance.executed_by,
            after_values={
                "test_case": instance.test_case.test_id,
                "status": instance.status,
            },
        )
    elif instance.status in ["PASSED", "FAILED", "BLOCKED", "ERROR", "SKIPPED"]:
        QAAuditReference.objects.create(
            reference_id=f"QA-TEX-{instance.pk}-COMPLETE",
            event_type="TEST_EXECUTION_COMPLETED",
            module="qa",
            user=instance.updated_by,
            after_values={
                "test_case": instance.test_case.test_id,
                "status": instance.status,
                "duration": instance.duration_seconds,
            },
        )


@receiver(post_save, sender=Defect)
def defect_post_save(sender, instance, created, **kwargs):
    """Handle defect post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-DEF-{instance.pk}-{instance.defect_id}",
            event_type="DEFECT_CREATED",
            module="qa",
            user=instance.reported_by,
            after_values={
                "defect_id": instance.defect_id,
                "title": instance.title,
                "severity": instance.severity,
            },
        )


@receiver(post_save, sender=ReleaseCandidate)
def release_candidate_post_save(sender, instance, created, **kwargs):
    """Handle release candidate post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-REL-{instance.pk}-{instance.version}",
            event_type="RELEASE_CANDIDATE_CREATED",
            module="qa",
            user=instance.created_by,
            after_values={"version": instance.version, "status": instance.status},
        )


@receiver(post_save, sender=QualityMetric)
def quality_metric_post_save(sender, instance, created, **kwargs):
    """Handle quality metric post-save."""
    if created:
        QAAuditReference.objects.create(
            reference_id=f"QA-QMT-{instance.pk}",
            event_type="QUALITY_METRIC_RECORDED",
            module="qa",
            user=instance.calculated_by,
            after_values={
                "metric_type": instance.metric_type,
                "name": instance.name,
                "value": float(instance.value),
                "period": f"{instance.period_start} to {instance.period_end}",
            },
        )
