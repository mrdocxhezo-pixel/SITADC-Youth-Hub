# NAMING_CONVENTIONS.md

# SITADC Youth Hub

## Naming Conventions

**Project:** SITADC Youth Hub

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

**Version:** 1.0.0

**Status:** Active

---

# Purpose

This document defines the official naming conventions for the SITADC Youth Hub project.

Following consistent naming conventions improves:

* Readability
* Maintainability
* Collaboration
* Code quality
* Searchability
* Scalability

These standards apply to all contributors, maintainers, reviewers, and AI coding agents.

---

# General Principles

Names should be:

* Clear
* Descriptive
* Consistent
* Predictable
* Meaningful
* Concise

Avoid:

* Abbreviations unless widely understood
* Single-letter variable names (except loop counters)
* Generic names like `data`, `temp`, `value`, or `test`
* Mixed naming styles

---

# Project Name

Official name:

```text
SITADC Youth Hub
```

Repository name:

```text
sitadc-youth-hub
```

Python project folder:

```text
sitadc_youth_hub
```

---

# Folder Naming

Use:

```text
snake_case
```

Examples:

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
meetings/
notifications/
audit/
finance/
communications/
settings_app/
templates/
static/
media/
```

---

# Python File Naming

Use:

```text
snake_case.py
```

Examples:

```text
views.py
models.py
forms.py
services.py
permissions.py
signals.py
validators.py
utils.py
```

Custom examples:

```text
report_service.py
leader_permissions.py
member_validator.py
notification_manager.py
```

---

# Django App Naming

Apps should use singular or commonly accepted plural names.

Examples:

```text
accounts
dashboard
leadership
membership
volunteers
projects
reports
documents
notifications
audit
```

---

# Python Variables

Use:

```python
snake_case
```

Examples:

```python
user_profile
report_status
project_budget
leader_name
approval_date
```

Avoid:

```python
UserProfile
LeaderName
leaderName
```

---

# Constants

Use:

```python
UPPER_CASE
```

Examples:

```python
MAX_FILE_SIZE
DEFAULT_PAGE_SIZE
REPORT_STATUS_APPROVED
SESSION_TIMEOUT
```

---

# Functions

Use:

```python
snake_case
```

Examples:

```python
create_report()
approve_report()
send_notification()
calculate_progress()
export_to_pdf()
```

Function names should start with a verb.

---

# Classes

Use:

```python
PascalCase
```

Examples:

```python
Volunteer
ProgramReport
ReportService
DashboardView
NotificationManager
```

---

# Django Models

Models should be singular.

Examples:

```python
Volunteer
Member
Partner
Project
Program
Beneficiary
Document
Meeting
Report
```

---

# Database Tables

Allow Django defaults.

Examples:

```text
accounts_user
reports_report
projects_project
volunteers_volunteer
documents_document
```

Do not manually rename tables unless required.

---

# Database Fields

Use:

```text
snake_case
```

Examples:

```python
first_name
last_name
phone_number
date_created
report_status
submitted_by
```

---

# Primary Keys

Use:

```python
id
```

or UUID:

```python
id = models.UUIDField(...)
```

Do not create names like:

```text
user_id_primary
project_primary_key
```

---

# Foreign Keys

Use:

```python
created_by
updated_by
leader
project
program
volunteer
```

Not:

```python
leader_id_fk
```

Django automatically creates the underlying ID column.

---

# Boolean Fields

Prefix with:

```text
is_
has_
can_
```

Examples:

```python
is_active
is_deleted
is_verified
has_attachment
can_edit
```

---

# Date & Time Fields

Use descriptive names.

Examples:

```python
created_at
updated_at
submitted_at
approved_at
deleted_at
start_date
end_date
```

---

# HTML Templates

Use:

```text
snake_case.html
```

Examples:

```text
dashboard.html
login.html
leader_profile.html
report_detail.html
meeting_list.html
```

---

# Template Blocks

Use:

```django
{% block content %}
{% block title %}
{% block sidebar %}
{% block scripts %}
{% block styles %}
```

---

# CSS Classes

Use:

```text
kebab-case
```

Examples:

```css
dashboard-card
report-status
leader-profile
volunteer-grid
approval-button
```

---

# CSS IDs

Use:

```text
kebab-case
```

Examples:

```css
#main-navbar
#report-table
#dashboard-chart
```

---

# JavaScript Variables

Use:

```javascript
camelCase
```

Examples:

```javascript
currentUser
reportStatus
approvalCount
dashboardData
```

---

# JavaScript Functions

Use:

```javascript
camelCase
```

Examples:

```javascript
loadDashboard()
submitReport()
filterMembers()
exportDocument()
```

---

# URLs

Use:

```text
kebab-case
```

Examples:

```text
/login/
/dashboard/
/reports/
/report-history/
/leader-profile/
/project-status/
```

---

# Route Names

Use:

```python
snake_case
```

Examples:

```python
dashboard
report_list
report_detail
leader_profile
project_update
```

---

# Static Files

CSS

```text
dashboard.css
reports.css
login.css
```

JavaScript

```text
dashboard.js
reports.js
charts.js
```

Images

```text
logo.png
hero_banner.jpg
dashboard_icon.svg
```

---

# Media Uploads

Recommended structure:

```text
media/

