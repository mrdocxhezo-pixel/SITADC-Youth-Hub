"""Beneficiary page, form, and URL integration tests."""

from datetime import date, timedelta

from django.urls import reverse
from django.utils import timezone

from apps.beneficiaries.constants import (
    BeneficiaryStatus,
    ConfidentialityLevel,
    ReferenceDataKind,
)
from apps.beneficiaries.forms import BeneficiaryForm
from apps.beneficiaries.models import Beneficiary

from .base import BeneficiaryTestCase


class BeneficiaryPageTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.beneficiary = self.create_beneficiary(
            first_name="Visible",
            last_name="Youth",
            confidentiality=ConfidentialityLevel.DIRECTORY,
            created_by=self.viewer,
            updated_by=self.viewer,
        )
        self.grant_permissions(self.viewer, "beneficiaries.view")
        self.client.force_login(self.viewer)

    def test_dashboard_renders_scoped_metrics(self):
        response = self.client.get(reverse("beneficiaries:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "beneficiaries/dashboard.html")
        self.assertEqual(response.context["metrics"]["total"], 1)

    def test_directory_renders_search_and_results(self):
        response = self.client.get(reverse("beneficiaries:directory"), {"q": "Visible"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "beneficiaries/directory.html")
        self.assertContains(response, "Visible Youth")

    def test_directory_scopes_results_to_user(self):
        self.create_beneficiary(first_name="Hidden", last_name="Other")
        response = self.client.get(reverse("beneficiaries:directory"))
        self.assertContains(response, "Visible Youth")
        self.assertNotContains(response, "Hidden Other")

    def test_profile_renders_authorized_record(self):
        response = self.client.get(
            reverse("beneficiaries:profile", kwargs={"pk": self.beneficiary.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "beneficiaries/profile.html")
        self.assertContains(response, self.beneficiary.reference_number)

    def test_profile_shows_archive_action_to_manager(self):
        self.client.force_login(self.manager)
        response = self.client.get(
            reverse("beneficiaries:profile", kwargs={"pk": self.beneficiary.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("beneficiaries:archive", kwargs={"pk": self.beneficiary.pk}),
        )

    def test_out_of_scope_profile_returns_not_found(self):
        other = self.create_beneficiary(first_name="Other", last_name="Scope")
        response = self.client.get(
            reverse("beneficiaries:profile", kwargs={"pk": other.pk})
        )
        self.assertEqual(response.status_code, 404)

    def test_households_and_groups_pages_render(self):
        response = self.client.get(reverse("beneficiaries:households"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("beneficiaries:groups"))
        self.assertEqual(response.status_code, 200)


class BeneficiaryFormTests(BeneficiaryTestCase):
    def test_profile_form_limits_each_taxonomy_to_its_kind(self):
        form = BeneficiaryForm()
        expected = {
            "gender": ReferenceDataKind.GENDER,
            "marital_status": ReferenceDataKind.MARITAL_STATUS,
            "category": ReferenceDataKind.CATEGORY,
            "classification": ReferenceDataKind.CLASSIFICATION,
            "education_level": ReferenceDataKind.EDUCATION_LEVEL,
            "occupation": ReferenceDataKind.OCCUPATION,
        }
        for field_name, kind in expected.items():
            with self.subTest(field=field_name):
                self.assertFalse(
                    form.fields[field_name].queryset.exclude(kind=kind).exists()
                )

    def test_profile_form_requires_contact_detail(self):
        form = BeneficiaryForm(data={"first_name": "No", "last_name": "Contact"})
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_profile_form_accepts_valid_contact(self):
        gender = self.taxonomy(ReferenceDataKind.GENDER, "female")
        form = BeneficiaryForm(
            data={
                "first_name": "Valid",
                "last_name": "Contact",
                "date_of_birth": date.today() - timedelta(days=365 * 22),
                "gender": gender.pk,
                "email": "valid@example.com",
                "registration_date": timezone.localdate(),
            }
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_profile_form_rejects_future_registration(self):
        form = BeneficiaryForm(
            data={
                "first_name": "Future",
                "last_name": "Registration",
                "email": "future@example.com",
                "registration_date": timezone.localdate() + timedelta(days=1),
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue(
            any("future" in message for message in form.errors.get("__all__", []))
        )


class BeneficiaryCreateViewTests(BeneficiaryTestCase):
    def setUp(self):
        super().setUp()
        self.grant_permissions(
            self.viewer, "beneficiaries.view", "beneficiaries.create"
        )
        self.client.force_login(self.viewer)

    def test_create_form_renders(self):
        response = self.client.get(reverse("beneficiaries:create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "beneficiaries/beneficiary_form.html")

    def test_create_post_registers_beneficiary(self):
        gender = self.taxonomy(ReferenceDataKind.GENDER, "female")
        response = self.client.post(
            reverse("beneficiaries:create"),
            {
                "first_name": "Posted",
                "last_name": "Profile",
                "date_of_birth": date.today() - timedelta(days=365 * 22),
                "gender": gender.pk,
                "email": "posted.profile@example.com",
                "registration_date": timezone.localdate(),
            },
        )
        self.assertEqual(response.status_code, 302)
        beneficiary = Beneficiary.all_objects.get(first_name="Posted")
        self.assertEqual(beneficiary.status, BeneficiaryStatus.IDENTIFIED)
        self.assertTrue(beneficiary.reference_number.startswith("BEN-"))
        self.assertEqual(beneficiary.created_by, self.viewer)

    def test_create_post_rejects_duplicate(self):
        self.create_beneficiary(first_name="DupView", last_name="Create")
        response = self.client.post(
            reverse("beneficiaries:create"),
            {
                "first_name": "DupView",
                "last_name": "Create",
                "email": "dup.create@example.com",
                "registration_date": timezone.localdate(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "possible duplicate")
