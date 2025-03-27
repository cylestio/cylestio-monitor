"""
OpenTelemetry utilities for generating trace and span IDs.

This module provides utility functions for generating OpenTelemetry-compliant
trace and span IDs for use in telemetry events.
"""

import random
import uuid
from typing import Dict, Optional, Tuple


def generate_trace_id() -> str:
    """
    Generate an OpenTelemetry-compliant trace ID.

    A trace ID is a 16-byte array (32 hex characters) that is used to uniquely identify
    a trace across different systems.

    Returns:
        A 32-character hex string representing a valid trace ID.
    """
    # Generate a random 16-byte array (as hexadecimal string)
    return uuid.uuid4().hex


def generate_span_id() -> str:
    """
    Generate an OpenTelemetry-compliant span ID.

    A span ID is an 8-byte array (16 hex characters) that is used to uniquely identify
    a span within a trace.

    Returns:
        A 16-character hex string representing a valid span ID.
    """
    # Generate a random 8-byte array (as hexadecimal string)
    return ''.join(f'{random.randint(0, 255):02x}' for _ in range(8))


def generate_trace_context(parent_span_id: Optional[str] = None) -> Dict[str, str]:
    """
    Generate a complete trace context with trace_id, span_id, and optional parent_span_id.

    Args:
        parent_span_id: Optional parent span ID. If provided, the created span will be a child of this span.

    Returns:
        A dictionary containing trace_id, span_id, and optional parent_span_id.
    """
    return {
        "trace_id": generate_trace_id(),
        "span_id": generate_span_id(),
        "parent_span_id": parent_span_id
    }


# Track trace and span relationships per agent
_agent_trace_contexts = {}  # type: Dict[str, Dict[str, str]]


def get_or_create_agent_trace_context(agent_id: str) -> Dict[str, str]:
    """
    Get or create a trace context for an agent.

    This function ensures that operations within the same agent's lifecycle share the same trace ID
    but have unique span IDs.

    Args:
        agent_id: The agent identifier

    Returns:
        A dictionary containing trace_id, span_id, and optional parent_span_id.
    """
    global _agent_trace_contexts
    
    if agent_id not in _agent_trace_contexts:
        # Create a new trace context for this agent
        _agent_trace_contexts[agent_id] = {
            "trace_id": generate_trace_id(),
            "current_span_id": generate_span_id(),
            "parent_span_id": None
        }
    
    return {
        "trace_id": _agent_trace_contexts[agent_id]["trace_id"],
        "span_id": _agent_trace_contexts[agent_id]["current_span_id"],
        "parent_span_id": _agent_trace_contexts[agent_id]["parent_span_id"]
    }


def create_child_span(agent_id: str) -> Tuple[str, str, str]:
    """
    Create a child span for the current trace.

    This function creates a new span ID under the current trace, setting the previous span
    as the parent.

    Args:
        agent_id: The agent identifier

    Returns:
        A tuple of (trace_id, span_id, parent_span_id)
    """
    global _agent_trace_contexts
    
    if agent_id not in _agent_trace_contexts:
        # Initialize trace context if it doesn't exist
        context = get_or_create_agent_trace_context(agent_id)
        # For the first call, the parent_span_id should be None
        _agent_trace_contexts[agent_id]["parent_span_id"] = None
        return context["trace_id"], context["span_id"], None
    
    # Get existing trace context
    trace_context = _agent_trace_contexts[agent_id]
    trace_id = trace_context["trace_id"]
    parent_span_id = trace_context["current_span_id"]
    
    # Generate new span ID
    new_span_id = generate_span_id()
    
    # Update context
    _agent_trace_contexts[agent_id]["current_span_id"] = new_span_id
    _agent_trace_contexts[agent_id]["parent_span_id"] = parent_span_id
    
    return trace_id, new_span_id, parent_span_id 