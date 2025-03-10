#!/usr/bin/env python
"""
Demo script for modifying the configuration.

This script demonstrates how to modify the configuration
and verify that the changes persist.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from cylestio_monitor.config.config_manager import ConfigManager


def main():
    """Run the demo."""
    print("Cylestio Monitor Configuration Modification Demo")
    print("==============================================")
    
    # Get the configuration manager instance
    config_manager = ConfigManager()
    
    # Get the current suspicious keywords
    suspicious_keywords = config_manager.get_suspicious_keywords()
    print(f"\nCurrent suspicious keywords: {suspicious_keywords}")
    
    # Add a new suspicious keyword
    new_keyword = "NEW_SUSPICIOUS_KEYWORD"
    if new_keyword not in suspicious_keywords:
        suspicious_keywords.append(new_keyword)
        config_manager.set("security.suspicious_keywords", suspicious_keywords)
        print(f"\nAdded new suspicious keyword: {new_keyword}")
    else:
        print(f"\nKeyword {new_keyword} already exists in suspicious keywords")
    
    # Get the updated suspicious keywords
    updated_suspicious_keywords = config_manager.get_suspicious_keywords()
    print(f"\nUpdated suspicious keywords: {updated_suspicious_keywords}")
    
    # Set a new configuration value
    config_manager.set("custom.new_section.new_key", "new_value")
    print("\nAdded a new configuration section and key")
    
    # Get the new configuration value
    new_value = config_manager.get("custom.new_section.new_key")
    print(f"\nNew configuration value: {new_value}")
    
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    main() 