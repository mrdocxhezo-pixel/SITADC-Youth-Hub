# AGENTS.md

# SITADC Youth Hub
## AI Development Agent Instructions

Version: 1.0
Project: SITADC Youth Hub
Organization: Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

---

# PURPOSE

This document defines how every AI development agent must work on the SITADC Youth Hub project.

All agents must follow this document before generating, modifying, or deleting any code.

These instructions override assumptions made by the AI.

---

# PROJECT OBJECTIVE

Develop a complete enterprise organizational management system called:

SITADC Youth Hub

The application manages:

- Leadership
- Membership
- Volunteers
- Programs
- Projects
- Beneficiaries
- Stakeholders
- Partners
- Sponsors
- Donors
- Monitoring & Evaluation (MEAL)
- Governance
- Reports
- Documents
- Registers
- Audit Logs
- Notifications
- Meetings
- Workflows
- Organizational Learning

The system must be secure, scalable, maintainable, modular and production-ready.

---

# REQUIRED TECHNOLOGY STACK

The project MUST use:

Backend

- Python
- Django

Frontend

- HTML5
- CSS3
- Bootstrap 5
- Vanilla JavaScript

Database

- SQLite

Do NOT replace this stack with:

- React
- Next.js
- Vue
- Angular
- Laravel
- Node.js backend
- Firebase
- Supabase
- MongoDB

unless explicitly instructed.

---

# DEVELOPMENT PRINCIPLES

Always build using:

- Clean Architecture
- Modular Architecture
- DRY
- SOLID Principles
- Separation of Concerns
- Reusable Components
- Maintainability
- Scalability
- Secure Coding Practices
- Accessibility
- Responsive Design

Never duplicate logic.

---

# PROJECT STRUCTURE

The project should follow a modular Django architecture.

Example apps:

core/
accounts/
dashboard/
organizations/
leadership/
memberships/
volunteers/
stakeholders/
programs/
projects/
beneficiaries/
meal/
reports/
documents/
registers/
references/
finance/
notifications/
calendar_events/
communications/
governance/
risk_compliance/
audit/
search/
exports/
configuration/

Each app should contain:

- models.py
- views.py
- urls.py
- forms.py
- admin.py
- services.py (where needed)
- permissions.py (where needed)
- utils.py
- tests/
- templates/
- static/

---

# BEFORE WRITING CODE

Every task must begin by:

1. Reading AGENTS.md.
2. Reading README.md.
3. Reading the Development Roadmap.
4. Identifying the active phase.
5. Inspecting the existing project.
6. Checking for duplicate functionality.
7. Preserving valid existing code.
8. Listing files to modify.
9. Explaining implementation steps.

Never blindly overwrite files.

---

# IMPLEMENTATION RULES

Every feature must include:

Models

Forms

Views

URLs

Templates

Admin Registration

Permissions

Validation

Tests

Documentation

where applicable.

---

# DATABASE RULES

Use Django ORM only.

Do not write unnecessary raw SQL.

Normalize relationships.

Create proper:

Foreign Keys

Many-to-Many relationships

Indexes

Constraints

Migrations

Avoid duplicated data.

Design so SQLite can later migrate to PostgreSQL.

---

# USER MANAGEMENT

Use Django Authentication.

Support:

- Login
- Logout
- Invitation Registration
- Admin Approval
- Password Reset
- Profile Management
- Session Management

Passwords must never be stored in plain text.

---

# PERMISSIONS

Use Django:

Permissions

Groups

Role-based Access

Scope-based Access

Never rely only on hidden buttons.

Every request must validate permissions server-side.

---

# UI RULES

Use Bootstrap 5.

Design should be:

Professional

Modern

Clean

Responsive

Accessible

Youthful

Dashboard cards should be consistent.

Spacing should be uniform.

Use Bootstrap Icons.

Support:

Desktop

Tablet

Mobile

Light Mode

Dark Mode

---

# FORMS

All forms must include:

Validation

Helpful messages

Required indicators

Accessible labels

Responsive layouts

Server-side validation

Client-side enhancement

Never trust client-side validation alone.

---

# SECURITY

Always implement:

CSRF protection

Authentication

Authorization

Secure sessions

Input validation

Output escaping

Secure file uploads

Permission checks

Audit logging

Never hardcode:

Passwords

Secret keys

API keys

Credentials

---

# DOCUMENTS

All uploads must:

Validate file types

Validate size

Generate metadata

Track ownership

Track versions

Track approval

Support secure downloads

---

# REPORTS

Support:

Draft

Submitted

Returned

Approved

Archived

Reports must be exportable to:

PDF

DOCX

Excel

---

# AUDIT LOGGING

Log:

Login

Logout

Create

Update

Delete

Submit

Approve

Reject

Downloads

Exports

Permission changes

Configuration changes

Audit logs must be immutable.

---

# TESTING

Every major feature must include tests.

Test:

Models

Views

Forms

Permissions

Services

Authentication

Exports

Reports

Run tests before marking work complete.

---

# CODE STYLE

Follow:

PEP 8

Black formatting

isort

Ruff

Meaningful variable names

Meaningful comments

Meaningful docstrings

Avoid:

Magic numbers

Unused code

Large functions

Duplicated code

---

# GIT PRACTICES

Use descriptive commits.

One logical feature per commit.

Never commit:

Database files

Secrets

Passwords

Temporary files

Cache

---

# DOCUMENTATION

Update documentation whenever functionality changes.

Keep:

README

Roadmaps

Setup instructions

Architecture docs

Permission docs

Deployment docs

current.

---

# AI AGENT OUTPUT FORMAT

For every completed task provide:

## Summary

## Files Created

## Files Modified

## Database Changes

## Security Considerations

## Tests Added

## Documentation Updated

## Next Recommended Task

---

# DEFINITION OF DONE

A task is complete only if:

✓ Requirements implemented

✓ Permissions enforced

✓ Validation implemented

✓ Tests written

✓ Tests pass

✓ Documentation updated

✓ Responsive UI completed

✓ Accessibility considered

✓ Security implemented

✓ No duplicate functionality

✓ No placeholder code

---

# DEVELOPMENT ORDER

Always follow this sequence:

Phase 0
Project Governance

Phase 1
Project Foundation

Phase 2
Development Environment

Phase 3
Core Architecture

Phase 4
Authentication

Phase 5
Roles & Permissions

Phase 6
Organization Structure

Phase 7
Reference Numbering

Phase 8
Audit Logs

Phase 9
Dashboard

Phase 10
Leadership

Phase 11
Membership

Phase 12
Volunteers

Phase 13
Stakeholders

Phase 14
Programs

Phase 15
Projects

Phase 16
Beneficiaries

Phase 17
MEAL

Phase 18
Reports

Phase 19
Review & Approval

Phase 20
Documents

Phase 21
Registers

Phase 22
Calendar

Phase 23
Notifications

Phase 24
Search

Phase 25
Export Engine

Phase 26
Governance

Phase 27
Finance

Phase 28
Settings

Phase 29
Security Review

Phase 30
Accessibility Review

Phase 31
Performance Review

Phase 32
Testing

Phase 33
Documentation

Phase 34
Deployment

Phase 35
Final Acceptance

Never skip dependencies.

---

# FINAL INSTRUCTION

The SITADC Youth Hub must be developed as a single integrated enterprise management platform.

Every feature must integrate with:

Users

Roles

Permissions

Programs

Projects

Reports

Documents

Notifications

Audit Logs

Dashboards

Avoid isolated modules.

Think long-term.

Think maintainability.

Think security.

Think scalability.

Always produce production-quality code.
