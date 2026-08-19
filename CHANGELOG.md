# CHANGELOG

All notable changes to the **SITADC Youth Hub** project will be documented in this file.

This project follows the principles of **Keep a Changelog** and **Semantic Versioning (SemVer)**.

---

# Project Information

**Project Name:** SITADC Youth Hub

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

**Technology Stack**

* Python 3.12 or 3.13
* Django 5+
* HTML5
* CSS3
* Bootstrap 5
* JavaScript (ES6+)
* SQLite
* Git / GitHub

---

# Changelog Format

Each release should document:

* Added
* Changed
* Improved
* Fixed
* Removed
* Deprecated
* Security
* Database
* Documentation
* Performance
* Testing

---

# [Unreleased]

## Phase 30 Communication and Media – Implementation (2026-08-19)

- Implemented the Communication and Media module (`apps/communications`), per `roadmaps/30-Communication-and-Media.md`, providing a comprehensive, permission-scaled communication management platform covering core communications, announcements, news articles, newsletters with subscriber management, press releases, social media accounts and posts, campaigns with activities, media assets (images, documents, video) with albums, photographs, videos, publications, brand assets and guidelines, website pages and content sections, event communications, and an immutable activity timeline.
- Added 24 concrete models (`CommunicationRecord` abstract base + `CommunicationCategory`, `Communication`, `Announcement`, `NewsArticle`, `Newsletter`, `NewsletterSubscriber`, `PressRelease`, `SocialMediaAccount`, `SocialMediaPost`, `WebsitePage`, `WebsiteContent`, `Campaign`, `CampaignActivity`, `MediaAlbum`, `MediaAsset`, `Photograph`, `Video`, `Publication`, `BrandAsset`, `BrandGuideline`, `EventCommunication`, `CommunicationNotification`, `CommunicationTimeline`, `CommunicationAttachment`) with UUID primary keys, audit metadata, confidentiality classifications, reference numbering, and organizational scope; migration `communications.0001` applied.
- Added 6 transactional service classes (`CommunicationService`, `CampaignService`, `NewsletterService`, `MediaAssetService`, plus `create_notification`, `get_dashboard_analytics`, `allocate_reference`, `_record_timeline` helpers) covering status transitions (draft → pending_review → approved → active/archived → restored), campaign launch, newsletter distribution, media asset publishing, reference allocation, timeline recording, and dashboard analytics.
- Added fail-closed selectors and permissions (`communications.view`/`view_confidential`/`create`/`update`/`delete`/`approve`/`publish`/`archive`/`restore`/`export`/`manage`), seeded by `rbac.0024` (atomic=False) with `communications-officer` role; sidebar Communications navigation gated on `communications.view`/`manage`.
- Added 110 named routes (list/detail/create/update/delete + approve/publish/archive/restore/distribute/launch for all domains), 19 forms, and 42 Bootstrap 5 templates (`templates/communications/`) with responsive dashboards, data tables, pagination, search, and accessible forms.
- Added 11 reference numbering schemes (COM/ANN/NWS/NWL/PRS/CAM/WEB/EVC/PUB/MED/BRD) via `references.0015` (module) and `0016` (schemes) with annual reset and organization prefix.
- Added comprehensive test suite (`apps/communications/tests/`) covering models (33), permissions (12), selectors (9), services (12), forms (8), views (67) with fail-closed permission validation — all 141 tests pass.
- Added admin registration for all 24 models with custom display, filtering, search, and confidentiality-aware queryset restrictions.
- Quality gates green for `apps/communications`: ruff check, ruff format, isort, `manage.py check`, and `makemigrations --check --dry-run`.

## Phase 29 Governance, Risk, Compliance and Safeguarding – Implementation (2026-08-18)

- Implemented the Governance, Risk, Compliance and Safeguarding (GRCS) module (`apps/governance`), per `roadmaps/29-Governance-Risk-Compliance-and-Safeguarding.md`, providing a centralized, secure, transparent, and enterprise-grade governance and assurance platform covering policy management, enterprise risk management, compliance monitoring, internal controls, ethics management, safeguarding case management, incident reporting, complaint management, whistleblower management, corrective and preventive actions (CAPA), governance meetings, notifications, and timeline tracking.
- Added 25 concrete models (`Policy`, `PolicyVersion`, `PolicyAcknowledgement`, `RiskRegister`, `RiskAssessment`, `RiskTreatmentPlan`, `ComplianceRequirement`, `ComplianceAssessment`, `InternalControl`, `EthicsCase`, `ConflictOfInterestDeclaration`, `SafeguardingCase`, `IncidentReport`, `Complaint`, `WhistleblowerReport`, `CorrectivePreventiveAction`, `Document`, `GovernanceMeeting`, `MeetingAttendance`, `GovernanceNotification`, `GovernanceTimeline`) with UUID primary keys, audit metadata, confidentiality classifications, and reference numbering; migration `governance.0001` applied.
- Added 10 transactional service classes (`apps/governance/services.py`) covering policies, risks, compliance, safeguarding, incidents, complaints, whistleblower, CAPA, governance meetings, and dashboard analytics, with domain exceptions, reference generation, timeline event recording, and notification creation.
- Added fail-closed selectors and permissions (`governance.view`/`governance.manage`/`governance.view_confidential` + 18 specific permissions), seeded for existing databases by `rbac.0023` (atomic=False); sidebar Governance navigation item gated on those permissions.
- Added 76 permission-checked class-based views / 81 named routes (list/detail/create/update/delete for all domains), 22 forms, and 29 root-level Bootstrap 5 templates (`templates/governance/`) with responsive dashboards, data tables, and accessible forms.
- Added 10 reference numbering schemes (POL/RSK/CMP/ETH/SFG/INC/CPL/WHB/CAPA/MTG) via `references.0014` with annual reset and organization prefix.
- Added comprehensive test suite (`apps/governance/tests/`) covering models, services, selectors, permissions, views, and forms with fail-closed permission validation.
- Added admin registration for all 21 models with custom display, filtering, and confidentiality-aware queryset restrictions.
- Quality gates green for `apps/governance`: ruff check, ruff format, isort, `manage.py check`, and `makemigrations --check`.
- Updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 28 Finance and Resource Mobilization – Implementation (2026-08-17)

- Implemented the Finance and Resource Mobilization module (`apps/finance`), per `roadmaps/28-Finance-and-Resource-Mobilization.md`, providing chart of accounts, budgets with budget-line allocations, transactions with reference numbering and approval workflow (DRAFT/SUBMITTED/APPROVED/REJECTED/POSTED), bank accounts, petty cash, grants, donors, sponsors, fundraising campaigns, procurement and asset financial tracking, financial years, forecasts, financial statements, analytics, and reports.
- Added 15 models (`FinancialAccount`, `FinancialYear`, `Budget`, `BudgetAllocation`, `Transaction`, `BankAccount`, `PettyCash`, `Grant`, `Donor`, `Sponsor`, `FundraisingCampaign`, `ProcurementFinancialTracking`, `AssetFinancialTracking`, `FinancialForecast`, `BudgetAllocation`) with computed remaining/variance/percentage properties; migrations `finance.0003` and `finance.0004` (applied).
- Added 16 transactional services (`apps/finance/services.py`) covering accounts, budgets, transactions, grants, donors, sponsors, fundraising, petty cash, and forecasting, with domain exceptions, reference generation, and status transition validation.
- Added fail-closed selectors and permissions (`finance.view`/`finance.manage`), seeded for existing databases by `rbac.0021` (atomic=False); sidebar Finance navigation item gated on those permissions.
- Added 38 named views/routes (list/detail/analytics/report/export), 9 forms, and 55 root-level Bootstrap 5 templates (`templates/finance/`) replacing the deleted app-local template directory.
- Added analytics providers (dashboard, transactions, budgeting, analytics, grants, donors, sponsors, fundraising) and an export/renderer layer (`apps/finance/renderers`) producing PDF/DOCX/XLSX/CSV/HTML output.
- Added 46 tests in `apps/finance/tests/` (models, selectors, services, permissions, views), green in the 2026-08-17 verification run; 38 finance URLs render HTTP 200 in the smoke test.
- Quality gates green for `apps/finance`: ruff check, ruff format, isort, `manage.py check`, and `makemigrations --check`.
- Added `docs/development/PHASE28_FINANCE_REPORT.md` and updated `README.md`, `DEVELOPMENT_STATUS.md`, and `CHANGELOG.md`.

