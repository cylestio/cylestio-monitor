"""
Event logging functionality.

This module provides the log_event function for logging events with a standardized schema.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.event_logger import log_to_file, process_and_log_event, log_console_message
from cylestio_monitor.utils.otel import get_or_create_agent_trace_context, create_child_span
from cylestio_monitor.events.processing.security import mask_sensitive_data, check_security_concerns
from cylestio_monitor.events.schema import StandardizedEvent

# Get configuration manager instance
config_manager = ConfigManager()

# Set up module-level logger
monitor_logger = logging.getLogger("CylestioMonitor")

# Track processed events to prevent duplicates
_processed_events: Set[str] = set()


def _get_event_id(event_type: str, data: Dict[str, Any]) -> str:
    """Generate a unique identifier for events to track duplicates.
    
    Args:
        event_type: The type of event
        data: Event data
        
    Returns:
        A string identifier for the event
    """
    # Create a normalized representation of the event
    serialized_data = json.dumps(data, sort_keys=True, default=str)
    
    # Create a hash of the event type and serialized data
    return hashlib.md5(f"{event_type}:{serialized_data}".encode()).hexdigest()


def create_standardized_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> StandardizedEvent:
    """Create a standardized event object.
    
    Args:
        agent_id: ID of the agent
        event_type: Type of event
        data: Event data
        channel: Event channel
        level: Log level
        timestamp: Optional timestamp for the event
        direction: Optional direction for the event
        
    Returns:
        A StandardizedEvent object
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create the standardized event
    return StandardizedEvent(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel.upper(),
        level=level.upper(),
        timestamp=timestamp.isoformat(),
        direction=direction
    )


def log_event(
    event_type: str, 
    data: Dict[str, Any], 
    channel: str = "SYSTEM", 
    level: str = "info",
    direction: Optional[str] = None
) -> None:
    """Log a structured JSON event with uniform schema.
    
    Args:
        event_type: The type of event (e.g., "chat_exchange", "llm_call")
        data: Event data dictionary
        channel: Event channel (e.g., "SYSTEM", "LLM", "LANGCHAIN", "LANGGRAPH")
        level: Log level (e.g., "info", "warning", "error")
        direction: Message direction for chat events ("incoming" or "outgoing")
    """
    # Debug logging for LLM call events
    if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
        logger = logging.getLogger("CylestioMonitor")
        logger.debug(f"log_event: Processing LLM call event: {event_type}")
    
    # Check if this is a framework_patch event for the weather agent
    config_manager = ConfigManager()
    config_agent_id = config_manager.get("monitoring.agent_id", "unknown")
    if config_agent_id == "weather-agent" and event_type == "framework_patch":
        monitor_logger.debug(f"Skipping framework_patch event for weather-agent")
        return
    
    # Generate event ID for duplicate detection
    event_id = _get_event_id(event_type, data)
    
    # Check if we've already processed this event recently
    if event_id in _processed_events:
        monitor_logger.debug(f"Skipping duplicate event: {event_type}")
        return
    
    # Add to processed events set
    _processed_events.add(event_id)
    # Limit the size of the set to prevent memory growth
    if len(_processed_events) > 1000:
        # Remove oldest entries (arbitrary number)
        try:
            for _ in range(100):
                _processed_events.pop()
        except KeyError:
            pass
    
    # Get agent_id from data if available
    agent_id = data.get("agent_id")
    if not agent_id:
        # Only log warning if both data agent_id and config agent_id are missing
        if not config_agent_id or config_agent_id == "unknown":
            logger = logging.getLogger("CylestioMonitor")
            logger.warning(f"log_event: Missing agent_id for event: {event_type}")
        agent_id = config_agent_id or "unknown"
    
    # Add OpenTelemetry trace and span IDs if not present
    if not data.get("trace_id") and not data.get("span_id"):
        # Generate a new trace context or get existing one based on agent
        trace_context = get_or_create_agent_trace_context(agent_id)
        
        data["trace_id"] = trace_context["trace_id"]
        data["span_id"] = trace_context["span_id"]
        if trace_context["parent_span_id"]:
            data["parent_span_id"] = trace_context["parent_span_id"]
        
        # For sequential events from the same agent (like LLM_call_start → LLM_call_finish),
        # create child spans to maintain relationship
        if event_type.endswith("_finish") or event_type.endswith("_end") or event_type.endswith("_response"):
            # This is a finish event, so we keep the same span ID
            pass
        elif event_type.endswith("_start") or event_type.endswith("_begin") or event_type.endswith("_request"):
            # For start events, we create a child span for subsequent events
            trace_id, span_id, parent_span_id = create_child_span(agent_id)
            data["trace_id"] = trace_id
            data["span_id"] = span_id
            if parent_span_id:
                data["parent_span_id"] = parent_span_id
    
    # Mask sensitive data before logging
    masked_data = mask_sensitive_data(data)
    
    # Check for security concerns in the data
    alert = check_security_concerns(masked_data)
    
    # Adjust log level for security concerns
    if alert == "dangerous":
        level = "warning"
    
    # Add alert to data if it's not "none"
    if alert != "none":
        masked_data["alert"] = alert
    
    # Construct the event object
    timestamp = datetime.now()
    
    # Create a standardized event record
    event = {
        "timestamp": timestamp.isoformat(),
        "level": level.upper(),
        "agent_id": agent_id,
        "event_type": event_type,
        "channel": channel.upper(),
        "data": masked_data
    }
    
    # Add direction if provided
    if direction:
        event["direction"] = direction
    
    # Get configured log file from the config manager
    log_file = config_manager.get("monitoring.log_file")
    
    # Log to file if log_file is set
    if log_file:
        # Process the event through the standardized event pipeline
        standardized_event = create_standardized_event(
            agent_id=agent_id,
            event_type=event_type,
            data=masked_data,
            channel=channel,
            level=level,
            timestamp=timestamp,
            direction=direction
        )
        
        # Log the standardized event
        log_to_file(standardized_event.to_dict(), log_file)
    
    # Send the event to the API
    process_and_log_event(
        agent_id=agent_id, 
        event_type=event_type, 
        data=masked_data,
        channel=channel,
        level=level,
        record=event
    )
    
    # Log security alerts to console
    if alert != "none":
        log_console_message(
            message=f"Security Alert ({alert}): {event_type} event contains potentially {alert} content.",
            level="warning" if alert == "suspicious" else "error",
            channel="SECURITY"
        ) 