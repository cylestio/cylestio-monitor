"""
Anthropic event converter.

This module provides a converter for Anthropic events, transforming them
into the standardized event schema.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent

import json
import logging

logger = logging.getLogger(__name__)


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
            request = self._convert_anthropic_request(data)
        
        # For response events
        if event.get("event_type") in ["model_response", "completion_response"] or event.get("direction") == "incoming":
            response = self._convert_anthropic_response(data)
            
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

    def _convert_anthropic_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an Anthropic API request to a standardized event format.
        
        This now handles both direct client instances and auto-patched instances.
        
        Args:
            request: The raw Anthropic API request data
            
        Returns:
            A standardized request event
        """
        standardized = {
            "provider": "anthropic",
            "model": request.get("model", "unknown"),
            "input_tokens": 0,  # Will be updated by token counting later
            "input": None,
            "max_tokens": request.get("max_tokens"),
            "temperature": request.get("temperature", 1.0),
            "tools": [] if "tools" not in request else request["tools"],
            "raw_request": request  # Include the raw request for debugging
        }
        
        # Extract prompt from different possible locations
        if "messages" in request:
            messages = request["messages"]
            standardized["input"] = messages
            
            # Try to extract the last user message for simplified logging
            if isinstance(messages, list):
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        standardized["last_user_message"] = msg.get("content", "")
                        break
            
        # Include system prompt if present
        if "system" in request:
            standardized["system_prompt"] = request["system"]
        
        return standardized

    def _convert_anthropic_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an Anthropic API response to a standardized event format.
        
        Args:
            response: The raw Anthropic API response data
            
        Returns:
            A standardized response event
        """
        standardized = {
            "provider": "anthropic",
            "model": response.get("model", "unknown"),
            "output_tokens": 0,  # Will be updated by token counting later
            "output": None,
            "finish_reason": response.get("stop_reason", response.get("stop_sequence", "unknown")),
            "raw_response": response  # Include the raw response for debugging
        }
        
        # Extract response based on possible structures
        if "content" in response:
            content = response["content"]
            
            # Handle list format (newer Anthropic client)
            if isinstance(content, list):
                # Process each content item
                texts = []
                tool_calls = []
                
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            texts.append(item.get("text", ""))
                        elif item.get("type") == "tool_use":
                            tool_calls.append({
                                "name": item.get("name"),
                                "arguments": item.get("input")
                            })
                
                # Add extracted items
                if texts:
                    standardized["output"] = "\n".join(texts)
                
                if tool_calls:
                    standardized["tool_calls"] = tool_calls
                    
            # Handle simple string response
            elif isinstance(content, str):
                standardized["output"] = content
        
        # Extract token usage if available
        if "usage" in response:
            usage = response["usage"]
            if isinstance(usage, dict):
                standardized["input_tokens"] = usage.get("input_tokens", 0)
                standardized["output_tokens"] = usage.get("output_tokens", 0)
                standardized["total_tokens"] = usage.get("total_tokens", 0)
        
        return standardized 