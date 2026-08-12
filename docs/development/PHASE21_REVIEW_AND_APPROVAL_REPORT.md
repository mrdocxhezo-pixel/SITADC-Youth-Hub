# Phase 21 — Review & Approval: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-08

**Status:** Implemented (pending acceptance)

## Summary

Phase 21 (Part 1 of 4) implements the Review and Approval module in a new
`apps/reviews` app, per `roadmaps/21-Review-and-Approval.md` and building on the
Phase 20 Report Management submission workflow. The module provides a
structured, auditable workflow for reviewing, validating, commenting on,
approving, rejecting, returning, escalating, and digitally signing submitted
reports, together with reviewer assignment, delegation, and SLA tracking. The
module is wired into the RBAC framework (fresh installs and existing
databases), and a 99-test suite covers models, services, selectors,
permissions, and views. The full repository suite is green at 1134 passed.

## Architecture

- New Django app `apps/reviews` with 13 concrete models on an immutable
  `ReviewRecord` base (`UUIDModel`, `TimeStampedModel`, `CreatedByModel`,
  `UpdatedByModel`, `SoftDeleteModel`): `Review`, `ReviewAssignment`,
  `ReviewChecklist`, `ReviewChecklistItem`, `ReviewChecklistResponse`,
  `ReviewComment`, `ReviewDecision`, `DigitalSignature`, `EscalationRecord`,
  `DelegationRecord`, `SLAConfiguration`, `SLAEvent`, `ReviewConfiguration`,
  plus the `ReviewStatus`, `ReviewDecisionType`, `ReviewerRole`, `CommentType`,
  and `EscalationTrigger` enums.
- RBAC integration: the `reviews` category (19 actions: `view`, `create`,
  `assign`, `accept`, `start`, `comment`, `resolve_comment`,
  `update_checklist`, `decide`, `approve`, `reject`, `return_for_correction`,
  `escalate`, `delegate`, `sign`, `manage_checklists`, `manage_sla`,
  `manage_configuration`, `manage`) was added to `PERMISSION_CATEGORIES` and
  `ALL_PERMISSION_CODES` in `apps/rbac/seed_data.py`, together with named role
  groups `REVIEW_OPERATIONAL` / `REVIEW_REVIEWER` wired into the officer and
  coordinator/manager bases.
- Existing databases are brought in line by a dedicated seed migration
  (`rbac.0015`, `atomic=False`) that creates the category, the 19 `Permission`
  rows, and role grants: leadership = all actions, coordinators/managers =
  reviewer set, officers = operational set, board = read-only view actions.
  Both `role.permissions` and `role.group.permissions` are synchronized.
- Service layer (`apps/reviews/services.py`) covers review creation with
  auto-populated checklist responses, assignment/acceptance, delegation,
  escalation, commenting and comment resolution, decisions (approve/reject/
  return-for-correction) with review-number sequencing, SLA event tracking,
  and digital-signature capture.
- Views and URLs expose a dashboard (pending/overdue/inbox), review list,
  review detail, assign, delegate, escalate, and decision routes. All views
  authorize server-side with `check_permission` using the literal `reviews.*`
  codes; templates are Bootstrap 5 with a sidebar link to the Reviews section.
- Critical dependency fixes surfaced by the test suite:
  - `apps/accounts/models.py`: the custom `User` gained `get_full_name()`
    (only a `full_name` property existed; templates and the delegation service
    call `get_full_name()`).
  - `apps/reviews/views.py`: user resolution now uses `get_user_model()`
    instead of `from accounts.models import User`, which raised
    `ModuleNotFoundError` and was swallowed by the generic exception handler,
    silently aborting assignment/delegation/escalation.
  - `apps/reviews/services.py`: checklist responses populate from all items
    (removed a non-existent `is_active` filter) and review numbers increment
    correctly across reviews.
  - `apps/reviews/permissions.py`: added the `MANAGE = "reviews.manage"`
    constant used by templates and authorization checks.

## Files Created

- `apps/reviews/` — full module: `models.py`, `services.py`, `selectors.py`,
  `views.py`, `forms.py`, `permissions.py`, `urls.py`, `admin.py`, `apps.py`,
  `migrations/0001_initial.py`.
- `apps/reviews/templates/reviews/` — `dashboard.html`, `review_list.html`,
  `review_detail.html`, `sla_dashboard.html`.
