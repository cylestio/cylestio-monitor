#!/usr/bin/env python3
"""
Verify that package metadata in pyproject.toml is consistent.
This script works with tomllib (Python >= 3.12)
"""
import sys
from pathlib import Path

# Use tomllib (Python 3.12+)
import tomllib

def verify_field(config, section, field, message=None):
    """Verify that a field exists and has a value."""
    if section not in config:
        print(f"Error: Section '{section}' not found in pyproject.toml")
        return False
    
    if field not in config[section]:
        print(f"Error: Field '{field}' not found in section '{section}'")
        return False
    
    if not config[section][field]:
        print(f"Error: {message or f'Field {field} is empty'}")
        return False
    
    return True

def verify_field_value(config, section, field, expected_value, message=None):
    """Verify that a field has a specific value."""
    if not verify_field(config, section, field):
        return False
    
    if config[section][field] != expected_value:
        print(f"Error: {message or f'Field {field} has unexpected value'}")
        return False
    
    return True

try:
    # Load the TOML file
    with Path('pyproject.toml').open('rb') as f:
        config = tomllib.load(f)
    
    # Verify required fields
    all_valid = True
    all_valid &= verify_field_value(config, 'project', 'name', 'cylestio-monitor', 'Package name mismatch')
    all_valid &= verify_field(config, 'project', 'version', 'Version not set')
    all_valid &= verify_field(config, 'project', 'description', 'Description not set')
    all_valid &= verify_field(config, 'project', 'readme', 'README not set')
    all_valid &= verify_field(config, 'project', 'license', 'License not set')
    all_valid &= verify_field(config, 'project', 'authors', 'Authors not set')
    
    if all_valid:
        print('Package metadata verification passed')
    else:
        sys.exit(1)
except Exception as e:
    print(f'Error verifying metadata: {e}')
    sys.exit(1)

if __name__ == "__main__":
    pass 