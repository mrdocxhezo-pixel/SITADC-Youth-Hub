# PHASE 02 — DEVELOPMENT ENVIRONMENT AND TOOLING

## SITADC Youth Hub Web Application

**Roadmap File:** `roadmaps/02-Development-Environment-and-Tooling.md`
**Phase Number:** 02
**Phase Name:** Development Environment and Tooling
**Current Status:** Ready
**Previous Phase:** Phase 01 — Project Foundation
**Next Phase:** Phase 03 — Core System Architecture

---

# 1. PHASE PURPOSE

The purpose of Phase 02 is to establish a consistent, reproducible, automated, and secure development environment for the SITADC Youth Hub web application.

This phase must configure the tools required to:

* Format Python code
* Format Django templates
* Format CSS
* Format JavaScript
* Sort Python imports
* Lint Python code
* Lint JavaScript
* Lint CSS
* Check Python types
* Run Django tests
* Run pytest tests
* Measure test coverage
* Scan Python code for security issues
* Validate Django templates
* Run automated pre-commit checks
* Provide consistent development commands
* Validate pull requests through continuous integration
* Prepare optional containerized development services
* Document setup for Windows, Linux, and macOS

The purpose is not merely to install tools.

Each tool must be properly configured, documented, integrated, tested, and usable by both human developers and AI coding agents.

At the end of this phase, a developer must be able to clone the project, install dependencies, run one documented setup process, and execute all major quality checks consistently.

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

# 3. REQUIRED APPLICATION TECHNOLOGY STACK

The application must continue using:

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

SQLite remains the required initial database.

Development tooling must not replace or restructure the approved application stack.

---

# 4. REQUIRED DEVELOPMENT TOOLS

Configure the following tools during this phase.

## Python Quality Tools

* Ruff
* Black
* isort
* mypy
* pytest
* pytest-django
* coverage
* Bandit
* pre-commit

## Django and Template Tools

* djLint
* Django system checks
* Django deployment checks where practical

## Frontend Quality Tools

* ESLint
* Prettier
* Stylelint

## Supporting Development Tools

* npm for frontend quality-tool dependencies
* Git hooks through pre-commit
* GitHub Actions or another approved continuous-integration workflow
* Common development commands
* Environment validation scripts

## Optional Infrastructure Tools

The phase may prepare:

* Docker
* Docker Compose
* Redis

However, these must only be added when they support a clearly documented future requirement and do not replace the primary local development process.

The core Django application must remain runnable without Docker during early development.

Redis must not be treated as an active application dependency unless a later phase explicitly introduces functionality that requires it.

---

# 5. PROHIBITED TECHNOLOGY CHANGES

Do not replace the required application stack with:

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

Do not introduce during this phase:

* Django REST Framework
* GraphQL
* PostgreSQL as the active project database
* MySQL
* Celery as an active application dependency
* Kubernetes
* Microservices
* Cloud object storage
* External authentication providers
* Third-party application platforms

Node.js may only be used to run frontend development-quality tools such as:

* ESLint
* Prettier
* Stylelint

It must not become the application backend.

---

# 6. PHASE ENTRY CRITERIA

Before beginning Phase 02, verify that Phase 01 has been completed.

The repository must contain a working Django project with at least:

```text
manage.py
config/
config/settings/
apps/
apps/core/
templates/
static/
media/
requirements/
pyproject.toml
.env.example
.gitignore
```

The following commands must work before Phase 02 begins:

```bash
python manage.py check
python manage.py migrate
python manage.py test
```

The following pages should be available:

```text
/
about/
/admin/
```

Before writing or changing configuration, read:

1. `AGENTS.md`
2. `README.md`
3. `ARCHITECTURE.md`
4. `DEVELOPMENT_STATUS.md`
5. `DEFINITION_OF_DONE.md`
6. `NAMING_CONVENTIONS.md`
7. `PROJECT_STRUCTURE.md`
8. `CONTRIBUTING.md`
9. `SECURITY.md`
10. `roadmaps/00-Master-Development-Roadmap.md`
11. `roadmaps/01-Project-Foundation.md`
12. `roadmaps/02-Development-Environment-and-Tooling.md`

If the Django foundation is not functional, do not conceal the problem.

Resolve Phase 01 blockers before marking Phase 02 as complete.

---

# 7. PHASE OBJECTIVES

Complete the following objectives:

1. Verify the current Python and Django environment.
2. Audit existing dependency files.
3. Configure Ruff.
4. Configure Black.
5. Configure isort.
6. Configure mypy.
7. Configure pytest.
8. Configure pytest-django.
9. Configure test coverage.
10. Configure Bandit.
11. Configure djLint.
12. Configure ESLint.
13. Configure Prettier.
14. Configure Stylelint.
15. Configure pre-commit.
16. Create common development commands.
17. Create environment-validation scripts.
18. Create frontend asset and quality-control scripts.
19. Create a continuous-integration workflow.
20. Prepare optional Docker development configuration where approved.
21. Prepare optional Redis service configuration without making it an active dependency.
22. Document Windows development setup.
23. Document Linux development setup.
24. Document macOS development setup.
25. Validate formatting commands.
26. Validate linting commands.
27. Validate test commands.
28. Validate type-checking commands.
29. Validate security-check commands.
30. Validate pre-commit hooks.
31. Validate the CI workflow syntax and expected behavior.
32. Update project documentation.
33. Update the project development status.

---

# 8. REQUIRED FILES TO CREATE OR UPDATE

Create or update the following files as required:

```text
pyproject.toml
requirements/base.txt
requirements/development.txt
requirements/production.txt
package.json
package-lock.json
.pre-commit-config.yaml
.coveragerc
.editorconfig
.gitignore
README.md
CONTRIBUTING.md
ARCHITECTURE.md
DEVELOPMENT_STATUS.md
CHANGELOG.md
```

Create or update the following frontend configuration files:

```text
eslint.config.js
.prettierrc.json
.prettierignore
.stylelintrc.json
.stylelintignore
```

Create the following documentation files:

```text
docs/development/DEVELOPMENT_ENVIRONMENT.md
docs/development/WINDOWS_SETUP.md
docs/development/LINUX_SETUP.md
docs/development/MACOS_SETUP.md
docs/development/COMMON_COMMANDS.md
docs/testing/TESTING_GUIDE.md
docs/security/SECURITY_CHECKS.md
```

Create the following scripts where appropriate:

```text
scripts/setup.py
scripts/check_environment.py
scripts/quality.py
scripts/test.py
scripts/security.py
```

Shell-specific wrappers may also be created:

```text
scripts/setup.ps1
scripts/setup.sh
scripts/quality.ps1
scripts/quality.sh
scripts/test.ps1
scripts/test.sh
```

Create the continuous-integration workflow:

```text
.github/workflows/ci.yml
```

Optional files, only where approved and documented:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

Do not create duplicate configuration files that compete with one another.

