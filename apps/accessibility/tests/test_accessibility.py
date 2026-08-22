"""Tests for the Accessibility Review module."""

from __future__ import annotations

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.accessibility.constants import (
    AccessibilityCategory,
    AccessibilityStandard,
    AuditType,
    ComplianceStatus,
    FontSizeOption,
    SeverityLevel,
    WCAGLevel,
    WCAGPrinciple,
)
from apps.accessibility.models import (
    AccessibilityAudit,
    AccessibilityConfiguration,
    AccessibilityFinding,
    AccessibilityIssue,
    AccessibilityPolicy,
    AccessibilityPreference,
    AccessibilityStandardRecord,
    AccessibilityTimeline,
    WCAGCriterion,
)
from apps.accessibility.services import (
    AccessibilityAnalyticsService,
    AccessibilityAuditService,
    AccessibilityConfigurationService,
    AccessibilityIssueService,
    AccessibilityPreferenceService,
    AccessibilityRecommendationService,
    AccessibilityStandardService,
    WCAGCriterionService,
)

User = get_user_model()


class AccessibilityConstantsTest(TestCase):
    """Test accessibility constants."""

    def test_accessibility_standard_choices(self):
        self.assertEqual(AccessibilityStandard.WCAG_2_2_AA, "WCAG_2_2_AA")
        self.assertEqual(AccessibilityStandard.SECTION_508, "SECTION_508")

    def test_wcag_level_choices(self):
        self.assertEqual(WCAGLevel.AA, "AA")
        self.assertEqual(WCAGLevel.AAA, "AAA")

    def test_severity_level_choices(self):
        self.assertEqual(SeverityLevel.CRITICAL, "CRITICAL")
        self.assertEqual(SeverityLevel.HIGH, "HIGH")

    def test_audit_type_choices(self):
        self.assertEqual(AuditType.AUTOMATED, "AUTOMATED")
        self.assertEqual(AuditType.MANUAL, "MANUAL")

    def test_compliance_status_choices(self):
        self.assertEqual(ComplianceStatus.COMPLIANT, "COMPLIANT")
        self.assertEqual(ComplianceStatus.NON_COMPLIANT, "NON_COMPLIANT")


