"""
EventProcessor class for handling and processing events.

This module provides a class for processing different types of monitoring events,
including LLM requests and responses.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from cylestio_monitor.events.keyword_detection import get_alert_level
from cylestio_monitor.events.standardized_event import process_standardized_event

# Set up module-level logger
logger = logging.getLogger(__name__)


class EventProcessor:
    """Event processor for handling and routing monitoring events."""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """Initialize the event processor.
        
        Args:
            agent_id: The ID of the agent being monitored
            config: Optional configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config or {}
        
    def process_event(self, event_type: str, data: Dict[str, Any], 
                      channel: str = "APPLICATION", level: str = "info",
                      direction: Optional[str] = None) -> None:
        """Process an event by logging it to the API and performing any required actions.
        
        Args:
            event_type: The type of event
            data: Event data
            channel: Event channel
            level: Log level
            direction: Message direction for chat events ("incoming" or "outgoing")
        """
        # Add agent_id if not present
        if "agent_id" not in data:
            data["agent_id"] = self.agent_id
            
        # Call the standardized event processing function directly
        process_standardized_event(
            agent_id=self.agent_id,
            event_type=event_type,
            data=data,
            channel=channel,
            level=level,
            direction=direction
        )
    
    def process_llm_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Process an LLM request event.
        
        Args:
            prompt: The prompt being sent to the LLM
            kwargs: Additional keyword arguments
            
        Returns:
            Dictionary with request metadata
        """
        # Check for security concerns
        alert = get_alert_level(prompt)
        
        # Prepare metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "prompt": prompt,
            "alert": alert,
            **kwargs
        }
        
        # Log the event
        self.process_event("llm_request", metadata)
        
        return metadata
    
    def process_llm_response(self, prompt: str, response: str, 
                             processing_time: float, **kwargs) -> Dict[str, Any]:
        """Process an LLM response event.
        
        Args:
            prompt: The original prompt
            response: The LLM response
            processing_time: Time taken to process in seconds
            kwargs: Additional keyword arguments
            
        Returns:
            Dictionary with response metadata
        """
        # Check for security concerns in response
        alert = get_alert_level(response)
        
        # Prepare metadata
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": self.agent_id,
            "prompt": prompt,
            "response": response,
            "processing_time": processing_time,
            "alert": alert,
            **kwargs
        }
        
        # Log the event
        self.process_event("llm_response", metadata)
        
        return metadata 