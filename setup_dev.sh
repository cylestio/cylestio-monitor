#!/bin/bash
# Setup script for cylestio-monitor development environment
# This script installs pre-commit hooks and runs initial security checks

echo "Setting up cylestio-monitor development environment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3.11 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "pip is required but not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -e ".[dev,test,security]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Run initial security checks
echo "Running initial security checks..."
pre-commit run --all-files

echo "Setup complete! Your development environment is ready."
echo "Pre-commit hooks are installed and will run automatically on commit."
echo ""
echo "For compliance with SOC2, GDPR, and HIPAA, please ensure:"
echo "1. No PII or PHI is committed to the repository"
echo "2. No credentials or secrets are hardcoded"
echo "3. All security vulnerabilities are addressed promptly"
echo ""
echo "Happy coding!" 