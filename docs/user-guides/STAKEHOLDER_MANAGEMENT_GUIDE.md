# Stakeholder Management Guide

## 1. Purpose And Status

The `apps.stakeholders` module is the SITADC Youth Hub's operational registry and relationship-management workspace for organizations, individuals, networks, partners, donors, sponsors, government institutions, community stakeholders, suppliers, consultants, and other relationships.

It covers registration, classification, scoped directories, contacts, assessment and mapping, engagement planning, meetings, communications, agreements, renewals, commitments, contributions, due diligence, conflicts, risks, performance reviews, actions, notes, private documents, reporting, and CSV export.

```text
Phase 14 — Stakeholder Management: Accepted
```

The module is operational and was formally accepted on 2026-08-03. Central and later integrations remain deferred to their owning phases and are not Phase 14 defects.

## 2. Access And Navigation

All stakeholder pages require authentication and a server-side `partners.*` permission. Authorized users can use the **Stakeholders** sidebar link or open `/stakeholders/`.

The module exposes 47 named routes. Navigation provides Dashboard, Directory, Mapping matrix, Reports, and the current profile. The general directory has specialized partner, donor, sponsor, government, and community views. Search supports stakeholder reference, legal name, trading name, display name, and acronym. Filters cover status, category, relationship type, entity type, and region. Results support table/card views and 24-record pagination.

The stakeholder dashboard is operational inside this module. It is not the deferred central Dashboard application. It shows scoped record, relationship, pipeline, action, agreement, risk, contribution, category, and region data according to the user's permissions.

## 3. Stakeholder Registration And Profile

Users with `partners.create` can register an organization, individual, or network/coalition. Profiles support:

* Legal, trading, display, acronym, and former names
* Description, vision, mission, objectives, expertise, work, interests, and potential collaboration
* Configurable categories, relationship type, classification, ownership, priority, relationship level, sectors, focus areas, and SDGs
* Registration authority/number, establishment date, and country of registration
* Address, geographic coverage, authorized coordinates, website, public email, phone, and social data
* Identification source, referral, responsibilities, achievements, and challenges
* Responsible organization unit, directorate, officer, and leadership profile
* Confidentiality, consent, retention, and specialized JSON data
* Temporary program/project text references pending later domain models

Creation reserves an `STK` identifier through the centralized Reference Numbering service and confirms it only after the profile saves. The transaction rolls back if assignment fails. Legal names and nonblank registration numbers are checked case-insensitively for possible duplicates. This is an application-level duplicate check, not normalized database uniqueness.

Tax identifier and social-media fields exist in the model but are not exposed in the standard profile form.

## 4. Stakeholder Lifecycle

New records begin as `PROSPECT`. Status changes require `partners.update`, an allowed transition, and a reason. Activation records verification time and actor. Every change creates immutable `StakeholderStatusHistory`.

Allowed transitions:

* Prospect: Identified or Inactive
* Identified: Prospect, Under Assessment, or Contacted
* Under Assessment: Contacted, Prospect, or Suspended
* Contacted: Engaged, Dormant, or Suspended
* Engaged: Negotiating, Active, Dormant, or Suspended
* Negotiating: Pending Agreement, Engaged, or Closed
* Pending Agreement: Active, Negotiating, or Closed
* Active: Dormant, Inactive, Suspended, Completed, or Closed
* Dormant: Engaged, Active, or Closed
* Inactive: Active or Closed
* Suspended: Active, Inactive, Closed, or Blacklisted
* Completed: Closed
* Closed, Blacklisted, and Archived: no ordinary outgoing transition

Archiving is a separate reasoned operation that removes the record from normal selectors. Restore includes archived records in scope evaluation and returns the profile as `INACTIVE`. Operational deletion is not exposed in the UI.

## 5. Types, Categories, And Configuration

`StakeholderReferenceData` provides configurable kind, stable code, name, description, JSON metadata, active state, and order. `(kind, code)` is unique.

Seeded kinds are category, relationship type, classification, sector, focus area, SDG, engagement level, contribution type, agreement type, risk category, due-diligence check, stakeholder status, priority, relationship level, confidentiality, ownership type, engagement type, communication type, contact role, commitment status, agreement status, risk level, assessment scale, and performance scale.

The seed installs 241 reference rows and seven performance dimensions. Eight numbering schemes are installed by migration and checked idempotently by the seed loader. Running the seed again updates defaults but does not delete administrator-defined rows.

## 6. Contacts

Private contacts require `partners.view_private_contacts` to view and `partners.manage_contacts` to maintain. Records include identity, roles, department, channels, availability, validity dates, consent, active state, and private notes.

At least one email or phone is required. Only one active primary contact is permitted. Setting a new primary demotes the old one in the same transaction. Deactivation clears primary status and records a validity end date. Profile visibility alone never reveals contacts, and communication forms hide contact choices from users without private-contact access.

