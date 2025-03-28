"""
Core security tests for the Cylestio Monitor package.
Focused on essential security functionality only.
"""

import pytest
from unittest.mock import patch

from cylestio_monitor.config.config_manager import ConfigManager
from cylestio_monitor.events.processing.security import (
    contains_dangerous,
    contains_suspicious,
    normalize_text,
    check_security_concerns,
    mask_sensitive_data,
)

# Path for patching the config manager in tests
PATCH_PATH = "cylestio_monitor.events.processing.security.config_manager"


@pytest.fixture
def mock_config_manager():
    """Create a mock config manager with predefined keywords."""
    with patch(PATCH_PATH) as mock_cm:
        mock_cm.get_suspicious_keywords.return_value = ["HACK", "BOMB", "REMOVE"]
        mock_cm.get_dangerous_keywords.return_value = ["DROP", "RM -RF", "EXEC(", "FORMAT"]
        yield mock_cm


def test_dangerous_keywords_detection(mock_config_manager):
    """Test that dangerous keywords are properly detected."""
    # Test with dangerous keywords
    assert contains_dangerous("DROP TABLE users") is True
    assert contains_dangerous("rm -rf /") is True
    
    # Test with safe text
    assert contains_dangerous("Hello, world!") is False


def test_suspicious_keywords_detection(mock_config_manager):
    """Test that suspicious keywords are properly detected."""
    # Test with suspicious keywords
    assert contains_suspicious("HACK the system") is True
    
    # Test with safe text
    assert contains_suspicious("Hello, world!") is False


def test_sensitive_data_masked():
    """Test that sensitive data is properly masked."""
    # Test API key masking
    data = {"api_key": "sk-1234567890abcdef", "message": "Test"}
    masked_data = mask_sensitive_data(data)
    assert masked_data["api_key"] != "sk-1234567890abcdef"
    
    # Test regular data is not masked
    assert masked_data["message"] == "Test" 