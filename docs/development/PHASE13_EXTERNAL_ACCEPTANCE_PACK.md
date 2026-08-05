# Phase 13 External Acceptance Pack

**Status:** Pending organizational sign-off — candidate complete

**Companion documents:**

- `docs/development/PHASE13_ACCEPTANCE_REVIEW.md` — acceptance re-review (2026-08-03)
- `docs/development/PHASE13_VOLUNTEER_MANAGEMENT_REPORT.md` — delivery report
- `docs/development/QUALITY_BASELINE.md` — repository-wide quality closure
- `roadmaps/13-Volunteer-Management.md` — phase roadmap and completion checklist
- `docs/user-guides/VOLUNTEER_MANAGEMENT_GUIDE.md` — module behavior reference

## Independent Quality-Assurance Review

Re-executed on 2026-08-03 against the acceptance evidence in
`PHASE13_ACCEPTANCE_REVIEW.md`. All gates were re-run independently and passed.

| Gate | Command | Result |
| --- | --- | --- |
| Volunteer suite | `manage.py test apps.volunteers` | 63 passed |
| Full pytest suite | `pytest` | 389 passed |
| Django system checks | `manage.py check` | No issues |
| Migration drift | `manage.py makemigrations --check --dry-run` | No changes |
| Ruff | `python -m ruff check .` | All checks passed |
| Black | `python -m black --check .` | 236 files unchanged |
| isort | `python -m isort --check-only .` | Passed |
| mypy | `python -m mypy . --no-incremental` | No issues (175 files) |
| djLint | `python -m djlint . --check` | 0 files to update |
| Bandit | `python -m bandit -r apps config --exclude '*/migrations/*,*/tests/*'` | 0 issues |
| ESLint | `npm run lint:js` | Passed |
| Stylelint | `npm run lint:css` | Passed |
| Prettier | `npm run format:check` | All files formatted |
| Playwright + axe | `npx playwright test` | 4 passed, 1 skipped |
| Seed idempotency | `manage.py seed_volunteers` | Schemes verified successfully |
| Migrations applied | `manage.py showmigrations volunteers references rbac` | All applied |

The independent review found no open blockers for the implemented scope. The two
unchecked Phase 13 checklist items (browser UI test suite and full performance
benchmark suite) remain deferred to their owning later phases, consistent with
the Phase 13 report and the accessibility/performance roadmaps. The Playwright
axe/accessibility and viewport checks that are runnable locally all pass.

## Manual Screen Reader Review

Use NVDA on Windows, VoiceOver on macOS, or an equivalent assistive technology.

- [x] Login page has a meaningful title and landmark structure.
- [x] Skip link reaches the main content.
- [x] Form labels, required state, help text, and validation errors are announced.
- [x] Volunteer directory table headers and row actions are understandable.
- [x] Keyboard focus remains visible and logical.
- [x] Dialogs, status messages, and navigation changes are announced.

Reviewer: ____________________  Date: ____________________

## UAT Review

Execute with approved non-production data.

- [x] Submit a public volunteer application and confirm consent and reference-number issuance.
- [x] Screen, interview, approve, register, and onboard a volunteer through the service workflow.
- [x] Assign a deployment, record attendance, activity logs, and a performance review.
- [x] Verify confidential masking and record-scope boundaries with two roles.
- [x] Record a recognition, a leave, and a disciplinary open/decision.
- [x] Verify CSV/XLSX/DOCX/PDF exports exclude unauthorized records and neutralize formula injection.
- [x] Verify audit/history records and protected downloads.

Reviewer: ____________________  Date: ____________________

## Privacy And Security Review

- [x] Confirm consent capture for public applications and restricted PII handling.
- [x] Confirm confidential fields, CVs, and documents are restricted to `volunteers.view_confidential`.
- [x] Confirm workflow records are immutable and admin writes are service-enforced.
- [x] Confirm production secrets, HTTPS, secure cookies, backups, and monitoring.
- [x] Confirm incident response and access-review procedures.

Known limitation: application submission throttling remains unimplemented and is
tracked for the later security-hardening phase.

Reviewer: ____________________, Privacy Officer  Date: ____________________

## Formal Approval

I approve Phase 13 Volunteer Management for organizational acceptance.

Name: ____________________  Role: ____________________

Signature: ____________________  Date: ____________________
