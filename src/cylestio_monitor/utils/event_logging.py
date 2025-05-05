"""
Event Logging with OpenTelemetry-compliant structure.

This module provides an improved logging mechanism for the enhanced JSON structure,
adhering to OpenTelemetry conventions for telemetry data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.utils.context_attributes import (get_all_context,
                                                       get_environment_context,
                                                       get_library_versions)
from cylestio_monitor.utils.event_context import (enrich_event_with_context,
                                                  get_session_id)
from cylestio_monitor.utils.event_utils import format_timestamp
from cylestio_monitor.utils.schema import (get_current_schema_version,
                                           validate_event_schema)
from cylestio_monitor.utils.serialization import safe_event_serialize
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.security_detection import SecurityScanner

# Configure logger
logger = logging.getLogger("CylestioMonitor")


def log_event(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    level: str = "INFO",
    span_id: Optional[str] = None,
    trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None,
    include_context: bool = True,
    context_type: str = "minimal",
    add_thread_context: bool = True,
    channel: Optional[str] = None,
    event_category: Optional[str] = None,
    performance: Optional[Dict[str, Any]] = None,
    model: Optional[Dict[str, Any]] = None,
    security: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Log an event with OpenTelemetry-compliant structure.

    Args:
        name: Event name following OTel conventions
        attributes: Dict of attributes following OTel conventions
        level: Log level (INFO, ERROR, etc.)
        span_id: Optional span ID (uses current context if None)
        trace_id: Optional trace ID (uses current context if None)
        parent_span_id: Optional parent span ID (uses current context if None)
        include_context: Whether to include environmental context attributes
        context_type: Type of context to include ("minimal", "standard", or "full")
        add_thread_context: Whether to add thread-local context from event_context
        channel: Optional channel identifier for event converters (e.g., "OPENAI", "ANTHROPIC")
        event_category: Optional category for the event
        performance: Optional performance metrics
        model: Optional model information
        security: Optional security information

    Returns:
        Dict: The created event record
    """
    # Get current context if IDs not provided
    context = TraceContext.get_current_context()
    trace_id = trace_id or context.get("trace_id")
    span_id = span_id or context.get("span_id")
    agent_id = context.get("agent_id")
    
    # Ensure we have default values for agent_id and trace_id
    # This ensures early patch events still have identifiable values
    if trace_id is None:
        trace_id = "null-trace"
    if agent_id is None:
        agent_id = "unknown-agent"

    # Get parent_span_id from context if not provided
    if parent_span_id is None and span_id is not None:
        parent_span_id = context.get(
            "parent_span_id"
        ) or TraceContext.get_parent_span_id(span_id)

    # Create the event record with UTC timestamp and Z suffix
    timestamp = format_timestamp()

    # Safely serialize the attributes first
    safe_attributes = safe_event_serialize(attributes or {})

    event = {
        "schema_version": get_current_schema_version(),  # Add schema version
        "timestamp": timestamp,
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "name": name,
        "level": level.upper(),
        "attributes": safe_attributes,
        "agent_id": agent_id,  # Always include agent_id now
    }

    # Add channel if provided
    if channel:
        event["channel"] = channel
        
    # Add event category if provided
    if event_category:
        event["event_category"] = event_category
        
    # Add performance metrics if provided
    if performance and performance:
        event["performance"] = safe_event_serialize(performance)
        
    # Add model information if provided
    if model and model:
        event["model"] = safe_event_serialize(model)
        
    # Add security information if provided
    if security and security:
        event["security"] = safe_event_serialize(security)

    # Add session_id to attributes
    event["attributes"]["session.id"] = get_session_id()

    # Add environmental context attributes if enabled
    if include_context:
        env_attributes = {}

        # Add context based on the specified level
        if name == "monitoring.start" or context_type == "full":
            # Full context for monitoring.start events or if explicitly requested
            env_attributes.update({f"env.{k}": v for k, v in get_all_context().items()})
        elif context_type == "standard":
            # Standard context includes environment and library versions
            env_attributes.update(
                {f"env.{k}": v for k, v in get_environment_context().items()}
            )
            env_attributes.update(
                {f"env.{k}": v for k, v in get_library_versions().items()}
            )
        elif context_type == "minimal":
            # Minimal context includes only essential environment info
            env_attributes.update(
                {f"env.{k}": v for k, v in get_environment_context().items()}
            )

        # Add context attributes to the event
        event["attributes"].update(env_attributes)

    # Add thread-local context if enabled
    if add_thread_context:
        event = enrich_event_with_context(event)

    # Validate the event schema before writing/sending
    if not validate_event_schema(event):
        logger.warning(f"Event failed schema validation: {name}")

    # Mask sensitive data in the event before logging/sending
    scanner = SecurityScanner.get_instance()
    masked_event = scanner.mask_event(event)
    
    # If masking didn't occur, use the original event
    if masked_event is None:
        masked_event = event

    # Write to log file
    _write_to_log_file(masked_event)

    # Send to API if configured
    _send_to_api(masked_event)
    
    # Return the original unmasked event to the caller
    # This ensures internal processing isn't affected
    return event


