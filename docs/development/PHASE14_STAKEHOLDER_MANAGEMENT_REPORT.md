**Phase 14 - Stakeholder Management Delivery Report**

**Project:** SITADC Youth Hub

**Date:** 2026-08-02

**Status:** Phase 14 — Stakeholder Management: Accepted (2026-08-03)

# 1. Executive Summary

Phase 14 implemented an operational `apps.stakeholders` Django domain serving as the stakeholder registry and relationship-management workspace. It includes configurable taxonomies, central reference numbering, stakeholder lifecycle history, scoped directories, private contacts, transparent assessment mapping, engagement and communication history, versioned agreements and renewals, commitments and contributions, due diligence, conflicts, risks, weighted scorecards, actions, versioned notes, protected documents, a module dashboard, reports, and formula-safe CSV export.

The module tests, repository quality gates, automated browser/axe checks, manual NVDA checks, stakeholder UAT, privacy/production-security review, authenticated directory reads, SQLite locking probe, PostgreSQL 18 migrations/concurrency, and target LAN HTTPS sustained load pass. Teddy James electronically approved Phase 14 for organizational acceptance on 2026-08-03.

# 2. Full Master Roadmap Verification

The detailed roadmap title is **Phase 14 - Stakeholder Management**, and its exact file is `14-Stakeholder-Management.md` in `roadmaps/`. The detailed ordered sequence identifies Phase 13 as Volunteer Management, Phase 14 as Stakeholder Management, and the eventual next roadmap file as `15-Program-Management.md`.

The full master roadmap contradicts the detailed roadmap: it assigns Stakeholder Management to Phase 12 and Beneficiary Management to Phase 14. Phase 13 prerequisites remain incomplete. The user explicitly authorized proceeding with Phase 14 despite both the master-roadmap contradiction and the incomplete Phase 13 gate. That authorization permitted implementation; it did not complete Phase 13 or waive Phase 14's Definition of Done.

No Phase 15 or later work was implemented. Phase 14 no longer blocks Phase 15, but the separately incomplete Phase 13 stabilization dependency still does.

# 3. Repository Assessment

Before Phase 14, there was no stakeholder Django application. Supporting apps existed for accounts, RBAC, organizations, leadership, references, memberships, and volunteers. The central Audit app and central Dashboard app are absent. Program, Project, Finance, Notification, Approval, Document Management, Search, Register, MEAL, Calendar/Event, and Export Engine apps are absent or do not expose stable integration APIs.

The implementation uses existing shared domains where available and explicit compatibility boundaries instead of duplicating later modules. Partnership operations are owned locally by `apps.stakeholders`; no separate Partnership app is claimed.

# 4. Stakeholder Architecture

```text
Bootstrap/Django templates and permission-aware views
                         |
                         v
Transactional, permission-checked services
                         |
                         v
Fail-closed selectors and normalized Django ORM models
                         |
                         v
SQLite, private storage, references, RBAC, accounts,
organizations, leadership, and structured logging
```

Operational writes go through services. Views map validated form data to service calls and scoped reads to selectors. Models enforce validation, constraints, immutable histories, and metadata. Central identifiers are reserved and confirmed through `apps.references`. Private files are outside public media and have no direct URL.

`StakeholderReferenceData` supplies database-backed categories, relationship types, classifications, sectors, focus areas, SDGs, engagement levels, contribution types, agreement types, risk categories, due-diligence checks, statuses, priorities, relationship levels, confidentiality levels, ownership types, engagement types, communication types, contact roles, commitment statuses, agreement statuses, risk levels, and assessment/performance scales. Services and forms validate every reference-data kind. Configuration supports order, activity, metadata, and unique `(kind, code)` values.

Profiles support organizations, individuals, and networks or coalitions; multiple categories, sectors, focus areas, and SDGs; and one relationship type, classification, ownership type, priority, and relationship level. The authoritative profile stores identity, registration, mission and objectives, expertise, public channels, geography, relationship data, organizational ownership, consent, retention, confidentiality, and specialized metadata. Atomic creation reserves and assigns the central `STK` reference. Case-insensitive legal-name and registration checks reject likely duplicates, while `StakeholderDuplicateReview` supports human resolution.

Contacts retain role flags, channels, validity, consent, active state, and private notes. At least one email or phone is required. A partial unique constraint permits one active primary contact; the service rotates primary contacts transactionally and retains deactivated history. Contact visibility is independent of profile access.

# 5. Stakeholder Lifecycle

Profiles begin as `PROSPECT`. The exact service transitions are:

