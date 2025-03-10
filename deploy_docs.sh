#!/bin/bash
set -e

# Install MkDocs and required plugins if not already installed
pip install mkdocs mkdocs-material "mkdocstrings[python]"

# Build and deploy the documentation
mkdocs gh-deploy --force

echo "Documentation deployed to GitHub Pages" 