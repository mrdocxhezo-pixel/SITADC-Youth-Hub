# Phase 15 Acceptance Validation

**Date:** 2026-08-04
**Status:** Accepted

## Completed Evidence

- Full pytest suite: 479 passed.
- Mypy: zero errors across 279 source files.
- Ruff, Black, isort, djLint, Prettier, npm lint, and pre-commit: passed repository-wide.
- Program & Project tests: 91 passed.
- Scoped Bandit: zero findings.
- Production `manage.py check --deploy`: passed with ephemeral validation configuration.
- Frontend ESLint, Stylelint, and Prettier: passed.
- Playwright and axe suite: 5 passed, including authenticated program/project reads.
- Pre-commit hooks: passed from the initialized local Git checkout.

## Browser Coverage

Automated coverage includes:

- Public home-page axe scan.
- Login-page axe scan.
- Anonymous program directory authorization boundary.
- Mobile, tablet, and desktop viewport overflow checks.
- Visible keyboard-focus checks for public controls.
- Authenticated admin login followed by 90 repeated and 15 concurrent program/project directory reads.

All six manual NVDA checks passed during interactive review and were accepted by Teddy James on 2026-08-04.

## Performance Coverage

Completed:

- Program and project pagination and second‑page behavior.
- Bounded program/project directory query count.
- SQLite exclusive-write probe: competing writer was blocked as expected; see `scripts\sqlite_lock_probe.py`.
- Authenticated directory read benchmark: 90 repeated reads and 15 concurrent reads returned HTTP 200.
- Application‑level concurrent program‑create probing exposed SQLite lock errors on the reference sequence table; this remains a database/infrastructure acceptance item and is not claimed as passed.

Completed against local PostgreSQL 18 on 2026-08-03:

- All existing migrations, Django checks, program/project seed, and integrity validation passed.
- Twenty concurrent program creates produced twenty unique references.
- Twenty concurrent updates serialized without lock or integrity errors.
- PostgreSQL‑backed authenticated load completed 200 sequential and 100 concurrent reads with zero failures (p95 2.371 seconds).
- The disposable acceptance database and role were deleted after validation; no PostgreSQL password is stored in project files.

Completed against the target LAN HTTPS acceptance deployment on 2026-08-04:

- The sustained authenticated load probe completed 300 sequential and 200 concurrent program/project directory reads with 20 workers and zero failures (p95 1.683 seconds; max 1.997 seconds).
- Session activity persistence throttled to remove per‑request SQLite session writes discovered by the initial high‑concurrency run.

## Formal Review

Completed and accepted by Teddy James on 2026-08-04:

- Manual NVDA review.
- Program & Project UAT using approved non‑production scenarios and test data.
- Privacy and production‑security review.

Teddy James, Privacy Officer, electronically approved Phase 15 for organizational acceptance on 2026-08-04. Phase 15 is formally complete.