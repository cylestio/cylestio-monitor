"""
Trace Context Management for AI operations telemetry.

This module provides a simple context management system to maintain trace context
across operations, following OpenTelemetry conventions.
"""

from typing import Dict, Optional, Any

from cylestio_monitor.utils.otel import generate_trace_id, generate_span_id


class TraceContext:
    """Manages trace context for AI operations telemetry."""
    
    _context = {}
    
    @classmethod
    def initialize_trace(cls, agent_id: str) -> str:
        """Initialize a new trace for an agent session.
        
        Args:
            agent_id: Unique identifier for the agent
            
        Returns:
            str: The generated trace ID
        """
        trace_id = generate_trace_id()
        cls._context = {
            "trace_id": trace_id,
            "agent_id": agent_id,
            "current_span_id": None,
            "span_stack": []
        }
        return trace_id
    
    @classmethod
    def start_span(cls, name: str) -> Dict[str, Optional[str]]:
        """Start a new span and push it onto the stack.
        
        Args:
            name: Name of the span
            
        Returns:
            Dict: Information about the span including span_id, parent_span_id, trace_id, and name
        """
        span_id = generate_span_id()
        parent_span_id = cls._context.get("current_span_id")
        
        # Push current span to stack if it exists
        if parent_span_id:
            cls._context["span_stack"].append(parent_span_id)
        
        # Set new span as current
        cls._context["current_span_id"] = span_id
        
        return {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "trace_id": cls._context["trace_id"],
            "name": name
        }
    
    @classmethod
    def end_span(cls) -> Optional[str]:
        """End the current span and pop from the stack.
        
        Returns:
            str: The span ID that was ended
        """
        current_span_id = cls._context["current_span_id"]
        
        # Pop from stack to get parent
        if cls._context["span_stack"]:
            cls._context["current_span_id"] = cls._context["span_stack"].pop()
        else:
            cls._context["current_span_id"] = None
        
        return current_span_id
    
    @classmethod
    def get_current_context(cls) -> Dict[str, Optional[str]]:
        """Get the current trace context.
        
        Returns:
            Dict: The current trace context
        """
        return {
            "trace_id": cls._context.get("trace_id"),
            "span_id": cls._context.get("current_span_id"),
            "agent_id": cls._context.get("agent_id")
        }
    
    @classmethod
    def reset(cls) -> None:
        """Reset the trace context."""
        cls._context = {} 