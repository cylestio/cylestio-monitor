"""
REST API client for sending telemetry events to a remote endpoint.

This module provides a minimal implementation for sending telemetry events
to a remote REST API endpoint.
"""

import json
import logging
import os
import threading
import queue
import time
from typing import Any, Dict, Optional
import requests
from datetime import datetime

from cylestio_monitor.config import ConfigManager

# Set up module-level logger
logger = logging.getLogger(__name__)

# Get configuration manager instance
config_manager = ConfigManager()

# Global event queue for background processing
_event_queue = queue.Queue()
_thread_running = False
_thread_stop_event = threading.Event()


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
        # Try to get endpoint from parameters, then config, then environment, then default
        self.endpoint = endpoint
        if not self.endpoint:
            self.endpoint = config_manager.get("api.endpoint")
        if not self.endpoint:
            self.endpoint = os.environ.get("CYLESTIO_API_ENDPOINT")
        if not self.endpoint:
            # Set default endpoint if not provided anywhere else - use 127.0.0.1:8000
            self.endpoint = "http://127.0.0.1:8000/api/v1/telemetry/"
            logger.info(f"Using default API endpoint: {self.endpoint}")
            
        # Try to get HTTP method from parameters, then config, then default to POST
        self.http_method = http_method
        if not self.http_method:
            self.http_method = config_manager.get("api.http_method", "POST")
        if not self.http_method:
            self.http_method = "POST"  # Default to POST if not specified
            
        # Get timeout from config or use default
        self.timeout = config_manager.get("api.timeout", 5)
            
        logger.info(f"API client initialized with endpoint: {self.endpoint}, method: {self.http_method}")

    def send_event(self, event: Dict[str, Any]) -> bool:
        """
        Send a telemetry event to the remote API endpoint.
        
        Args:
            event: The telemetry event data to send
            
        Returns:
            bool: True if the event was successfully queued for sending
        """
        if not self.endpoint:
            logger.warning("Cannot send event: No API endpoint configured")
            return False
        
        # Add to the queue for background processing - non-blocking
        _event_queue.put((self.endpoint, self.http_method, self.timeout, event))
        
        # Start background thread if not already running
        _ensure_background_thread_running()
        
        return True

    def _send_event_direct(self, endpoint: str, http_method: str, timeout: int, event: Dict[str, Any]) -> bool:
        """
        Directly send a telemetry event to the API endpoint.
        
        This is the actual sending logic used by the background thread.
        
        Args:
            endpoint: The API endpoint to send to
            http_method: The HTTP method to use
            timeout: Request timeout in seconds
            event: The telemetry event data to send
            
        Returns:
            bool: True if the event was successfully sent
        """
        try:
            # Create the request based on the configured HTTP method
            headers = {"Content-Type": "application/json"}
            
            # Debug logging
            logger.debug(f"Sending event to API endpoint: {endpoint}")
            
            # Make the request using the configured HTTP method
            if http_method.upper() == "POST":
                response = requests.post(
                    endpoint,
                    json=event,
                    headers=headers,
                    timeout=timeout
                )
            elif http_method.upper() == "PUT":
                response = requests.put(
                    endpoint,
                    json=event,
                    headers=headers,
                    timeout=timeout
                )
            else:
                logger.error(f"Unsupported HTTP method: {http_method}")
                return False
            
            # Check if the request was successful
            if response.ok:
                logger.debug(f"Event successfully sent to API endpoint")
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


def _background_sender_thread():
    """Background thread function for sending events from the queue."""
    global _thread_running
    
    _thread_running = True
    logger.debug("Background event sender thread started")
    
    api_client = get_api_client()
    
    while not _thread_stop_event.is_set():
        try:
            # Get an event from the queue with timeout
            try:
                endpoint, http_method, timeout, event = _event_queue.get(block=True, timeout=0.5)
            except queue.Empty:
                continue
                
            # Send the event
            try:
                api_client._send_event_direct(endpoint, http_method, timeout, event)
            finally:
                # Mark task as done regardless of success
                _event_queue.task_done()
                
        except Exception as e:
            logger.error(f"Error in background sender thread: {str(e)}")
    
    # Process remaining items in the queue before exiting
    while not _event_queue.empty():
        try:
            endpoint, http_method, timeout, event = _event_queue.get(block=False)
            try:
                api_client._send_event_direct(endpoint, http_method, timeout, event)
            finally:
                _event_queue.task_done()
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Error processing remaining events: {str(e)}")
    
    logger.debug("Background event sender thread stopped")
    _thread_running = False


def _ensure_background_thread_running():
    """Ensure the background sender thread is running."""
    global _thread_running
    
    if not _thread_running and not _thread_stop_event.is_set():
        thread = threading.Thread(target=_background_sender_thread, daemon=True)
        thread.start()


def stop_background_thread():
    """Stop the background sender thread."""
    global _thread_running
    
    if _thread_running:
        _thread_stop_event.set()
        # Wait for the remaining events to be processed (with timeout)
        try:
            _event_queue.join(timeout=2.0)
        except Exception:
            pass


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


def send_event_to_api(event: Dict[str, Any]) -> bool:
    """
    Send an event to the remote API endpoint asynchronously.
    
    Args:
        event: The event to send (in OpenTelemetry-compliant format)
        
    Returns:
        bool: True if the event was successfully queued for sending
    """
    # Get the API client
    api_client = get_api_client()
    
    # Check if we have an endpoint
    if not api_client.endpoint:
        return False
        
    # Queue the event for sending
    return api_client.send_event(event)


# Legacy API function for backward compatibility - will be removed in future versions
def send_event_to_api_legacy(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None
) -> bool:
    """
    Legacy function for sending an event to the remote API endpoint.
    
    This function is deprecated and will be removed in future versions.
    Use the new send_event_to_api function instead.
    
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
    
    # Create the event payload in the new format
    event = {
        "timestamp": timestamp.isoformat(),
        "agent_id": agent_id,
        "name": event_type.lower().replace('_', '.'),
        "level": level.upper(),
        "attributes": {
            **data,
            "source": channel.upper()
        }
    }
    
    # Add direction if provided
    if direction:
        event["attributes"]["direction"] = direction
        
    # Send the event
    return send_event_to_api(event) 