documents/
reports/
images/
profiles/
evidence/
meeting_minutes/
policies/
```

---

# Report Names

Use title case.

Examples:

```text
Annual Organizational Report

Monthly Leadership Report

Project Status Report

Monitoring Visit Report

Financial Report
```

---

# Permission Codes

Use:

```text
module.action
```

Examples:

```text
reports.view
reports.create
reports.update
reports.delete

volunteers.view
volunteers.create

documents.download
documents.upload
```

---

# Git Branches

Examples:

```text
main

develop

feature/report-management

feature/document-library

bugfix/login-error

hotfix/security-update

docs/readme-update

refactor/dashboard
```

---

# Git Tags

Use Semantic Versioning.

Examples:

```text
v1.0.0

v1.0.1

v1.1.0

v2.0.0
```

---

# Environment Variables

Use uppercase.

Examples:

```text
SECRET_KEY

DEBUG

ALLOWED_HOSTS

DATABASE_URL

EMAIL_HOST

EMAIL_PORT

EMAIL_USER

EMAIL_PASSWORD
```

---

# Documentation Files

Use uppercase names.

Examples:

```text
README.md

AGENTS.md

ARCHITECTURE.md

CHANGELOG.md

CONTRIBUTING.md

SECURITY.md

CODE_OF_CONDUCT.md

DEVELOPMENT_STATUS.md

DEFINITION_OF_DONE.md

NAMING_CONVENTIONS.md
```

---

# Test Files

Use:

```text
test_<module>.py
```

Examples:

```text
test_accounts.py

test_reports.py

test_documents.py

test_dashboard.py
```

---

# Migration Files

Use Django's automatic naming convention.

Examples:

```text
0001_initial.py

0002_add_program_model.py

0003_update_report_status.py
```

Avoid renaming migration files after they are committed.

---

# Naming Summary

| Item                  | Convention          | Example               |
| --------------------- | ------------------- | --------------------- |
| Python variables      | snake_case          | `report_status`       |
| Functions             | snake_case          | `create_report()`     |
| Classes               | PascalCase          | `VolunteerProfile`    |
| Constants             | UPPER_CASE          | `MAX_FILE_SIZE`       |
| Folders               | snake_case          | `report_management`   |
| Django apps           | snake_case          | `leadership`          |
| HTML templates        | snake_case          | `leader_profile.html` |
| CSS classes           | kebab-case          | `dashboard-card`      |
| CSS IDs               | kebab-case          | `main-navbar`         |
| JavaScript            | camelCase           | `loadDashboard()`     |
| URLs                  | kebab-case          | `/leader-profile/`    |
| Route names           | snake_case          | `leader_profile`      |
| Environment variables | UPPER_CASE          | `SECRET_KEY`          |
| Documentation         | UPPERCASE filenames | `README.md`           |

---

# Compliance

All contributors and AI coding agents must follow these naming conventions.

Any new code, documentation, database object, file, folder, template, or asset that does not comply with this standard should be corrected during code review before merging into the main branch.

Consistent naming is essential for maintaining a clean, scalable, and professional codebase throughout the lifecycle of the SITADC Youth Hub project.
