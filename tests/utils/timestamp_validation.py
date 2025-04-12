"""
Timestamp validation utilities for testing.

This module provides utilities to validate timestamps are in the
correct ISO8601 format with UTC timezone and Z suffix.
"""

import re
from datetime import datetime, timezone, timedelta


def validate_timestamp_format(timestamp_str):
    """
    Validate that a timestamp string is in ISO8601 format with UTC timezone (Z suffix).
    
    Args:
        timestamp_str: The timestamp string to validate
        
    Returns:
        bool: True if the timestamp is valid, False otherwise
    """
    # Check if it ends with Z
    if not timestamp_str.endswith('Z'):
        return False
    
    # Check ISO8601 format with Z
    iso_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$'
    if not re.match(iso_pattern, timestamp_str):
        return False
    
    # Try to parse it
    try:
        # Replace Z with +00:00 for fromisoformat
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Verify it's UTC
        return dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) == timedelta(0)
    except ValueError:
        return False


def check_event_timestamps(event_dict):
    """
    Check that all timestamps in an event dictionary are properly formatted.
    
    This function recursively checks all string values in the event dictionary
    that contain the word "timestamp" to ensure they have the proper format.
    
    Args:
        event_dict: Event dictionary to check
        
    Returns:
        bool: True if all timestamps are valid, False otherwise
    """
    # Check main timestamp
    if "timestamp" in event_dict and isinstance(event_dict["timestamp"], str):
        if not validate_timestamp_format(event_dict["timestamp"]):
            return False
    
    # Check attributes for timestamps
    if "attributes" in event_dict and isinstance(event_dict["attributes"], dict):
        for key, value in event_dict["attributes"].items():
            if "timestamp" in key.lower() and isinstance(value, str):
                if not validate_timestamp_format(value):
                    return False
    
    # Check nested dictionaries
    for key, value in event_dict.items():
        if isinstance(value, dict):
            if not check_event_timestamps(value):
                return False
    
    return True


def check_events_list_timestamps(events_list):
    """
    Check that all timestamps in a list of events are properly formatted.
    
    Args:
        events_list: List of event dictionaries to check
        
    Returns:
        bool: True if all timestamps are valid, False otherwise
    """
    for event in events_list:
        if not check_event_timestamps(event):
            return False
    
    return True 