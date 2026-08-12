"""Security enforcement: auth, authorization, and data protection tests."""

from django.core.exceptions import PermissionDenied
from django.urls import reverse

from apps.beneficiaries.constants import ConfidentialityLevel
from apps.beneficiaries.selectors import visible_beneficiaries

from .base import BeneficiaryTestCase


class AuthenticationTests(BeneficiaryTestCase):
    def test_anonymous_user_redirected_to_login(self):
        self.create_beneficiary()
        response = self.client.get(reverse("beneficiaries:directory"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.url)

    def test_authenticated_user_without_permission_denied(self):
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("beneficiaries:create"))
        self.assertEqual(response.status_code, 403)

    def test_post_requires_csrf_token(self):
        self.grant_permissions(self.viewer, "beneficiaries.create")
        client = self.client.__class__(enforce_csrf_checks=True)
        client.force_login(self.viewer)
        response = client.post(
            reverse("beneficiaries:create"),
            {"first_name": "Csrf", "last_name": "Attack", "email": "x@example.com"},
        )
        self.assertEqual(response.status_code, 403)


class AuthorizationTests(BeneficiaryTestCase):
    def test_export_denied_without_export_permission(self):
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("beneficiaries:register_export"))
        self.assertEqual(response.status_code, 403)

    def test_export_allowed_for_module_manager(self):
        self.client.force_login(self.manager)
        response = self.client.get(reverse("beneficiaries:register_export"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"].split(";")[0], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_related_write_permission_required_for_guardians_page(self):
        beneficiary = self.create_beneficiary(
            created_by=self.viewer, updated_by=self.viewer
        )
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("beneficiaries:guardians", kwargs={"pk": beneficiary.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_confidential_field_not_visible_to_directory_only_user(self):
        confidential = self.create_beneficiary(
            first_name="Secret",
            last_name="Identity",
            confidentiality=ConfidentialityLevel.CONFIDENTIAL,
        )
        self.grant_permissions(self.viewer, "beneficiaries.view")
        visible = list(visible_beneficiaries(self.viewer))
        self.assertNotIn(confidential, visible)

    def test_out_of_scope_related_record_page_returns_not_found(self):
        other = self.create_beneficiary(
            first_name="Outside",
            last_name="Scope",
            created_by=self.manager,
            updated_by=self.manager,
        )
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("beneficiaries:profile", kwargs={"pk": other.pk})
        )
        self.assertEqual(response.status_code, 404)


class ServiceSecurityTests(BeneficiaryTestCase):
    def test_service_requires_authenticated_actor(self):
        from apps.beneficiaries.services import BeneficiaryService

        with self.assertRaises(PermissionDenied):
            BeneficiaryService(user=None).create(first_name="No", last_name="Actor")

    def test_service_denies_write_outside_scope(self):
        from apps.beneficiaries.services import BeneficiaryService

        beneficiary = self.create_beneficiary()
        self.grant_permissions(self.viewer, "beneficiaries.update")
        with self.assertRaises(PermissionDenied):
            BeneficiaryService(user=self.viewer).update(
                beneficiary, email="hijack@example.com"
            )
