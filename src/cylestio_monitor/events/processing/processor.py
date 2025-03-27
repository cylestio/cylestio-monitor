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


def _get_event_id(event_type: str, data: Dict[str, Any], timestamp: Optional[datetime] = None) -> str:
    """Generate a unique identifier for events to track duplicates.
    
    Args:
        event_type: The type of event
        data: Event data
        timestamp: Optional timestamp for the event
        
    Returns:
        A string identifier for the event
    """
    # Create a normalized representation of the event
    serialized_data = json.dumps(data, sort_keys=True, default=str)
    
    # Add timestamp if provided
    if timestamp:
        serialized_data += timestamp.isoformat()
    
    # Create a hash of the event type and serialized data
    return hashlib.md5(f"{event_type}:{serialized_data}".encode()).hexdigest()


def create_standardized_event(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> StandardizedEvent:
    """Create a standardized event object.
    
    Args:
        agent_id: ID of the agent
        event_type: Type of event
        data: Event data
        channel: Event channel
        level: Log level
        timestamp: Optional timestamp for the event
        direction: Optional direction for the event
        
    Returns:
        A StandardizedEvent object
    """
    # Use current timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create the standardized event
    return StandardizedEvent(
        agent_id=agent_id,
        event_type=event_type,
        data=data,
        channel=channel.upper(),
        level=level.upper(),
        timestamp=timestamp.isoformat(),
        direction=direction
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
    event_id = _get_event_id(event.event_type, event.data, 
                            datetime.fromisoformat(event.timestamp) if isinstance(event.timestamp, str) else event.timestamp)
    
    # Check for duplicates
    if event_id in _processed_event_ids:
        logger.debug(f"Skipping duplicate event: {event.event_type}")
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
    masked_data = mask_sensitive_data(event.data)
    event.data = masked_data
    
    # Check for security concerns
    alert = check_security_concerns(masked_data)
    
    # Update alert in data if it's not "none"
    if alert != "none":
        event.data["alert"] = alert
    
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
    
    def process_event(self, event_type: str, data: Dict[str, Any], **kwargs) -> None:
        """Process a general event.
        
        Args:
            event_type: Type of event
            data: Event data
            **kwargs: Additional parameters for log_event
        """
        # Add agent_id to data if not present
        if "agent_id" not in data:
            data["agent_id"] = self.agent_id
        
        # Log the event
        from cylestio_monitor.events.processing.logger import log_event
        log_event(event_type, data, **kwargs)
    
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
        
        # Ensure agent_id is passed to the hook
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = self.agent_id
        
        # Process the request
        return llm_call_hook(provider, model, prompt, **kwargs)
    
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
            call_id: Call ID from process_llm_request
            provider: LLM provider name
            model: Model identifier
            response: Response from the LLM
            prompt: Optional prompt that generated the response
            **kwargs: Additional parameters
        """
        from cylestio_monitor.events.processing.hooks import llm_response_hook
        
        # Ensure agent_id is passed to the hook
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = self.agent_id
        
        # Process the response
        llm_response_hook(call_id, provider, model, response, prompt, **kwargs)
    
    def process_mcp_connection(
        self,
        connection_id: str,
        event_type: str,
        client_info: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Process an MCP connection event.
        
        Args:
            connection_id: ID of the MCP connection
            event_type: Type of connection event
            client_info: Optional client information
            error: Optional error message
        """
        from cylestio_monitor.events.processing.mcp import log_mcp_connection_event
        
        # Process the connection event
        log_mcp_connection_event(
            agent_id=self.agent_id,
            connection_id=connection_id,
            event_type=event_type,
            client_info=client_info,
            error=error
        )
    
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
            connection_id: ID of the MCP connection
            command: Command data
            direction: Direction ("incoming" or "outgoing")
            response: Optional response data
            error: Optional error message
        """
        from cylestio_monitor.events.processing.mcp import log_mcp_command_event
        
        # Process the command
        log_mcp_command_event(
            agent_id=self.agent_id,
            connection_id=connection_id,
            command=command,
            direction=direction,
            response=response,
            error=error
        )
    
    def process_langchain_input(
        self,
        chain_name: str,
        inputs: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Process a Langchain input.
        
        Args:
            chain_name: Name of the Langchain component
            inputs: Input data
            **kwargs: Additional parameters
            
        Returns:
            Dict with execution_id
        """
        from cylestio_monitor.events.processing.hooks import langchain_input_hook
        
        # Ensure agent_id is passed to the hook
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = self.agent_id
        
        # Process the input
        return langchain_input_hook(chain_name, inputs, **kwargs)
    
    def process_langchain_output(
        self,
        chain_name: str,
        execution_id: str,
        outputs: Dict[str, Any],
        **kwargs
    ) -> None:
        """Process a Langchain output.
        
        Args:
            chain_name: Name of the Langchain component
            execution_id: Execution ID from process_langchain_input
            outputs: Output data
            **kwargs: Additional parameters
        """
        from cylestio_monitor.events.processing.hooks import langchain_output_hook
        
        # Ensure agent_id is passed to the hook
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = self.agent_id
        
        # Process the output
        langchain_output_hook(chain_name, execution_id, outputs, **kwargs)
    
    def process_langgraph_state(
        self,
        graph_name: str,
        state: Dict[str, Any],
        node_name: Optional[str] = None,
        **kwargs
    ) -> None:
        """Process a LangGraph state update.
        
        Args:
            graph_name: Name of the LangGraph
            state: State data
            node_name: Optional node name
            **kwargs: Additional parameters
        """
        from cylestio_monitor.events.processing.hooks import langgraph_state_update_hook
        
        # Ensure agent_id is passed to the hook
        if "agent_id" not in kwargs:
            kwargs["agent_id"] = self.agent_id
        
        # Process the state update
        langgraph_state_update_hook(graph_name, state, node_name, **kwargs) 