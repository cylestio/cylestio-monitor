"""Tests for the configuration manager."""

import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from cylestio_monitor.config import ConfigManager, get_config_path


@pytest.fixture
def mock_config_path(tmp_path):
    """Create a temporary config path for testing."""
    config_dir = tmp_path / "cylestio-monitor"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    
    # Create a mock configuration
    test_config = {
        "security": {
            "suspicious_keywords": ["TEST1", "TEST2"],
            "dangerous_keywords": ["DANGER1", "DANGER2"]
        }
    }
    
    with open(config_path, "w") as f:
        yaml.dump(test_config, f)
    
    return config_path


@pytest.fixture
def mock_config_manager(mock_config_path):
    """Create a ConfigManager with a mocked config path."""
    with patch("cylestio_monitor.config.config_manager.platformdirs.user_config_dir") as mock_dir:
        mock_dir.return_value = str(mock_config_path.parent)
        config_manager = ConfigManager()
        yield config_manager


def test_singleton_pattern():
    """Test that ConfigManager implements the singleton pattern."""
    with patch("cylestio_monitor.config.config_manager.platformdirs.user_config_dir"):
        with patch.object(ConfigManager, "_ensure_config_exists"):
            with patch.object(ConfigManager, "_load_config"):
                cm1 = ConfigManager()
                cm2 = ConfigManager()
                assert cm1 is cm2


def test_config_path_creation(tmp_path):
    """Test that the config path is created if it doesn't exist."""
    config_dir = tmp_path / "test-config-dir"
    
    with patch("cylestio_monitor.config.config_manager.platformdirs.user_config_dir") as mock_dir:
        mock_dir.return_value = str(config_dir)
        
        # Mock the importlib.resources.path context manager
        mock_path = MagicMock()
        mock_path.__enter__.return_value = Path(__file__).parent / "fixtures" / "test_config.yaml"
        
        with patch("importlib.resources.path", return_value=mock_path):
            with patch("shutil.copy") as mock_copy:
                # Create a ConfigManager instance
                ConfigManager()
                
                # Check that the directory was created
                assert config_dir.exists()
                
                # Check that shutil.copy was called
                mock_copy.assert_called_once()


def test_get_suspicious_keywords(mock_config_manager):
    """Test getting suspicious keywords from the config."""
    keywords = mock_config_manager.get_suspicious_keywords()
    assert keywords == ["TEST1", "TEST2"]


def test_get_dangerous_keywords(mock_config_manager):
    """Test getting dangerous keywords from the config."""
    keywords = mock_config_manager.get_dangerous_keywords()
    assert keywords == ["DANGER1", "DANGER2"]


def test_get_config_value(mock_config_manager):
    """Test getting a config value by key."""
    value = mock_config_manager.get("security.suspicious_keywords")
    assert value == ["TEST1", "TEST2"]
    
    # Test with a default value
    value = mock_config_manager.get("nonexistent.key", "default")
    assert value == "default"


def test_set_config_value(mock_config_manager):
    """Test setting a config value by key."""
    with patch.object(mock_config_manager, "save_config"):
        mock_config_manager.set("security.new_key", "new_value")
        assert mock_config_manager.get("security.new_key") == "new_value"
        
        # Test creating nested keys
        mock_config_manager.set("new_section.nested.key", "nested_value")
        assert mock_config_manager.get("new_section.nested.key") == "nested_value"


def test_reload_config(mock_config_manager, mock_config_path):
    """Test reloading the configuration."""
    # Modify the config file directly
    new_config = {
        "security": {
            "suspicious_keywords": ["UPDATED1", "UPDATED2"],
            "dangerous_keywords": ["DANGER1", "DANGER2"]
        }
    }
    
    with open(mock_config_path, "w") as f:
        yaml.dump(new_config, f)
    
    # Reload the configuration
    mock_config_manager.reload()
    
    # Check that the updated values are loaded
    assert mock_config_manager.get_suspicious_keywords() == ["UPDATED1", "UPDATED2"]


def test_get_config_path_util():
    """Test the get_config_path utility function."""
    with patch("cylestio_monitor.config.utils.platformdirs.user_config_dir") as mock_dir:
        mock_dir.return_value = "/mock/config/dir"
        path = get_config_path()
        assert path == Path("/mock/config/dir/config.yaml") 