## Phase 26 Global Search — Implementation (2026-08-11)

- Implemented the Global Search module (`apps/search`), per `roadmaps/26-Global-Search.md`, providing a unified, permission-scaled search surface across all authorized modules: grouped results, entity-type refinements, per-user recent history, named saved searches (create/list/run/delete), a permission-gated CSV export, and an immutable append-only audit trail.
- Added 3 concrete models: `RecentSearch` (deduplicated history with a unique `(user, query)` constraint and prune cap), `SavedSearch` (unique `(user, name)`), and `SearchQueryLog` (append-only audit row with result count, duration and IP; updates/deletes rejected at the model and admin layers).
- Added a pluggable provider registry (`SearchProvider`/`SearchHit`/`Registry`) with 22 entity providers covering beneficiaries, documents, leadership, MEAL, meetings & calendar events, memberships, notifications, programmes & projects, registers & entries, report templates, report instances, reviews, stakeholders & partners, and volunteers; each provider delegates visibility to the source module's fail-closed selectors.
- Added fail-closed selectors and `search.view`/`search.export`/`search.manage` permissions; seeded for existing databases by `rbac.0018` (atomic=False); sidebar Search navigation item gated on `search.view`.
- Added 7 permission-checked views/7 named routes (home, export, saved list/create/delete/run, audit), 2 forms, 3 Bootstrap 5 templates, CSV export with UTF-8 BOM and sanitized cells, and client-side entity-type filtering.
- Added 59 tests in `apps/search/tests/` (permissions, validators, providers/registry, services, views), green in the 2026-08-11 verification run.
- Added `docs/development/PHASE26_GLOBAL_SEARCH_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 25 Notifications & Announcements — Implementation (2026-08-09)

- Implemented the Notifications & Announcements module (`apps/notifications`), per `roadmaps/25-Notifications-and-Announcements.md`, providing per-recipient notifications (categories, priorities, channels, preferences, quiet hours, digests), event-driven rules/templates, delivery tracking with retry/backoff and expiry, immutable audit/event records, and managed system announcements.
- Added 12 concrete models on a shared `NotificationRecord` base: `NotificationEvent` (immutable), `NotificationCategory`, `Notification`, `NotificationTemplate`, `NotificationRule`, `NotificationPreference`, `NotificationDelivery`, `SystemAnnouncement`, `AnnouncementDelivery`, `AnnouncementDismissal`, `NotificationAuditRecord` (immutable), `NotificationDigest` (plus deprecated `Announcement` proxy).
- Added 15 permission-checked service classes and 7 manager/queryset pairs; fail-closed selectors; 25 view classes/25 named routes (dashboard, inbox, actions, preferences, templates, rules, announcements, events, audit, JSON APIs).
- Wired RBAC: `notifications` (9), `announcements` (6), `preferences` (3) permission categories seeded in `seed_data` and `rbac.0017` (atomic=False); reference schemes `notification`/NTF and `announcement`/ANN via `references.0011`.
- Added notification bell badge/dropdown integration (`static/js/notifications.js`, `top_nav.html`, dashboard layout) plus the `process_notifications` management command.
- Added 121 tests in `apps/notifications/tests/`; documents/registers/notifications suites verified green in the 2026-08-10 repository verification run.
- Added `docs/development/PHASE25_NOTIFICATIONS_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 24 Calendar & Meetings — Implementation (2026-08-15)
 
- Implemented the Calendar & Meetings module (`apps/meetings`), per `roadmaps/24-Calendar-and-Meetings.md`, providing organizational calendars, events with recurrence/conflict detection, and a full meeting lifecycle (scheduling, rescheduling, participants, invitations/RSVP, versioned agendas, quorum, attendance with corrections, versioned minutes, decisions/votes, action items, matters arising, venues, templates, confidential-access logging).
- Added 26 concrete models on a shared `MeetingRecord` base, 16 service classes, a bounded recurrence engine (`recurrence.py`), fail-closed selectors, 76 view classes/81 named routes, and 30 Bootstrap 5 templates.
- Wired RBAC: `calendars` (10), `events` (14), `meetings` (36) permission categories seeded in `seed_data` and `rbac.0016` (atomic=False); 6 reference schemes (CAL/EVT/MTG/MIN/DEC/ACT) via `references.0010`; 5 management commands.
- Added 152 tests in `apps/meetings/tests/`. **Stabilization complete**: all tests pass (152/152) as of 2026-08-15. Phase 24 is now acceptance-ready.
- Added `docs/development/PHASE24_MEETINGS_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 23 Organizational Registers — Implementation (2026-08-07)

- Implemented the Organizational Registers module (`apps/registers`), per `roadmaps/23-Organizational-Registers.md`, providing configurable register categories/registers, entry templates with JSON validation, register entries with approval workflow, relationships, private attachments, review decisions, immutable version history and activity timeline, and CSV/JSON/XLSX/DOCX/PDF exports with formula-injection neutralization.
- Added 10 concrete models, 7 service classes (category/register/template/entry/validation/relationship/attachment), fail-closed confidentiality-aware selectors, 26 view classes/29 named routes, 12 `registers.*` permissions, and the `register_entry` reference scheme (prefix REG) via `references.0009` and `rbac.0013`.
- Added 88 tests in `apps/registers/tests/` (verified green in the 2026-08-10 verification run).
- Added `docs/development/PHASE23_REGISTERS_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 22 Document Management — Implementation (2026-08-07)

