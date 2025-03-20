"""
REST API client for sending telemetry events to a remote endpoint.

This module provides a minimal implementation for sending telemetry events
to a remote REST API endpoint instead of storing them in a local SQLite database.
"""

import json
import logging
import os
from typing import Any, Dict, Optional
import requests
from datetime import datetime

# Set up module-level logger
logger = logging.getLogger(__name__)


class ApiClient:
    """
    Simple REST API client for sending telemetry events to a remote endpoint.
    """

    def __init__(self, endpoint: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            endpoint: The remote API endpoint URL. If None, it will try to get from environment.
        """
        self.endpoint = endpoint or os.environ.get("CYLESTIO_API_ENDPOINT")
        if not self.endpoint:
            logger.warning("No API endpoint configured. Events will not be sent to a remote server.")

    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send a telemetry event to the remote API endpoint.
        
        Args:
            event: The telemetry event data to send
            
        Returns:
            bool: True if the event was successfully sent, False otherwise
        """
        if not self.endpoint:
            logger.warning("Cannot send event: No API endpoint configured")
            return False
            
        try:
            # Set a reasonable timeout to avoid blocking the application
            response = requests.post(
                self.endpoint,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=5  # 5 seconds timeout
            )
            
            # Check if the request was successful
            if response.ok:
                logger.debug(f"Event sent to API endpoint: {self.endpoint}")
                return True
            else:
                logger.error(f"Failed to send event to API: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error sending event to API: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending event to API: {str(e)}")
            return False


# Create a global API client instance
_api_client = None


def get_api_client() -> ApiClient:
    """
    Get the API client instance.
    
    Returns:
        ApiClient instance
    """
    global _api_client
    if _api_client is None:
        _api_client = ApiClient()
    return _api_client


def send_event_to_api(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> bool:
    """
    Send an event to the remote API endpoint.
    
    Args:
        agent_id: Agent ID
        event_type: Event type
        data: Event data
        channel: Event channel
        level: Log level
        timestamp: Event timestamp (defaults to now)
        direction: Event direction
        
    Returns:
        bool: True if the event was successfully sent, False otherwise
    """
    # Get timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Create the event payload
    event = {
        "timestamp": timestamp.isoformat(),
        "agent_id": agent_id,
        "event_type": event_type,
        "channel": channel.upper(),
        "level": level.upper(),
        "data": data
    }
    
    # Add direction if provided
    if direction:
        event["direction"] = direction
    
    # Get session_id and conversation_id from data if available
    if "session_id" in data:
        event["session_id"] = data["session_id"]
    if "conversation_id" in data:
        event["conversation_id"] = data["conversation_id"]
    
    # Send the event to the API
    client = get_api_client()
    return client.send_event(event) 