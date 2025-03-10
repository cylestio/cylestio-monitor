#!/usr/bin/env python
"""
Demo script for the configuration management system.

This script demonstrates how to use the configuration management system
to access and modify the configuration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cylestio_monitor.config.config_manager import ConfigManager
from cylestio_monitor.config.utils import get_config_path


def main():
    """Run the demo."""
    print("Cylestio Monitor Configuration Management Demo")
    print("=============================================")
    
    # Get the configuration manager instance
    config_manager = ConfigManager()
    
    # Get the path to the global configuration file
    config_path = config_manager.get_config_path()
    print(f"\nConfiguration file is located at: {config_path}")
    
    # Check if the configuration file exists
    if os.path.exists(config_path):
        print("Configuration file exists!")
    else:
        print("Configuration file does not exist!")
    
    # Get the suspicious keywords
    suspicious_keywords = config_manager.get_suspicious_keywords()
    print(f"\nSuspicious keywords: {suspicious_keywords}")
    
    # Get the dangerous keywords
    dangerous_keywords = config_manager.get_dangerous_keywords()
    print(f"\nDangerous keywords: {dangerous_keywords}")
    
    # Get a configuration value by key
    log_level = config_manager.get("logging.level", "INFO")
    print(f"\nLog level: {log_level}")
    
    # Get a non-existent configuration value with a default
    non_existent = config_manager.get("non_existent.key", "default_value")
    print(f"\nNon-existent key with default: {non_existent}")
    
    # Utility function to get the configuration path
    util_config_path = get_config_path()
    print(f"\nConfiguration path from utility function: {util_config_path}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main() 