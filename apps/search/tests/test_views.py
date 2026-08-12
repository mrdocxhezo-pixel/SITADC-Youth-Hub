"""View-level tests for the Enterprise Search module."""

from __future__ import annotations

from django.urls import reverse

from apps.search.models import SavedSearch
from apps.search.tests.base import SearchTestCase


class SearchHomeViewTests(SearchTestCase):
    def test_anonymous_denied(self):
        response = self.client.get(reverse("search:home"))
        self.assertEqual(response.status_code, 403)

    def test_outsider_denied(self):
        self.login_as(self.outsider)
        response = self.client.get(reverse("search:home"))
        self.assertEqual(response.status_code, 403)

    def test_viewer_can_open(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("search:home"))
        self.assertEqual(response.status_code, 200)

    def test_short_query_no_crash(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("search:home"), {"q": "x"})
        self.assertEqual(response.status_code, 200)


class SearchAuditViewTests(SearchTestCase):
    def test_requires_manage_permission(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("search:audit"))
        self.assertEqual(response.status_code, 403)

    def test_manager_can_open(self):
        self.login_as(self.admin)
        response = self.client.get(reverse("search:audit"))
        self.assertEqual(response.status_code, 200)


class SavedSearchViewTests(SearchTestCase):
    def setUp(self):
        super().setUp()
        self.saved = SavedSearch.objects.create(
            user=self.viewer, name="Water", query="water project"
        )

    def test_create_saved_search(self):
        self.login_as(self.viewer)
        response = self.client.post(
            reverse("search:saved_create"),
            {"name": "Health", "query": "health clinic", "types": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            SavedSearch.objects.filter(user=self.viewer, name="Health").exists()
        )

    def test_list_own_saved_searches(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("search:saved_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Water")

    def test_delete_own_saved_search(self):
        self.login_as(self.viewer)
        response = self.client.post(
            reverse("search:saved_delete", args=[self.saved.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavedSearch.objects.filter(pk=self.saved.pk).exists())

    def test_delete_others_denied(self):
        self.login_as(self.manager)
        response = self.client.post(
            reverse("search:saved_delete", args=[self.saved.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavedSearch.objects.filter(pk=self.saved.pk).exists())

    def test_run_own_saved_search(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("search:saved_run", args=[self.saved.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn("q=water+project", response.url)

    def test_run_others_denied(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("search:saved_run", args=[self.saved.pk]))
        self.assertEqual(response.status_code, 403)


class ExportSearchViewTests(SearchTestCase):
    def test_export_requires_export_permission(self):
        self.login_as(self.viewer)
        response = self.client.get(reverse("search:export"), {"q": "water"})
        self.assertEqual(response.status_code, 403)

    def test_manager_can_export(self):
        self.login_as(self.manager)
        response = self.client.get(reverse("search:export"), {"q": "water"})
        self.assertEqual(response.status_code, 200)


class BuildExportQueryStringTests(SearchTestCase):
    def test_builds_query_string_with_types(self):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get(
            "/search/?q=water&types=programs.program&types=documents.document"
        )
        from apps.search.views import build_export_query_string

        qs = build_export_query_string(request)
        self.assertIn("q=water", qs)
        self.assertEqual(qs.count("types="), 2)
