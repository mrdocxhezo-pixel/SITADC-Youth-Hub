# SITADC Youth Hub

A secure, modular, responsive, and configurable organizational management, reporting, documentation, accountability, monitoring, evaluation, learning, collaboration, and decision-support web application for the **Sustainable Initiatives Through Transformative Actions for Development in Communities — SITADC Youth Organization**.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Organizational Background](#organizational-background)
3. [Project Vision](#project-vision)
4. [Project Objectives](#project-objectives)
5. [Core Features](#core-features)
6. [Technology Stack](#technology-stack)
7. [System Architecture](#system-architecture)
8. [Main Modules](#main-modules)
9. [User Roles](#user-roles)
10. [Organizational Structure](#organizational-structure)
11. [Report Categories](#report-categories)
12. [Report Workflow](#report-workflow)
13. [Security](#security)
14. [Accessibility](#accessibility)
15. [Project Structure](#project-structure)
16. [Development Requirements](#development-requirements)
17. [Installation](#installation)
18. [Environment Configuration](#environment-configuration)
19. [Database Setup](#database-setup)
20. [Running the Application](#running-the-application)
21. [Testing](#testing)
22. [Code Quality](#code-quality)
23. [Static and Media Files](#static-and-media-files)
24. [Development Workflow](#development-workflow)
25. [Development Roadmap](#development-roadmap)
26. [Definition of Done](#definition-of-done)
27. [Deployment](#deployment)
28. [Backup and Recovery](#backup-and-recovery)
29. [Contributing](#contributing)
30. [License](#license)
31. [Support](#support)

---

# Project Overview

The **SITADC Youth Hub** is the official organizational management platform for SITADC Youth Organization.

The system is designed to centralize and digitize the organization’s operational, administrative, leadership, programmatic, reporting, governance, accountability, and learning processes.

It provides one integrated platform for managing:

* Leaders
* Members
* Volunteers
* Programs
* Projects
* Activities
* Tasks
* Beneficiaries
* Partners
* Sponsors
* Donors
* Stakeholders
* Reports
* Documents
* Meetings
* Events
* Indicators
* Monitoring visits
* Evaluations
* Risks
* Complaints
* Safeguarding cases
* Organizational registers
* Reviews
* Approvals
* Notifications
* Audit logs
* Dashboards
* Organizational learning

The application replaces fragmented paper files, spreadsheets, messaging threads, email-based approvals, and disconnected storage systems with a secure and structured digital platform.

---

# Organizational Background

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities — SITADC Youth Organization

**Established:** 2021

**Registration:** Registered under the National Youth Development Council in Zambia in 2023.

**Mission:** Amplifying Digital Skills Through Innovations and Education.

**Vision:** To empower young people for sustainable living and meaningful economic participation through digitalized innovations, education, skills development, leadership, health, entrepreneurship, and community transformation.

## Core Values

* Youth Leadership
* Innovation and Creativity
* Integrity
* Inclusiveness
* Accountability
* Equity
* Sustainability

## Main Program Pillars

1. Education, Digital Literacy and Innovation
2. Entrepreneurship, Employability and Skills Development
3. Leadership, Civic Engagement and Community Development
4. Health, Well-being and Youth Empowerment

---

# Project Vision

The SITADC Youth Hub will serve as a digital organizational headquarters where authorized users can plan, coordinate, implement, monitor, evaluate, document, report, review, approve, learn, and make evidence-based decisions.

The platform must operate as one interconnected system rather than a collection of isolated pages.

All major modules must share common:

* Users
* Roles
* Permissions
* Organizational units
* Reporting lines
* Programs
* Projects
* Activities
* Reporting periods
* Workflows
* Documents
* Notifications
* Reference numbers
* Status histories
* Audit records

---

# Project Objectives

The SITADC Youth Hub aims to:

* Centralize organizational information.
* Improve accountability and transparency.
* Strengthen leadership and volunteer management.
* Improve program and project coordination.
* Standardize organizational reporting.
* Simplify review and approval workflows.
* Improve monitoring, evaluation, accountability, and learning.
* Strengthen stakeholder and partnership management.
* Protect sensitive organizational information.
* Improve document and records management.
* Track organizational performance.
* Support evidence-based decision-making.
* Preserve institutional knowledge.
* Strengthen governance and compliance.
* Improve reporting timeliness and quality.
* Support sustainable organizational growth.

---

# Core Features

The system will support:

* Invitation-based account registration
* Administrative account approval
* Role-based access control
* Organizational-scope permissions
* User and profile management
* Leader management
* Membership management
* Volunteer lifecycle management
* Program management
* Project management
* Activity and task tracking
* Beneficiary management
* Stakeholder management
* Partner, sponsor, and donor management
* MEAL frameworks and indicators
* Dynamic report-template creation
* Report drafting and autosave
* Review and approval workflows
* Document version control
* Centralized organizational registers
* Meeting and event management
* Calendar management
* Notifications and announcements
* Global permission-aware search
* PDF, DOCX, XLSX, CSV, and authorized JSON exports
* Configurable dashboards
* Audit logging
* Risk and compliance management
* Safeguarding and accountability controls
* Light and dark themes
* Responsive mobile, tablet, and desktop layouts
* Accessibility support

---

# Technology Stack

The project must use the following technologies.

## Backend

* Python
* Django
* Django Templates
* Django Forms
* Django ModelForms
* Django ORM
* Django Authentication
* Django Permissions
* Django Groups
* Django Sessions
* Django Admin
* Django Middleware
* Django Signals where appropriate
* Django Management Commands

## Frontend

* HTML5
* CSS3
* Bootstrap 5
* Vanilla JavaScript
* Django Template Language
* Bootstrap Icons

## Database

* SQLite

SQLite is the initial development database.

The database architecture must remain compatible with a future migration to PostgreSQL.

## Testing and Quality Tools

* pytest
* pytest-django
* coverage
* Ruff
* Black
* isort
* mypy
* Bandit
* djLint
* ESLint
* Prettier
* Stylelint
* pre-commit

## Export Support

The project may use maintained Python packages for:

* PDF generation
* DOCX generation
* XLSX generation
* CSV generation
* QR-code generation
* Image processing
* File validation

All dependencies must be version-pinned and documented.

## Prohibited Replacements

Do not replace the required stack with:

* React
* Next.js
* Angular
* Vue
* Svelte
* Laravel
* Firebase
* Supabase
* MongoDB
* WordPress
* Node.js as the primary backend

---

# System Architecture

The SITADC Youth Hub follows a modular Django architecture.

Each major organizational domain should be implemented as a separate Django application while using shared core services.

Recommended shared services include:

* Permission evaluation
* Organizational-scope filtering
* Reference-number generation
* Workflow transitions
* Audit logging
* Notification delivery
* Export generation
* File validation
* Document versioning
* Status history
* Search
* Reporting-period calculations
* Archiving
* Soft deletion

Business logic should not be placed directly in templates or oversized views.

Use service-layer functions for complex operations.

---

# Main Modules

## Core and Configuration

Provides:

* Shared models
* Shared utilities
* System settings
* Organization profile
* Branding
* Statuses
* Reporting periods
* Numbering formats
* Confidentiality levels
* Workflow settings

## Accounts and Authentication

Provides:

* Login
* Logout
* Invitation-based registration
* Account approval
* Password reset
* Profile management
* Account suspension
* Session management
* Authentication history

## Roles and Permissions

Provides:

* Roles
* Django groups
* Custom permissions
* Access scopes
* Role assignments
* Permission matrices
* Scope-based query filtering

## Organizational Structure

Provides:

* Directorates
* Departments
* Regions
* Districts
* Communities
* Teams
* Committees
* Units
* Positions
* Reporting lines

## Reference Numbering

Provides:

* Numbering schemes
* Configurable number patterns and tokens
* Per-period sequences
* Reference registry
* Numbering audit trail
* Preview without consumption
* Lifecycle management (reserve, assign, cancel, void)

## Leadership

Provides:

* Leader profiles
* Appointments
* Terms
* Responsibilities
* Performance targets
* Coaching
* Mentorship
* Succession readiness
* Position history

## Membership and Volunteers

### Membership

Provides:

* Member registration
* Membership applications and approval workflow
* Configurable membership categories, types, levels, and statuses
* Membership renewals, upgrades, transfers, and suspensions
* Membership termination and exit/alumni records
* Membership ID generation, membership cards, and QR codes
* Attendance, participation, committees, skills, interests, and training
* Membership fees, payments, receipts, discounts, and waivers
* Membership communications and documents
* Immutable status history and audit logging
* Membership dashboards, analytics, and reports

### Volunteers

Implemented capabilities:

* Permission-scoped volunteer registry, profiles, directory, and dashboard
* Public recruitment applications with consent and private CV storage
* Centralized `VOL`, `VAP`, and `VRC` reference numbers with assignment confirmation
* Validated application, screening, interview, approval, and onboarding transitions
* Assignments, attendance and service hours, training, performance, recognition, leave, and exit
* Immutable status history and volunteer audit records
* Role-based confidential-field controls and permission-checked CV downloads
* Formula-safe, permission-scoped CSV register exports with audit logging
* Responsive Bootstrap 5 forms with labels, required indicators, errors, and pagination

Phase 13 remains in stabilization because configurable database-backed volunteer taxonomies, activity/disciplinary workflows, complete document lifecycle management, and PDF/DOCX/XLSX reports are not yet implemented. See `docs/user-guides/VOLUNTEER_MANAGEMENT_GUIDE.md` and `docs/development/PHASE13_VOLUNTEER_MANAGEMENT_REPORT.md`.

## Stakeholders

Implemented Phase 14 capabilities:

* Permission-scoped stakeholder, partner, donor, sponsor, government, and community directories
* Configurable categories, relationship types, classifications, sectors, focus areas, SDGs, engagement levels, agreement types, contribution types, and risk data
* Central `STK`, `SEG`, `SAG`, `SCM`, `SCN`, `SAS`, `SPF`, and `SDD` reference numbers
* Reasoned lifecycle transitions with immutable status history, archive, and restore
* Private multi-contact management with one active primary contact
* Power-interest mapping using `>= 3` as high, explicit quadrants, completeness, missing fields, and no imputation
* Engagement plans, meetings/consultations, communication history, commitments, and contributions
* Agreement review, approval, signature, activation, immutable versions, expiry, termination, and renewal into a new agreement
* Due diligence, conflict declarations, likelihood-impact risks, weighted scorecards, and follow-up actions
* Versioned confidential notes and private, validated, permission-checked documents
* Operational module dashboard, scoped reports, formula-safe CSV register export, 47 named routes, and four maintenance/validation commands

Phase 14 was formally accepted on 2026-08-03 after repository quality, browser/axe, manual NVDA, stakeholder UAT, privacy/security, PostgreSQL concurrency, and target LAN HTTPS sustained-load validation passed. The central Audit and Dashboard apps remain deferred; immutable domain histories/versions, structured logging, and the operational module dashboard do not constitute those central integrations. PDF, DOCX, and XLSX remain later Export Engine targets. See `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md` and `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`.

## Programs and Projects

Provides:

* Program profiles
* Project profiles
* Objectives
* Work plans
* Activities
* Tasks
* Deliverables
* Milestones
* Budgets
* Risks
* Issues
* Teams
* Evidence
* Closure records

## Beneficiaries

Provides:

* Beneficiary registration
* Consent
* Program participation
* Attendance
* Services received
* Outcomes
* Referrals
* Follow-up
* Privacy controls

## MEAL

Provides:

* Results frameworks
* Theories of change
* Indicators
* Baselines
* Targets
* Actual results
* Monitoring visits
* Evaluations
* Data-quality assessments
* Performance scorecards
* Learning logs
* Accountability and feedback

## Reports

Provides:

* Report categories
* Dynamic templates
* Report forms
* Drafts
* Autosave
* Submission
* Review
* Approval
* Comments
* Evidence
* Versioning
* Export

## Reviews and Approvals

Provides:

* Reviewer inbox
* Approval queue
* Section comments
* General comments
* Return for correction
* Recommendation
* Approval
* Rejection
* Version comparison
* Decision history

## Documents

Provides:

* Upload
* Classification
* Version control
* Metadata
* Ownership
* Approval
* Expiry
* Retention
* Archiving
* Secure access
* Search
* Download logging

## Registers

Provides centralized registers for:

* Members
* Volunteers
* Beneficiaries
* Leaders
* Training
* Attendance
* Stakeholders
* Partners
* Donors
* Assets
* Risks
* Issues
* Complaints
* Actions
* Decisions
* Policies
* Meetings
* Grants
* Proposals

## Meetings and Calendar

Provides:

* Organizational calendars
* Reporting calendars
* Meetings
* Agendas
* Minutes
* Attendance
* Decisions
* Action items
* Events
* Reminders

## Notifications

Provides:

* In-app notifications
* Optional email notifications
* Deadline reminders
* Approval alerts
* Assignment alerts
* Document-expiry alerts
* Announcements
* Escalations

## Dashboards and Analytics

Provides role-aware dashboards for:

* Administrators
* Board members
* Executive management
* Directors
* Coordinators
* Staff
* Volunteers
* Partners
* Donors
* Sponsors
* MEAL officers
* Reviewers
* Approvers

## Audit Logs

Records:

* Authentication events
* Data creation
* Data updates
* Deletions
* Restorations
* Report submissions
* Review decisions
* Approval decisions
* File access
* Exports
* Role changes
* Permission changes
* Configuration changes

---

# User Roles

The system may include the following roles:

* Super Administrator
* System Administrator
* Board Chairperson
* Board Secretary
* Board Member
* President
* Vice President
* Executive Director
* Executive Secretary
* Secretary General
* National Executive Committee Member
* Director
* Deputy Director
* Regional Coordinator
* District Coordinator
* Community Coordinator
* Team Leader
* Program Manager
* Project Manager
* Project Officer
* MEAL Officer
* Finance Officer
* Membership Officer
* Volunteer Officer
* Communications Officer
* Training Officer
* Research Officer
* Partnerships Officer
* Resource Mobilization Officer
* Quality Assurance Officer
* Safeguarding Officer
* Legal and Governance Officer
* Staff Member
* Member
* Volunteer
* Partner Representative
* Sponsor Representative
* Donor Representative
* Stakeholder Representative
* Auditor
* Read-Only User

Roles and permissions must remain configurable.

Access must not depend only on role names.

The system must also consider:

* Organizational scope
* Geographic scope
* Record ownership
* Program assignment
* Project assignment
* Workflow assignment
* Confidentiality
* Explicit sharing

---

# Organizational Structure

Recommended reporting hierarchy:

```text
General Assembly
└── Board of Trustees
    └── National Executive Committee
        └── Executive Director / Executive Secretary
            └── Directorates
                └── Regional Coordinators
                    └── District Coordinators
                        └── Community Coordinators
                            └── Team Leaders
                                └── Volunteers and Members
```

The hierarchy must be configurable and must not be permanently hard-coded.

## Recommended Directorates

1. Programs and Project Management
2. Monitoring, Evaluation, Accountability and Learning
3. Operations and Administration
4. Finance and Resource Management
5. Human Resources and Organizational Development
6. Membership and Volunteer Services
7. Partnerships, Resource Mobilization and External Relations
8. Communications, Media and Public Relations
9. ICT and Digital Innovation
10. Research, Innovation and Knowledge Management
11. Training and Capacity Development
12. Governance, Legal Affairs and Compliance
13. Quality Assurance, Risk and Safeguarding
14. Stakeholder Engagement and Community Relations
15. Events, Protocol and Special Initiatives
16. Enterprise Development and Sustainability

---

# Report Categories

The report-management system should support configurable categories including:

* Organizational Governance
* Leadership
* Program Management
* Membership and Volunteer Management
* Monitoring, Evaluation, Accountability and Learning
* Finance
* Partnerships, Sponsors and Donors
* Communications and Media
* Training and Capacity Building
* Meetings and Events
* Safeguarding and Protection
* Administration and Operations
* Quality Assurance
* Risk and Compliance
* Organizational Learning
* Organizational Registers

Administrators must be able to:

* Add report categories
* Edit report categories
* Reorder report categories
* Deactivate report categories
* Archive report categories
* Add report templates
* Version report templates
* Assign reporting frequencies
* Assign workflows
* Assign responsible roles
* Assign reviewer roles
* Assign approver roles

---

# Report Workflow

The standard report workflow is:

```text
Draft
→ Submitted
→ Under Review
→ Returned for Correction
→ Resubmitted
→ Recommended for Approval
→ Pending Approval
→ Approved
```

Additional statuses may include:

* Incomplete
* Rejected
* Withdrawn
* Cancelled
* Reopened
* Superseded
* Archived

Every transition must record:

* Actor
* Previous status
* New status
* Date and time
* Comments
* Reason
* Version
* Assignment
* Decision

Approved reports must be locked.

Reopening an approved report requires special permission, a written reason, a new version, and a complete audit record.

---

# Security

Security must be implemented at the server level.

Hiding a button or menu item is not sufficient authorization.

## Required Security Controls

* Django authentication
* Role-based access control
* Scope-based access control
* Server-side permission checks
* CSRF protection
* XSS protection
* Secure password hashing
* Secure sessions
* Login throttling where practical
* Strong file validation
* Secure downloads
* Environment-based secrets
* Audit logging
* Confidentiality classifications
* Least-privilege access
* Soft deletion
* Data-retention controls
* Privacy-aware exports

## Sensitive Information

Strictly protect:

* Beneficiary identities
* Safeguarding cases
* Complaints
* Whistleblower records
* Health information
* Personnel records
* Financial information
* Board documents
* Donor due-diligence records
* Signed agreements
* Evaluation datasets
* Confidential evidence

Sensitive files must not be served using unrestricted public URLs.

---

# Accessibility

The application should follow WCAG-oriented accessibility practices.

Required features include:

* Semantic HTML5
* Accessible heading structure
* Keyboard navigation
* Visible focus states
* Proper form labels
* Accessible error summaries
* Screen-reader support
* Sufficient color contrast
* Reduced-motion support
* Accessible tables
* Text alternatives for charts
* Accessible dialogs
* Focus trapping
* Focus restoration

Status must never be communicated through color alone.

---

# Project Structure

The final structure may evolve, but the recommended root structure is:

```text
sitadc-youth-hub/
├── AGENTS.md
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── manage.py
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── config/
│   ├── __init__.py
│   ├── asgi.py
│   ├── urls.py
│   ├── wsgi.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── development.py
│       └── production.py
├── apps/
│   ├── core/
│   ├── accounts/
│   ├── organizations/
│   ├── permissions/
│   ├── dashboard/
│   ├── leadership/
│   ├── memberships/
│   ├── volunteers/
│   ├── stakeholders/
│   ├── programs/
│   ├── projects/
│   ├── beneficiaries/
│   ├── meal/
│   ├── reports/
│   ├── workflows/
│   ├── documents/
│   ├── registers/
│   ├── meetings/
│   ├── calendar_events/
│   ├── notifications/
│   ├── governance/
│   ├── risk_compliance/
│   ├── safeguarding/
│   ├── finance/
│   ├── communications/
│   ├── audit/
│   ├── search/
│   ├── exports/
│   └── configuration/
├── templates/
│   ├── base/
│   ├── components/
│   ├── errors/
│   └── registration/
├── static/
│   ├── css/
│   ├── js/
│   ├── images/
│   ├── icons/
│   └── vendor/
├── media/
├── locale/
├── tests/
├── docs/
│   ├── architecture/
│   ├── development/
│   ├── security/
│   ├── deployment/
│   └── user-guides/
├── roadmaps/
├── scripts/
└── .github/
    └── workflows/
```

The exact structure may be adjusted where technically justified.

All changes must remain consistent with `AGENTS.md`.

---

# Development Requirements

## Recommended Software

* Python 3.12 or 3.13 (Django 5.0.7 support range)
* pip
* virtualenv or `venv`
* Git
* SQLite
* Node.js only for frontend quality tools where required
* Modern web browser

Confirm the supported Python and Django versions in the project dependency files.

---

# Installation

## 1. Clone the Repository

```bash
git clone <repository-url>
cd sitadc-youth-hub
```

## 2. Create a Virtual Environment

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Upgrade pip

```bash
python -m pip install --upgrade pip
```

## 4. Install Dependencies

During early project setup:

```bash
pip install -r requirements/development.txt
```

For production:

```bash
pip install -r requirements/production.txt
```

## 5. Create the Environment File

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Update the values in `.env` before running the application.

---

# Environment Configuration

The `.env` file may include:

```env
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=replace-with-a-secure-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DEFAULT_FROM_EMAIL=no-reply@example.org
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
TIME_ZONE=Africa/Lusaka
```

Never commit the real `.env` file.

Never hard-code:

* Secret keys
* Passwords
* Email credentials
* API keys
* Storage credentials
* Production domain secrets

---

# Database Setup

Apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Load development seed data where available:

```bash
python manage.py seed_development_data
```

The exact seed command may change as the project develops.

Do not commit development database files unless the project explicitly defines an approved exception.

---

# Running the Application

Start the Django development server:

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

To run on another local port:

```bash
python manage.py runserver 8080
```

---

# Testing

Run the complete test suite:

```bash
pytest
```

Run tests with coverage:

```bash
coverage run -m pytest
coverage report
```

Generate an HTML coverage report:

```bash
coverage html
```

Open:

```text
htmlcov/index.html
```

Run a specific app’s tests:

```bash
pytest apps/accounts/tests/
```

Run a specific test:

```bash
pytest apps/accounts/tests/test_permissions.py::test_user_cannot_access_other_scope
```

Critical areas that must be tested include:

* Authentication
* Registration approval
* Roles
* Permissions
* Organizational scope
* Reference-number generation
* Report workflow
* Review and approval
* Document versioning
* Secure downloads
* Exports
* Search
* Audit logging
* Confidential records

---

# Code Quality

## Format Python

```bash
black .
```

## Sort Imports

```bash
isort .
```

## Run Ruff

```bash
ruff check .
```

Apply safe Ruff fixes:

```bash
ruff check . --fix
```

## Run Type Checking

```bash
mypy .
```

## Run Security Checks

```bash
bandit -r apps config
```

## Check Django Templates

```bash
djlint templates --check
```

## Format Django Templates

```bash
djlint templates --reformat
```

## Run Django Checks

```bash
python manage.py check
```

Run production-oriented checks:

```bash
python manage.py check --deploy
```

## Run Pre-commit

```bash
pre-commit run --all-files
```

No feature should be marked complete when relevant quality checks are failing.

---

# Static and Media Files

## Static Files

Static files include:

* CSS
* JavaScript
* Icons
* Public images
* Vendor assets

Collect static files for production:

```bash
python manage.py collectstatic
```

## Media Files

Media files include user-uploaded content such as:

* Profile photographs
* Evidence files
* Documents
* Agreements
* Meeting attachments
* Report attachments

Protected media must be accessed through permission-checked application views.

Do not assume all uploaded files are public.

---

# Development Workflow

Before implementing any task:

1. Read `AGENTS.md`.
2. Read this `README.md`.
3. Read the active roadmap file.
4. Inspect the existing project.
5. Identify completed dependencies.
6. Identify the active development phase.
7. List files that will be created or modified.
8. Preserve valid existing work.
9. Implement the feature.
10. Add permissions.
11. Add validation.
12. Add audit logging where applicable.
13. Add tests.
14. Run quality checks.
15. Update documentation.
16. Provide a delivery report.

## Required Delivery Report

Every completed development task should report:

* Task summary
* Active phase
* Files created
* Files modified
* Database changes
* Permissions and security controls
* UI and accessibility changes
* Tests added
* Commands run
* Test and quality results
* Known limitations
* Next recommended task

---

# Development Roadmap

The recommended development sequence is:

1. Phase 00 — Project Governance and Documentation
2. Phase 01 — Project Foundation
3. Phase 02 — Development Environment and Tooling
4. Phase 03 — Django Core Architecture
5. Phase 04 — Authentication and Accounts
6. Phase 05 — Roles, Permissions, and Access Scopes
7. Phase 06 — Organizational Structure
8. Phase 07 — Reference Numbering
9. Phase 08 — Audit Logging
10. Phase 09 — UI Design System
11. Phase 10 — Dashboard
12. Phase 11 — Leadership Management
13. Phase 12 — Membership Management
14. Phase 13 — Volunteer Management
15. Phase 14 — Stakeholder Management
16. Phase 15 — Program Management
17. Beneficiary Management
18. MEAL
19. Dynamic Report Template Builder
20. Report Management
21. Review and Approval
22. Document Management
23. Registers
24. Meetings and Calendar
25. Notifications and Announcements
26. Dashboards and Analytics
27. Search
28. Export Engine
29. Governance, Risk, Compliance, and Safeguarding
30. Finance and Resource Mobilization
31. System Configuration
32. Security Review
33. Accessibility Review
34. Performance Review
35. Full Testing
36. Documentation and Training
37. Deployment Preparation
38. Final Acceptance and Handover

Do not skip dependencies.

Refer to the files inside the `roadmaps/` directory for detailed phase requirements.

---

# Definition of Done

A feature is complete only when:

* Requirements are implemented.
* Models and migrations are valid.
* Server-side permissions are enforced.
* Organizational-scope restrictions are enforced.
* Forms include server-side validation.
* Audit logging is implemented where required.
* Templates are responsive.
* Accessibility requirements are addressed.
* Tests are written.
* Tests pass.
* Formatting passes.
* Linting passes.
* Type checks pass where configured.
* Security checks pass.
* Django system checks pass.
* Documentation is updated.
* No critical placeholders remain.
* No unauthorized data is exposed.
* No secrets are hard-coded.
* No duplicate architecture is introduced.
* The feature connects correctly to related modules.
* A delivery report is completed.

---

# Deployment

The application must use separate development and production settings.

Before production deployment:

* Set `DEBUG=False`.
* Configure a secure secret key.
* Configure allowed hosts.
* Configure CSRF trusted origins.
* Configure HTTPS.
* Enable secure cookies.
* Configure static files.
* Configure private media storage.
* Configure email delivery.
* Configure logging.
* Configure error monitoring.
* Apply migrations.
* Run Django deployment checks.
* Create backups.
* Test restoration.
* Review permissions.
* Review administrative accounts.
* Remove development-only seed users.

Run:

```bash
python manage.py check --deploy
```

SQLite may be used for initial low-scale deployment where appropriate.

Migration to PostgreSQL should be considered when:

* Concurrent writes increase.
* The user base grows significantly.
* Reporting volume becomes high.
* Background processing increases.
* Multi-server deployment becomes necessary.
* Advanced database features are required.
* Reliability and concurrency requirements exceed SQLite’s appropriate use.

---

# Backup and Recovery

Back up:

* SQLite database
* Uploaded media
* Environment configuration
* Export templates
* Organization branding
* System configuration
* Relevant deployment files

Backups must:

* Follow an approved schedule.
* Be protected from unauthorized access.
* Be stored separately from the application server.
* Be tested through restoration exercises.
* Follow organizational retention policies.

Do not consider a backup strategy complete until restoration has been tested.

---

# Contributing

All contributors and AI development agents must follow:

* `AGENTS.md`
* The active development roadmap
* Project coding standards
* Security requirements
* Accessibility requirements
* Testing requirements
* Documentation requirements

## Branch Naming Examples

```text
feature/authentication
feature/leader-management
feature/report-workflow
fix/document-permissions
docs/deployment-guide
refactor/reference-number-service
```

## Commit Message Examples

```text
feat(accounts): add invitation approval workflow
feat(reports): implement report status transitions
fix(documents): enforce secure download permissions
test(audit): add immutable event tests
docs(setup): add Windows development instructions
```

Each commit should represent one clear logical change.

Never commit:

* `.env`
* Secret keys
* Passwords
* API credentials
* Private production data
* Unapproved database files
* Cache directories
* Temporary exports
* Uploaded sensitive documents

---

# License

The licensing terms for this project must be defined in the root `LICENSE` file.

Until a license is formally selected, the source code and project materials should be treated as proprietary to SITADC Youth Organization.

Unauthorized distribution, commercial use, copying, or deployment is not permitted without written authorization from SITADC Youth Organization.

---

# Support

For project support, implementation decisions, organizational requirements, or access authorization, contact the authorized SITADC Youth Organization project leadership.

Do not publish private contact details, credentials, or internal system information in this repository.

---

# Project Status

The project is under active development.

## Current Phase Status

| Phase | Module | Status |
| --- | --- | --- |
| 00 — Project Governance and Documentation | Governance | Complete |
| 01 — Project Foundation | Foundation | Complete |
| 02 — Development Environment and Tooling | Tooling | Complete |
| 03 — Django Core Architecture | Core | Complete |
| 04 — Authentication and Accounts | Accounts | Complete |
| 05 — Roles, Permissions, and Access Scopes | RBAC | Complete |
| 06 — Organizational Structure | Organizations | Complete |
| 07 — Reference Numbering | References | Complete |
| 08 — Audit Logging | Audit | Complete |
| 09 — UI Design System | UI | Complete |
| 10 — Dashboard | Dashboard | Complete |
| 11 — Leadership Management | Leadership | Complete |
| 12 — Membership Management | Memberships | Complete |
| 13 — Volunteer Management | Volunteers | Candidate complete — acceptance re-review passed (2026-08-03) |
| 14 — Stakeholder Management | Stakeholders | Accepted (2026-08-03) |
| 15 — Program & Project Management | Programs | Accepted (2026-08-04) |
| 16 — Project Management | Programs | Implemented (2026-08-05) |
| 17 — Beneficiary Management | Beneficiaries | Implemented (2026-08-05) |
| 18 — MEAL | Meal | Implemented (2026-08-05) |

## Next Recommended Phase

**Phase 19 — Dynamic Report Builder.**

After implementation of Phase 18, the recommended next roadmap is `roadmaps/19-Dynamic-Report-Builder.md`; Phase 18 MEAL is implemented in `apps/meal` per `roadmaps/18-MEAL.md`.

## Acceptance References

- Phase 13 delivery report: `docs/development/PHASE13_VOLUNTEER_MANAGEMENT_REPORT.md`
- Phase 13 acceptance re-review: `docs/development/PHASE13_ACCEPTANCE_REVIEW.md`
- Phase 13 external acceptance pack: `docs/development/PHASE13_EXTERNAL_ACCEPTANCE_PACK.md`
- Phase 14 delivery report: `docs/development/PHASE14_STAKEHOLDER_MANAGEMENT_REPORT.md`
- Phase 15 delivery report: `docs/development/PHASE15_*`
- Phase 16 delivery report: `docs/development/PHASE16_PROJECT_MANAGEMENT_REPORT.md`
- Phase 17 delivery report: `docs/development/PHASE17_BENEFICIARY_MANAGEMENT_REPORT.md`
- Phase 18 delivery report: `docs/development/PHASE18_MEAL_MANAGEMENT_REPORT.md`
- Phase 14 user guide: `docs/user-guides/STAKEHOLDER_MANAGEMENT_GUIDE.md`
- Phase 13 user guide: `docs/user-guides/VOLUNTEER_MANAGEMENT_GUIDE.md`

---

# Final Development Rule

The SITADC Youth Hub must be developed as one secure, connected, modular, maintainable, and production-ready organizational management platform.

Do not create disconnected demonstration pages.

Do not bypass server-side permissions.

Do not expose confidential information.

Do not replace the required technology stack.

Do not mark incomplete functionality as complete.