Prefer centralized Python-tool configuration in:

```text
pyproject.toml
```

where the selected tool supports it reliably.

---

# 9. DEPENDENCY MANAGEMENT

Maintain three requirements files:

```text
requirements/base.txt
requirements/development.txt
requirements/production.txt
```

## Base Dependencies

`requirements/base.txt` must contain runtime dependencies only.

Examples include:

* Django
* Environment-variable loader

Do not add linting, test, formatting, or security tools to the base requirements.

## Development Dependencies

`requirements/development.txt` must include:

```text
-r base.txt
```

It must also contain pinned versions of:

* Ruff
* Black
* isort
* mypy
* pytest
* pytest-django
* coverage
* Bandit
* djLint
* pre-commit
* Django typing support where required
* Testing utilities where justified

Possible supporting packages may include:

* `django-stubs`
* `types-*` stub packages
* `factory-boy`
* `Faker`

Do not add supporting packages without an immediate and documented use.

## Production Dependencies

`requirements/production.txt` must include:

```text
-r base.txt
```

Do not add development-only quality tools to production requirements.

## Dependency Rules

All dependencies must:

* Be version-pinned
* Be compatible with the approved Python version
* Be compatible with the approved Django version
* Be actively maintained
* Have a documented purpose
* Avoid unnecessary duplication
* Be reviewed for known security concerns

Do not upgrade existing major versions silently.

Document every added dependency in the delivery report.

---

# 10. PYPROJECT.TOML STRUCTURE

Use `pyproject.toml` as the main configuration location for compatible Python tools.

It should contain configuration sections for:

* Project metadata
* Black
* Ruff
* isort
* mypy
* pytest
* coverage where supported
* djLint where supported

Avoid repeating the same configuration in multiple files unless a tool requires its own dedicated file.

The project metadata must remain consistent with:

* The approved Python version
* Project name
* Project description
* Current pre-release development status

---

# 11. RUFF CONFIGURATION

Configure Ruff as the main Python linter.

Ruff must check:

* Standard Python errors
* Pyflakes issues
* pycodestyle issues
* Import issues
* Common bug patterns
* Simplification opportunities
* Django-specific issues where supported
* Security-related patterns where appropriate
* Unused variables
* Unused imports
* Ambiguous variable names
* Incorrect exception handling

Recommended rule groups may include:

* `E`
* `F`
* `W`
* `I`
* `B`
* `UP`
* `SIM`
* `DJ`
* `C4`
* `PIE`
* `RUF`

Enable rules deliberately.

Do not enable large rule collections without reviewing their effect.

Configure:

* Target Python version
* Maximum line length
* Source directories
* Excluded directories
* Per-file ignores
* Migration-file exceptions
* Test-file exceptions
* Auto-fix rules

Recommended excluded directories include:

```text
.venv
venv
env
node_modules
staticfiles
media
htmlcov
dist
build
migrations
```

Migration files may be excluded from selected style rules, but must not be ignored by security review without reason.

Required commands:

```bash
ruff check .
ruff check . --fix
ruff format --check .
```

If Black remains the official formatter, use Ruff for linting rather than creating conflicting formatting behavior.

---

# 12. BLACK CONFIGURATION

Configure Black as the official Python code formatter.

Recommended configuration:

```text
Line length: 88 or another documented project standard
Target version: Approved Python version
Exclude: Generated files, virtual environments, migrations where appropriate
```

Required commands:

```bash
black --check .
black .
```

Black and Ruff settings must not conflict.

Do not manually enforce formatting standards that Black will automatically control.

---

# 13. ISORT CONFIGURATION

Configure isort for Python import ordering.

Use a Black-compatible profile.

Recommended configuration:

```text
profile = "black"
known_first_party = ["apps", "config"]
```

Organize imports into:

1. Standard library
2. Third-party packages
3. Django packages where applicable
4. First-party project imports
5. Local imports

Required commands:

```bash
isort --check-only .
isort .
```

Ruff may also detect import issues, but isort remains the explicit import-formatting tool required by the roadmap.

Ensure the two tools agree on import ordering.

---

# 14. MYPY CONFIGURATION

Configure mypy for gradual static typing.

The configuration must support Django code.

Use appropriate Django typing integrations where required, such as:

* `django-stubs`
* `django-stubs-ext`

Configure:

* Python version
* Django settings module
* Source paths
* Plugin configuration
* Excluded generated files
* Missing import behavior
* Incremental strictness
* Test-file exceptions where justified

Recommended settings may include:

```text
check_untyped_defs = true
disallow_untyped_defs = false initially
warn_unused_ignores = true
warn_redundant_casts = true
warn_unused_configs = true
no_implicit_optional = true
```

Do not configure strict mode globally if the existing foundation cannot satisfy it.

Adopt a staged typing approach:

## Initial Stage

* Type-check core configuration and shared services.
* Detect obvious errors.
* Require annotations for new service-layer code where practical.

## Later Stage

* Increase strictness by module.
* Remove temporary ignores.
* Require stronger typing for critical business logic.

Required command:

```bash
mypy .
```

All `# type: ignore` comments must:

* Be narrowly scoped
* Include an error code where supported
* Have a clear technical reason
* Not conceal genuine defects

---

# 15. PYTEST CONFIGURATION

Configure pytest as the main automated test runner.

Configure it in `pyproject.toml` or another single approved configuration file.

Include:

* Django settings module
* Test file patterns
* Python file patterns
* Python class patterns
* Python function patterns
* Warning behavior
* Output verbosity
* Test paths
* Database reuse guidance
* Strict marker handling

Recommended test paths:

```text
apps/
tests/
```

Recommended file patterns:

```text
test_*.py
*_test.py
```

Required command:

```bash
pytest
```

Useful optional commands:

```bash
pytest -v
pytest -x
pytest --failed-first
pytest --reuse-db
pytest apps/core/tests/
```

Do not remove Django’s existing tests merely because pytest is introduced.

Ensure existing tests are discovered and run successfully.

---

# 16. PYTEST-DJANGO CONFIGURATION

Configure pytest-django to use:

```text
config.settings.development
```

or an approved dedicated test settings module where justified.

A dedicated test settings file may be created:

```text
config/settings/test.py
```

only if it provides clear benefits such as:

* Faster password hashing
* Isolated email backend
* Temporary media storage
* Predictable cache behavior
* Test-specific logging
* Stable test configuration

If created, it must inherit from the approved base settings.

Do not weaken production or development security settings globally just to simplify tests.

Use pytest markers correctly:

```python
@pytest.mark.django_db
```

Only tests that require database access should request database access.

---

# 17. TEST COVERAGE CONFIGURATION

Configure coverage measurement.

Create:

```text
.coveragerc
```

or use the relevant `pyproject.toml` sections.

Coverage must measure project source code while excluding:

