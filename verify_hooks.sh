#!/bin/bash
# Script to verify that pre-commit and pre-push hooks are installed and working properly

echo "Verifying git hooks setup..."

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo "Error: .git directory not found. Are you in a git repository?"
    exit 1
fi

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "Error: pre-commit is not installed. Please run './setup_dev.sh' first."
    exit 1
fi

# Check if pre-commit hook is installed
if [ ! -f ".git/hooks/pre-commit" ]; then
    echo "Error: pre-commit hook is not installed. Please run 'pre-commit install'."
    exit 1
else
    echo "✅ pre-commit hook is installed."
fi

# Check if pre-push hook is installed
if [ ! -f ".git/hooks/pre-push" ]; then
    echo "Error: pre-push hook is not installed. Please run 'pre-commit install --hook-type pre-push'."
    exit 1
else
    echo "✅ pre-push hook is installed."
fi

# Verify pre-commit configuration
echo "Verifying pre-commit configuration..."
pre-commit --version

# Run a dry-run of pre-commit
echo "Running pre-commit checks (dry run)..."
pre-commit run --all-files || {
    echo "⚠️ Some pre-commit checks failed. This is expected if there are issues to fix."
    echo "   Please fix the issues before committing."
}

echo ""
echo "Hook verification complete!"
echo ""
echo "Your local security checks workflow is:"
echo "1. Make changes to code"
echo "2. Stage changes: git add ."
echo "3. Commit changes: git commit -m 'your message'"
echo "   - pre-commit hooks will run automatically"
echo "   - If they fail, fix issues and try again"
echo "4. Push changes: git push"
echo "   - pre-push hooks will run automatically"
echo "   - More comprehensive security checks will run"
echo "5. CI will run on GitHub after push"
echo ""
echo "For compliance with SOC2, GDPR, and HIPAA, remember to:"
echo "- Never commit credentials or secrets"
echo "- Never commit PII or PHI data"
echo "- Address all security warnings promptly"
echo "" 