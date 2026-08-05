"""Direct-object authorization, private files, and safe export tests."""

from django.urls import reverse

from apps.stakeholders.constants import ConfidentialityLevel
from apps.stakeholders.models import StakeholderContact
from apps.stakeholders.services import StakeholderDocumentService

from .base import StakeholderTestCase


class DirectObjectAuthorizationTests(StakeholderTestCase):
    def setUp(self):
        super().setUp()
        self.allowed = self.create_stakeholder(
            primary_responsible_officer=self.viewer,
            legal_name="Allowed Partner",
        )
        self.denied = self.create_stakeholder(
            legal_name="Denied Partner",
            confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        )
        self.grant_permissions(
            self.viewer,
            "partners.view",
            "partners.view_profile",
        )
        self.client.force_login(self.viewer)

    def test_scoped_profile_returns_404_for_an_existing_denied_object(self):
        allowed_response = self.client.get(
            reverse("stakeholders:profile", kwargs={"pk": self.allowed.pk})
        )
        denied_response = self.client.get(
            reverse("stakeholders:profile", kwargs={"pk": self.denied.pk})
        )
        self.assertEqual(allowed_response.status_code, 200)
        self.assertEqual(denied_response.status_code, 404)

    def test_anonymous_and_permissionless_users_cannot_open_directory(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse("stakeholders:directory")).status_code, 302
        )
        self.client.force_login(self.outsider)
        self.assertEqual(
            self.client.get(reverse("stakeholders:directory")).status_code, 403
        )

    def test_private_contact_is_not_rendered_without_contact_permission(self):
        StakeholderContact.objects.create(
            stakeholder=self.allowed,
            full_name="Secret Contact",
            email="secret-contact@example.com",
        )
        response = self.client.get(
            reverse("stakeholders:profile", kwargs={"pk": self.allowed.pk})
        )
        self.assertNotContains(response, "Secret Contact")
        self.assertNotContains(response, "secret-contact@example.com")


class ProtectedDownloadTests(StakeholderTestCase):
    def setUp(self):
        super().setUp()
        self.allowed = self.create_stakeholder(primary_responsible_officer=self.viewer)
        self.denied = self.create_stakeholder()
        service = StakeholderDocumentService(user=self.manager)
        self.allowed_document = service.add_version(
            self.allowed,
            document_key="allowed",
            title="Allowed document",
            document_type="Evidence",
            file=self.pdf_upload("allowed.pdf"),
        )
        self.denied_document = service.add_version(
            self.denied,
            document_key="denied",
            title="Denied document",
            document_type="Evidence",
            file=self.pdf_upload("denied.pdf"),
        )
        self.grant_permissions(
            self.viewer,
            "partners.view",
            "partners.manage_documents",
        )
        self.client.force_login(self.viewer)

    def test_authorized_download_is_private_and_not_sniffable(self):
        response = self.client.get(
            reverse(
                "stakeholders:document_download",
                kwargs={"document_pk": self.allowed_document.pk},
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
                "stakeholders:document_download",
                kwargs={"document_pk": self.denied_document.pk},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_document_download_requires_document_permission(self):
        self.client.force_login(self.owner)
        self.grant_permissions(self.owner, "partners.view")
        self.allowed.primary_responsible_officer = self.owner
        self.allowed.save(update_fields=["primary_responsible_officer"])
        response = self.client.get(
            reverse(
                "stakeholders:document_download",
                kwargs={"document_pk": self.allowed_document.pk},
            )
        )
        self.assertEqual(response.status_code, 403)


class CsvExportSecurityTests(StakeholderTestCase):
    def test_export_is_formula_safe_scoped_and_has_private_cache_headers(self):
        visible = self.create_stakeholder(
            legal_name='=HYPERLINK("https://example.invalid")',
            primary_responsible_officer=self.viewer,
        )
        denied = self.create_stakeholder(legal_name="Denied Export Row")
        self.grant_permissions(self.viewer, "partners.view", "partners.export")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("stakeholders:register_export"))
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=HYPERLINK", content)
        self.assertIn(visible.reference_number, content)
        self.assertNotIn(denied.reference_number, content)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response["Pragma"], "no-cache")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")

    def test_export_without_permission_is_denied(self):
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("stakeholders:register_export"))
        self.assertEqual(response.status_code, 403)

    def test_export_permission_alone_does_not_bypass_record_scope(self):
        stakeholder = self.create_stakeholder(legal_name="Out of Scope")
        self.grant_permissions(self.outsider, "partners.export")
        self.client.force_login(self.outsider)
        response = self.client.get(reverse("stakeholders:register_export"))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(stakeholder.reference_number, response.content.decode())
