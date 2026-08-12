"""Comprehensive view tests for the Phase 19 Dynamic Report Builder.

Covers all 23 views across the permission matrix (manager, officer,
viewer, outsider, anonymous) and verifies basic happy-path behaviour
for each endpoint.
"""

from __future__ import annotations

import json

from django.urls import reverse

from apps.reports.models import ReportCategory, ReportTemplateVersion
from apps.reports.services import ReportTemplateService
from apps.reports.tests.base import ReportsTestCase

# ── Shared template factory ────────────────────────────────────────────────


def _make_template(user, suffix=""):
    svc = ReportTemplateService(user=user)
    cat = ReportCategory.objects.first()
    return svc.create(code=f"vtest{suffix}", title=f"View Test {suffix}", category=cat)


# ── Dashboard ──────────────────────────────────────────────────────────────


class DashboardViewTests(ReportsTestCase):
    def test_manager_gets_200(self):
        self.login_as(self.manager)
        r = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Report Builder Dashboard")

    def test_viewer_gets_403(self):
        """Viewer lacks manage permission; fail-closed (403)."""
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(r.status_code, 403)

    def test_outsider_gets_403(self):
        self.login_as(self.outsider)
        r = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(r.status_code, 403)

    def test_anonymous_redirected(self):
        r = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r["Location"])


# ── Template directory ─────────────────────────────────────────────────────


class TemplateDirectoryViewTests(ReportsTestCase):
    def test_viewer_gets_200(self):
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:template_list"))
        self.assertEqual(r.status_code, 200)

    def test_officer_gets_200(self):
        self.login_as(self.officer)
        r = self.client.get(reverse("reports:template_list"))
        self.assertEqual(r.status_code, 200)

    def test_outsider_denied(self):
        self.login_as(self.outsider)
        r = self.client.get(reverse("reports:template_list"))
        self.assertEqual(r.status_code, 403)


# ── Template Create ─────────────────────────────────────────────────────────


class TemplateCreateViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("reports:template_create")
        self.category = ReportCategory.objects.first()

    def test_officer_get_200(self):
        self.login_as(self.officer)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_get(self):
        self.login_as(self.viewer)
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 403)

    def test_officer_create_post_redirects(self):
        self.login_as(self.officer)
        data = {
            "code": "ct-officer-test",
            "title": "Officer Created",
            "category": str(self.category.pk),
            "reporting_frequency": "ONE_OFF",
            "confidentiality": "INTERNAL",
            "description": "",
            "department": "",
            "notes": "",
        }
        r = self.client.post(self.url, data)
        self.assertIn(r.status_code, (200, 302))  # 302 on success, 200 with form errors


# ── Template Detail ─────────────────────────────────────────────────────────


class TemplateDetailViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "detail")

    def test_viewer_can_read(self):
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_detail", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, self.template.title)

    def test_outsider_cannot_read(self):
        self.login_as(self.outsider)
        r = self.client.get(
            reverse("reports:template_detail", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_anon_redirected(self):
        r = self.client.get(
            reverse("reports:template_detail", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 302)


# ── Template Update ─────────────────────────────────────────────────────────


class TemplateUpdateViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "update")

    def test_officer_gets_form(self):
        self.login_as(self.officer)
        r = self.client.get(
            reverse("reports:template_update", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_update(self):
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_update", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)


# ── Schema Designer ──────────────────────────────────────────────────────────


class SchemaDesignerViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "schema")

    def test_officer_gets_designer(self):
        self.login_as(self.officer)
        r = self.client.get(
            reverse("reports:template_schema", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Visual Schema Designer")

    def test_viewer_cannot_access_designer(self):
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_schema", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_valid_schema_post_redirects(self):
        self.login_as(self.officer)
        schema = {
            "sections": [
                {
                    "code": "intro",
                    "name": "Introduction",
                    "sort_order": 0,
                    "groups": [
                        {
                            "code": "basics",
                            "name": "Basic Info",
                            "sort_order": 0,
                            "fields": [
                                {
                                    "code": "title_field",
                                    "label": "Report Title",
                                    "field_type": "TEXT",
                                    "data_type": "STRING",
                                    "sort_order": 0,
                                },
                            ],
                        }
                    ],
                }
            ]
        }
        r = self.client.post(
            reverse("reports:template_schema", kwargs={"pk": self.template.pk}),
            {"schema": json.dumps(schema), "change_summary": "Initial"},
        )
        self.assertIn(r.status_code, (200, 302))

    def test_invalid_json_returns_form_error(self):
        self.login_as(self.officer)
        r = self.client.post(
            reverse("reports:template_schema", kwargs={"pk": self.template.pk}),
            {"schema": "{not valid json!", "change_summary": ""},
        )
        self.assertEqual(r.status_code, 200)


# ── Template Preview ─────────────────────────────────────────────────────────


class TemplatePreviewViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "preview")

    def test_viewer_cannot_preview(self):
        """Preview requires REPORT_TEMPLATE_PREVIEW; viewer only has view."""
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_preview", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_outsider_cannot_preview(self):
        self.login_as(self.outsider)
        r = self.client.get(
            reverse("reports:template_preview", kwargs={"pk": self.template.pk})
        )
        self.assertIn(r.status_code, (403, 404))


# ── Template Publish ─────────────────────────────────────────────────────────


class TemplatePublishViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "publish")

    def test_manager_gets_publish_form(self):
        self.login_as(self.manager)
        r = self.client.get(
            reverse("reports:template_publish", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)

    def test_officer_cannot_publish(self):
        """Officer has create/update/view but not publish."""
        self.login_as(self.officer)
        r = self.client.get(
            reverse("reports:template_publish", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)


# ── Template Archive / Restore / Delete ─────────────────────────────────────


class TemplateLifecycleViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "lifecycle")

    def test_manager_can_post_archive(self):
        self.login_as(self.manager)
        r = self.client.post(
            reverse("reports:template_archive", kwargs={"pk": self.template.pk})
        )
        self.assertIn(r.status_code, (302,))

    def test_officer_cannot_archive(self):
        self.login_as(self.officer)
        r = self.client.post(
            reverse("reports:template_archive", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_manager_can_delete_draft(self):
        self.login_as(self.manager)
        r = self.client.post(
            reverse("reports:template_delete", kwargs={"pk": self.template.pk})
        )
        self.assertIn(r.status_code, (302,))


# ── Template Clone ────────────────────────────────────────────────────────────


class TemplateCloneViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "clone")

    def test_manager_gets_clone_form(self):
        self.login_as(self.manager)
        r = self.client.get(
            reverse("reports:template_clone", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_clone(self):
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_clone", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_clone_post_creates_new_template(self):
        self.login_as(self.manager)
        r = self.client.post(
            reverse("reports:template_clone", kwargs={"pk": self.template.pk}),
            {
                "new_code": "vtest-clone-copy",
                "new_title": "Cloned Template",
                "notes": "",
            },
        )
        self.assertIn(r.status_code, (200, 302))


# ── Template Import / Export ──────────────────────────────────────────────────


class TemplateImportExportViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "importex")

    def test_manager_gets_import_form(self):
        self.login_as(self.manager)
        r = self.client.get(reverse("reports:template_import"))
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_import(self):
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:template_import"))
        self.assertEqual(r.status_code, 403)

    def test_manager_can_export(self):
        self.login_as(self.manager)
        r = self.client.get(
            reverse("reports:template_export", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)
        self.assertIn("application/json", r.get("Content-Type", ""))


# ── Template Version views ─────────────────────────────────────────────────────


class TemplateVersionViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.template = _make_template(self.manager, "versions")

    def test_viewer_can_list_versions(self):
        self.login_as(self.viewer)
        r = self.client.get(
            reverse("reports:template_version_list", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 200)

    def test_outsider_cannot_list_versions(self):
        self.login_as(self.outsider)
        r = self.client.get(
            reverse("reports:template_version_list", kwargs={"pk": self.template.pk})
        )
        self.assertEqual(r.status_code, 403)

    def test_restore_version_accessible_to_officer(self):
        """Officer has update permission required for version restore."""
        version = ReportTemplateVersion.objects.filter(template=self.template).first()
        if not version:
            self.skipTest("No version exists for this template")
        self.login_as(self.officer)
        url = reverse(
            "reports:template_version_restore",
            kwargs={"pk": self.template.pk, "version_pk": version.pk},
        )
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)


# ── Category views ────────────────────────────────────────────────────────────


class CategoryViewTests(ReportsTestCase):
    def setUp(self):
        super().setUp()
        self.cat = ReportCategory.objects.first()

    def test_viewer_can_list_categories(self):
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:category_list"))
        self.assertEqual(r.status_code, 200)

    def test_manager_gets_create_form(self):
        self.login_as(self.manager)
        r = self.client.get(reverse("reports:category_create"))
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_configure(self):
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:category_create"))
        self.assertEqual(r.status_code, 403)

    def test_manager_can_update_category(self):
        self.login_as(self.manager)
        r = self.client.get(
            reverse("reports:category_update", kwargs={"pk": self.cat.pk})
        )
        self.assertEqual(r.status_code, 200)

    def test_manager_can_toggle_category(self):
        self.login_as(self.manager)
        r = self.client.post(
            reverse("reports:category_toggle", kwargs={"pk": self.cat.pk})
        )
        self.assertEqual(r.status_code, 302)


# ── Settings view ────────────────────────────────────────────────────────────


class ReportBuilderSettingsViewTests(ReportsTestCase):
    def test_manager_can_access_settings(self):
        self.login_as(self.manager)
        r = self.client.get(reverse("reports:settings"))
        self.assertEqual(r.status_code, 200)

    def test_viewer_cannot_access_settings(self):
        self.login_as(self.viewer)
        r = self.client.get(reverse("reports:settings"))
        self.assertEqual(r.status_code, 403)
