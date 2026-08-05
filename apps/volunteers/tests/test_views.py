"""
View tests for volunteer management module.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.volunteers.constants import VolunteerStatus
from apps.volunteers.models import (
    VolunteerCategory,
    VolunteerOnboarding,
    VolunteerProfile,
)

User = get_user_model()


class VolunteerViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="staff@example.com",
            username="staffuser",
            password="Password123!",
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(email="staff@example.com", password="Password123!")

        self.category, _ = VolunteerCategory.objects.get_or_create(
            code="COMMUNITY", defaults={"name": "Community Volunteer"}
        )
        self.profile = VolunteerProfile.objects.create(
            user=self.user,
            reference_number="SITADC-VOL-2026-000001",
            category=self.category,
            status=VolunteerStatus.ACTIVE,
        )
        VolunteerOnboarding.objects.create(
            profile=self.profile,
            orientation_completed=True,
            code_of_conduct_signed=True,
            safeguarding_agreed=True,
            confidentiality_signed=True,
            id_card_issued=True,
            completed=True,
        )

    def test_dashboard_view(self):
        url = reverse("volunteers:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_directory_view(self):
        url = reverse("volunteers:directory")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_detail_view(self):
        url = reverse("volunteers:detail", kwargs={"pk": self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_id_card_view(self):
        url = reverse("volunteers:id_card", kwargs={"pk": self.profile.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_reports_view(self):
        url = reverse("volunteers:reports")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_recruitment_list_view(self):
        url = reverse("volunteers:recruitment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("volunteers:recruitment_create"))

    def test_csv_export(self):
        url = reverse("volunteers:reports") + "?export=csv"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")


class VolunteerFeatureViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="staff@example.com",
            username="staffuser",
            password="Password123!",
            is_staff=True,
            is_superuser=True,
        )
        self.client.login(email="staff@example.com", password="Password123!")

        self.category, _ = VolunteerCategory.objects.get_or_create(
            code="COMMUNITY", defaults={"name": "Community Volunteer"}
        )
        self.profile = VolunteerProfile.objects.create(
            user=self.user,
            reference_number="SITADC-VOL-2026-000002",
            category=self.category,
            status=VolunteerStatus.ACTIVE,
        )

    def test_activity_log_list_view(self):
        url = reverse("volunteers:activity_log_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_activity_log_create_view(self):
        url = reverse("volunteers:activity_log_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "profile": self.profile.pk,
                "activity_title": "Community Cleanup",
                "category": "OUTREACH",
                "activity_date": "2026-03-10",
                "hours_served": "4.5",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_disciplinary_list_view(self):
        url = reverse("volunteers:disciplinary_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_disciplinary_create_view(self):
        url = reverse("volunteers:disciplinary_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "profile": self.profile.pk,
                "incident_date": "2026-03-15",
                "nature_of_concern": "Violated code of conduct.",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_communication_list_view(self):
        url = reverse("volunteers:communication_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_communication_create_view(self):
        url = reverse("volunteers:communication_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "profile": self.profile.pk,
                "channel": "EMAIL",
                "subject": "Welcome",
                "body": "Welcome to the team.",
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_document_list_view(self):
        url = reverse("volunteers:document_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_document_upload_view(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        url = reverse("volunteers:document_upload")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        upload = SimpleUploadedFile(
            "contract.pdf", b"%PDF-1.4 test", content_type="application/pdf"
        )
        response = self.client.post(
            url,
            {
                "profile": self.profile.pk,
                "title": "Volunteer Contract",
                "document_type": "Contract",
                "file": upload,
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_category_list_view(self):
        url = reverse("volunteers:category_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_category_create_view(self):
        url = reverse("volunteers:category_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "name": "Digital Volunteer",
                "code": "DIGITAL",
                "description": "Volunteers supporting digital initiatives.",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VolunteerCategory.objects.filter(code="DIGITAL").exists())

    def test_category_update_view(self):
        url = reverse("volunteers:category_update", kwargs={"pk": self.category.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            url,
            {
                "name": "Community Volunteer Updated",
                "code": "COMMUNITY",
                "description": "Updated description.",
                "is_active": True,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, "Community Volunteer Updated")
