#!/usr/bin/env python3
"""
Simple demo script to test the API client functionality.
This script directly imports from the source directory to bypass installation issues.
"""

import os
import sys
from unittest.mock import patch, MagicMock

# Add the src directory to the path to import directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

# Import from source directory
from cylestio_monitor.api_client import ApiClient, send_event_to_api


def test_api_client():
    """Test the basic functionality of the API client."""
    # Create client with endpoint
    client = ApiClient("https://example.com/api/events")
    print(f"API client initialized with endpoint: {client.endpoint}")
    
    # Mock the requests.post method
    with patch("cylestio_monitor.api_client.requests.post") as mock_post:
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        # Send an event
        event_data = {"event_type": "test", "message": "Hello, API!"}
        result = client.send_event(event_data)
        
        # Check result
        print(f"Event sent successfully: {result}")
        print(f"Request URL: {mock_post.call_args[0][0]}")
        print(f"Request data: {mock_post.call_args[1]['json']}")


def test_send_event_to_api():
    """Test the high-level send_event_to_api function."""
    # Mock the API client
    with patch("cylestio_monitor.api_client.get_api_client") as mock_get_client:
        # Set up mock client
        mock_client = MagicMock()
        mock_client.send_event.return_value = True
        mock_get_client.return_value = mock_client
        
        # Send an event using the high-level function
        print("Testing send_event_to_api function...")
        result = send_event_to_api(
            agent_id="test-agent",
            event_type="test-event",
            data={"content": "This is a test event"},
            channel="TEST",
            level="info"
        )
        
        # Check result
        print(f"Event sent successfully: {result}")
        
        # Get the event argument
        event = mock_client.send_event.call_args[0][0]
        
        # Display the event structure
        print(f"Event agent_id: {event['agent_id']}")
        print(f"Event type: {event['event_type']}")
        print(f"Event channel: {event['channel']}")
        print(f"Event level: {event['level']}")
        print(f"Event data: {event['data']}")


if __name__ == "__main__":
    print("=== Testing API Client ===")
    test_api_client()
    print("\n=== Testing send_event_to_api Function ===")
    test_send_event_to_api()
    print("\nAll tests completed successfully!") 