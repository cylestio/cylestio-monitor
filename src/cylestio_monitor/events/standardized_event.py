"""
Standardized event processing module for Cylestio Monitor.

This module provides functions for processing standardized events
with a consistent format.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.events.deduplication import get_event_id, is_duplicate_event, mark_event_processed
from cylestio_monitor.event_logger import log_to_file, send_event_to_remote_api

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()


def process_standardized_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Process a standardized event with consistent formatting.
    
    Args:
        agent_id: The agent identifier
        event_type: The type of event
        data: Event data dictionary
        channel: Event channel
        level: Log level
        timestamp: Event timestamp
        direction: Message direction
        session_id: Session identifier
    """
    # Debug logging for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        logger.debug(f"Processing LLM call event: {event_type}")
    
    # Get timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Generate event ID for duplicate detection
    event_id = get_event_id(event_type, data, timestamp)
    
    # Check for duplicate events
    if is_duplicate_event(event_id):
        logger.debug(f"Skipping duplicate event: {event_type}")
        return
        
    # Mark event as processed
    mark_event_processed(event_id)
    
    # Create base record with required fields
    record = {
        "timestamp": timestamp.isoformat(),
        "level": level.upper(),
        "agent_id": agent_id,
        "event_type": event_type,
        "channel": channel.upper(),
    }
    
    # Add direction for chat events if provided
    if direction:
        record["direction"] = direction
        
    # Add session ID if provided
    if session_id:
        record["session_id"] = session_id
    elif "session_id" in data:
        record["session_id"] = data["session_id"]
        
    # Add conversation ID if present in data
    if "conversation_id" in data:
        record["conversation_id"] = data["conversation_id"]
    
    # Add data to record
    record["data"] = data
    
    # Log to file
    log_file = config_manager.get("monitoring.log_file")
    if log_file:
        log_to_file(record, log_file)
    
    # Send to API
    send_event_to_remote_api(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel,
        level=level,
        timestamp=timestamp,
        direction=direction
    ) 