- Implemented the enterprise Document & Records Management module (`apps/documents`), per `roadmaps/22-Document-Management.md`, covering the full document lifecycle: upload validation, metadata, version control, checkout/check-in, review/approval/publish workflow, sharing, legal holds, retention/disposal, archive/restore, and an immutable audit trail plus chronological timeline.
- Added 15 concrete models, 29 transactional service functions, fail-closed selectors and object-level permission helpers, 34 view classes/35 named routes, and 20 Bootstrap 5 templates.
- Wired RBAC: `documents` permission category (33 actions) seeded in `seed_data` and `rbac.0012` (atomic=False); `DOC` document reference scheme; private storage, extension/MIME/size validators, SHA-256 checksums; `seed_document_data` command (21 categories, 39 types, 10 retention policies).
- Added 111 tests in `apps/documents/tests/` (verified green in the 2026-08-10 verification run).
- Added `docs/development/PHASE22_DOCUMENT_MANAGEMENT_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and `CHANGELOG.md`.

## Phase 21 Review & Approval — Implementation (2026-08-08)

- Implemented the Review and Approval module (`apps/reviews`), per `roadmaps/21-Review-and-Approval.md` (Part 1 of 4), building on the Phase 20 Report Management submission workflow.
- Added 13 concrete models: `Review`, `ReviewAssignment`, `ReviewChecklist`, `ReviewChecklistItem`, `ReviewChecklistResponse`, `ReviewComment`, `ReviewDecision`, `DigitalSignature`, `EscalationRecord`, `DelegationRecord`, `SLAConfiguration`, `SLAEvent`, `ReviewConfiguration`, with status/decision/role/comment-type/trigger enums and immutable `ReviewRecord` auditing base.
- Wired the module into the RBAC framework: added the `reviews` category (19 actions: view, create, assign, accept, start, comment, resolve_comment, update_checklist, decide, approve, reject, return_for_correction, escalate, delegate, sign, manage_checklists, manage_sla, manage_configuration, manage) to `PERMISSION_CATEGORIES` in `apps/rbac/seed_data.py`, plus `REVIEW_OPERATIONAL` / `REVIEW_REVIEWER` role groups; added `apps/rbac/migrations/0015_seed_review_permissions.py` so existing databases receive the new codes and grants (leadership = full access, coordinators/managers = reviewer set, officers = operational set, board = read-only).
- Added `MANAGE = "reviews.manage"` to `apps/reviews/permissions.py` and fixed the `apps/reviews` view layer to resolve users via `get_user_model()` instead of `from accounts.models import User` (which raised `ModuleNotFoundError` and was silently swallowed by the generic exception handler).
- Added a `get_full_name()` method to the custom `User` model (`apps/accounts/models.py`); templates and review services render reviewer names correctly.
- Built service layer covering review creation with auto-populated checklist responses, assignment/delegation/escalation, commenting and comment resolution, decisions (approve/reject/return-for-correction), SLA tracking, and digital-signature capture; fixed checklist population to include all items (removed a non-existent `is_active` filter).
- Added Bootstrap 5 views and templates: dashboard (pending/overdue/inbox), review list, review detail, assign, delegate, escalate, and decision, all with server-side `check_permission` authorization; sidebar now links the Reviews section.
- Added comprehensive test suite (99 tests) in `apps/reviews/tests/`: models (constraints, immutability, unique constraints), services (lifecycle, delegation, escalation, decisions, SLA), selectors, permissions, and views (auth, fail-closed redirects/403, assign/delegate/escalate/decide). The suite is green (99/99).
- Full repository suite: **1134/1134 passed** (previously 1035/1035 before Phase 21); `manage.py check` and `makemigrations --check --dry-run` are clean; Ruff/Black/isort green on `apps/reviews` and `apps/accounts`.
- Added `docs/development/PHASE21_REVIEW_AND_APPROVAL_REPORT.md` and updated `DEVELOPMENT_STATUS.md` (1.3.0) and the roadmap tracker.

## Phase 20 Report Management — Implementation (2026-08-08)

- Wired the `report_instances` module into the RBAC framework: added the `report_instances` category (27 actions) to `PERMISSION_CATEGORIES` in `apps/rbac/seed_data.py` and to the `_operational_base` / `_officer_base` role groups so fresh installs grant the new codes.
- Added `apps/rbac/migrations/0014_seed_report_instance_permissions.py` seeding the `report_instances` category, `Permission` rows, and role grants (leadership = full access, coordinators/managers = reviewer set, officers = operational set, board = read-only) for existing databases.
- Created the previously-missing `report_instances/report_versions.html` and `report_instances/report_version_detail.html` templates, fixing 500s on the version-history routes (`ReportVersionsView`, `ReportVersionDetailView`).
- Fixed `ReportSubmitView` to enforce `can_submit_report` instead of `can_update_report` so a `READY_FOR_SUBMISSION` report (which is not editable) can actually be submitted.
- Added a shared test scaffold (`apps/report_instances/tests/base.py`) and comprehensive suites: models (state helpers, immutability of status history/timeline, version snapshots), services (create/update/validate/submit/withdraw/return/resubmit/approve/archive/restore, evidence, attachments, comments, versions, exports, assignment, reminders, auto-save), selectors, RBAC permissions, exports, forms, and views (auth, permission-denied, lifecycle, versions, exports, JSON API).
- Repository test suite now includes **86 report-instance tests**; `apps/report_instances`, `apps/reports` (97) and `apps/rbac` (41) suites are green.
- Full repository suite: **1035/1035 passed** (previously 950/950 before Phase 20).
- Added `docs/development/PHASE20_REPORT_MANAGEMENT_REPORT.md` and updated `DEVELOPMENT_STATUS.md` and the roadmap tracker.

## Phase 19 Dynamic Report Builder — Stabilization (2026-08-08)

- Aligned the `apps/reports` test suite with the current service APIs: formula validation now expects `InvalidTemplateSchemaError`, `create_version(..., bump="major")` yields "2.0", and export uses `TemplateSchemaService.export_json`.
- Added a unique `code` to `TemplateImportService.import_json` in the import/export round-trip test (prevents UNIQUE constraint collision on `reports_reporttemplate.code`).
- `TemplatePublicationService.publish` is used directly in model tests; invalid publish now raises `TemplatePublishError`.
- Corrected the officer-create RBAC test (officer holds CREATE) and added a viewer-create denial test.
- Changed 15 reports view RBAC assertions from 302→403 so authenticated-but-unauthorized users fail closed, matching the other permission-gated modules.
- Fixed the schema-editor POST 500 by catching `DynamicTemplateError` in `SchemaDesignerView.form_valid`.
- Fixed the template-versions 500 by guarding the compare link when only one version exists.
- Rewrote `apps/report_instances/tests/test_reports.py` as a service-level workflow test (create → save responses → validate → submit, DRAFT → READY_FOR_SUBMISSION → SUBMITTED).
- Fixed the volunteers leave test to use relative dates.
- Repository test suite: **950/950 passed** (previously 926 passed / 23 failed).
- Added `docs/development/PHASE19_DYNAMIC_REPORT_BUILDER_REPORT.md` and updated `DEVELOPMENT_STATUS.md`.

## Document Management — Unified Workflow Action (2026-08-07)

- Added a unified **Workflow Action** view (`DocumentWorkflowActionView` at `documents:workflow_action`) that renders a dynamic action dropdown populated by document status and the current user's permissions.
- Available actions per status: **Submit for Review** (DRAFT/UPLOADED/RETURNED), **Approve & Forward / Return for Correction** (PENDING_REVIEW/UNDER_REVIEW), **Approve** (PENDING_APPROVAL), **Publish** (APPROVED), **Unpublish** (PUBLISHED), **Archive** (non-archived), **Restore** (ARCHIVED).
- Each action dispatches to the corresponding service (`submit_for_review`, `review_document`, `approve_document`, `publish_document`, `unpublish_document`, `archive_document`, `restore_document`) with optional comments and full audit/timeline recording.
- Updated `document_detail.html` action sidebar to route all workflow buttons through the unified page instead of separate POST-only endpoints.
- Added `DocumentWorkflowActionForm` with `action` ChoiceField and optional `comments` field; `action_choices` computed via `_available_workflow_actions(user, document)`.
- Added "Create New Folder" and "Browse Folders" quick links under the Classification section of the upload form.
- Added `DocumentWorkflowActionViewTests` (9 tests covering GET/POST for each action, permission filtering, and viewer access) to `apps/documents/tests/test_views.py`.
- Fixed `_available_workflow_actions` to use `gettext_lazy`; manager test user granted `RETURN_FOR_CORRECTION` permission.

## Phase 18 MEAL — Implementation (2026-08-05)

- Implemented Phase 18 MEAL in the new `apps/meal` app per `roadmaps/18-MEAL.md`: the centralized monitoring, evaluation, accountability and learning platform (35 models).
- Added Theory of Change, Results Frameworks, and Logical Frameworks (logframes) with result statements and logframe rows.
- Added the centralized Indicator registry with categories, baselines, targets, and actual results, plus data collection (plans, sources, tools, submissions).
- Added monitoring (plans, visits, findings, corrective actions), evaluations and recommendations, and Data Quality Assessments (DQA) with dimension scores.
- Added accountability (complaints, feedback, corrective actions), learning (outcome harvesting, learning logs, best practices, lessons learned), organizational KPIs, performance scorecards with dimensions, and MEAL reports with an executive dashboard.
- Added 11 transactional, permission-checked service classes and fail-closed permission helpers (`user_can_view_meal`, `user_can_manage_meal`, `user_can_view_confidential`) with the `MealPermissionMixin` applied to every view.
- Added the `meal` RBAC permission category (22 actions) with operational role grants (`rbac.0010`) and 21 reference-numbering sub-schemes (TOC/RFR/LGF/IND/BSL/TGT/DCP/MNP/MON/EVL/DQA/CMP/FDB/CRA/OCH/LLG/BPR/LSN/SCR/MRL/KPI) under the new `meal` reference module (`references.0008`).
- Added 36 forms, 87 permission-checked CBV routes (82 paths), and 13 Bootstrap 5 templates (dashboard, indicator registry, framework profile, entity directory/detail/form, monitoring visit, scorecard, complaint/feedback, workflow forms).
- Added formula-safe CSV register exports plus XLSX/DOCX/PDF report export; uploads use private storage with type/size validation and metadata tracking.
- Registered `apps.meal` in settings/URLs and added the sidebar navigation entry gated by `meal.view`/`meal.manage`.
- Added 61 tests in `apps/meal/tests/`; the full `apps/meal` suite is green (61/61) and the repository suite is green (483/483).
- Quality gates green on `apps/meal`: Ruff, Black, isort, mypy (whole `apps` tree), `manage.py check`, and `makemigrations --check`.

## Phase 17 Beneficiary Management — Implementation (2026-08-05)

- Implemented Phase 17 Beneficiary Management in the new `apps.beneficiaries` app per `roadmaps/17-Beneficiary-Management.md`: the official, consent-governed beneficiary registry with a validated lifecycle (IDENTIFIED → REGISTERED → VERIFIED → ENROLLED → ACTIVE → GRADUATED, plus SUSPENDED/EXITED).
- Added 27 concrete models covering the beneficiary profile, households, groups, enrollments, participations, attendance, service delivery, referrals, role-based case notes, assessments, follow-up visits, safeguarding records, support plans, outcomes, exits, transfers, consent records, guardians, confidential documents, communications, feedback, duplicate review, immutable status history, and audit records.
- Added consent governance: `ConsentService.record` is the only write path; adults require recorded consent and minors require guardian consent plus child assent before VERIFIED and later statuses.
- Added 22 transactional, permission-checked service classes and fail-closed selectors (`visible_beneficiaries`, `user_can_access_beneficiary`, `visible_beneficiary_documents`) enforcing confidentiality levels and scope-based access.
- Added the `beneficiaries` RBAC permission category (32 actions) with operational role grants (`rbac.0009`), 16 reference-numbering sub-schemes (HHL/GRP/ENR/PRT/ASS/RFL/SRV/CSE/SPL/EXT/TRF/BND/CNS/SFG/OUT/FDB) and the base `beneficiary` (BEN) scheme (`references.0006`/`0007`).
- Added 36 forms, 56 permission-checked CBV routes, and 12 Bootstrap 5 templates (dashboard, directory, profile, households, groups, related records, workflow forms).
- Added formula-safe CSV register export plus XLSX/DOCX/PDF register and profile exports; document uploads use private storage with type/size validation and metadata tracking.
- Registered `apps.beneficiaries` in settings/URLs and added the sidebar navigation entry gated by `beneficiaries.view`/`beneficiaries.manage`.
- Added 91 tests in `apps/beneficiaries/tests/`; the full `apps/beneficiaries` suite is green (91/91).
- Quality gates green on `apps/beneficiaries`: Ruff, Black, isort, mypy (full `apps` tree), Bandit, djLint, `manage.py check`, and `makemigrations --check`.

## Phase 16 Project Management — Implementation (2026-08-05)

- Implemented Phase 16 Project Management within `apps/programs`, closing the gaps identified after Phase 15 acceptance per `roadmaps/16-Project-Management.md`.
- Added operation models: `WBSNode`, `ProjectResult`, `BeneficiaryParticipation`, `ProjectTimeline`, `ProjectClosure`, `ProjectReport`, `EvidenceVersion`; extended `Project` with a `classifications` M2M (`PROJECT_CLASSIFICATION`) and derived `completion_percentage`.
- Extended workflow models: `Milestone`/`Deliverable` submission and approval fields, `EvidenceRecord` versioning, `ChangeRequest` decision fields (`target_model`, `target_field`, `target_record_id`, `proposed_value`, `reviewer`, `reviewer_notes`, `reviewed_at`).
- Added `PROJECT_CLASSIFICATION` taxonomy seed (16 rows with `area` metadata) and the `wbs` reference-numbering scheme.
- Added transactional services: `WbsService`, `ProjectApprovalService`, `ProjectClosureService`, `ProjectResultService`, `BeneficiaryParticipationService`, `ProjectTimelineService`, `EvidenceService.upload_version`, `ProjectReportService`, `ProjectAnalyticsService`, and `ChangeRequestService.decide` (approve/reject with auto-apply).
- Added permission-checked views, URLs, and Bootstrap 5 templates for WBS tree, results, timeline, beneficiary participation, closure workflow, reports, analytics, milestone/deliverable approval, change-request decisions, and project report exports (CSV/XLSX/DOCX/PDF).
- Enabled `classifications` M2M handling in `ProjectService.create`/`update` (service-side field allow-list now includes many-to-many fields).
- Fixed `ProjectAnalyticsService` to derive budget utilization from `Project.budget_approved`/`budget_utilized` and project task counts through `activity__work_plan__project`.
- Registered all new operation models with `ServiceManagedAdmin` and added 22 Phase 16 tests; full `apps/programs` suite green (112 tests).
- Quality gates green on `apps/programs`: Ruff, Black, isort, mypy, Bandit, djLint, `manage.py check`, and `makemigrations --check`.

## Phase 15 Formal Acceptance (2026-08-04)

- Completed the external acceptance pack, acceptance validation, runbook, and delivery report for Phase 15 in `docs/development/PHASE15_*`; Phase 15 Program & Project Management is formally accepted (2026-08-04).
- Re-verified acceptance evidence: program tests (91), full pytest suite (479), Django system checks, migration drift, seed idempotency, Ruff, Black, isort, mypy, djLint, Bandit, ESLint, Stylelint, Prettier, and pre-commit.
- Resolved the remaining repository-wide quality findings in `apps/programs` (Ruff, Black, isort, mypy, djLint) so all gates pass repository-wide.
- `DEVELOPMENT_STATUS.md` updated to mark Phase 15 as Accepted.

## Phase 15 Program & Project Management — Stabilization (2026-08-03)

- Resolved the remaining 15 repository-wide mypy findings against `apps/programs` without broadening suppression: narrowed `forms.ModelChoiceField` references via the existing `_model_choice(...)` helper, replaced the unused `# type: ignore[index]` with the correct `[attr-defined]` code on the `_relax_defaulted_fields` mixin, and switched `User.get_full_name()` to `User.full_name` (the property actually exposed by `apps.accounts.models.User`).
- Documented the non-generic `ProgramManager` / `ProjectManager` re-declarations with a focused `# type: ignore[assignment]` to satisfy the base `SoftDeleteManager[Program]` / `SoftDeleteManager[Project]` constraint until `models.Manager` exposes a generic interface upstream.
- Reformatted `apps/programs/views.py` with Black and isort to restore the repository quality baseline.
- Re-verified the full repository: 479/479 pytest tests, Ruff, Black, isort, mypy, Bandit, and `manage.py check` all pass.
- Phase 15 implementation, services, selectors, validators, permissions, RBAC integration, exports, and seed command remain unchanged from the prior implementation pass.

