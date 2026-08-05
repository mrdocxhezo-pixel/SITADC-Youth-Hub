# Phase 14 Acceptance Validation

**Date:** 2026-08-03
**Status:** Accepted

## Completed Evidence

- Full pytest suite: 359 passed.
- Mypy: zero errors across 169 source files.
- Ruff, Black, isort, and djLint: passed repository-wide.
- Stakeholder tests: 73 passed.
- Stakeholder pagination and bounded-query tests: passed.
- Scoped Bandit: zero findings.
- Production `manage.py check --deploy`: passed with ephemeral validation configuration.
- Frontend ESLint, Stylelint, and Prettier: passed.
- Playwright and axe suite: 5 passed, including authenticated stakeholder reads.
- Pre-commit hooks: passed from the initialized local Git checkout.

## Browser Coverage

Automated coverage includes:

- Public home-page axe scan.
- Login-page axe scan.
- Anonymous stakeholder authorization boundary.
- Mobile, tablet, and desktop viewport overflow checks.
- Visible keyboard-focus checks for public controls.
- Authenticated admin login followed by 50 repeated and 10 concurrent stakeholder directory reads.

All six manual NVDA checks passed during interactive review and were accepted
by Teddy James on 2026-08-03.

## Performance Coverage

Completed:

- 24-row directory pagination and second-page behavior.
- Bounded stakeholder directory query count.
- SQLite exclusive-write probe: competing writer was blocked as expected; see
  `scripts/sqlite_lock_probe.py`.
- Authenticated directory read benchmark: 50 repeated reads and 10 concurrent
  reads returned HTTP 200.
- Application-level concurrent stakeholder-create probing exposed SQLite lock
  errors on the reference sequence table; this remains a database/infrastructure
  acceptance item and is not claimed as passed.

Completed against local PostgreSQL 18 on 2026-08-02:

- All existing migrations, Django checks, stakeholder seed, and stakeholder
  integrity validation passed.
- Twenty concurrent stakeholder creates produced twenty unique references.
- Twenty concurrent updates serialized without lock or integrity errors.
- PostgreSQL-backed authenticated load completed 200 sequential and 100
  concurrent reads with zero failures (p95 2.371 seconds; max 3.483 seconds).
- The disposable acceptance database and role were deleted after validation;
  no PostgreSQL password is stored in project files.

Completed against the target LAN HTTPS acceptance deployment on 2026-08-03:

- Uvicorn served the production-like Django profile over TLS at
  `192.168.0.135:8443`; deployment checks passed without warnings and static
  assets were served through WhiteNoise.
- The sustained authenticated load probe completed 300 sequential and 200
  concurrent stakeholder-directory reads with 20 workers and zero failures
  (p95 1.683 seconds; max 1.997 seconds).
- Session activity persistence was throttled to remove per-request SQLite
  session writes discovered by the initial high-concurrency run.

## Formal Review

Completed and accepted by Teddy James on 2026-08-03:

- Manual NVDA review.
- Stakeholder UAT using approved non-production scenarios and test data.
- Privacy and production-security review.

Teddy James, Privacy Officer, electronically approved Phase 14 for
organizational acceptance on 2026-08-03. Phase 14 is formally complete.

Phase 15 remains blocked by the separate incomplete Phase 13 stabilization
dependency, not by Phase 14.
