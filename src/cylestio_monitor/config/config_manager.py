"""Configuration manager for Cylestio Monitor."""

import importlib.resources
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import platformdirs
import yaml

logger = logging.getLogger("CylestioMonitor")


class ConfigManager:
    """
    Manages the configuration for Cylestio Monitor.
    
    This class handles loading the configuration from a global location,
    or copying the default configuration to that location if it doesn't exist.
    It provides access to configuration values and ensures that the configuration
    is a single source of truth across different virtual environments.
    """

    _instance: Optional["ConfigManager"] = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls) -> "ConfigManager":
        """Implement the singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize the configuration manager."""
        self._config_dir = platformdirs.user_config_dir(
            appname="cylestio-monitor",
            appauthor="cylestio"
        )
        self._config_path = Path(self._config_dir) / "config.yaml"
        self._ensure_config_exists()
        self._load_config()
    
    def _ensure_config_exists(self) -> None:
        """
        Ensure that the global configuration file exists.
        
        If the file doesn't exist, copy the default configuration file to the global location.
        """
        if not self._config_path.exists():
            logger.info(f"Creating global configuration at {self._config_path}")
            
            # Create the directory if it doesn't exist
            os.makedirs(self._config_dir, exist_ok=True)
            
            # Copy the default configuration file
            try:
                # Get the default config file path using importlib.resources
                with importlib.resources.path("cylestio_monitor.config", "default_config.yaml") as default_path:
                    shutil.copy(default_path, self._config_path)
                logger.info("Default configuration copied successfully")
            except Exception as e:
                logger.error(f"Failed to copy default configuration: {e}")
                raise
    
    def _load_config(self) -> None:
        """Load the configuration from the global location."""
        try:
            with open(self._config_path, "r") as f:
                self._config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {self._config_path}")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def save_config(self) -> None:
        """Save the current configuration to the global location."""
        try:
            with open(self._config_path, "w") as f:
                yaml.dump(self._config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self._config_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def get_config_path(self) -> Path:
        """Get the path to the global configuration file."""
        return self._config_path
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.
        
        Args:
            key: The key to look up, using dot notation for nested keys (e.g., "security.suspicious_keywords")
            default: The default value to return if the key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        keys = key.split(".")
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by key.
        
        Args:
            key: The key to set, using dot notation for nested keys (e.g., "security.suspicious_keywords")
            value: The value to set
        """
        keys = key.split(".")
        config = self._config
        
        # Navigate to the nested dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        self.save_config()
    
    def get_suspicious_keywords(self) -> List[str]:
        """Get the list of suspicious keywords from the configuration."""
        return self.get("security.suspicious_keywords", [])
    
    def get_dangerous_keywords(self) -> List[str]:
        """Get the list of dangerous keywords from the configuration."""
        return self.get("security.dangerous_keywords", [])
    
    def reload(self) -> None:
        """Reload the configuration from the global location."""
        self._load_config()

    def reset(self) -> None:
        """Reset the configuration to default values."""
        self._config = self.default_config.copy()
        self.save_config()

    def save(self) -> None:
        """Save the current configuration to the config file."""
        self.save_config()
        
    def _save_config_to_file(self) -> None:
        """Save the configuration to the config file."""
        self.save_config() 