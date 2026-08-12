# Phase 26 — Global Search: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-11

**Status:** Implemented (pending acceptance)

## Phase Summary

Phase 26 implements the Global Search module in a new `apps/search` app, per
`roadmaps/26-Global-Search.md`. The module provides a single, permission-scaled
search surface across the entire organization: a universal search home page
with grouped results, entity-type refinements, per-type result limits, recent
search history, named saved searches with run/delete, a CSV export endpoint,
and an immutable audit trail of every executed query. Search is delivered
through a pluggable provider registry — each searchable entity type is indexed
by exactly one provider that delegates permission scoping to the source
module's fail-closed selectors, so confidentiality rules are always preserved.
The module is wired into the RBAC framework (fresh installs and existing
databases via a seed migration) and the dashboard sidebar.

## Architecture

- New Django app `apps/search` with **3 concrete models**: `RecentSearch`
  (per-user, deduplicated search history with a unique `(user, query)`
  constraint and prune cap), `SavedSearch` (named reusable searches with a
  unique `(user, name)` constraint), and `SearchQueryLog` (immutable,
  append-only audit row recording user, query, entity types, result count,
  duration, and IP). All models extend `UUIDModel` + `TimeStampedModel`.
- **Provider registry** (`providers/base.py`): `SearchHit` (frozen dataclass),
  `SearchProvider` (ABC) and a `Registry` singleton. A provider declares the
  fields searched, fields displayed, canonical deep-link and its permission
  gates; `queryset()` is abstract and must be fail-closed. 22 concrete
  providers register at import time covering beneficiaries, documents,
  leadership, MEAL, meetings & calendar events, memberships, notifications,
  programmes & projects, registers & register entries, report templates, report
  instances, reviews, stakeholders & partners, and volunteers.
- **Service layer** (`services.py`): `run_search` (permission gate → query
  validation → entity-type scoping → provider fan-out → optional history/audit
  persistence with timing), `record_search` (recent-search dedup + prune +
  append-only audit), `create_saved_search`, `delete_saved_search`,
  `run_saved_search`, and `exportable_search`.
- **Selectors** (`selectors.py`): fail-closed read layer — available entity
  types/choices, recent/saved searches for an actor, the audit log (managers
  only), and `user_can_access_search`.
- **Permissions** (`permissions.py`): three codes — `search.view` (page),
  `search.export` (CSV export), `search.manage` (audit log) — plus helpers
  (`user_can_search/export/manage`) built on `user_has_permission`.
- **Views/URLs**: 7 permission-checked views in the `search` namespace
  (`/search/`): home (search + refinements + recent/saved), export (CSV),
  saved list, saved create, saved delete, saved run (deep link), and audit.
- **CSV export** (`exports.py`): only the actor's accessible hits are exported
  (results flow through the permission-scaled providers); UTF-8 BOM for Excel,
  sanitized cell text, download disposition.
- **RBAC**: `search` permission category (3 codes) added to
  `apps/rbac/seed_data.py` and seeded for existing databases by
  `apps/rbac/migrations/0018_seed_search_permissions.py` (`atomic=False`),
  granting `view`/`export` to staff/management roles and
  `view`/`export`/`manage` to the two administrator roles.
- **Front-end**: Bootstrap 5 search page with client-side entity-type
  filtering (`static/search/js/search.js`) and consistent hit cards
  (`static/search/css/search.css`); sidebar navigation entry gated on
  `search.view` / `search.manage`.

## Files Created

- `apps/search/` — full module: `models.py`, `services.py`, `selectors.py`,
  `views.py`, `forms.py`, `permissions.py`, `validators.py`, `constants.py`,
  `exceptions.py`, `exports.py`, `urls.py`, `admin.py`, `apps.py`,
  `migrations/0001_initial.py`.
- `apps/search/providers/` — `base.py` (registry + contract) and 22 entity
  providers (beneficiaries, documents, leadership, meal, meetings, memberships,
  notifications, programs, registers, report_instances, reports, reviews,
  stakeholders, volunteers).
- `apps/search/templates/search/` — `search.html`, `saved_search_list.html`,
  `audit_log.html`.
- `apps/search/static/search/` — `css/search.css`, `js/search.js`.
- `apps/search/tests/` — `base.py` plus 5 test modules (`test_permissions.py`,
  `test_validators.py`, `test_providers.py`, `test_services.py`,
  `test_views.py`).
- `apps/rbac/migrations/0018_seed_search_permissions.py` — RBAC seed migration
  for existing databases.
