"""
Event utilities for Cylestio Monitor.

This module provides utilities for event creation and timestamp formatting.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from cylestio_monitor.config import ConfigManager

logger = logging.getLogger("CylestioMonitor")
config_manager = ConfigManager()


def get_utc_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current time in UTC timezone
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format a datetime object as ISO-8601 string with UTC timezone and Z suffix.
    
    Args:
        dt: Datetime object to format (default: current UTC time)
        
    Returns:
        str: ISO-8601 formatted timestamp with Z suffix
    """
    if dt is None:
        dt = get_utc_timestamp()
    elif dt.tzinfo is None:
        # Assume naive datetimes are UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    # Format with Z suffix for UTC
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


def create_event_dict(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
    agent_id: Optional[str] = None,
    timestamp: Optional[datetime] = None,
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
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID 
        parent_span_id: Optional parent span ID
        
    Returns:
        Dict: Standardized event dictionary
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