* Virtual environments
* Migrations where approved
* Generated files
* Test files where appropriate
* WSGI and ASGI boilerplate where justified
* Development-only entry points where justified

Required commands:

```bash
coverage run -m pytest
coverage report
coverage html
```

Alternative command where supported:

```bash
pytest --cov=apps --cov=config --cov-report=term-missing
```

Do not enforce an unrealistic global threshold immediately.

Recommended staged thresholds:

* Phase 02 foundation: no regression below the current measured baseline
* Core shared services: at least 80%
* Security-critical business logic: at least 90%
* Workflow and permission services: strong branch coverage
* Overall mature project target: at least 80%

The CI workflow should fail when the agreed threshold is not met.

Document the initial threshold and the plan for increasing it.

Coverage percentage alone does not prove test quality.

Tests must validate meaningful behavior.

---

# 18. BANDIT CONFIGURATION

Configure Bandit for Python security scanning.

Bandit must review project Python code for patterns such as:

* Hard-coded passwords
* Unsafe process execution
* Unsafe deserialization
* Weak cryptography
* Insecure temporary files
* SQL injection risks
* Unsafe YAML loading
* Debugging code
* Unsafe shell usage
* Insecure random generation

Required command:

```bash
bandit -r apps config
```

Configure exclusions for:

* Tests where justified
* Migrations where justified
* Virtual environments
* Generated files

Do not exclude the entire project to make the scan pass.

Every skipped Bandit issue must include:

* A documented reason
* Narrow scope
* Evidence that the behavior is safe
* Review during security hardening

---

# 19. DJLINT CONFIGURATION

Configure djLint for Django templates.

djLint must check:

* HTML structure
* Template formatting
* Django template syntax
* Indentation
* Accessibility-related markup patterns where supported
* Excessively long lines
* Invalid tags
* Inconsistent formatting

Required commands:

```bash
djlint templates --check
djlint templates --reformat
```

Configure:

* Django template profile
* Indentation
* Line length
* Excluded generated or vendor templates
* Formatting rules

Do not automatically reformat templates without reviewing the resulting Django template syntax.

Ensure Bootstrap markup and Django template tags remain valid.

---

# 20. ESLINT CONFIGURATION

Configure ESLint for vanilla JavaScript.

Do not configure React, Vue, Angular, TypeScript, or Node backend rules unless a later approved requirement introduces them.

ESLint must check:

* Syntax errors
* Undefined variables
* Unused variables
* Unsafe equality
* Unreachable code
* Accidental globals
* Inconsistent declarations
* Browser compatibility assumptions
* Modern JavaScript best practices
* Safe DOM manipulation practices

Configure the environment for:

* Browser JavaScript
* Modern ECMAScript
* Project static JavaScript files

Recommended command:

```bash
npm run lint:js
```

Equivalent direct command:

```bash
eslint "static/js/**/*.js"
```

Do not lint third-party vendor files.

Exclude:

```text
static/vendor/
staticfiles/
node_modules/
```

---

# 21. PRETTIER CONFIGURATION

Configure Prettier for:

* JavaScript
* JSON
* CSS
* Markdown where approved
* YAML where approved

Avoid applying Prettier directly to Django templates unless the configuration is verified not to corrupt Django template syntax.

Use djLint as the primary formatter for Django templates.

Create:

```text
.prettierrc.json
.prettierignore
```

Recommended commands:

```bash
npm run format:check
npm run format
```

Do not apply broad formatting to generated files, vendor files, media, or migrations.

---

# 22. STYLELINT CONFIGURATION

Configure Stylelint for project CSS.

Stylelint must check:

* Invalid CSS
* Duplicate declarations
* Invalid selectors
* Unknown properties
* Empty blocks
* Naming consistency where appropriate
* Modern CSS practices
* Avoidable specificity problems
* Bootstrap-compatible customization

Recommended commands:

```bash
npm run lint:css
```

Equivalent direct command:

```bash
stylelint "static/css/**/*.css"
```

Do not lint:

* Bootstrap vendor files
* Minified CSS
* Generated static files
* Third-party stylesheets

Create:

```text
.stylelintrc.json
.stylelintignore
```

---

# 23. PACKAGE.JSON

Create a minimal `package.json` for frontend quality tools only.

It must include:

* Project name
* Private package flag
* Description
* Development scripts
* Development dependencies
* Supported Node version where appropriate

Set:

```json
"private": true
```

Recommended scripts:

```text
lint
lint:js
lint:css
format
format:check
check
```

Example command purposes:

```text
npm run lint
npm run lint:js
npm run lint:css
npm run format
npm run format:check
npm run check
```

Do not place application runtime dependencies in `package.json`.

Do not turn the project into a Node application.

Commit:

```text
package-lock.json
```

after installing dependencies.

Do not commit:

```text
node_modules/
```

---

# 24. PRE-COMMIT CONFIGURATION

Create:

```text
.pre-commit-config.yaml
```

Configure hooks for:

* Trailing whitespace
* End-of-file fixes
* YAML validation
* JSON validation
* TOML validation
* Merge-conflict detection
* Large-file detection
* Private-key detection
* Black
* Ruff
* isort
* djLint
* Bandit where practical
* Prettier where practical
* Stylelint where practical

Install hooks using:

```bash
pre-commit install
```

Validate all files using:

```bash
pre-commit run --all-files
```

Do not configure hooks that:

* Rewrite large parts of the repository unexpectedly
* Run excessively slowly on every commit
* Require unavailable external services
* Modify database or media files
* Leak environment variables
* Skip critical source files without reason

Use local hooks where necessary for project-specific commands.

Document any hook that requires Node.js.

---

# 25. EDITORCONFIG

Create:

```text
.editorconfig
```

Configure consistent editor behavior for:

* UTF-8 encoding
* Final newline
* Trailing whitespace
* Indentation
* Python files
* HTML and Django templates
* CSS
* JavaScript
* JSON
* YAML
* Markdown
* Shell scripts
* PowerShell scripts

Recommended defaults:

```text
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 4
```

Use two-space indentation for formats where it is more appropriate, such as:

* JSON
* YAML
* CSS
* JavaScript

Markdown may preserve intentional trailing spaces where necessary.

---

# 26. COMMON DEVELOPMENT COMMANDS

Create a consistent command interface for developers.

Because the project must support Windows, Linux, and macOS, do not rely exclusively on GNU Make.

Preferred approach:

Create cross-platform Python command scripts under:

```text
scripts/
```

Examples:

```bash
python scripts/setup.py
python scripts/check_environment.py
python scripts/quality.py
python scripts/test.py
python scripts/security.py
```

The commands should perform clear, limited tasks.

## Setup Command

Should:

* Confirm Python version
* Confirm virtual environment
* Install Python dependencies
* Install Node dependencies where available
* Validate `.env`
* Run migrations
* Run Django checks
* Provide clear next instructions

## Quality Command

Should run:

