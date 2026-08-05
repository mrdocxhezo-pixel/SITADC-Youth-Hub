# Phase 09 — Reference Numbering System: Delivery Report

**Project:** SITADC Youth Hub

**Phase:** 09 — Reference Numbering System (roadmap file: `roadmaps/07-Reference-Numbering-System.md`)

**Date:** 2026-08-01

**Status:** Complete

---

# 1. Summary

The Reference Numbering System provides a centralized, configurable mechanism for generating, managing, auditing, and tracing every business reference number used across SITADC Youth Hub. It is implemented as the `apps/references` Django application.

The module delivers:

* Configurable numbering schemes with token-based patterns.
* Per-period sequence counters with multiple reset policies.
* A registry of every issued reference number with an immutable lifecycle.
* An immutable audit trail of all numbering events.
* A preview capability that never consumes sequence values.
* RBAC permissions integrated into the wildcard role catalogue.
* Seed data for 16 default schemes and three management commands.

---

# 2. Scope

Implemented, per `roadmaps/07-Reference-Numbering-System.md`:

* Scheme model (`ReferenceNumberScheme`).
* Sequence model (`ReferenceSequence`).
* Registry model (`GeneratedReferenceNumber`).
* Audit model (`ReferenceNumberAuditRecord`).
* Token engine and scheme resolution (`numbering.py`).
* Scheme lifecycle services (create, update, activate, deactivate, archive, restore).
* Reference lifecycle services (generate, confirm, cancel, void, manual correction, sequence reset).
* Validators, selectors, forms, views, URLs, templates, and admin registration.
* Seed data and management commands.
* RBAC permission category and seed migration.
* Unit and integration tests.

Out of scope for this phase (per roadmap):

* Business modules (leadership, membership, volunteers, etc.).
* Global search and export engine integration for numbering.
* Notification wiring.

---

# 3. Files Created

New files under `apps/references/`:

* `__init__.py`
* `apps.py`
* `admin.py`
* `constants.py`
* `exceptions.py`
* `forms.py`
* `managers.py`
* `models.py`
* `numbering.py`
* `permissions.py`
* `seed_data.py`
* `selectors.py`
* `services.py`
* `urls.py`
* `validators.py`
* `views.py`
* `migrations/0001_initial.py`
* `management/commands/seed_reference_schemes.py`
* `management/commands/validate_reference_schemes.py`
* `management/commands/preview_reference_number.py`
* `templates/references/index.html`
* `templates/references/scheme_list.html`
* `templates/references/scheme_detail.html`
* `templates/references/scheme_form.html`
* `templates/references/reset_form.html`
* `templates/references/preview.html`
* `templates/references/registry.html`
* `templates/references/sequence_list.html`
* `templates/references/audit_list.html`
* `tests/__init__.py`
* `tests/test_models.py`
* `tests/test_numbering.py`
* `tests/test_services.py`
* `tests/test_views.py`

New files elsewhere:

* `apps/rbac/migrations/0003_seed_reference_numbers_permissions.py`

---

# 4. Files Modified

* `config/settings/base.py` — added `apps.references.apps.ReferencesConfig` to `INSTALLED_APPS`.
* `apps/core/urls.py` — added `path("references/", include("apps.references.urls"))`.
* `templates/components/sidebar.html` — added "Reference Numbers" navigation link.
* `apps/rbac/seed_data.py` — added the `reference_numbers` permission category (9 actions).
* `README.md` — added the Reference Numbering module to Main Modules.
* `ARCHITECTURE.md` — added Reference Numbering to the core modules and application structure lists.
* `PROJECT_STRUCTURE.md` — added `references/` to the applications list.
* `AGENTS.md` — added `references/` to the example apps list.
* `DEVELOPMENT_STATUS.md` — updated phase, module, sprint, metrics, accomplishments, and next actions.
* `CHANGELOG.md` — added the Phase 09 entry.

---

# 5. Database Changes

* New migration `references.0001_initial` (applied), creating:

  * `references_referencenumberscheme`
  * `references_referencesequence`
  * `references_generatedreferencenumber`
  * `references_referencenumberauditrecord`