## Phase 13 Formal Acceptance (2026-08-03)

- Completed the independent quality-assurance review and external acceptance pack for Phase 13 in `docs/development/PHASE13_EXTERNAL_ACCEPTANCE_PACK.md`; the quality-assurance checklist item in `roadmaps/13-Volunteer-Management.md` is closed.
- Re-verified all acceptance evidence independently: volunteer tests (63), full pytest suite (389), Django system checks, migration drift, seed idempotency, Ruff, Black, isort, mypy, djLint, Bandit, ESLint, Stylelint, Prettier, and the runnable Playwright axe/accessibility suite (4 passed, 1 skipped).
- Phase 13 Volunteer Management is formally accepted (2026-08-03); `DEVELOPMENT_STATUS.md` updated and Phase 15 Program Management is now the active phase.
- Tracked remaining deferred items: application submission throttling, full browser UI test suite, and full performance benchmark suite to their owning later phases.

## Phase 13 Acceptance Re-Review (2026-08-03)

- Completed the Phase 13 acceptance re-review recorded in `docs/development/PHASE13_ACCEPTANCE_REVIEW.md`; all volunteer tests (63), references/RBAC tests (96), and the full pytest suite (389) pass.
- Restored repository-wide quality gates to green: reformatted eight volunteer files with Black, corrected `views.py` import ordering with isort, resolved 11 mypy findings, and reformatted four volunteer templates with djLint.
- Fixed a genuine defect in the volunteer document-rejection path where the review view passed a non-existent `reason=` parameter instead of the service's `notes=` parameter.
- Annotated optional export-library imports (openpyxl, reportlab) for mypy and added scoped ignores for the stakeholder form mixin and the load-probe handler list.
- Installed declared export dependencies (openpyxl, python-docx, reportlab) that were missing from the development environment.
- Verified Django system checks, migration drift, seed idempotency, bandit (zero findings), and frontend ESLint/Stylelint/Prettier gates.
- Phase 13 checklist updated to mark repository-wide quality gates and acceptance criteria as satisfied; status is candidate complete pending formal organizational sign-off.

