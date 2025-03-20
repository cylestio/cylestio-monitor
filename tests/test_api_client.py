"""Tests for the API client module."""

import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from cylestio_monitor.api_client import ApiClient, get_api_client, send_event_to_api


class TestApiClient(unittest.TestCase):
    """Test the API client."""

    def setUp(self):
        """Set up the test environment."""
        # Clear environment variable to ensure clean test
        if "CYLESTIO_API_ENDPOINT" in os.environ:
            del os.environ["CYLESTIO_API_ENDPOINT"]

    def test_api_client_init_with_endpoint(self):
        """Test initializing the API client with an explicit endpoint."""
        client = ApiClient("https://example.com/api/events")
        self.assertEqual(client.endpoint, "https://example.com/api/events")

    def test_api_client_init_with_env_var(self):
        """Test initializing the API client with an environment variable."""
        os.environ["CYLESTIO_API_ENDPOINT"] = "https://example.com/api/events"
        client = ApiClient()
        self.assertEqual(client.endpoint, "https://example.com/api/events")

    def test_api_client_init_without_endpoint(self):
        """Test initializing the API client without an endpoint."""
        client = ApiClient()
        self.assertIsNone(client.endpoint)

    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event_success(self, mock_post):
        """Test sending an event successfully."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        # Create client with endpoint
        client = ApiClient("https://example.com/api/events")
        
        # Test sending an event
        result = client.send_event({"foo": "bar"})
        
        # Assert the result
        self.assertTrue(result)
        
        # Assert the post call
        mock_post.assert_called_once_with(
            "https://example.com/api/events",
            json={"foo": "bar"},
            headers={"Content-Type": "application/json"},
            timeout=5
        )

    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event_fail_response(self, mock_post):
        """Test sending an event with a failed response."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Create client with endpoint
        client = ApiClient("https://example.com/api/events")
        
        # Test sending an event
        result = client.send_event({"foo": "bar"})
        
        # Assert the result
        self.assertFalse(result)

    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event_exception(self, mock_post):
        """Test sending an event with an exception."""
        # Set up mock to raise an exception
        mock_post.side_effect = Exception("Connection error")
        
        # Create client with endpoint
        client = ApiClient("https://example.com/api/events")
        
        # Test sending an event
        result = client.send_event({"foo": "bar"})
        
        # Assert the result
        self.assertFalse(result)

    def test_send_event_no_endpoint(self):
        """Test sending an event without an endpoint."""
        # Create client without endpoint
        client = ApiClient()
        
        # Test sending an event
        result = client.send_event({"foo": "bar"})
        
        # Assert the result
        self.assertFalse(result)

    @patch("cylestio_monitor.api_client.get_api_client")
    def test_send_event_to_api(self, mock_get_client):
        """Test the send_event_to_api function."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.send_event.return_value = True
        mock_get_client.return_value = mock_client
        
        # Test sending an event
        result = send_event_to_api(
            agent_id="test-agent",
            event_type="test-event",
            data={"foo": "bar"},
            channel="TEST",
            level="info",
            direction="incoming"
        )
        
        # Assert the result
        self.assertTrue(result)
        
        # Assert the send_event call
        mock_client.send_event.assert_called_once()
        
        # Get the event argument
        event = mock_client.send_event.call_args[0][0]
        
        # Assert the event structure
        self.assertEqual(event["agent_id"], "test-agent")
        self.assertEqual(event["event_type"], "test-event")
        self.assertEqual(event["channel"], "TEST")
        self.assertEqual(event["level"], "INFO")
        self.assertEqual(event["direction"], "incoming")
        self.assertEqual(event["data"], {"foo": "bar"})

    @patch("cylestio_monitor.api_client._api_client", None)
    def test_get_api_client(self):
        """Test the get_api_client function."""
        # Set environment variable
        os.environ["CYLESTIO_API_ENDPOINT"] = "https://example.com/api/events"
        
        # Get client
        client = get_api_client()
        
        # Assert it's an ApiClient instance
        self.assertIsInstance(client, ApiClient)
        
        # Assert it has the right endpoint
        self.assertEqual(client.endpoint, "https://example.com/api/events")
        
        # Test that subsequent calls return the same instance
        client2 = get_api_client()
        self.assertIs(client, client2)


if __name__ == "__main__":
    unittest.main() 