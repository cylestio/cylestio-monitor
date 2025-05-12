"""
Basic tests for security features of Cylestio Monitor.

This module tests fundamental security features including:
- API key handling
- Secret detection
- Security configuration
"""

import os
import pytest
import re
import sys
import subprocess


def test_sensitive_data_not_in_package():
    """Verify that sensitive patterns are not in the built package."""
    # Run the build if package doesn't exist
    if not os.path.exists("dist"):
        subprocess.run(["python", "-m", "build", "--wheel"], check=True)

    # Find the wheel file
    wheel_files = [f for f in os.listdir("dist") if f.endswith(".whl")]
    assert wheel_files, "No wheel files found in dist directory"

    wheel_file = sorted(wheel_files)[-1]  # Get the latest wheel

    # Run a check for sensitive patterns in the wheel
    sensitive_patterns = [
        r'\.env$',
        r'\.pem$',
        r'secret',
        r'password',
        r'credential',
        r'apikey',
        r'\.p12$',
        r'\.key$'
    ]

    # Use unzip -l to list contents without extracting
    result = subprocess.run(
        ["unzip", "-l", f"dist/{wheel_file}"],
        capture_output=True,
        text=True,
        check=True
    )

    for pattern in sensitive_patterns:
        for line in result.stdout.splitlines():
            assert not re.search(pattern, line, re.IGNORECASE), \
                f"Found potentially sensitive file matching '{pattern}' in package"


def test_secure_api_key_handling():
    """Test that API keys are handled securely via environment variables."""
    # Import the module (assuming it's installed or in path)
    try:
        from cylestio_monitor import Monitor
    except ImportError:
        pytest.skip("cylestio_monitor not installed, skipping test")

    # Set up test environment
    test_api_key = "test-api-key-12345"  # pragma: allowlist secret
    os.environ["CYLESTIO_API_KEY"] = test_api_key

    # Verify that we can initialize with environment variable
    monitor = Monitor(api_key=os.environ.get("CYLESTIO_API_KEY"))

    # Clean up
    os.environ.pop("CYLESTIO_API_KEY")

    # Basic verification that key was properly stored
    assert hasattr(monitor, "api_key"), "Monitor instance should have api_key attribute"
    assert monitor.api_key == test_api_key, "API key not correctly stored"


def test_security_configuration_available():
    """Test that security configuration options are available."""
    try:
        from cylestio_monitor import start_monitoring
    except ImportError:
        pytest.skip("cylestio_monitor not installed, skipping test")

    # Test security-related configuration
    security_config = {
        "log_file": None,  # Disable file logging for test
        "telemetry_endpoint": None,  # Disable telemetry for test
        "security": {
            "content_filtering": True,
            "detect_pii": True,
            "mask_sensitive_data": True
        }
    }

    # This should not raise an exception if security config is valid
    try:
        start_monitoring(agent_id="test-agent", config=security_config)
        from cylestio_monitor import stop_monitoring
        stop_monitoring()
    except Exception as e:
        assert False, f"Failed to configure security options: {e}"
