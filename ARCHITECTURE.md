# ARCHITECTURE.md

# SITADC Youth Hub

## System Architecture Documentation

**Project:** SITADC Youth Hub

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

**Current Version:** 1.0.0

**Status:** Development

---

# 1. Project Overview

SITADC Youth Hub is a centralized organizational management and reporting platform designed to support the governance, administration, operations, monitoring, evaluation, accountability, learning, and digital transformation of the SITADC Youth Organization.

The platform enables secure collaboration between leadership, staff, volunteers, partners, donors, and other stakeholders through role-based access, workflow automation, document management, reporting, dashboards, and organizational registers.

---

# 2. System Goals

The architecture is designed to provide:

* Scalability
* Security
* Reliability
* Maintainability
* Modularity
* Accessibility
* High Performance
* Extensibility
* Auditability
* Long-term sustainability

---

# 3. Technology Stack

## Backend

* Python 3.12+
* Django 5+
* Django ORM
* Django Authentication
* Django Admin

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* JavaScript (ES6+)
* Django Templates

## Database

### Development

* SQLite

### Future Production (Optional)

* PostgreSQL

## Storage

* Django Media Storage
* Local development storage
* Cloud storage supported in production

## Version Control

* Git
* GitHub

## AI Development Tools

* Antigravity
* OpenCode

---

# 4. High-Level Architecture

```text
Users
   │
   ▼
Web Browser
   │
   ▼
Django Templates
   │
   ▼
Views
   │
   ▼
Services
   │
   ▼
Models
   │
   ▼
SQLite Database
```

Supporting services include:

* Authentication
* Authorization
* File Storage
* Email Services
* Notifications
* Audit Logging
* Reporting
* Dashboards

---

# 5. Application Layers

The application follows a layered architecture.

## Presentation Layer

Responsible for:

* User Interface
* Forms
* Templates
* Dashboards
* Reports
* Responsive layouts

---

## Business Logic Layer

Responsible for:

* Business rules
* Workflow processing
* Report generation
* Approval logic
* Validation
* Notification handling

---

## Data Access Layer

Responsible for:

* Django ORM
* Database queries
* Transactions
* Migrations
* Data integrity

---

## Database Layer

Stores:

* Users
* Roles
* Permissions
* Leadership records
* Volunteers
* Members
* Programs
* Projects
* Reports
* Documents
* Registers
* Audit logs

---

# 6. Core Modules

The application consists of the following major modules:

* Authentication
* Dashboard
* User Management
* Role & Permission Management
* Leadership Management
* Membership Management
* Volunteer Management
* Beneficiary Management
* Partner, Donor & Sponsor Management
* Program Management
* Project Management
* MEAL
* Report Management
* Review & Approval
* Document Management
* Organizational Registers
* Reference Numbering
* Calendar & Meetings
* Notifications
* Audit Logging
* Finance
* Communication & Media
* System Configuration

Each module is developed independently while integrating seamlessly with the rest of the system.

---

# Volunteer Management Architecture

The `apps.volunteers` domain owns volunteer recruitment and lifecycle records. It integrates with `accounts.User`, internal `organizations.OrganizationUnit`, centralized `references`, and RBAC without duplicating those domains.

## Write Model

All operational web writes use transaction-backed services in `apps/volunteers/services.py`. Profile status and application transitions use explicit transition maps, row locking, model validation, actor attribution, and append-only audit records. Public application submission is the only anonymous write and requires consent.

## Read Model

`apps/volunteers/selectors.py` is the authorization boundary for profiles. Module managers and superusers receive the permitted registry; a user holding only `volunteers.view` is restricted to their own profile. Related lists, dashboard aggregates, form choices, ID cards, and exports derive from the same selector and use `select_related` to avoid common N+1 queries.

## Reference Numbers

The central reference service reserves and confirms three Phase 13 identifiers:

* `VOL` — volunteer profiles
* `VAP` — volunteer applications
* `VRC` — recruitment campaigns

No volunteer view or model generates local timestamp identifiers.

## Security And Records

Volunteer audit/status/deployment histories reject updates and deletes through their application managers and model methods. CVs, certificates, and volunteer documents use `PrivateVolunteerStorage` outside `MEDIA_ROOT`; direct URLs are prohibited and authorized downloads are audited. Upload validation checks size, extension, MIME type, and basic file signature. Confidential profile values and export columns require `volunteers.view_confidential`.

## Current Boundaries

