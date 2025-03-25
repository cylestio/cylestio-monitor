# Deleted Tests

This file documents test files that have been deleted from the codebase and the reason for their removal.

## Deleted Test Files

### `tests/test_events_processor.py`
- **Removal Date**: Prior to March 25, 2024
- **Reason**: Deprecated functionality that was DB-related has been removed from the codebase

### `tests/test_patchers_anthropic.py`
- **Removal Date**: Prior to March 25, 2024  
- **Reason**: Deprecated functionality that was DB-related has been removed from the codebase

## CI/CD Pipeline Notes

If you encounter CI/CD pipeline errors referencing these deleted files:

1. Ensure the pipeline is using a clean checkout
2. Clear all cache directories, especially `.pytest_cache` 
3. Regenerate pytest cache with the current test files by running `pytest --collect-only`

This documentation helps prevent confusion when old references appear in error messages or caches. 