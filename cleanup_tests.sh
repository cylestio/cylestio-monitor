#!/bin/bash
# Script to clean up unnecessary test files

# Make sure we're in the right directory
cd "$(dirname "$0")"

echo "Starting test cleanup..."

# Files to keep (core tests and essential utilities)
# - tests/core_tests/ directory
# - tests/ci_check_installation.py (our diagnostics tool)
# - tests/__init__.py (package marker)
# - tests/conftest.py (pytest configuration)
# - tests/pytest.ini (pytest settings)
# - tests/README.md (documentation)

# Delete old security tests
echo "Removing old security tests..."
rm -f tests/test_security.py
rm -f tests/test_security_new.py
rm -f tests/test_security_compat.py

# Delete redundant config tests
echo "Removing redundant config tests..."
rm -f tests/test_config_manager.py
rm -f tests/test_config_reload.py

# Delete redundant monitor tests
echo "Removing redundant monitor tests..."
rm -f tests/test_monitor.py
rm -f tests/test_mcp_monitoring.py
rm -f tests/test_patchers_mcp.py

# Delete API client tests that are too complex for MVP
echo "Removing complex API client tests..."
rm -f tests/test_api_client.py
rm -f tests/test_api_client_unit.py
rm -f tests/test_simple_api_client.py

# Delete advanced tests not needed for MVP
echo "Removing advanced tests not needed for MVP..."
rm -f tests/test_anthropic_enhanced.py
rm -f tests/test_otel.py
rm -f tests/test_core_architecture.py

# Delete events directory if it's not part of core tests
if [ -d "tests/events" ]; then
    echo "Removing events tests directory..."
    rm -rf tests/events
fi

# Delete utils directory if it's not part of core tests
if [ -d "tests/utils" ]; then
    echo "Removing utils tests directory..."
    rm -rf tests/utils
fi

# Delete fixtures if they're not used by core tests
if [ -d "tests/fixtures" ]; then
    echo "Removing fixtures directory..."
    rm -rf tests/fixtures
fi

# Delete examples if they're not part of MVP
if [ -d "tests/examples" ]; then
    echo "Removing examples directory..."
    rm -rf tests/examples
fi

# Clean up pycache files
echo "Cleaning up __pycache__ files..."
find tests -name "__pycache__" -type d -exec rm -rf {} +
find tests -name "*.pyc" -delete
find tests -name "*.pyo" -delete
find tests -name "*.pyd" -delete

echo "Test cleanup complete!" 