class AccessibilityModelTest(TestCase):
    """Test accessibility models."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.auditor = User.objects.create_user(
            username="auditor",
            email="auditor@example.com",
            password="testpass123"
        )

    def test_accessibility_standard_record_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            description="WCAG 2.2 Level AA standard",
            effective_date=timezone.localdate(),
            review_date=timezone.localdate() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(standard.code, "WCAG_2_2_AA")
        self.assertEqual(standard.target_level, WCAGLevel.AA)

    def test_accessibility_policy_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        policy = AccessibilityPolicy.objects.create(
            title="Web Accessibility Policy",
            reference_number="ACC-POL-001",
            standard=standard,
            category=AccessibilityCategory.PERCEIVABLE,
            description="Policy for web accessibility",
            version="1.0",
            effective_date=timezone.localdate(),
            review_date=timezone.localdate() + timedelta(days=365),
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(policy.reference_number, "ACC-POL-001")

    def test_wcag_criterion_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        criterion = WCAGCriterion.objects.create(
            standard=standard,
            guideline_number="1.4",
            criterion_number="3",
            title="Contrast (Minimum)",
            description="The visual presentation of text and images of text has a contrast ratio of at least 4.5:1",
            principle=WCAGPrinciple.PERCEIVABLE,
            level=WCAGLevel.AA,
            category=AccessibilityCategory.PERCEIVABLE,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(criterion.guideline_number, "1.4")
        self.assertEqual(criterion.criterion_number, "3")

    def test_accessibility_audit_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        audit = AccessibilityAudit.objects.create(
            name="Website Accessibility Audit",
            audit_type=AuditType.AUTOMATED,
            scope="MODULE",
            module="reports",
            standard=standard,
            target_level=WCAGLevel.AA,
            auditor=self.auditor,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(audit.name, "Website Accessibility Audit")
        self.assertEqual(audit.audit_type, AuditType.AUTOMATED)

    def test_accessibility_finding_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        criterion = WCAGCriterion.objects.create(
            standard=standard,
            guideline_number="1.4",
            criterion_number="3",
            title="Contrast (Minimum)",
            description="Test",
            principle=WCAGPrinciple.PERCEIVABLE,
            level=WCAGLevel.AA,
            category=AccessibilityCategory.PERCEIVABLE,
            created_by=self.user,
            updated_by=self.user,
        )
        audit = AccessibilityAudit.objects.create(
            name="Test Audit",
            audit_type=AuditType.MANUAL,
            scope="MODULE",
            module="reports",
            standard=standard,
            auditor=self.auditor,
            created_by=self.user,
            updated_by=self.user,
        )
        finding = AccessibilityFinding.objects.create(
            audit=audit,
            criterion=criterion,
            component="Header",
            description="Insufficient contrast on header text",
            severity=SeverityLevel.HIGH,
            assigned_to=self.auditor,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(finding.severity, SeverityLevel.HIGH)

    def test_accessibility_issue_creation(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        criterion = WCAGCriterion.objects.create(
            standard=standard,
            guideline_number="2.1",
            criterion_number="1",
            title="Keyboard",
            description="Test",
            principle=WCAGPrinciple.OPERABLE,
            level=WCAGLevel.AA,
            category=AccessibilityCategory.OPERABLE,
            created_by=self.user,
            updated_by=self.user,
        )
        issue = AccessibilityIssue.objects.create(
            title="Keyboard Navigation Issue",
            source="USER_REPORT",
            module="reports",
            component="Navigation Menu",
            description="Cannot navigate menu with keyboard",
            severity=SeverityLevel.CRITICAL,
            criterion=criterion,
            reporter=self.user,
            assigned_to=self.auditor,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(issue.severity, SeverityLevel.CRITICAL)

    def test_accessibility_preference_creation(self):
        prefs = AccessibilityPreference.objects.create(
            user=self.user,
            font_size=FontSizeOption.LARGE,
            colour_theme="DARK",
            high_contrast=True,
            reduced_motion=True,
            created_by=self.user,
            updated_by=self.user,
        )
        self.assertEqual(prefs.font_size, FontSizeOption.LARGE)
        self.assertTrue(prefs.high_contrast)

    def test_accessibility_configuration_singleton(self):
        config = AccessibilityConfiguration.load()
        self.assertIsNotNone(config)
        self.assertEqual(config.target_wcag_level, WCAGLevel.AA)

        # Second call should return same instance
        config2 = AccessibilityConfiguration.load()
        self.assertEqual(config.pk, config2.pk)

    def test_accessibility_timeline_immutable(self):
        timeline = AccessibilityTimeline.objects.create(
            event_type="STANDARD_CREATED",
            description="Test timeline event",
            module="accessibility",
            performed_by=self.user,
            created_by=self.user,
            updated_by=self.user,
        )
        # Try to modify - should raise ValidationError
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            timeline.description = "Modified"
            timeline.save()

        # Try to delete - should raise ValidationError
        with self.assertRaises(ValidationError):
            timeline.delete()


class AccessibilityServiceTest(TestCase):
    """Test accessibility services."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="serviceuser",
            email="service@example.com",
            password="testpass123"
        )
        self.auditor = User.objects.create_user(
            username="serviceauditor",
            email="serviceauditor@example.com",
            password="testpass123"
        )

    def test_standard_service_create(self):
        standard = AccessibilityStandardService(user=self.user).create(
            code="TEST_STD",
            name="Test Standard",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            effective_date=timezone.localdate(),
        )
        self.assertEqual(standard.code, "TEST_STD")

    def test_criterion_service_create(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        criterion = WCAGCriterionService(user=self.user).create(
            standard=standard,
            guideline_number="1.4",
            criterion_number="3",
            title="Contrast (Minimum)",
            description="Test criterion",
            principle=WCAGPrinciple.PERCEIVABLE,
            level=WCAGLevel.AA,
            category=AccessibilityCategory.PERCEIVABLE,
        )
        self.assertEqual(criterion.guideline_number, "1.4")

    def test_preference_service_get_or_create(self):
        prefs = AccessibilityPreferenceService().get_or_create_for_user(self.user)
        self.assertIsNotNone(prefs)
        self.assertEqual(prefs.user, self.user)

    def test_preference_service_update(self):
        AccessibilityPreferenceService().get_or_create_for_user(self.user)
        updated = AccessibilityPreferenceService(user=self.user).update_preferences(
            self.user,
            font_size=FontSizeOption.LARGE,
            high_contrast=True,
        )
        self.assertEqual(updated.font_size, FontSizeOption.LARGE)
        self.assertTrue(updated.high_contrast)

    def test_configuration_service_update(self):
        AccessibilityConfigurationService(user=self.user).update(
            target_wcag_level=WCAGLevel.AAA,
            enable_high_contrast=True,
        )
        config = AccessibilityConfiguration.load()
        self.assertEqual(config.target_wcag_level, WCAGLevel.AAA)
        self.assertTrue(config.enable_high_contrast)

    def test_audit_service_create(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        audit = AccessibilityAuditService(user=self.user).create_audit(
            name="Test Audit",
            audit_type=AuditType.MANUAL,
            scope="MODULE",
            module="reports",
            standard=standard,
            auditor=self.auditor,
        )
        self.assertEqual(audit.name, "Test Audit")
        self.assertIsNotNone(audit.reference_number)

    def test_issue_service_create(self):
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        criterion = WCAGCriterion.objects.create(
            standard=standard,
            guideline_number="2.1",
            criterion_number="1",
            title="Keyboard",
            description="Test",
            principle=WCAGPrinciple.OPERABLE,
            level=WCAGLevel.AA,
            category=AccessibilityCategory.OPERABLE,
            created_by=self.user,
            updated_by=self.user,
        )
        issue = AccessibilityIssueService(user=self.user).create_issue(
            title="Test Issue",
            source="USER_REPORT",
            module="reports",
            component="Navigation",
            description="Test description",
            severity=SeverityLevel.HIGH,
            criterion=criterion,
            assigned_to=self.auditor,
        )
        self.assertEqual(issue.title, "Test Issue")
        self.assertIsNotNone(issue.reference_number)

    def test_recommendation_service_create(self):
        rec = AccessibilityRecommendationService(user=self.user).create(
            title="Improve Contrast",
            description="Improve contrast ratios across the site",
            priority="HIGH",
            rationale="Current contrast ratios are below WCAG AA",
        )
        self.assertEqual(rec.title, "Improve Contrast")
        self.assertEqual(rec.priority, "HIGH")

    def test_analytics_service_generate(self):
        # Create some test data first
        standard = AccessibilityStandardRecord.objects.create(
            code="WCAG_2_2_AA",
            name="WCAG 2.2 Level AA",
            standard_type=AccessibilityStandard.WCAG_2_2_AA,
            version="2.2",
            target_level=WCAGLevel.AA,
            effective_date=timezone.localdate(),
            created_by=self.user,
            updated_by=self.user,
        )
        AccessibilityAudit.objects.create(
            name="Test Audit",
            audit_type=AuditType.AUTOMATED,
            scope="MODULE",
            module="reports",
            standard=standard,
            auditor=self.auditor,
            status=ComplianceStatus.COMPLIANT,
            overall_score=85.5,
            created_by=self.user,
            updated_by=self.user,
        )
        snapshot = AccessibilityAnalyticsService(user=self.user).generate_snapshot()
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.module, "")


class AccessibilityViewTest(TestCase):
    """Test accessibility views."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="viewuser",
            email="view@example.com",
            password="testpass123"
        )
        self.client.force_login(self.user)

    def test_dashboard_view(self):
        response = self.client.get("/accessibility/")
        self.assertEqual(response.status_code, 200)

    def test_standard_list_view(self):
        response = self.client.get("/accessibility/standards/")
        self.assertEqual(response.status_code, 200)

    def test_policy_list_view(self):
        response = self.client.get("/accessibility/policies/")
        self.assertEqual(response.status_code, 200)

    def test_configuration_view(self):
        response = self.client.get("/accessibility/configuration/")
        self.assertEqual(response.status_code, 200)

    def test_user_preferences_view(self):
        response = self.client.get("/accessibility/preferences/")
        self.assertEqual(response.status_code, 200)

    def test_criterion_list_view(self):
        response = self.client.get("/accessibility/criteria/")
        self.assertEqual(response.status_code, 200)

    def test_audit_list_view(self):
        response = self.client.get("/accessibility/audits/")
        self.assertEqual(response.status_code, 200)

    def test_issue_list_view(self):
        response = self.client.get("/accessibility/issues/")
        self.assertEqual(response.status_code, 200)

    def test_recommendation_list_view(self):
        response = self.client.get("/accessibility/recommendations/")
        self.assertEqual(response.status_code, 200)

    def test_compliance_list_view(self):
        response = self.client.get("/accessibility/compliance/")
        self.assertEqual(response.status_code, 200)

    def test_analytics_view(self):
        response = self.client.get("/accessibility/analytics/")
        self.assertEqual(response.status_code, 200)

    def test_timeline_view(self):
        response = self.client.get("/accessibility/timeline/")
        self.assertEqual(response.status_code, 200)


class AccessibilityAPITest(TestCase):
    """Test accessibility API endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser",
            email="api@example.com",
            password="testpass123"
        )
        self.client.force_login(self.user)

    def test_user_preferences_api_get(self):
        response = self.client.get("/accessibility/api/preferences/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("font_size", data)
        self.assertIn("high_contrast", data)

    def test_user_preferences_api_post(self):
        response = self.client.post(
            "/accessibility/api/preferences/",
            data=json.dumps({"font_size": "LARGE", "high_contrast": True}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_contrast_check_api(self):
        response = self.client.post(
            "/accessibility/api/contrast-check/",
            data=json.dumps({"foreground": "#000000", "background": "#FFFFFF"}),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("ratio", data)
        self.assertEqual(data["ratio"], 21.0)
        self.assertTrue(data["passes_aa_normal"])


class AccessibilityTemplateTagTest(TestCase):
    """Test accessibility template tags."""

    def test_accessibility_severity_badge_filter(self):
        from apps.accessibility.templatetags.accessibility_tags import (
            accessibility_severity_badge,
        )

        self.assertEqual(accessibility_severity_badge("CRITICAL"), "bg-danger")
        self.assertEqual(accessibility_severity_badge("HIGH"), "bg-warning text-dark")
        self.assertEqual(accessibility_severity_badge("MEDIUM"), "bg-info")
        self.assertEqual(accessibility_severity_badge("LOW"), "bg-secondary")

    def test_accessibility_status_badge_filter(self):
        from apps.accessibility.templatetags.accessibility_tags import (
            accessibility_status_badge,
        )

        self.assertEqual(accessibility_status_badge("COMPLIANT"), "bg-success")
        self.assertEqual(accessibility_status_badge("NON_COMPLIANT"), "bg-danger")
        self.assertEqual(accessibility_status_badge("PARTIAL"), "bg-warning text-dark")

    def test_wcag_level_badge_filter(self):
        from apps.accessibility.templatetags.accessibility_tags import wcag_level_badge

        self.assertEqual(wcag_level_badge("AA"), "bg-info")
        self.assertEqual(wcag_level_badge("AAA"), "bg-dark")

    def test_accessibility_contrast_ratio(self):
        from apps.accessibility.templatetags.accessibility_tags import (
            accessibility_contrast_ratio,
        )

        # Black on white = 21:1
        ratio = accessibility_contrast_ratio("#000000", "#FFFFFF")
        self.assertAlmostEqual(ratio, 21.0, places=1)

    def test_accessibility_passes_aa(self):
        from apps.accessibility.templatetags.accessibility_tags import (
            accessibility_passes_aa,
        )

        # Black on white passes AA
        self.assertTrue(accessibility_passes_aa("#000000", "#FFFFFF"))
        # Gray on white might not pass
        self.assertFalse(accessibility_passes_aa("#999999", "#FFFFFF"))