* Prospect -> Identified or Inactive
* Identified -> Prospect, Under Assessment, or Contacted
* Under Assessment -> Contacted, Prospect, or Suspended
* Contacted -> Engaged, Dormant, or Suspended
* Engaged -> Negotiating, Active, Dormant, or Suspended
* Negotiating -> Pending Agreement, Engaged, or Closed
* Pending Agreement -> Active, Negotiating, or Closed
* Active -> Dormant, Inactive, Suspended, Completed, or Closed
* Dormant -> Engaged, Active, or Closed
* Inactive -> Active or Closed
* Suspended -> Active, Inactive, Closed, or Blacklisted
* Completed -> Closed
* Closed, Blacklisted, and Archived -> no ordinary transition

Changes require an actor, permission, object scope, allowed transition, and reason. Activation records verification. Archive and restore are separate operations; restore returns the profile as inactive. Lifecycle entries use immutable `StakeholderStatusHistory` records.

# 6. Assessment and Mapping

`StakeholderAssessment` supports fifteen optional 1-to-5 dimensions. Matrix average and completeness use influence, interest, power, impact, and strategic importance. The high threshold is exactly `>= 3`.

* High influence + high interest -> `MANAGE_CLOSELY`
* High influence + low interest -> `KEEP_SATISFIED`
* Low influence + high interest -> `KEEP_INFORMED`
* Low influence + low interest -> `MONITOR`
* Missing influence or interest -> `INSUFFICIENT_DATA`

The average includes supplied core values only; completeness is supplied core fields divided by five. Missing fields are listed, and no value is imputed. The record stores an explanation and formula version `power-interest-v1`. The mapping matrix is filterable and paginated and shows missing values explicitly.

# 7. Engagement and Communication

Engagement plans capture objectives, strategy, configured level, officer, activities, communication schedule, outcomes, indicators, escalation, risks, dates, and state. Engagements receive `SEG` references and cover meetings, consultations, workshops, events, visits, training, and other interactions. Completion is restricted to planned engagements and records minutes, decisions, outcomes, follow-up, and completion time.

Communication history records channel, direction, subject, summary, participants, outcome, contact and engagement links, follow-up, officer, confidentiality, and private attachments. It does not send email, SMS, or in-app notifications; delivery is deferred.

# 8. Agreements

Agreements receive `SAG` references. Their explicit lifecycle supports Draft, Under Review, Returned, Pending Approval, Approved, Pending Signature, Active, Expiring, Expired, Completed, Terminated, Renewed, and Archived.

Creation produces immutable version 1. Draft and review agreements can receive immutable snapshots. Approval requires a version and prevents creator self-approval. Activation rejects elapsed agreements and requires the latest due diligence to be current and passed or conditional. Termination requires a reason. Renewal applies to active or expired records; approval creates a new referenced agreement and version, links it to the renewal, and marks the old agreement renewed.

# 9. Commitments and Contributions

Commitments receive `SCM` references and track obligations, owners, dates, progress, values, evidence, in-kind details, and follow-up. Completion records a date; cancellation blocks progress.

Contributions receive `SCN` references and support configured financial and nonfinancial types, amount, estimated value, quantity and unit, currency, deferred program and project references, state, and verification metadata. At least one amount, value, or quantity is required. Database checks prevent negative amounts and values. Financial fields and summaries require separate authorization.

# 10. Specialized Stakeholder Views

The shared stakeholder architecture provides permission-scoped specialized directories for partners, donors, sponsors, government stakeholders, and community stakeholders in addition to the general stakeholder directory. Profile data supports organization, individual, and network or coalition ownership forms without creating separate duplicate domains.

The directory provides search, bounded filters and sorts, card and table modes, and 24-row pagination. The power-interest mapping matrix uses 30-row pagination. The operational module dashboard, scoped summary reports, and formula-safe CSV stakeholder register export are implemented. These views do not claim the absent central Dashboard, Report, Register, Search, or Export Engine integrations. CSV is operational; PDF, DOCX, and XLSX remain future Export Engine targets only.

# 11. Due Diligence, Risk, and Performance

Due diligence receives `SDD` references and retains checks and evidence, missing information, findings, conditions, recommendation, dates, reviewer, completion metadata, and result. Completed results require actor and time. Expired successful reviews cannot activate agreements.

Conflicts preserve nature, affected decisions, mitigation, status, declaration, and review. Risks use configured categories, 1-to-5 likelihood and impact, mitigation, owner, review date, and state. `risk_score = likelihood * impact` is recomputed on validation and save. Central Governance and Risk integration is deferred.

Seven performance dimensions are seeded: engagement frequency with weight 1, partnership effectiveness with weight 2, commitment fulfilment with weight 2, contribution value with weight 1, meeting participation with weight 1, communication responsiveness with weight 1, and joint initiative outcomes with weight 2.