## Phase 14 Acceptance Remediation (2026-08-03)

- Fixed completed due-diligence form validation so authenticated reviewer metadata is applied before model validation.
- Fixed dynamic transition choices being validated before they were populated.
- Added CDN-independent, keyboard-accessible profile tab behavior and a visible permission-aware Archive action.
- Protected the dashboard preview behind authentication.
- Added PostgreSQL 18 acceptance settings, concurrency and authenticated-load probes, and completed local migration/concurrency validation.
- Completed interactive manual NVDA and stakeholder UAT checks; named signatures remain outstanding.
- Increased the stakeholder suite to 73 tests and the full pytest suite to 359 passing tests.
- Completed manual NVDA, stakeholder UAT, privacy/security, PostgreSQL concurrency, and target LAN HTTPS sustained-load acceptance; Teddy James electronically approved Phase 14.

## Added

### Phase 14: Stakeholder Management Implementation (2026-08-02)
- Added `apps.stakeholders` with 25 models for profiles, lifecycle history, contacts, assessments, engagement, communications, agreements, renewals, commitments, contributions, due diligence, conflicts, risks, scorecards, actions, notes, documents, duplicate review, and access grants.
- Added configurable taxonomies with 241 seeded reference rows across 24 kinds and seven weighted performance dimensions.
- Added eight centralized reference schemes: STK, SEG, SAG, SCM, SCN, SAS, SPF, and SDD.
- Added 35 `partners.*` RBAC permissions with operational partnerships/resource-mobilization grants and focused legal/governance grants.
- Added fail-closed selectors for profile, directory, assigned/owned, explicit time-bound grant, private-contact, and private-document access.
- Added explicit stakeholder transitions, reasoned archive/restore, verification metadata, and immutable status history.
- Added influence/interest mapping using `>= 3` as high, four quadrants, insufficient-data output, completeness, and no imputation.
- Added engagement plans, meetings/consultations, communication history, commitments, contribution verification, due diligence, conflicts, and likelihood-impact risks.
- Added agreement review/approval/signature/activation/expiry/termination/renewal, immutable versions, current due-diligence activation checks, and self-approval prevention.
- Added normalized weighted scorecards with weight snapshots, missing-dimension disclosure, completeness, and no imputation.
- Added versioned notes, private checksummed documents, legal hold, controlled downloads, upload validation, and formula-safe scoped CSV.
- Added an operational permission-scoped module dashboard, specialized directories, mapping matrix, profile workspaces, reports, 47 named routes, and 12 Bootstrap templates.
- Added four commands for seeding, validation, agreement expiry checks, and overdue action checks.
- Added 70 stakeholder tests covering models, services, permissions, security, commands, UI, pagination, and bounded query count.
- Added supported-runtime documentation for Python 3.12-3.13 with Django 5.0.7.
- Added frontend lint and formatting validation using the declared npm dependencies.
- Added repository quality baseline and stable integration-boundary documentation for Phase 14 acceptance.
- Added Playwright/axe accessibility tests and a Phase 14 acceptance validation checklist.

### Repository-wide typing remediation (2026-08-02)
- Resolved all repository mypy diagnostics without broad suppression, including Django manager generics, form field narrowing, translated seed data, nullable model relations, and custom view attributes.
- Verified the full Python 3.13 test suite (355 tests) and Django system checks.

Phase 14 is accepted. Central Audit and Dashboard apps remain absent; domain histories/versions, structured logging, and the module dashboard do not constitute those central integrations. CSV is operational; PDF/DOCX/XLSX and Program/Project, Finance, Notification, Approval, and central Document integrations remain deferred to their owning phases.

Current validation: stakeholder tests 73/73, pytest 359/359, stakeholder coverage 76% overall (models 93%, services 71%, views 59%), Django deployment checks, PostgreSQL 18 migrations/concurrency, target LAN HTTPS load, repository Python quality gates, stakeholder security/template gates, and frontend lint/format checks pass.

