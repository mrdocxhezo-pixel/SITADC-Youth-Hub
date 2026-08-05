#!/bin/bash
# scripts/quality.sh

echo "Running Python Quality Checks..."

echo "1. Formatting with Black"
black .

echo "2. Sorting imports with isort"
isort .

echo "3. Linting with Ruff"
ruff check . --fix

echo "4. Type checking with mypy"
mypy .

if command -v npm > /dev/null; then
    echo "5. Formatting frontend with Prettier and linting"
    npm run lint
fi

echo "Quality checks complete."
