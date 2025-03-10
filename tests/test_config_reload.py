"""Tests for configuration file loading and reloading."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from cylestio_monitor.config.config_manager import ConfigManager


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
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.yaml"
        
        # Create a test configuration
        test_config = {
            "security": {
                "suspicious_keywords": ["TEST1", "TEST2"],
                "dangerous_keywords": ["DANGER1", "DANGER2"]
            },
            "logging": {
                "level": "INFO"
            }
        }
        
        # Write the configuration to the file
        with open(config_path, "w") as f:
            yaml.dump(test_config, f)
        
        yield config_path


def test_config_reload(temp_config_file):
    """Test that configuration changes are detected after reload."""
    # Patch the platformdirs.user_config_dir to return our temp directory
    with patch("cylestio_monitor.config.config_manager.platformdirs.user_config_dir") as mock_dir:
        mock_dir.return_value = str(temp_config_file.parent)
        
        # Create a ConfigManager instance
        config_manager = ConfigManager()
        
        # Check initial values
        assert config_manager.get_suspicious_keywords() == ["TEST1", "TEST2"]
        assert config_manager.get_dangerous_keywords() == ["DANGER1", "DANGER2"]
        assert config_manager.get("logging.level") == "INFO"
        
        # Modify the configuration file directly
        modified_config = {
            "security": {
                "suspicious_keywords": ["TEST1", "TEST2", "TEST3"],
                "dangerous_keywords": ["DANGER1", "DANGER2", "DANGER3"]
            },
            "logging": {
                "level": "DEBUG"
            }
        }
        
        with open(temp_config_file, "w") as f:
            yaml.dump(modified_config, f)
        
        # Before reload, the values should be the same
        assert config_manager.get_suspicious_keywords() == ["TEST1", "TEST2"]
        assert config_manager.get_dangerous_keywords() == ["DANGER1", "DANGER2"]
        assert config_manager.get("logging.level") == "INFO"
        
        # Reload the configuration
        config_manager.reload()
        
        # After reload, the values should be updated
        assert config_manager.get_suspicious_keywords() == ["TEST1", "TEST2", "TEST3"]
        assert config_manager.get_dangerous_keywords() == ["DANGER1", "DANGER2", "DANGER3"]
        assert config_manager.get("logging.level") == "DEBUG"


def test_config_set_and_get():
    """Test setting and getting configuration values."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "config.yaml"
        
        # Patch the platformdirs.user_config_dir to return our temp directory
        with patch("cylestio_monitor.config.config_manager.platformdirs.user_config_dir") as mock_dir:
            mock_dir.return_value = str(temp_dir)
            
            # Also patch _load_config to create an empty config
            with patch.object(ConfigManager, "_load_config") as mock_load:
                # Create a ConfigManager instance with an empty config
                config_manager = ConfigManager()
                config_manager._config = {}
                config_manager._config_path = config_path
                
                # Set some values
                config_manager.set("security.suspicious_keywords", ["NEW1", "NEW2"])
                config_manager.set("security.dangerous_keywords", ["DANGER1"])
                config_manager.set("logging.level", "DEBUG")
                config_manager.set("new_section.nested.key", "value")
                
                # Get the values
                assert config_manager.get_suspicious_keywords() == ["NEW1", "NEW2"]
                assert config_manager.get_dangerous_keywords() == ["DANGER1"]
                assert config_manager.get("logging.level") == "DEBUG"
                assert config_manager.get("new_section.nested.key") == "value"
                
                # Check that the file was created and contains the expected values
                assert config_path.exists()
                
                with open(config_path, "r") as f:
                    saved_config = yaml.safe_load(f)
                
                assert saved_config["security"]["suspicious_keywords"] == ["NEW1", "NEW2"]
                assert saved_config["security"]["dangerous_keywords"] == ["DANGER1"]
                assert saved_config["logging"]["level"] == "DEBUG"
                assert saved_config["new_section"]["nested"]["key"] == "value" 