* Black check
* isort check
* Ruff
* mypy
* djLint
* ESLint
* Stylelint
* Prettier check

## Test Command

Should run:

* pytest
* Coverage
* Django system checks

## Security Command

Should run:

* Bandit
* Django deployment checks where safe
* Dependency-audit preparation where approved
* Secret-file checks where available

Each script must:

* Exit with a non-zero status on failure
* Print the command being run
* Stop on critical failure
* Avoid shell injection
* Work from the repository root
* Avoid logging secrets
* Provide readable error messages

Optional wrapper scripts may call the Python scripts.

---

# 27. FRONTEND BUILD AND ASSET SCRIPTS

The application does not require a JavaScript bundler in this phase.

Do not add:

* Webpack
* Vite
* Parcel
* Rollup

unless a later approved requirement justifies one.

Create npm scripts for:

* JavaScript linting
* CSS linting
* Frontend formatting
* Frontend format validation

Static frontend files should remain directly manageable through Django’s static-file system.

Bootstrap may remain CDN-based during early development if approved in Phase 01.

The future production asset strategy will be reviewed later.

---

# 28. CONTINUOUS INTEGRATION

Create:

```text
.github/workflows/ci.yml
```

The workflow must validate pushes and pull requests to protected development branches.

Recommended triggers:

* Pull requests
* Pushes to `main`
* Pushes to the primary development branch if one exists
* Manual workflow dispatch

The CI workflow should include:

1. Repository checkout
2. Supported Python setup
3. Python dependency caching
4. Development dependency installation
5. Supported Node setup
6. Node dependency caching
7. Frontend dependency installation
8. Environment configuration using safe test values
9. Django system checks
10. Migration consistency checks
11. Ruff
12. Black check
13. isort check
14. mypy
15. Bandit
16. djLint
17. ESLint
18. Stylelint
19. Prettier check
20. pytest
21. Coverage report
22. Test artifact upload where appropriate

Use safe temporary environment variables.

Do not place real secrets in the workflow file.

Use GitHub repository secrets only when a future workflow genuinely requires them.

---

# 29. CI MIGRATION VALIDATION

The CI workflow must verify that model changes are accompanied by migrations.

Use:

```bash
python manage.py makemigrations --check --dry-run
```

Then run:

```bash
python manage.py migrate --noinput
```

Phase 02 currently has no expected business-model changes, but the check must be configured for all future pull requests.

The workflow must fail when unapplied model changes are detected.

---

# 30. CI TEST DATABASE

Use SQLite for CI during the current phase.

Do not introduce PostgreSQL into CI until the project formally adopts it.

The CI database must be temporary and recreated for each workflow run.

Do not upload or commit the CI database.

---

# 31. CI SECURITY

The continuous-integration workflow must:

* Use pinned or trusted action versions
* Use minimal permissions
* Avoid exposing secrets
* Avoid executing untrusted arbitrary scripts with elevated permissions
* Avoid uploading environment files
* Avoid uploading databases or media
* Fail on critical linting, security, and test failures
* Use dependency caching safely
* Avoid writing sensitive output to logs

Configure workflow permissions explicitly where practical.

Example principle:

```yaml
permissions:
  contents: read
```

Do not give write permissions unless a specific approved job requires them.

---

# 32. OPTIONAL DOCKER CONFIGURATION

Docker configuration may be introduced during this phase only if:

* It improves development reproducibility.
* It does not replace local virtual-environment setup.
* It is documented.
* It is tested.
* It remains consistent with SQLite development.
* It does not create unnecessary complexity.

Possible files:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

A development container may include:

* Python
* Django dependencies
* Node quality-tool dependencies

Do not add unrelated services.

Do not claim Docker support works unless the image is built and the application is tested inside it.

If Docker cannot be validated in the current environment, document it as prepared but unverified.

---

# 33. OPTIONAL REDIS CONFIGURATION

Redis is not an active application requirement in Phase 02.

A Redis service may be documented or optionally included in Docker Compose only when:

* It is clearly marked as reserved for future use.
* The Django application does not depend on it.
* The application still starts when Redis is unavailable.
* No Redis package is added to runtime requirements without use.
* No fake integration is claimed.

Do not implement:

* Redis sessions
* Redis caching
* Celery queues
* Realtime notifications
* Background processing

These require explicit later-phase approval.

---

# 34. WINDOWS DEVELOPMENT SETUP

Create:

```text
docs/development/WINDOWS_SETUP.md
```

Document:

* Installing supported Python
* Verifying Python
* Installing Git
* Cloning the repository
* Creating `.venv`
* Activating `.venv` in PowerShell
* PowerShell execution-policy guidance
* Activating in Command Prompt
* Upgrading pip
* Installing Python dependencies
* Installing Node.js where frontend tools are used
* Installing Node dependencies
* Creating `.env`
* Running migrations
* Running Django checks
* Running the server
* Running tests
* Running linting
* Running pre-commit
* Common path problems
* Common SQLite problems
* Line-ending considerations
* Deactivating the environment

Use Windows-compatible commands.

Do not provide Linux-only instructions as the primary method.

---

# 35. LINUX DEVELOPMENT SETUP

Create:

```text
docs/development/LINUX_SETUP.md
```

Document:

* Required system packages
* Supported Python installation
* Git installation
* Cloning the repository
* Creating `.venv`
* Activating `.venv`
* Upgrading pip
* Installing dependencies
* Installing Node.js where needed
* Installing Node dependencies
* Creating `.env`
* Running migrations
* Running checks
* Running the server
* Running tests
* Running quality tools
* Running pre-commit
* File-permission guidance
* Common package-build issues
* Deactivating the environment

Do not assume a single Linux distribution.

Where commands vary, provide separate examples for major package managers.

---

# 36. MACOS DEVELOPMENT SETUP

Create:

```text
docs/development/MACOS_SETUP.md
```

Document:

* Installing supported Python
* Homebrew-based option
* Git setup
* Cloning the repository
* Creating `.venv`
* Activating `.venv`
* Upgrading pip
* Installing dependencies
* Installing Node.js where needed
* Installing Node dependencies
* Creating `.env`
* Running migrations
* Running checks
* Running the server
* Running tests
* Running quality tools
* Running pre-commit
* Apple Silicon considerations
* Common PATH problems
* Deactivating the environment

Do not assume Homebrew is already installed.

---

# 37. DEVELOPMENT ENVIRONMENT GUIDE

Create:

```text
docs/development/DEVELOPMENT_ENVIRONMENT.md
```

Include:

* Supported operating systems
* Supported Python version
* Supported Django version
* Supported Node version
* Required tools
* Optional tools
* Repository setup
* Environment variables
* Dependency installation
* Database initialization
* Quality-control workflow
* Test workflow
* Security-check workflow
* Pre-commit workflow
* CI overview
* Troubleshooting
* Environment-reset instructions

Explain the relationship between:

* Python runtime dependencies
* Python development dependencies
* Production dependencies
* Node development dependencies

---

# 38. COMMON COMMANDS GUIDE

Create:

```text
docs/development/COMMON_COMMANDS.md
```

Document commands for:

## Environment

```bash
python --version
python -m pip --version
python -m django --version
```

## Installation

```bash
pip install -r requirements/development.txt
npm ci
```

## Django

```bash
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py createsuperuser
```

## Tests

```bash
pytest
coverage run -m pytest
coverage report
coverage html
```

## Python Quality

```bash
ruff check .
black --check .
isort --check-only .
mypy .
bandit -r apps config
```

## Templates

```bash
djlint templates --check
```

## Frontend

```bash
npm run lint
npm run format:check
```

## Pre-commit

```bash
pre-commit install
pre-commit run --all-files
```

## Project Scripts

```bash
python scripts/check_environment.py
python scripts/quality.py
python scripts/test.py
python scripts/security.py
```

Include Windows variations where path or activation behavior differs.

---

# 39. TESTING GUIDE

Create:

```text
docs/testing/TESTING_GUIDE.md
```

Document:

* Test philosophy
* Test folder conventions
* pytest configuration
* pytest-django usage
* Database tests
* Unit tests
* Integration tests
* Permission tests
* Security tests
* Accessibility-test preparation
* Fixtures
* Factories
* Mocking rules
* Coverage
* Test naming
* Running individual tests
* Debugging failures
* Avoiding brittle tests
* Avoiding implementation-only assertions

State that tests must verify behavior rather than only code execution.

Do not use real sensitive data in test fixtures.

---

# 40. SECURITY-CHECK GUIDE

Create:

```text
docs/security/SECURITY_CHECKS.md
```

Document:

* Bandit usage
* Django system checks
* Django deployment checks
* Secret-management checks
* Dependency review
* File-upload security checks planned for later phases
* Manual security review
* False-positive handling
* Suppression policy
* Security issue escalation
* CI security behavior

Every suppression must be documented and narrowly scoped.

---

# 41. GIT HOOK POLICY

Update `CONTRIBUTING.md` to require pre-commit hooks.

Developers must run:

```bash
pre-commit install
```

before contributing.

Pre-commit must check the staged or repository content for:

* Formatting
* Linting
* Invalid configuration
* Merge conflicts
* Large accidental files
* Private keys
* Unsafe patterns

Hooks support developer quality but do not replace CI.

CI remains authoritative because local hooks can be bypassed.

---

# 42. GITIGNORE UPDATES

Update `.gitignore` for tooling artifacts.

Include:

```text
# Python tooling
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
.coverage.*
htmlcov/
.pytype/
.dmypy.json
dmypy.json

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Test artifacts
test-results/
coverage.xml
junit.xml

# Build and distribution
build/
dist/
*.egg-info/

# Docker overrides
docker-compose.override.yml

# Editor and operating system
.vscode/
.idea/
.DS_Store
Thumbs.db
```

Do not ignore required lock files such as:

```text
package-lock.json
```

Do not ignore the CI workflow.

---

# 43. SECURITY REQUIREMENTS

This phase must ensure:

* No secrets are placed in configuration files.
* No real `.env` file is committed.
* No private keys are committed.
* Pre-commit checks for private-key patterns.
* Bandit scans project Python code.
* CI uses safe test environment values.
* CI permissions are minimized.
* Dependency versions are pinned.
* Tool suppressions are documented.
* Logs do not expose credentials.
* Scripts avoid unsafe shell execution.
* Development scripts validate their inputs.
* Production settings remain secure.
* SQLite database files remain ignored.
* Media files remain ignored.
* Test data contains no real personal information.

Do not weaken Django security settings to make tooling pass.

---

# 44. ACCESSIBILITY REQUIREMENTS

Tooling must support accessibility quality where practical.

Configure or document checks for:

* Semantic HTML
* Template validity
* Missing labels
* Missing alternative text
* Heading hierarchy
* Keyboard access
* Focus visibility
* Color contrast
* Accessible error messages

Automated tooling cannot fully validate accessibility.

Document that later accessibility reviews require:

* Manual keyboard testing
* Screen-reader testing
* Responsive testing
* Contrast testing
* Modal focus testing
* Form-error testing

Do not claim WCAG compliance based only on automated linting.

---

# 45. PERFORMANCE REQUIREMENTS

The development tooling must remain reasonably fast.

Configure:

* Tool caches
* Scoped source directories
* Appropriate exclusions
* CI dependency caching
* Separate quick and full validation commands
* Incremental type checking where supported
* Targeted local tests
* Full CI tests

Recommended command categories:

## Quick Check

* Ruff
* Black check
* isort check
* Selected tests

## Full Check

* All format checks
* All linters
* mypy
* Bandit
* Full pytest
* Coverage
* Django checks
* Frontend checks

Do not skip full validation before completing a phase.

---

# 46. CROSS-PLATFORM REQUIREMENTS

All essential development tasks must be executable on:

* Windows
* Linux
* macOS

Do not rely only on:

* Bash
* GNU Make
* PowerShell
* Windows batch files

Use Python-based command scripts for the cross-platform core workflow.

Shell wrappers may provide convenience but must not be the only supported method.

Use `pathlib` in Python scripts.

Avoid hard-coded path separators.

---

# 47. SCRIPT SECURITY AND QUALITY

Project scripts must:

* Use Python’s `subprocess` safely.
* Pass command arguments as lists.
* Avoid `shell=True` unless strictly justified.
* Avoid accepting unvalidated arbitrary commands.
* Return meaningful exit codes.
* Stop after critical failures.
* Display readable output.
* Hide sensitive environment values.
* Operate relative to the repository root.
* Be tested where practical.
* Include docstrings and type hints.

Do not create scripts that silently modify source code unless the command clearly states that it formats or fixes files.

---

# 48. ENVIRONMENT VALIDATION SCRIPT

Create:

```text
scripts/check_environment.py
```

It should verify:

* Supported Python version
* Active virtual environment
* Django installation
* Required Python packages
* Node availability where frontend checks are requested
* npm availability
* Required configuration files
* `.env` presence without displaying secrets
* Django settings-module resolution
* SQLite database configuration
* Required project directories
* Git availability where needed

The script should classify findings as:

* Passed
* Warning
* Failed

It must exit with a non-zero status when critical requirements are missing.

Do not fail merely because an optional tool such as Docker is unavailable.

---

# 49. QUALITY SCRIPT

Create:

```text
scripts/quality.py
```

The script should run the approved checks in a clear order:

1. Ruff
2. Black check
3. isort check
4. mypy
5. djLint
6. ESLint
7. Stylelint
8. Prettier check

Allow optional command-line flags such as:

```text
--python-only
--frontend-only
--fix
```

The `--fix` option must only run documented auto-fix commands.

Do not silently modify files when `--fix` is absent.

