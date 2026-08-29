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
            leadership_level=LeadershipLevel.TEAM_LEADER,
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

    def test_all_leaders_url(self):
        url = reverse("leadership:all_leaders")
        self.assertEqual(url, "/leadership/leaders/")

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


class AllLeadersAccessTest(TestCase):
    """Access control for the All Leaders & Staff page."""

    def setUp(self):
        self.client = Client()
        self.url = reverse("leadership:all_leaders")

    def test_requires_login(self):
        """All Leaders redirects unauthenticated users to login."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_forbidden_without_permission(self):
        """All Leaders returns 403 for authenticated users without view."""
        user = User.objects.create_user(
            email="noperm@sitadc.org",
            password="TestPass123!",
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_accessible_with_permission(self):
        """All Leaders returns 200 with the leadership view permission."""
        user = User.objects.create_user(
            email="permitted@sitadc.org",
            password="TestPass123!",
        )
        user.user_permissions.add(
            Permission.objects.get(codename="leadership.view")
        )
        self.client.force_login(user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "All Leaders")

    def test_directory_and_all_leaders_share_view(self):
        """/leadership/directory/ and /leadership/leaders/ both resolve."""
        user = User.objects.create_user(
            email="both@sitadc.org",
            password="TestPass123!",
        )
        user.user_permissions.add(
            Permission.objects.get(codename="leadership.view")
        )
        self.client.force_login(user)
        self.assertEqual(
            self.client.get(reverse("leadership:directory")).status_code,
            200,
        )
        self.assertEqual(self.client.get(self.url).status_code, 200)


class LeadershipDashboardCardTest(TestCase):
    """The View Leaders dashboard card and its statistics."""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email="cardviewer@sitadc.org",
            password="TestPass123!",
        )
        self.user.user_permissions.add(
            Permission.objects.get(codename="leadership.view")
        )
        self.client.force_login(self.user)
        self._sequence = 0

    def _create_profile(self, first_name, last_name, level, status):
        self._sequence += 1
        person = User.objects.create_user(
            email=f"person{self._sequence}@sitadc.org",
            password="TestPass123!",
            first_name=first_name,
            last_name=last_name,
        )
        return LeadershipProfile.objects.create(
            user=person,
            reference_number=f"LDR-SITADC-2026-{self._sequence:06d}",
            leadership_level=level,
            status=status,
        )

    def test_card_statistics_use_database_counts(self):
        """Card totals reflect real Leader/Staff counts from the database."""
        self._create_profile(
            "Board", "One", LeadershipLevel.BOARD_OF_TRUSTEES,
            LeadershipStatus.ACTIVE,
        )
        self._create_profile(
            "Dir", "One", LeadershipLevel.DIRECTORATE, LeadershipStatus.ACTING,
        )
        self._create_profile(
            "Staff", "One", LeadershipLevel.TEAM_LEADER, LeadershipStatus.ACTIVE,
        )
        # Archived personnel must not inflate the card statistics.
        self._create_profile(
            "Gone", "Away", LeadershipLevel.TEAM_LEADER,
            LeadershipStatus.ARCHIVED,
        )

        response = self.client.get(reverse("leadership:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_leaders_count"], 2)
        self.assertEqual(response.context["total_staff_count"], 1)
        self.assertEqual(response.context["total_active_personnel"], 3)

    def test_card_links_to_all_leaders(self):
        """Dashboard renders a link to the All Leaders & Staff page."""
        response = self.client.get(reverse("leadership:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("leadership:all_leaders"))
        self.assertContains(response, "View All Leaders")


class AllLeadersDirectoryContentTest(TestCase):
    """Content behaviour of the All Leaders & Staff directory."""

    def setUp(self):
        self.client = Client()
        self.viewer = User.objects.create_user(
            email="directory@sitadc.org",
            password="TestPass123!",
        )
        self.viewer.user_permissions.add(
            Permission.objects.get(codename="leadership.view")
        )
        self.client.force_login(self.viewer)
        self.leader = self._create_person(
            "bigleader@sitadc.org", "Thandiwe", "Banda",
            LeadershipLevel.DIRECTORATE, LeadershipStatus.ACTIVE,
        )
        self.staff = self._create_person(
            "regularstaff@sitadc.org", "Kondwani", "Phiri",
            LeadershipLevel.TEAM_LEADER, LeadershipStatus.ACTIVE,
        )

    def _create_person(self, email, first_name, last_name, level, status):
        person = User.objects.create_user(
            email=email,
            password="TestPass123!",
            first_name=first_name,
            last_name=last_name,
        )
        return LeadershipProfile.objects.create(
            user=person,
            reference_number=f"LDR-SITADC-2026-{abs(hash(email)) % 900000 + 100000}",
            leadership_level=level,
            status=status,
        )

    def test_leaders_and_staff_both_listed(self):
        """Both leader-level and staff-level personnel are displayed."""
        response = self.client.get(reverse("leadership:all_leaders"))
        self.assertContains(response, "Thandiwe Banda")
        self.assertContains(response, "Kondwani Phiri")

    def test_search_filters_by_name(self):
        """Database-side search narrows results by name."""
        response = self.client.get(
            reverse("leadership:all_leaders"), {"search": "Kondwani"}
        )
        profiles = list(response.context["profiles"])
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].pk, self.staff.pk)

    def test_explicit_status_filter_overrides_default(self):
        """Requesting a non-default status returns those records."""
        self._create_person(
            "suspended@sitadc.org", "Sue", "Spended",
            LeadershipLevel.TEAM_LEADER, LeadershipStatus.SUSPENDED,
        )
        response = self.client.get(
            reverse("leadership:all_leaders"), {"status": "SUSPENDED"}
        )
        profiles = list(response.context["profiles"])
        self.assertEqual(len(profiles), 1)
        self.assertEqual(profiles[0].user.email, "suspended@sitadc.org")

    def test_archived_hidden_by_default(self):
        """Archived personnel do not appear unless explicitly requested."""
        archived = self._create_person(
            "archived2@sitadc.org", "Ar", "Chived",
            LeadershipLevel.TEAM_LEADER, LeadershipStatus.ARCHIVED,
        )
        default_response = self.client.get(reverse("leadership:all_leaders"))
        self.assertNotContains(default_response, "Chived")

        filtered = self.client.get(
            reverse("leadership:all_leaders"), {"status": "ARCHIVED"}
        )
        self.assertContains(filtered, "Chived")

    def test_empty_state_when_no_match(self):
        """A non-matching search renders the professional empty state."""
        response = self.client.get(
            reverse("leadership:all_leaders"), {"search": "zzznotfoundzzz"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No leaders found")

    def test_pagination_preserves_filters(self):
        """Pagination uses 20 per page and filters persist across requests."""
        response = self.client.get(
            reverse("leadership:all_leaders"),
            {"search": "Kondwani", "page": "1"},
        )
        paginator = response.context["paginator"]
        self.assertEqual(paginator.per_page, 20)
        self.assertIn('value="Kondwani"', response.content.decode())

    def test_sorting_descending_last_name(self):
        """Whitelisted sort fields order results correctly."""
        response = self.client.get(
            reverse("leadership:all_leaders"), {"sort": "-user__last_name"}
        )
        self.assertEqual(
            list(response.context["profiles"]), [self.staff, self.leader]
        )

    def test_invalid_sort_falls_back_to_default(self):
        """Unrecognized sort values are ignored, not injected."""
        response = self.client.get(
            reverse("leadership:all_leaders"), {"sort": "password; DROP"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["profiles"])[0].pk, self.leader.pk)

    def test_summary_statistics_in_context(self):
        """Summary cards receive database-derived counts."""
        response = self.client.get(reverse("leadership:all_leaders"))
        self.assertEqual(response.context["total_personnel"], 2)
        self.assertEqual(response.context["active_leaders"], 2)
        self.assertEqual(response.context["leaders_count"], 1)
        self.assertEqual(response.context["staff_count"], 1)

    def test_profile_link_targets_detail_page(self):
        """Each card links to the existing profile detail view."""
        response = self.client.get(reverse("leadership:all_leaders"))
        detail_path = reverse(
            "leadership:profile_detail", kwargs={"pk": self.leader.pk}
        )
        self.assertContains(response, detail_path)
