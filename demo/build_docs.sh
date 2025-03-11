#!/bin/bash
# Script to build and preview documentation locally

# Ensure we're in the project root
cd "$(dirname "$0")/.." || exit

# Check if mkdocs is installed
if ! command -v mkdocs &> /dev/null; then
    echo "mkdocs is not installed. Installing mkdocs-material..."
    pip install mkdocs-material
fi

# Build and serve the documentation
echo "Starting documentation server at http://127.0.0.1:8000/"
echo "Press Ctrl+C to stop the server"
mkdocs serve 