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

# OpenTelemetry name mapping for standardization
EVENT_NAME_MAPPING = {
    # LLM events
    "LLM_call_start": "llm.request",
    "LLM_call_finish": "llm.response",
    "LLM_call_blocked": "llm.error",
    # Framework events
    "framework_patch": "framework.initialization",
    # Model events
    "model_request": "llm.chain.request",
    "model_response": "llm.chain.response",
    # Tool events
    "tool_start": "tool.execution",
    "tool_finish": "tool.result",
    "tool_error": "tool.error",
    # Chain events
    "chain_start": "chain.start",
    "chain_end": "chain.end",
    # Graph events
    "graph_node_start": "graph.node.start",
    "graph_node_end": "graph.node.end",
    "graph_edge": "graph.edge.traversal",
    # Other events
    "retrieval_query": "retrieval.query",
    "retrieval_result": "retrieval.result",
    # MCP events
    "mcp_call": "mcp.call",
    "mcp_response": "mcp.response"
}


def _get_event_id(event_name: str, data: Dict[str, Any]) -> str:
    """Generate a unique identifier for events to track duplicates.
    
    Args:
        event_name: The name of event
        data: Event data
        
    Returns:
        A string identifier for the event
    """
    # Create a normalized representation of the event
    serialized_data = json.dumps(data, sort_keys=True, default=str)
    
    # Create a hash of the event type and serialized data
    return hashlib.md5(f"{event_name}:{serialized_data}".encode(), usedforsecurity=False).hexdigest()


def create_standardized_event(
    agent_id: str,
    name: str,
    attributes: Dict[str, Any],
    level: str = "info",
    timestamp: Optional[datetime] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None
) -> StandardizedEvent:
    """Create a standardized event object.
    
    Args:
        agent_id: ID of the agent
        name: Name of event (OpenTelemetry convention)
        attributes: Event attributes following OpenTelemetry conventions
        level: Log level
        timestamp: Optional timestamp for the event
        trace_id: Optional trace ID
        span_id: Optional span ID
        parent_span_id: Optional parent span ID
        
    Returns:
        A StandardizedEvent object
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create the standardized event
    return StandardizedEvent(
        agent_id=agent_id,
        name=name,
        attributes=attributes,
        level=level.upper(),
        timestamp=timestamp.isoformat(),
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id
    )


def log_event(
    name: str, 
    attributes: Dict[str, Any], 
    level: str = "info",
    channel: Optional[str] = None,
    direction: Optional[str] = None
) -> None:
    """Log a structured JSON event with OpenTelemetry-compliant schema.
    
    Args:
        name: The name of event following OpenTelemetry conventions
        attributes: Event attributes dictionary
        level: Log level (e.g., "info", "warning", "error")
        channel: Optional legacy channel parameter
        direction: Optional legacy direction parameter
    """
    # Debug logging
    if name in ["llm.request", "llm.response", "llm.error"] or name.startswith("llm."):
        logger = logging.getLogger("CylestioMonitor")
        logger.debug(f"log_event: Processing LLM event: {name}")
    
    # Map legacy event_type names to OpenTelemetry names if needed
    otel_name = name
    if name in EVENT_NAME_MAPPING:
        otel_name = EVENT_NAME_MAPPING[name]
        monitor_logger.debug(f"Mapped legacy event name '{name}' to OpenTelemetry name '{otel_name}'")
    
    # Check if this is a framework_patch event for the weather agent
    config_manager = ConfigManager()
    config_agent_id = config_manager.get("monitoring.agent_id", "unknown")
    if config_agent_id == "weather-agent" and (otel_name == "framework.initialization" or name == "framework_patch"):
        monitor_logger.debug(f"Skipping framework initialization event for weather-agent")
        return
    
    # Generate event ID for duplicate detection
    event_id = _get_event_id(otel_name, attributes)
    
    # Check if we've already processed this event recently
    if event_id in _processed_events:
        monitor_logger.debug(f"Skipping duplicate event: {otel_name}")
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
    
    # Get agent_id from attributes if available
    agent_id = attributes.get("agent_id")
    if not agent_id:
        # Only log warning if both attributes agent_id and config agent_id are missing
        if not config_agent_id or config_agent_id == "unknown":
            logger = logging.getLogger("CylestioMonitor")
            logger.warning(f"log_event: Missing agent_id for event: {otel_name}")
        agent_id = config_agent_id or "unknown"
    
    # Extract trace context from attributes if present
    trace_id = attributes.get("trace_id")
    span_id = attributes.get("span_id")
    parent_span_id = attributes.get("parent_span_id")
    
    # Remove these from attributes if present since they'll be top-level fields
    if "trace_id" in attributes:
        del attributes["trace_id"]
    if "span_id" in attributes:
        del attributes["span_id"]
    if "parent_span_id" in attributes:
        del attributes["parent_span_id"]
    if "agent_id" in attributes:
        del attributes["agent_id"]
    
    # Add OpenTelemetry trace and span IDs if not present
    if not trace_id or not span_id:
        # Generate a new trace context or get existing one based on agent
        trace_context = get_or_create_agent_trace_context(agent_id)
        
        trace_id = trace_context["trace_id"]
        span_id = trace_context["span_id"]
        if trace_context["parent_span_id"]:
            parent_span_id = trace_context["parent_span_id"]
        
        # For sequential events from the same agent (like LLM_call_start → LLM_call_finish),
        # create child spans to maintain relationship
        if otel_name.endswith(".response") or otel_name.endswith(".end") or otel_name.endswith(".result"):
            # This is a finish event, so we keep the same span ID
            pass
        elif otel_name.endswith(".request") or otel_name.endswith(".start") or otel_name.endswith(".execution"):
            # For start events, we create a child span for subsequent events
            trace_id, span_id, parent_span_id = create_child_span(agent_id)
    
    # If channel is provided, add it to attributes
    if channel:
        attributes["channel"] = channel.upper()
    
    # If direction is provided, add it to attributes
    if direction:
        attributes["direction"] = direction
    
    # Mask sensitive data before logging
    masked_attributes = mask_sensitive_data(attributes)
    
    # Check for security concerns in the data
    alert = check_security_concerns(masked_attributes)
    
    # Adjust log level for security concerns
    if alert == "dangerous":
        level = "warning"
    
    # Add alert to attributes if it's not "none"
    if alert != "none":
        masked_attributes["security.alert"] = alert
    
    # Create a standardized event with OpenTelemetry structure
    timestamp = datetime.now()
    event = {
        "timestamp": timestamp.isoformat(),
        "level": level.upper(),
        "agent_id": agent_id,
        "name": otel_name,
        "trace_id": trace_id,
        "span_id": span_id,
        "attributes": masked_attributes
    }
    
    # Add parent_span_id if available
    if parent_span_id:
        event["parent_span_id"] = parent_span_id
    
    # Get configured log file from the config manager
    log_file = config_manager.get("monitoring.log_file")
    
    # Log to file if log_file is set
    if log_file:
        log_to_file(event, log_file)
    
    # Log to console
    if config_manager.get("monitoring.console_logging", False):
        log_console_message(f"{otel_name}: {json.dumps(masked_attributes)[:100]}...")
    
    # Call process_and_log_event to handle additional processing
    process_and_log_event(event) 