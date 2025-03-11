#!/bin/bash
set -e

echo "Force deploying documentation..."

# Save the current branch name
CURRENT_BRANCH=$(git symbolic-ref --short HEAD || echo "detached")
echo "Current branch: $CURRENT_BRANCH"

# Install MkDocs and required plugins if not already installed
pip install mkdocs mkdocs-material pymdown-extensions "mkdocstrings[python]"

# Create .nojekyll file to prevent GitHub Pages from using Jekyll
touch docs/.nojekyll

# Clean the site directory
rm -rf site/

# Build the documentation locally first
mkdocs build

# Create a temporary directory for the gh-pages branch
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"

# Copy the built site to the temporary directory
cp -R site/* $TEMP_DIR/
cp docs/.nojekyll $TEMP_DIR/
cp CNAME $TEMP_DIR/

# Switch to gh-pages branch or create it if it doesn't exist
if git show-ref --verify --quiet refs/heads/gh-pages; then
  echo "Checking out existing gh-pages branch"
  git checkout gh-pages
else
  echo "Creating new gh-pages branch"
  git checkout --orphan gh-pages
  git rm -rf .
fi

# Remove all files in the current directory except .git
find . -maxdepth 1 -not -path "./.git" -not -path "." -exec rm -rf {} \;

# Copy the built site from the temporary directory
cp -R $TEMP_DIR/* .
cp $TEMP_DIR/.nojekyll .

# Add all files
git add -A

# Commit changes
git commit -m "Deploy documentation to GitHub Pages" --no-verify || echo "No changes to commit"

# Push to remote
git push origin gh-pages --force --no-verify

# Clean up
rm -rf $TEMP_DIR
echo "Temporary directory removed"

# Switch back to the original branch
git checkout $CURRENT_BRANCH

echo "Documentation force deployed to GitHub Pages"
echo "Please check https://docs.cylestio.com/ in a few minutes" 