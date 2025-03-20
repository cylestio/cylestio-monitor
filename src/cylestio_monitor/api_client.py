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

from cylestio_monitor.config import ConfigManager

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()

class ApiClient:
    """
    Simple REST API client for sending telemetry events to a remote endpoint.
    """

    def __init__(self, endpoint: Optional[str] = None, http_method: Optional[str] = None):
        """
        Initialize the API client.
        
        Args:
            endpoint: The remote API endpoint URL. If None, it will try to get from configuration or environment.
            http_method: The HTTP method to use (POST, PUT, etc.). If None, it will try to get from configuration.
        """
        # Try to get endpoint from parameters, then config, then environment
        self.endpoint = endpoint
        if not self.endpoint:
            self.endpoint = config_manager.get("api.endpoint")
        if not self.endpoint:
            self.endpoint = os.environ.get("CYLESTIO_API_ENDPOINT")
            
        # Try to get HTTP method from parameters, then config, then default to POST
        self.http_method = http_method
        if not self.http_method:
            self.http_method = config_manager.get("api.http_method", "POST")
        if not self.http_method:
            self.http_method = "POST"  # Default to POST if not specified
            
        # Get timeout from config or use default
        self.timeout = config_manager.get("api.timeout", 5)
            
        if not self.endpoint:
            logger.warning("No API endpoint configured. Events will not be sent to a remote server.")
        
        logger.info(f"API client initialized with endpoint: {self.endpoint}, method: {self.http_method}")

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
            # Create the request based on the configured HTTP method
            headers = {"Content-Type": "application/json"}
            
            # Make the request using the configured HTTP method
            if self.http_method.upper() == "POST":
                response = requests.post(
                    self.endpoint,
                    json=event,
                    headers=headers,
                    timeout=self.timeout
                )
            elif self.http_method.upper() == "PUT":
                response = requests.put(
                    self.endpoint,
                    json=event,
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                logger.error(f"Unsupported HTTP method: {self.http_method}")
                return False
            
            # Check if the request was successful
            if response.ok:
                logger.debug(f"Event sent to API endpoint: {self.endpoint} using {self.http_method}")
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