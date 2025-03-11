"""Utility functions for configuration management."""

from pathlib import Path

import platformdirs


def get_config_dir() -> Path:
    """
    Get the global configuration directory for Cylestio Monitor.
    
    This function returns the path to the global configuration directory,
    which is determined using platformdirs to ensure OS-agnostic behavior.
    
    Returns:
        Path: The path to the global configuration directory
    """
    config_dir = platformdirs.user_config_dir(
        appname="cylestio-monitor",
        appauthor="cylestio"
    )
    return Path(config_dir)


def get_config_path() -> Path:
    """
    Get the path to the global configuration file.
    
    This function returns the path to the global configuration file,
    which is located in the global configuration directory.
    
    Returns:
        Path: The path to the global configuration file
    """
    return get_config_dir() / "config.yaml"


def get_data_dir() -> Path:
    """
    Get the global data directory for Cylestio Monitor.
    
    This function returns the path to the global data directory,
    which is determined using platformdirs to ensure OS-agnostic behavior.
    
    Returns:
        Path: The path to the global data directory
    """
    data_dir = platformdirs.user_data_dir(
        appname="cylestio-monitor",
        appauthor="cylestio"
    )
    return Path(data_dir) 