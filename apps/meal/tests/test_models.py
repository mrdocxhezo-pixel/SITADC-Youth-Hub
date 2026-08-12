"""Model behaviour, validation, and immutability tests."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.meal.constants import (
    ComplaintStatus,
    IndicatorStatus,
    MonitoringVisitStatus,
    ReferenceDataKind,
    ScorecardDimension,
)
from apps.meal.models import (
    MEALAuditRecord,
    MEALStatusHistory,
    MonitoringFinding,
    MonitoringVisit,
)
from apps.meal.models import ScorecardDimension as ScorecardDimensionRow

from .base import MEALTestCase


class IndicatorModelTests(MEALTestCase):
    def test_default_status_is_draft(self):
        indicator = self.create_indicator()
        self.assertEqual(indicator.status, IndicatorStatus.DRAFT)

    def test_unique_code_and_reference_enforced(self):
        self.create_indicator(code="dup_code")
        with self.assertRaises((IntegrityError, ValidationError)):
            self.create_indicator(code="dup_code")

    def test_latest_approved_baseline_property(self):
        from apps.meal.constants import BaselineStatus
        from apps.meal.models import IndicatorBaseline

        indicator = self.create_indicator()
        IndicatorBaseline.objects.create(
            indicator=indicator,
            reference_number="BSL-APP-0001",
            value=5,
            status=BaselineStatus.APPROVED,
            created_by=self.manager,
            updated_by=self.manager,
        )
        IndicatorBaseline.objects.create(
            indicator=indicator,
            reference_number="BSL-PND-0002",
            value=9,
            status=BaselineStatus.PENDING_APPROVAL,
            created_by=self.manager,
            updated_by=self.manager,
        )
        self.assertEqual(indicator.latest_approved_baseline.value, 5)


class MonitoringVisitModelTests(MEALTestCase):
    def test_future_visit_date_rejected(self):
        from datetime import timedelta

        from django.utils import timezone

        visit = MonitoringVisit(
            reference_number="VIS-0001",
            visit_date=timezone.localdate() + timedelta(days=1),
            status=MonitoringVisitStatus.PLANNED,
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(ValidationError):
            visit.full_clean()

    def test_findings_related(self):
        visit = MonitoringVisit.objects.create(
            reference_number="VIS-0002",
            visit_date="2026-01-10",
            created_by=self.manager,
            updated_by=self.manager,
        )
        MonitoringFinding.objects.create(
            visit=visit,
            description="Delayed distribution observed.",
            created_by=self.manager,
            updated_by=self.manager,
        )
        self.assertEqual(visit.findings.count(), 1)


class ScorecardDimensionModelTests(MEALTestCase):
    def test_score_percentage_validation(self):
        from apps.meal.models import PerformanceScorecard

        scorecard = PerformanceScorecard.objects.create(
            reference_number="SCR-0001",
            title="Q1 Performance",
            period_label="Q1 2026",
            created_by=self.manager,
            updated_by=self.manager,
        )
        row = ScorecardDimensionRow(
            scorecard=scorecard,
            dimension=ScorecardDimension.PROGRAM,
            label="Program performance",
            score=115,
            created_by=self.manager,
            updated_by=self.manager,
        )
        with self.assertRaises(ValidationError):
            row.full_clean()


class StatusHistoryModelTests(MEALTestCase):
    def test_status_history_is_immutable(self):
        entry = MEALStatusHistory.objects.create(
            entity_type="Indicator",
            entity_id="IND-0001",
            action="CREATE",
            to_status="DRAFT",
            created_by=self.manager,
        )
        entry.from_status = "DRAFT"
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()

    def test_audit_record_is_immutable(self):
        record = MEALAuditRecord.objects.create(
            entity_type="Indicator",
            entity_id="IND-0001",
            action="create",
            created_by=self.manager,
        )
        record.notes = "changed"
        with self.assertRaises(ValidationError):
            record.save()


class ComplaintModelTests(MEALTestCase):
    def test_default_status_received(self):
        complaint = self.create_complaint()
        self.assertEqual(complaint.status, ComplaintStatus.RECEIVED)


class ReferenceDataTests(MEALTestCase):
    def test_seeded_taxonomy_present(self):
        self.assertIsNotNone(
            self.taxonomy(ReferenceDataKind.REPORTING_FREQUENCY, "monthly")
        )
        self.assertIsNotNone(
            self.taxonomy(ReferenceDataKind.EVALUATION_TYPE, "endline")
        )
