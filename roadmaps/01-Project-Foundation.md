# PHASE 01 — PROJECT FOUNDATION

## SITADC Youth Hub Web Application

**Roadmap File:** `roadmaps/01-Project-Foundation.md`
**Phase Number:** 01
**Phase Name:** Project Foundation
**Current Status:** Ready
**Previous Phase:** Phase 00 — Project Governance and Development Control
**Next Phase:** Phase 02 — Development Environment and Tooling

---

# 1. PHASE PURPOSE

The purpose of Phase 01 is to establish the initial runnable foundation of the SITADC Youth Hub web application using Python, Django, SQLite, HTML5, CSS3, Bootstrap 5, and vanilla JavaScript.

This phase must transform the governed documentation-only project directory created during Phase 00 into a clean, structured, runnable Django project.

The phase must create:

* The Python development environment
* The initial Django project
* Environment-based configuration
* SQLite database configuration
* Static-file configuration
* Media-file configuration
* Root URL routing
* Shared templates
* Basic public pages
* Initial error pages
* Initial project directories
* Base development documentation
* Initial Django tests
* Initial system validation

This phase must not implement complete organizational business modules.

The objective is to establish a reliable platform on which all later SITADC Youth Hub modules will be developed.

---

# 2. PROJECT IDENTITY

## Application Name

SITADC Youth Hub

## Organization

Sustainable Initiatives Through Transformative Actions for Development in Communities — SITADC Youth Organization

## Application Type

A secure organizational management, reporting, documentation, accountability, monitoring, evaluation, learning, collaboration, governance, and decision-support web application.

## Mission

Amplifying Digital Skills Through Innovations and Education.

## Vision

Empowering young people for sustainable living and meaningful economic participation through digitalized innovations, education, skills development, leadership, health, entrepreneurship, and community transformation.

---

# 3. REQUIRED TECHNOLOGY STACK

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
* Django Admin
* Django Sessions
* Django Middleware
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

SQLite is the required initial database.

The project architecture must remain compatible with a future migration to PostgreSQL.

## Development Package Management

Use:

* Python virtual environment
* `pip`
* Version-controlled requirements files

Do not introduce an alternative Python dependency manager unless explicitly approved.

---

# 4. PROHIBITED TECHNOLOGY CHANGES

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
* Another backend framework
* Another frontend framework

Do not introduce the following during this phase:

* Django REST Framework
* GraphQL
* PostgreSQL
* MySQL
* Redis
* Celery
* Docker
* Kubernetes
* Cloud object storage
* External authentication providers
* Third-party workflow platforms
* Microservices
* Message queues

These technologies may only be introduced in later phases when explicitly required and approved.

---

# 5. PHASE ENTRY CRITERIA

Before beginning Phase 01, verify that Phase 00 has been completed.

The following files must exist:

```text
AGENTS.md
README.md
LICENSE
CHANGELOG.md
CONTRIBUTING.md
SECURITY.md
CODE_OF_CONDUCT.md
ARCHITECTURE.md
DEVELOPMENT_STATUS.md
DEFINITION_OF_DONE.md
NAMING_CONVENTIONS.md
PROJECT_STRUCTURE.md
```

The following directories must exist:

```text
roadmaps/
docs/
docs/architecture/
docs/development/
docs/security/
docs/testing/
docs/deployment/
docs/user-guides/
docs/decisions/
```

The following roadmap files must exist:

```text
roadmaps/00-Master-Development-Roadmap.md
roadmaps/01-Project-Foundation.md
roadmaps/02-Development-Environment-and-Tooling.md
```

Before writing code, the AI agent must read:

1. `AGENTS.md`
2. `README.md`
3. `ARCHITECTURE.md`
4. `DEVELOPMENT_STATUS.md`
5. `DEFINITION_OF_DONE.md`
6. `NAMING_CONVENTIONS.md`
7. `PROJECT_STRUCTURE.md`
8. `roadmaps/00-Master-Development-Roadmap.md`
9. `roadmaps/01-Project-Foundation.md`

If Phase 00 is incomplete, stop Phase 01 implementation and report the missing governance requirements.

---

# 6. PHASE OBJECTIVES

Complete the following objectives:

1. Confirm the supported Python version.
2. Create a local Python virtual environment.
3. Create the initial dependency files.
4. Install Django.
5. Create the Django project.
6. Establish the approved root project structure.
7. Configure development, base, and production settings.
8. Configure environment-variable loading.
9. Configure SQLite.
10. Configure static files.
11. Configure media files.
12. Configure root URL routing.
13. Create the initial shared `core` application.
14. Create a shared base template.
15. Create basic public pages.
16. Create custom error templates.
17. Configure Django administration access.
18. Configure project metadata.
19. Create an environment-variable example file.
20. Create a secure `.gitignore`.
21. Create initial Django tests.
22. Apply initial migrations.
23. Run Django system checks.
24. Confirm that the development server starts.
25. Update project documentation.
26. Update project-development status.

