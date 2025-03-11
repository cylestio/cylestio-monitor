#!/bin/bash
set -e

# Install MkDocs and required plugins if not already installed
pip install mkdocs mkdocs-material pymdown-extensions "mkdocstrings[python]"

# Create .nojekyll file to prevent GitHub Pages from using Jekyll
touch docs/.nojekyll

# Clean gh-pages branch if it exists
if git ls-remote --heads origin gh-pages | grep gh-pages; then
  echo "Cleaning existing gh-pages branch..."
  git branch -D gh-pages 2>/dev/null || true
  git push origin --delete gh-pages 2>/dev/null || true
fi

# Build and deploy the documentation
mkdocs gh-deploy --force

echo "Documentation deployed to GitHub Pages"
echo "If the documentation is not visible, please check the GitHub Pages settings in the repository" 