# Phase 19 — Dynamic Report Builder: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-08

**Status:** Implemented (pending acceptance)

## Summary

Phase 19 implements the Dynamic Report Builder in the new `apps/reports` Django
app, per `roadmaps/19-Dynamic-Report-Builder.md`. The module is the
organization's centralized report template engine: authorized administrators
design, publish, maintain, version, clone, import, and export reusable report
templates without modifying application source code. It provides report
categories, dynamic sections, field groups, supported field types, validation
rules, conditional logic, version history with restore/compare, JSON schema
snapshots, workflow definitions, publication lifecycle, and an admin-facing
dashboard. All `report_templates.*` permission actions are enforced
server-side through fail-closed, permission-aware selectors and a shared
`ReportPermissionMixin`. The full module suite passes (97 reports tests) and
the full repository suite is green (950 passed).

## Architecture

- The module lives in a dedicated `apps.reports` app; no other app was given
  report-builder functionality.
- Core models: `ReportCategory`, `ReportTemplate`, `ReportTemplateVersion`,
  `TemplateSchema`, `TemplateSection`, `FieldGroup`, `ReportField` (with
  supported field types, validation rules, and conditional logic), `ReportLayout`,
  `ReportBuilderConfiguration`, `ReportBuilderAuditLog`, `WorkflowDefinition`,
  `WorkflowStage`, `ApprovalRule`.
- Transactional, permission-checked services in `apps/reports/services.py`
  (`ReportTemplateService`, `TemplateSchemaService`, `TemplateVersionService`,
  `TemplatePublicationService`, `TemplateCloneService`, `TemplateImportService`,
  `ReportCategoryService`, plus report-builder configuration services) that
  centralize create/update/publish/clone/import/export logic (DRY).
- Permission-aware selectors (`apps/reports/selectors.py`) and a shared
  `ReportPermissionMixin` resolve literal `report_templates.*` permission codes
  with fail-closed behavior: authenticated-but-unauthorized users receive 403
  (not redirects), matching the other RBAC-gated modules.
- `TemplateSchemaService.save_schema` validates dynamic field schemas against
  `FieldType`/`FieldDataType` enums and raises the domain exception
  `InvalidTemplateSchemaError` (a `DynamicTemplateError` subclass) on invalid
  schema input; views catch `DynamicTemplateError` so malformed schema posts
  render a clean error instead of a 500.
- The `report_instances` app ships a service-level workflow test
  (`create_report` → `save_field_response`/`save_section_response` →
  `validate_report` → `submit_report`) proving DRAFT →
  READY_FOR_SUBMISSION → SUBMITTED transitions end-to-end.
- Reference numbering uses the `report_template` scheme (prefix `RT`, module
  `ReferenceModules.REPORTS`), integrated with the Phase 7 numbering engine.

## Files Created

- `apps/reports/` (full Phase 19 module): models, forms, views, urls, services,
  selectors, permissions, validators, formulas, constants, managers, querysets,
  seed data, admin, 3 migrations, management commands
  (`seed_report_templates`, `validate_report_templates`), 17 Bootstrap 5
  templates, and static JS/CSS for the visual schema designer.
- `apps/reports/tests/` — 8 test files (`test_forms`, `test_formulas`,
  `test_models`, `test_permissions`, `test_selectors`, `test_services`,
  `test_views`, plus `base.py` fixtures).
- `apps/report_instances/tests/test_reports.py` — service-level workflow test.

## Files Modified

- `apps/reports/tests/test_services.py` — aligned with current service APIs:
  formula validation now expects `InvalidTemplateSchemaError`,
  `create_version(..., bump="major")` for "2.0", export via
  `TemplateSchemaService.export_json`, and import with a unique `code`.
- `apps/reports/tests/test_models.py` — `test_publish_validation_errors` uses
  `TemplatePublicationService.publish` and expects `TemplatePublishError`.
- `apps/reports/tests/test_permissions.py` — officer create test corrected
  (officer has CREATE); added viewer-create denial test.
- `apps/reports/tests/test_views.py` — 15 RBAC assertions changed 302→403
  (viewer/outsider denied fail-closed); schema POST now sends `data_type` and
  `sort_order`.
- `apps/reports/views.py` — `SchemaDesignerView.form_valid` added
  `except DynamicTemplateError` branch and import.
- `apps/reports/templates/reports/template_versions.html` — guard the compare
  link with `{% if versions|length > 1 %}` (fixes single-version crash).
- `apps/volunteers/tests/test_services.py` — relative-date leave test.

## Database Changes

- `reports.0001` — report categories, templates, versions, schemas, sections,
  field groups, fields, layouts, configuration, audit log.
- `reports.0002` — workflow definition/stage/approval rule models.
- `reports.0003` — report configuration + reporting period.
- `references.0006/0007` and `rbac.0011` (pre-existing) seed the
  `report_template` numbering scheme and `report_templates.*` permissions;
  `makemigrations --check --dry-run` is clean.

## Security Considerations

- Every `reports:` view is guarded by `ReportPermissionMixin` with fail-closed
  behavior (403 for unauthorized authenticated users, 404 for out-of-scope or
  archived records).
- Permission checks are enforced server-side in both views and services; the
  UI never relies on hidden buttons alone.
- Report template imports validate payload shape and regenerate template codes;
  exports do not leak internal secrets.
- Audit logging records create/update/publish/clone/import/export activity.

## Tests Added

- 97 tests in `apps/reports/tests/` across 7 files: forms, formulas, models,
  permissions, selectors, services, views (dashboard, directory, create,
  detail, update, schema designer, preview, publish, lifecycle, clone,
  import/export, versions, compare, restore, categories, settings).
- 1 service-level workflow test in `apps/report_instances/tests/test_reports.py`.
- Full `apps/reports` suite: 97/97 passed.
- Full repository suite: **950/950 passed** (previously 926 passed / 23 failed);
  `manage.py check` and `makemigrations --check --dry-run` clean.

## Quality Gates

- Ruff: clean on all session-modified reports test files.
- Black/isort: clean on all session-modified files.
- Pre-existing findings retained (not introduced by this work):
  `apps/reports/views.py:800` E402 (local `re` import), and E501 lines in
  `tests/base.py`, `tests/test_forms.py`, `tests/test_selectors.py`.

## Documentation Updated

- `DEVELOPMENT_STATUS.md` — Phase 19 status row, module status table, and
  next actions.
- `CHANGELOG.md` — Phase 19 entry under `[Unreleased]`.

## Known Notes

- Central dashboard/audit integration, notification wiring, and the
  report-submission workflow pages (Phase 20) remain deferred to their owning
  phases; `apps/report_instances` provides the models/views skeleton for Phase 20.
- `RemovedInDjango60Warning` for `CheckConstraint.check` (stakeholders) and the
  `FORMS_URLFIELD_ASSUME_HTTPS` default are pre-existing, repo-wide notices.

## Next Recommended Task

Begin Phase 20 — Report Submission, Review & Approval Workflow
(`roadmaps/20-Report-Management.md`), building on the published report
templates and the `report_instances` foundation.
