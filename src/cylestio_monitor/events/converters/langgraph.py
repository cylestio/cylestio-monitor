"""
LangGraph event converter.

This module provides a converter for LangGraph events, transforming them
into the standardized event schema.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class LangGraphEventConverter(BaseEventConverter):
    """
    Converter for LangGraph events.
    
    This class handles the conversion of LangGraph-specific events to the
    standardized event schema, ensuring proper extraction and mapping of fields.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert a LangGraph event to the standardized schema.
        
        Args:
            event: The original LangGraph event
            
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
        if not framework and "framework" in data and isinstance(data["framework"], str):
            framework = {
                "name": data["framework"],
                "version": data.get("version", "unknown")
            }
        
        # Extract model info (LangGraph typically doesn't include model info)
        model = self._extract_model_info(event)
        
        # Extract request or response data based on event type
        request = None
        response = None
        
        # For framework patch events
        if event.get("event_type") == "framework_patch":
            request = {
                "method": data.get("method"),
                "patch_time": data.get("patch_time"),
                "version": data.get("version"),
                "note": data.get("note")
            }
        
        # For graph execution events
        if event.get("event_type") in ["graph_start", "graph_end", "node_start", "node_end"]:
            graph_info = {}
            
            # Extract graph-specific fields
            for key in ["graph_id", "node_id", "node_type", "input", "output"]:
                if key in data:
                    graph_info[key] = data[key]
            
            if event.get("event_type") in ["graph_start", "node_start"]:
                request = graph_info
            else:
                response = graph_info
                
        # Store any unmapped fields in extra
        processed_keys = {
            "framework", "model", "call_stack", "security", 
            "performance", "method", "patch_time", "version", 
            "note", "agent_id", "run_id", "graph_id", "node_id",
            "node_type", "input", "output"
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