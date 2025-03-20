"""
Base interface for event converters.

This module defines the base interface that all framework-specific event 
converters must implement to provide a consistent conversion approach.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from cylestio_monitor.events.schema import StandardizedEvent


class BaseEventConverter(ABC):
    """
    Base interface for all event converters.
    
    This abstract class defines the methods that all converters must implement to
    transform framework-specific events into the standardized schema.
    """
    
    @abstractmethod
    def convert(self, event: Dict[str, Any]) -> StandardizedEvent:
        """
        Convert a raw event to the standardized schema.
        
        Args:
            event: The original event as a dictionary
            
        Returns:
            StandardizedEvent: A standardized event instance
        """
        pass
    
    def _copy_common_fields(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Copy common fields from the original event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with common fields copied
        """
        result = {
            "timestamp": event.get("timestamp"),
            "level": event.get("level"),
            "agent_id": event.get("agent_id"),
            "event_type": event.get("event_type"),
            "channel": event.get("channel"),
        }
        
        # Add optional common fields if present
        if "direction" in event:
            result["direction"] = event["direction"]
        
        if "session_id" in event:
            result["session_id"] = event["session_id"]
            
        return result
    
    def _extract_trace_span_ids(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract trace and span IDs from the event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with trace_id, span_id, and parent_span_id (if available)
        """
        result = {}
        
        # Extract from data if available
        data = event.get("data", {})
        
        # Different frameworks use different naming conventions
        trace_id_candidates = ["run_id", "chain_id", "trace_id", "conversation_id"]
        span_id_candidates = ["span_id", "step_id"]
        parent_span_id_candidates = ["parent_id", "parent_span_id", "parent_run_id"]
        
        # Find trace_id
        for candidate in trace_id_candidates:
            if candidate in data:
                result["trace_id"] = data[candidate]
                break
                
        # Find span_id
        for candidate in span_id_candidates:
            if candidate in data:
                result["span_id"] = data[candidate]
                break
                
        # Find parent_span_id
        for candidate in parent_span_id_candidates:
            if candidate in data:
                result["parent_span_id"] = data[candidate]
                break
                
        return result
    
    def _extract_call_stack(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract call stack information from the event.
        
        Args:
            event: The original event
            
        Returns:
            List of call stack entries
        """
        data = event.get("data", {})
        
        if "call_stack" in data and isinstance(data["call_stack"], list):
            return data["call_stack"]
        
        return []
    
    def _extract_security_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract security information from the event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with security information
        """
        data = event.get("data", {})
        
        if "security" in data and isinstance(data["security"], dict):
            return data["security"]
        
        return {}
    
    def _extract_performance_metrics(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance metrics from the event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with performance metrics
        """
        data = event.get("data", {})
        
        if "performance" in data and isinstance(data["performance"], dict):
            return data["performance"]
        
        return {}
    
    def _extract_framework_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract framework information from the event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with framework information
        """
        data = event.get("data", {})
        
        if "framework" in data and isinstance(data["framework"], dict):
            return data["framework"]
        
        return {}
    
    def _extract_model_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract model information from the event.
        
        Args:
            event: The original event
            
        Returns:
            Dictionary with model information
        """
        data = event.get("data", {})
        
        if "model" in data and isinstance(data["model"], dict):
            return data["model"]
        
        return {} 