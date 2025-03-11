# Contributing to Cylestio Monitor

Thank you for your interest in contributing to Cylestio Monitor! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

Please be respectful and considerate of others when contributing to this project. We expect all contributors to adhere to the following guidelines:

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

We use the following tools to enforce code style:

- **Black**: For code formatting
- **isort**: For import sorting
- **mypy**: For type checking
- **ruff**: For linting

These tools are automatically run by pre-commit hooks when you commit changes.

### Type Hints

All code must include proper type hints. We use mypy to verify type correctness.

### Docstrings

All modules, classes, and functions must have docstrings following the Google style:

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

All new features and bug fixes must include tests. We use pytest for testing.

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test interactions between components
- **Security tests**: Test security features and requirements

Run tests with:
```bash
pytest
```

### Security

Security is a top priority for this project. All code must adhere to security best practices:

- Never use `eval()`, `exec()`, or similar functions
- Always validate and sanitize user input
- Use parameterized queries for database operations
- Never log sensitive information
- Use secure defaults

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types include:
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: Code changes that neither fix a bug nor add a feature
- **test**: Adding or modifying tests
- **chore**: Changes to the build process or auxiliary tools
- **security**: Security-related changes

Example:
```
feat(db): add function to query events by date range

This adds a new function to query events within a specific date range,
which helps with implementing retention policies.

Closes #123
```

## Pull Request Process

1. Update the documentation to reflect any changes
2. Add or update tests as necessary
3. Ensure all tests pass and code style checks pass
4. Update the CHANGELOG.md file with details of your changes
5. Submit a pull request to the `main` branch

## Release Process

1. Update the version number in `pyproject.toml` following [Semantic Versioning](https://semver.org/)
2. Update the CHANGELOG.md file with details of the changes
3. Create a new release on GitHub with a tag matching the version number (e.g., `v0.1.0`)
4. The CI/CD pipeline will automatically publish the package to PyPI

## Questions?

If you have any questions or need help, please open an issue on GitHub or contact the maintainers directly. 