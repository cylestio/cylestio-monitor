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
    prompt: Union[str, List[Dict[str, str]]],
    timestamp: Optional[datetime] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a standardized LLM request event.
    
    Args:
        agent_id: Agent identifier
        provider: LLM provider (e.g., 'openai', 'anthropic')
        model: Model identifier
        prompt: Prompt text or messages
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: LLM request event
    """
    # Create base attributes
    attributes = {
        "llm.vendor": provider,
        "llm.model": model,
        "llm.request.type": "completion",
        "llm.request.prompt": prompt,
        "llm.request.timestamp": format_timestamp(timestamp),
    }
    
    # Add additional attributes
    for key, value in kwargs.items():
        if key not in ("parent_span_id"):
            attributes[f"llm.request.{key}"] = value
    
    return create_event_dict(
        name="llm.request",
        attributes=attributes,
        level="INFO",
        agent_id=agent_id,
        timestamp=timestamp,
        trace_id=trace_id,
        span_id=span_id
    )


def create_llm_response_event(
    agent_id: str,
    provider: str,
    model: str,
    response: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
    timestamp: Optional[datetime] = None,
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
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: LLM response event
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
    timestamp: Optional[datetime] = None,
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
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Tool call event
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
    timestamp: Optional[datetime] = None,
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
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        **kwargs: Additional attributes
        
    Returns:
        Dict: Tool result event
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
    timestamp: Optional[datetime] = None,
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
        timestamp: Optional timestamp (default: current UTC time)
        trace_id: Optional trace ID
        span_id: Optional span ID
        level: Log level
        **kwargs: Additional attributes
        
    Returns:
        Dict: System event
    """
    # Create base attributes
    attributes = {
        "system.type": event_type,
        **data
    }
    
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