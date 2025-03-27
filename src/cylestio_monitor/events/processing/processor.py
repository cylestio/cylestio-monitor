"""
Event processor for Cylestio Monitor.

This module provides the EventProcessor class and process_standardized_event function
for handling events and processing standardized events.
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.events.processing.security import mask_sensitive_data, check_security_concerns
from cylestio_monitor.api_client import ApiClient


# Set up module-level logger
logger = logging.getLogger("CylestioMonitor")

# Get configuration manager instance
config_manager = ConfigManager()

# Initialize API client
api_client = ApiClient()

# Track processed events to prevent duplicates
_processed_event_ids: Set[str] = set()


def _get_event_id(name: str, attributes: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
    """Generate a unique identifier for events to track duplicates.
    
    Args:
        name: The name of the event
        attributes: Event attributes
        timestamp: Optional timestamp for the event
        
    Returns:
        A string identifier for the event
    """
    # Create a normalized representation of the event
    serialized_data = json.dumps(attributes, sort_keys=True, default=str)
    
    # Add timestamp if provided
    if timestamp:
        serialized_data += timestamp.isoformat()
    
    # Create a hash of the event name and serialized data
    return hashlib.md5(f"{name}:{serialized_data}".encode(), usedforsecurity=False).hexdigest()


def create_standardized_event(
    agent_id: str,
    name: str,
    attributes: Dict[str, Any],
    level: str = "info",
    timestamp: Optional[datetime] = None,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    parent_span_id: Optional[str] = None
) -> StandardizedEvent:
    """Create a standardized event object.
    
    Args:
        agent_id: ID of the agent
        name: Name of the event (OpenTelemetry convention)
        attributes: Event attributes following OpenTelemetry conventions
        level: Log level
        timestamp: Optional timestamp for the event
        trace_id: Optional trace ID
        span_id: Optional span ID
        parent_span_id: Optional parent span ID
        
    Returns:
        A StandardizedEvent object
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create the standardized event
    return StandardizedEvent(
        agent_id=agent_id,
        name=name,
        attributes=attributes,
        level=level.upper(),
        timestamp=timestamp.isoformat(),
        trace_id=trace_id,
        span_id=span_id,
        parent_span_id=parent_span_id
    )


def process_standardized_event(event: StandardizedEvent) -> None:
    """Process an event using the standardized schema.
    
    This function:
    1. Checks for duplicates
    2. Masks sensitive data
    3. Checks for security concerns
    4. Logs the event to a file
    5. Sends the event to the API endpoint
    
    Args:
        event: A StandardizedEvent object
    """
    # Generate event ID
    event_id = _get_event_id(
        event.name, 
        event.attributes, 
        datetime.fromisoformat(event.timestamp) if isinstance(event.timestamp, str) else event.timestamp
    )
    
    # Check for duplicates
    if event_id in _processed_event_ids:
        logger.debug(f"Skipping duplicate event: {event.name}")
        return
    
    # Add to processed events
    _processed_event_ids.add(event_id)
    # Limit the size of the set
    if len(_processed_event_ids) > 1000:
        try:
            for _ in range(100):
                _processed_event_ids.pop()
        except KeyError:
            pass
    
    # Mask sensitive data
    masked_attributes = mask_sensitive_data(event.attributes)
    event.attributes = masked_attributes
    
    # Check for security concerns
    alert = check_security_concerns(masked_attributes)
    
    # Update alert in attributes if it's not "none"
    if alert != "none":
        event.attributes["security.alert"] = alert
    
    # Get log file path from config
    log_file = config_manager.get("monitoring.log_file")
    
    # Log to file if configured
    if log_file:
        from cylestio_monitor.event_logger import log_to_file
        log_to_file(event.to_dict(), log_file)
    
    # Send to API if enabled
    if config_manager.get("monitoring.api_enabled", True):
        try:
            api_client.send_event(event.to_dict())
        except Exception as e:
            logger.error(f"Failed to send event to API: {e}")


