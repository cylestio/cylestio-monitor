"""
Default event converter implementation.

This module contains the DefaultEventConverter class which converts events to the standardized schema.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from cylestio_monitor.events.converters.base import BaseEventConverter
from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.events.converters.default.standardizer import standardize_event_name
from cylestio_monitor.events.converters.default.extractors import (
    extract_security_info,
    extract_performance_metrics,
    extract_model_info,
    extract_framework_info,
    extract_request_info,
    extract_response_info
)


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
        standardized_event_type = standardize_event_name(event_type)
        if standardized_event_type != event_type:
            common_fields["event_type"] = standardized_event_type
        
        # Extract call stack
        call_stack = self._extract_call_stack(event)
        
        # Extract various components using the dedicated extraction functions
        security = extract_security_info(event, data)
        performance = extract_performance_metrics(event, data)
        model = extract_model_info(event, data)
        framework = extract_framework_info(event, data)
        request = extract_request_info(event, data)
        response = extract_response_info(event, data)
        
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
            logger = logging.getLogger("CylestioMonitor")
            logger.debug(f"DefaultConverter: Created standardized event for {event_type}")
            
        return standardized_event 