The user explicitly authorized implementation despite the master-roadmap discrepancy and incomplete Phase 13 gate. This did not complete Phase 13 or make Phase 15 ready.

### Phase 12: Membership Management Implementation (2026-08-02)
- Implemented the `memberships` module serving as the official membership registry: applications, registration, approval workflow, renewals, upgrades, transfers, suspensions, terminations, exit & alumni.
- Created configurable, DB-backed `MembershipCategory`, `MembershipType`, `MembershipLevel`, `MembershipStatus`, `MembershipBenefit`, and `RenewalRule` (no code changes required to manage configuration).
- Created `MemberProfile` with full personal/contact/emergency/membership fields, profile visibility, consent and responsibilities acknowledgement.
- Created `MembershipCard` with unique card numbers, 16-character verification codes, issue/revoke lifecycle, and QR-code generation for digital and printable membership IDs.
- Implemented engagement tracking: `MembershipAttendance`, `MemberParticipation`, `MemberCommittee`/`MemberCommitteeAssignment`, `MemberSkill`, `MemberInterest`, `MemberTrainingRecord`, `MemberRecognition`, `MemberLeave`, confidential `MemberComplaint`, and `MemberDisciplinaryRecord`.
- Implemented fee and payment management: `MembershipFee`, `MembershipPayment` (with receipts), and `MembershipFeeAdjustment` (discounts/waivers).
- Added `MembershipDocument` (versioned, confidentiality levels), `MembershipCommunication`, and `MemberBenefitAssignment`/`MemberOrganizationAssignment`.
- Created immutable `MembershipStatusHistory` and `MembershipAuditRecord` (updates/deletes raise `ValidationError`; admin read-only).
- Built transactional service layer: 15 services covering application, registration, status, renewal, upgrade, transfer, payment, fee adjustment, card, participation, committee, recognition, leave, exit, and analytics.
- Integrated `ReferenceNumberService` for `MEM` (members), `APL` (applications), `RCT` (receipts), and `CRD` (cards).
- Configured the `membership` RBAC permission category (28 actions) and granted `membership-officer` role via migration `rbac.0005`.
- Scaffolded 15 Bootstrap 5 templates (dashboard, directory, profile tabs, applications, renewals, transfers, payments, cards, leave, exit, id-card, reports).
- Added `seed_memberships` management command (7 statuses, 5 categories, 3 types, 5 levels, 6 benefits; idempotent).
- Developed comprehensive test suite (`test_models`, `test_services`, `test_views`) demonstrating lifecycle, immutability, permission, and validation coverage.
- Full test suite green: **100 tests OK** (49 in `apps/memberships`).

### Phase 13: Volunteer Management Stabilization (2026-08-02)
- Replaced local/timestamp application identifiers with centrally reserved and confirmed `VOL`, `VAP`, and `VRC` reference schemes.
- Added validated and audited recruitment, screening, interview, approval, registration, onboarding, assignment, leave, and exit transitions.
- Routed profile and operational web writes through transaction-backed services with fail-closed actor permissions.
- Added permission-aware selectors, own-profile fallback access, confidential-field masking, scoped form choices, and optimized related queries.
- Made volunteer audit, status, and deployment history records reject instance and queryset mutation through supported application APIs.
- Added upload size, extension, MIME, and signature validation; moved CVs, certificates, and documents outside public media storage; added permission-checked audited CV downloads.
- Hardened CSV exports against spreadsheet formulas, scoped rows and confidential columns, disabled response caching, and recorded export audits.
- Added accessible public receipt/workflow forms, labels, required indicators, error summaries, table semantics, and pagination.
- Added RBAC and reference data migrations, idempotent volunteer seeding, QR-code dependency, database indexes, uniqueness constraints, and score/hour validators.
- Made volunteer workflow records read-only in Django admin so privileged users cannot bypass audited domain services.
- Expanded the volunteer suite to 32 model, service, workflow, security, view, seed, storage, and query-regression tests.
- Phase 13 remains incomplete pending activity/disciplinary workflows, configurable taxonomies, full document lifecycle, PDF/DOCX/XLSX reports, and repository-wide quality-gate remediation.

### Phase 13: Volunteer Management Feature Completion (2026-08-03)
- Added configurable `VolunteerCategory`/`VolunteerType`/`VolunteerLevel` database taxonomies, converted profile/recruitment/application taxonomy fields to foreign keys, and backfilled existing records via `volunteers.0004`.
- Added `VolunteerActivityLog` with activity categories, hours/beneficiary tracking, private evidence uploads, and future-date/hour-bound validation.
- Added `VolunteerDisciplinaryRecord` with centralized `VDC` references (`references.0004`), open/decide/reopen workflow, and profile consequences (suspension, dismissal).
- Added `VolunteerCommunication` records with configurable channels and audited send trail.
- Extended `VolunteerDocument` with versioning, supersede chains, pending-approval/approved/rejected/archived status, approval metadata, and retention dates; added approve/reject/archive services and permission-checked secure downloads.
- Added taxonomy management UI behind `volunteers.configure`; activity, disciplinary, communication, and document management views/forms/templates.
- Added PDF (reportlab), DOCX (python-docx), and XLSX (openpyxl) volunteer register exports alongside CSV; all audited and confidentiality-aware; dependencies pinned in `requirements/base.txt`.
- Added five feature permissions (`manage_activity`, `manage_disciplinary`, `manage_communications`, `manage_documents`, `configure`) and Volunteer Officer grants via `rbac.0008`.
- Grew the volunteer suite to 63 tests including new service, view, and security coverage for all feature surfaces; references/RBAC suites remain green (96 tests).

### Branding Asset Integration (2026-08-01)
- Integrated official SITADC Youth Organization logo across all application layouts (auth, dashboard, public, print).
- Configured `.homepage-hero` component with the official background image.
- Implemented global `branding_context` processor to centralized organization branding details.
- Fixed SITADC Logo Sizing, Alignment, and Responsiveness.
- Implemented `.brand-logo-wrapper` and `.brand-logo` base classes preserving the natural 1:1 aspect ratio of the 2048x2048 logo without distortion or cropping.
- Defined specific sizing variants (`.navbar-brand-logo`, `.sidebar-logo`, `.homepage-logo`, `.auth-logo`, `.app-logo--print`) for responsive rendering on desktop, tablet, and mobile.
- Enforced accessibility with ARIA labels and consistent branding display.
- Replaced the deprecated `SITADC_logo.png` file references with the official `app_logo.png` asset across the entire application (context processors, templates, and documentation).
- Documented future report export dimensions constraints (pending Phase 09 completion).

### Phase 09: Reference Numbering System (2026-08-01)

