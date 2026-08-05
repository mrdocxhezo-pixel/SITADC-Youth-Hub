# scripts/quality.ps1
Write-Host "Running Python Quality Checks..."

Write-Host "1. Formatting with Black"
black .

Write-Host "2. Sorting imports with isort"
isort .

Write-Host "3. Linting with Ruff"
ruff check . --fix

Write-Host "4. Type checking with mypy"
mypy .

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "5. Formatting frontend with Prettier and linting"
    npm run lint
}

Write-Host "Quality checks complete." -ForegroundColor Green