class EventProcessor:
    """Process events and standardize them for logging and API submission."""
    
    def __init__(self, agent_id: Optional[str] = None):
        """Initialize the event processor.
        
        Args:
            agent_id: Optional agent ID to use for events
        """
        self.agent_id = agent_id or config_manager.get("monitoring.agent_id", "unknown")
        self.logger = logging.getLogger("CylestioMonitor")
    
    def process_event(self, name: str, attributes: Dict[str, Any], **kwargs) -> None:
        """Process a general event.
        
        Args:
            name: Name of the event (OpenTelemetry convention)
            attributes: Event attributes
            **kwargs: Additional parameters for log_event
        """
        # Add agent_id to attributes if not present
        if "agent_id" not in attributes:
            attributes["agent_id"] = self.agent_id
        
        # Log the event
        from cylestio_monitor.events.processing.logger import log_event
        log_event(name, attributes, **kwargs)
    
    def process_llm_request(
        self, 
        provider: str, 
        model: str, 
        prompt: Union[str, List[Dict[str, str]]],
        **kwargs
    ) -> Dict[str, Any]:
        """Process an LLM request and check for security concerns.
        
        Args:
            provider: LLM provider name
            model: Model identifier
            prompt: Prompt text or messages
            **kwargs: Additional parameters
            
        Returns:
            Dict with call_id and safe_to_call flag
        """
        from cylestio_monitor.events.processing.hooks import llm_call_hook
        
        # Prepare attributes
        attributes = {
            "llm.vendor": provider,
            "llm.model": model,
            "llm.request.type": "completion",
            "llm.request.prompt": prompt
        }
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in ("agent_id", "trace_id", "span_id", "parent_span_id"):
                attributes[f"llm.request.{key}"] = value
        
        # Add agent_id
        if "agent_id" not in attributes and self.agent_id:
            attributes["agent_id"] = self.agent_id
        
        # Process the request through the hook
        return llm_call_hook(
            provider=provider,
            model=model, 
            prompt=prompt,
            attributes=attributes,
            **kwargs
        )
    
    def process_llm_response(
        self,
        call_id: str,
        provider: str,
        model: str,
        response: Union[str, Dict[str, Any], List[Dict[str, Any]]],
        prompt: Optional[Union[str, List[Dict[str, str]]]] = None,
        **kwargs
    ) -> None:
        """Process an LLM response.
        
        Args:
            call_id: Identifier for the call (used to match request and response)
            provider: LLM provider name
            model: Model identifier
            response: Response data
            prompt: Original prompt if available
            **kwargs: Additional parameters
        """
        # Prepare attributes
        attributes = {
            "llm.vendor": provider,
            "llm.model": model,
            "llm.call_id": call_id,
            "llm.response.content": response
        }
        
        # Include prompt if provided
        if prompt:
            attributes["llm.request.prompt"] = prompt
        
        # Add usage statistics if available
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            if "input_tokens" in usage:
                attributes["llm.response.usage.input_tokens"] = usage["input_tokens"]
            if "output_tokens" in usage:
                attributes["llm.response.usage.output_tokens"] = usage["output_tokens"]
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in ("agent_id", "trace_id", "span_id", "parent_span_id"):
                attributes[f"llm.response.{key}"] = value
                
        # Add agent_id
        if "agent_id" not in attributes and self.agent_id:
            attributes["agent_id"] = self.agent_id
        
        # Log the response
        self.process_event("llm.response", attributes)
    
    def process_mcp_connection(
        self,
        connection_id: str,
        event_type: str,
        client_info: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Process an MCP connection event.
        
        Args:
            connection_id: MCP connection identifier
            event_type: Type of connection event
            client_info: Optional client information
            error: Optional error message
        """
        # Map event type to OpenTelemetry name
        if event_type == "connect":
            name = "mcp.connection.open"
        elif event_type == "disconnect":
            name = "mcp.connection.close"
        elif event_type == "error":
            name = "mcp.connection.error"
        else:
            name = f"mcp.connection.{event_type}"
        
        # Prepare attributes
        attributes = {
            "mcp.connection_id": connection_id
        }
        
        # Add client info if provided
        if client_info:
            for key, value in client_info.items():
                attributes[f"mcp.client.{key}"] = value
        
        # Add error if provided
        if error:
            attributes["error.message"] = error
            
        # Log the event
        self.process_event(name, attributes)
    
    def process_mcp_command(
        self,
        connection_id: str,
        command: Dict[str, Any],
        direction: str,
        response: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Process an MCP command.
        
        Args:
            connection_id: MCP connection identifier
            command: Command data
            direction: Direction of the command ("incoming" or "outgoing")
            response: Optional response data
            error: Optional error message
        """
        # Determine event name based on direction
        if direction == "incoming":
            name = "mcp.command.received"
        else:
            name = "mcp.command.sent"
        
        # Prepare attributes
        attributes = {
            "mcp.connection_id": connection_id,
            "mcp.command": command,
            "direction": direction
        }
        
        # Add response if provided
        if response:
            attributes["mcp.response"] = response
        
        # Add error if provided
        if error:
            attributes["error.message"] = error
            
        # Log the event
        self.process_event(name, attributes)
    
    def process_langchain_input(
        self,
        chain_name: str,
        inputs: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Process LangChain chain input.
        
        Args:
            chain_name: Name of the chain
            inputs: Chain input data
            **kwargs: Additional parameters
            
        Returns:
            Dict with execution_id and other context
        """
        # Generate execution ID
        execution_id = hashlib.md5(f"{chain_name}:{json.dumps(inputs, sort_keys=True, default=str)}".encode(), usedforsecurity=False).hexdigest()
        
        # Prepare attributes
        attributes = {
            "chain.name": chain_name,
            "chain.inputs": inputs,
            "chain.execution_id": execution_id
        }
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in ("agent_id", "trace_id", "span_id", "parent_span_id"):
                attributes[f"chain.{key}"] = value
                
        # Log the event
        self.process_event("chain.start", attributes)
        
        # Return context for later use
        return {
            "execution_id": execution_id,
            "chain_name": chain_name,
            "inputs": inputs
        }
    
    def process_langchain_output(
        self,
        chain_name: str,
        execution_id: str,
        outputs: Dict[str, Any],
        **kwargs
    ) -> None:
        """Process LangChain chain output.
        
        Args:
            chain_name: Name of the chain
            execution_id: Execution identifier
            outputs: Chain output data
            **kwargs: Additional parameters
        """
        # Prepare attributes
        attributes = {
            "chain.name": chain_name,
            "chain.execution_id": execution_id,
            "chain.outputs": outputs
        }
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in ("agent_id", "trace_id", "span_id", "parent_span_id"):
                attributes[f"chain.{key}"] = value
                
        # Log the event
        self.process_event("chain.end", attributes)
    
    def process_langgraph_state(
        self,
        graph_name: str,
        state: Dict[str, Any],
        node_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """Process LangGraph state update.
        
        Args:
            graph_name: Name of the graph
            state: Graph state data
            node_name: Optional node name
            **kwargs: Additional parameters
        """
        # Determine event name based on node presence
        if node_name:
            name = "graph.node.update"
        else:
            name = "graph.state.update"
        
        # Prepare attributes
        attributes = {
            "graph.name": graph_name,
            "graph.state": state
        }
        
        # Add node name if provided
        if node_name:
            attributes["node.name"] = node_name
        
        # Add any additional attributes
        for key, value in kwargs.items():
            if key not in ("agent_id", "trace_id", "span_id", "parent_span_id"):
                attributes[f"graph.{key}"] = value
                
        # Log the event
        self.process_event(name, attributes) 