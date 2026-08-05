# scripts/test.ps1
Write-Host "Running tests with pytest..."
pytest --cov=apps --cov-report=term-missing

Write-Host "Running security scan with Bandit..."
bandit -r apps config -ll