## 7. Assessment And Mapping Matrix

Assessments support fifteen optional 1-to-5 scores. Average and completeness use these five core fields: influence, interest, power, impact, and strategic importance.

The high threshold is exactly `>= 3`:

| Influence | Interest | Classification |
| --- | --- | --- |
| High | High | Manage closely |
| High | Low | Keep satisfied |
| Low | High | Keep informed |
| Low | Low | Monitor |
| Missing influence or interest | Any | Insufficient data |

The average is `sum(supplied core scores) / count(supplied core scores)`. Completeness is `count(supplied core scores) / 5 * 100`. Missing values are listed and never imputed. Each result stores its explanation and formula version `power-interest-v1`. The mapping page displays missing influence/interest explicitly, filters by classification, and paginates at 30 records.

## 8. Engagement Plans, Meetings, And Communications

Engagement plans record objectives, strategy, configured level, responsible officer, activities, communication method/frequency, key messages, expected outcomes, indicators, risks, escalation, dates, review date, and state.

Engagements cover meetings, consultations, workshops, events, site visits, training, and other interactions and receive `SEG` references. Only a planned engagement can be completed; completion records time, minutes, decisions, outcomes, and follow-up. Linked plans must belong to the same stakeholder.

Communications retain channel, direction, subject, summary, occurrence, sender, recipients, outcome, optional contact/engagement, responsible officer, follow-up, confidentiality, and private attachment. This stores communication history; it does not send email, SMS, or in-app notifications because those central modules are deferred.

## 9. Agreements, Versions, And Renewals

Agreements receive `SAG` references and support configured MoUs, grants, sponsorships, service contracts, data-sharing agreements, and other types. They record terms, responsibilities, deliverables, reporting, dates, notice period, signatories, values, relationship owner, and deferred program/project references.

The lifecycle supports Draft, Under Review, Returned, Pending Approval, Approved, Pending Signature, Active, Expiring, Expired, Completed, Terminated, Renewed, and Archived through an explicit transition map.

Controls include:

* Creation automatically produces immutable version 1.
* New versions are allowed only in Draft or Under Review.
* The creator cannot approve their own agreement.
* Approval requires at least one version.
* Activation requires prior approval, an effective and non-expired agreement, and the latest due diligence to be current and `PASSED` or `CONDITIONAL`.
* Termination requires a reason.
* Private agreement downloads are permission-checked with no-store/no-sniff headers.

Renewal applies to active or expired agreements. Approval creates a new referenced agreement and version 1, links the renewal, and marks the old agreement renewed; it does not overwrite the old agreement.

## 10. Commitments And Contributions

Commitments receive `SCM` references and record obligation, responsible party/officer, dates, expected/actual values, in-kind details, progress, evidence, and follow-up owner. Completion records a date. Cancelled commitments cannot be progressed.

Contributions receive `SCN` references. Configured types include financial, in-kind, technical, equipment, training, volunteer, advisory, venue, transport, staff time, mentorship, media, data, research, materials, and other resources. At least one amount, estimated value, or quantity is required. Amount/value cannot be negative. Verification separately records actor and time.

Financial details require a financial permission. Program/project links remain text until those modules expose stable foreign keys.

## 11. Due Diligence, Conflicts, And Risks

Due-diligence records receive `SDD` references and retain structured checks, missing information, findings, conditions, recommendation, review/expiry, status, reviewer, and completion. Completed results require actor metadata. `EXPIRED`, or a passed/conditional result after its expiry date, cannot satisfy agreement activation.

Conflict records retain declaration, affected decisions, mitigation, status, and review metadata. Risks use configured categories and 1-to-5 likelihood/impact:

```text
risk score = likelihood * impact
```

Risk/conflict pages require confidential/risk permissions. Integration with the later Governance/Risk/Compliance module is deferred.

## 12. Performance Scorecards

Default dimensions and weights are engagement frequency (1), partnership effectiveness (2), commitment fulfilment (2), contribution value (1), meeting participation (1), communication responsiveness (1), and joint initiative outcomes (2).

```text
normalized = (score - minimum) / (maximum - minimum) * 100
weighted score = sum(normalized * weight snapshot) / supplied weight
completeness = supplied weight / all active weight * 100
```

Results round to two decimals. Missing dimensions are listed and never imputed. Saved scores retain weight snapshots. A review requires at least one score, is unique by stakeholder/review period, and can be finalized from Draft once.

## 13. Actions, Notes, And Documents

Actions may link to a same-stakeholder engagement, commitment, or agreement and record assignee, due date, priority, progress, evidence, escalation, and comments. Completed/cancelled actions cannot be reopened through the current service.

Notes are confidential versioned containers. Draft notes accept versions; finalization locks the current version against instance and queryset updates/deletes and records actor/time.