---

# 7. REQUIRED PROJECT STRUCTURE

Create the following runnable project structure:

```text
sitadc-youth-hub/
├── .env.example
├── .gitignore
├── AGENTS.md
├── README.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── ARCHITECTURE.md
├── DEVELOPMENT_STATUS.md
├── DEFINITION_OF_DONE.md
├── NAMING_CONVENTIONS.md
├── PROJECT_STRUCTURE.md
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
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── migrations/
│       │   └── __init__.py
│       ├── models.py
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── test_urls.py
│       │   └── test_views.py
│       ├── urls.py
│       └── views.py
├── templates/
│   ├── base.html
│   ├── components/
│   │   ├── footer.html
│   │   ├── messages.html
│   │   └── public_navbar.html
│   ├── core/
│   │   ├── about.html
│   │   └── home.html
│   └── errors/
│       ├── 400.html
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
├── static/
│   ├── css/
│   │   └── app.css
│   ├── images/
│   │   └── README.md
│   └── js/
│       └── app.js
├── media/
│   └── .gitkeep
├── tests/
│   └── __init__.py
├── scripts/
├── docs/
└── roadmaps/
```

Do not create all future business applications during this phase.

Only create the shared `core` application.

The future application directories described in `ARCHITECTURE.md` will be created in their respective development phases.

---

# 8. PYTHON VERSION

Use a currently supported Python version approved for the project.

The recommended initial version is:

```text
Python 3.12
```

Before using it, confirm that it is compatible with the selected Django version.

Document the selected versions in:

* `README.md`
* `requirements/base.txt`
* `pyproject.toml`
* Development setup documentation

Do not claim compatibility with versions that have not been tested.

---

# 9. DJANGO VERSION

Select a supported stable Django release.

Prefer a Django Long-Term Support release when appropriate for the project timeline.

Pin the selected version in:

```text
requirements/base.txt
```

Example structure:

```text
Django==<approved-version>
python-dotenv==<approved-version>
```

Do not use unpinned dependency ranges for the application’s primary dependencies.

Before finalizing dependency versions:

* Confirm compatibility with the selected Python version.
* Confirm that the packages are actively maintained.
* Confirm that no critical security issues are known.
* Document the selected versions.

---

# 10. VIRTUAL ENVIRONMENT

Create a virtual environment in the project root:

```text
.venv/
```

Recommended commands:

## Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

## Windows Command Prompt

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

## Linux and macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

The virtual environment must be excluded from Git.

Add the following to `.gitignore`:

```text
.venv/
venv/
env/
```

---

# 11. REQUIREMENTS FILES

Create:

```text
requirements/base.txt
requirements/development.txt
requirements/production.txt
```

## Base Requirements

`requirements/base.txt` must contain the minimum runtime dependencies required by the application.

At this phase, it should include only essential packages such as:

* Django
* Environment-variable loader

Do not add future packages speculatively.

## Development Requirements

`requirements/development.txt` must include:

```text
-r base.txt
```

Detailed quality-control dependencies will be added in Phase 02.

## Production Requirements

`requirements/production.txt` must include:

```text
-r base.txt
```

Production-server and deployment dependencies will be added during the deployment phase unless an earlier phase explicitly requires them.

---

# 12. PYPROJECT.TOML

Create an initial `pyproject.toml`.

It must define at least:

* Project name
* Project description
* Initial development version
* Python requirement
* Basic project metadata
* Formatting defaults where appropriate
* Tool sections reserved for Phase 02 configuration

Use a pre-release development version such as:

```text
0.1.0-dev
```

Do not claim that the project has reached a production release.

Example project name:

```text
sitadc-youth-hub
```

The file must remain consistent with:

* `README.md`
* `CHANGELOG.md`
* Requirements files
* The selected Python version

Do not duplicate dependency declarations in incompatible ways.

---

# 13. DJANGO PROJECT CREATION

Create the Django project using:

```text
config
```

The root management command must be:

```text
manage.py
```

Recommended command:

```bash
django-admin startproject config .
```

After project creation, refactor the generated settings into:

```text
config/settings/base.py
config/settings/development.py
config/settings/production.py
```

Update:

* `manage.py`
* `config/asgi.py`
* `config/wsgi.py`

The default development settings module must be:

```text
config.settings.development
```

Do not leave the original single-file `config/settings.py` after the settings package has been established.

---

# 14. SETTINGS ARCHITECTURE

## Base Settings

Create:

```text
config/settings/base.py
```

It must contain settings shared by all environments, including:

* Base directory
* Installed applications
* Middleware
* Template configuration
* Authentication password validators
* Internationalization
* Static-file settings
* Media settings
* Default auto field
* Common security defaults
* Common application settings

