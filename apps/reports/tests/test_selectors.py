"""Tests for Phase 19 fail-closed permission-aware selectors."""

from __future__ import annotations

from apps.reports.models import ReportCategory
from apps.reports.selectors import (
    category_queryset,
    template_queryset,
    user_can_access_template,
    visible_audit_records,
)
from apps.reports.services import ReportTemplateService
from apps.reports.tests.base import ReportsTestCase

# ── template_queryset ──────────────────────────────────────────────────────


class TemplateQuerysetTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        svc = ReportTemplateService(user=self.manager)
        cat = ReportCategory.objects.first()
        self.template = svc.create(
            code="sel-tpl", title="Selector Template", category=cat
        )

    def test_manager_sees_templates(self):
        qs = template_queryset(self.manager)
        self.assertIn(self.template, qs)

    def test_viewer_sees_templates(self):
        qs = template_queryset(self.viewer)
        self.assertIn(self.template, qs)

    def test_outsider_sees_nothing(self):
        qs = template_queryset(self.outsider)
        self.assertNotIn(self.template, qs)

    def test_anonymous_user_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser

        qs = template_queryset(AnonymousUser())
        self.assertFalse(qs.exists())

    def test_none_user_sees_nothing(self):
        qs = template_queryset(None)
        self.assertFalse(qs.exists())

    def test_archived_excluded_by_default(self):
        ReportTemplateService(user=self.manager).archive(self.template)
        qs = template_queryset(self.manager)
        self.assertNotIn(self.template, qs)

    def test_archived_included_when_requested(self):
        ReportTemplateService(user=self.manager).archive(self.template)
        qs = template_queryset(self.manager, include_archived=True)
        self.assertIn(self.template, qs)


# ── category_queryset ──────────────────────────────────────────────────────


class CategoryQuerysetTests(ReportsTestCase):
    def test_manager_sees_categories(self):
        qs = category_queryset(self.manager)
        self.assertTrue(qs.exists())

    def test_viewer_sees_categories(self):
        qs = category_queryset(self.viewer)
        self.assertTrue(qs.exists())

    def test_outsider_sees_nothing(self):
        qs = category_queryset(self.outsider)
        self.assertFalse(qs.exists())

    def test_anonymous_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser

        qs = category_queryset(AnonymousUser())
        self.assertFalse(qs.exists())


# ── user_can_access_template ───────────────────────────────────────────────


class UserCanAccessTemplateTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        svc = ReportTemplateService(user=self.manager)
        cat = ReportCategory.objects.first()
        self.template = svc.create(code="sel-access", title="Access Test", category=cat)

    def test_manager_can_access(self):
        self.assertTrue(user_can_access_template(self.manager, self.template))

    def test_viewer_can_access(self):
        self.assertTrue(user_can_access_template(self.viewer, self.template))

    def test_outsider_cannot_access(self):
        self.assertFalse(user_can_access_template(self.outsider, self.template))

    def test_none_returns_false(self):
        self.assertFalse(user_can_access_template(self.manager, None))


# ── visible_audit_records ──────────────────────────────────────────────────


class VisibleAuditRecordsTests(ReportsTestCase):
    def test_manager_can_see_audit_records(self):
        # Audit records may be empty but the queryset itself should not fail
        records = visible_audit_records(self.manager, limit=5)
        self.assertIsNotNone(records)

    def test_outsider_sees_nothing(self):
        records = visible_audit_records(self.outsider)
        self.assertFalse(list(records))

    def test_anonymous_sees_nothing(self):
        from django.contrib.auth.models import AnonymousUser

        records = visible_audit_records(AnonymousUser())
        self.assertFalse(list(records))
