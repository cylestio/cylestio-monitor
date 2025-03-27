"""
Event Logging with OpenTelemetry-compliant structure.

This module provides an improved logging mechanism for the enhanced JSON structure,
adhering to OpenTelemetry conventions for telemetry data.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Optional, Any

from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.config import ConfigManager
from cylestio_monitor.api_client import send_event_to_api

# Configure logger
logger = logging.getLogger("CylestioMonitor")


def log_event(
    name: str, 
    attributes: Optional[Dict[str, Any]] = None, 
    level: str = "INFO", 
    span_id: Optional[str] = None, 
    trace_id: Optional[str] = None, 
    parent_span_id: Optional[str] = None
) -> Dict[str, Any]:
    """Log an event with OpenTelemetry-compliant structure.
    
    Args:
        name: Event name following OTel conventions
        attributes: Dict of attributes following OTel conventions
        level: Log level (INFO, ERROR, etc.)
        span_id: Optional span ID (uses current context if None)
        trace_id: Optional trace ID (uses current context if None)
        parent_span_id: Optional parent span ID (uses current context if None)
        
    Returns:
        Dict: The created event record
    """
    # Get current context if IDs not provided
    context = TraceContext.get_current_context()
    trace_id = trace_id or context.get("trace_id")
    span_id = span_id or context.get("span_id")
    agent_id = context.get("agent_id")
    
    # Create the event record
    timestamp = datetime.now().isoformat()
    
    event = {
        "timestamp": timestamp,
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "name": name,
        "level": level.upper(),
        "attributes": attributes or {},
    }
    
    # Add agent_id if available
    if agent_id:
        event["agent_id"] = agent_id
    
    # Write to log file
    _write_to_log_file(event)
    
    # Send to API if configured
    _send_to_api(event)
    
    return event


def _write_to_log_file(event: Dict[str, Any]) -> None:
    """Write event to log file.
    
    Args:
        event: The event to write
    """
    config_manager = ConfigManager()
    log_file = config_manager.get("monitoring.log_file")
    
    if log_file:
        try:
            logger.debug(f"Writing event to log file: {log_file}")
            logger.debug(f"Event data: {json.dumps(event)[:200]}...")
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(event) + '\n')
                
            logger.debug(f"Successfully wrote event to log file")
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")
    else:
        logger.debug("No log file configured, skipping file logging")


def _send_to_api(event: Dict[str, Any]) -> None:
    """Send event to API if configured.
    
    Args:
        event: The event to send
    """
    try:
        send_event_to_api(event)
    except Exception as e:
        logger.error(f"Failed to send event to API: {e}")


def log_error(
    name: str,
    error: Exception,
    attributes: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Log an error event with structured error information.
    
    Args:
        name: Event name (should follow the pattern "category.error")
        error: The exception that occurred
        attributes: Additional attributes to include
        
    Returns:
        Dict: The created event record
    """
    error_attributes = attributes or {}
    error_attributes.update({
        "error.type": error.__class__.__name__,
        "error.message": str(error),
    })
    
    return log_event(
        name=name,
        attributes=error_attributes,
        level="ERROR"
    ) 