- `apps/reviews/tests/` — shared scaffold (`base.py`) plus 5 test modules:
  `test_models.py`, `test_services.py`, `test_selectors.py`,
  `test_permissions.py`, `test_views.py`.
- `apps/rbac/migrations/0015_seed_review_permissions.py` — seed migration for
  the `reviews` category, permissions, and role grants on existing databases.
- `docs/development/PHASE21_REVIEW_AND_APPROVAL_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — added the `reviews` category to
  `PERMISSION_CATEGORIES` and `ALL_PERMISSION_CODES`, plus the
  `REVIEW_OPERATIONAL` / `REVIEW_REVIEWER` role groups wired into the officer
  and coordinator/manager bases.
- `apps/accounts/models.py` — added `get_full_name()` to the custom `User`.
- `apps/reviews/views.py` — `get_user_model()` lookups (assign/escalate/
  delegate), dashboard pending-review wiring, `MANAGE` permission checks.
- `apps/reviews/permissions.py` — added `MANAGE = "reviews.manage"`.
- `apps/reviews/services.py` — checklist item population and review-number
  fixes; black/E501 formatting.
- `apps/reviews/models.py`, `apps/reviews/admin.py`, `apps/reviews/forms.py`,
  `apps/reviews/selectors.py` — lint/format cleanups (RUF012 noqa comments,
  unused imports, import ordering).
- `templates/components/sidebar.html` — Reviews navigation item.
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 21 entries.

## Database Changes

- `reviews.0001` — initial schema for the 13 models (no data migration).
- `rbac.0015` — new seed migration (category, 19 permissions, role grants),
  reversible. No model schema changes outside the new app;
  `makemigrations --check --dry-run` is clean.

## Security Considerations

- Server-side authorization only: every view uses `check_permission` with the
  literal `reviews.*` codes; the UI never relies on hidden buttons.
- The permission catalogue gate (`ALL_PERMISSION_CODES`) is aware of the review
  codes, so previously-denied non-superusers gain exactly the granted actions
  and nothing more.
- Role grants follow least privilege: board members are read-only, officers get
  the operational set, coordinators/managers get the reviewer set, and only
  leadership holds `manage`.
- The `get_user_model()` fix eliminates the silently-swallowed import error
  that could leave assignment/delegation actions looking successful without
  applying.
- Tests assert deny-by-default for unassigned users, fail-closed redirects/
  403s, and per-action permission enforcement.

## Tests Added

- 99 tests across 5 modules in `apps/reviews/tests/`: models (constraints,
  unique `(review, item)` checklist response constraint, immutable audit base,
  status transitions), services (create/assign/accept/start, checklist
  auto-population, delegation, escalation, decisions with review-number
  sequencing, SLA events), selectors (pending/overdue scoping), permissions
  (officer/reviewer code sets, deny-by-default), and views (auth, fail-closed
  403/302, assign/delegate/escalate/decide, dashboard).
- `apps/reviews` suite: 99/99 passed.
- Full repository suite: **1134/1134 passed** (previously 1035/1035);
  `manage.py check` and `makemigrations --check --dry-run` clean.

## Quality Gates

- Ruff: clean on `apps/reviews` and `apps/accounts`.
- Black/isort: clean on `apps/reviews` and `apps/accounts`.
- No new lint findings introduced; pre-existing `RemovedInDjango60Warning`
  (CheckConstraint) and `asyncio.iscoroutinefunction` deprecation notices
  remain repo-wide and unrelated.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — version bumped to 1.3.0, Phase 21 status section,
  module status row for Review & Approval, quality metrics (1134), next
  actions, and version history.
- `CHANGELOG.md` — Phase 21 entry under `[Unreleased]`.

## Known Notes

- Part 1 of 4: reviewer inbox/queue polish, digital-signature enforcement
  end-to-end, SLA escalation automation, and full decision-history/dashboard
  reporting remain open for Parts 2–4 of `roadmaps/21-Review-and-Approval.md`.
- Report *documents* (DOCX/PDF) and notification integration for review events
  remain deferred to their owning phases.
- Central dashboard/audit/notification integration is still deferred to its
  owning phase.

## Next Recommended Task

Continue Phase 21 Parts 2–4 (`roadmaps/21-Review-and-Approval.md`) or proceed
to Phase 22 — Notifications & Communication, per the roadmap sequence.
