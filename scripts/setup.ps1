# scripts/setup.ps1
Write-Host "Setting up SITADC Youth Hub Development Environment (Windows)..."

# Create virtual environment if it doesn't exist
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements/development.txt

# Install frontend dependencies
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "Installing frontend dependencies..."
    npm install
} else {
    Write-Host "Warning: npm is not installed. Frontend tooling will not be available." -ForegroundColor Yellow
}

# Set up pre-commit hooks
Write-Host "Setting up pre-commit hooks..."
pre-commit install

Write-Host "Setup complete. Run '.venv\Scripts\Activate.ps1' to start working." -ForegroundColor Green
