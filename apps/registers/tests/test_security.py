"""Security invariants: immutable audit rows, confidentiality, safe uploads."""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.registers.constants import RegisterActivityAction, RegisterApprovalStatus
from apps.registers.models import RegisterActivity, RegisterVersion

from .base import RegistersTestCase


class ActivityImmutabilityTests(RegistersTestCase):
    def test_activity_delete_blocked(self):
        entry = self.create_register_entry()
        activity = RegisterActivity.objects.get(entry=entry)
        with self.assertRaises(ValidationError):
            activity.delete()

    def test_version_delete_blocked(self):
        entry = self.create_register_entry()
        version = RegisterVersion.objects.get(entry=entry)
        with self.assertRaises(ValidationError):
            version.delete()

    def test_every_transition_records_activity(self):
        entry = self.approve_through_workflow(self.create_register_entry())
        actions = set(
            RegisterActivity.objects.filter(entry=entry).values_list(
                "action", flat=True
            )
        )
        self.assertIn(RegisterActivityAction.SUBMITTED, actions)
        self.assertIn(RegisterActivityAction.APPROVED, actions)


class ConfidentialityGuardTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.restricted = self.create_user("restricted")
        self.grant_permissions(self.restricted, "registers.view")

    def test_confidential_entry_invisible_to_viewer(self):
        confidential = self.make_confidential_entry()
        self.client.force_login(self.restricted)
        response = self.client.get(
            reverse("registers:entry_detail", kwargs={"pk": confidential.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_confidential_entry_not_in_listing(self):
        self.make_confidential_entry()
        self.client.force_login(self.restricted)
        response = self.client.get(reverse("registers:entry_list"))
        self.assertEqual(response.status_code, 200)

    def test_confidential_data_excluded_from_csv(self):
        confidential = self.make_confidential_entry()
        from apps.registers.exports import register_register_csv_response

        response = register_register_csv_response(self.officer)
        content = response.content.decode("utf-8")
        self.assertNotIn(confidential.reference_number, content)


class SafeUploadTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.restricted = self.create_user("restricted")
        self.grant_permissions(self.restricted, "registers.view")

    def test_attachment_upload_via_view(self):
        self.client.force_login(self.officer)
        entry = self.create_register_entry()
        response = self.client.post(
            reverse(
                "registers:attachment_create",
                kwargs={"entry_pk": entry.pk},
            ),
            {
                "file": SimpleUploadedFile(
                    "evidence.pdf", b"%PDF-1.4 test", "application/pdf"
                ),
                "description": "Supporting evidence",
            },
        )
        self.assertIn(response.status_code, (302, 200))
        entry.refresh_from_db()
        self.assertEqual(entry.attachments.count(), 1)

    def test_confidential_entry_attachment_denied(self):
        confidential = self.make_confidential_entry()
        self.grant_permissions(self.restricted, "registers.update")
        self.client.force_login(self.restricted)
        response = self.client.post(
            reverse(
                "registers:attachment_create",
                kwargs={"entry_pk": confidential.pk},
            ),
            {
                "file": SimpleUploadedFile(
                    "evidence.pdf", b"%PDF-1.4 test", "application/pdf"
                ),
                "description": "Nope",
            },
        )
        self.assertEqual(response.status_code, 404)


class ApprovalWorkflowGuardTests(RegistersTestCase):
    def setUp(self):
        super().setUp()
        self.submitter_only = self.create_user("submitter_only")
        self.grant_permissions(
            self.submitter_only, "registers.view", "registers.submit"
        )
        self.entry = self.create_register_entry()

    def test_approve_requires_approve_permission(self):
        self.client.force_login(self.submitter_only)
        self.client.post(
            reverse("registers:entry_submit", kwargs={"pk": self.entry.pk})
        )
        self.client.post(
            reverse("registers:entry_start_review", kwargs={"pk": self.entry.pk})
        )
        response = self.client.post(
            reverse("registers:entry_approve", kwargs={"pk": self.entry.pk})
        )
        self.assertEqual(response.status_code, 403)
        self.entry.refresh_from_db()
        self.assertNotEqual(self.entry.approval_status, RegisterApprovalStatus.APPROVED)
