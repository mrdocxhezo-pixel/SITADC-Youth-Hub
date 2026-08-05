# CONTRIBUTING.md

# Contributing to SITADC Youth Hub

Thank you for your interest in contributing to the **SITADC Youth Hub**.

This project is the official organizational management platform for the **Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization**.

The goal is to build a secure, scalable, maintainable, and production-ready Django application that supports organizational governance, leadership, membership, volunteer management, program implementation, reporting, monitoring, evaluation, accountability, learning (MEAL), document management, and decision support.

---

# Project Technology Stack

The project currently uses:

* Python 3.12+
* Django 5+
* SQLite (Development Database)
* HTML5
* CSS3
* Bootstrap 5
* JavaScript (ES6+)
* Django Templates
* Django ORM
* Django Authentication
* Django Admin
* Git
* GitHub
* Antigravity AI
* OpenCode AI

**Development Database**

SQLite is the official database for local development because it is lightweight, requires no additional setup, and simplifies onboarding for contributors.

Future production deployments may migrate to PostgreSQL or another enterprise-supported database without changing application business logic.

---

# Development Principles

Every contribution should follow these principles:

* Security First
* Clean Architecture
* Modular Design
* Readable Code
* Performance
* Accessibility
* Maintainability
* Documentation
* Testability
* Scalability

Every change should improve the project without introducing unnecessary complexity.

---

# Before You Contribute

Before writing code:

1. Read `README.md`.
2. Read `AGENTS.md`.
3. Read `ARCHITECTURE.md`.
4. Review the Development Roadmaps.
5. Read this `CONTRIBUTING.md`.
6. Synchronize your branch with the latest `main`.

---

# Development Workflow

1. Fork the repository (if applicable).
2. Clone the repository.
3. Create a new feature branch.
4. Implement your changes.
5. Run formatting and quality checks.
6. Run all tests.
7. Update documentation where necessary.
8. Commit using clear commit messages.
9. Push your branch.
10. Open a Pull Request for review.

---

# Branch Naming

Use descriptive branch names.

Examples:

* `feature/authentication`
* `feature/report-management`
* `feature/document-library`
* `feature/dashboard`
* `bugfix/login-validation`
* `bugfix/export-error`
* `hotfix/security-patch`
* `docs/update-readme`
* `refactor/leadership-module`

---

# Commit Message Convention

Follow Conventional Commits.

Examples:

```text
feat(authentication): add invitation registration

fix(report): resolve PDF export issue

docs: update README

refactor(user): simplify profile service

test(meal): add indicator unit tests

style: format project

chore: update dependencies
```

---

# Coding Standards

Contributors should:

* Follow PEP 8.
* Use meaningful variable names.
* Keep functions small.
* Write reusable components.
* Avoid duplicated code.
* Separate business logic from presentation.
* Document complex logic.
* Remove unused code before submission.

---

# Django Standards

Follow Django best practices.

* One responsibility per app.
* Keep models focused.
* Use Django Forms or ModelForms where appropriate.
* Keep views clean.
* Move business logic into services when needed.
* Use class-based views where suitable.
* Use migrations for all schema changes.

---

# Database Guidelines

Development uses:

* SQLite

Guidelines:

* Never edit migration files after they have been committed.
* Create a new migration for every schema change.
* Keep models normalized.
* Avoid unnecessary database queries.
* Use indexes where appropriate.
* Test migrations before submitting.

---

# Frontend Guidelines

The interface should be:

* Responsive
* Accessible
* Mobile friendly
* Clean
* Professional
* Consistent

Use:

* Bootstrap components
* Reusable templates
* Semantic HTML
* Minimal JavaScript
* Consistent spacing
* SITADC branding

---

# Security Requirements

Every contribution must protect:

* User accounts
* Personal information
* Uploaded documents
* Organizational records

Never:

* Store passwords in plain text.
* Commit secrets or API keys.
* Disable authentication.
* Bypass permissions.
* Expose sensitive data.

Always:

* Validate input.
* Escape output.
* Protect against CSRF.
* Use Django's authentication and authorization features.
* Log important actions where appropriate.

---

# Testing

Before submitting code:

* Run unit tests.
* Verify affected functionality manually.
* Check database migrations.
* Confirm templates render correctly.
* Test responsive layouts.
* Verify role-based permissions.

Pull requests should not introduce failing tests.

---

# Documentation

Update documentation whenever you:

* Add features.
* Change workflows.
* Modify APIs.
* Update settings.
* Add configuration options.
* Change database models.

Documentation should remain synchronized with the codebase.

---

# Pull Request Checklist

Before opening a Pull Request, confirm that:

* [ ] Code builds successfully.
* [ ] Tests pass.
* [ ] Migrations are included (if required).
* [ ] Documentation is updated.
* [ ] No sensitive information is committed.
* [ ] Code follows project standards.
* [ ] Commit history is clean.
* [ ] The feature has been tested.

---

# Code Review

Every Pull Request will be reviewed for:

* Correctness
* Security
* Performance
* Readability
* Maintainability
* Documentation
* Testing
* Consistency with project architecture

Requested changes should be addressed before merging.

---

# Reporting Issues

When reporting an issue, include:

* Clear title
* Description
* Steps to reproduce
* Expected behavior
* Actual behavior
* Environment
* Screenshots (if applicable)
* Error logs (if available)

---

# Feature Requests

Feature requests should include:

* Problem statement
* Proposed solution
* Expected benefits
* Potential impact
* Relevant screenshots or mockups (if applicable)

---

# Contributor Recognition

All meaningful contributions are valued.

Contributors may be acknowledged in project documentation, release notes, or contributor listings, subject to project governance.

---

# Code of Conduct

All contributors are expected to:

* Be respectful.
* Be professional.
* Welcome constructive feedback.
* Collaborate openly.
* Support an inclusive community.
* Respect organizational policies and confidentiality.

Harassment, discrimination, or disruptive behavior will not be tolerated.

---

# License

By contributing to this project, you agree that your contributions will be licensed under the project's chosen license.

---

# Contact

**Project:** SITADC Youth Hub

**Organization:** Sustainable Initiatives Through Transformative Actions for Development in Communities (SITADC) Youth Organization

For questions regarding contributions, project governance, or development standards, contact the project maintainers through the official repository communication channels.

---

Thank you for helping build the SITADC Youth Hub. Every contribution strengthens the platform and supports the organization's mission to empower communities through innovation, accountability, and sustainable development.
