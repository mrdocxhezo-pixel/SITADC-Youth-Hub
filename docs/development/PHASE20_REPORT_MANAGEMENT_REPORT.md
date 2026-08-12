# Phase 20 — Report Management: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-08

**Status:** Implemented (pending acceptance)

## Summary

Phase 20 completes the Report Management module in the existing
`apps/report_instances` app, per `roadmaps/20-Report-Management.md` and building
on the Phase 19 Dynamic Report Builder (`apps/reports`). This phase wires the
report instance domain into the RBAC framework, seeds the permission catalogue
for both fresh installs and existing databases, fixes a real submission
permission bug, adds the two templates that were missing from the version
routes, and establishes a comprehensive 86-test suite for models, services,
selectors, permissions, exports, forms, and views. The full repository suite is
green at 1035 passed.

## Architecture

- The report instance domain remains in `apps/report_instances`; no new app was
  introduced and no Phase 19 code was duplicated.
- RBAC integration: the `report_instances` category (27 actions, including
  `view`, `view_own`, `view_all`, `view_timeline`, `view_validation`, `create`,
  `update`, `update_own`, `delete`, `submit`, `submit_own`, `withdraw`,
  `resubmit`, `validate`, `approve`, `reject`, `archive`, `restore`, `export`,
  `assign`, `comment`, `comment_internal`, `upload_evidence`,
  `verify_evidence`, `upload_attachment`, `manage_reminders`, `manage`) was
  added to `PERMISSION_CATEGORIES` in `apps/rbac/seed_data.py`, and named role
  groups `REPORT_INSTANCES_OPERATIONAL` / `REPORT_INSTANCES_REVIEW` were wired
  into the officer and coordinator/manager bases so fresh installs grant the new
  codes automatically.
- Existing databases are brought in line by a dedicated seed migration
  (`rbac.0014`, `atomic=False`) that creates the category, the 27 `Permission`
  rows, and role grants: leadership = all actions, coordinators/managers =
  reviewer set (all except `manage`), officers = operational set, board =
  read-only view actions. Both `role.permissions` and `role.group.permissions`
  are synchronized.
- `ReportSubmitView` now enforces `can_submit_report` instead of
  `can_update_report` (`apps/report_instances/views.py`). This fixes a real
  lifecycle bug: a `READY_FOR_SUBMISSION` report is no longer editable, so the
  old check always denied submission; the corrected check lets authorized users
  actually submit.
- Two previously-missing templates were added:
  `report_instances/report_versions.html` (version list) and
  `report_instances/report_version_detail.html` (snapshot details), fixing 500s
  on `ReportVersionsView` and `ReportVersionDetailView`.

## Files Created

- `apps/rbac/migrations/0014_seed_report_instance_permissions.py` — seed
  migration for the `report_instances` category, permissions, and role grants
  on existing databases.
- `apps/report_instances/templates/report_instances/report_versions.html` and
  `report_instances/templates/report_instances/report_version_detail.html`.
- `apps/report_instances/tests/` — shared scaffold (`base.py`) plus 8 test
  modules: `test_models.py`, `test_services.py`, `test_selectors.py`,
  `test_permissions.py`, `test_exports.py`, `test_forms.py`, `test_views.py`,
  and the rewritten `test_reports.py` service-level workflow test.
- `docs/development/PHASE20_REPORT_MANAGEMENT_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — added the `report_instances` category to
  `PERMISSION_CATEGORIES` and `ALL_PERMISSION_CODES`, plus the
  `REPORT_INSTANCES_OPERATIONAL` / `REPORT_INSTANCES_REVIEW` role groups wired
  into the officer and coordinator/manager bases.
- `apps/report_instances/views.py` — `ReportSubmitView` uses `can_submit_report`;
  added the `can_submit_report` import, the `suppress` import (SIM105), and a
  `ClassVar` annotation for `ACTION_CHOICES` (RUF012).
- `apps/report_instances/tests/test_reports.py` — rewritten as a service-level
  workflow test (create → save responses → validate → submit, DRAFT →
  READY_FOR_SUBMISSION → SUBMITTED).
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 20 entries.

## Database Changes

- `rbac.0014` — new seed migration (category, 27 permissions, role grants),
  reversible. No model schema changes; `makemigrations --check --dry-run` is
  clean.

## Security Considerations

- Server-side authorization only: every view uses `check_permission` with the
  literal `report_instances.*` codes; the UI never relies on hidden buttons.
- The permission catalogue gate (`ALL_PERMISSION_CODES`) is now aware of the
  report instance codes, so previously-denied non-superusers gain exactly the
  granted actions and nothing more.
- Role grants follow least privilege: board members are read-only, officers get
  the operational set, coordinators/managers get the reviewer set (excluding
  `manage`), and only leadership holds `manage`.
- Tests assert deny-by-default for unassigned users and scope-based visibility
  (`view_own` vs `view_all` vs assigned reports).

## Tests Added

- 86 tests across 8 modules in `apps/report_instances/tests/`: models (state
  helpers, status-history/timeline immutability, submission version snapshots,
  reference-number uniqueness), services (create/update/validate/submit/
  withdraw/return/resubmit/approve/archive/restore, evidence, attachments,
  comments, assignment, reminders, auto-save, duplicate, exports,
  submission records), selectors (scope filtering, overdue, reviewer, own vs
  all), permissions (officer/manager/board code sets, scope visibility,
  deny-by-default), exports (CSV/HTML/JSON), forms (dynamic field building,
  required-field validation, published-template queryset), and views (auth,
  fail-closed 403/302, create/edit/detail, data entry, preview, versions,
  exports, autosave, review actions, archive/restore, duplicate).
- `apps/report_instances` suite: 86/86 passed.
- Full repository suite: **1035/1035 passed** (previously 950/950);
  `manage.py check` and `makemigrations --check --dry-run` clean.

## Quality Gates

- Ruff: clean on all session-modified files.
- Black/isort: clean on all session-modified files.
- No new lint findings introduced; pre-existing `RemovedInDjango60Warning`
  (CheckConstraint) and `asyncio.iscoroutinefunction` deprecation notices
  remain repo-wide and unrelated.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — version bumped to 1.2.0, Phase 20 status section,
  module status row for Report Instances, quality metrics (1035), next actions,
  and version history.
- `CHANGELOG.md` — Phase 20 entry under `[Unreleased]`.

## Known Notes

- The submitted/approved report content is exported via the pre-existing
  export service; report *documents* (DOCX/PDF) and review-workflow automation
  beyond the current state machine remain part of Phase 21
  (`roadmaps/21-Review-and-Approval.md`).
- Central dashboard/audit/notification integration for report events is still
  deferred to its owning phase.

## Next Recommended Task

Begin Phase 21 — Report Review, Approval & Workflow Automation
(`roadmaps/21-Review-and-Approval.md`), building on the Phase 20 submission
workflow.