---

# 50. TEST SCRIPT

Create:

```text
scripts/test.py
```

The script should support:

* Full pytest suite
* Coverage mode
* Specific test path
* Stop-on-first-failure
* Reuse database
* Verbose output

Possible usage:

```bash
python scripts/test.py
python scripts/test.py --coverage
python scripts/test.py apps/core/tests/
python scripts/test.py --fail-fast
```

Arguments must be validated.

Do not use unsafe arbitrary shell concatenation.

---

# 51. SECURITY SCRIPT

Create:

```text
scripts/security.py
```

The script should run:

1. Bandit
2. Django system checks
3. Django deployment checks where appropriate
4. Pre-commit secret and private-key checks where practical
5. Approved dependency-security checks if configured

Django deployment checks may report expected local-environment warnings.

The script must distinguish:

* Expected development warnings
* Actionable security failures
* Production blockers

Do not suppress all deployment warnings.

---

# 52. CI FAILURE POLICY

The CI workflow must fail when:

* Ruff reports errors.
* Black check fails.
* isort check fails.
* mypy reports configured blocking errors.
* djLint reports blocking template issues.
* ESLint reports errors.
* Stylelint reports errors.
* Prettier check fails.
* Bandit reports issues at or above the configured severity.
* Django system checks fail.
* Uncommitted migrations are detected.
* Migrations fail.
* Tests fail.
* Coverage falls below the configured threshold.
* A configuration file is invalid.

Warnings may remain non-blocking only when documented.

Do not convert critical failures into warnings merely to make CI green.

---

# 53. TOOL-SUPPRESSION POLICY

Suppressions include:

* `# noqa`
* `# type: ignore`
* `# nosec`
* Stylelint disables
* ESLint disables
* djLint ignores
* Coverage exclusions

Every suppression must:

* Be as narrow as possible
* Identify a specific rule
* Have a legitimate reason
* Not conceal vulnerable behavior
* Be reviewed during code review
* Be removed when no longer necessary

Broad file-level or project-level suppression is prohibited without documented architectural justification.

---

# 54. EXISTING-CODE CLEANUP

After configuring tools, run them against the Phase 01 foundation.

Resolve findings in:

* Python files
* Django settings
* Core views
* URL configuration
* Tests
* Templates
* CSS
* JavaScript
* Documentation configuration

Do not rewrite valid architecture solely to satisfy an opinionated optional rule.

Where a rule conflicts with Django conventions:

1. Confirm the rule’s purpose.
2. Apply a narrow configuration adjustment.
3. Document the exception.
4. Preserve readability and security.

Do not exclude all existing code from checks.

---

# 55. DATABASE IMPACT

Phase 02 should not introduce new business-domain database models.

Expected database impact:

* No new application tables
* No new business migrations
* Existing Django migrations remain valid
* Test database creation is validated
* Migration-consistency checks are added to CI

If a tool requires a model change, reconsider the design.

Development tooling must not alter business data.

---

# 56. TESTING REQUIREMENTS

Test the tooling itself.

Validate:

## Python Formatting

```bash
black --check .
```

## Import Formatting

```bash
isort --check-only .
```

## Python Linting

```bash
ruff check .
```

## Type Checking

```bash
mypy .
```

## Django Tests

```bash
pytest
```

## Coverage

```bash
coverage run -m pytest
coverage report
```

## Security

```bash
bandit -r apps config
```

## Templates

```bash
djlint templates --check
```

## JavaScript

```bash
npm run lint:js
```

## CSS

```bash
npm run lint:css
```

## Formatting

```bash
npm run format:check
```

## Pre-commit

```bash
pre-commit run --all-files
```

## Django Checks

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Common Scripts

```bash
python scripts/check_environment.py
python scripts/quality.py
python scripts/test.py --coverage
python scripts/security.py
```

Do not report a command as successful unless it was actually run.

---

# 57. DOCUMENTATION REQUIREMENTS

Update:

## README.md

Add:

* Development-tool prerequisites
* Python setup summary
* Node setup summary
* Common quality commands
* Test commands
* Pre-commit setup
* CI summary
* Links to platform-specific guides

## CONTRIBUTING.md

Add:

* Required local checks
* Pre-commit requirement
* CI expectations
* Tool-suppression policy
* Coverage expectations
* Migration-check requirement
* Frontend formatting rules

## ARCHITECTURE.md

Document:

* Development-tool boundaries
* Why Node is used only for frontend quality tooling
* Cross-platform command strategy
* CI quality gate
* Optional Docker status
* Optional Redis status

## DEVELOPMENT_STATUS.md

At the beginning of work:

```text
Current Phase: Phase 02 — Development Environment and Tooling
Status: In Progress
Last Completed Phase: Phase 01
Next Planned Phase: Phase 03 — Core System Architecture
```

After successful validation:

```text
Current Phase: Phase 02 — Development Environment and Tooling
Status: Completed
Last Completed Phase: Phase 02
Next Planned Phase: Phase 03 — Core System Architecture
```

## CHANGELOG.md

Under `Unreleased`, record:

* Python quality-tool configuration
* Testing framework configuration
* Coverage configuration
* Security scanning
* Template linting
* Frontend linting and formatting
* Pre-commit hooks
* Common development scripts
* Continuous-integration workflow
* Platform-specific setup guides

## PROJECT_STRUCTURE.md

Add all actual configuration, script, workflow, and documentation files created during this phase.

---

# 58. PROHIBITED WORK DURING PHASE 02

Do not implement:

* Custom user model
* Authentication workflows
* User invitations
* Roles
* Permission scopes
* Organizational units
* Reference numbering
* Audit logging
* Authenticated dashboards
* Leadership management
* Membership management
* Volunteer management
* Stakeholder management
* Program management
* Project management
* Beneficiary management
* MEAL
* Report builders
* Review workflows
* Document uploads
* Registers
* Meetings
* Notifications
* Search
* Export functionality
* Finance
* Governance workflows
* Safeguarding cases
* Production deployment

Do not create placeholder applications for later phases.

Do not introduce unnecessary infrastructure.

---

# 59. IMPLEMENTATION SEQUENCE

The AI agent must follow this order:

1. Read all required governance and roadmap files.
2. Inspect the repository.
3. Confirm Phase 01 completion.
4. Run the existing Django checks and tests.
5. Update `DEVELOPMENT_STATUS.md`.
6. Audit existing dependency files.
7. Pin development dependencies.
8. Configure `pyproject.toml`.
9. Configure Ruff.
10. Configure Black.
11. Configure isort.
12. Configure mypy.
13. Configure pytest and pytest-django.
14. Configure coverage.
15. Configure Bandit.
16. Configure djLint.
17. Create `package.json`.
18. Install and pin frontend quality dependencies.
19. Configure ESLint.
20. Configure Prettier.
21. Configure Stylelint.
22. Create `.editorconfig`.
23. Configure pre-commit.
24. Create cross-platform Python scripts.
25. Create platform-specific wrapper scripts where useful.
26. Create development documentation.
27. Create CI workflow.
28. Prepare optional Docker configuration only if approved.
29. Prepare optional Redis configuration only if approved.
30. Run all checks.
31. Fix valid findings.
32. Run pre-commit against all files.
33. Review the CI workflow.
34. Update documentation.
35. Update development status.
36. Produce the final delivery report.