Do not put development-only or production-only values directly in the base settings.

## Development Settings

Create:

```text
config/settings/development.py
```

It must:

* Import base settings.
* Set development debug behavior.
* Use SQLite.
* Use localhost development hosts.
* Use the console email backend.
* Enable appropriate development logging.
* Load values from environment variables.
* Avoid production-only security settings that would break local HTTP development.

## Production Settings

Create:

```text
config/settings/production.py
```

It must:

* Import base settings.
* Set `DEBUG` to false by default.
* Require explicit allowed hosts.
* Require a secure secret key.
* Prepare HTTPS-related security settings.
* Enable secure cookies when HTTPS is used.
* Avoid insecure default credentials.
* Fail clearly when required production values are missing.

Do not configure an actual production database or hosting service during this phase.

---

# 15. ENVIRONMENT VARIABLES

Create:

```text
.env.example
```

Do not create or commit a real `.env` containing secrets.

The example file should contain safe placeholders such as:

```env
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=replace-with-a-secure-development-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://localhost:8000
DJANGO_TIME_ZONE=Africa/Lusaka
DEFAULT_FROM_EMAIL=no-reply@example.org
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Environment parsing must handle:

* Boolean values
* Comma-separated host lists
* Comma-separated trusted origins
* Required production values
* Optional development values

Never expose environment-variable values in templates or logs.

---

# 16. SECRET KEY MANAGEMENT

The Django secret key must be loaded from an environment variable.

Do not hard-code a real production secret key.

Development may use a clearly identified unsafe fallback only when:

* It is limited to development settings.
* It is never used by production settings.
* A warning is documented.
* The fallback is not presented as secure.

Production settings must fail when the secret key is absent or insecure.

---

# 17. SQLITE CONFIGURATION

Configure SQLite in development settings.

Recommended database path:

```text
BASE_DIR / "db.sqlite3"
```

Requirements:

* Use Django ORM.
* Do not write raw SQL.
* Do not commit `db.sqlite3`.
* Add `db.sqlite3` to `.gitignore`.
* Keep models compatible with future PostgreSQL migration.
* Do not use database-specific SQL behavior.
* Do not create business-domain tables during this phase.

Apply Django’s initial built-in migrations.

---

# 18. INSTALLED APPLICATIONS

At this phase, `INSTALLED_APPS` should contain:

## Django Applications

* Django administration
* Django authentication
* Django content types
* Django sessions
* Django messages
* Django static files

## Project Applications

* `apps.core`

Do not register future applications before they exist.

Use the explicit application configuration:

```python
"apps.core.apps.CoreConfig"
```

---

# 19. CORE APPLICATION

Create the first shared Django application:

```text
apps/core/
```

Use an appropriate Django command or create it with the correct package structure.

The application must provide:

* Home-page view
* About-page view
* Core URL configuration
* Shared utility location where appropriate
* Initial tests
* Basic application configuration

Do not add complex models to `core` during this phase.

Do not turn `core` into a dumping ground for unrelated business logic.

Its purpose is to support genuinely shared project-level functionality.

---

# 20. ROOT URL CONFIGURATION

Configure:

```text
config/urls.py
```

It must include:

* Django administration
* Core application URLs
* Development media serving only when debug mode is enabled
* Custom error handlers

Recommended public URLs:

```text
/
about/
admin/
```

Use namespaced URL patterns.

Example namespace:

```text
core
```

Example URL names:

```text
core:home
core:about
```

Do not hard-code links in templates when Django URL reversing can be used.

---

# 21. INITIAL PUBLIC PAGES

Create only the following public pages:

## Home Page

The home page should:

* Display the SITADC Youth Hub name.
* Identify the SITADC Youth Organization.
* Briefly describe the future platform.
* Indicate that the system is under active development.
* Provide a link to the About page.
* Avoid false claims that incomplete features are operational.
* Use responsive Bootstrap layout.
* Use semantic HTML.
* Use the shared base template.

## About Page

The About page should include:

* Organization name
* Application purpose
* Mission
* Vision
* Core values
* Program pillars
* High-level platform objectives
* Development-status notice

Do not create mock dashboards, fake statistics, or placeholder business records.

---

# 22. BASE TEMPLATE

Create:

```text
templates/base.html
```

The base template must include:

* Valid HTML5 document structure
* Responsive viewport metadata
* Page-title block
* Meta-description block
* Bootstrap 5 CSS
* Bootstrap Icons
* Project stylesheet
* Accessible navigation
* Main-content landmark
* Django message rendering
* Footer
* JavaScript block
* Project JavaScript
* Optional page-specific CSS and JavaScript blocks

Recommended template blocks:

```django
{% block title %}{% endblock %}
{% block meta_description %}{% endblock %}
{% block extra_css %}{% endblock %}
{% block content %}{% endblock %}
{% block extra_js %}{% endblock %}
```

Use template inheritance for all pages.

Do not duplicate the entire HTML structure across templates.

---

# 23. BOOTSTRAP CONFIGURATION

Use Bootstrap 5.

For the initial development foundation, Bootstrap may be loaded from a reliable CDN.

Document that production asset strategy will be reviewed later.

Include:

* Bootstrap CSS
* Bootstrap JavaScript bundle
* Bootstrap Icons

Apply:

* Subresource integrity when available and practical
* `crossorigin` attributes where required
* Appropriate fallback documentation

Do not add jQuery unless a later requirement explicitly needs it.

Use vanilla JavaScript.

---

# 24. SHARED TEMPLATE COMPONENTS

Create reusable template components:

```text
templates/components/public_navbar.html
templates/components/messages.html
templates/components/footer.html
```

## Public Navbar

The public navbar must contain:

* SITADC Youth Hub brand
* Home link
* About link
* Accessible navigation toggle
* Visible keyboard focus
* Active-page indication where practical

Do not include links to modules that do not exist.

## Messages

The messages component must:

* Render Django messages.
* Map message levels to Bootstrap alert classes.
* Include accessible alert semantics.
* Avoid unsafe rendering.
* Support dismissible alerts where appropriate.

## Footer

The footer must include:

* SITADC Youth Organization name
* Current year rendered dynamically
* Application name
* Development-status statement where appropriate

Do not add unverified contact information.

---

# 25. STATIC FILES

Configure:

```text
STATIC_URL
STATIC_ROOT
STATICFILES_DIRS
```

Create:

```text
static/css/app.css
static/js/app.js
static/images/
```

## Initial Stylesheet

`static/css/app.css` should define a minimal project foundation for:

* Body layout
* Typography
* Navigation
* Hero section
* Cards
* Footer
* Focus states
* Responsive spacing
* Basic light-theme variables

Do not implement the complete design system in this phase.

The full design system belongs to Phase 09.

## Initial JavaScript

`static/js/app.js` should contain only shared foundational behavior, such as:

* Bootstrap component initialization if required
* Current-year support only when not rendered server-side
* Safe DOM-ready wrapper
* Minimal accessibility enhancements

Do not add application business logic.

---

# 26. MEDIA FILES

Configure:

```text
MEDIA_URL
MEDIA_ROOT
```

Create:

```text
media/.gitkeep
```

Exclude uploaded media from Git while retaining the directory structure.

Suggested `.gitignore` rule:

```text
media/*
!media/.gitkeep
```

Development media serving must only be enabled when:

```text
DEBUG=True
```

Do not implement file uploads during this phase.

Secure document storage will be implemented in the document-management phase.

---

# 27. CUSTOM ERROR PAGES

Create templates for:

```text
400 Bad Request
403 Permission Denied
404 Page Not Found
500 Internal Server Error
```

Files:

```text
templates/errors/400.html
templates/errors/403.html
templates/errors/404.html
templates/errors/500.html
```

Requirements:

* Extend the base template where safe.
* Use clear, non-technical language.
* Provide a safe path back to the home page.
* Do not expose stack traces.
* Do not display internal exception details.
* Use accessible headings.
* Maintain consistent branding.
* Avoid false support-contact details.

Configure custom handlers in the root URL module.

Test error handlers with debug mode disabled where necessary.

---

# 28. DJANGO ADMINISTRATION

Enable Django administration at:

```text
/admin/
```

Requirements:

* Use Django’s default secure authentication.
* Do not create default credentials in source code.
* Do not commit administrator passwords.
* Do not customize the full administration interface during this phase.
* Set basic site headers if appropriate.

Suggested administration branding:

```text
Site header: SITADC Youth Hub Administration
Site title: SITADC Youth Hub Admin
Index title: Organizational Administration
```

Administrative security hardening will be expanded in later phases.

---

# 29. INTERNATIONALIZATION AND TIME ZONE

Configure:

```text
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Africa/Lusaka"
USE_I18N = True
USE_TZ = True
```

Use timezone-aware datetimes.

Do not use naive datetime values in project code.

Prepare template and settings architecture for future translation support without translating the application during this phase.

---

# 30. DEFAULT PRIMARY KEYS

Use:

```text
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

Future business entities may use UUID primary keys or stable internal identifiers as approved in Phase 03.

Do not implement the reference-numbering system during this phase.

Reference-number generation belongs to Phase 07.

---

# 31. MIDDLEWARE

Use Django’s standard middleware stack.

Ensure it includes:

* Security middleware
* Session middleware
* Common middleware
* CSRF middleware
* Authentication middleware
* Messages middleware
* Clickjacking protection

Do not create custom business middleware during this phase unless it is strictly necessary for foundational request handling.

Audit middleware belongs to Phase 08.

---

# 32. TEMPLATE CONTEXT

Use Django’s standard context processors for:

* Debug
* Request
* Authentication
* Messages

Do not add broad custom context processors that perform database queries during this phase.

Future navigation and permission context must be designed carefully to avoid unnecessary queries.

---

# 33. LOGGING FOUNDATION

Create a minimal logging configuration.

It should support:

* Console logging in development
* Appropriate log levels
* Django request errors
* Application namespace logging
* Environment-controlled verbosity

Do not log:

* Passwords
* Secret keys
* Session cookies
* Authentication tokens
* Full sensitive request bodies
* Personal information

Advanced structured logging and production monitoring belong to later phases.

---

# 34. .GITIGNORE

Create a comprehensive `.gitignore` including:

```text
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/

# Virtual environments
.venv/
venv/
env/

# Django
db.sqlite3
db.sqlite3-journal
*.log
staticfiles/
media/*
!media/.gitkeep

# Environment variables
.env
.env.*
!.env.example

# IDEs and editors
.vscode/
.idea/
*.swp
*.swo

# Operating systems
.DS_Store
Thumbs.db

# Node tooling
node_modules/

# Temporary files
tmp/
temp/
*.tmp

# Build artifacts
dist/
build/
```

Review the rules to ensure that required source files are not accidentally ignored.

---

# 35. INITIAL TESTING REQUIREMENTS

Create initial tests for the project foundation.

## URL Tests

Test:

* The root URL resolves.
* The About URL resolves.
* The administrator URL is registered.
* Named URL reversing works.

## View Tests

Test:

* Home page returns HTTP 200.
* About page returns HTTP 200.
* Home page uses the correct template.
* About page uses the correct template.
* Home page contains the application name.
* About page contains the organization name.
* Public pages do not require authentication.

## Template Tests

Verify:

* Base template is used.
* Navigation is displayed.
* The page includes a main-content landmark.
* Static CSS is referenced.
* Static JavaScript is referenced.

## Error-Page Tests

Where practical, test:

* Custom 404 behavior with `DEBUG=False`
* Custom permission-denied behavior
* No sensitive debugging information is displayed

Do not add fake tests that merely assert `True`.

---

# 36. DATABASE IMPACT

Phase 01 database impact must be limited to:

* Django authentication tables
* Django administration tables
* Django content-type tables
* Django session tables
* Django migration-history tables

Do not create SITADC business-domain models during this phase.

Run:

```bash
python manage.py migrate
```

Verify that migrations complete successfully.

Do not commit:

```text
db.sqlite3
```

---

# 37. SECURITY REQUIREMENTS

Implement the following foundational security controls:

* Secret key loaded from environment variables
* Debug controlled through environment settings
* Allowed hosts controlled through environment settings
* CSRF middleware enabled
* Clickjacking protection enabled
* XSS-safe Django template rendering
* Secure password validators enabled
* No committed credentials
* No committed `.env`
* No committed database
* No public media assumptions
* No unsafe use of `mark_safe`
* No sensitive logging
* No default administrator credentials
* Production settings prepared for secure cookies
* Production settings prepared for HTTPS
* Custom errors that do not reveal internals

Do not disable Django security middleware to simplify development.

Do not use wildcard allowed hosts in production settings.

---

# 38. ACCESSIBILITY REQUIREMENTS

The foundational pages must include:

* Semantic HTML5
* Logical heading structure
* Keyboard-accessible navigation
* Visible focus indicators
* Sufficient contrast
* Descriptive links
* Main-content landmark
* Accessible navigation toggle
* Language attribute
* Responsive viewport
* Screen-reader-friendly alert messages
* Skip-to-content link
* Meaningful page titles
* Reduced-motion consideration

Do not communicate essential information through color alone.

---

# 39. RESPONSIVE-DESIGN REQUIREMENTS

The public pages must work on:

* Small mobile screens
* Large mobile screens
* Tablets
* Laptops
* Desktop screens

Use Bootstrap’s responsive grid.

Verify:

* Navigation collapses correctly.
* Text remains readable.
* Cards stack appropriately.
* No horizontal page overflow occurs.
* Buttons remain usable on touch devices.
* Focus outlines remain visible.
* Content is not hidden behind fixed elements.

Do not create the authenticated application sidebar or mobile bottom navigation during this phase.

Those elements belong to later UI and dashboard phases.

---

# 40. DOCUMENTATION REQUIREMENTS

Update the following files:

## README.md

Add or verify:

* Supported Python version
* Selected Django version
* Virtual-environment setup
* Dependency installation
* Environment configuration
* Migration commands
* Development-server command
* Initial test command
* Current project status
* Project structure

Remove any statement that the application is not yet runnable after the foundation becomes operational.

Do not claim that business modules are complete.

## PROJECT_STRUCTURE.md

Update it to distinguish:

* Files created in Phase 01
* Directories planned for later phases
* Current runnable structure
* Future modular application structure

## DEVELOPMENT_STATUS.md

At the beginning of work, update to:

```text
Current Phase: Phase 01 — Project Foundation
Status: In Progress
Last Completed Phase: Phase 00
Next Planned Phase: Phase 02 — Development Environment and Tooling
```

After full validation, update to:

```text
Current Phase: Phase 01 — Project Foundation
Status: Completed
Last Completed Phase: Phase 01
Next Planned Phase: Phase 02 — Development Environment and Tooling
```

## CHANGELOG.md

Under `Unreleased`, record:

* Django project initialization
* Environment-based settings
* SQLite setup
* Core application
* Public pages
* Base templates
* Static configuration
* Media configuration
* Error templates
* Initial tests

## ARCHITECTURE.md

Update the document to record:

* Actual Django project name
* Actual settings structure
* Actual core application
* Actual template structure
* Actual static-file structure
* Actual media configuration

Do not overwrite future architecture plans.

---

# 41. INSTALLATION COMMANDS

The agent must execute or document the appropriate commands.

A typical sequence is:

```bash
python -m venv .venv
```

Activate the environment.

Then:

```bash
python -m pip install --upgrade pip
pip install -r requirements/development.txt
django-admin startproject config .
python manage.py startapp core
```

Because applications are stored under `apps/`, ensure the `core` application is moved or created correctly as:

```text
apps/core/
```

After restructuring, verify:

* Python import paths
* `CoreConfig.name`
* `INSTALLED_APPS`
* URL imports
* Test discovery

Then run:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
```

If pytest has not yet been configured, Django’s built-in test runner may be used temporarily during this phase.

Pytest configuration belongs to Phase 02.

---

# 42. REQUIRED VALIDATION COMMANDS

Run all commands relevant to the environment:

```bash
python --version
python -m pip --version
python -m django --version
python manage.py check
python manage.py showmigrations
python manage.py migrate
python manage.py test
python manage.py runserver
```

Also inspect the repository:

```bash
git status
git diff
```

Use an appropriate file-listing command to confirm project structure.

Examples:

## Windows PowerShell

```powershell
Get-ChildItem -Recurse
```

## Windows Command Prompt

```cmd
tree /F
```

## Linux and macOS

```bash
find . -maxdepth 4 -type f | sort
```

Do not leave the development server running indefinitely after confirming that it starts.

---

# 43. DEVELOPMENT SERVER VALIDATION

Start the server:

```bash
python manage.py runserver
```

Verify:

* The server starts without configuration errors.
* The home page loads.
* The About page loads.
* Static styles load.
* JavaScript loads.
* The administration login page loads.
* Unknown URLs use the expected error behavior.
* No critical console errors appear.
* No stack traces are visible to normal users.

Stop the server after validation.

Do not claim successful validation unless the server was actually started or clearly state that it could not be started.

---

# 44. PROHIBITED WORK DURING PHASE 01

Do not implement:

* Custom user model
* Invitation registration
* User profiles
* Roles
* Permission scopes
* Organizational structure
* Reference numbering
* Audit logging
* Dashboard analytics
* Leadership management
* Membership management
* Volunteer management
* Stakeholder management
* Program management
* Project management
* Beneficiary management
* MEAL
* Dynamic report builder
* Report workflows
* Document uploads
* Registers
* Meetings
* Notifications
* Search
* Exports
* Finance
* Governance workflows
* Safeguarding cases
* Production deployment
* APIs
* Background tasks

These functions belong to later phases.

Do not create placeholder database models for future modules.

Do not create fake dashboard statistics.

Do not generate empty Django applications for all future modules.

---

# 45. IMPLEMENTATION GUIDELINES

The AI agent must:

1. Read the governance files.
2. Inspect the repository.
3. Confirm Phase 00 completion.
4. Update `DEVELOPMENT_STATUS.md`.
5. Create the virtual environment.
6. Create dependency files.
7. Install Django.
8. Create the Django project.
9. Refactor settings.
10. Create the `apps` package.
11. Create the `core` application.
12. Configure URLs.
13. Configure templates.
14. Configure static files.
15. Configure media files.
16. Create public pages.
17. Create error pages.
18. Create tests.
19. Apply migrations.
20. Run validation.
21. Update documentation.
22. Produce the delivery report.

Implement one verified step at a time.

After major changes, run:

```bash
python manage.py check
```

Do not accumulate many untested changes before validation.

---

# 46. ERROR-HANDLING REQUIREMENTS

If an implementation command fails:

1. Read the full error.
2. Identify the root cause.
3. Correct the configuration or code.
4. Re-run the failed command.
5. Record the failure and correction in the delivery report.

Do not:

* Suppress errors without investigation.
* Delete failing tests.
* Disable middleware.
* Remove security checks.
* Change the technology stack.
* Mark the phase complete with unresolved critical errors.

---

# 47. ACCEPTANCE CRITERIA

Phase 01 is accepted only when:

* Phase 00 governance files have been reviewed.
* The virtual environment has been created.
* Dependency files exist.
* Dependencies are version-pinned.
* Django is installed.
* The Django project exists.
* Split settings work.
* Development settings load correctly.
* Production settings exist and fail safely when required values are missing.
* SQLite is configured.
* Initial migrations have been applied.
* The `core` application exists.
* Root URLs work.
* Home page works.
* About page works.
* Base template works.
* Bootstrap loads.
* Project CSS loads.
* Project JavaScript loads.
* Static files are configured.
* Media files are configured.
* Error templates exist.
* Admin login page works.
* Environment secrets are not committed.
* `.gitignore` is complete.
* Initial tests exist.
* Tests pass.
* Django system checks pass.
* The development server starts.
* Documentation is updated.
* `DEVELOPMENT_STATUS.md` is updated.
* No later-phase business modules have been implemented.
* No prohibited framework has been introduced.

---

# 48. DEFINITION OF DONE

Phase 01 is complete only when:

* The project is runnable.
* The project structure matches the approved architecture.
* All foundational configuration is environment-aware.
* No secrets are committed.
* SQLite works.
* Initial migrations work.
* Public pages render correctly.
* Templates use inheritance.
* Static assets load.
* Media configuration exists.
* Error templates exist.
* Initial tests pass.
* Django checks pass.
* Documentation matches the implementation.
* The delivery report is complete.
* Phase 02 is marked ready.

The phase is not complete when:

* Settings remain in one unmanaged file.
* The secret key is hard-coded for production.
* `DEBUG` is permanently enabled.
* Allowed hosts use an insecure production wildcard.
* The database file is committed.
* Tests are absent.
* The server has not been validated.
* Documentation makes false claims.
* Future modules have been prematurely generated.
* Critical warnings remain unresolved.

---

# 49. REQUIRED AI AGENT COMMAND PROMPT

Use the following prompt to command the implementation agent.

## AI Agent Implementation Prompt

You are a senior Python and Django software architect working on the SITADC Youth Hub web application.

The project has completed Phase 00 — Project Governance and Development Control.

Your active task is:

# Phase 01 — Project Foundation

Begin by reading:

1. `AGENTS.md`
2. `README.md`
3. `ARCHITECTURE.md`
4. `DEVELOPMENT_STATUS.md`
5. `DEFINITION_OF_DONE.md`
6. `NAMING_CONVENTIONS.md`
7. `PROJECT_STRUCTURE.md`
8. `roadmaps/00-Master-Development-Roadmap.md`
9. `roadmaps/01-Project-Foundation.md`

Inspect the full repository before making changes.

Confirm that Phase 00 is complete.

Update `DEVELOPMENT_STATUS.md` to mark Phase 01 as in progress.

Create the first runnable Django foundation using:

* Python
* Django
* SQLite
* HTML5
* CSS3
* Bootstrap 5
* Vanilla JavaScript
* Django Templates

Create:

* Python virtual environment
* Version-pinned requirements files
* Initial `pyproject.toml`
* Django project named `config`
* Split settings
* Environment-variable configuration
* SQLite development database
* `apps` package
* Shared `core` application
* Root URL routing
* Home page
* About page
* Base template
* Shared template components
* Static-file structure
* Media-file structure
* Custom error pages
* Initial tests
* Secure `.gitignore`
* `.env.example`

Use:

```text
config.settings.development
```

as the default development settings module.

Do not implement future business modules.

Do not generate all planned Django applications.

Do not create a custom user model during this phase.

Do not add Supabase, Firebase, React, Vue, Angular, Node.js backend, PostgreSQL, Redis, Celery, Docker, APIs, or external services.

Apply Django’s initial migrations.

Run all available tests and checks.

Start the development server and verify that:

* `/` loads
* `/about/` loads
* `/admin/` loads
* Static files load
* Unknown routes are handled safely

Update:

* `README.md`
* `CHANGELOG.md`
* `ARCHITECTURE.md`
* `PROJECT_STRUCTURE.md`
* `DEVELOPMENT_STATUS.md`

Do not mark Phase 01 complete until every acceptance criterion in `roadmaps/01-Project-Foundation.md` has been validated.

Provide the required delivery report.

---

# 50. REQUIRED DELIVERY REPORT

After completing the phase, provide:

## Phase Summary

Explain what foundation was implemented.

## Active Phase

```text
Phase 01 — Project Foundation
```

## Files Created

List every created file.

## Files Modified

List every modified file.

## Directories Created

List every created directory.

## Environment

Report:

* Operating system
* Python version
* Django version
* Virtual-environment location
* Settings module

## Dependencies

List installed and pinned dependencies.

## Django Configuration

Summarize:

* Settings structure
* Database
* Static files
* Media files
* Templates
* URLs
* Installed applications
* Middleware
* Time zone

## Database Changes

List:

* Migrations applied
* Tables created by Django
* Confirmation that no business-domain models were added

## Pages Created

List:

* Home
* About
* Error pages
* Administration access

## Security Controls

Explain:

* Environment-secret handling
* Debug handling
* Allowed-host handling
* CSRF protection
* Session protection
* `.gitignore`
* Production-setting safeguards

## Accessibility

Explain:

* Semantic structure
* Skip link
* Keyboard navigation
* Focus states
* Accessible messages
* Responsive design

## Tests Added

List all tests and their purposes.

## Commands Run

List all commands executed.

## Validation Results

Report the result of:

* Django system checks
* Migrations
* Tests
* Development-server startup
* Page validation
* Static-file validation

## Problems Found

List errors, warnings, or conflicts encountered.

## Problems Resolved

Explain how they were corrected.

## Known Limitations

List incomplete items honestly.

## Documentation Updated

List all updated documentation files.

## Phase Status

Use one of:

```text
Phase 01: Completed
Phase 02: Ready
```

or:

```text
Phase 01: Incomplete
```

Provide the exact reason if incomplete.

## Next Recommended Action

```text
Proceed to Phase 02 — Development Environment and Tooling.
```

---

# 51. PHASE COMPLETION CHECKLIST

Before completing Phase 01, verify every item.

## Governance

* [ ] `AGENTS.md` was read.
* [ ] `README.md` was read.
* [ ] Active roadmap was read.
* [ ] Phase 00 completion was confirmed.
* [ ] Development status was updated.

## Environment

* [ ] Python version was confirmed.
* [ ] Virtual environment was created.
* [ ] pip was upgraded.
* [ ] Django was installed.
* [ ] Dependency versions were pinned.

## Project

* [ ] `manage.py` exists.
* [ ] `config/` exists.
* [ ] Split settings exist.
* [ ] ASGI configuration works.
* [ ] WSGI configuration works.
* [ ] Root URL configuration works.

## Application

* [ ] `apps/` is a Python package.
* [ ] `apps/core/` exists.
* [ ] Core application is registered.
* [ ] Core URLs are namespaced.
* [ ] Core views work.

## Templates

* [ ] Base template exists.
* [ ] Home template exists.
* [ ] About template exists.
* [ ] Shared components exist.
* [ ] Error templates exist.
* [ ] Template inheritance works.

## Static and Media

* [ ] Static configuration works.
* [ ] CSS loads.
* [ ] JavaScript loads.
* [ ] Media configuration exists.
* [ ] Uploaded media is ignored by Git.
* [ ] `.gitkeep` preserves the media directory.

## Database

* [ ] SQLite is configured.
* [ ] Initial migrations were applied.
* [ ] Database file is ignored.
* [ ] No business-domain models were created.

## Security

* [ ] Secret key is environment-controlled.
* [ ] Debug is environment-controlled.
* [ ] Allowed hosts are environment-controlled.
* [ ] `.env` is ignored.
* [ ] `.env.example` exists.
* [ ] CSRF middleware is enabled.
* [ ] Clickjacking protection is enabled.
* [ ] No credentials are committed.

## Testing

* [ ] URL tests exist.
* [ ] View tests exist.
* [ ] Template tests exist.
* [ ] Error-page tests exist where practical.
* [ ] All tests pass.
* [ ] Django checks pass.

## Documentation

* [ ] README was updated.
* [ ] Changelog was updated.
* [ ] Architecture document was updated.
* [ ] Project structure was updated.
* [ ] Development status was updated.

## Final Validation

* [ ] Development server starts.
* [ ] Home page loads.
* [ ] About page loads.
* [ ] Admin page loads.
* [ ] Static assets load.
* [ ] No critical error remains.
* [ ] No prohibited technology was introduced.
* [ ] No later-phase module was implemented.
* [ ] Delivery report was produced.

---

# 52. NEXT PHASE

After Phase 01 has been completed and validated, proceed to:

# Phase 02 — Development Environment and Tooling

Phase 02 will configure:

* Ruff
* Black
* isort
* mypy
* pytest
* pytest-django
* coverage
* Bandit
* djLint
* ESLint
* Prettier
* Stylelint
* pre-commit
* Common development commands
* Continuous integration
* Reproducible development setup

Do not begin Phase 02 until Phase 01 has passed all acceptance criteria.
