"""
Event utilities for Cylestio Monitor.

This module provides utilities for event creation and timestamp formatting.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from cylestio_monitor.config import ConfigManager

logger = logging.getLogger("CylestioMonitor")
config_manager = ConfigManager()


def get_utc_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current time in UTC timezone
    
    Example:
        >>> get_utc_timestamp()
        datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=datetime.timezone.utc)
    """
    return datetime.now(timezone.utc)


def parse_timestamp(timestamp_str: str) -> datetime:
    """
    Parse a timestamp string into a datetime object with UTC timezone.
    
    Args:
        timestamp_str: ISO format timestamp string
        
    Returns:
        datetime: Parsed datetime in UTC timezone
    
    Example:
        >>> parse_timestamp("2023-09-15T14:30:45.123Z")
        datetime.datetime(2023, 9, 15, 14, 30, 45, 123000, tzinfo=datetime.timezone.utc)
        >>> parse_timestamp("2023-09-15T14:30:45+00:00")
        datetime.datetime(2023, 9, 15, 14, 30, 45, 0, tzinfo=datetime.timezone.utc)
    
    Raises:
        ValueError: If the timestamp string is not in a valid ISO-8601 format
    """
    # Handle Z suffix
    if timestamp_str.endswith('Z'):
        # Replace Z with +00:00 for parsing
        timestamp_str = timestamp_str[:-1] + "+00:00"
    
    try:
        # Check if timezone info is present
        has_timezone = ('+' in timestamp_str or '-' in timestamp_str and timestamp_str.rindex('-') > 10)
        
        if has_timezone:
            # Parse with existing timezone info
            dt = datetime.fromisoformat(timestamp_str)
        else:
            # If no timezone specified, explicitly interpret as UTC
            dt = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
    except ValueError:
        raise ValueError(f"Invalid timestamp format: {timestamp_str}. Expected ISO-8601 format.")
    
    # Convert to UTC if not already
    return dt.astimezone(timezone.utc)


def validate_iso8601(timestamp_str: str) -> bool:
    """
    Validate if a string is in ISO-8601 format.
    
    Args:
        timestamp_str: String to validate
        
    Returns:
        bool: True if valid ISO-8601 format, False otherwise
    
    Example:
        >>> validate_iso8601("2023-09-15T14:30:45.123Z")
        True
        >>> validate_iso8601("2023-09-15 14:30:45")
        False
    """
    # ISO-8601 pattern with optional fractional seconds and timezone
    iso_pattern = r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'
    return bool(re.match(iso_pattern, timestamp_str))


def format_timestamp(dt: Optional[Union[datetime, str]] = None) -> str:
    """
    Format a datetime object or string as ISO-8601 string with UTC timezone and Z suffix.
    
    Args:
        dt: Datetime object or ISO format string to format (default: current UTC time)
        
    Returns:
        str: ISO-8601 formatted timestamp with Z suffix
    
    Example:
        >>> format_timestamp()  # Current time
        '2023-09-15T14:30:45.123456Z'
        >>> format_timestamp(datetime(2023, 9, 15, 14, 30, 45, 123456))
        '2023-09-15T14:30:45.123456Z'
        >>> format_timestamp("2023-09-15T14:30:45+00:00")
        '2023-09-15T14:30:45.000000Z'
    
    Raises:
        ValueError: If dt is a string but not in a valid ISO-8601 format
    """
    if dt is None:
        dt = get_utc_timestamp()
    elif isinstance(dt, str):
        # Parse string to datetime
        dt = parse_timestamp(dt)
    elif dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Ensure microseconds are preserved in the output
    iso_format = dt.astimezone(timezone.utc).isoformat()
    
    # If there's no microseconds in the output, add them
    if '.' not in iso_format:
        # Find the position before Z or timezone offset
        if 'Z' in iso_format:
            pos = iso_format.index('Z')
            iso_format = iso_format[:pos] + '.000000' + iso_format[pos:]
        elif '+' in iso_format:
            pos = iso_format.index('+')
            iso_format = iso_format[:pos] + '.000000' + iso_format[pos:]
        elif '-' in iso_format and iso_format.rindex('-') > 10:  # Not the date separator
            pos = iso_format.rindex('-')
            iso_format = iso_format[:pos] + '.000000' + iso_format[pos:]
    
    # Replace +00:00 with Z for UTC
    return iso_format.replace('+00:00', 'Z')


def create_event_dict(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
    agent_id: Optional[str] = None,
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a standardized event dictionary with proper timestamp formatting.
    
    Args:
        name: Event name following OpenTelemetry conventions
        attributes: Event attributes following OpenTelemetry conventions
        level: Log level (INFO, ERROR, etc.)
        agent_id: Agent identifier
        timestamp: Optional timestamp (default: current UTC time) as datetime or ISO-8601 string
        trace_id: Optional trace ID
        span_id: Optional span ID 
        parent_span_id: Optional parent span ID
        
    Returns:
        Dict: Standardized event dictionary
    
    Example:
        >>> create_event_dict("agent.startup", {"version": "1.0.0"})
        {
            "name": "agent.startup",
            "timestamp": "2023-09-15T14:30:45.123456Z",
            "level": "INFO",
            "agent_id": "default-agent",
            "attributes": {"version": "1.0.0"}
        }
    """
    # Get agent_id from config if not provided
    if agent_id is None:
        agent_id = config_manager.get("monitoring.agent_id", "unknown")
    
    # Use or create attributes dict
    attrs = attributes or {}
    
    # Create base event
    event = {
        "name": name,
        "timestamp": format_timestamp(timestamp),
        "level": level.upper(),
        "agent_id": agent_id,
        "attributes": attrs,
    }
    
    # Add optional tracing info
    if trace_id:
        event["trace_id"] = trace_id
    if span_id:
        event["span_id"] = span_id
    if parent_span_id:
        event["parent_span_id"] = parent_span_id
    
    return event 