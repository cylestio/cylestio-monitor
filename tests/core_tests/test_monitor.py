"""
Core monitor tests for the Cylestio Monitor package.
Focused on essential monitoring functionality only.
"""

import pytest
from unittest.mock import patch, MagicMock

from cylestio_monitor.monitor import CylestioMonitor


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    with patch("cylestio_monitor.api_client.ApiClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        yield mock_instance


def test_monitor_initialization():
    """Test that CylestioMonitor initializes correctly."""
    monitor = CylestioMonitor()
    assert monitor is not None
    assert hasattr(monitor, "add_event")
    assert hasattr(monitor, "register_processor")


def test_monitor_patching_decorator():
    """Test that the patching decorator works correctly."""
    monitor = CylestioMonitor()
    
    @monitor.patch_function
    def test_function(arg1, arg2=None):
        """Test function to be patched."""
        return f"Original: {arg1}, {arg2}"
    
    # Test that the function is still callable
    result = test_function("hello", arg2="world")
    assert "hello" in result
    assert "world" in result


def test_event_capturing_with_mock(mock_api_client):
    """Test that events are captured and sent to the API client."""
    monitor = CylestioMonitor()
    
    # Create a test event
    test_event = {
        "event_type": "test",
        "content": "Test event content",
        "metadata": {"test_key": "test_value"}
    }
    
    # Add the event
    monitor.add_event(test_event)
    
    # Check if the event was processed
    assert monitor.event_queue.qsize() > 0 or mock_api_client.send_event.called 