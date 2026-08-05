"""Authorization, privacy, upload, and export tests for volunteers."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.volunteers import models as volunteer_models
from apps.volunteers.admin import ServiceManagedAdminMixin
from apps.volunteers.constants import VolunteerStatus
from apps.volunteers.models import (
    VolunteerApplication,
    VolunteerCategory,
    VolunteerProfile,
    VolunteerType,
)
from apps.volunteers.validators import validate_volunteer_document

User = get_user_model()


class VolunteerSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="owner@example.com",
            username="owner",
            first_name="Profile",
            last_name="Owner",
            password="Password123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="other",
            first_name="Other",
            last_name="Volunteer",
        )
        self.profile = VolunteerProfile.objects.create(
            user=self.user,
            reference_number="VOL-OWNER-0001",
            status=VolunteerStatus.ACTIVE,
            email="private@example.com",
            emergency_contact_name="Private Contact",
        )
        self.other_profile = VolunteerProfile.objects.create(
            user=self.other_user,
            reference_number="VOL-OTHER-0001",
            status=VolunteerStatus.ACTIVE,
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="volunteers.view")
        )
        self.client.login(email=self.user.email, password="Password123!")

    def test_view_permission_is_limited_to_own_profile(self):
        own_response = self.client.get(
            reverse("volunteers:detail", kwargs={"pk": self.profile.pk})
        )
        other_response = self.client.get(
            reverse("volunteers:detail", kwargs={"pk": self.other_profile.pk})
        )
        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)

    def test_confidential_fields_are_hidden_without_permission(self):
        response = self.client.get(
            reverse("volunteers:detail", kwargs={"pk": self.profile.pk})
        )
        self.assertNotContains(response, "private@example.com")
        self.assertNotContains(response, "Private Contact")
        self.assertContains(response, "details are restricted")

    def test_anonymous_user_cannot_access_directory(self):
        self.client.logout()
        response = self.client.get(reverse("volunteers:directory"))
        self.assertEqual(response.status_code, 302)

    def test_invalid_document_signature_is_rejected(self):
        upload = SimpleUploadedFile(
            "resume.pdf",
            b"not a real PDF",
            content_type="application/pdf",
        )
        with self.assertRaises(ValidationError):
            validate_volunteer_document(upload)

    def test_workflow_admins_cannot_bypass_domain_services(self):
        request = RequestFactory().get("/admin/volunteers/")
        request.user = User.objects.create_superuser(
            email="admin@example.com",
            username="admin",
            password="Password123!",
        )
        service_managed_models = (
            volunteer_models.VolunteerProfile,
            volunteer_models.VolunteerRecruitment,
            volunteer_models.VolunteerApplication,
            volunteer_models.VolunteerScreening,
            volunteer_models.VolunteerInterview,
            volunteer_models.VolunteerOnboarding,
            volunteer_models.VolunteerAssignment,
            volunteer_models.VolunteerAttendance,
            volunteer_models.VolunteerTraining,
            volunteer_models.VolunteerPerformance,
            volunteer_models.VolunteerRecognition,
            volunteer_models.VolunteerLeave,
            volunteer_models.VolunteerExit,
            volunteer_models.VolunteerSkill,
            volunteer_models.VolunteerInterest,
            volunteer_models.VolunteerWelfare,
            volunteer_models.VolunteerDocument,
            volunteer_models.VolunteerActivityLog,
            volunteer_models.VolunteerDisciplinaryRecord,
            volunteer_models.VolunteerCommunication,
            volunteer_models.VolunteerCategory,
            volunteer_models.VolunteerType,
            volunteer_models.VolunteerLevel,
        )

        for model in service_managed_models:
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertIsInstance(model_admin, ServiceManagedAdminMixin)
                self.assertFalse(model_admin.has_add_permission(request))
                self.assertFalse(model_admin.has_change_permission(request))
                self.assertFalse(model_admin.has_delete_permission(request))
                self.assertEqual(
                    set(model_admin.get_readonly_fields(request)),
                    {field.name for field in model._meta.fields},
                )


class VolunteerFeaturePermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="limited@example.com",
            username="limited",
            first_name="Limited",
            last_name="User",
            password="Password123!",
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="volunteers.view")
        )
        self.client.login(email=self.user.email, password="Password123!")

    def test_activity_create_requires_manage_activity_permission(self):
        response = self.client.get(reverse("volunteers:activity_log_create"))
        self.assertIn(response.status_code, (302, 403))

    def test_disciplinary_create_requires_manage_disciplinary_permission(self):
        response = self.client.get(reverse("volunteers:disciplinary_create"))
        self.assertIn(response.status_code, (302, 403))

    def test_communication_create_requires_manage_communications_permission(self):
        response = self.client.get(reverse("volunteers:communication_create"))
        self.assertIn(response.status_code, (302, 403))

    def test_document_upload_requires_manage_documents_permission(self):
        response = self.client.get(reverse("volunteers:document_upload"))
        self.assertIn(response.status_code, (302, 403))

    def test_category_management_requires_configure_permission(self):
        response = self.client.get(reverse("volunteers:category_list"))
        self.assertIn(response.status_code, (302, 403))

    def test_list_views_are_visible_with_view_permission(self):
        for url_name in (
            "activity_log_list",
            "disciplinary_list",
            "communication_list",
            "document_list",
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(f"volunteers:{url_name}"))
                self.assertEqual(response.status_code, 200)


class VolunteerPublicApplicationTests(TestCase):
    def test_public_application_renders_and_uses_central_reference(self):
        category, _ = VolunteerCategory.objects.get_or_create(
            code="COMMUNITY", defaults={"name": "Community Volunteer"}
        )
        volunteer_type, _ = VolunteerType.objects.get_or_create(
            code="PART_TIME", defaults={"name": "Part-Time Volunteer"}
        )
        response = self.client.get(reverse("volunteers:apply"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Submit Application")

        response = self.client.post(
            reverse("volunteers:apply"),
            {
                "applicant_name": "Public Applicant",
                "email": "public@example.com",
                "phone_number": "+260970000002",
                "category": category.pk,
                "volunteer_type": volunteer_type.pk,
                "consent_confirmed": "on",
            },
        )
        self.assertRedirects(response, reverse("volunteers:application_success"))
        application = VolunteerApplication.objects.get(email="public@example.com")
        self.assertTrue(application.reference_number.startswith("VAP-SITADC-"))

    def test_export_neutralizes_spreadsheet_formulas(self):
        admin = User.objects.create_superuser(
            email="exporter@example.com",
            username="exporter",
            first_name="=CMD()",
            last_name="Exporter",
            password="Password123!",
        )
        VolunteerProfile.objects.create(
            user=admin,
            reference_number="VOL-EXPORT-0001",
            status=VolunteerStatus.ACTIVE,
        )
        self.client.login(email=admin.email, password="Password123!")
        response = self.client.get(reverse("volunteers:reports") + "?export=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("'=CMD() Exporter", response.content.decode())

    def test_export_supports_xlsx_docx_pdf(self):
        admin = User.objects.create_superuser(
            email="multi-exporter@example.com",
            username="multi-exporter",
            first_name="Multi",
            last_name="Exporter",
            password="Password123!",
        )
        VolunteerProfile.objects.create(
            user=admin,
            reference_number="VOL-EXPORT-0002",
            status=VolunteerStatus.ACTIVE,
        )
        self.client.login(email=admin.email, password="Password123!")
        expected = {
            "xlsx": (
                "application/vnd.openxmlformats-officedocument." "spreadsheetml.sheet"
            ),
            "docx": (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            "pdf": "application/pdf",
        }
        for export_format, content_type in expected.items():
            with self.subTest(export_format=export_format):
                response = self.client.get(
                    reverse("volunteers:reports") + f"?export={export_format}"
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], content_type)
                self.assertGreater(len(response.content), 0)
