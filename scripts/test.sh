#!/bin/bash
# scripts/test.sh

echo "Running tests with pytest..."
pytest --cov=apps --cov-report=term-missing

echo "Running security scan with Bandit..."
bandit -r apps config -ll
