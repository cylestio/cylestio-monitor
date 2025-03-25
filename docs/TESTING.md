# Cylestio Monitor Testing Guide

## Overview

This document describes the testing approach for Cylestio Monitor, focusing on how we handle dependency issues, particularly with LangChain and database-related modules.

## Key Challenges and Solutions

### 1. LangChain Version Compatibility

**Challenge:** LangChain has undergone significant changes in its import structure and API between versions, requiring our code to handle both older (`langchain.*`) and newer (`langchain_core.*`) import patterns.

**Solution:** 
- Comprehensive mocking of LangChain modules and classes
- Try/except import patterns in production code to handle different versions
- Custom test runner that sets up mock imports before any real imports occur

### 2. Indirect Database Dependencies

**Challenge:** While our library doesn't directly use database modules like SQLAlchemy, they may be imported indirectly through dependencies.

**Solution:**
- Mock SQLAlchemy and database-related modules in tests
- Isolate tests from environment-specific configurations

### 3. Python Import System and Path Issues

**Challenge:** The Python import system can be affected by stale cache files and inconsistent paths between development and CI environments.

**Solution:**
- Custom test runner that cleans up cache files
- Explicit Python path configuration to ensure consistent import behavior
- Installation of the package in development mode before running tests

### 4. Dynamic Module Imports

**Challenge:** Some modules may be imported dynamically, making mocking more complex.

**Solution:**
- Proactive registration of mock modules in `sys.modules` before any real code runs
- Comprehensive mocking of module hierarchies

## Testing Tools

### Custom Test Runner

We've created a custom test runner (`tests/run_tests.py`) that provides several key features:

1. **Cache Cleanup:** Removes `__pycache__` directories and `.pyc` files to avoid stale bytecode
2. **Import Path Setup:** Ensures the correct Python path for imports
3. **Comprehensive Mocking:** Sets up module mocks before any real imports occur
4. **Development Mode Installation:** Ensures the package is installed in development mode

### Mock Architecture

Our mocking approach is structured to handle:

1. **Module Hierarchies:** Mock entire module trees (e.g., `langchain.callbacks.base`)
2. **Core Classes:** Mock essential classes like `BaseCallbackHandler`, `Chain`, etc.
3. **Version-Specific Imports:** Support both old and new import patterns

## Test Types

- **Unit Tests:** Test individual components with comprehensive mocking
- **Integration Tests:** Test interactions between components
- **Security Tests:** Verify security aspects of the code

## Running Tests

### Using the Custom Test Runner

```bash
# Run all tests
python tests/run_tests.py

# Run with coverage
python tests/run_tests.py --cov=src --cov-report=term-missing

# Run with specific markers
python tests/run_tests.py -m "integration"
```

### Using Pytest Directly (Not Recommended)

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## CI/CD Integration

Our CI/CD pipeline (GitHub Actions) uses the custom test runner to ensure consistent test execution. The workflow includes:

1. **Environment Setup:** Install dependencies and set up the environment
2. **Linting and Formatting:** Run code quality checks
3. **Unit Tests:** Run unit tests with coverage reporting
4. **Integration Tests:** Run integration tests for end-to-end verification
5. **Security Scanning:** Check for dependency vulnerabilities

## Best Practices for Test Development

1. **Use Fixtures:** Prefer pytest fixtures for reusable test setup
2. **Mock External Dependencies:** Always mock external API calls and services
3. **Isolate Tests:** Ensure tests don't depend on each other or environment state
4. **Focus on Functionality:** Test the actual functionality, not the implementation details
5. **Use Markers:** Use pytest markers to categorize tests (e.g., integration, security)

## Troubleshooting

If you encounter issues with tests:

1. **Clean Cache Files:** Run `python tests/run_tests.py --no-mocks` to clean cache files without running mocks
2. **Check Import Paths:** Use `python -c "import sys; print(sys.path)"` to verify the Python path
3. **Verify Mocks:** Ensure all required modules are mocked properly
4. **Check Dependencies:** Verify all required dependencies are installed 