* Created the `apps/references` Django application implementing the centralized, configurable reference numbering system.
* Added `ReferenceNumberScheme`, `ReferenceSequence`, `GeneratedReferenceNumber`, and `ReferenceNumberAuditRecord` models with immutable registry/audit enforcement and DB-level uniqueness on `reference_number` and `(scheme, period_key, sequence_value)`.
* Added the token engine (`apps/references/numbering.py`) supporting `{PREFIX}`, `{ORG}`, `{MODULE}`, `{TYPE}`, `{UNIT}`, `{DIRECTORATE}`, `{REGION}`, `{DISTRICT}`, `{COMMUNITY}`, `{TEAM}`, `{PROGRAM}`, `{PROJECT}`, `{YEAR}`, `{YEAR_SHORT}`, `{MONTH}`, `{DAY}`, `{FY}`, and `{SEQUENCE}` tokens.
* Added scheme resolution (explicit code -> record-type default -> module default -> fallback) with `MissingNumberingContextError` and `InactiveNumberingSchemeError` exceptions.
* Added sequence reset policies (Never, Annually, Monthly, Daily, Fiscal, Custom) with per-period counters and preview that does not consume sequence values.
* Added `ReferenceNumberService` with transaction-scoped `select_for_update()` increment, registry insertion, and bounded retry (max 5 attempts).
* Added lifecycle management services for schemes (create, update, activate, deactivate, archive, restore) and reference numbers (confirm, cancel, void, manual correction, sequence reset).
* Added scheme, registry, sequence, preview, and audit views with templates under `apps/references/templates/references/`.
* Registered models in Django admin with read-only immutable registry/audit handling.
* Added `reference_numbers` permission category (9 actions) to the RBAC catalogue with seed migration `0003_seed_reference_numbers_permissions`.
* Added seed data for 16 default schemes (USR, MEM, VOL, LDR, RPT, DOC, PRG, PRJ, EVT, AST, FIN, MTG, GRT, PAR, DON, BEN) with default pattern `{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}`.
* Added management commands: `seed_reference_schemes`, `validate_reference_schemes`, and `preview_reference_number`.
* Added 55 tests covering models, numbering engine, services, and views.

### Phase 08: Organizational Structure - Stabilization (2026-08-01)

* Added `coerce_date()` helper in `apps/organizations/validators.py` to normalize ISO date strings and `datetime` objects to `date` for validation and audit logging.
* Added `with_parent()` to `OrganizationUnitManager` and `with_unit()` to `PositionManager`.
* Added `has_perm` filter to `apps/rbac/templatetags/rbac_tags.py` for permission checks inside `{% if %}` expressions.

### Phase 04: Authentication and Accounts - Stabilization (2026-07-31)

* Added regression tests for the full password reset workflow (request OTP, verify OTP, confirm new password) and verification-gated password reset confirmation.
* Added test covering unverified access to the password reset confirmation endpoint.

### Phase 05: UI Design System and Layouts (2026-07-31)

* Designed global UI system aligned with SITADC brand guidelines (Blue/Indigo/Cyan primary, Emerald success, Orange action).
* Created core layout architecture (`base.html`, `public.html`, `auth.html`, `dashboard.html`, `full_width.html`, `error.html`, `print.html`).
* Developed reusable navigation components (`sidebar.html`, `top_nav.html`, `user_menu.html`, `breadcrumbs.html`).
* Added UI placeholders for Authentication screens (`login.html`, `forgot_password.html`, `reset_password.html`).
* Re-designed error pages (`400`, `403`, `404`, `500`) to match brand aesthetic.
* Centralized static assets logic (`design-system.css`, `app.js` with bootstrap component initialization).

### Phase 04: Database Architecture (2026-07-31)

* Implemented abstract base models (`UUIDModel`, `IsActiveModel`, `NotesModel`, `BaseModel`)
* Implemented unified base managers and querysets (`BaseManager`, `BaseQuerySet`)
* Refactored existing soft-delete querysets and managers into `apps.core.managers`
* Updated mixins for core database abstractions (`UUIDMixin`, `IsActiveMixin`, `NotesMixin`, `BaseMixin`)
* Verified database architecture for SQLite compatibility and future PostgreSQL migration
* Maintained alignment with clean modular architecture

### Phase 03: Core System Architecture (2026-07-31)

* Implemented abstract base models (`TimeStampedModel`, `CreatedByModel`, `UpdatedByModel`, `SoftDeleteModel`, `ArchivableModel`, `StatusModel`)
* Implemented shared mixins (`OwnershipMixin`, `PermissionMixin`, `ExportMixin` etc.)
* Created foundational service, selector, and validator layers
* Configured core middleware (`RequestIDMiddleware`, `CurrentUserMiddleware`, `SecurityHeadersMiddleware`, etc.)
* Configured core exception classes and business rules
* Configured centralized logging architecture

### Phase 02: Development Environment & Tooling (2026-07-31)

* Configured **Ruff** for Python linting (rules: E, F, W, I, B, UP, SIM, DJ, C4, PIE, RUF)
* Configured **Black** for Python code formatting (line-length: 88, target: py312)
* Configured **isort** for import ordering (profile: black)
* Configured **mypy** for gradual static type checking with django-stubs
* Configured **pytest** and **pytest-django** as the primary test runner
* Configured **coverage** for test coverage measurement (source: apps)
* Configured **Bandit** for security vulnerability scanning
* Configured **djLint** for Django template linting and formatting
* Configured **ESLint** for JavaScript linting (eslint.config.js, flat config)
* Configured **Prettier** for JavaScript and CSS formatting
* Configured **Stylelint** for CSS linting with standard config
* Created **pre-commit** hook configuration (`.pre-commit-config.yaml`)
* Created **GitHub Actions** CI workflow (`.github/workflows/ci.yml`)
* Created cross-platform developer scripts: `setup.sh/ps1`, `quality.sh/ps1`, `test.sh/ps1`
* Created **Dockerfile** and **docker-compose.yml** for containerized development
* Created **`.dockerignore`** to keep Docker image clean
* Created developer documentation: `DEVELOPMENT_ENVIRONMENT.md`, `WINDOWS_SETUP.md`, `LINUX_SETUP.md`, `MACOS_SETUP.md`, `COMMON_COMMANDS.md`
* Created `docs/testing/TESTING_GUIDE.md` and `docs/security/SECURITY_CHECKS.md`
* Created `package.json` with npm scripts for frontend quality tools

### Phase 01: Project Foundation (Previously completed)

* Django project initialization
* Core application structure
* Base templates with Bootstrap 5 integration
* Custom error pages (400, 403, 404, 500)
* Environment configuration system
* `apps/core` Django application

## Changed

* Completed Phase 1: Project Foundation

## Improved

* UserProfile `preferred_language` and `time_zone` are now optional in the profile form while retaining their database defaults.
* Clarified the BaseModel manager ordering with a `noqa` note; `objects` remains the default manager.

## Fixed

* Fixed `NameError` in password reset confirmation (`transaction` was used without being imported in `apps/accounts/views.py`).
- Fixed stakeholder `CheckConstraint` declarations and migration serialization for Django 5.0.7.
- Replaced insecure OTP pseudo-random generation with `secrets`.
- Fixed repository Ruff, Black, and isort compliance through safe automated cleanup and explicit Django declarative exceptions.
- Fixed production deployment checks by filtering empty CSRF origin configuration and validating production settings separately from development settings.
* Fixed password reset success message to interpolate the terminated-session count instead of passing a dict as `extra_tags`.
* Fixed profile update validation failure when `preferred_language` / `time_zone` were omitted.
* Resolved `mypy` errors across `managers.py`, `forms.py`, and `views.py`.
* Resolved 90+ Ruff lint issues (import ordering, unused imports, line length, `raise ... from`, `ClassVar` annotations, implicit `Optional`, etc.) across `apps` and `config`.
* Updated the stale Phase 5 placeholder test for password reset confirmation to match the secure verification-first behavior.

