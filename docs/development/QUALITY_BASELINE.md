# Repository Quality Baseline

**Date:** 2026-08-02
**Runtime:** Python 3.13, Django 5.0.7, Node.js 11.12.1

This document records the repository-wide quality closure for Phase 14. It
replaced the temporary debt baseline without suppressing runtime or security
checks.

## Green Gates

The following checks pass from the project root:

```text
python -m ruff check .
python -m black --check .
python -m isort --check-only .
npm run lint
python -m bandit -r apps config --exclude '*/migrations/*,*/tests/*'
```

Temporary repair scripts (`fix.py`, `fix2.py`, `fix_blocks.py`, and
`fix_perms.py`) are excluded from formatter and linter discovery. They are
not application modules and are retained only as historical repair utilities.
Django declarative `Meta`, `ModelForm`, and `ModelAdmin` class namespaces use
intentional mutable declarations; their `RUF012` findings are documented by
per-file Ruff exceptions.

## Quality Closure

### Mypy

`python -m mypy . --no-incremental` reports zero errors across 169 source files.
The repository-wide Django typing remediation covered custom managers, form
field narrowing, translated seed data, nullable model relations, and custom
view class attributes without adding global error suppression.

No global `ignore_errors` setting has been added. Mypy is a green gate.

### djLint

`python -m djlint . --check` reports zero differences across all 143 templates:

```text
python -m djlint apps/stakeholders/templates --check
```

The older templates were reformatted and validated without changing template
logic. The CI pre-commit job continues to run the maintained stakeholder hooks.

## Maintenance Criteria

The baseline can be retired when:

1. Keep all repository quality checks green in CI.
2. Keep the full test suite green after future formatting or typing changes.

The remaining Phase 14 conditions are independent accessibility, concurrency,
UAT, privacy, and formal acceptance reviews listed in the Phase 14 report.
