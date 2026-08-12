# Phase 18 — Monitoring, Evaluation, Accountability & Learning (MEAL): Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-05

**Status:** Implemented (pending acceptance)

## Summary

Phase 18 implements the MEAL module in the new `apps/meal` Django app, per
`roadmaps/18-MEAL.md`. The module is the organization's centralized,
evidence-based monitoring, evaluation, accountability and learning platform. It
provides Theory of Change, Results Frameworks, Logical Frameworks (logframes),
a centralized Indicator registry with categories, baselines, targets and actual
results, data collection (plans, sources, tools, submissions), monitoring
(plans, visits, findings, corrective actions), evaluations and
recommendations, Data Quality Assessments (DQA) with dimension scores,
accountability (complaints, feedback, corrective actions), learning (outcome
harvesting, learning logs, best practices, lessons learned), organizational
KPIs and performance scorecards, and MEAL reports with an executive dashboard.
All 22 `meal.*` permission actions are enforced server-side on every service
and view through fail-closed, scope-aware selectors. The full suite passes
(61 MEAL tests; 483 repository-wide) and every quality gate is green.

## Architecture

- The module lives in a dedicated `apps.meal` app; no other app was given MEAL
  functionality.
- 35 concrete models inherit the shared audit, soft-delete, and
  reference-numbered base records (`MEALRecord`, `ImmutableHistoricalRecord`);
  status history and audit records are append-only (immutable) via
  `ActiveMEALManager` (`IMMUTABLE_MEAL_HISTORY_MESSAGE`).
- Transactional, permission-checked services in `apps/meal/services.py`
  (11 service classes: `MEALService`, `FrameworkService`, `IndicatorService`,
  `DataCollectionService`, `MonitoringService`, `EvaluationService`,
  `DQAService`, `AccountabilityService`, `LearningService`, `ScorecardService`,
  `ReportService`) with a fail-closed `MEALService.create/update/delete` write
  boundary and `_apply_service_errors`/`_history` helpers shared across the
  module (DRY).
- Fail-closed access is enforced through permission helpers
  (`user_can_view_meal`, `user_can_manage_meal`, `user_can_view_confidential`)
  and the `MealPermissionMixin` applied to every view.
- Status workflow is unified: entities transition through a shared
  transition view backed by `TransitionForm(choices=...)` and
  permission-mapped transitions (submit/approve/return/archive), with immutable
  history rows recorded on every write.
- Reference numbering is fully integrated: 21 meal sub-schemes
  (TOC/RFR/LGF/IND/BSL/TGT/DCP/MNP/MON/EVL/DQA/CMP/FDB/CRA/OCH/LLG/BPR/LSN/
  SCR/MRL/KPI) under the new `meal` reference module.
- Evidence/document uploads use isolated private storage with type/size
  validation, metadata, ownership, and secure download; register and report
  exports reuse the formula-safe CSV helpers plus XLSX/DOCX/PDF responses.

## Files Created

- `apps/meal/` — full app:
  - `models.py` (35 concrete models), `constants.py` (30 `TextChoices` +
    `MEAL_ACTION_PERMISSIONS`), `permissions.py` (22 `meal.*` actions),
    `managers.py`, `validators.py`, `exceptions.py`, `selectors.py`,
    `services.py` (11 service classes), `forms.py` (36 forms), `views.py`
    (87 CBVs / routes), `urls.py` (82 routes), `admin.py`, `exports.py`,
    `storage.py`, `seed_data.py`, `seed_loader.py`, `apps.py`, `__init__.py`
  - `migrations/0001_initial.py`
  - `management/commands/seed_meal_reference_data.py`
  - 13 Bootstrap 5 templates under `templates/meal/` (dashboard, indicator
    registry, framework profile, indicator detail, entity directory/detail/form,
    monitoring visit detail, scorecard detail, complaint/feedback detail,
    workflow form)
  - 8 test files under `tests/` (`base.py` + 7 `test_*.py`)
- `apps/rbac/migrations/0010_seed_meal_permissions.py` — the `meal` RBAC
  permission category (22 actions) and role grants.
- `apps/references/migrations/0008_alter_referencenumberscheme_module.py` —
  captures the new `meal` module choice on `ReferenceNumberScheme.module`.
- `docs/development/PHASE18_MEAL_MANAGEMENT_REPORT.md` — this report.

## Files Modified

- `config/settings/base.py` — `apps.meal` added to `INSTALLED_APPS`.
- `config/urls.py` — `meal/` namespace route.
- `templates/components/sidebar.html` — MEAL navigation link gated by
  `meal.view` / `meal.manage`.