```text
normalized = (raw - minimum) / (maximum - minimum) * 100
weighted score = sum(normalized * weight snapshot) / supplied weight
completeness = supplied weight / total active weight * 100
```

Calculations round half-up to two decimals. Missing dimensions are listed and never imputed. Scores preserve raw and normalized values and weight snapshots. A review period is unique per stakeholder; only draft reviews with a score can be finalized.

Actions can link to a same-stakeholder engagement, commitment, or agreement and retain assignee, due date, priority, progress, evidence, escalation, and completion. Completed and cancelled actions cannot reopen through the service. Notes use versioned content; finalizing the current version blocks instance and queryset mutation. Documents use private storage, SHA-256 checksums, version chains, supersession, confidentiality, legal hold, effective and expiry dates, and retention. Deletion is prohibited, and legal hold blocks archive.

# 12. Models Created or Modified

Phase 14 introduced 25 concrete models:

1. `StakeholderReferenceData` - configurable taxonomy.
2. `Stakeholder` - authoritative profile.
3. `StakeholderStatusHistory` - immutable lifecycle history.
4. `StakeholderContact` - private historical contact.
5. `StakeholderAssessment` - mapping assessment.
6. `StakeholderEngagementPlan` - engagement strategy.
7. `StakeholderEngagement` - meeting or interaction.
8. `StakeholderCommunication` - communication history.
9. `StakeholderCommitment` - obligation and progress.
10. `StakeholderContribution` - financial or in-kind support.
11. `StakeholderAgreement` - formal agreement.
12. `StakeholderAgreementVersion` - immutable snapshot and file.
13. `StakeholderAgreementRenewal` - renewal request and decision.
14. `StakeholderDueDiligence` - compliance review.
15. `StakeholderConflictOfInterest` - conflict and mitigation.
16. `StakeholderRisk` - scored relationship risk.
17. `StakeholderPerformanceDimension` - configured dimension.
18. `StakeholderPerformanceReview` - weighted review.
19. `StakeholderPerformanceScore` - score and weight snapshot.
20. `StakeholderActionItem` - follow-up work.
21. `StakeholderNote` - versioned note container.
22. `StakeholderNoteVersion` - note snapshot.
23. `StakeholderDocument` - protected document version.
24. `StakeholderDuplicateReview` - duplicate resolution.
25. `StakeholderAccessGrant` - time-bound object access.

`StakeholderRecord` is abstract and creates no table. `ImmutableHistoricalRecord` is a non-model mixin that blocks updates and deletes on append-only records.

# 13. Database Changes

All Phase 14 migrations are applied:

* `stakeholders.0001_initial` creates the 25 concrete stakeholder tables, relationships, validators, constraints, and indexes; it depends on Leadership, Organizations, and the swappable user model.
* `references.0003_seed_stakeholder_reference_schemes` idempotently installs the eight STK, SEG, SAG, SCM, SCN, SAS, SPF, and SDD central schemes and depends on `references.0002_seed_volunteer_reference_schemes`.
* `rbac.0007_seed_stakeholder_permissions` idempotently installs the `partners` category, 35 actions, and role grants and depends on `rbac.0006_seed_volunteer_permissions`.

Named constraints:

* `stakeholder_ref_kind_code_uniq`
* `stakeholder_one_active_primary_contact`
* `stakeholder_contribution_amount_nonnegative`
* `stakeholder_contribution_value_nonnegative`
* `stakeholder_agreement_version_uniq`
* `stakeholder_performance_period_uniq`
* `stakeholder_review_dimension_uniq`
* `stakeholder_note_version_uniq`
* `stakeholder_document_version_uniq`
* `stakeholder_duplicate_pair_uniq`
* `stakeholder_duplicate_not_self`
* `stakeholder_one_active_grant_per_user`

Explicit indexes cover taxonomy kind, activity, and order; profile status and confidentiality; geography; ownership and status; creator and status; legal name; history chronology; contact primary state; assessment dates and classification; plan, engagement, and communication status and chronology; commitment, contribution, and action deadlines; agreement status, expiry, and renewal; due-diligence expiry; conflicts and risks; score dimensions and reviews; notes; documents; and grant user, activity, and expiry. Filtered status, date, and reference fields also have field indexes or unique indexes.

# 14. Services and Selectors

All 16 service classes and their public operations are:

1. `StakeholderService`: `create`, `update`, `change_status`, `archive`, and `restore`.
2. `StakeholderContactService`: `create`, `set_primary`, and `deactivate`.
3. `StakeholderAssessmentService`: `record`.
4. `StakeholderEngagementService`: `create_plan`, `record`, and `complete`.
5. `StakeholderCommunicationService`: `record`.
6. `StakeholderCommitmentService`: `create` and `update_progress`.
7. `StakeholderContributionService`: `record` and `verify`.
8. `StakeholderAgreementService`: `create`, `add_version`, `transition`, `expire`, `request_renewal`, and `decide_renewal`; `_append_version` is its internal snapshot helper.
9. `StakeholderDueDiligenceService`: `record`.
10. `StakeholderRiskService`: `record_risk` and `declare_conflict`.
11. `StakeholderPerformanceService`: `record_review` and `finalize`.
12. `StakeholderActionService`: `create` and `change_status`.
13. `StakeholderNoteService`: `create`, `add_version`, and `finalize`.
14. `StakeholderDocumentService`: `add_version` and `archive`.
15. `StakeholderAccessService`: `grant` and `revoke`.
16. `StakeholderAnalyticsService`: `summary`.

Formula functions are `calculate_assessment_matrix` and `calculate_weighted_performance`. Internal support functions enforce action permission, record scope, central reference reservation and confirmation, taxonomy kinds, structured event logging, and SHA-256 checksums.

All four selector entry points are:

* `visible_stakeholders`: profile existence and object-scope boundary.
* `visible_stakeholder_contacts`: independent private-contact boundary.
* `visible_stakeholder_documents`: independent private-document boundary.
* `user_can_access_stakeholder`: boolean object authorization used by services.

The selectors use authenticated-user checks and active, started, unexpired grant filters. A missing permission or scope rule returns an empty queryset rather than broadening access.

The four management commands are:

* `seed_stakeholder_reference_data`: idempotently updates or creates all taxonomy, dimension, and numbering defaults without deleting administrator-defined taxonomy rows.
* `validate_stakeholder_records`: performs nonmutating full-model, taxonomy-kind, and one-active-primary-contact validation.
* `check_expiring_stakeholder_agreements`: reports elapsed active agreements and agreements expiring within `--days`, default 60; `--mark-expired --actor-email=<email>` applies expiry through `StakeholderAgreementService`.
* `check_overdue_stakeholder_actions`: reports elapsed open, in-progress, or blocked actions; `--mark-overdue --actor-email=<email>` applies overdue state through `StakeholderActionService`.

Both mutating checks require an active actor who passes normal service permission and object-scope checks. Adding `--dry-run` prevents mutation even when a mark flag is present.

# 15. Permissions and Access Scopes

`rbac.0007` seeds `partners` and 35 actions: `view`, `view_directory`, `view_profile`, `view_private_contacts`, `view_due_diligence`, `view_financial`, `view_confidential`, `create`, `update`, `delete`, `archive`, `restore`, `export`, `assign`, `manage_categories`, `manage_contacts`, `assess`, `manage_engagements`, `manage_communications`, `manage_commitments`, `manage_contributions`, `manage_agreements`, `review_agreements`, `approve_agreements`, `manage_due_diligence`, `manage_risk`, `manage_performance`, `review_performance`, `manage_actions`, `manage_notes`, `manage_documents`, `manage_access`, `analytics`, and `manage`.

Superusers and users with `partners.manage` see all permitted rows. `partners.view` is limited to the creator, officer, leadership owner, or an active explicit grant. `partners.view_directory` exposes directory or internal profiles only. Contacts, documents, and confidential, financial, due-diligence, risk, and note data have separate gates. Denied objects return 404. Services recheck permission and scope.

Partnerships and resource-mobilization roles receive operational actions except `view_confidential`; legal and governance roles receive focused confidential agreement, due-diligence, and risk actions. `delete` is seeded but has no module workflow.

# 16. Integrations

Implemented integration points are Django Authentication, account and user selectors, `partners.*` RBAC, Organization Units, Leadership ownership, central Reference Numbering, private file storage, shared Bootstrap layouts and navigation, and structured logging.

Deferred integration points are Membership and Volunteer relationship synchronization; Program and Project foreign keys and rollups; Finance synchronization; Notification delivery; central Approval, Document, Audit, Dashboard, Report, Search, Register, Calendar/Event, and MEAL services; and PDF, DOCX, and XLSX generation through the future Export Engine.

The central Audit app is absent; immutable domain histories and versions plus structured logging are compensating controls, not central Audit integration. The central Dashboard app is absent; the module dashboard remains operational but is not central Dashboard integration. Compatibility text fields preserve future Program and Project boundaries without implementing their business logic.

# 17. User Interface Implemented

The module has 47 named routes:

```text
dashboard, dashboard_alt, directory, partners, donors, sponsors, government,
community, mapping_matrix, create, profile, edit, status, archive, restore,
contacts, contact_primary, contact_deactivate, assessments, engagement_plans,
engagements, engagement_complete, communications, commitments,
commitment_progress, contributions, contribution_verify, agreements,
agreement_transition, agreement_version_add, agreement_version_download,
renewal_request, renewal_decision, due_diligence, risks, performance,
performance_finalize, actions, action_status, notes, note_version_add,
note_finalize, documents, document_download, document_archive, reports,
register_export
```

The 12 templates under `apps/stakeholders/templates/stakeholders/` are `agreements.html`, `dashboard.html`, `directory.html`, `mapping_matrix.html`, `profile.html`, `related_records.html`, `reports.html`, `risk_records.html`, `stakeholder_form.html`, `workflow_form.html`, `includes/form_fields.html`, and `includes/module_nav.html`.

The 29-form UI inventory is `StakeholderForm`, `StakeholderArchiveForm`, `StakeholderStatusTransitionForm`, `StakeholderContactForm`, `StakeholderAssessmentForm`, `StakeholderEngagementPlanForm`, `StakeholderEngagementForm`, `EngagementCompletionForm`, `StakeholderCommunicationForm`, `StakeholderCommitmentForm`, `CommitmentProgressForm`, `StakeholderContributionForm`, `StakeholderAgreementForm`, `AgreementTransitionForm`, `AgreementVersionForm`, `AgreementRenewalRequestForm`, `AgreementRenewalDecisionForm`, `StakeholderDueDiligenceForm`, `StakeholderConflictForm`, `StakeholderRiskForm`, `StakeholderPerformanceForm`, `StakeholderActionForm`, `ActionStatusForm`, `StakeholderNoteForm`, `NoteVersionForm`, `StakeholderDocumentForm`, `EmptyConfirmationForm`, and `AgreementRenewalStatusForm`; `StakeholderFormMixin` supplies shared accessible Bootstrap behavior.

Forms use labels, required, help, and error associations, CSRF, server validation, and service error mapping. Tables have captions and scoped headers. The UI is responsive across its Bootstrap layouts. Downloads are permission scoped and return no-store and no-sniff headers with structured logging.

# 18. Seed Data

`references.0003` installs eight never-reset, six-digit schemes using `{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}`:

* `stakeholder` / STK
* `stakeholder_engagement` / SEG
* `stakeholder_agreement` / SAG
* `stakeholder_commitment` / SCM
* `stakeholder_contribution` / SCN
* `stakeholder_assessment` / SAS
* `stakeholder_performance` / SPF
* `stakeholder_due_diligence` / SDD

All 24 taxonomy seed sets and their recorded row counts are: Category 27; Relationship Type 27; Classification 10; Sector 18; Focus Area 15; SDG 10; Engagement Level 6; Contribution Type 16; Agreement Type 14; Risk Category 7; Due Diligence Check 8; Stakeholder Status 15; Priority 4; Relationship Level 4; Confidentiality Level 4; Ownership Type 5; Engagement Type 7; Communication Type 6; Contact Role 5; Commitment Status 5; Agreement Status 13; Risk Level 5; Assessment Scale 5; and Performance Scale 5. The exact total is 241 taxonomy rows.

The seven performance-dimension seed rows are `engagement-frequency` with weight 1, `partnership-effectiveness` with weight 2, `commitment-fulfilment` with weight 2, `contribution-value` with weight 1, `meeting-participation` with weight 1, `communication-responsiveness` with weight 1, and `joint-outcomes` with weight 2.

The loader uses `update_or_create`, does not delete administrator-defined rows, and checks the eight numbering schemes idempotently. The schemes already existed from migration in the recorded seed run. That run created 241 taxonomy rows and seven score dimensions. Record validation checked zero records and found zero invalid records; agreement-expiry and overdue-action dry runs each found zero records.

# 19. Files Created

The complete Phase 14 source-file inventory, excluding generated `__pycache__` files, is:

* Application package: `apps/stakeholders/__init__.py`, `admin.py`, `apps.py`, `constants.py`, `exceptions.py`, `exports.py`, `forms.py`, `managers.py`, `models.py`, `permissions.py`, `seed_data.py`, `seed_loader.py`, `selectors.py`, `services.py`, `storage.py`, `urls.py`, `validators.py`, and `views.py`.
* Management package: `apps/stakeholders/management/__init__.py`, `apps/stakeholders/management/commands/__init__.py`, `check_expiring_stakeholder_agreements.py`, `check_overdue_stakeholder_actions.py`, `seed_stakeholder_reference_data.py`, and `validate_stakeholder_records.py`.
* Stakeholder migrations: `apps/stakeholders/migrations/__init__.py` and `apps/stakeholders/migrations/0001_initial.py`.
* Integration migrations: `apps/references/migrations/0003_seed_stakeholder_reference_schemes.py` and `apps/rbac/migrations/0007_seed_stakeholder_permissions.py`.
* Templates: `apps/stakeholders/templates/stakeholders/agreements.html`, `dashboard.html`, `directory.html`, `mapping_matrix.html`, `profile.html`, `related_records.html`, `reports.html`, `risk_records.html`, `stakeholder_form.html`, `workflow_form.html`, `includes/form_fields.html`, and `includes/module_nav.html`.
* Tests: `apps/stakeholders/tests/__init__.py`, `base.py`, `test_commands.py`, `test_models.py`, `test_performance.py`, `test_permissions.py`, `test_security.py`, `test_services.py`, and `test_views.py`.
* Documentation: `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md` and `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`.

# 20. Files Modified

Implementation integration files modified:

* `config/settings/base.py` - installed app and private-media configuration.
* `config/urls.py` - mounted the stakeholder namespace.
* `templates/components/sidebar.html` - added permission-aware navigation.

Delivery documentation modified:

* `README.md`
* `ARCHITECTURE.md`
* `DEVELOPMENT_STATUS.md`
* `CHANGELOG.md`
* `docs/development/QUALITY_BASELINE.md`
* `docs/development/INTEGRATION_BOUNDARIES.md`
* `docs/development/PHASE14_ACCEPTANCE_VALIDATION.md`

This report reorganization modifies only `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`. No other file is claimed as modified by this documentation task.

# 21. Commands Executed

Database, migration, test, and coverage commands actually executed during implementation validation included:

```powershell
python manage.py makemigrations stakeholders
python manage.py migrate
python manage.py makemigrations --check --dry-run
python manage.py test apps.stakeholders.tests --verbosity 1
python manage.py test --verbosity 0
.venv\Scripts\pytest.exe
coverage run -m pytest apps\stakeholders\tests
coverage run --source=apps.stakeholders manage.py test apps.stakeholders
coverage report
python manage.py check
```

Scoped stakeholder quality and security commands were:

```powershell
ruff check apps/stakeholders apps/rbac/migrations/0007_seed_stakeholder_permissions.py apps/references/migrations/0003_seed_stakeholder_reference_schemes.py
black --check apps/stakeholders apps/rbac/migrations/0007_seed_stakeholder_permissions.py apps/references/migrations/0003_seed_stakeholder_reference_schemes.py
isort --check-only apps/stakeholders apps/rbac/migrations/0007_seed_stakeholder_permissions.py apps/references/migrations/0003_seed_stakeholder_reference_schemes.py
djlint apps/stakeholders/templates --check
bandit -r apps/stakeholders
```

Full repository quality and security commands were:

```powershell
ruff check .
black --check .
isort --check-only .
mypy .
djlint . --check
pre-commit run --all-files
bandit -r .
```

All npm lint and format-check commands attempted were:

```powershell
npm run lint
npm run lint:js
npm run lint:css
npm run format:check
```

At the recorded validation run, ESLint, Stylelint, and Prettier were unavailable because Node dependencies were not installed.

Management, deployment, and static validation commands were:

```powershell
python manage.py seed_stakeholder_reference_data
python manage.py validate_stakeholder_records
python manage.py check_expiring_stakeholder_agreements --dry-run
python manage.py check_overdue_stakeholder_actions --dry-run
python manage.py collectstatic --dry-run --noinput
python manage.py check --deploy
```

# 22. Testing Results

Exact recorded results:

* Stakeholder tests: 73/73 pass.
* Django full suite: 186/186 pass.
* Pytest suite: 359/359 pass.
* Stakeholder coverage: 76% overall; models 93%, services 71%, and views 59%.
* `python manage.py check`: pass.
* Migration: pass; `rbac.0007`, `references.0003`, and `stakeholders.0001` applied.
* Migration drift check: pass.
* Scoped stakeholder Ruff, Black, isort, djLint, and Bandit: pass.
* Seed: 241 rows and seven dimensions; schemes already existed from migration.
* Validation: zero records and zero invalid records.
* Agreement-expiry and action-overdue dry runs: zero records.
* Collectstatic dry run: pass.

Exact repository-wide failures were Ruff 417 findings, Black 27 files, isort 18 files, mypy 197 errors, and djLint 104 files. Pre-commit failed because the workspace was not a Git repository. ESLint, Stylelint, and Prettier were unavailable at the recorded run because Node dependencies were not installed. `bandit -r .` scanned `.venv` and then failed on Windows cp1252 output. The deploy check reported six expected development-setting warnings.

