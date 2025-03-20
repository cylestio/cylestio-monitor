"""
LangChain event converter.

This module provides a converter for LangChain events, transforming them
into the standardized event schema.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class LangChainEventConverter(BaseEventConverter):
    """
    Converter for LangChain events.
    
    This class handles the conversion of LangChain-specific events to the
    standardized event schema, ensuring proper extraction and mapping of fields.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert a LangChain event to the standardized schema.
        
        Args:
            event: The original LangChain event
            
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
        if not framework and "framework_version" in data:
            framework = {
                "name": "langchain",
                "version": data.get("framework_version")
            }
        
        # Extract model info
        model = self._extract_model_info(event)
        if not model and "llm_type" in data:
            model = {
                "name": data.get("llm_type"),
                "type": "unknown",
                "provider": data.get("model", {}).get("provider") if isinstance(data.get("model"), dict) else None
            }
        
        # Extract request or response data based on event type
        request = None
        response = None
        
        # For request events
        if event.get("event_type") == "model_request" or event.get("direction") == "outgoing":
            request = {
                "prompts": data.get("prompts", []),
                "metadata": data.get("metadata", {}),
                "components": data.get("components", {})
            }
        
        # For response events
        if event.get("event_type") == "model_response" or event.get("direction") == "incoming":
            response = {
                "content": data.get("response", {}),
                "llm_output": data.get("llm_output", {})
            }
            
            # Extract performance metrics specific to response
            if "performance" in data and "duration_ms" in data["performance"]:
                if not performance:
                    performance = {}
                performance["duration_ms"] = data["performance"]["duration_ms"]
        
        # Store any unmapped fields in extra
        processed_keys = {
            "framework", "model", "call_stack", "security", 
            "performance", "prompts", "metadata", "response", 
            "llm_output", "run_id", "framework_version", 
            "components", "session_id", "agent_id", "llm_type"
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