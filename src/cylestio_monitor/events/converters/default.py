"""
Default event converter.

This module provides a default converter for events that don't have a specific converter.
It handles the basic conversion of events to the standardized schema.
"""

from datetime import datetime
from typing import Any, Dict, List

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class DefaultEventConverter(BaseEventConverter):
    """
    Default event converter for handling events without a specific converter.
    
    This converter provides a baseline implementation that other converters can build upon.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an event to the standardized schema.
        
        Args:
            event: The original event
            
        Returns:
            StandardizedEvent: The standardized event
        """
        # Extract common fields
        common_fields = self._copy_common_fields(event)
        
        # Extract the event type for special handling
        event_type = common_fields.get("event_type", "unknown")
        
        # Extract data field
        data = event.get("data", {})
        
        # Extract trace/span IDs from event data (OTel fields)
        trace_span_ids = {}
        if "trace_id" in data:
            trace_span_ids["trace_id"] = data["trace_id"]
        if "span_id" in data:
            trace_span_ids["span_id"] = data["span_id"]
        if "parent_span_id" in data:
            trace_span_ids["parent_span_id"] = data["parent_span_id"]
        
        # If no trace/span IDs found in the new format, try extract from legacy fields
        if not trace_span_ids:
            trace_span_ids = self._extract_trace_span_ids(event)
            
        # Standardize event names according to OpenTelemetry conventions
        standardized_event_type = self._standardize_event_name(event_type)
        if standardized_event_type != event_type:
            common_fields["event_type"] = standardized_event_type
        
        # Extract call stack
        call_stack = self._extract_call_stack(event)
        
        # Extract security info
        security = self._extract_security_info(event, data)
        
        # Extract performance metrics
        performance = self._extract_performance_metrics(event, data)
        
        # Extract model information
        model = self._extract_model_info(event, data)
        
        # Extract framework information
        framework = self._extract_framework_info(event, data)
        
        # Extract request information
        request = self._extract_request_info(event, data)
        
        # Extract response information
        response = self._extract_response_info(event, data)
        
        # Move caller information to attributes
        extra = data.copy()
        
        # Create the standardized event
        standardized_event = StandardizedEvent(
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
        
        # Log final event creation for LLM call events
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            import logging
            logger = logging.getLogger("CylestioMonitor")
            logger.debug(f"DefaultConverter: Created standardized event for {event_type}")
            
        return standardized_event
    
    def _standardize_event_name(self, event_type: str) -> str:
        """
        Standardize event names according to OpenTelemetry conventions.
        
        Args:
            event_type: The original event type
            
        Returns:
            str: The standardized event name
        """
        # OpenTelemetry AI-specific event types
        otel_event_map = {
            # LLM events
            "LLM_call_start": "llm.request",
            "LLM_call_finish": "llm.response",
            "llm_request": "llm.request",
            "llm_response": "llm.response",
            "completion_request": "llm.completion.request",
            "completion_response": "llm.completion.response",
            "chat_request": "llm.chat.request",
            "chat_response": "llm.chat.response",
            
            # Tool events
            "tool_call": "tool.call",
            "tool_result": "tool.result",
            
            # Agent events
            "agent_start": "agent.start",
            "agent_finish": "agent.finish",
            
            # Session events
            "session_start": "session.start",
            "session_end": "session.end",
            
            # User interaction
            "user_message": "user.message",
            "user_feedback": "user.feedback",
            "assistant_message": "assistant.message"
        }
        
        # Return mapped name or original if no mapping exists
        return otel_event_map.get(event_type, event_type)
    
    def _extract_security_info(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract security information from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Security information
        """
        security = {}
        
        # Extract security alert if present
        if "alert" in data:
            security["alert"] = data["alert"]
            
        # Extract other security-related fields
        for key in ["security_level", "blocked", "allowed", "flagged"]:
            if key in data:
                security[key] = data[key]
                
        return security
    
    def _extract_performance_metrics(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance metrics from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Performance metrics
        """
        performance = {}
        
        # Extract common performance metrics
        perf_keys = ["processing_time", "latency", "tokens", "input_tokens", "output_tokens", "total_tokens"]
        for key in perf_keys:
            if key in data:
                # Use OTel semantic conventions for token metrics
                if key == "input_tokens":
                    performance["llm.usage.prompt_tokens"] = data[key]
                elif key == "output_tokens":
                    performance["llm.usage.completion_tokens"] = data[key]
                elif key == "total_tokens":
                    performance["llm.usage.total_tokens"] = data[key]
                else:
                    performance[key] = data[key]
                
        # Extract nested token usage
        if "usage" in data and isinstance(data["usage"], dict):
            for key, value in data["usage"].items():
                if key in ["prompt_tokens", "completion_tokens", "total_tokens"]:
                    performance[f"llm.usage.{key}"] = value
        
        return performance
    
    def _extract_model_info(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract model information from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Model information
        """
        model = {}
        
        # Extract model name
        model_name_keys = ["model", "model_name", "model_id"]
        for key in model_name_keys:
            if key in data:
                model["llm.model"] = data[key]
                break
                
        # Extract other model parameters
        param_keys = ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]
        for key in param_keys:
            if key in data:
                model[f"llm.{key}"] = data[key]
                
        return model
    
    def _extract_framework_info(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract framework information from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Framework information
        """
        framework = {}
        
        # Extract channel as framework
        channel = event.get("channel", "").upper()
        if channel and channel != "SYSTEM":
            framework["name"] = channel.lower()
            
        # Extract version if available
        if "framework_version" in data:
            framework["version"] = data["framework_version"]
            
        return framework
    
    def _extract_request_info(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract request information from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Request information
        """
        request = {}
        
        # Extract prompt or messages
        if "prompt" in data:
            request["prompt"] = data["prompt"]
            
        if "messages" in data and isinstance(data["messages"], list):
            request["messages"] = data["messages"]
            
        # For events that are clearly requests
        event_type = event.get("event_type", "").lower()
        if event_type.endswith("_request") or event_type == "llm_call_start":
            # Extract request parameters
            for key, value in data.items():
                if key not in ["prompt", "messages", "response", "result"]:
                    request[key] = value
                    
        # Extract caller if available
        if "caller" in data and isinstance(data["caller"], dict):
            for key, value in data["caller"].items():
                request[f"caller.{key}"] = value
                
        return request
    
    def _extract_response_info(self, event: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract response information from the event.
        
        Args:
            event: The original event
            data: The data field from the event
            
        Returns:
            Dict[str, Any]: Response information
        """
        response = {}
        
        # Extract completion or response
        if "response" in data:
            response["completion"] = data["response"]
            
        if "completion" in data:
            response["completion"] = data["completion"]
            
        if "result" in data:
            response["result"] = data["result"]
            
        # For events that are clearly responses
        event_type = event.get("event_type", "").lower()
        if event_type.endswith("_response") or event_type.endswith("_result") or event_type == "llm_call_finish":
            # Extract response metadata
            for key, value in data.items():
                if key not in ["prompt", "messages", "response", "completion", "result"]:
                    response[key] = value
                    
        return response 