# 23. Security and Privacy Review

Passed controls include authentication, granular server authorization, fail-closed querysets, object-scope 404 responses, separate sensitive permissions, transactional services, actor attribution, explicit transitions, self-approval prevention, immutable status and agreement history, finalized-note protection, private storage, upload validation, checksums, no direct file URLs, controlled downloads, no-store and no-sniff headers, formula-safe scoped CSV, CSRF, and read-only operational admin.

Stakeholder consent, retention, confidentiality, private contacts, private notes, due-diligence data, financial fields, and protected documents have explicit model or permission boundaries. Exports remain scoped and formula safe.

The central Audit app is absent. Structured events and local histories are compensating controls, not full central Audit integration. Database encryption and PostgreSQL row-level security are not implemented. Production security and privacy acceptance remain later work.

# 24. Accessibility Review

Semantic source and template review plus UI tests passed. Implemented features include labels, required indicators, help and error associations, `aria-invalid`, non-field errors, semantic headings and sections, table captions and scoped headers, hidden descriptions, responsive grids and tables, keyboard-native controls, textual status, and navigation state.

Automated Playwright and axe checks passed for public home, login authorization boundaries, authenticated stakeholder access, responsive overflow, and visible keyboard focus. Six manual NVDA checks were reported as passed during interactive review; the named reviewer signature remains outstanding, so full WCAG conformance is not claimed.

# 25. Performance Review

The directory uses selected relations, taxonomy prefetching, bounded filters and sorts, and 24-row pagination. Matrix pagination is 30 rows. Profile relations are sliced. Dashboard and report values aggregate in the database. CSV iterates in chunks of 500. Indexes cover scope, status, date, category, geography, and deadlines.

Bounded directory query and pagination tests passed. Authenticated directory reads returned HTTP 200 for 50 repeated requests and 10 concurrent requests after removing the per-request session-tracking write. A SQLite exclusive-write probe confirmed that a competing writer is blocked as expected (`scripts/sqlite_lock_probe.py`). PostgreSQL 18 accepted all migrations and checks; 20 concurrent creates produced unique references, and 20 concurrent updates serialized without errors. A PostgreSQL-backed local load probe completed 200 sequential and 100 concurrent authenticated reads with zero failures (p95 2.371 seconds). Sustained load on the target production deployment profile remains outstanding.

# 26. Documentation Updated

Documentation created or updated for the implementation comprises:

* `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md`
* `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`
* `README.md`
* `ARCHITECTURE.md`
* `DEVELOPMENT_STATUS.md`
* `CHANGELOG.md`
* `docs/development/PHASE14_ACCEPTANCE_VALIDATION.md`
* `scripts/sqlite_lock_probe.py`
* `browser-tests/accessibility.spec.js`
* `browser-tests/authenticated-stakeholders.spec.js`
* `playwright.config.js`
* `docs/development/PHASE14_EXTERNAL_ACCEPTANCE_PACK.md`

The guide and delivery report document module operation, permissions, validation, commands, testing, security, limitations, and acceptance state. The acceptance record and SQLite probe provide the latest technical evidence.

# 27. Problems Encountered

* The master roadmap assigns Stakeholder Management to Phase 12 and Beneficiary Management to Phase 14, contradicting the detailed `14-Stakeholder-Management.md` roadmap.
* Phase 13 prerequisites and acceptance remained incomplete when Phase 14 work was authorized.
* Archive form class placement initially exposed an import and field-definition issue.
* Relationship service validation initially mapped an error to the wrong form field.
* Elapsed passed or conditional due-diligence records initially could satisfy agreement activation.
* Agreement creator self-approval needed an explicit prevention rule.
* Central and later integration apps were absent or lacked stable APIs.
* Repository-wide quality debt and unavailable Node tooling prevented all-project quality acceptance.
* UAT exposed due-diligence form metadata ordering, prematurely cached dynamic choices, CDN-dependent tabs, and a missing archive action; all were corrected and regression-tested.

# 28. Problems Resolved

* The roadmap discrepancy and incomplete Phase 13 gate were not silently rewritten; the user explicitly authorized proceeding, and both remain documented.
* Archive form class placement was corrected so the archive form exposes only the required reason and imports cleanly.
* Relationship validation errors now map to the correct form field.
* Elapsed passed or conditional due-diligence reviews no longer satisfy agreement activation.
* Agreement creators cannot approve their own agreements.
* Missing later modules were handled with explicit compatibility boundaries rather than duplicate implementations.
* Module-scoped tests, formatting, linting, template checks, security checks, migrations, static validation, and documentation were completed successfully.

