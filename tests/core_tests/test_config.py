"""
Core configuration tests for the Cylestio Monitor package.
Focused on essential configuration functionality only.
"""

import os
import pytest
import tempfile
import yaml

from cylestio_monitor.config.config_manager import ConfigManager


@pytest.fixture
def reset_config_manager():
    """Reset the ConfigManager singleton instance before and after each test."""
    # Save the original instance
    original_instance = ConfigManager._instance
    
    # Reset the instance
    ConfigManager._instance = None
    
    # Run the test
    yield
    
    # Restore the original instance
    ConfigManager._instance = original_instance


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = {
        "log_level": "DEBUG",
        "suspicious_keywords": ["TEST", "SUSPICIOUS"],
        "dangerous_keywords": ["DANGEROUS", "CRITICAL"],
        "api": {
            "base_url": "https://test-api.example.com",
            "timeout_seconds": 10
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        yaml.dump(config_data, temp_file)
        temp_path = temp_file.name
    
    yield temp_path
    
    # Clean up after test
    os.unlink(temp_path)


def test_config_manager_is_singleton(reset_config_manager):
    """Test that ConfigManager is a singleton."""
    cm1 = ConfigManager()
    cm2 = ConfigManager()
    assert cm1 is cm2


def test_config_manager_loads_defaults(reset_config_manager):
    """Test that ConfigManager loads default values."""
    cm = ConfigManager()
    # Check that some default values are loaded
    assert cm.get_log_level() is not None
    assert cm.get_suspicious_keywords() is not None
    assert cm.get_dangerous_keywords() is not None


def test_config_manager_custom_file(reset_config_manager, temp_config_file):
    """Test that ConfigManager can load a custom config file."""
    cm = ConfigManager(config_file=temp_config_file)
    
    # Check that values from the custom file are loaded
    assert cm.get_log_level() == "DEBUG"
    assert "TEST" in cm.get_suspicious_keywords()
    assert "DANGEROUS" in cm.get_dangerous_keywords()
    assert cm.get_api_config()["base_url"] == "https://test-api.example.com"
    assert cm.get_api_config()["timeout_seconds"] == 10 