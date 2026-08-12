# Phase 17 — Beneficiary Management: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-05

**Status:** Implemented (pending acceptance)

## Summary

Phase 17 implements the Beneficiary Management module in the new
`apps.beneficiaries` Django app, per `roadmaps/17-Beneficiary-Management.md`.
The module provides the official, consent-governed beneficiary registry: a
unified profile with a validated lifecycle (IDENTIFIED → REGISTERED → VERIFIED
→ ENROLLED → ACTIVE → GRADUATED, with SUSPENDED and EXITED branches), household
and group management, enrollments, participation, attendance, service
delivery, referrals, role-based case notes, assessments, follow-up visits,
safeguarding records, support plans, outcome tracking, exits and transfers,
consent records (including guardian consent and child assent for minors),
confidential documents, communications, feedback, and duplicate review. All 32
`beneficiaries.*` permission actions are enforced server-side on every service
and view through fail-closed, scope-aware selectors. The full suite passes
(91 tests) and every quality gate is green.

## Architecture

- The module lives in a dedicated `apps.beneficiaries` app; no other app was
  given beneficiary functionality. `apps.programs` records that referenced
  beneficiary profiles in earlier phases remain unchanged and continue to use
  their own program-scoped `BeneficiaryRecord`.
- 27 concrete models inherit the shared audit, soft-delete, and
  reference-numbered base records (`BeneficiaryRecord`,
  `ImmutableHistoricalRecord`). Status history and audit records are
  append-only (immutable) via `ImmutableHistoryManager`.
- Transactional, permission-checked services in `apps/beneficiaries/services.py`
  (22 service classes covering create/update/archive/restore, status
  transitions, consent, guardians, households, groups, enrollments,
  participation, attendance, services, referrals, case notes, assessments,
  follow-ups, safeguarding, support plans, outcomes, exits, transfers,
  documents, communications, feedback, and duplicate review).
- Fail-closed access is enforced through `visible_beneficiaries`,
  `user_can_access_beneficiary`, and `visible_beneficiary_documents`
  (document-related records additionally require the document-manage
  permission and fail closed without it).
- Consent governs the lifecycle: adults require recorded consent, minors
  require guardian consent plus assent before VERIFIED/ELIGIBLE/ENROLLED/
  ACTIVE/GRADUATED; `ConsentService.record` is the only write path.
- Reference numbering is fully integrated: 16 beneficiary sub-schemes
  (HHL/GRP/ENR/PRT/ASS/RFL/SRV/CSE/SPL/EXT/TRF/BND/CNS/SFG/OUT/FDB) plus the
  base `beneficiary` (BEN) record scheme.
- Document uploads use isolated private storage with type/size validation,
  metadata, ownership, and secure download; the register and profile exports
  reuse the formula-safe CSV helpers plus XLSX/DOCX/PDF responses.

## Files Created

- `apps/beneficiaries/` — full app:
  - `models.py` (27 concrete models), `constants.py`, `permissions.py` (32
    `beneficiaries.*` actions), `managers.py`, `validators.py`,
    `exceptions.py`, `selectors.py`, `services.py` (22 service classes),
    `forms.py` (36 forms), `views.py` (56 CBVs / routes), `urls.py`,
    `admin.py`, `exports.py`, `report_exports.py`, `storage.py`,
    `seed_data.py`, `seed_loader.py`, `apps.py`, `__init__.py`
  - `migrations/0001_initial.py`
  - `management/commands/seed_beneficiary_reference_data.py`
  - 12 Bootstrap 5 templates under `templates/beneficiaries/` (dashboard,
    directory, profile, beneficiary form, workflow form, households,
    household detail, groups, group detail, related records, and includes)
  - 8 test files under `tests/` (`base.py` + 7 `test_*.py`)
- `apps/references/migrations/0006_seed_beneficiary_reference_schemes.py` —
  16 beneficiary sub-schemes.
- `apps/references/migrations/0007_seed_beneficiary_record_scheme.py` — base
  `beneficiary` (BEN) record scheme.
- `apps/rbac/migrations/0009_seed_beneficiary_permissions.py` — beneficiary
  permission actions and role grants.
