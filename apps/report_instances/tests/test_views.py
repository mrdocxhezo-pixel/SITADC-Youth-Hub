"""View tests for the ``report_instances`` app."""

import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.report_instances.models import Report
from apps.report_instances.services import assign_report, submit_report, validate_report
from apps.reports.constants import ReportStatus

from .base import ReportInstanceBaseTestCase


class ReportViewAuthTest(ReportInstanceBaseTestCase):
    """Login is required for every report route."""

    def _get(self, name, **kwargs):
        return self.client.get(reverse(f"report_instances:{name}", kwargs=kwargs))

    def test_dashboard_requires_login(self):
        response = self._get("dashboard")
        self.assertEqual(response.status_code, 302)

    def test_list_requires_login(self):
        response = self._get("list")
        self.assertEqual(response.status_code, 302)

    def test_detail_requires_login(self):
        report = self.make_report()
        response = self._get("detail", pk=report.pk)
        self.assertEqual(response.status_code, 302)


class ReportListViewTest(ReportInstanceBaseTestCase):
    """Listing respects the view permission."""

    def setUp(self):
        self.client.force_login(self.admin)

    def test_list_renders(self):
        self.make_report(title="Visible")
        response = self.client.get(reverse("report_instances:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Visible")

    def test_list_filters_by_status(self):
        report = self.make_report(title="Draft Report")
        response = self.client.get(
            reverse("report_instances:list"), {"status": ReportStatus.DRAFT}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, report.title)

    def test_list_denied_without_permission(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("report_instances:list"))
        self.assertEqual(response.status_code, 302)


class ReportCreateViewTest(ReportInstanceBaseTestCase):
    """Creating a report from a published template."""

    def setUp(self):
        self.client.force_login(self.admin)

    def test_get_create_form(self):
        response = self.client.get(reverse("report_instances:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Template")

    def test_post_creates_report_and_redirects(self):
        response = self.client.post(
            reverse("report_instances:create"),
            {
                "template": str(self.template.pk),
                "title": "Newly Created",
                "confidentiality": "INTERNAL",
            },
        )
        self.assertEqual(response.status_code, 302)
        report = Report.objects.get(title="Newly Created")
        self.assertRedirects(
            response, reverse("report_instances:enter_data", kwargs={"pk": report.pk})
        )


class ReportDetailAndDataEntryTest(ReportInstanceBaseTestCase):
    """Detail rendering and dynamic data entry."""

    def setUp(self):
        self.client.force_login(self.admin)

    def test_detail_renders(self):
        report = self.make_report(title="Detail Report")
        response = self.client.get(
            reverse("report_instances:detail", kwargs={"pk": report.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Detail Report")

    def test_enter_data_get(self):
        report = self.make_report()
        response = self.client.get(
            reverse("report_instances:enter_data", kwargs={"pk": report.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_enter_data_post_saves_responses(self):
        report = self.make_report()
        section = self.template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        field = group.fields.get(code="field1")
        field_name = f"section_{section.pk}_field_{field.pk}"

        response = self.client.post(
            reverse("report_instances:enter_data", kwargs={"pk": report.pk}),
            {field_name: "entered value"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(report.field_responses.count(), 1)
        self.assertEqual(report.section_responses.count(), 1)

    def test_enter_data_post_with_date_and_file_upload(self):
        """Dates serialize to ISO strings and files persist to storage."""
        from django.core.files.storage import default_storage

        from apps.report_instances.services import create_report
        from apps.reports.services import (
            ReportTemplateService,
            TemplatePublicationService,
            TemplateSchemaService,
        )

        template = ReportTemplateService(user=self.admin).create(
            code="rpt-entry-mixed",
            title="Mixed Entry Template",
            category=self.category,
        )
        schema = {
            "template": {
                "code": template.code,
                "title": template.title,
                "reference_number": template.reference_number,
            },
            "sections": [
                {
                    "code": "sec1",
                    "name": "Section 1",
                    "sort_order": 1,
                    "groups": [
                        {
                            "code": "grp1",
                            "name": "Group 1",
                            "sort_order": 1,
                            "fields": [
                                {
                                    "code": "field1",
                                    "label": "Full Name",
                                    "field_type": "TEXT",
                                    "data_type": "STRING",
                                    "required": True,
                                },
                                {
                                    "code": "fielddob",
                                    "label": "Date of Birth",
                                    "field_type": "DATE",
                                    "data_type": "DATE",
                                    "required": False,
                                },
                                {
                                    "code": "fielddoc",
                                    "label": "Evidence",
                                    "field_type": "DOCUMENT",
                                    "data_type": "STRING",
                                    "required": False,
                                },
                            ],
                        }
                    ],
                }
            ],
            "conditional_rules": [],
            "components": [],
        }
        TemplateSchemaService(user=self.admin).save_schema(template, schema)
        TemplatePublicationService(user=self.admin).publish(template)

        report = create_report(template=template, title="Entry Report", owner=self.owner)
        section = template.sections.get(code="sec1")
        group = section.groups.get(code="grp1")
        text_field = group.fields.get(code="field1")
        date_field = group.fields.get(code="fielddob")
        doc_field = group.fields.get(code="fielddoc")

        payload = {
            f"section_{section.pk}_field_{text_field.pk}": "entered value",
            f"section_{section.pk}_field_{date_field.pk}": "1999-11-18",
            f"section_{section.pk}_field_{doc_field.pk}": SimpleUploadedFile(
                "evidence.jpg", b"bytes", content_type="image/jpeg"
            ),
        }

        response = self.client.post(
            reverse("report_instances:enter_data", kwargs={"pk": report.pk}),
            payload,
        )
        self.assertEqual(response.status_code, 302)

        date_response = report.field_responses.get(field=date_field)
        self.assertEqual(date_response.value, "1999-11-18")

        file_response = report.field_responses.get(field=doc_field)
        self.assertIsInstance(file_response.value, str)
        self.assertTrue(file_response.value.startswith("report_field_uploads/"))
        self.assertTrue(default_storage.exists(file_response.value))

        section_response = report.section_responses.get(section=section)
        self.assertEqual(section_response.data[str(date_field.pk)], "1999-11-18")
        json.dumps(section_response.data)  # must be JSON-serializable

        self.assertTrue(
            report.timeline_events.filter(event_type="FIELD_FILE_UPLOADED").exists()
        )

    def test_preview_renders(self):
        report = self.make_report()
        response = self.client.get(
            reverse("report_instances:preview", kwargs={"pk": report.pk})
        )
        self.assertEqual(response.status_code, 200)


class ReportLifecycleViewTest(ReportInstanceBaseTestCase):
    """Lifecycle actions reachable through the view layer."""

    def setUp(self):
        self.client.force_login(self.admin)

    def _submitted(self):
        report = self.make_report()
        self.fill_report(report)
        validate_report(report, validated_by=self.admin)
        submit_report(report, submitted_by=self.admin)
        report.refresh_from_db()
        return report

    def test_validate_then_submit(self):
        report = self.make_report()
        self.fill_report(report)
        url = reverse("report_instances:validate", kwargs={"pk": report.pk})
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.READY_FOR_SUBMISSION)

        url = reverse("report_instances:submit", kwargs={"pk": report.pk})
        response = self.client.post(url, {"notes": "Please review"})
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)

    def test_withdraw_returns_to_draft(self):
        report = self._submitted()
        response = self.client.post(
            reverse("report_instances:withdraw", kwargs={"pk": report.pk}),
            {"reason": "Not ready"},
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.DRAFT)

    def test_archive_and_restore(self):
        report = self._submitted()
        response = self.client.post(
            reverse("report_instances:archive", kwargs={"pk": report.pk}), {}
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.ARCHIVED)

        response = self.client.post(
            reverse("report_instances:restore", kwargs={"pk": report.pk}), {}
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)

    def test_review_approve(self):
        report = self._submitted()
        response = self.client.post(
            reverse("report_instances:review", kwargs={"pk": report.pk}),
            {"action": "approve", "notes": "Approved"},
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.APPROVED)

    def test_duplicate(self):
        report = self.make_report(title="Source")
        response = self.client.post(
            reverse("report_instances:duplicate", kwargs={"pk": report.pk}),
            {"title": "Cloned"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(title="Cloned").exists())

    def test_start_review(self):
        report = self._submitted()
        response = self.client.post(
            reverse("report_instances:start_review", kwargs={"pk": report.pk}), {}
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.UNDER_REVIEW)


class ReportCommentEvidenceTest(ReportInstanceBaseTestCase):
    """Comments, evidence and attachments via views."""

    def setUp(self):
        self.client.force_login(self.admin)
        self.report = self.make_report()

    def test_add_comment(self):
        response = self.client.post(
            reverse("report_instances:comment", kwargs={"pk": self.report.pk}),
            {"body": "A comment", "is_internal": "on"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.comments.count(), 1)
        self.assertTrue(self.report.comments.first().is_internal)

    def test_add_video_link(self):
        response = self.client.post(
            reverse("report_instances:video_link", kwargs={"pk": self.report.pk}),
            {"url": "https://example.com/video", "description": "Walkthrough"},
        )
        self.assertEqual(response.status_code, 302)
        evidence = self.report.evidence_items.first()
        self.assertEqual(evidence.evidence_type, "VIDEO")
        self.assertEqual(evidence.original_filename, "https://example.com/video")

    def test_upload_evidence(self):
        file = SimpleUploadedFile("photo.jpg", b"data", content_type="image/jpeg")
        response = self.client.post(
            reverse("report_instances:evidence", kwargs={"pk": self.report.pk}),
            {"evidence_type": "PHOTOGRAPH", "file": file},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.evidence_items.count(), 1)

    def test_upload_attachment(self):
        file = SimpleUploadedFile("doc.pdf", b"data", content_type="application/pdf")
        response = self.client.post(
            reverse("report_instances:attachment", kwargs={"pk": self.report.pk}),
            {"file": file},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.attachments.count(), 1)

    def test_assign_reviewer(self):
        assign_report(
            self.report,
            assigned_to=self.reviewer,
            assigned_by=self.admin,
            role="REVIEWER",
        )
        response = self.client.post(
            reverse("report_instances:assign", kwargs={"pk": self.report.pk}),
            {"assigned_to": str(self.other.pk), "role": "REVIEWER"},
        )
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.assigned_reviewer, self.other)


class ReportVersionViewTest(ReportInstanceBaseTestCase):
    """Version history pages render without errors."""

    def setUp(self):
        self.client.force_login(self.admin)
        self.report = self.make_report()
        self.fill_report(self.report)
        validate_report(self.report, validated_by=self.admin)
        submit_report(self.report, submitted_by=self.admin)
        self.report.refresh_from_db()

    def test_versions_list_renders(self):
        response = self.client.get(
            reverse("report_instances:versions", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Version History")

    def test_version_detail_renders(self):
        version = self.report.versions.first()
        response = self.client.get(
            reverse(
                "report_instances:version_detail",
                kwargs={"pk": self.report.pk, "version_number": version.version_number},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"v{version.version_number}")


class ReportExportViewTest(ReportInstanceBaseTestCase):
    """Exports return downloadable responses."""

    def setUp(self):
        self.client.force_login(self.admin)
        self.report = self.make_report()

    def test_export_csv(self):
        response = self.client.post(
            reverse("report_instances:export", kwargs={"pk": self.report.pk}),
            {"format": "CSV"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_export_html(self):
        response = self.client.post(
            reverse("report_instances:export", kwargs={"pk": self.report.pk}),
            {"format": "HTML"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/html")

    def test_export_json_default(self):
        response = self.client.post(
            reverse("report_instances:export", kwargs={"pk": self.report.pk}),
            {"format": "UNKNOWN"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")


class ReportApiViewTest(ReportInstanceBaseTestCase):
    """Auto-save and template-fields JSON endpoints."""

    def setUp(self):
        self.client.force_login(self.admin)
        self.report = self.make_report()

    def test_autosave(self):
        response = self.client.post(
            reverse("report_instances:autosave", kwargs={"pk": self.report.pk}),
            data=json.dumps({"sections": {}, "fields": {}}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")

    def test_template_fields(self):
        response = self.client.get(
            reverse(
                "report_instances:template_fields",
                kwargs={"template_id": self.template.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["sections"]), 1)
        self.assertEqual(payload["sections"][0]["name"], "Section 1")


class ReportPermissionDeniedViewTest(ReportInstanceBaseTestCase):
    """Unauthorized users are denied server-side."""

    def setUp(self):
        # ``self.other`` has no report_instances role grant.
        self.client.force_login(self.other)
        self.report = self.make_report()

    def test_create_redirects_without_permission(self):
        response = self.client.get(reverse("report_instances:create"))
        self.assertEqual(response.status_code, 302)

    def test_detail_redirects_for_unrelated_user(self):
        response = self.client.get(
            reverse("report_instances:detail", kwargs={"pk": self.report.pk})
        )
        self.assertEqual(response.status_code, 302)

    def test_archive_redirects_without_permission(self):
        report = self.make_report()
        report.status = ReportStatus.SUBMITTED
        report.save()
        response = self.client.post(
            reverse("report_instances:archive", kwargs={"pk": report.pk}), {}
        )
        self.assertEqual(response.status_code, 302)
        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.SUBMITTED)