Do not configure every tool at once and only test at the end.

Validate incrementally.

---

# 60. ERROR-HANDLING REQUIREMENTS

When a tool fails:

1. Read the complete output.
2. Identify whether the failure is:

   * A real code issue
   * A configuration issue
   * A dependency issue
   * A platform issue
   * A false positive
3. Fix the root cause.
4. Re-run the command.
5. Document significant failures and corrections.

Do not:

* Delete tests to make pytest pass.
* Disable entire rule groups without review.
* Add broad ignore patterns.
* Lower security severity to hide findings.
* Reduce coverage thresholds without explanation.
* Skip frontend checks.
* Remove CI jobs because they fail.
* Mark unvalidated tooling as complete.

---

# 61. ACCEPTANCE CRITERIA

Phase 02 is accepted only when:

* Phase 01 completion was confirmed.
* Existing Django checks pass.
* Existing tests pass.
* Development dependencies are pinned.
* Runtime and development dependencies are separated.
* Ruff is configured and runs.
* Black is configured and runs.
* isort is configured and runs.
* mypy is configured and runs.
* pytest is configured and runs.
* pytest-django is configured and runs.
* Coverage is configured and reports results.
* Bandit is configured and runs.
* djLint is configured and runs.
* ESLint is configured and runs.
* Prettier is configured and runs.
* Stylelint is configured and runs.
* pre-commit is configured and runs against all files.
* Common cross-platform development commands exist.
* Environment-validation scripts work.
* Test scripts work.
* Security scripts work.
* CI workflow exists.
* CI validates migrations.
* CI runs backend checks.
* CI runs frontend checks.
* CI runs tests.
* CI reports coverage.
* Windows setup is documented.
* Linux setup is documented.
* macOS setup is documented.
* Common commands are documented.
* Testing is documented.
* Security checks are documented.
* `.gitignore` includes tool artifacts.
* No secrets are committed.
* No business-domain model was introduced.
* No prohibited application framework was introduced.
* Documentation matches the actual configuration.
* Development status is updated.

---

# 62. DEFINITION OF DONE

Phase 02 is complete only when:

* Formatting commands run successfully.
* Linting commands run successfully.
* Type checks run successfully under the configured policy.
* Tests run successfully.
* Coverage is generated.
* Security checks run successfully.
* Template checks run successfully.
* Frontend checks run successfully.
* Pre-commit hooks work.
* CI configuration is syntactically valid.
* CI is capable of validating pull requests.
* Migration checks are automated.
* Development setup is reproducible.
* Windows instructions are complete.
* Linux instructions are complete.
* macOS instructions are complete.
* Common commands are documented.
* Tool exceptions are narrowly documented.
* No critical unresolved tool failure remains.
* The delivery report is complete.
* Phase 03 is marked ready.

The phase is not complete when:

* Tools are listed but not configured.
* Commands are documented but do not run.
* CI exists but skips critical checks.
* Pre-commit exists but was not validated.
* Broad ignore rules hide the project.
* Dependencies are unpinned.
* Runtime dependencies include all development tools.
* Node is used as an application backend.
* Tests fail.
* Django checks fail.
* Security findings remain unresolved.
* Documentation contradicts the actual configuration.
* Optional Docker support is claimed without validation.

---

# 63. REQUIRED AI AGENT IMPLEMENTATION PROMPT

Use the following prompt to command the implementation agent.

## AI Agent Prompt

You are a senior Python and Django development-environment architect, DevOps engineer, test engineer, frontend tooling specialist, security engineer, and quality-assurance engineer working on the SITADC Youth Hub web application.

The project has completed:

* Phase 00 — Project Governance and Development Control
* Phase 01 — Project Foundation

Your active task is:

# Phase 02 — Development Environment and Tooling

Begin by reading:

1. `AGENTS.md`
2. `README.md`
3. `ARCHITECTURE.md`
4. `DEVELOPMENT_STATUS.md`
5. `DEFINITION_OF_DONE.md`
6. `NAMING_CONVENTIONS.md`
7. `PROJECT_STRUCTURE.md`
8. `CONTRIBUTING.md`
9. `SECURITY.md`
10. `roadmaps/00-Master-Development-Roadmap.md`
11. `roadmaps/01-Project-Foundation.md`
12. `roadmaps/02-Development-Environment-and-Tooling.md`

Inspect the full repository before making changes.

Confirm that the Django foundation works by running:

```bash
python manage.py check
python manage.py test
```

Update `DEVELOPMENT_STATUS.md` to mark Phase 02 as in progress.

Configure:

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

Create:

* Properly separated and pinned requirements files
* Python tool configuration
* Frontend tool configuration
* `.editorconfig`
* Common cross-platform development scripts
* Environment-validation script
* Quality-check script
* Test script
* Security-check script
* Windows development guide
* Linux development guide
* macOS development guide
* Common command guide
* Testing guide
* Security-check guide
* Continuous-integration workflow

Use Node.js only for frontend quality tools.

Do not use Node.js as the application backend.

Create a CI workflow that validates:

* Dependency installation
* Django checks
* Migration consistency
* Migrations
* Python formatting
* Import formatting
* Python linting
* Type checking
* Security scanning
* Django template linting
* JavaScript linting
* CSS linting
* Frontend formatting
* pytest
* Coverage

Configure pre-commit hooks and run them against the full repository.

Prepare Docker and Redis only when they are justified, documented, and do not become active application dependencies.

Do not implement Phase 03 or later business functionality.

Do not create user, role, organizational, reporting, document, or MEAL modules.

Run every configured command.

Resolve valid failures.

Do not hide failures using broad exclusions or suppressions.

Update:

* `README.md`
* `CONTRIBUTING.md`
* `ARCHITECTURE.md`
* `PROJECT_STRUCTURE.md`
* `CHANGELOG.md`
* `DEVELOPMENT_STATUS.md`

Do not mark Phase 02 complete until all acceptance criteria in `roadmaps/02-Development-Environment-and-Tooling.md` have been validated.

Provide the required delivery report.

---

# 64. REQUIRED DELIVERY REPORT

After completing Phase 02, provide:

## Phase Summary

Explain the tooling and development-environment foundation established.

## Active Phase

```text
Phase 02 — Development Environment and Tooling
```

## Files Created

List every created file.

## Files Modified

List every modified file.

## Dependencies Added

For each dependency, state:

* Package name
* Version
* Purpose
* Requirements file or package file

