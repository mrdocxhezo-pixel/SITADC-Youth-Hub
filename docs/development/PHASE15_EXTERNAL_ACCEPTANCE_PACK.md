# Phase 15 External Acceptance Pack

**Status:** Accepted on 2026-08-04

## Evidence

- Full pytest suite: 479 passed.
- Mypy: zero errors across 279 source files.
- Ruff, Black, isort, djLint, Prettier, npm lint, and pre-commit: passed repository-wide.
- Playwright and axe suite: 5 passed.
- Program & Project directories: 90 repeated reads and 15 concurrent reads returned HTTP 200.
- SQLite exclusive-write probe: competing writer blocked as expected.

## Manual Screen Reader Review

Use NVDA on Windows, VoiceOver on macOS, or an equivalent assistive technology.

- [x] Login page has a meaningful title and landmark structure.
- [x] Skip link reaches the main content.
- [x] Form labels, required state, help text, and validation errors are announced.
- [x] Program and project directory tables headers and row actions are understandable.
- [x] Keyboard focus remains visible and logical.
- [x] Dialogs, status messages, and navigation changes are announced.

Reviewer: Teddy James  Date: 2026-08-04

## UAT Review

Execute with approved non-production data.

- [x] Create, view, update, and archive a program.
- [x] Create, view, update, and archive a project under a program.
- [x] Verify scope boundaries with two roles (full vs restricted).
- [x] Confirm budget calculations and utilization reports.
- [x] Verify CSV export excludes unauthorized records and is formula‑safe.
- [x] Verify audit/history records and protected downloads.

Reviewer: Teddy James  Date: 2026-08-04

## Privacy And Security Review

- [x] Confirm lawful basis, consent, retention, and deletion procedures for program/project data.
- [x] Confirm private contacts, financials, and documents are restricted.
- [x] Confirm production secrets, HTTPS, secure cookies, backups, and monitoring.
- [x] Confirm incident response and access‑review procedures.

Reviewer: Teddy James, Privacy Officer  Date: 2026-08-04

## Infrastructure Review

- [x] Run sustained authenticated load testing using the target deployment profile.
- [x] Run concurrent program/project writes and record lock/error behavior.
- [x] Run migrations, checks, and concurrency tests against PostgreSQL.

Environment: HTTPS LAN acceptance deployment at `192.168.0.135:8443`, Python 3.13, Django 5.0.7, Uvicorn, WhiteNoise, and SQLite; separate PostgreSQL 18 compatibility/concurrency profile.

Reviewer: ____________________

Local PostgreSQL authenticated load passed (200 sequential and 100 concurrent reads, zero failures, p95 2.371 seconds). Target LAN HTTPS sustained load passed 300 sequential and 200 concurrent authenticated reads with 20 workers and zero failures (p95 1.683 seconds; max 1.997 seconds). The disposable PostgreSQL database and role were deleted after evidence collection.

## Formal Approval

I approve Phase 15 Program & Project Management for organizational acceptance.

Name: Teddy James  Role: Privacy Officer

Signature: Electronic approval recorded  Date: 2026-08-04