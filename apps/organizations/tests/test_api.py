"""Tests for organizational dynamic / cascading dropdown JSON API endpoints."""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase
from django.urls import reverse

from apps.organizations.models import OrganizationUnit, Position

User = get_user_model()


class OrganizationApiTests(TestCase):
    """Test JSON API endpoints used by cascading dropdowns."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_organization_structure", verbosity=0)

        cls.user = User.objects.create_user(
            email="api.user@sitadc.org",
            username="apiuser",
            password="StrongPassword123!",
        )

        cls.dir_meal = OrganizationUnit.objects.get(identifier="DIR-MEAL")
        cls.dir_fin = OrganizationUnit.objects.get(identifier="DIR-FIN-RES")
        cls.dept_meal = OrganizationUnit.objects.get(identifier="DEPT-MEAL")
        cls.dept_fin = OrganizationUnit.objects.get(identifier="DEPT-FGRM")

    def setUp(self):
        self.client = Client()

    def test_endpoints_require_authentication(self):
        """Unauthenticated requests receive 401 Unauthorized."""
        endpoints = [
            reverse("organizations:api_units"),
            reverse("organizations:api_directorates"),
            reverse("organizations:api_departments"),
            reverse("organizations:api_program_technical"),
            reverse("organizations:api_teams"),
            reverse("organizations:api_positions"),
        ]
        for url in endpoints:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 401, f"Failed for {url}")

    def test_directorates_endpoint(self):
        """Directorates endpoint returns all 17 approved active directorates."""
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:api_directorates"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 17)
        identifiers = [d["identifier"] for d in data]
        self.assertIn("DIR-PROG-PROJ", identifiers)
        self.assertIn("DIR-MEAL", identifiers)
        self.assertIn("DIR-FIN-RES", identifiers)

    def test_departments_endpoint_filtered(self):
        """Departments endpoint filters by directorate_id."""
        self.client.force_login(self.user)
        url = f"{reverse('organizations:api_departments')}?directorate_id={self.dir_meal.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        identifiers = [d["identifier"] for d in data]
        self.assertIn("DEPT-MEAL", identifiers)
        self.assertNotIn("DEPT-FGRM", identifiers)

    def test_program_technical_endpoint_filtered(self):
        """Program & Technical Management endpoint filters by department_id."""
        self.client.force_login(self.user)
        url = f"{reverse('organizations:api_program_technical')}?department_id={self.dept_meal.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        identifiers = [d["identifier"] for d in data]
        self.assertIn("PTM-MEO", identifiers)
        self.assertNotIn("PTM-FM", identifiers)
