"""
Event deduplication module for Cylestio Monitor.

This module handles generation of event IDs and tracking of processed events
to prevent duplicate processing.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

logger = logging.getLogger(__name__)

# Track processed events to prevent duplicates
_processed_events: Set[str] = set()


def get_event_id(event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
    """
    Generate a unique identifier for an event to track duplicates.
    
    Args:
        event_type: The event type
        data: Event data
        timestamp: Event timestamp
        
    Returns:
        str: Unique event identifier
    """
    ts = timestamp.isoformat() if timestamp else datetime.now().isoformat()
    # Create a simplified representation of the data for fingerprinting
    data_repr = str(sorted([(k, str(v)[:50]) for k, v in data.items() if k not in ["timestamp"]]))
    # Combine elements into a unique identifier
    return f"{event_type}:{data_repr}:{ts[:16]}"  # Only use first part of timestamp for deduplication window


def is_duplicate_event(event_id: str) -> bool:
    """
    Check if an event has already been processed.
    
    Args:
        event_id: The event ID to check
        
    Returns:
        bool: True if the event is a duplicate, False otherwise
    """
    return event_id in _processed_events


def mark_event_processed(event_id: str) -> None:
    """
    Mark an event as processed to prevent duplicate processing.
    
    Args:
        event_id: The event ID to mark as processed
    """
    _processed_events.add(event_id)
    # Limit the size of the set to prevent memory growth
    if len(_processed_events) > 1000:
        # Remove oldest entries (arbitrary number)
        try:
            for _ in range(100):
                _processed_events.pop()
        except KeyError:
            pass 