## Python Tooling

Report configuration and results for:

* Ruff
* Black
* isort
* mypy
* pytest
* pytest-django
* Coverage
* Bandit
* djLint
* pre-commit

## Frontend Tooling

Report configuration and results for:

* ESLint
* Prettier
* Stylelint
* npm scripts

## Common Commands

List the cross-platform scripts created and explain their purposes.

## Continuous Integration

Explain:

* Workflow triggers
* Python version
* Node version
* Caching
* Environment setup
* Migration validation
* Quality jobs
* Security checks
* Test execution
* Coverage behavior

## Docker and Redis

State one of:

```text
Not introduced because they are not currently required.
```

or provide:

* Files created
* Services configured
* Validation performed
* Current limitations

## Security Controls

Explain:

* Secret protection
* Private-key checks
* Bandit configuration
* CI permissions
* Dependency pinning
* Suppression policy
* Script safety

## Testing and Coverage

Report:

* Tests discovered
* Tests passed
* Tests failed
* Coverage percentage
* Coverage threshold
* Uncovered critical areas

## Commands Run

List every validation command actually executed.

## Validation Results

Provide the result of:

* Django checks
* Migration checks
* Ruff
* Black
* isort
* mypy
* pytest
* Coverage
* Bandit
* djLint
* ESLint
* Stylelint
* Prettier
* pre-commit
* Project scripts
* CI syntax review

## Problems Found

List every significant issue encountered.

## Problems Resolved

Explain each correction.

## Known Limitations

List unresolved items honestly.

## Documentation Updated

List all documentation created or updated.

## Phase Status

Use one of:

```text
Phase 02: Completed
Phase 03: Ready
```

or:

```text
Phase 02: Incomplete
```

Explain the exact blockers if incomplete.

## Next Recommended Action

```text
Proceed to Phase 03 — Core System Architecture.
```

---

# 65. PHASE COMPLETION CHECKLIST

## Governance and Entry

* [ ] `AGENTS.md` was read.
* [ ] `README.md` was read.
* [ ] Active roadmap was read.
* [ ] Phase 01 completion was confirmed.
* [ ] Existing Django checks passed.
* [ ] Existing tests passed.
* [ ] Development status was updated.

## Dependencies

* [ ] Base dependencies remain runtime-only.
* [ ] Development dependencies are separated.
* [ ] Production dependencies remain clean.
* [ ] Python dependencies are pinned.
* [ ] Node development dependencies are pinned.
* [ ] `package-lock.json` exists.
* [ ] No unnecessary dependency was added.

## Python Formatting and Linting

* [ ] Ruff is configured.
* [ ] Ruff passes.
* [ ] Black is configured.
* [ ] Black check passes.
* [ ] isort is configured.
* [ ] isort check passes.

## Type Checking

* [ ] mypy is configured.
* [ ] Django typing support is configured.
* [ ] mypy runs.
* [ ] Type ignores are narrowly scoped.
* [ ] The staged strictness policy is documented.

## Testing

* [ ] pytest is configured.
* [ ] pytest-django is configured.
* [ ] Existing tests are discovered.
* [ ] Tests pass.
* [ ] Coverage is configured.
* [ ] Coverage report is generated.
* [ ] Coverage threshold is documented.

## Security

* [ ] Bandit is configured.
* [ ] Bandit runs.
* [ ] Critical findings are resolved.
* [ ] Suppressions are documented.
* [ ] No secrets are committed.
* [ ] Private-key checks are configured.
* [ ] CI permissions are minimized.

## Templates and Frontend

* [ ] djLint is configured.
* [ ] Django templates pass checks.
* [ ] ESLint is configured.
* [ ] JavaScript passes linting.
* [ ] Prettier is configured.
* [ ] Frontend format check passes.
* [ ] Stylelint is configured.
* [ ] CSS passes linting.
* [ ] Vendor files are excluded correctly.

## Pre-commit

* [ ] `.pre-commit-config.yaml` exists.
* [ ] Hooks are installed.
* [ ] Hooks run against all files.
* [ ] Hooks pass.
* [ ] Hooks do not expose secrets.
* [ ] Hooks do not modify unrelated files unexpectedly.

## Scripts

* [ ] Environment-check script exists.
* [ ] Environment-check script works.
* [ ] Quality script exists.
* [ ] Quality script works.
* [ ] Test script exists.
* [ ] Test script works.
* [ ] Security script exists.
* [ ] Security script works.
* [ ] Scripts use safe subprocess handling.
* [ ] Scripts are cross-platform.

## Continuous Integration

* [ ] CI workflow exists.
* [ ] CI triggers are correct.
* [ ] Python setup is configured.
* [ ] Node setup is configured.
* [ ] Dependency caching is configured.
* [ ] Test environment variables are safe.
* [ ] Django checks run.
* [ ] Migration checks run.
* [ ] Migrations run.
* [ ] Python quality checks run.
* [ ] Frontend quality checks run.
* [ ] Security checks run.
* [ ] Tests run.
* [ ] Coverage runs.
* [ ] CI fails on critical errors.

## Platform Documentation

* [ ] Windows setup guide exists.
* [ ] Linux setup guide exists.
* [ ] macOS setup guide exists.
* [ ] Development environment guide exists.
* [ ] Common commands guide exists.
* [ ] Testing guide exists.
* [ ] Security-check guide exists.

## Optional Infrastructure

* [ ] Docker was either validated or intentionally deferred.
* [ ] Redis was either documented as optional or intentionally deferred.
* [ ] The application does not require Redis.
* [ ] Local development does not require Docker.

## Final Documentation

* [ ] README was updated.
* [ ] CONTRIBUTING was updated.
* [ ] ARCHITECTURE was updated.
* [ ] PROJECT_STRUCTURE was updated.
* [ ] CHANGELOG was updated.
* [ ] DEVELOPMENT_STATUS was updated.

## Final Validation

* [ ] Full quality command passes.
* [ ] Full test command passes.
* [ ] Full security command passes.
* [ ] Pre-commit passes.
* [ ] Django checks pass.
* [ ] Migration consistency check passes.
* [ ] No prohibited framework was introduced.
* [ ] No business module was prematurely implemented.
* [ ] Delivery report was produced.

---

# 66. NEXT PHASE

After Phase 02 has been completed and validated, proceed to:

# Phase 03 — Core System Architecture

Phase 03 will establish:

* Shared abstract models
* Timestamp models
* User-attribution patterns
* Soft deletion
* Archiving
* Status histories
* Service-layer conventions
* Selector and query-service conventions
* Validators
* Shared exceptions
* Shared middleware foundations
* Shared form patterns
* Shared permission foundations
* Common utilities
* Database constraints
* Transaction patterns
* Error-handling architecture
* Application boundaries
* Internal dependency rules

Do not begin Phase 03 until all Phase 02 acceptance criteria have been satisfied.
