"""Service-level tests for the Enterprise Search module."""

from __future__ import annotations

from unittest.mock import patch

from django.core.exceptions import ValidationError

from apps.search import services as search_services
from apps.search.exceptions import SearchPermissionDenied, SearchValidationError
from apps.search.models import RecentSearch, SavedSearch, SearchQueryLog
from apps.search.providers.base import SearchHit, SearchProvider
from apps.search.services import (
    create_saved_search,
    delete_saved_search,
    record_search,
    run_search,
)

from .base import SearchTestCase


class StubProvider(SearchProvider):
    """A minimal registry-compatible provider used to stub searches."""

    key = "programs.program"
    label = "Stub"
    search_fields = ("title",)

    def __init__(self, hits: list[SearchHit] | None = None):
        super().__init__()
        self._hits = hits or []

    def is_available(self, user) -> bool:
        return True

    def queryset(self, user):
        return None

    def search(self, user, query: str, *, limit: int = 5) -> list[SearchHit]:
        return self._hits[:limit]


def make_hit(title: str = "Water Project") -> SearchHit:
    return SearchHit(
        key="programs.program",
        label="Stub",
        object_id="1",
        title=title,
        subtitle="Sub",
        reference="REF-001",
        status="Active",
        url="/stub/1/",
    )


class RunSearchTests(SearchTestCase):
    @patch.object(search_services.registry, "subsets")
    @patch.object(search_services.registry, "available")
    def test_run_search_returns_grouped_results(self, available, subsets):
        provider = StubProvider(hits=[make_hit()])
        available.return_value = [provider]
        subsets.return_value = [provider]

        results = run_search(self.viewer, "water", entity_types=["programs.program"])

        self.assertTrue(results.executed)
        self.assertEqual(results.total, 1)
        self.assertEqual(len(results.groups), 1)
        self.assertEqual(results.groups[0].key, "programs.program")
        self.assertEqual(results.groups[0].hits[0].title, "Water Project")

    def test_unauthorized_user_raises(self):
        with self.assertRaises(SearchPermissionDenied):
            run_search(self.outsider, "water")

    def test_invalid_query_raises(self):
        with self.assertRaises(SearchValidationError):
            run_search(self.viewer, "")

    @patch.object(search_services.registry, "subsets")
    @patch.object(search_services.registry, "available")
    def test_persist_false_writes_no_log(self, available, subsets):
        provider = StubProvider(hits=[make_hit()])
        available.return_value = [provider]
        subsets.return_value = [provider]

        run_search(
            self.viewer,
            "water",
            entity_types=["programs.program"],
            persist=False,
            ip_address="127.0.0.1",
        )

        self.assertEqual(SearchQueryLog.objects.count(), 0)
        self.assertEqual(RecentSearch.objects.count(), 0)

    @patch.object(search_services.registry, "subsets")
    @patch.object(search_services.registry, "available")
    def test_persist_true_writes_audit_row(self, available, subsets):
        provider = StubProvider(hits=[make_hit()])
        available.return_value = [provider]
        subsets.return_value = [provider]

        run_search(self.viewer, "water", entity_types=["programs.program"])

        log = SearchQueryLog.objects.get()
        self.assertEqual(log.user, self.viewer)
        self.assertEqual(log.query, "water")
        self.assertEqual(log.result_count, 1)


class RecordSearchTests(SearchTestCase):
    def test_records_recent_and_audit(self):
        record_search(
            self.viewer, "water", ["programs.program"], 3, ip_address="127.0.0.1"
        )
        self.assertEqual(RecentSearch.objects.filter(user=self.viewer).count(), 1)
        self.assertEqual(SearchQueryLog.objects.count(), 1)

    def test_same_query_deduplicates_recent(self):
        record_search(self.viewer, "water", ["programs.program"], 2)
        record_search(self.viewer, "water", ["documents.document"], 1)
        self.assertEqual(RecentSearch.objects.filter(user=self.viewer).count(), 1)
        recent = RecentSearch.objects.get(user=self.viewer)
        self.assertIn("documents.document", recent.entity_types)
        self.assertEqual(SearchQueryLog.objects.count(), 2)

    def test_audit_is_append_only(self):
        record_search(self.viewer, "water", ["programs.program"], 1)
        log = SearchQueryLog.objects.get()
        with self.assertRaises(ValidationError):
            log.save()

    def test_anonymous_not_recorded(self):
        record_search(None, "water", ["programs.program"], 1)
        self.assertEqual(SearchQueryLog.objects.count(), 0)


class SavedSearchTests(SearchTestCase):
    def test_create_saved_search(self):
        saved = create_saved_search(self.viewer, "Water", "water project")
        self.assertEqual(saved.name, "Water")
        self.assertEqual(saved.query, "water project")
        self.assertEqual(saved.user, self.viewer)

    def test_upsert_by_name(self):
        create_saved_search(self.viewer, "Water", "water")
        saved = create_saved_search(self.viewer, "Water", "water project")
        self.assertEqual(SavedSearch.objects.filter(user=self.viewer).count(), 1)
        self.assertEqual(saved.query, "water project")

    def test_requires_permission(self):
        with self.assertRaises(SearchPermissionDenied):
            create_saved_search(self.outsider, "Water", "water project")

    def test_blank_name_rejected(self):
        with self.assertRaises(SearchValidationError):
            create_saved_search(self.viewer, "   ", "water project")

    def test_unknown_entity_types_rejected(self):
        with self.assertRaises(SearchValidationError):
            create_saved_search(
                self.viewer, "Water", "water", entity_types=["bogus.key"]
            )

    def test_delete_own_only(self):
        saved = create_saved_search(self.viewer, "Water", "water")
        delete_saved_search(self.viewer, saved)
        self.assertEqual(SavedSearch.objects.count(), 0)

    def test_delete_foreign_raises(self):
        saved = create_saved_search(self.viewer, "Water", "water")
        with self.assertRaises(SearchPermissionDenied):
            delete_saved_search(self.manager, saved)