- `docs/development/PHASE26_GLOBAL_SEARCH_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — `search` permission category and role grants.
- `config/urls.py` — `search/` path with `search` namespace.
- `templates/components/sidebar.html` — Search navigation item gated on
  `search.view` / `search.manage`.
- `pyproject.toml` — per-file RUF012 ignore for `apps/search/models.py`
  (Django declarative constraints/indexes).
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 26 entries.

## Features Implemented

- **Universal search**: one search surface querying all authorized modules
  simultaneously, with results grouped by entity type and direct links to the
  source records.
- **Filtered search**: entity-type refinements (checkboxes) scoped to the
  permissions of the requesting actor.
- **Search history**: per-user recent searches, deduplicated by query,
  persisted and pruned to a configured cap.
- **Saved searches**: name-and-save a query (with entity types), list, run
  (reconstructed deep link), and delete (owner-only).
- **Search audit**: immutable `SearchQueryLog` recording who searched, what,
  which entity types, result count, duration, and IP; readable only by
  `search.manage` holders; admin exposure is read-only.
- **CSV export**: authorized users (`search.export`) can download current
  results with the search parameters preserved in the URL.
- **Fail-closed scoping**: providers delegate visibility to source-module
  selectors; anonymous/unauthorized actors never discover results.

## Performance Review

- Searches run against the source module querysets directly (no separate
  materialized index) so latency tracks the existing, indexed ORM queries.
- Per-type result caps (default 5, max 25) bound result volume and rendering
  cost; `distinct()` and `select_related` are used by providers.
- `SearchQueryLog` and `RecentSearch` are indexed on `(user, query)` and
  `(-created_at, user)` respectively; audit lookups are limited to the 100
  most recent rows.
- Recent-search pruning runs once per new search rather than per row.

## Accessibility Review

- Search controls carry `aria-label` / `aria-current="page"`; result groups use
  semantic headings; tables expose `<caption>`; hit links are keyboard
  reachable; entity-type checkboxes remain labelled and focusable.
- Dashboard layout, sidebar and card spacing follow the shared
  `layouts/dashboard.html` base, preserving the existing light/dark theme
  behaviour and responsive breakpoints.

## Testing Results

- **Unit tests**: validators (query normalization/length/symbols, entity-key
  coercion), provider base/registry (registration, duplicates, availability,
  empty queryset), permissions helpers, and service layer (search execution,
  history/audit persistence, saved-search lifecycle, ownership).
- **View tests**: authentication/authorization fail-closed, saved search
  create/list/delete/run, export gating, audit gating, and export query-string
  serialization.
- **Result**: 59 tests in `apps/search/tests/` — all green in the 2026-08-11
  verification run.
- **Outstanding issues**: none in the search suite.

## Commands Executed

- `python manage.py makemigrations search`
- `python manage.py migrate`
- `python manage.py check`
- `python -m pytest apps/search` (59 passed)
- `python -m ruff check apps/search`
- `python -m black --check apps/search`
- `python -m isort --check-only apps/search`

## Documentation Updated

- `docs/development/PHASE26_GLOBAL_SEARCH_REPORT.md` (this file).
- `DEVELOPMENT_STATUS.md` — Phase 26 status section and module status row.
- `CHANGELOG.md` — Phase 26 entry.

## Problems Encountered

1. The `SearchQueryLog.save()` immutability guard used `if self.pk:` to block
   updates, but `UUIDModel` pre-assigns the primary key, so the guard also
   rejected legitimate inserts — the audit trail could not be written.
2. The initial `apps/search/providers/report_instances.py` rewrite lost its
   `from .base import` line, producing a `NameError` at import time.
3. The first `pytest` run appeared to hang; in fact the test database had never
   been created and applying the full migration set took several minutes, which
   exceeded the command timeout.

## Problems Resolved

1. The immutability guard now checks `self._state.adding` so inserts are
   allowed and updates/deletes are rejected (fix surfaced by the new test
   suite). (1) was corrected, verified by the audit test cases.
2. Restored the missing import in `report_instances.py`; `manage.py check` and
   all tests confirm clean imports.
3. Built the test database once with Django's own runner (`manage.py test
   --keepdb`) and verified the suite end to end; subsequent runs reuse it.

## Known Limitations

- Search executes live ORM queries rather than a materialized full-text index;
  future parts of Phase 26 may introduce an index layer.
- Advanced search (filters, facets, highlighting, sorting) and bookmarks are
  deferred to later parts of the Phase 26 roadmap.
- Export is CSV-only for now (PDF/DOCX/XLSX deferred).
- The sidebar dashboard link and global search bar on other pages are not yet
  integrated with the module.

## Phase Status

```text
Phase 26 (Part 2 scope delivered): Implemented — universal search, filtered
search, history, saved searches, audit, and CSV export
Phase 26 (full roadmap): Incomplete — advanced search, suggestions,
bookmarks, analytics, full-text indexing remain for later parts
Phase 27: Ready
```
