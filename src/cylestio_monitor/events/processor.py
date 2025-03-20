"""
Event processor module.

This module provides functions for processing events through the conversion layer,
transforming them into the standardized schema before they are logged.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.events.registry import converter_factory
from cylestio_monitor.events.schema import StandardizedEvent


def process_event(
    event: Dict[str, Any]
) -> StandardizedEvent:
    """
    Process an event through the conversion layer.
    
    Args:
        event: The original event
        
    Returns:
        StandardizedEvent: The standardized event
    """
    # Convert the event using the appropriate converter
    standardized_event = converter_factory.convert_event(event)
    
    return standardized_event


def create_standardized_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None,
    session_id: Optional[str] = None
) -> StandardizedEvent:
    """
    Create a standardized event from raw components.
    
    Args:
        agent_id: Agent ID
        event_type: Event type
        data: Event data
        channel: Event channel
        level: Log level
        timestamp: Event timestamp
        direction: Event direction
        session_id: Session ID
        
    Returns:
        StandardizedEvent: The standardized event
    """
    # Create the raw event
    event = {
        "timestamp": timestamp.isoformat() if timestamp else datetime.now().isoformat(),
        "level": level.upper(),
        "agent_id": agent_id,
        "event_type": event_type,
        "channel": channel.upper(),
        "data": data
    }
    
    # Add optional fields if present
    if direction:
        event["direction"] = direction
        
    if session_id:
        event["session_id"] = session_id
    
    # Process the event through the conversion layer
    return process_event(event) 