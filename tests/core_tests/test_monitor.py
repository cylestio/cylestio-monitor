"""
Core monitor tests for the Cylestio Monitor package.
Focused on essential monitoring functionality only.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from cylestio_monitor.monitor import start_monitoring, stop_monitoring


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    with patch("cylestio_monitor.api_client.ApiClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        # Also patch get_api_client to return our mock
        with patch("cylestio_monitor.api_client.get_api_client", return_value=mock_instance):
            yield mock_instance


@pytest.fixture
def clean_environment():
    """Clean up environment variables and restore after test."""
    # Save original environment variables
    original_env = os.environ.copy()
    
    # Remove any existing cylestio variables
    for key in list(os.environ.keys()):
        if key.startswith("CYLESTIO_"):
            del os.environ[key]
            
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


def test_monitor_initialization(clean_environment):
    """Test that monitor initializes correctly."""
    # Initialize monitoring with a test agent ID
    with patch("cylestio_monitor.utils.event_logging.log_event") as mock_log:
        with patch("cylestio_monitor.monitor.log_event") as mock_monitor_log:
            # We need to patch both imports of log_event
            start_monitoring("test-agent")
            
            # Check if either of the log_event patches was called
            assert mock_log.called or mock_monitor_log.called


def test_monitor_config_options(clean_environment):
    """Test that monitor respects configuration options."""
    # Test with custom config
    with patch("cylestio_monitor.utils.event_logging.log_event"):
        with patch("cylestio_monitor.monitor.log_event"):
            start_monitoring(
                "test-agent", 
                config={
                    "debug_level": "DEBUG",
                    "development_mode": True
                }
            )
            
            # Check that environment variable was set
            assert os.environ.get("CYLESTIO_DEVELOPMENT_MODE") == "1"


def test_monitor_api_endpoint(mock_api_client, clean_environment):
    """Test that monitor sets up the API endpoint correctly."""
    # Test with custom API endpoint
    with patch("cylestio_monitor.utils.event_logging.log_event"):
        with patch("cylestio_monitor.monitor.log_event"):
            start_monitoring(
                "test-agent", 
                config={
                    "api_endpoint": "https://test-api.example.com"
                }
            )
            
            # Check that environment variable was set
            assert os.environ.get("CYLESTIO_API_ENDPOINT") == "https://test-api.example.com" 