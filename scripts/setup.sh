#!/bin/bash
# scripts/setup.sh

echo "Setting up SITADC Youth Hub Development Environment (Linux/macOS)..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements/development.txt

# Install frontend dependencies
if command -v npm > /dev/null; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "Warning: npm is not installed. Frontend tooling will not be available."
fi

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

echo "Setup complete. Run 'source .venv/bin/activate' to start working."
