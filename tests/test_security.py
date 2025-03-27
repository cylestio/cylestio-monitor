"""Security tests for the Cylestio Monitor package."""

import pytest
from unittest.mock import patch

from cylestio_monitor.config.config_manager import ConfigManager
from cylestio_monitor.events.processing.security import (
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
    with patch("cylestio_monitor.events.processing.security.config_manager") as mock_cm:
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
    from cylestio_monitor.utils.event_logging import log_event
    
    with patch("cylestio_monitor.events.processing.processor.process_and_log_event") as mock_process_log_event, \
         patch("cylestio_monitor.events.processing.logger.log_to_file"):
        
        # Test with dangerous content in different fields
        log_event("test_event", {"content": "DROP TABLE users"}, "TEST")
        # Check alert in the data passed to process_and_log_event
        assert mock_process_log_event.call_args[1]["data"]["alert"] == "dangerous"
        # Check level is elevated
        assert mock_process_log_event.call_args[1]["level"] == "warning"
        
        mock_process_log_event.reset_mock()
        log_event("test_event", {"message": "The server will rm -rf by mistake"}, "TEST")
        assert mock_process_log_event.call_args[1]["data"]["alert"] == "dangerous"
        
        # Test with suspicious content
        mock_process_log_event.reset_mock()
        log_event("test_event", {"text": "Someone might BOMB the server"}, "TEST")
        assert mock_process_log_event.call_args[1]["data"]["alert"] == "suspicious"
        
        # Test with safe content
        mock_process_log_event.reset_mock()
        log_event("test_event", {"value": "This is a safe message"}, "TEST")
        assert "alert" not in mock_process_log_event.call_args[1]["data"]


@pytest.mark.security
def test_sensitive_data_not_logged():
    """Test that sensitive data like API keys are not logged in plain text."""
    from cylestio_monitor.utils.event_logging import log_event
    
    with patch("cylestio_monitor.events.processing.processor.process_and_log_event") as mock_process_log_event, \
         patch("cylestio_monitor.events.processing.logger.log_to_file"):
        
        # API keys should be masked
        api_key = "sk-1234567890abcdef"
        log_event("api_request", {"api_key": api_key, "message": "Test"}, "TEST")
        
        # Check that the API key is not logged in plain text
        sent_data = mock_process_log_event.call_args[1]["data"]
        assert api_key not in str(sent_data)
        
        # Authentication tokens should be masked
        auth_token = "Bearer eyJhbGciOiJ.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ikpva.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        log_event("user_login", {"auth_token": auth_token, "user": "test_user"}, "TEST")
        
        # Check that the token is not logged in plain text
        sent_data = mock_process_log_event.call_args[1]["data"]
        assert auth_token not in str(sent_data)