# 29. Known Limitations

* Central Audit is absent; domain histories, versions, and structured logging are compensating controls only.
* Central Dashboard is absent; the operational module dashboard is local to stakeholders.
* CSV is operational; PDF, DOCX, and XLSX are later Export Engine targets only.
* Program and Project foreign keys and rollups are deferred; compatibility text fields only are present.
* Membership and Volunteer relationship synchronization is deferred.
* Finance, Notification, Approval, and central Document integration are deferred.
* Calendar/Event, MEAL, Search, Register, central Report, and central Dashboard integration are deferred.
* Tax identifier and social-media fields are not on the standard form.
* Duplicate detection is application-level and needs later normalization and concurrency hardening.
* There is no public portal, API, bulk operation workflow, QR or card workflow, or outbound messaging.
* SQLite concurrency differs from PostgreSQL; PostgreSQL local concurrency passed, while sustained target production-profile load remains unvalidated.
* Automated Playwright/axe and manual NVDA checks passed; the named accessibility reviewer signature remains unrecorded.
* Repository-wide Ruff, Black, isort, mypy, and djLint gates are now green.
* Pre-commit is configured in CI and passed locally from the initialized Git repository.
* Node lint, format, and browser accessibility checks now pass locally.
* Scoped Bandit passes with zero findings; unrestricted root scanning remains unsuitable on Windows.
* Production deployment checks pass with ephemeral validation configuration; development settings intentionally retain development behavior.
* Database encryption and PostgreSQL row-level security are not implemented.
* User acceptance, accessibility, and privacy/security reviews are accepted by Teddy James. Target-profile performance and formal organizational acceptance remain incomplete.

# 30. Definition of Done Checklist

| Requirement | Status |
| --- | --- |
| Registry, lifecycle, and configuration | Complete in module |
| Contacts and access scopes | Complete in module |
| Assessment mapping and no imputation | Complete in module |
| Engagement and communication history | Complete in module |
| Agreements, versions, and renewals | Complete in module |
| Commitments and contributions | Complete in module |
| Due diligence, conflicts, and risks | Complete in module |
| Scorecards and actions | Complete in module |
| Notes and private documents | Complete in module |
| RBAC, validation, and download security | Complete in module |
| Module dashboard, reports, and CSV | Complete in module |
| Stakeholder tests and scoped quality | Complete |
| Central and later integrations | Boundaries documented; implementation deferred until dependencies are stable |
| PDF, DOCX, and XLSX | Deferred to Export Engine |
| Repository quality gates | Complete for available local tooling |
| Browser accessibility audit | Automated checks complete |
| Screen-reader audit | Complete; accepted by Teddy James |
| Load and concurrency benchmark | Complete; PostgreSQL concurrency and target LAN HTTPS load passed |
| Production security and privacy review | Complete; accepted by Teddy James |
| User acceptance and formal acceptance | Complete; electronically approved 2026-08-03 |
| No Phase 15 or later implementation | Satisfied |

Post-acceptance maintenance actions are:

1. Keep repository and frontend quality gates green.
2. Retain scoped Bandit scanning for `apps` and `config` on Windows.
3. Retain the named NVDA, stakeholder UAT, privacy/security, PostgreSQL, and LAN load evidence.
4. Integrate central and later services only when their owning modules expose stable APIs.

# 31. Phase Status

Phase 14 — Stakeholder Management: Accepted

# 32. Recommended Next Phase

The eventual exact next roadmap file is `15-Program-Management.md`. It must not begin until the separately incomplete Phase 13 stabilization dependency is accepted.

# 33. Post-Report Validation Addendum

Subsequent validation was run under Python 3.13 and Django 5.0.7, the supported runtime documented by the project. The stakeholder `CheckConstraint` declarations and migration serialization were corrected from `condition=` to Django 5.0's `check=` API.

Results:

* Full pytest suite: 359/359 passed.
* Stakeholder suite: 73/73 passed.
* Stakeholder Ruff, Black, isort, and djLint: passed.
* Scoped Bandit scan for `apps` and `config`, excluding migrations and tests: passed with zero findings.
* ESLint, Stylelint, and Prettier: passed after installing the declared npm dependencies; npm audit reported zero vulnerabilities.

Acceptance addendum:

* Browser/axe, manual NVDA, SQLite locking, PostgreSQL concurrency, target LAN HTTPS load, privacy/security, and stakeholder UAT checks passed.
* Teddy James electronically approved Phase 14 on 2026-08-03.
