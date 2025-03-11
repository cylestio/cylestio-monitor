#!/bin/bash
set -e

echo "Cleaning and redeploying documentation..."

# Install MkDocs and required plugins if not already installed
pip install mkdocs mkdocs-material pymdown-extensions "mkdocstrings[python]"

# Create .nojekyll file to prevent GitHub Pages from using Jekyll
touch docs/.nojekyll

# Clean the site directory
rm -rf site/

# Clean gh-pages branch if it exists
if git ls-remote --heads origin gh-pages | grep gh-pages; then
  echo "Cleaning existing gh-pages branch..."
  git branch -D gh-pages 2>/dev/null || true
  git push origin --delete gh-pages 2>/dev/null || true
fi

# Build the documentation locally first
mkdocs build

# Deploy the documentation
mkdocs gh-deploy --force

echo "Documentation cleaned and redeployed to GitHub Pages"
echo "Please check https://docs.cylestio.com/ in a few minutes" 