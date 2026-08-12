# Phase 16 — Project Management: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-05

**Status:** Implemented (pending acceptance)

## Summary

Phase 16 closes the project-management gaps identified after Phase 15
acceptance, per `roadmaps/16-Project-Management.md`. It adds operational
project-management capability inside `apps.programs`: a hierarchical Work
Breakdown Structure (WBS) with roll-up progress, a results framework,
beneficiary participation tracking, project timelines, a closure workflow,
project reports with CSV/XLSX/DOCX/PDF export, milestone and deliverable
submission/approval workflows, change-request decisions with auto-apply,
evidence versioning, and project analytics. Every entry point is protected by
server-side `projects.*` permission checks and records structured audit
events. The full `apps/programs` suite passes (112 tests) and all quality
gates are green.

## Architecture

- All new models live in `apps.programs` (no new app; the existing Phase 15
  registry already hosts project records). Operation models inherit the
  existing soft-delete, audit, and reference-numbered base records.
- Transactional, permission-checked services in `apps/programs/services.py`
  (`WbsService`, `ProjectApprovalService`, `ProjectClosureService`,
  `ProjectResultService`, `BeneficiaryParticipationService`,
  `ProjectTimelineService`, `EvidenceService.upload_version`,
  `ProjectReportService`, `ProjectAnalyticsService`, and
  `ChangeRequestService.decide`).
- Fail-closed access is enforced through the existing `user_can_access_project`
  selector on every Phase 16 service and view.
- WBS progress, project completion percentage, and analytics derive from a
  single `_recalculate_project_progress` path; task counts traverse
  `activity__work_plan__project` because `Task` belongs to `Activity`.
- Project budget analytics use `Project.budget_approved` / `budget_utilized`
  (program budgets remain program-scoped).
- Report exports reuse the existing formula-safe CSV helpers and private-storage
  document validation.

## Files Created

- `apps/programs/migrations/0003_beneficiaryparticipation_evidenceversion_and_more.py`
- `apps/programs/migrations/0004_milestone_submitted_at_milestone_submitted_by.py`
- `apps/programs/migrations/0005_changerequest_proposed_value_and_more.py`
- `apps/programs/migrations/0006_deliverable_submitted_by.py`
- `apps/programs/templates/programs/project_related_records.html`
- `apps/programs/templates/programs/project_wbs.html`
- `apps/programs/templates/programs/project_closure.html`
- `apps/programs/templates/programs/project_analytics.html`
- `apps/programs/tests/test_project_management.py`
- `docs/development/PHASE16_PROJECT_MANAGEMENT_REPORT.md`

## Files Modified

- `apps/programs/models.py` — `WBSNode`, `ProjectResult`, `BeneficiaryParticipation`,
  `ProjectTimeline`, `ProjectClosure`, `ProjectReport`, `EvidenceVersion` added;
  `Project.classifications` M2M + derived `completion_percentage`; `Milestone` /
  `Deliverable` submission and approval fields; `EvidenceRecord.version_number`;
  `ChangeRequest` decision fields.
- `apps/programs/constants.py` — `WBSNodeType`, `WBSNodeStatus`,
  `MilestoneApprovalStatus`, `ProjectClosureStatus`, `ProjectReportType`,
  `ProjectReportStatus`, `ResultType`, `ResultStatus`, `TimelineEntryStatus`,
  `ReferenceDataKind.PROJECT_CLASSIFICATION`, and `wbs` scheme mapping.
- `apps/programs/services.py` — Phase 16 services, M2M support in
  `ProjectService`, analytics fixes.
- `apps/programs/forms.py` — 10+ Phase 16 forms; `ProjectForm.classifications`
  queryset.
- `apps/programs/views.py` — WBS, results, timeline, participation, closure,
  reports, analytics, approval, change-decision, and report-export views.
- `apps/programs/urls.py` — new named routes.
- `apps/programs/report_exports.py` — project report CSV/XLSX/DOCX/PDF responses
  with permission guard.
- `apps/programs/admin.py` — all Phase 16 operation models registered.
- `apps/programs/seed_data.py` + `seed_loader.py` — `PROJECT_CLASSIFICATION`
  taxonomy (16 rows) and `wbs` scheme.
- `apps/programs/templates/programs/project_profile.html` — project tools bar.
- `README.md`, `CHANGELOG.md`, `DEVELOPMENT_STATUS.md` — Phase 16 status.

## Database Changes

- New tables: `programs_wbsnode`, `programs_projectresult`,
  `programs_beneficiaryparticipation`, `programs_projecttimeline`,
  `programs_projectclosure`, `programs_projectreport`,
  `programs_evidenceversion`, and the `programs_project_classifications`
  join table.
- New columns on existing tables: `Project.completion_percentage`,
  `Milestone.submitted_by/submitted_at/approval_status/approval_notes/
  approved_by/approved_at/evidence_notes`, `Deliverable.submitted_by/
  submitted_at/approval_notes/approved_by/approved_at/evidence_notes`,
  `EvidenceRecord.version_number`, `ChangeRequest.target_model/target_field/
  target_record_id/proposed_value/reviewer/reviewer_notes/reviewed_at`.
- New indexes: milestone `[project, approval_status]`,
  `EvidenceRecord.version_number`, `Project.completion_percentage`.
- Seeded reference data: 16 `PROJECT_CLASSIFICATION` rows and the `wbs`
  numbering scheme.

## Security Considerations

- Server-side `projects.*` permission checks on every Phase 16 service and view
  (never client-only).
- Fail-closed project-scope selector `user_can_access_project`.
- Self-approval is blocked for milestone/deliverable approval, closure, and
  report approval (approver cannot approve own submission).
- Rejection paths require decision notes.
- Change-request decisions require reviewer permission and cannot be decided by
  the creator.
- WBS cycles and cross-project parents are rejected.
- Report exports enforce the export/manage permission, respect archived-state
  access, and set `Cache-Control: no-store`; CSV output remains formula-safe.
- Evidence versions keep private storage and validated document uploads.
- All service writes emit structured audit events.

## Tests Added

- 22 tests in `apps/programs/tests/test_project_management.py` covering WBS
  create/update/delete, roll-up completion, cross-project rejection, cycle
  detection, milestone/deliverable approval workflows, change-request decisions,
  closure workflow, results uniqueness, evidence versioning, report lifecycle,
  and analytics.
- Full `apps/programs` suite: 112/112 passed.
- Quality gates green: `manage.py check`, `makemigrations --check`, Ruff, Black,
  isort, mypy, Bandit, and djLint on `apps/programs`.

## Documentation Updated

- `README.md` — Phase 16 status row, next-phase pointer, acceptance reference.
- `CHANGELOG.md` — Phase 16 entry under `[Unreleased]`.
- `DEVELOPMENT_STATUS.md` — current phase, roadmap and module status, Phase 16
  implementation-status table, sprint, accomplishments, and next actions.

## Known Notes

- `roadmaps/16-Project-Management.md` header reads "Next: Phase 17 — MEAL";
  this is consistent with the active phase sequence and requires no action.
- Notification wiring, central audit integration, and dashboard/app-level
  performance instrumentation for the new features remain deferred to their
  owning later phases, consistent with the roadmap.
- `WBSNodeProgressForm` exists for per-node progress capture; the primary WBS
  update path is `WbsService.update_node`.

## Next Recommended Task

Begin Phase 17 — MEAL (`roadmaps/17-MEAL.md`), keeping the same modular
`apps/programs` conventions and quality gates.