* New migration `rbac.0003_seed_reference_numbers_permissions` (applied), seeding the `reference_numbers` permission category and re-granting wildcard roles.

* Seed data: 16 default reference schemes created by `seed_reference_schemes`.

---

# 6. Design

## 6.1 Models

* `ReferenceNumberScheme` — describes a numbering policy: prefix, token pattern, organizational code, sequence length, start value, reset period (Never / Annually / Monthly / Daily / Fiscal / Custom), fiscal start month, custom interval, defaults (module, record type, fallback), and lifecycle status.
* `ReferenceSequence` — per-scheme, per-period counter (`period_key`, `start_value`, `current_value`, `next_value`).
* `GeneratedReferenceNumber` — the registry record holding the rendered number, module, record type, sequence value, period key, and status. Immutable: direct edits and deletes raise `ValidationError`; lifecycle changes go through `transition()`.
* `ReferenceNumberAuditRecord` — immutable audit trail of numbering events.

Database-level uniqueness is enforced on both `reference_number` and `(scheme, period_key, sequence_value)`.

## 6.2 Token Engine

`numbering.py` renders patterns using tokens:

`{PREFIX} {ORG} {MODULE} {TYPE} {UNIT} {DIRECTORATE} {REGION} {DISTRICT} {COMMUNITY} {TEAM} {PROGRAM} {PROJECT} {YEAR} {YEAR_SHORT} {MONTH} {DAY} {FY} {SEQUENCE}`

Unknown tokens are rejected during validation.

## 6.3 Resolution

`resolve_scheme()` resolves the applicable scheme in order:

1. Explicit scheme by code.
2. Record-type default for the module.
3. Module default.
4. Organizational fallback scheme.

Failure raises `MissingNumberingContextError`; an unusable scheme raises `InactiveNumberingSchemeError`.

## 6.4 Generation

`ReferenceNumberService` locks the sequence row with `select_for_update()` inside a transaction, increments the counter, inserts the registry row, and retries up to 5 times on contention (`MAX_GENERATION_ATTEMPTS`). Reference numbers are never reused: a freed number is cancelled/voided, never reissued.

## 6.5 Lifecycle

Registry statuses follow `Available → Reserved → Assigned`, with `Cancelled` and `Voided` terminal states. `ConfirmReferenceAssignmentService` re-checks the stored reference against the scheme before assignment.

## 6.6 Preview

`selectors.next_reference_number()` renders the next number without consuming the sequence.

---

# 7. Permissions

New `reference_numbers` category with actions:

* `reference_numbers.view`
* `reference_numbers.create`
* `reference_numbers.update`
* `reference_numbers.activate`
* `reference_numbers.archive`
* `reference_numbers.preview`
* `reference_numbers.reset`
* `reference_numbers.view_registry`
* `reference_numbers.correct`

Views are protected with `@permission_required(...)`; services enforce permissions server-side; wildcard (`"*"`) roles pick up the new actions automatically via the RBAC seed machinery. Tests verify both granted access and 403 for unauthorized users.

---

# 8. Management Commands

* `python manage.py seed_reference_schemes` — idempotent seed of the 16 default schemes.
* `python manage.py validate_reference_schemes` — validates all schemes and exits non-zero on problems (CI-friendly).
* `python manage.py preview_reference_number` — renders the next number for a module/context without consuming it.

---

# 9. UI

Nine Bootstrap 5 templates extend `layouts/dashboard.html` and are responsive, accessible, and consistent with the design system:

* `index.html` — dashboard summary.
* `scheme_list.html` — schemes with module filter.
* `scheme_detail.html` — scheme, sequences, recent numbers, history.
* `scheme_form.html` — create/update.
* `reset_form.html` — sequence reset.
* `preview.html` — number preview.
* `registry.html` — registry of issued numbers.
* `sequence_list.html` — sequence counters.
* `audit_list.html` — immutable audit trail.

---

# 10. Admin

All four models are registered in `apps/references/admin.py`. Registry and audit records are read-only in admin; schemes support the full lifecycle.

---

# 11. Security Considerations

