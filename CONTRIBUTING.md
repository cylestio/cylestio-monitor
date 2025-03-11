# Contributing to Cylestio Monitor

Thank you for your interest in contributing to Cylestio Monitor! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

We expect all contributors to interact respectfully and professionally. Please:

- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/cylestio-monitor.git
   cd cylestio-monitor
   ```
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev,test,security]"
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   pre-commit install --hook-type pre-push
   ```
5. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Guidelines

### Code Style

We enforce consistent code style with automated tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking
- **ruff**: Linting

These tools run automatically via pre-commit hooks when you commit changes.

### Type Hints

All code must include proper type hints. We use mypy to verify type correctness.

### Docstrings

All modules, classes, and functions must have Google-style docstrings:

```python
def example_function(param1: str, param2: int) -> bool:
    """
    Short description of the function.
    
    Longer description explaining the function's purpose and behavior.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of the return value
        
    Raises:
        ValueError: When param1 is empty
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
    # Function implementation
    return True
```

### Testing

All new features and bug fixes must include tests. We use pytest for testing:

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test interactions between components
- **Security tests**: Test security features and requirements

Run the test suite with:
```bash
pytest
```

### Security

Security is our top priority. Please adhere to these practices:

- Never use `eval()`, `exec()`, or similar functions
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Never log sensitive information

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types include:
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Changes that do not affect code functionality
- **refactor**: Code changes that neither fix a bug nor add a feature
- **test**: Adding or modifying tests
- **chore**: Changes to the build process or auxiliary tools
- **security**: Security-related changes

## Pull Request Process

1. Update documentation to reflect any changes
2. Add or update tests as necessary
3. Ensure all tests pass and code style checks pass
4. Update the CHANGELOG.md file with details of your changes
5. Submit a pull request to the `main` branch

## Publishing a Release

For maintainers, follow these steps to publish a new release:

1. Ensure all tests pass
   ```bash
   python -m pytest
   ```

2. Update version numbers in:
   - `pyproject.toml`
   - `src/cylestio_monitor/__init__.py`

3. Update CHANGELOG.md with new version and changes

4. Commit changes and push to main
   ```bash
   git add pyproject.toml src/cylestio_monitor/__init__.py CHANGELOG.md
   git commit -m "chore: prepare release x.y.z"
   git push origin main
   ```

5. Create a new GitHub release:
   - Tag version: `vx.y.z` (must start with 'v')
   - Title: `Release vx.y.z`
   - Description: Copy relevant section from CHANGELOG.md

The GitHub Actions workflow will automatically build, test, and publish to PyPI.

## Questions?

If you have questions or need help, please open an issue on GitHub or contact the maintainers directly. 