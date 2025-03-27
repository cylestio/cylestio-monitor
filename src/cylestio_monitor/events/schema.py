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
                 name: str,  # changed from event_type to name for OTel compliance
                 trace_id: Optional[str] = None,
                 span_id: Optional[str] = None,
                 parent_span_id: Optional[str] = None,
                 attributes: Optional[Dict[str, Any]] = None,
                 # Legacy parameters - to be migrated into attributes
                 channel: Optional[str] = None, 
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
            name: Name of event (following OpenTelemetry naming conventions)
            trace_id: Trace identifier (equivalent to run_id, chain_id, etc.)
            span_id: Span identifier for events part of a larger operation
            parent_span_id: Parent span identifier for nested operations
            attributes: OpenTelemetry-compliant attributes dictionary
            channel: Source channel/framework - legacy field
            direction: Direction of event ("incoming" or "outgoing") - legacy field
            session_id: Session identifier - legacy field
            call_stack: Call stack information - legacy field
            security: Security assessment data - legacy field
            performance: Performance metrics - legacy field
            model: Model details - legacy field
            framework: Framework information - legacy field
            request: Structured request data - legacy field
            response: Structured response data - legacy field
            extra: Any unmapped data - legacy field
        """
        self.timestamp = timestamp.isoformat() if isinstance(timestamp, datetime) else timestamp
        self.level = level
        self.agent_id = agent_id
        self.name = name  # OpenTelemetry uses 'name' instead of 'event_type'
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        
        # Initialize attributes with provided dict or empty dict
        self.attributes = attributes or {}
        
        # Migrate legacy fields into attributes
        if channel:
            self.attributes["channel"] = channel
        
        if direction:
            self.attributes["direction"] = direction
            
        if session_id:
            self.attributes["session_id"] = session_id
            
        if call_stack:
            for i, frame in enumerate(call_stack):
                for key, value in frame.items():
                    self.attributes[f"caller.{key}"] = value
                    break  # Only use the first frame for standard attributes
                
        if security:
            for key, value in security.items():
                self.attributes[f"security.{key}"] = value
                
        if performance:
            for key, value in performance.items():
                self.attributes[f"performance.{key}"] = value
                
        if model:
            for key, value in model.items():
                self.attributes[f"llm.{key}"] = value
                
        if framework:
            for key, value in framework.items():
                self.attributes[f"framework.{key}"] = value
                
        if request:
            for key, value in request.items():
                self.attributes[f"request.{key}"] = value
                
        if response:
            for key, value in response.items():
                self.attributes[f"response.{key}"] = value
                
        if extra:
            # Keep extra fields at top level of attributes
            for key, value in extra.items():
                self.attributes[key] = value
        
        # Set event category based on event name
        self.event_category = self._determine_event_category()
        
    def _determine_event_category(self) -> str:
        """
        Determine the event category based on event name.
        
        Categories:
        - user_interaction: Events related to user inputs/requests
        - llm: Events where an LLM is being used
        - tool: Events related to tool usage
        - system: System-level events
        
        Returns:
            The event category as a string
        """
        # Determine by OpenTelemetry prefixes
        if self.name.startswith("user."):
            return "user_interaction"
            
        if self.name.startswith("llm."):
            return "llm"
            
        if self.name.startswith("tool."):
            return "tool"
            
        if self.name.startswith("chain.") or self.name.startswith("graph."):
            return "framework"
            
        if self.name.startswith("retrieval."):
            return "retrieval"
            
        if self.name.startswith("framework."):
            return "system"
            
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
            "name": self.name,  # OpenTelemetry uses 'name' instead of 'event_type'
            "event_category": self.event_category,
        }
        
        # Add trace context if present
        if self.trace_id:
            result["trace_id"] = self.trace_id
            
        if self.span_id:
            result["span_id"] = self.span_id
            
        if self.parent_span_id:
            result["parent_span_id"] = self.parent_span_id
            
        # Add attributes if present
        if self.attributes:
            result["attributes"] = self.attributes
            
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
        # Handle different variations in field names (support legacy format)
        name = data.get("name") or data.get("event_type", "unknown")
        attributes = data.get("attributes", {})
        
        # Extract legacy fields if present
        channel = data.get("channel")
        direction = data.get("direction")
        session_id = data.get("session_id")
        call_stack = data.get("call_stack")
        security = data.get("security")
        performance = data.get("performance")
        model = data.get("model")
        framework = data.get("framework") 
        request = data.get("request")
        response = data.get("response")
        extra = data.get("extra")
        
        return cls(
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            level=data.get("level", "INFO"),
            agent_id=data.get("agent_id", "unknown"),
            name=name,
            trace_id=data.get("trace_id"),
            span_id=data.get("span_id"),
            parent_span_id=data.get("parent_span_id"),
            attributes=attributes,
            channel=channel,
            direction=direction,
            session_id=session_id,
            call_stack=call_stack,
            security=security,
            performance=performance,
            model=model,
            framework=framework,
            request=request,
            response=response,
            extra=extra
        ) 