* Every view and service checks permissions server-side (never client-side only).
* Registry and audit records are immutable at the model layer (`delete`/`update` raise `ValidationError`) and in the admin.
* Generation uses row-level locking within a transaction to prevent duplicate numbers under concurrency.
* Sequence reset never moves the counter backwards; it resumes at `max(configured, current + 1)`.
* Manual correction requires a documented reason and is recorded in the audit trail.
* No secrets, keys, or credentials are stored or logged.
* CSRF protection applies to all forms.

---

# 12. Audit Logging

Every numbering event is recorded immutably:

* Scheme creation, update, activation, deactivation, archive, restore.
* Sequence reset.
* Reference generation, confirmation, cancellation, void, manual correction.

Audit records capture entity type/id, action, actor (`changed_by`), before/after snapshots, and notes.

---

# 13. Tests

New tests: **55** across `apps/references/tests/`:

* `test_models.py` — scheme validation, immutability, uniqueness, status transitions, permission registration.
* `test_numbering.py` — token rendering, context overrides, period keys, fiscal year, resolution, fallbacks.
* `test_services.py` — scheme lifecycle, generation, concurrency behavior, confirmation, cancellation, void, correction, reset, audit recording, permission enforcement.
* `test_views.py` — index/scheme/list/detail/registry/sequence/audit/preview rendering, create flows, login and permission guards.

**Full suite:** `171 passed, 124 warnings`.

---

# 14. Quality Gates

* `manage.py check` — clean.
* `ruff check apps` — all checks passed.
* `black --check apps/references` — clean.
* `isort --check apps/references` — clean.
* `mypy apps/references` — clean (remaining mypy findings are pre-existing in `apps/organizations` and `apps/rbac`).
* Template compilation — all 9 templates compile.
* `makemigrations --check --dry-run references` — no changes detected.

Known environment limitations (pre-existing, not introduced by this phase):

* Bandit 1.7.9 raises `'Constant' object has no attribute 's'` on Python 3.14 for all scanned files (including `apps/organizations`).
* djlint cannot be installed because its `regex` dependency fails to build wheels on Python 3.14; templates were verified via Django's template loader instead.

---

# 15. Documentation Updated

* `CHANGELOG.md` — Phase 09 entry.
* `DEVELOPMENT_STATUS.md` — phase/module status, sprint, metrics, accomplishments, next actions.
* `README.md` — Main Modules.
* `ARCHITECTURE.md` — core modules and application structure.
* `PROJECT_STRUCTURE.md` — applications list.
* `AGENTS.md` — example apps list.
* This report.

---

# 16. Known Limitations / Notes

* Business modules are not yet wired to `ReferenceNumberService`; integration occurs when those modules are built (e.g., reports, documents, programs).
* The pre-existing `rbac` migration drift (`0004_alter_rolehistory_action.py`, `RoleHistoryAction.DELETED` vs the initial migration) is unrelated to this phase and was left untouched.
* Pre-existing mypy findings in `apps/organizations` and `apps/rbac` remain tracked as pending work.

---

# 17. Commands Executed (Validation)

* `python manage.py check`
* `python manage.py migrate`
* `python manage.py seed_reference_schemes` (16 created; idempotent on re-run)
* `python manage.py validate_reference_schemes` — "All schemes valid."
* `python manage.py preview_reference_number --module reports --year 2025` — `RPT-SITADC-2025-000001`
* `pytest` (171 passed)
* `ruff check`, `black`, `isort`, `mypy`

---

# 18. Phase Status

Phase 09 — Reference Numbering System is **complete**:

* Requirements implemented.
* Permissions enforced server-side.
* Validation implemented.
* Tests written and passing.
* Documentation updated.
* Responsive, accessible UI completed.
* No duplicate functionality.
* No placeholder code.

---

# 19. Next Recommended Task

Begin **Phase 10 — Audit Logging** (`roadmaps/08-Audit-Logging.md`), the system-wide centralized audit infrastructure that builds on the immutable audit patterns established in `apps/organizations` and `apps/references`. Before that, optionally resolve the remaining pre-existing mypy findings in `apps/organizations` and `apps/rbac`.
