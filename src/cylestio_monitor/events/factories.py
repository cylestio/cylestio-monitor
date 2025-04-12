"""
Event factories for Cylestio Monitor.

This module provides factory functions for creating different types of events
with consistent formatting and UTC timestamps.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from cylestio_monitor.utils.event_utils import create_event_dict, format_timestamp


# LLM Events
def create_llm_request_event(
    agent_id: str,
    provider: str,
    model: str,
    prompt: str,
    timestamp: Optional[Union[datetime, str]] = None,
    request_timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an LLM request event.
    
    Args:
        agent_id: Agent identifier
        provider: LLM provider (e.g., OpenAI, Anthropic)
        model: Model identifier (e.g., gpt-4, claude-2)
        prompt: Prompt sent to the LLM
        timestamp: Event timestamp (default: current UTC time)
        request_timestamp: When the request was sent (default: same as timestamp)
        trace_id: Trace identifier
        attributes: Additional attributes
        
    Returns:
        Dict: Standardized event dictionary
    """
    # Create base attributes
    attrs = attributes or {}
    
    # Add LLM-specific attributes
    attrs["llm.provider"] = provider
    attrs["llm.model"] = model
    attrs["llm.request.prompt"] = prompt
    
    # Ensure request_timestamp is properly formatted
    if request_timestamp is not None:
        attrs["llm.request.request_timestamp"] = format_timestamp(request_timestamp)
    else:
        attrs["llm.request.timestamp"] = format_timestamp(timestamp)
    
    # Create the event
    event = create_event_dict(
        name="llm.request",
        attributes=attrs,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
    )
    
    return event


def create_llm_response_event(
    agent_id: str,
    provider: str,
    model: str,
    response: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized LLM response event.
    
    Args:
        agent_id: Agent identifier
        provider: LLM provider (e.g., 'openai', 'anthropic')
        model: Model identifier
        response: LLM response
        prompt: Optional original prompt
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: LLM response event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "llm.vendor": provider,
        "llm.model": model,
        "llm.response.content": response,
        "llm.response.timestamp": format_timestamp(timestamp),
    }
    
    # Add prompt if provided
    if prompt is not None:
        attributes["llm.request.prompt"] = prompt
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"llm.response.{key}"] = value
    
    return create_event_dict(
        name="llm.response",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


# Tool Events
def create_tool_call_event(
    agent_id: str,
    tool_name: str,
    inputs: Dict[str, Any],
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized tool call event.
    
    Args:
        agent_id: Agent identifier
        tool_name: Name of the tool being called
        inputs: Tool input parameters
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Tool call event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "tool.name": tool_name,
        "tool.call.inputs": inputs,
        "tool.call.timestamp": format_timestamp(timestamp),
    }
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"tool.{key}"] = value
    
    return create_event_dict(
        name="tool.call",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


def create_tool_result_event(
    agent_id: str,
    tool_name: str,
    inputs: Dict[str, Any],
    output: Any,
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized tool result event.
    
    Args:
        agent_id: Agent identifier
        tool_name: Name of the tool that was called
        inputs: Tool input parameters
        output: Tool execution result
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Tool result event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "tool.name": tool_name,
        "tool.call.inputs": inputs,
        "tool.result.output": output,
        "tool.result.timestamp": format_timestamp(timestamp),
    }
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"tool.{key}"] = value
    
    return create_event_dict(
        name="tool.result",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


# System Events
def create_system_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    level: str = "INFO",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized system event.
    
    Args:
        agent_id: Agent identifier
        event_type: Type of system event
        data: Event data
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        level: Log level
        **kwargs: Additional attributes
        
    Returns:
        Dict: System event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "system.type": event_type,
        **data
    }
    
    # Add timestamp attribute
    attributes["system.timestamp"] = format_timestamp(timestamp)
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"system.{key}"] = value
    
    return create_event_dict(
        name=f"system.{event_type}",
        attributes=attributes,
        level=level,
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )

# Continue with the rest of the factory functions in the file...

# Additional factory methods for common event types

def create_agent_startup_event(
    agent_id: str,
    version: str,
    configuration: Dict[str, Any],
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized agent startup event.
    
    Args:
        agent_id: Agent identifier
        version: Agent version
        configuration: Agent configuration
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Agent startup event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "agent.version": version,
        "agent.configuration": configuration,
        "agent.startup.timestamp": format_timestamp(timestamp),
    }
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"agent.{key}"] = value
    
    return create_event_dict(
        name="agent.startup",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


def create_agent_shutdown_event(
    agent_id: str,
    reason: str,
    metrics: Optional[Dict[str, Any]] = None,
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized agent shutdown event.
    
    Args:
        agent_id: Agent identifier
        reason: Shutdown reason
        metrics: Optional runtime metrics
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Agent shutdown event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "agent.shutdown.reason": reason,
        "agent.shutdown.timestamp": format_timestamp(timestamp),
    }
    
    # Add metrics if provided
    if metrics is not None:
        attributes["agent.metrics"] = metrics
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"agent.{key}"] = value
    
    return create_event_dict(
        name="agent.shutdown",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


def create_error_event(
    agent_id: str,
    error_type: str,
    message: str,
    stack_trace: Optional[str] = None,
    timestamp: Optional[Union[datetime, str]] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized error event.
    
    Args:
        agent_id: Agent identifier
        error_type: Type of error
        message: Error message
        stack_trace: Optional stack trace
        timestamp: Optional timestamp (datetime or ISO8601 string, default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Error event with UTC timestamp and Z suffix
    """
    # Create base attributes
    attributes = {
        "error.type": error_type,
        "error.message": message,
        "error.timestamp": format_timestamp(timestamp),
    }
    
    # Add stack trace if provided
    if stack_trace is not None:
        attributes["error.stack_trace"] = stack_trace
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"error.{key}"] = value
    
    return create_event_dict(
        name="error",
        attributes=attributes,
        level="ERROR",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    ) 