# Phase 13 — Volunteer Management: Delivery Report

**Project:** SITADC Youth Hub

**Date:** 2026-08-02

**Status:** Stabilized — remaining blockers implemented, acceptance re-review required

# 1. Executive Summary

Phase 13 was audited against `roadmaps/13-Volunteer-Management.md`, security policy, and the project Definition of Done. The existing scaffold passed its 17 tests but contained local reference generation, unconfirmed reservations, direct unaudited writes, global PII queries, public uploads, invalid transitions, incomplete immutability, and contradictory completion claims. Stabilization corrected the critical numbering, workflow, authorization, privacy, storage, export, validation, audit, query, UI, and test defects. Phase 13 is not marked complete because several roadmap capabilities remain absent.

# 2. Master Roadmap Compliance

The canonical detailed roadmap sequence is Phase 13 Volunteer Management, Phase 14 Stakeholder Management, and Phase 15 Program Management. No Stakeholder, Program, or Project module was implemented. Phase 14 remains gated.

# 3. Repository Assessment

The Django app already contained 20 volunteer models, nine service classes, forms, 25 routes, 23 templates, a single migration, and 17 tests. Dashboard and centralized audit prerequisites remain incomplete elsewhere in the repository. Repository-wide quality gates also had hundreds of pre-existing findings.

# 4. Volunteer Management Architecture

`apps.volunteers.services` owns writes; `apps.volunteers.selectors` owns scoped reads; models enforce portable validation and constraints; RBAC owns authorization; references owns all identifier issuance; and private storage owns confidential uploads. Later program/project integrations were not duplicated.

# 5. Volunteer Lifecycle

Implemented service transitions cover campaign, application submission, screening, interview, approval, profile registration, onboarding, active service, assignment, leave, exit, alumni, archive, and restore. Invalid profile/application transitions raise `ValidationError`; concurrent status decisions use row locks.

# 6. Recruitment, Screening, And Onboarding

Campaign creation and public application submission now use VRC/VAP references. Consent is mandatory. Screening prerequisites, interview score bounds, approval, approved-application registration, onboarding acknowledgements, and activation are validated and audited.

# 7. Assignments And Service

Assignment eligibility, date ordering, self-supervision, attendance dates/hours/duplicates, training dates, performance scores/review periods, leave overlap/state, and exit clearance are validated. Assignment closure writes immutable deployment history.

# 8. Communications

Dedicated volunteer communication records are now implemented via `VolunteerCommunication` with configurable channels (email, SMS, phone, letter, newsletter, in-app, other). Communications are recorded through `VolunteerCommunicationService`, gated by `volunteers.manage_communications`, and audited under `COMMUNICATION_SENT`.

# 9. Reporting

The volunteer register exports as CSV, XLSX, DOCX, and PDF via `apps/volunteers/exports.py`. All exports are scoped to visible profiles, confidential-column aware, formula-safe, `no-store`, and audited with the format and row count. CSV streaming is preserved; XLSX auto-sizes columns; DOCX and PDF build styled tables.

# 10. Integrations

Implemented integrations: accounts, RBAC, organization teams, references, local immutable audit, and navigation/design system. Membership remains a validated-number compatibility field rather than a foreign key. Program, Project, Document Management, Notification, MEAL, and centralized Audit integrations await their domain APIs.

# 11. Database Changes

* `volunteers.0002` adds application consent/review metadata, document confidentiality, validators, indexes, and uniqueness constraints.
* `volunteers.0003` moves confidential uploads to private storage and migrates legacy files.
* `volunteers.0004` creates configurable `VolunteerCategory`/`VolunteerType`/`VolunteerLevel` taxonomies, converts profile/recruitment/application taxonomy fields to foreign keys with backfilled data, and adds `VolunteerActivityLog`, `VolunteerDisciplinaryRecord`, and `VolunteerCommunication` models plus document version/status/supersede/approval/retention columns.
* `references.0002` idempotently seeds VOL/VAP/VRC schemes.
* `references.0004` idempotently seeds the VDC disciplinary reference scheme.
* `rbac.0006` idempotently seeds volunteer permissions and operational role grants without granting confidential access to Volunteer Officer.
* `rbac.0008` idempotently seeds the Phase 13 feature permissions (`manage_activity`, `manage_disciplinary`, `manage_communications`, `manage_documents`, `configure`) and their Volunteer Officer grants.