- `docs/development/PHASE17_BENEFICIARY_MANAGEMENT_REPORT.md` — this report.

## Files Modified

- `config/settings/base.py` — `apps.beneficiaries` added to `INSTALLED_APPS`.
- `config/urls.py` — `beneficiaries/` namespace route.
- `templates/components/sidebar.html` — Beneficiaries navigation link gated by
  `beneficiaries.view` / `beneficiaries.manage`.
- `apps/rbac/seed_data.py` — beneficiary module action groups.
- `README.md`, `CHANGELOG.md`, `DEVELOPMENT_STATUS.md` — Phase 17 status.

## Database Changes

- New app migration `apps/beneficiaries/migrations/0001_initial.py` creating
  27 tables (beneficiary, households, groups, enrollments, participations,
  attendance, services, referrals, case notes, assessments, follow-ups,
  safeguarding, support plans, outcomes, exits, transfers, consent records,
  guardians, documents, communications, feedback, duplicate reviews, status
  history, audit records, reference data).
- Seeded reference data: 16 beneficiary numbering sub-schemes
  (HHL/GRP/ENR/PRT/ASS/RFL/SRV/CSE/SPL/EXT/TRF/BND/CNS/SFG/OUT/FDB) plus the
  base `beneficiary` (BEN) scheme, and the `beneficiaries` RBAC permission
  category (32 actions) with operational role grants.

## Security Considerations

- Server-side `beneficiaries.*` permission checks on every Phase 17 service and
  view (never client-only), with any-permission module access plus a
  module-manager override.
- Fail-closed selectors: records are visible only to superusers, module
  managers, or users with view/confidential-view permission whose scope
  includes the record (created-by, responsible officer, case manager).
- Confidentiality levels enforced (DIRECTORY/INTERNAL/CONFIDENTIAL visible to
  confidential-view users; RESTRICTED reserved for authorized roles).
- Document records fail closed: viewing documents requires both the document
  permission and beneficiary-scope access.
- Consent gates the lifecycle; minors require guardian consent plus assent;
  consent validity is tracked via `consent_expiry_date`.
- Immutable status/audit history blocks update/delete/queryset mutation.
- Exports require export or manage permission (not view alone), set
  `Cache-Control: private, no-store`, and keep CSV output formula-safe
  (`=`, `+`, `-`, `@`, tab, CR prefixes neutralized).
- Document uploads validate type/size, store privately, and track
  ownership/metadata.
- All service writes emit structured audit events; soft delete is applied
  through PROTECT-safe paths.

## Tests Added

- 91 tests in `apps/beneficiaries/tests/` across 7 files: models (including
  immutable history and soft-delete), services (lifecycle, consent gating,
  guardians, households, groups, case notes, referrals, safeguarding), RBAC
  permissions and fail-closed selectors, views, security (login redirect, 403,
  CSRF, export permission, out-of-scope 404), seed-command idempotency, and
  formula-safe exports.
- Full `apps/beneficiaries` suite: 91/91 passed.
- Quality gates green: `manage.py check`, `makemigrations --check --dry-run`,
  Ruff, Black, isort, mypy (whole `apps` tree), Bandit, and djLint on
  `apps/beneficiaries`.

## Documentation Updated

- `README.md` — Phase 17 roadmap status row, next-phase pointer, acceptance
  reference.
- `CHANGELOG.md` — Phase 17 entry under `[Unreleased]`.
- `DEVELOPMENT_STATUS.md` — current phase, roadmap and module status, Phase 17
  implementation-status table, sprint, accomplishments, and next actions.

## Known Notes

- Notification wiring, central audit/dashboard integration, and app-level
  performance instrumentation for the new features remain deferred to their
  owning later phases, consistent with the roadmap.
- The Phase 16 delivery report's pointer to `roadmaps/17-MEAL.md` predates this
  phase; the beneficiary roadmap is `roadmaps/17-Beneficiary-Management.md` and
  the MEAL roadmap is `roadmaps/18-MEAL.md`.

## Next Recommended Task

Begin Phase 18 — MEAL (`roadmaps/18-MEAL.md`), keeping the same modular
`apps/beneficiaries` conventions and quality gates.