Program/project names remain compatibility fields until those later domain apps expose stable foreign keys. Phase 13 still requires configurable database-backed taxonomies, activity and disciplinary workflows, complete document version/retention handling, and non-CSV report formats before acceptance.

---

# Stakeholder Management Architecture

The `apps.stakeholders` domain is the operational stakeholder registry and relationship-management boundary. It integrates with Authentication, RBAC, Accounts, Organization Units, Leadership, centralized Reference Numbering, private storage, shared layouts/navigation, and structured logging. It does not duplicate Program, Project, Finance, Notification, Approval, Document Management, Dashboard, Audit, or Export Engine domains that are absent or scheduled later.

## Write And Read Boundaries

Operational writes use permission-checked, transaction-backed services in `apps/stakeholders/services.py`. Services validate object scope, reserve and confirm central references, lock rows where the database supports it, call model validation, attribute actors, and emit structured events. Operational Django admin models are read-only to prevent service bypass.

`apps/stakeholders/selectors.py` is the read authorization boundary. Superusers and `partners.manage` receive all permitted rows; ordinary `partners.view` access is limited to creator, responsible officer, leadership owner, or active explicit grant; `partners.view_directory` receives only directory/internal profiles. Private contacts/documents have independent selectors. Unauthorized lookups fail closed.

## Domain Model

Twenty-five concrete models cover reference data, profiles, immutable status history, contacts, assessments, plans, engagements, communications, commitments, contributions, agreements/versions/renewals, due diligence, conflicts, risks, performance dimensions/reviews/scores, actions, notes/versions, documents, duplicate reviews, and access grants. Sixteen transaction-backed service classes own domain writes and analytics; four fail-closed selectors own profile, contact, document, and boolean object access. The web layer exposes 47 named routes through 12 Bootstrap templates.

Profiles support organizations, individuals, and networks/coalitions. Categories, types, classifications, sectors, focus areas, SDGs, engagement levels, contribution/agreement/risk types, and scales are database-backed. The seed contains 241 reference rows and seven score dimensions.

## Lifecycle, Assessment, And Scorecards

Stakeholder/agreement lifecycles use explicit transition maps. Stakeholder activation records verification; agreement approval prevents self-approval; activation requires current passed/conditional due diligence and a non-expired agreement. Status history/agreement versions are immutable through instance and queryset APIs.

The power-interest matrix uses `>= 3` as high. High/high is Manage Closely, high/low Keep Satisfied, low/high Keep Informed, and low/low Monitor. Missing influence or interest produces Insufficient Data. Average/completeness use supplied values only; missing values are listed and never imputed.

Scorecards normalize supplied dimensions to 0-100 from configured ranges, multiply by weight snapshots, and divide by supplied weight. Completeness is supplied weight divided by all active weight. Missing dimensions are never imputed.

## Private Records And Exports

Images, communication attachments, agreement files, status evidence, and documents use `PrivateStakeholderStorage` outside `MEDIA_ROOT` and expose no direct URL. Uploads validate filename, extension, size, declared MIME type, and basic signatures. Downloads are permission/scoped, no-store, no-sniff, and structured-logged. Documents are versioned/checksummed, protected from deletion, and respect legal hold during archive.

CSV export is operational, scoped, formula-safe, no-store, logged, and iterated in 500-row chunks. PDF, DOCX, and XLSX remain later Export Engine targets.

## Audit, Dashboard, And Integration Boundaries

The central Audit app is absent. The stakeholder domain therefore uses immutable histories/versions, actor/time metadata, and a structured logging adapter. These controls are not full central audit integration.

The central Dashboard app is absent. `apps.stakeholders` has an operational permission-scoped module dashboard/report page, but no central dashboard integration is claimed.

Program/project references remain compatibility text until stable foreign keys exist. Finance synchronization, outbound notifications, central approvals, the central document engine, search/registers, calendar/events, MEAL outcomes, and non-CSV exports are deferred to their owning modules.

## SQLite Boundary

SQLite is supported for development, but `select_for_update()` does not provide PostgreSQL-style row locks, writes are serialized, and sustained concurrent mutation can cause lock contention. Partial unique constraints require a recent SQLite version. Advanced JSON querying/indexing is avoided. Bounded directory-query and pagination tests pass, but no load/concurrency benchmark was performed.

See `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md` and `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`.

---

# 7. Authentication & Authorization

Authentication is managed using Django's built-in authentication framework.

Authorization is enforced through:

* Roles
* Groups
* Permissions
* Staff access
* Superuser access

Every request is validated before access is granted.

---

# 8. Database Architecture

SQLite serves as the primary database during development.

Database design follows:

* Normalized schema
* Foreign key relationships
* UUID identifiers where appropriate
* Timestamp tracking
* Migration-based schema management

Business logic is implemented in the application layer rather than the database.

---

# 9. File Storage

The system supports:

* Document uploads
* Images
* Evidence files
* Reports
* Meeting documents
* Policies
* MoUs
* Media assets

Development uses local storage, while production can be configured to use cloud-based storage.

---

# 10. Security Architecture

Security features include:

* Authentication
* Role-Based Access Control (RBAC)
* CSRF protection
* XSS protection
* SQL injection prevention
* Secure password hashing
* Session management
* Audit logging
* File validation
* Input validation

Production deployments should enforce HTTPS and additional security headers.

---

# 11. Reporting Architecture

Reports are generated from centralized data and support:

* Drafts
* Reviews
* Approvals
* Version history
* Evidence attachments
* PDF export
* DOCX export
* Excel export

Reporting workflows maintain a complete audit trail.

---

# 12. Dashboard Architecture

Dashboards are role-aware and provide:

* KPIs
* Notifications
* Recent activities
* Pending approvals
* Reporting status
* Organizational statistics
* Performance metrics

Dashboard content is dynamically generated based on user permissions.

---

# 13. Organizational Workflow

The reporting hierarchy follows:

```text
Volunteers
        │
Team Leaders
        │
Community Coordinators
        │
District Coordinators
        │
Regional Coordinators
        │
Directorates
        │
Executive Director
        │
National Executive Committee
        │
Board of Trustees
```

Workflow approvals follow this hierarchy where applicable.

---

# 14. Application Structure

A recommended Django project structure:

```text
sitadc_youth_hub/
│
├── accounts/
├── dashboard/
├── leadership/
├── memberships/
├── volunteers/
├── beneficiaries/
├── partners/
├── programs/
├── projects/
├── meal/
├── reports/
├── approvals/
├── documents/
├── registers/
├── references/
├── meetings/
├── notifications/
├── audit/
├── finance/
├── communications/
├── settings_app/
├── templates/
├── static/
├── media/
├── config/
└── manage.py
```

Each application is responsible for a specific business domain.

---

# 15. Development Standards

Development follows:

* Modular architecture
* Separation of concerns
* Reusable components
* Clean code principles
* PEP 8 coding standards
* Django best practices
* Migration-based database changes
* Comprehensive documentation
* Automated testing where applicable

---

# 16. Performance Considerations

The system should:

* Minimize database queries
* Use ORM optimization (`select_related`, `prefetch_related`)
* Paginate large datasets
* Cache frequently accessed content where appropriate
* Optimize static assets
* Compress media for web delivery

---

# 17. Scalability

The architecture is designed to support:

* Additional organizational modules
* Increased user volume
* Larger datasets
* Future API integrations
* Migration from SQLite to PostgreSQL
* Cloud deployment
* Background task processing

Scalability is achieved without major architectural redesign.

---

# 18. Documentation

The project documentation includes:

* README.md
* AGENTS.md
* ARCHITECTURE.md
* CONTRIBUTING.md
* SECURITY.md
* CODE_OF_CONDUCT.md
* CHANGELOG.md
* Development Roadmaps
* API Documentation
* User Guides
* Administrator Guides

---

# 19. Design Principles

The architecture follows:

* Keep It Simple (KISS)
* Don't Repeat Yourself (DRY)
* Separation of Concerns (SoC)
* Single Responsibility Principle (SRP)
* Open/Closed Principle
* Secure by Default
* Convention over Configuration

These principles guide all development decisions.

---

# 20. Future Enhancements

The architecture supports future expansion, including:

* PostgreSQL migration
* REST API integration
* Mobile application support
* Cloud object storage
* Email and SMS notifications
* Real-time updates
* Advanced analytics
* Third-party integrations
* AI-assisted reporting
* Multi-organization support

---

# 21. Architecture Maintenance

This document shall be reviewed and updated whenever:

* New modules are introduced.
* Major architectural changes occur.
* Core technologies are replaced or upgraded.
* Security architecture changes.
* Database architecture changes.
* Deployment architecture changes.

Maintaining this document ensures that the SITADC Youth Hub remains consistent, scalable, secure, and aligned with the organization's long-term strategic goals.
