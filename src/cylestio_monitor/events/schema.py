"""
Standardized event schema based on OpenTelemetry trace/span concepts.

This module defines the standardized event schema that all framework-specific 
events will be converted to, ensuring consistent data structure for processing
and storage.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union


class StandardizedEvent:
    """
    Standardized event schema based on OpenTelemetry trace/span concepts.
    
    This class defines the structure that all events will be converted to,
    providing a consistent format for processing and analysis.
    """
    
    def __init__(self, 
                 timestamp: Union[str, datetime],
                 level: str,
                 agent_id: str,
                 event_type: str,
                 channel: str,
                 trace_id: Optional[str] = None,
                 span_id: Optional[str] = None,
                 parent_span_id: Optional[str] = None,
                 direction: Optional[str] = None,
                 session_id: Optional[str] = None,
                 call_stack: Optional[List[Dict[str, Any]]] = None,
                 security: Optional[Dict[str, Any]] = None,
                 performance: Optional[Dict[str, Any]] = None,
                 model: Optional[Dict[str, Any]] = None,
                 framework: Optional[Dict[str, Any]] = None,
                 request: Optional[Dict[str, Any]] = None,
                 response: Optional[Dict[str, Any]] = None,
                 extra: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize a standardized event.
        
        Args:
            timestamp: Event timestamp (ISO format string or datetime)
            level: Log level (INFO, WARNING, ERROR, etc.)
            agent_id: Agent identifier
            event_type: Type of event
            channel: Source channel/framework
            trace_id: Trace identifier (equivalent to run_id, chain_id, etc.)
            span_id: Span identifier for events part of a larger operation
            parent_span_id: Parent span identifier for nested operations
            direction: Direction of event ("incoming" or "outgoing")
            session_id: Session identifier
            call_stack: Call stack information
            security: Security assessment data
            performance: Performance metrics
            model: Model details
            framework: Framework information
            request: Structured request data
            response: Structured response data
            extra: Any unmapped data
        """
        self.timestamp = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
        self.level = level
        self.agent_id = agent_id
        self.event_type = event_type
        self.channel = channel
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.direction = direction
        self.session_id = session_id
        self.call_stack = call_stack or []
        self.security = security or {}
        self.performance = performance or {}
        self.model = model or {}
        self.framework = framework or {}
        self.request = request or {}
        self.response = response or {}
        self.extra = extra or {}
        
        # Set event category based on event type and direction
        self.event_category = self._determine_event_category()
        
    def _determine_event_category(self) -> str:
        """
        Determine the event category based on event type and direction.
        
        Categories:
        - user_interaction: Events related to user inputs/requests
        - llm_request: Events where an LLM is being prompted
        - llm_response: Events where an LLM is responding
        - tool_interaction: Events related to tool usage
        - system: System-level events
        
        Returns:
            The event category as a string
        """
        # User interaction events
        if self.event_type in ["user_message", "user_input", "user_request"]:
            return "user_interaction"
            
        # LLM interaction events
        if self.event_type in ["model_request", "llm_request", "completion_request"]:
            return "llm_request"
            
        if self.event_type in ["model_response", "llm_response", "completion_response"]:
            return "llm_response"
            
        # Tool interaction events
        if "tool" in self.event_type.lower() or self.event_type.startswith("tool_"):
            return "tool_interaction"
            
        # System events (default)
        return "system"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the standardized event to a dictionary.
        
        Returns:
            Dictionary representation of the event
        """
        result = {
            "timestamp": self.timestamp,
            "level": self.level,
            "agent_id": self.agent_id,
            "event_type": self.event_type,
            "channel": self.channel,
            "event_category": self.event_category,
        }
        
        # Add optional fields if they have values
        if self.trace_id:
            result["trace_id"] = self.trace_id
            
        if self.span_id:
            result["span_id"] = self.span_id
            
        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id
            
        if self.direction:
            result["direction"] = self.direction
            
        if self.session_id:
            result["session_id"] = self.session_id
            
        if self.call_stack:
            result["call_stack"] = self.call_stack
            
        if self.security:
            result["security"] = self.security
            
        if self.performance:
            result["performance"] = self.performance
            
        if self.model:
            result["model"] = self.model
            
        if self.framework:
            result["framework"] = self.framework
            
        if self.request:
            result["request"] = self.request
            
        if self.response:
            result["response"] = self.response
            
        if self.extra:
            result["extra"] = self.extra
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardizedEvent':
        """
        Create a StandardizedEvent from a dictionary.
        
        Args:
            data: Dictionary containing event data
            
        Returns:
            StandardizedEvent instance
        """
        return cls(
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            level=data.get("level", "INFO"),
            agent_id=data.get("agent_id", "unknown"),
            event_type=data.get("event_type", "unknown"),
            channel=data.get("channel", "SYSTEM"),
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            parent_span_id=data.get("parent_span_id"),
            direction=data.get("direction"),
            session_id=data.get("session_id"),
            call_stack=data.get("call_stack"),
            security=data.get("security"),
            performance=data.get("performance"),
            model=data.get("model"),
            framework=data.get("framework"),
            request=data.get("request"),
            response=data.get("response"),
            extra=data.get("extra")
        ) 