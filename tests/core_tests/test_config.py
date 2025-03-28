"""
Core configuration tests for the Cylestio Monitor package.
Focused on essential configuration functionality only.
"""

import os
import pytest
import tempfile
import yaml
from pathlib import Path

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
def temp_config_dir():
    """Create a temporary config directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a simple config file
        config_data = {
            "security": {
                "suspicious_keywords": ["TEST", "SUSPICIOUS"],
                "dangerous_keywords": ["DANGEROUS", "CRITICAL"]
            },
            "monitoring": {
                "agent_id": "test-agent",
                "log_level": "DEBUG"
            },
            "api": {
                "base_url": "https://test-api.example.com",
                "timeout_seconds": 10
            }
        }
        
        config_path = Path(temp_dir) / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)
        
        # Patch platformdirs to use our temp directory
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("platformdirs.user_config_dir", lambda **kwargs: temp_dir)
            yield temp_dir


def test_config_manager_is_singleton(reset_config_manager):
    """Test that ConfigManager is a singleton."""
    cm1 = ConfigManager()
    cm2 = ConfigManager()
    assert cm1 is cm2


def test_config_manager_loads_defaults(reset_config_manager):
    """Test that ConfigManager loads default values."""
    cm = ConfigManager()
    # Check that some default values are loaded
    assert cm.get("security.suspicious_keywords") is not None
    assert cm.get("security.dangerous_keywords") is not None


def test_config_manager_get_set(reset_config_manager, temp_config_dir):
    """Test getting and setting config values."""
    cm = ConfigManager()
    
    # Test getting values
    assert "TEST" in cm.get_suspicious_keywords()
    assert "DANGEROUS" in cm.get_dangerous_keywords()
    assert cm.get("api.base_url") == "https://test-api.example.com"
    assert cm.get("api.timeout_seconds") == 10
    
    # Test setting a value
    cm.set("monitoring.log_level", "INFO")
    assert cm.get("monitoring.log_level") == "INFO"
    
    # Test setting a nested value that doesn't exist yet
    cm.set("new.nested.value", "test")
    assert cm.get("new.nested.value") == "test" 