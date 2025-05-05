"""API client for sending telemetry data to the Cylestio API.

This module provides a client for sending telemetry data to the Cylestio API.
It supports both synchronous and asynchronous sending of data.
"""

import json
import logging
import threading
import time
import urllib.request
from datetime import datetime
from queue import Empty, Queue
from typing import Any, Dict, List, Optional, Tuple
import os

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.utils.serialization import safe_event_serialize
from cylestio_monitor.security_detection import SecurityScanner
from cylestio_monitor.utils.event_utils import get_utc_timestamp, format_timestamp

# Configure logging
logger = logging.getLogger("cylestio_monitor.api_client")

# Background sending queue and thread
_event_queue: Queue = Queue()
_sender_thread: Optional[threading.Thread] = None
_thread_stop_event = threading.Event()


class ApiClient:
    """Client for sending telemetry data to the Cylestio API."""

    def __init__(
        self, endpoint: Optional[str] = None, http_method: Optional[str] = None
    ):
        """Initialize the API client.

        Args:
            endpoint: The API endpoint to send data to
            http_method: The HTTP method to use (POST or PUT)

        Raises:
            ValueError: If an invalid HTTP method is provided
        """
        # Load configuration
        config = ConfigManager()

        # Set endpoint - prioritize:
        # 1. Directly provided endpoint
        # 2. Environment variable
        # 3. Config file setting
        # 4. Default value
        env_endpoint = os.environ.get("CYLESTIO_TELEMETRY_ENDPOINT")
        telemetry_endpoint = endpoint or env_endpoint or config.get("api.endpoint") or "http://127.0.0.1:8000"
        
        # Ensure the endpoint ends with /v1/telemetry
        if not telemetry_endpoint.endswith("/v1/telemetry"):
            # Remove trailing slash if present
            if telemetry_endpoint.endswith("/"):
                telemetry_endpoint = telemetry_endpoint[:-1]
            telemetry_endpoint = f"{telemetry_endpoint}/v1/telemetry"
            
        self.endpoint = telemetry_endpoint

        # Set HTTP method (defaulting to POST)
        self.http_method = http_method or config.get("api.http_method") or "POST"
        if self.http_method not in ["POST", "PUT"]:
            raise ValueError(f"Invalid HTTP method: {self.http_method}")

        # Log configuration
        logger.info(
            f"API client initialized with endpoint: {self.endpoint}, method: {self.http_method}"
        )

        # Set request timeout (default: 5 seconds)
        self.timeout = int(config.get("api.timeout") or 5)

        # Whether to send in background
        self.send_in_background = bool(config.get("api.background_sending") or True)

    def send_event(self, event: Dict[str, Any]) -> bool:
        """Send an event to the API.

        Args:
            event: The event to send

        Returns:
            bool: True if the event was sent successfully, False otherwise
        """
        # Apply safe serialization to the event attributes
        event = self._ensure_serializable(event)
        
        # Ensure event has a properly formatted timestamp
        event_copy = event.copy()
        if 'timestamp' not in event_copy:
            event_copy['timestamp'] = format_timestamp()
        elif isinstance(event_copy['timestamp'], (str, datetime)):
            event_copy['timestamp'] = format_timestamp(event_copy['timestamp'])

        # Check if we should send in background
        if self.send_in_background:
            # Add to background queue
            _event_queue.put((self.endpoint, self.http_method, self.timeout, event_copy))
            _ensure_background_thread_running()
            return True
        else:
            # Send directly
            return self._send_event_direct(
                self.endpoint, self.http_method, self.timeout, event_copy
            )

    def _ensure_serializable(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the event is JSON serializable.

        Args:
            event: The event to check

        Returns:
            Dict: The serializable event
        """
        # Make a copy to avoid modifying the original
        event_copy = event.copy()

        # Safely serialize the attributes
        if "attributes" in event_copy:
            event_copy["attributes"] = safe_event_serialize(event_copy["attributes"])

        return event_copy

    def _send_event_direct(
        self, endpoint: str, http_method: str, timeout: int, event: Dict[str, Any]
    ) -> bool:
        """Send an event directly to the API.

        Args:
            endpoint: The API endpoint
            http_method: The HTTP method
            timeout: Request timeout in seconds
            event: The event to send

        Returns:
            bool: True if the event was sent successfully, False otherwise
        """
        try:
            # Convert event to JSON
            event_json = json.dumps(event)
            event_bytes = event_json.encode("utf-8")

            # Create request
            req = urllib.request.Request(
                url=endpoint, data=event_bytes, method=http_method
            )

            # Add headers
            req.add_header("Content-Type", "application/json")
            req.add_header("User-Agent", "Cylestio-Monitor/1.0")

            # Send request
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status

                if status < 200 or status >= 300:
                    logger.warning(f"API request failed with status {status}")
                    return False

                return True

        except Exception as e:
            logger.error(f"Unexpected error sending event to API: {e}")
            return False


def _background_sender_thread():
    """Background thread for sending events to the API."""
    logger.debug("Starting background sender thread")

    # List to batch events
    batch: List[Tuple[str, str, int, Dict[str, Any]]] = []
    batch_size = 10  # Max events to send in a batch
    last_send_time = time.time()
    max_batch_age = 5  # Max seconds to hold events before sending

    try:
        while not _thread_stop_event.is_set():
            try:
                # Get the next event from the queue with a timeout
                try:
                    event_data = _event_queue.get(timeout=1.0)
                    batch.append(event_data)
                    _event_queue.task_done()
                except Empty:
                    # No new events
                    pass

                # Check if we should send the batch
                batch_age = time.time() - last_send_time
                if (len(batch) >= batch_size) or (batch and batch_age >= max_batch_age):
                    # Process the batch
                    for endpoint, http_method, timeout, event in batch:
                        try:
                            # Get an API client and send directly
                            client = ApiClient(endpoint, http_method)
                            client._send_event_direct(
                                endpoint, http_method, timeout, event
                            )
                        except Exception as e:
                            logger.error(f"Error in background sending: {e}")

                    # Reset the batch
                    batch = []
                    last_send_time = time.time()

            except Exception as e:
                logger.error(f"Error in background sender thread: {e}")
                time.sleep(1)  # Avoid tight loop on persistent errors

    except Exception as e:
        logger.error(f"Background sender thread died: {e}")
    finally:
        logger.debug("Background sender thread stopping")

        # Attempt to send any remaining events
        for endpoint, http_method, timeout, event in batch:
            try:
                client = ApiClient(endpoint, http_method)
                client._send_event_direct(endpoint, http_method, timeout, event)
            except Exception:
                # Just log and continue
                logger.error("Failed to send event during thread shutdown")


def _ensure_background_thread_running():
    """Ensure the background sender thread is running."""
    global _sender_thread

    if _sender_thread is None or not _sender_thread.is_alive():
        _thread_stop_event.clear()
        _sender_thread = threading.Thread(target=_background_sender_thread, daemon=True)
        _sender_thread.start()


def stop_background_thread():
    """Stop the background sender thread."""
    global _sender_thread

    if _sender_thread and _sender_thread.is_alive():
        logger.debug("Stopping background sender thread")
        _thread_stop_event.set()
        _sender_thread.join(timeout=5.0)
        _sender_thread = None

        # Process any remaining items in the queue
        while not _event_queue.empty():
            try:
                endpoint, http_method, timeout, event = _event_queue.get(block=False)
                client = ApiClient(endpoint, http_method)
                client._send_event_direct(endpoint, http_method, timeout, event)
                _event_queue.task_done()
            except:
                break


def get_api_client() -> ApiClient:
    """Get an API client with the default configuration.

    Returns:
        ApiClient: The configured API client
    """
    return ApiClient()


def send_event_to_api(event: Dict[str, Any]) -> bool:
    """Send an event to the API.

    Args:
        event: The event to send

    Returns:
        bool: True if event was sent successfully
    """
    # Mask sensitive data in the event before sending
    scanner = SecurityScanner.get_instance()
    masked_event = scanner.mask_event(event)
    
    # If masking didn't occur, use the original event
    if masked_event is None:
        masked_event = event
    
    # Create client
    client = ApiClient()
    
    # Send event
    return client.send_event(masked_event)


def send_event_to_api_legacy(
    agent_id: str,
    event_type: str,
    data: Dict[str, Any],
    channel: str = "SYSTEM",
    level: str = "info",
    timestamp: Optional[datetime] = None,
    direction: Optional[str] = None,
) -> bool:
    """Send an event to the API using the legacy format.

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
        timestamp = get_utc_timestamp()

    # Create the event payload in the new format
    event = {
        "timestamp": format_timestamp(timestamp),
        "agent_id": agent_id,
        "name": event_type.lower().replace("_", "."),
        "level": level.upper(),
        "attributes": {**data, "source": channel.upper()},
    }

    # Add direction if provided
    if direction:
        event["attributes"]["direction"] = direction

    # Send the event
    return send_event_to_api(event)
