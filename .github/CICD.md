# CI/CD Pipeline for cylestio-monitor

This document describes the CI/CD pipeline setup for cylestio-monitor.

## Workflows

### CI Workflow (ci.yml)

Runs on push to main and on pull requests:
- **Testing**: Runs pytest with coverage reporting
- **Security**: Scans for security issues with bandit and safety

### Publish Workflow (publish.yml)

Runs when a new release is published:
- Builds the package
- Verifies the package with twine
- Publishes to PyPI

### Dependency Review (dependency-review.yml)

Runs on pull requests:
- Reviews dependencies for security vulnerabilities

## Setup Instructions

### PyPI Deployment

To enable automatic deployment to PyPI:

1. Generate a PyPI API token at https://pypi.org/manage/account/token/
2. Add the token as a repository secret in GitHub:
   - Go to your repository → Settings → Secrets → Actions
   - Create a new repository secret named `PYPI_API_TOKEN`
   - Paste your PyPI token as the value

## Security Notes

The current security checks skip the following low-severity issues:
- B110: Try-except-pass patterns (these are used intentionally in specific error handling scenarios)
- B311: Standard random generators (low-risk for our usage, but should be replaced with cryptographic random generators in future releases)

## Best Practices

- Create semantic versioned releases to trigger PyPI deployments
- Review dependency review reports in pull requests