Documents use private storage outside `MEDIA_ROOT`, expose no URL, and support keys, versions, previous-version links, status, confidentiality, SHA-256 checksum, legal hold, effective/expiry, and retention. New current versions supersede the prior current version. Documents cannot be deleted; legal hold blocks archive.

Uploads validate filename, extension, size, declared MIME type, and supported signatures. Documents are limited to 20 MB and profile images to 5 MB. Authorized downloads are structured-logged.

## 14. Permissions And Scopes

Phase 14 seeds 35 `partners.*` actions:

```text
view, view_directory, view_profile, view_private_contacts,
view_due_diligence, view_financial, view_confidential, create, update,
delete, archive, restore, export, assign, manage_categories,
manage_contacts, assess, manage_engagements, manage_communications,
manage_commitments, manage_contributions, manage_agreements,
review_agreements, approve_agreements, manage_due_diligence,
manage_risk, manage_performance, review_performance, manage_actions,
manage_notes, manage_documents, manage_access, analytics, manage
```

No delete workflow is exposed despite the catalogue permission.

* Superusers/`partners.manage` see all nondeleted records; archived rows require explicit inclusion.
* `partners.view` sees records created by, assigned to, leadership-owned by, or actively granted to the user.
* `partners.view_directory` sees `DIRECTORY` and `INTERNAL`, not `CONFIDENTIAL`/`RESTRICTED`.
* Explicit grants must be active, started, and unexpired.
* No matching scope returns an empty queryset; denied object lookup returns 404.
* Contacts, documents, due diligence, financial data, risks, notes, analytics, and export have separate gates.

Services recheck both action permission and object scope. The partnerships/resource-mobilization roles receive operational actions except `view_confidential`; legal/governance receives focused confidential agreement, due-diligence, and risk access.

## 15. Reports And Exports

Reports provide scoped counts by status/category/region and an authorized contribution summary. CSV export is operational, scoped, chunked at 500, formula-safe, no-store, no-sniff, and structured-logged.

PDF, DOCX, and XLSX controls are intentionally disabled. They are targets for the later Export Engine/dependencies, not implemented Phase 14 formats.

## 16. Management Commands

```powershell
python manage.py seed_stakeholder_reference_data
python manage.py validate_stakeholder_records
python manage.py check_expiring_stakeholder_agreements --dry-run
python manage.py check_overdue_stakeholder_actions --dry-run
```

Expiry supports `--days=N`; mutation requires `--mark-expired --actor-email=<active-authorized-user>`. Action mutation requires `--mark-overdue --actor-email=<active-authorized-user>`. `--dry-run` is report-only.

Mutating command modes still execute the normal service-layer permission and stakeholder-scope checks. A valid actor email alone does not bypass RBAC or object scope.

The recorded run created 241 reference rows and seven dimensions; schemes already existed from migration. Validation checked zero records, and both expiry/action dry runs found zero.

## 17. SQLite Limitations

SQLite is the development database:

* `select_for_update()` does not provide PostgreSQL-style row locks.
* Writes are serialized and can return database-locked errors under contention.
* Partial unique constraints require a recent SQLite version.
* JSON fields are used, but advanced JSON query/index features are avoided.
* No load/concurrent-write benchmark has been run.
* Authorization is application RBAC/scoping; database row-level security is not implemented.

Validate reference issuance, approval, renewal, primary-contact rotation, document versioning, and access grants on PostgreSQL before higher-concurrency deployment.

## 18. Integrations And Deferred Work

Implemented integrations: authentication, RBAC, user selectors, organization units, leadership ownership, central references, private storage, shared Bootstrap navigation/layouts, and structured logging.

The central Audit app is absent. Immutable status/agreement histories, finalized notes, document versions, actor/time fields, and structured logging are compensating domain controls, not full central audit integration.

The central Dashboard app is absent. The module dashboard is operational but is not central integration.

Deferred to owning modules/stable APIs:

* Program/project foreign keys and rollups
* Membership and Volunteer relationship synchronization
* Finance synchronization
* Notification delivery/reminders
* Central Approval and Document engines
* Central Audit and Dashboard
* Search, Registers, Calendar/Event, and MEAL integration
* PDF, DOCX, XLSX through Export Engine

## 19. Validation And Acceptance

Stakeholder tests passed 73/73; the previously recorded Django suite passed 186/186; the current pytest suite passed 359/359. Stakeholder coverage remains 76% overall: models 93%, services 71%, views 59%. Stakeholder Ruff, Black, isort, djLint, and Bandit pass.

Phase 14 is formally accepted. Browser/axe, manual NVDA, stakeholder UAT, privacy/security, PostgreSQL 18 concurrency, and target LAN HTTPS sustained load checks pass. The eventual next roadmap is `15-Program-Management.md`, but Phase 13 stabilization remains a separate prerequisite.
