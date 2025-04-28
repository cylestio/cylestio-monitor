"""
OpenAI event converter implementation.

This module contains the OpenAIEventConverter class which handles OpenAI-specific events.
"""

import logging
from typing import Any, Dict, List

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class OpenAIEventConverter(BaseEventConverter):
    """
    Event converter for OpenAI-specific events.

    This converter handles events from OpenAI models, ensuring token usage metrics
    are properly captured and standardized.
    """

    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an OpenAI API event to a standardized event.

        Args:
            event: The raw OpenAI API event

        Returns:
            StandardizedEvent: The standardized event
        """
        # Extract common fields
        common_fields = self._copy_common_fields(event)
        
        # Extract data for processing
        data = event.get("data", {})
        
        # Initialize attribute containers
        attributes = {}
        model = {}
        performance = {}
        security = {}
        
        # Determine provider and model
        provider = "openai"
        model_name = data.get("model", "unknown")
        
        # Default event category
        event_category = "llm"
        
        # Process based on event type or direction
        if (
            event.get("event_type") in ["model_request", "completion_request", "llm.call.start"]
            or event.get("direction") == "outgoing"
        ):
            request = self._convert_openai_request(data)
            attributes.update(request)
            
            # Extract model parameters if available
            if model_name != "unknown":
                model["llm.model"] = model_name
                
            # Add temperature if available
            temperature = data.get("temperature")
            if temperature is not None:
                model["llm.temperature"] = temperature
                
            # Add max_tokens if available
            max_tokens = data.get("max_tokens")
            if max_tokens is not None:
                model["llm.request.max_tokens"] = max_tokens
                attributes["llm.request.max_tokens"] = max_tokens
                
        elif (
            event.get("event_type") in ["model_response", "completion_response", "llm.call.finish", "llm.response"]
            or event.get("direction") == "incoming"
        ):
            response = self._convert_openai_response(data)
            attributes.update(response)
            
            # Extract model info
            if model_name != "unknown":
                model["llm.model"] = model_name
                
            # Extract performance metrics - specifically token usage
            if "usage" in data:
                usage = data["usage"]
                if "prompt_tokens" in usage:
                    performance["llm.usage.input_tokens"] = usage["prompt_tokens"]
                    attributes["llm.usage.input_tokens"] = usage["prompt_tokens"]
                if "completion_tokens" in usage:
                    performance["llm.usage.output_tokens"] = usage["completion_tokens"]
                    attributes["llm.usage.output_tokens"] = usage["completion_tokens"]
                if "total_tokens" in usage:
                    performance["llm.usage.total_tokens"] = usage["total_tokens"]
                    attributes["llm.usage.total_tokens"] = usage["total_tokens"]
            
            # Check for usage data in attributes field
            for key in ["llm.usage.input_tokens", "llm.usage.output_tokens", "llm.usage.total_tokens"]:
                # First try in nested attributes if available
                if "attributes" in data and isinstance(data["attributes"], dict) and key in data["attributes"]:
                    performance[key] = data["attributes"][key]
                # Then try in top-level data
                elif key in data:
                    performance[key] = data[key]
                
        # If this is a raw event coming directly from the OpenAI patcher
        # It might have response_attributes with llm.usage keys in a different structure
        if "attributes" in event and isinstance(event["attributes"], dict):
            patcher_attrs = event["attributes"]
            for key in ["llm.usage.input_tokens", "llm.usage.output_tokens", "llm.usage.total_tokens"]:
                if key in patcher_attrs:
                    performance[key] = patcher_attrs[key]
                    attributes[key] = patcher_attrs[key]

        # Add vendor information to attributes
        attributes["llm.vendor"] = provider
        
        # Create standardized event
        return StandardizedEvent(
            timestamp=common_fields.get("timestamp"),
            level=common_fields.get("level", "INFO"),
            agent_id=common_fields.get("agent_id"),
            name=common_fields.get("event_type", "llm.response"),
            event_category=event_category,
            attributes=attributes,
            performance=performance,
            model=model,
            security=security,
            trace_id=event.get("trace_id"),
            span_id=event.get("span_id"),
            parent_span_id=event.get("parent_span_id"),
        )

    def _convert_openai_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an OpenAI API request to a standardized format.

        Args:
            request: The raw OpenAI API request data

        Returns:
            A standardized request event
        """
        standardized = {
            "provider": "openai",
            "model": request.get("model", "unknown"),
            "input_tokens": 0,  # Will be updated by token counting later
            "input": None,
            "max_tokens": request.get("max_tokens"),
            "temperature": request.get("temperature", 1.0),
            "raw_request": request,  # Include the raw request for debugging
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

        # For completions API
        if "prompt" in request:
            standardized["input"] = request["prompt"]
            standardized["last_user_message"] = (
                request["prompt"] if isinstance(request["prompt"], str) 
                else str(request["prompt"])
            )

        # Include system prompt if present
        if "system" in request:
            standardized["system_prompt"] = request["system"]

        return standardized

    def _convert_openai_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert an OpenAI API response to a standardized format.

        Args:
            response: The raw OpenAI API response data

        Returns:
            A standardized response event
        """
        standardized = {
            "provider": "openai",
            "model": response.get("model", "unknown"),
            "output_tokens": 0,  # Will be updated by token counting later
            "output": None,
            "raw_response": response,  # Include the raw response for debugging
        }

        # Extract response based on possible structures
        if "choices" in response and response["choices"]:
            first_choice = response["choices"][0]
            
            # Chat completions format
            if "message" in first_choice:
                message = first_choice["message"]
                if isinstance(message, dict) and "content" in message:
                    standardized["output"] = message["content"]
                
            # Completions format    
            elif "text" in first_choice:
                standardized["output"] = first_choice["text"]
                
            # Add finish reason if available
            if "finish_reason" in first_choice:
                standardized["finish_reason"] = first_choice["finish_reason"]

        # Extract token usage if available
        if "usage" in response:
            usage = response["usage"]
            if isinstance(usage, dict):
                standardized["input_tokens"] = usage.get("prompt_tokens", 0)
                standardized["output_tokens"] = usage.get("completion_tokens", 0)
                standardized["total_tokens"] = usage.get("total_tokens", 0)
                
        # Also check for usage values added by the patcher
        if "llm.usage.input_tokens" in response:
            standardized["input_tokens"] = response["llm.usage.input_tokens"]
        if "llm.usage.output_tokens" in response:
            standardized["output_tokens"] = response["llm.usage.output_tokens"]
        if "llm.usage.total_tokens" in response:
            standardized["total_tokens"] = response["llm.usage.total_tokens"]

        return standardized 