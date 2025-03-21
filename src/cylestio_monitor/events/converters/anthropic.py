"""
Anthropic event converter.

This module provides a converter for Anthropic events, transforming them
into the standardized event schema.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class AnthropicEventConverter(BaseEventConverter):
    """
    Converter for Anthropic events.
    
    This class handles the conversion of Anthropic-specific events to the
    standardized event schema, ensuring proper extraction and mapping of fields.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an Anthropic event to the standardized schema.
        
        Args:
            event: The original Anthropic event
            
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
                "name": "anthropic",
                "version": data.get("version")
            }
        
        # Extract model info
        model = self._extract_model_info(event)
        if not model and "model" in data:
            model_name = data["model"] if isinstance(data["model"], str) else data.get("model", {}).get("name")
            model = {
                "name": model_name,
                "type": "completion",
                "provider": "anthropic"
            }
        
        # Extract request or response data based on event type
        request = None
        response = None
        
        # For request events
        if event.get("event_type") in ["model_request", "completion_request"] or event.get("direction") == "outgoing":
            request = {}
            
            # Extract messages or prompt
            if "messages" in data:
                request["messages"] = data["messages"]
            elif "prompt" in data:
                request["prompt"] = data["prompt"]
                
            # Add other request parameters
            for key in ["model", "max_tokens", "temperature", "top_p", "stop_sequences"]:
                if key in data:
                    request[key] = data[key]
        
        # For response events
        if event.get("event_type") in ["model_response", "completion_response"] or event.get("direction") == "incoming":
            response = {}
            
            # Extract completion or content
            if "completion" in data:
                response["completion"] = data["completion"]
            elif "content" in data:
                response["content"] = data["content"]
                
            # Add response metadata
            for key in ["stop_reason", "model", "usage"]:
                if key in data:
                    response[key] = data[key]
                    
            # Extract any detailed usage info
            if "usage" in data:
                usage = data["usage"]
                if isinstance(usage, dict):
                    if not performance:
                        performance = {}
                        
                    # Copy usage metrics to performance
                    for usage_key, usage_value in usage.items():
                        performance[f"usage_{usage_key}"] = usage_value
            
        # Store any unmapped fields in extra
        processed_keys = {
            "framework", "model", "call_stack", "security", 
            "performance", "messages", "prompt", "max_tokens",
            "temperature", "top_p", "stop_sequences", "completion",
            "content", "stop_reason", "usage", "version"
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