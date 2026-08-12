# Phase 23 — Organizational Registers: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-07

**Status:** Implemented (pending acceptance)

## Summary

Phase 23 implements the Organizational Registers module in a new
`apps/registers` app, per `roadmaps/23-Organizational-Registers.md`. The module
provides a centralized, configurable register engine: register categories and
registers, configurable entry templates with JSON validation, register
entries with data, tags, approval workflow, relationships, attachments, review
decisions, immutable version history, an immutable activity timeline, and
multi-format exports (CSV/JSON/XLSX/DOCX/PDF). The module is wired into the
RBAC framework (fresh installs and existing databases), reference numbering
via the central `references` service, and the platform navigation.

## Architecture

- New Django app `apps/registers` with **10 concrete models** on shared
  `apps.core` bases (`UUIDModel`, `TimeStampedModel`, `CreatedByModel`,
  `UpdatedByModel`, `SoftDeleteModel`, `ArchivableModel`, `NotesModel`):
  `RegisterCategory`, `Register`, `RegisterTemplate`, `RegisterEntry`,
  `RegisterVersion`, `RegisterAttachment`, `RegisterRelationship`,
  `RegisterReview`, `RegisterActivity`, `RegisterValidation` (plus abstract
  `RegisterRecord`).
- **Approval workflow**: DRAFT → SUBMITTED → PENDING_REVIEW → APPROVED, with
  return-for-correction and reject paths, exercised through `RegisterEntryService`
  transitions (`submit`, `start_review`, `approve`, `return_entry`, `reject`)
  plus archive/restore.
- **Service layer** (`services.py`): 7 service classes on a shared
  `_RegisterServiceMixin` — category, register, template, entry, validation,
  relationship, and attachment services. All writes are permission-gated,
  confidentiality-gated, transaction-backed, and audited into the immutable
  `RegisterActivity` timeline; entries reserve and confirm reference numbers
  through the central `ReferenceNumberService`.
- **Selectors** (`selectors.py`): fail-closed, confidentiality-aware
  querysets (`visible_registers`, `visible_entries`, category/template
  scoping) and access guards.
- **Permissions** (`permissions.py`): 12 `registers.*` action constants plus
  helper functions (`user_can_view_registers`, `user_can_manage_registers`,
  `user_can_view_confidential`, `user_can_export`, `user_can_act_on_entries`).
- **Views/URLs**: 26 permission-checked view classes and a 29-route
  `registers` namespace (dashboard, category/register/template/entry CRUD,
  workflow action views, attachment creation, multi-format exports).
- **Reference numbering**: `ReferenceModules.REGISTERS` registered;
  `registers.0009_seed_register_scheme.py` seeds the `register_entry` scheme
  (prefix `REG`, pattern `{ORG}/REG/{PREFIX}/{YEAR}/{SEQUENCE}`).
- **Exports**: `exports.py` provides CSV/JSON/XLSX/DOCX/PDF with
  formula-injection neutralization, permission gating, no-store/nosniff
  headers, and audited export events.
- **Storage**: `PrivateRegisterStorage` keeps entry attachments outside public
  media and blocks direct URL exposure.

## Files Created

- `apps/registers/` — full module: `models.py`, `services.py`, `selectors.py`,
  `views.py`, `forms.py`, `permissions.py`, `urls.py`, `admin.py`, `apps.py`,
  `managers.py`, `constants.py`, `exports.py`, `storage.py`,
  `migrations/0001_initial.py`.
- `apps/registers/templates/registers/` — 15 Bootstrap 5 templates (dashboard,
  directories, details, forms, entry action, attachment form, module nav and
  form-field includes).
- `apps/registers/tests/` — shared scaffold (`base.py`) plus 6 test modules:
  `test_models.py`, `test_services.py`, `test_views.py`, `test_permissions.py`,
  `test_security.py`, `test_exports.py`.
- `apps/rbac/migrations/0013_seed_register_permissions.py` — RBAC seed
  migration for existing databases.
- `apps/references/migrations/0009_seed_register_scheme.py` — register
  reference scheme seeding.
- `docs/development/PHASE23_REGISTERS_REPORT.md` (this file).

## Files Modified

- `apps/rbac/seed_data.py` — `registers` permission category and role grants.
- `config/settings/base.py` — `apps.registers.apps.RegistersConfig` added to
  `INSTALLED_APPS`.
- `config/urls.py` — `registers/` path with `registers` namespace.
- `templates/components/sidebar.html` — Registers navigation item gated on
  `registers.view` / `registers.manage`.
- `apps/references/constants.py` — `ReferenceModules.REGISTERS`.
- `CHANGELOG.md` and `DEVELOPMENT_STATUS.md` — Phase 23 entries.

## Database Changes

- `registers.0001` — initial schema for all 10 tables with constraints
  (`unique_default_template_per_register`, `unique_version_per_entry`) and an
  index on generic relationship content-type/object-id.
- `rbac.0013` — new seed migration (category, 12 permissions, role grants),
  reversible.
- `references.0009` — register reference scheme seed migration,
  reversible. `makemigrations --check --dry-run` is clean.

## Security Considerations

- Server-side authorization only: every view goes through
  `RegisterPermissionMixin` with a `REGISTER_MANAGE` override; the UI never
  relies on hidden buttons.
- Confidentiality levels scope both selectors and exports; `view_confidential`
  permission is enforced separately.
- Immutable `RegisterActivity` and `RegisterVersion` models reject deletion
  (raise `ValidationError`); admin exposes them read-only.
- CSV exports neutralize spreadsheet-formula injection (`=`, `+`, `-`, `@`,
  tab, CR) and exports are permission-gated and audited.
- Attachments are stored in private storage with metadata validation.
- Tests assert deny-by-default, fail-closed 403/302, and per-action
  permission enforcement.

## Tests Added

- 88 tests across 6 modules in `apps/registers/tests/`: models (defaults,
  immutability, constraints), services (category/register/template/entry/
  validation services, reference + version assignment, full workflow, invalid
  transitions), views (dashboard, CRUD, workflow, exports), permissions
  (fail-closed selectors, confidential scoping), security (immutability,
  confidentiality, uploads), and exports (CSV inclusion/scoping, confidential
  hiding, formula injection, JSON/XLSX/DOCX/PDF).

## Quality Gates

- Ruff/Black/isort: clean on `apps/registers` and touched shared files.
- No new lint findings introduced.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — Phase 23 status section and module status row.
- `CHANGELOG.md` — Phase 23 entry.

## Known Notes

- No management commands exist in `apps/registers` (register lifecycle is
  exercised through views/services).
- Register exports support CSV/JSON/XLSX/DOCX/PDF via lazy library imports.

## Next Recommended Task

Proceed to Phase 24 — Calendar & Meetings
(`roadmaps/24-Calendar-and-Meetings.md`).