## Removed

*

## Deprecated

*

## Security

* Scoped Bandit scans pass with no findings when generated environments and migrations/tests are excluded.

## Database

* Added migration `accounts.0003` making `UserProfile.preferred_language` and `UserProfile.time_zone` optional (`blank=True`).

## Documentation

* Added the Stakeholder Management user guide and the 32-section Phase 14 delivery report.
* Documented the incomplete acceptance status, exact quality-gate results, SQLite limits, and deferred integration boundaries without marking Phase 15 ready.
* Corrected the stakeholder UI inventory to 47 named routes and documented all models, services, selectors, seed sets, migrations, permissions, templates, forms, commands, and implementation files.
* Added repository quality baseline and integration-boundary documentation.

## Performance

*

## Fixed

### Phase 08: Organizational Structure (2026-08-01)

* Fixed `TypeError` in `validate_transfer_dates`/`validate_acting_dates` when services received ISO date strings instead of `date` objects.
* Fixed `AttributeError` from `OrganizationUnitManager.with_parent` and `PositionManager.with_unit` not exposing queryset helpers.
* Fixed `FieldError` in `PositionQuerySet.with_unit()` referencing a non-existent `reports_to` relation.
* Fixed infinite template recursion caused by a literal `{% include %}` inside an HTML comment in `templates/components/empty_state.html`.
* Fixed invalid `{% if has_permission 'code' %}` template syntax (a `simple_tag` cannot be called with args inside `{% if %}`) by switching to the new `|has_perm` filter across organization templates.
* Fixed `VacancyForm` failing validation because required `date_vacant` had no form default despite the model default.
* Removed unused `PositionClassification` import in `apps/organizations/models.py` that shadowed the model class (Ruff F811).

## Testing

* Full suite: 116 tests passing (was 106 passing / 10 failing before stabilization).
* `pytest` (116) and `ruff check`/`ruff format` all pass; remaining mypy findings are pre-existing in the newer `apps/organizations` module and tracked as pending work.
* Full pytest suite passes with 355 tests under Python 3.13 and Django 5.0.7.
* Frontend ESLint, Stylelint, and Prettier checks pass.
* Production `manage.py check --deploy` passes with ephemeral test configuration; migration drift checks pass.
* Playwright/axe: 4 automated accessibility tests passed.
* Pre-commit: all configured hooks passed from the local Git checkout.

---

# Version 1.0.0 - Initial Production Release

**Release Date:** YYYY-MM-DD

## Added

### Core Platform

* Complete authentication system
* Invitation-based registration
* OTP verification
* Multi-factor authentication
* Session management
* Role-Based Access Control (RBAC)

### Dashboard

* User dashboard
* Leadership dashboard
* Administrator dashboard
* Executive dashboard
* Analytics dashboard

### Leadership Management

* Leadership profiles
* Organizational hierarchy
* Performance scorecards
* Succession planning

### Membership Management

* Member registration
* Membership approval
* Membership reporting

### Volunteer Management

* Volunteer profiles
* Deployment tracking
* Attendance management
* Skills management
* Performance tracking

### Beneficiary Management

* Beneficiary registration
* Case management
* Confidential records

### Program Management

* Program profiles
* Project management
* Activities
* Milestones
* Budgets
* Risks
* Outcomes

### MEAL

* Results frameworks
* Indicators
* Baselines
* Targets
* Monitoring visits
* Evaluations
* Learning logs

### Report Management

Implemented all organizational reporting categories:

* Governance Reports
* Leadership Reports
* Program Reports
* Membership Reports
* Volunteer Reports
* MEAL Reports
* Finance Reports
* Communication Reports
* Training Reports
* Research Reports
* Partnership Reports
* Community Reports
* Quality Assurance Reports
* Risk & Compliance Reports
* Organizational Learning Reports
* Organizational Registers

### Document Management

* Document uploads
* Version control
* Search
* Preview
* Downloads
* Metadata
* Confidentiality controls

### Organizational Registers

* Membership Register
* Volunteer Register
* Beneficiary Register
* Stakeholder Register
* Partner Register
* Donor Register
* Asset Register
* Risk Register
* Issue Register
* Complaints Register
* Policy Register
* Meeting Register
* Event Register
* Media Register
* Grant Register
* Proposal Register

### Notifications

* Email notifications
* In-app notifications
* Approval reminders
* Report reminders
* System alerts

### Audit Logging

* Login history
* Activity history
* Approval history
* Export history
* User actions

---

## Changed

* Initial enterprise release.

---

## Improved

* User experience
* Navigation
* Dashboard responsiveness
* Accessibility
* Reporting workflows
* Organizational collaboration

---

## Fixed

* Initial production release.

---

## Removed

* None.

---

## Deprecated

* None.

---

## Security

* Row-Level Security implemented
* Audit logging enabled
* Secure authentication
* Secure file storage
* Password encryption
* Session timeout
* Permission validation

---

## Database

* Enterprise database schema deployed.
* Initial production migration completed.
* Seed data successfully loaded.

---

## Documentation

Completed:

* README.md
* AGENTS.md
* ARCHITECTURE.md
* DEVELOPMENT_STATUS.md
* CHANGELOG.md
* API Documentation
* User Manual
* Administrator Guide
* Developer Guide
* Deployment Guide
* Disaster Recovery Guide

---

## Performance

* Performance optimized.
* Database indexing completed.
* Query optimization completed.
* Caching configured.

---

## Testing

Completed:

* Unit Tests
* Integration Tests
* System Tests
* User Acceptance Testing
* Security Testing
* Performance Testing
* Accessibility Testing
* Regression Testing

---

# Version History

| Version | Date       | Status     | Description                |
| ------- | ---------- | ---------- | -------------------------- |
| 1.0.0   | 2026-08-05 | Development | Phase 18 MEAL implemented (`apps/meal`, 61 tests, 483 repository-wide) |
| 1.1.0   | 2026-08-07 | Development | Phase 22 Document Management implemented (`apps/documents`, 88+ tests) |

---

# Upgrade Procedure

For every release:

1. Update the version number.
2. Record the release date.
3. Document all changes under the appropriate sections.
4. Update database migration references.
5. Update documentation references.
6. Record security updates.
7. Record breaking changes.
8. Record deprecated features.
9. Commit the updated CHANGELOG.md before tagging the release.
10. Create a Git tag matching the release version.

---

# Release Approval

Each production release should include approval from:

* Project Lead
* Technical Lead
* Quality Assurance Lead
* DevOps Lead
* Executive Director
* System Administrator (Production Release)
* Board of Trustees (Major Releases)

---

# Release Status Definitions

* **Planned** – Scheduled but not yet implemented.
* **In Progress** – Currently under development.
* **Testing** – Under quality assurance and validation.
* **Release Candidate (RC)** – Feature complete and awaiting final approval.
* **Production** – Successfully deployed to the live environment.
* **Deprecated** – Scheduled for future removal.
* **Archived** – No longer maintained.

---

# Maintenance Notes

The `CHANGELOG.md` shall be updated:

* Before every release.
* After every production deployment.
* After every hotfix.
* After every security update.
* After every database migration.
* After major documentation updates.
* After significant infrastructure changes.
* After changes to organizational workflows.

Maintaining an accurate changelog is mandatory for governance, auditing, traceability, compliance, and long-term maintenance of the SITADC Youth Hub.
