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
