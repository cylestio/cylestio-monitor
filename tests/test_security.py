"""Security tests for the Cylestio Monitor package."""

import pytest
from unittest.mock import patch

from cylestio_monitor.config.config_manager import ConfigManager
from cylestio_monitor.events_processor import (
    contains_dangerous,
    contains_suspicious,
    normalize_text,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the ConfigManager singleton instance before each test."""
    # Save the original instance
    original_instance = ConfigManager._instance
    
    # Reset the instance
    ConfigManager._instance = None
    
    # Run the test
    yield
    
    # Restore the original instance
    ConfigManager._instance = original_instance


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager."""
    with patch("cylestio_monitor.events_processor.config_manager") as mock_cm:
        mock_cm.get_suspicious_keywords.return_value = ["HACK", "BOMB", "REMOVE"]
        mock_cm.get_dangerous_keywords.return_value = ["DROP", "RM -RF", "EXEC(", "FORMAT"]
        yield mock_cm


@pytest.mark.security
def test_dangerous_keywords_detection(mock_config_manager):
    """Test that dangerous keywords are properly detected."""
    # Test with dangerous keywords
    assert contains_dangerous("DROP TABLE users") is True
    assert contains_dangerous("rm -rf /") is True
    assert contains_dangerous("exec(malicious_code)") is True
    assert contains_dangerous("format c:") is True

    # Test with safe text
    assert contains_dangerous("Hello, world!") is False
    assert contains_dangerous("This is a safe message") is False


@pytest.mark.security
def test_suspicious_keywords_detection(mock_config_manager):
    """Test that suspicious keywords are properly detected."""
    # Test with suspicious keywords
    assert contains_suspicious("HACK the system") is True
    assert contains_suspicious("REMOVE all files") is True
    assert contains_suspicious("BOMB the application") is True

    # Test with safe text
    assert contains_suspicious("Hello, world!") is False
    assert contains_suspicious("This is a safe message") is False


@pytest.mark.security
def test_text_normalization():
    """Test that text normalization works correctly."""
    # Test basic normalization
    assert normalize_text("Hello, World!") == "HELLO, WORLD!"
    assert normalize_text("  Spaces  ") == "SPACES"

    # Test with special characters
    assert normalize_text("Special@#$%^&*()Characters") == "SPECIAL@#$%^&*()CHARACTERS"

    # Test with numbers
    assert normalize_text("123Numbers456") == "123NUMBERS456"


@pytest.mark.security
def test_event_content_alerts(mock_config_manager):
    """Test that events with dangerous or suspicious content trigger alerts."""
    from cylestio_monitor.events_processor import log_event
    
    with patch("cylestio_monitor.events_processor.send_event_to_api") as mock_send_event_to_api, \
         patch("cylestio_monitor.events_processor.log_to_file"):
        
        # Test with dangerous content in different fields
        log_event("test_event", {"content": "DROP TABLE users"}, "TEST")
        assert mock_send_event_to_api.call_args[1]["data"]["alert"] == "dangerous"
        assert mock_send_event_to_api.call_args[1]["level"] == "warning"
        
        mock_send_event_to_api.reset_mock()
        log_event("test_event", {"message": "The server will rm -rf by mistake"}, "TEST")
        assert mock_send_event_to_api.call_args[1]["data"]["alert"] == "dangerous"
        
        # Test with suspicious content
        mock_send_event_to_api.reset_mock()
        log_event("test_event", {"text": "Someone might BOMB the server"}, "TEST")
        assert mock_send_event_to_api.call_args[1]["data"]["alert"] == "suspicious"
        
        # Test with safe content
        mock_send_event_to_api.reset_mock()
        log_event("test_event", {"value": "This is a safe message"}, "TEST")
        assert "alert" not in mock_send_event_to_api.call_args[1]["data"]
