"""
MCP event converter.

This module provides a converter for MCP (Monitoring Control Plane) events,
transforming them into the standardized event schema.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class MCPEventConverter(BaseEventConverter):
    """
    Converter for MCP events.
    
    This class handles the conversion of MCP-specific events to the
    standardized event schema, ensuring proper extraction and mapping of fields.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an MCP event to the standardized schema.
        
        Args:
            event: The original MCP event
            
        Returns:
            StandardizedEvent: A standardized event instance
        """
        # Start with common fields
        common_fields = self._copy_common_fields(event)
        
        # Extract data field
        data = event.get("data", {})
        
        # Extract trace/span IDs
        trace_span_ids = self._extract_trace_span_ids(event)
        
        # Extract call stack
        call_stack = self._extract_call_stack(event)
        
        # Extract security info
        security = self._extract_security_info(event)
        
        # Extract performance metrics
        performance = self._extract_performance_metrics(event)
        
        # Extract framework info
        framework = self._extract_framework_info(event)
        if not framework:
            framework = {
                "name": "system",
                "version": None
            }
        
        # Extract model info
        model = self._extract_model_info(event)
        
        # Extract request or response data based on event type
        request = None
        response = None
        
        # For MCP_patch events
        if event.get("event_type") == "MCP_patch":
            request = {
                "message": data.get("message")
            }
        
        # For monitoring_enabled events
        if event.get("event_type") == "monitoring_enabled":
            request = {
                "agent_id": data.get("agent_id"),
                "LLM_provider": data.get("LLM_provider")
            }
            
        # For user interaction events
        if event.get("event_type") in ["user_message", "user_input", "user_request"]:
            request = {
                "content": data.get("content", ""),
                "metadata": data.get("metadata", {})
            }
            
        # Store any unmapped fields in extra
        processed_keys = {
            "framework", "call_stack", "security", "performance", 
            "message", "agent_id", "LLM_provider",
            "content", "metadata"
        }
                          
        extra = {k: v for k, v in data.items() if k not in processed_keys}
        
        # Create the standardized event
        return StandardizedEvent(
            timestamp=common_fields["timestamp"],
            level=common_fields["level"],
            agent_id=common_fields["agent_id"],
            event_type=common_fields["event_type"],
            channel=common_fields["channel"],
            direction=common_fields.get("direction"),
            session_id=common_fields.get("session_id"),
            trace_id=trace_span_ids.get("trace_id"),
            span_id=trace_span_ids.get("span_id"),
            parent_span_id=trace_span_ids.get("parent_span_id"),
            call_stack=call_stack,
            security=security,
            performance=performance,
            model=model,
            framework=framework,
            request=request,
            response=response,
            extra=extra
        ) 