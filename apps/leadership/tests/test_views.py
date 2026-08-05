"""View and permission tests for the Leadership Management module."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse

from apps.leadership.constants import LeadershipLevel, LeadershipStatus
from apps.leadership.models import LeadershipProfile

User = get_user_model()


class LeadershipViewAccessTest(TestCase):
    """Test that leadership views enforce authentication."""

    def setUp(self):
        self.client = Client()

    def test_dashboard_requires_login(self):
        """Dashboard redirects unauthenticated users."""
        url = reverse("leadership:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_directory_requires_login(self):
        """Directory redirects unauthenticated users."""
        url = reverse("leadership:directory")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_appointment_list_requires_login(self):
        """Appointment list redirects unauthenticated."""
        url = reverse("leadership:appointment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)


class LeadershipViewPermissionTest(TestCase):
    """Test that leadership views enforce permissions."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="viewer@sitadc.org",
            password="TestPass123!",
        )
        self.client.login(
            email="viewer@sitadc.org",
            password="TestPass123!",
        )

    def test_dashboard_requires_permission(self):
        """Dashboard returns 403 without permission."""
        url = reverse("leadership:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_dashboard_accessible_with_permission(self):
        """Dashboard returns 200 with view permission."""
        perm = Permission.objects.get(
            codename="leadership.view",
        )
        self.user.user_permissions.add(perm)
        url = reverse("leadership:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_directory_accessible_with_permission(self):
        """Directory returns 200 with view permission."""
        perm = Permission.objects.get(
            codename="leadership.view",
        )
        self.user.user_permissions.add(perm)
        url = reverse("leadership:directory")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_profile_requires_add_permission(self):
        """Profile creation requires add permission."""
        url = reverse("leadership:profile_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_create_profile_accessible_with_permission(self):
        """Profile creation returns 200 with add perm."""
        perm = Permission.objects.get(
            codename="leadership.create",
        )
        self.user.user_permissions.add(perm)
        url = reverse("leadership:profile_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class LeadershipDirectoryTest(TestCase):
    """Test the leadership directory view content."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="admin@sitadc.org",
            password="TestPass123!",
        )
        perm = Permission.objects.get(
            codename="leadership.view",
        )
        self.user.user_permissions.add(perm)
        self.client.login(
            email="admin@sitadc.org",
            password="TestPass123!",
        )

    def test_directory_shows_active_profiles(self):
        """Directory displays only active profiles."""
        leader_user = User.objects.create_user(
            email="active@sitadc.org",
            password="TestPass123!",
            first_name="Active",
            last_name="Leader",
        )
        LeadershipProfile.objects.create(
            user=leader_user,
            reference_number="SITADC-LDR-2026-00100",
            leadership_level=LeadershipLevel.DIRECTORATE,
            status=LeadershipStatus.ACTIVE,
        )
        archived_user = User.objects.create_user(
            email="archived@sitadc.org",
            password="TestPass123!",
            first_name="Archived",
            last_name="Leader",
        )
        LeadershipProfile.objects.create(
            user=archived_user,
            reference_number="SITADC-LDR-2026-00101",
            leadership_level=LeadershipLevel.TEAM,
            status=LeadershipStatus.ARCHIVED,
        )
        url = reverse("leadership:directory")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        profiles = response.context["profiles"]
        self.assertEqual(profiles.count(), 1)


class LeadershipURLTest(TestCase):
    """Test that leadership URL patterns resolve."""

    def test_dashboard_url(self):
        url = reverse("leadership:dashboard")
        self.assertEqual(url, "/leadership/dashboard/")

    def test_directory_url(self):
        url = reverse("leadership:directory")
        self.assertEqual(url, "/leadership/directory/")

    def test_appointment_list_url(self):
        url = reverse("leadership:appointment_list")
        self.assertEqual(url, "/leadership/appointments/")

    def test_review_list_url(self):
        url = reverse("leadership:review_list")
        self.assertEqual(url, "/leadership/reviews/")

    def test_attendance_list_url(self):
        url = reverse("leadership:attendance_list")
        self.assertEqual(url, "/leadership/attendance/")

    def test_coaching_list_url(self):
        url = reverse("leadership:coaching_list")
        self.assertEqual(url, "/leadership/coaching/")

    def test_mentorship_list_url(self):
        url = reverse("leadership:mentorship_list")
        self.assertEqual(url, "/leadership/mentorship/")

    def test_succession_list_url(self):
        url = reverse("leadership:succession_list")
        self.assertEqual(url, "/leadership/succession/")