- `apps/references/constants.py` — `ReferenceModules.MEAL` choice.
- `apps/references/seed_data.py` — 21 meal reference schemes in `DEFAULT_SCHEMES`.
- `apps/rbac/seed_data.py` — meal module action groups.
- `README.md`, `CHANGELOG.md`, `DEVELOPMENT_STATUS.md` — Phase 18 status.

## Database Changes

- New app migration `apps/meal/migrations/0001_initial.py` creating 35 tables
  (reference data, theory of change, results frameworks and statements,
  logframes and rows, indicator categories/indicators, baselines, targets,
  results, data sources, collection tools/plans, submissions, monitoring
  plans/visits/findings, corrective actions, evaluations and recommendations,
  DQAs and dimension scores, complaints, feedback, outcome harvests, learning
  logs, best practices, lessons learned, organizational KPIs, performance
  scorecards and dimensions, MEAL reports, status history, audit records).
- `apps/references/migrations/0008_alter_referencenumberscheme_module.py` —
  extends the `module` field choices with the `meal` module.
- Seeded reference data via `seed_meal_reference_data` (idempotent): MEAL
  taxonomies and the 21 meal numbering sub-schemes (TOC/RFR/LGF/IND/BSL/TGT/
  DCP/MNP/MON/EVL/DQA/CMP/FDB/CRA/OCH/LLG/BPR/LSN/SCR/MRL/KPI), plus the
  `meal` RBAC permission category (22 actions) with operational role grants
  (`rbac.0010`).

## Security Considerations

- Server-side `meal.*` permission checks on every Phase 18 service and view
  (never client-only), with any-permission module access plus a module-manager
  override.
- Fail-closed selectors: records are visible only to superusers, module
  managers, or users with the relevant view/confidential-view permission whose
  scope includes the record.
- Confidentiality controls: `meal.view_confidential` gates sensitive records
  (complaints, feedback, findings); the dashboard aggregates respect the same
  permissions.
- Every write path emits structured audit/history events; status and audit
  histories are immutable (update/delete/queryset mutation blocked).
- Transitions validate both permission (`permission_by_status`) and status
  legality; invalid transitions are rejected.
- Exports require export or manage permission (not view alone), set
  `Cache-Control: private, no-store`, and keep CSV output formula-safe
  (`=`, `+`, `-`, `@`, tab, CR prefixes neutralized).
- Uploads validate type/size, store privately, and track ownership/metadata.

## Tests Added

- 61 tests in `apps/meal/tests/` across 7 files: models (immutable history,
  soft-delete, unique indicator code/reference enforcement, derived
  aggregates), services (framework/indicator/monitoring/evaluation/DQA/
  accountability/learning/scorecard/report services, transition legality,
  reference confirmation), RBAC permissions and fail-closed access, views,
  security (login redirect, 403, CSRF, export permission, out-of-scope 404),
  seed-command idempotency, and formula-safe exports.
- Full `apps/meal` suite: 61/61 passed.
- Full repository suite: 483/483 passed; `manage.py check` and
  `makemigrations --check --dry-run` clean.
- Quality gates green: Ruff, Black, isort, and mypy across the whole `apps`
  tree (repo-wide clean), plus `manage.py check`.

## Documentation Updated

- `README.md` — Phase 18 roadmap status row, next-phase pointer, acceptance
  reference.
- `CHANGELOG.md` — Phase 18 entry under `[Unreleased]`.
- `DEVELOPMENT_STATUS.md` — current phase, roadmap and module status, Phase 18
  implementation-status table, sprint, accomplishments, and next actions.

## Known Notes

- Notification wiring, central dashboard/audit integration, and app-level
  performance instrumentation for the new features remain deferred to their
  owning later phases, consistent with the roadmap.
- The master roadmap's alternate phase numbering (`roadmaps/
  00-Master-Development-Roadmap.md`) is stale at line 3226: it labels
  "Phase 18: Review and Approval", whereas the authoritative phase sequence
  (`roadmaps/18-MEAL.md`) assigns Phase 18 to MEAL. The master roadmap's
  per-phase labels generally use a legacy numbering that predates the
  per-phase roadmap files; the per-phase roadmap files are authoritative.
- The `ScorecardDimension` name collision (constants `TextChoices` vs. the
  model class) is resolved by referencing the choices via the constants module;
  the meal app also carries the repo's first fully typed mypy-clean pass over
  all 23 module files.

## Next Recommended Task

Begin Phase 19 — Dynamic Report Builder (`roadmaps/19-Dynamic-Report-Builder.md`),
keeping the same modular `apps/meal` conventions and quality gates. Note the
18-MEAL.md roadmap header/section 86 points "next" to Finance & Resource
Management, but the authoritative next roadmap file in the per-phase sequence
is `19-Dynamic-Report-Builder.md`.
