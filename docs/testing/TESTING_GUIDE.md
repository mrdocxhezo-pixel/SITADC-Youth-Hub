# Testing Guide

We use `pytest` as our test runner and `coverage` to measure code coverage.

## Running Tests
To run all tests:
```bash
pytest
```

To run tests with coverage:
```bash
pytest --cov=apps --cov-report=term-missing
```

## Writing Tests
Tests should be placed in `apps/<app_name>/tests/`.
Files must be named starting with `test_` or ending with `_test.py`.

Use the `@pytest.mark.django_db` decorator when a test requires database access.
