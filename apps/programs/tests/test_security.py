"""Direct-object authorization, protected downloads, and safe export tests."""

from django.urls import reverse

from apps.programs.models import ProgramStatus
from apps.programs.services import ProgramDocumentService

from .base import ProgramTestCase


class DirectObjectAuthorizationTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.allowed = self.create_program(
            created_by=self.viewer, program_manager=self.viewer
        )
        self.denied = self.create_program(created_by=self.manager)
        self.grant_permissions(self.viewer, "programmes.view")
        self.client.force_login(self.viewer)

    def test_scoped_profile_returns_404_for_an_existing_denied_object(self):
        allowed_response = self.client.get(
            reverse("programs:program_profile", kwargs={"pk": self.allowed.pk})
        )
        denied_response = self.client.get(
            reverse("programs:program_profile", kwargs={"pk": self.denied.pk})
        )
        self.assertEqual(allowed_response.status_code, 200)
        self.assertEqual(denied_response.status_code, 404)

    def test_anonymous_and_permissionless_users_cannot_open_directory(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse("programs:program_directory")).status_code, 302
        )
        self.client.force_login(self.outsider)
        self.assertEqual(
            self.client.get(reverse("programs:program_directory")).status_code, 403
        )

    def test_archived_program_is_hidden_from_profile(self):
        self.allowed.is_archived = True
        self.allowed.save(update_fields=["is_archived"])
        response = self.client.get(
            reverse("programs:program_profile", kwargs={"pk": self.allowed.pk})
        )
        self.assertEqual(response.status_code, 404)


class ProtectedDownloadTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.allowed = self.create_program(
            created_by=self.viewer, program_manager=self.viewer
        )
        self.denied = self.create_program(created_by=self.manager)
        service = ProgramDocumentService(user=self.manager)
        self.allowed_document = service.upload(
            self.allowed,
            None,
            title="Allowed document",
            document_type=self.taxonomy("DOCUMENT_TYPE"),
            file=self.pdf_upload("allowed.pdf"),
        )
        self.denied_document = service.upload(
            self.denied,
            None,
            title="Denied document",
            document_type=self.taxonomy("DOCUMENT_TYPE"),
            file=self.pdf_upload("denied.pdf"),
        )
        self.grant_permissions(self.viewer, "programmes.view")
        self.client.force_login(self.viewer)

    def test_authorized_download_is_private_and_not_sniffable(self):
        response = self.client.get(
            reverse(
                "programs:document_download",
                kwargs={"pk": self.allowed_document.pk},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        response.close()

    def test_scoped_download_returns_404_for_denied_existing_document(self):
        response = self.client.get(
            reverse(
                "programs:document_download",
                kwargs={"pk": self.denied_document.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_document_download_requires_view_permission(self):
        self.client.force_login(self.outsider)
        response = self.client.get(
            reverse(
                "programs:document_download",
                kwargs={"pk": self.allowed_document.pk},
            )
        )
        self.assertEqual(response.status_code, 403)


class CsvExportSecurityTests(ProgramTestCase):
    def setUp(self):
        super().setUp()
        self.visible = self.create_program(
            title='=HYPERLINK("https://example.invalid")',
            created_by=self.viewer,
            program_manager=self.viewer,
            status=ProgramStatus.ACTIVE,
        )
        self.denied = self.create_program(created_by=self.manager)
        self.grant_permissions(self.viewer, "programmes.view", "programmes.export")
        self.client.force_login(self.viewer)

    def test_export_is_formula_safe_scoped_and_has_private_cache_headers(self):
        response = self.client.get(reverse("programs:program_register_export"))
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=HYPERLINK", content)
        self.assertIn(self.visible.reference_number, content)
        self.assertNotIn(self.denied.reference_number, content)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_export_without_permission_is_denied(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("programs:program_register_export"))
        self.assertEqual(response.status_code, 403)

    def test_export_permission_alone_does_not_bypass_record_scope(self):
        program = self.create_program(title="Out of Scope", created_by=self.manager)
        self.grant_permissions(self.outsider, "programmes.export")
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("programs:program_register_export"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(program.reference_number, response.content.decode())
