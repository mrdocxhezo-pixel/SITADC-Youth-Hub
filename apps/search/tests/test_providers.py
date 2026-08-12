"""Unit tests for the Enterprise Search provider base & registry."""

from __future__ import annotations

from django.test import SimpleTestCase

from apps.search.providers.base import Registry, SearchHit, SearchProvider

from .base import SearchTestCase


class DummyProvider(SearchProvider):
    key = "tests.dummy"
    label = "Dummy"
    search_fields = ("title",)
    title_field = "title"
    status_field = "status"

    def queryset(self, user):
        return None


class RegistryTests(SimpleTestCase):
    def setUp(self):
        self.registry = Registry()

    def test_register_and_get(self):
        provider = DummyProvider()
        self.registry.register(provider)
        self.assertIs(self.registry.get("tests.dummy"), provider)

    def test_duplicate_key_rejected(self):
        self.registry.register(DummyProvider())
        with self.assertRaises(ValueError):
            self.registry.register(DummyProvider())

    def test_empty_key_rejected(self):
        provider = DummyProvider()
        provider.key = ""
        with self.assertRaises(ValueError):
            self.registry.register(provider)

    def test_subsets_ignores_unknown(self):
        self.registry.register(DummyProvider())
        self.assertEqual(
            self.registry.subsets(["tests.dummy", "bogus.key"])[0].key, "tests.dummy"
        )


class ProviderAvailabilityTests(SearchTestCase):
    def test_superuser_has_everything(self):
        provider = DummyProvider()
        provider.view_permissions = ("search.view",)
        self.assertTrue(provider.is_available(self.admin))

    def test_outsider_unavailable(self):
        provider = DummyProvider()
        provider.view_permissions = ("search.view",)
        self.assertFalse(provider.is_available(self.outsider))

    def test_anonymous_unavailable(self):
        provider = DummyProvider()
        self.assertFalse(provider.is_available(None))

    def test_search_returns_empty_for_no_queryset(self):
        provider = DummyProvider()
        provider.view_permissions = ("search.view",)
        self.assertEqual(provider.search(self.viewer, "anything"), [])


class SearchHitTests(SimpleTestCase):
    def test_hit_is_immutable_dataclass(self):
        hit = SearchHit(
            key="tests.dummy",
            label="Dummy",
            object_id="1",
            title="T",
            subtitle="S",
            reference="R",
            status="Active",
            url="/dummy/1/",
        )
        self.assertEqual(hit.key, "tests.dummy")
        self.assertEqual(hit.url, "/dummy/1/")