# 12. Services

Profile, recruitment, application workflow, assignment, attendance, training, performance, recognition, leave, and exit services now validate actors, permissions, state, model constraints, audit data, and transactional boundaries. Public application submission is the only anonymous mutation.

# 13. Permissions

The module uses 20 `volunteers.*` permissions. Specific operational permissions or `volunteers.manage` authorize ordinary management. Confidential fields and files require `volunteers.view_confidential` or superuser status; module management alone does not grant confidential access. Activity, disciplinary, communication, and document management each have a dedicated permission, and taxonomy configuration is gated by `volunteers.configure`.

# 14. UI Implemented

Added public receipt, workflow forms, campaign creation, screening, interview, onboarding, confidential masking, permission-aware actions, accessible labels/errors, table captions/header scopes, and pagination. Existing dashboard, directory, profile, lists, ID card, and reports were retained. New UI surfaces: activity log registry and form, disciplinary registry/open/detail/decision forms, communication registry and form, document registry with upload/review/archive/download, category registry/create/edit, and CSV/XLSX/DOCX/PDF export buttons.

# 15. Seed Data

`seed_volunteers` is idempotent and verifies centralized volunteer reference schemes. Category, type, and level taxonomies are now database-backed, seeded by `volunteers.0004`, and manageable through the `volunteers.configure` UI. `references.0004` seeds the VDC disciplinary scheme. Code-backed skill/interest constants remain.

# 16. Files Created

* `apps/volunteers/selectors.py`
* `apps/volunteers/storage.py`
* `apps/volunteers/exports.py`
* `apps/volunteers/migrations/0002_volunteerapplication_consent_confirmed_and_more.py`
* `apps/volunteers/migrations/0003_alter_volunteerapplication_cv_file_and_more.py`
* `apps/volunteers/migrations/0004_taxonomy_and_activity_models.py`
* `apps/references/migrations/0002_seed_volunteer_reference_schemes.py`
* `apps/references/migrations/0004_seed_volunteer_disciplinary_scheme.py`
* `apps/rbac/migrations/0006_seed_volunteer_permissions.py`
* `apps/rbac/migrations/0008_seed_volunteer_feature_permissions.py`
* `apps/volunteers/templates/volunteers/application_success.html`
* `apps/volunteers/templates/volunteers/workflow_form.html`
* `apps/volunteers/templates/volunteers/includes/form_fields.html`
* `apps/volunteers/templates/volunteers/activity_log_list.html`
* `apps/volunteers/templates/volunteers/activity_log_form.html`
* `apps/volunteers/templates/volunteers/disciplinary_list.html`
* `apps/volunteers/templates/volunteers/disciplinary_form.html`
* `apps/volunteers/templates/volunteers/disciplinary_detail.html`
* `apps/volunteers/templates/volunteers/disciplinary_decision_form.html`
* `apps/volunteers/templates/volunteers/communication_list.html`
* `apps/volunteers/templates/volunteers/communication_form.html`
* `apps/volunteers/templates/volunteers/document_list.html`
* `apps/volunteers/templates/volunteers/document_form.html`
* `apps/volunteers/templates/volunteers/document_review_form.html`
* `apps/volunteers/templates/volunteers/category_list.html`
* `apps/volunteers/templates/volunteers/category_form.html`
* `apps/volunteers/tests/test_workflows.py`
* `apps/volunteers/tests/test_security.py`
* `apps/volunteers/tests/test_integrations.py`
* `apps/volunteers/tests/test_feature_services.py`
* `docs/user-guides/VOLUNTEER_MANAGEMENT_GUIDE.md`
* `docs/development/PHASE13_VOLUNTEER_MANAGEMENT_REPORT.md`

# 17. Files Modified

Volunteer models, managers, constants, validators, permissions, services, forms, views, URLs, admin, utilities, seed command/data, templates, and tests were modified. Reference/RBAC seeds, settings, dependencies, README, architecture, status, changelog, and the Phase 13 roadmap were updated.

# 18. Commands Executed

Commands included Django checks, migration drift checks, migrations, volunteer/full tests, pytest, Ruff, Black, isort, mypy, Bandit, djLint discovery, dependency installation, and seed validation. Exact final outcomes are recorded below.

# 19. Testing Results

