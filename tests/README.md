# Cylestio Monitor Test Suite

This directory contains the test suite for Cylestio Monitor, which ensures the functionality and reliability of the monitoring tool.

## Testing Strategy

The test suite employs a comprehensive mocking approach to handle dependencies, particularly for LangChain, LangGraph, and database-related modules. This approach serves several purposes:

1. **Isolation**: Tests run in an isolated environment, free from external dependencies.
2. **Consistency**: Tests produce consistent results regardless of installed versions of dependencies.
3. **CI/CD Compatibility**: By mocking external dependencies, we avoid compatibility issues in CI/CD pipelines.
4. **Focus on Core Functionality**: Tests focus on our core monitoring functionality rather than the behavior of external libraries.

## Key Files

- `conftest.py`: Sets up pytest fixtures and mock modules
- `run_tests.py`: Custom test runner that ensures proper mocking and cleanup
- `fixtures/`: Directory containing test fixtures and sample data

## Running Tests

### Using the Custom Test Runner

We recommend using our custom test runner script for the most reliable results:

```bash
# Run all tests with comprehensive mocking
python tests/run_tests.py

# Run specific tests
python tests/run_tests.py tests/test_api_client.py

# Run tests with specific markers
python tests/run_tests.py -m "integration"
```

### Using Pytest Directly

You can also use pytest directly, but ensure you've properly set up the environment:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Mock Architecture

Our mock architecture addresses several key challenges:

### LangChain Compatibility

We create comprehensive mocks for both old-style (`langchain.*`) and new-style (`langchain_core.*`) imports to ensure compatibility with different versions of LangChain. This allows our patchers to work correctly regardless of which LangChain version is installed.

### Database References

Even though our library doesn't directly use SQLAlchemy or other database modules, indirect references may exist through dependencies. Our mocking approach eliminates these dependencies for testing.

### Dynamic Imports

Some modules may be imported dynamically (via `importlib` or `__import__`). Our approach ensures that all required modules are available in `sys.modules` before any actual code runs.

## Troubleshooting

If you encounter issues with the tests:

1. **Clean Python Cache**: Remove `__pycache__` directories and `.pyc` files
2. **Check Mock Coverage**: Ensure all required modules are properly mocked in `conftest.py`
3. **Isolation Issues**: Use `run_tests.py` which ensures proper isolation
4. **Import Errors**: Check import order and ensure mocks are set up before imports

## CI/CD Integration

Our CI/CD pipeline uses the custom test runner to ensure tests pass consistently. Key features:

1. **Cache Cleanup**: Removes any stale Python cache files
2. **Comprehensive Mocking**: Sets up mocks for all external dependencies
3. **Consistent Environment**: Ensures the same test environment across all runs
4. **Version Pinning**: Pins dependency versions to avoid compatibility issues 