def _write_to_log_file(event: Dict[str, Any]) -> None:
    """Write event to log file.

    Args:
        event: The event to write
    """
    config_manager = ConfigManager()
    # Check for new parameter name first, fall back to old one for backward compatibility
    events_file = config_manager.get("monitoring.events_output_file")
    if events_file is None:
        events_file = config_manager.get("monitoring.log_file")

    if events_file:
        try:
            logger.debug(f"Writing event to file: {events_file}")
            logger.debug(f"Event data: {json.dumps(event)[:200]}...")

            with open(events_file, "a") as f:
                f.write(json.dumps(event) + "\n")

            logger.debug("Successfully wrote event to file")
        except Exception as e:
            logger.error(f"Failed to write to event file: {e}")
    else:
        logger.debug("No events output file configured, skipping file logging")


def _send_to_api(event: Dict[str, Any]) -> None:
    """Send event to API if configured.

    Args:
        event: The event to send
    """
    try:
        # Import here to avoid circular import
        from cylestio_monitor.api_client import send_event_to_api

        send_event_to_api(event)
    except Exception as e:
        logger.error(f"Failed to send event to API: {e}")


def log_error(
    name: str, 
    error: Exception, 
    attributes: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Log an error event with structured error information.

    Args:
        name: Event name (should follow the pattern "category.error")
        error: The exception that occurred
        attributes: Additional attributes to include
        trace_id: Optional trace ID (uses current context if None)
        agent_id: Optional agent ID (uses current context if None)
        **kwargs: Additional parameters to pass to log_event

    Returns:
        Dict: The created event record
    """
    error_attributes = attributes or {}
    error_attributes.update(
        {
            "error.type": error.__class__.__name__,
            "error.message": str(error),
        }
    )

    # Pass agent_id only if it's in the log_event signature
    try:
        from inspect import signature
        sig = signature(log_event)
        log_kwargs = kwargs.copy()
        
        if 'agent_id' in sig.parameters:
            log_kwargs['agent_id'] = agent_id
            
        return log_event(
            name=name, 
            attributes=error_attributes, 
            level="ERROR", 
            trace_id=trace_id,
            **log_kwargs
        )
    except Exception as e:
        # Fallback to simpler call if there's any issue with signature inspection
        logger.debug(f"Using fallback log_event call: {e}")
        return log_event(
            name=name, 
            attributes=error_attributes, 
            level="ERROR", 
            trace_id=trace_id
        )


def log_info(
    name: str, attributes: Optional[Dict[str, Any]] = None, **kwargs
) -> Dict[str, Any]:
    """Log an info-level event.

    Args:
        name: Event name following OTel conventions
        attributes: Dict of attributes following OTel conventions
        **kwargs: Additional parameters to pass to log_event

    Returns:
        Dict: The created event record
    """
    return log_event(name=name, attributes=attributes, level="INFO", **kwargs)


def log_warning(
    name: str, attributes: Optional[Dict[str, Any]] = None, **kwargs
) -> Dict[str, Any]:
    """Log a warning-level event.

    Args:
        name: Event name following OTel conventions
        attributes: Dict of attributes following OTel conventions
        **kwargs: Additional parameters to pass to log_event

    Returns:
        Dict: The created event record
    """
    return log_event(name=name, attributes=attributes, level="WARNING", **kwargs)