The volunteer suite grew to 63 tests and covers models, immutable records, services, lifecycle workflows, references, activity logs, disciplinary workflows, communications, document versioning/approval/archive, taxonomy management, permission gates, own-profile scope, confidential masking, admin service enforcement, uploads, CSV/XLSX/DOCX/PDF exports, UI responses, seed idempotency, private storage, and query count.

* `python manage.py test apps.volunteers` — 63 tests passed.
* `pytest apps/references/tests apps/rbac/tests` — 96 tests passed.
* `python manage.py check` and migration drift check (`makemigrations --check`) — passed with no changes.
* Volunteer/RBAC/references Ruff — passed.
* Repository-wide lint/type/security gates — legacy findings outside the stabilized volunteer scope remain (unchanged since stabilization).

# 20. Security Review

Critical defects corrected: global PII access, fail-open services, direct writes, admin bypasses of domain services, public confidential storage, unaudited exports/downloads, local identifiers, weak upload checks, CSV injection, and incomplete model/queryset immutability. Volunteer workflow records are read-only in Django admin. Document downloads require `volunteers.view_confidential` for confidential files, and all download/export/approve/reject/archive actions are audited. Remaining risk: no application submission rate limiter.

# 21. Accessibility Review

Forms now use associated labels, required indicators, help/error relationships, non-field error alerts, semantic controls, and responsive layouts. Core updated tables include captions and scoped headings. A full browser/screen-reader audit remains part of the later accessibility phase.

# 22. Performance Review

Profile selectors use `select_related`; related lists use `profile__user`; all registries paginate; dashboard counts are aggregated; exports stream queryset iteration in chunks; indexes cover status/category, team/status, geography, audit entity, and status-history timelines. A query regression test verifies profile/user retrieval in one query.

# 23. Documentation Updated

Updated `README.md`, `ARCHITECTURE.md`, `DEVELOPMENT_STATUS.md`, `CHANGELOG.md`, and `roadmaps/13-Volunteer-Management.md`; added this report and the Volunteer Management Guide.

# 24. Problems Encountered

Phase numbering conflicted across governance documents. The RBAC data migration initially mixed current and historical Permission instances. Django private `FileSystemStorage` synthesized a media URL by default. The pinned Bandit/djLint versions did not support the installed Python 3.14 environment. A date-sensitive organization test used a now-past hard-coded date. Repository-wide lint/type failures predated this stabilization.

# 25. Problems Resolved

The detailed numbered roadmaps were selected as canonical. RBAC grants now use primary keys compatible with historical models. Private storage explicitly rejects URL generation. Data migrations are SQLite-compatible and idempotent. Bandit/djLint were upgraded for Python 3.14. The organization test now uses the current date. Both full test runners and every volunteer-scoped quality gate are green.

# 26. Known Limitations

* Application throttling is not implemented.
* Repository-wide lint, formatting, typing, and security-tool gates are not green (legacy findings outside the volunteer scope).
* Concrete organization-unit scope mappings are not available in the current RBAC schema; ordinary view-only users therefore fail closed to their own profile.
* Volunteer type and level taxonomies are configurable at the data level but do not yet have dedicated management screens; category management UI is provided as the reference pattern.

# 27. Definition Of Done Checklist

| Requirement | Status |
| --- | --- |
| Core profile and registry | Complete |
| Reference numbering | Complete |
| Application/screening/interview/onboarding | Complete |
| Assignments/attendance/training/performance | Complete |
| Recognition/leave/exit | Complete |
| RBAC/confidentiality/private files | Complete |
| Audit and status immutability | Complete within module |
| Activity/discipline/communications | Complete |
| Configurable taxonomies | Complete |
| Document version/approval/retention | Complete |
| All report formats (CSV/XLSX/DOCX/PDF) | Complete |
| Full quality gates | Incomplete (repository-wide legacy debt) |
| Documentation | Complete for current implemented scope |

# 28. Phase Status

```text
Phase 13: Candidate complete — acceptance re-review required
```

Phase 14 Stakeholder Management must not begin until the Phase 13 acceptance runbook is re-executed, all quality gates pass, and acceptance is reviewed and approved.

## Next Recommended Task

Complete the remaining Phase 13 acceptance items in `roadmaps/13-Volunteer-Management.md` (acceptance re-review, UI/performance test execution, and repository-wide quality-gate remediation as they apply to the volunteer scope), then proceed to `roadmaps/14-Stakeholder-Management.md`.
