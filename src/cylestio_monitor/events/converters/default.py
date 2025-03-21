"""
Default event converter.

This module provides a default converter for events that don't match any
known framework, ensuring all events can still be processed.
"""

from typing import Any, Dict, Optional

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class DefaultEventConverter(BaseEventConverter):
    """
    Default converter for unknown event types.
    
    This class provides a fallback converter for events that don't match
    any of the known frameworks, ensuring all events can still be processed.
    """
    
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert an unknown event to the standardized schema.
        
        Args:
            event: The original event of unknown type
            
        Returns:
            StandardizedEvent: A standardized event instance
        """
        # Debug logging for LLM call events
        event_type = event.get("event_type", "unknown")
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            import logging
            logger = logging.getLogger("CylestioMonitor")
            logger.debug(f"DefaultConverter: Processing LLM call event: {event_type}")
            
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
        
        # Extract model info
        model = self._extract_model_info(event)
        
        # Determine if this is a request or response based on event type or direction
        request = None
        response = None
        
        if (event.get("direction") == "outgoing" or 
            any(req_type in event.get("event_type", "").lower() for req_type in ["request", "input", "start"])):
            # This is likely a request event
            request = data
        elif (event.get("direction") == "incoming" or 
              any(resp_type in event.get("event_type", "").lower() for resp_type in ["response", "output", "end", "result"])):
            # This is likely a response event
            response = data
        else:
            # If we can't determine, put everything in extra
            extra = data
            
        # For LLM call events, ensure we don't lose data
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            if request is None and response is None:
                request = data  # Default to putting data in request for these events
                
            import logging
            logger = logging.getLogger("CylestioMonitor")
            logger.debug(f"DefaultConverter: Constructed event data for {event_type}")
            
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
            extra=data
        )
        
        # Log final event creation for LLM call events
        if event_type in ["LLM_call_start", "LLM_call_finish", "LLM_call_blocked"]:
            import logging
            logger = logging.getLogger("CylestioMonitor")
            logger.debug(f"DefaultConverter: Created standardized event for {event_type}")
            
        return standardized_event 