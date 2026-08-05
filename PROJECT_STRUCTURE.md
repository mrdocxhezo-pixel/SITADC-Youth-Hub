# PROJECT_STRUCTURE.md

# SITADC Youth Hub

## Project Structure

**Project:** SITADC Youth Hub

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

**Version:** 1.0.0

**Status:** Active

---

# Purpose

This document defines the official folder and file structure for the SITADC Youth Hub project.

The objectives are to:

* Maintain consistency
* Improve scalability
* Simplify navigation
* Support modular development
* Improve maintainability
* Enable AI-assisted development
* Support future expansion

Every contributor and AI coding agent should follow this structure.

---

# High-Level Project Structure

```text
sitadc-youth-hub/
│
├── .github/
│   ├── workflows/
│   └── ISSUE_TEMPLATE/
│
├── docs/
│
├── roadmaps/
│
├── config/
│
├── sitadc_youth_hub/
│
├── accounts/
├── dashboard/
├── leadership/
├── membership/
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
├── meetings/
├── notifications/
├── audit/
├── finance/
├── communications/
├── settings_app/
│
├── templates/
├── static/
├── media/
├── tests/
│
├── manage.py
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── AGENTS.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── SECURITY.md
├── DEVELOPMENT_STATUS.md
├── DEFINITION_OF_DONE.md
├── NAMING_CONVENTIONS.md
├── PROJECT_STRUCTURE.md
└── LICENSE
```

---

# Root Directory

The root directory contains:

* Django entry point
* Project documentation
* Development configuration
* Dependency files
* Git configuration
* CI/CD configuration

Only project-level files should exist here.

---

# Django Project Configuration

```text
sitadc_youth_hub/

├── __init__.py
├── settings.py
├── urls.py
├── asgi.py
├── wsgi.py
└── context_processors.py
```

This directory contains the global Django configuration.

---

# Django Applications

Each business domain should be implemented as a separate Django application.

```text
accounts/
dashboard/
leadership/
membership/
volunteers/
beneficiaries/
partners/
programs/
projects/
meal/
reports/
approvals/
documents/
registers/
references/
meetings/
notifications/
audit/
finance/
communications/
settings_app/
```

Each application should remain independent and reusable.

---

# Standard Django App Structure

Every application should follow the same internal structure.

```text
app_name/

├── migrations/
├── templates/
├── static/
├── admin.py
├── apps.py
├── forms.py
├── models.py
├── urls.py
├── views.py
├── services.py
├── permissions.py
├── validators.py
├── signals.py
├── tests.py
└── utils.py
```

Additional files may be added where appropriate without breaking modularity.

---

# Templates

Global templates should be stored in:

```text
templates/

├── base/
├── authentication/
├── dashboard/
├── leadership/
├── membership/
├── volunteers/
├── reports/
├── documents/
├── errors/
└── shared/
```

Use reusable template components where possible.

---

# Static Files

```text
static/

├── css/
├── js/
├── images/
├── icons/
├── fonts/
└── vendors/
```

### CSS

```text
static/css/

base.css
dashboard.css
reports.css
forms.css
tables.css
```

### JavaScript

```text
static/js/

dashboard.js
reports.js
charts.js
notifications.js
```

### Images

```text
static/images/

logo.png
favicon.ico
banners/
backgrounds/
illustrations/
```

---

# Media Directory

User-generated content should be stored separately.

```text
media/

profiles/
documents/
reports/
evidence/
meeting_minutes/
policies/
mous/
images/
exports/
```

Media files should never be committed to version control.

---

# Documentation Directory

```text
docs/

api/
architecture/
deployment/
user-guides/
admin-guides/
developer-guides/
training/
```

This folder contains extended documentation beyond the root Markdown files.

---

# Development Roadmaps

```text
roadmaps/

00-Master-Development-Roadmap.md
01-Project-Foundation.md
02-Development-Environment-and-Tooling.md
...
38-Final-Acceptance-and-Production-Release.md
```

These documents define the implementation sequence for the project.

---

# Configuration Directory

```text
config/

logging.py
email.py
storage.py
security.py
constants.py
permissions.py
```

Configuration should be centralized and reusable.

---

# Test Structure

```text
tests/

unit/
integration/
functional/
performance/
security/
```

Tests should be organized by type rather than mixed together.

---

# GitHub Configuration

```text
.github/

workflows/
ISSUE_TEMPLATE/
PULL_REQUEST_TEMPLATE.md
CODEOWNERS
```

This directory contains automation and repository configuration.

---

# Requirements Files

```text
requirements.txt
requirements-dev.txt
```

* `requirements.txt` contains production dependencies.
* `requirements-dev.txt` contains development and testing tools.

---

# Environment Configuration

Environment-specific settings should be managed through environment variables.

Examples include:

* `SECRET_KEY`
* `DEBUG`
* `DATABASE_URL`
* `ALLOWED_HOSTS`
* `EMAIL_HOST`
* `EMAIL_PORT`

Sensitive configuration files must not be committed to version control.

---

# SQLite Database

During development, the database file will typically reside in the project root.

```text
db.sqlite3
```

This file is generated automatically by Django after migrations are run.

---

# File Organization Principles

Every file should have a clear purpose.

General rules:

* One responsibility per module.
* Avoid deeply nested directories.
* Group related files together.
* Keep configuration centralized.
* Reuse components instead of duplicating them.

---

# Adding New Modules

When introducing a new module:

1. Create a new Django application.
2. Follow the standard app structure.
3. Register the app in `INSTALLED_APPS`.
4. Create initial migrations.
5. Add URLs.
6. Add templates.
7. Add tests.
8. Update documentation.

---

# Files That Should Never Be Committed

Examples include:

```text
.env
.env.local
__pycache__/
*.pyc
db.sqlite3
media/
*.log
.coverage
.pytest_cache/
```

These should be listed in `.gitignore`.

---

# Project Structure Maintenance

This document should be updated whenever:

* A new Django application is added.
* Directory structures change.
* New documentation categories are introduced.
* Deployment architecture changes.
* Testing structure changes.
* Static or media organization changes.

Maintaining a consistent project structure ensures the SITADC Youth Hub remains scalable, organized, and easy to maintain as development progresses.
