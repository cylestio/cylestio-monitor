"""Unit tests for the API client module."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cylestio_monitor.api_client import ApiClient, get_api_client, send_event_to_api


class TestApiClientUnit(unittest.TestCase):
    """Unit tests for the API client module."""

    def setUp(self):
        """Set up test environment."""
        # Clear environment variable to ensure clean test environment
        if "CYLESTIO_API_ENDPOINT" in os.environ:
            self.old_endpoint = os.environ["CYLESTIO_API_ENDPOINT"]
            del os.environ["CYLESTIO_API_ENDPOINT"]
        else:
            self.old_endpoint = None
        
        # Reset global client instance
        import cylestio_monitor.api_client
        cylestio_monitor.api_client._api_client = None
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore environment variable if it existed
        if self.old_endpoint is not None:
            os.environ["CYLESTIO_API_ENDPOINT"] = self.old_endpoint
        elif "CYLESTIO_API_ENDPOINT" in os.environ:
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
        # Clear any existing environment variables
        if "CYLESTIO_API_ENDPOINT" in os.environ:
            del os.environ["CYLESTIO_API_ENDPOINT"]
            
        client = ApiClient()
        # Default local endpoint is now expected instead of None
        self.assertEqual(client.endpoint, "http://127.0.0.1:8000/")
    
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
        event_data = {"test_key": "test_value"}
        result = client.send_event(event_data)
        
        # Assert the result is True (success)
        self.assertTrue(result)
        
        # Assert the post call was made correctly
        mock_post.assert_called_once_with(
            "https://example.com/api/events",
            json=event_data,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
    
    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event_failure_response(self, mock_post):
        """Test handling a failed response when sending an event."""
        # Set up mock response with failure
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        # Create client with endpoint
        client = ApiClient("https://example.com/api/events")
        
        # Test sending an event
        result = client.send_event({"test_key": "test_value"})
        
        # Assert the result is False (failure)
        self.assertFalse(result)
    
    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event_exception(self, mock_post):
        """Test sending an event when an exception occurs."""
        # Set up the mock post to raise an exception
        mock_post.side_effect = Exception("Test connection error")
        
        # Create client with endpoint
        client = ApiClient("https://example.com/api/events")
        
        # Test sending an event - should handle the exception and return False
        result = client.send_event({"test_key": "test_value"})
        
        # Assert the result is False (failure)
        self.assertFalse(result)
    
    def test_send_event_no_endpoint(self):
        """Test sending an event when no endpoint is configured."""
        # For consistency with the codebase, we'll test what happens when
        # we attempt to send an event to an invalid endpoint instead
        with patch("cylestio_monitor.api_client.requests.post") as mock_post:
            # Setup the mock to simulate a connection error
            mock_post.side_effect = Exception("Connection refused")
            
            # Create client with the default endpoint
            client = ApiClient()
            
            # Test sending an event
            result = client.send_event({"test_key": "test_value"})
            
            # Assert the result is False (failure) when the connection fails
            self.assertFalse(result)
    
    def test_get_api_client_singleton(self):
        """Test that get_api_client returns a singleton instance."""
        # Set endpoint in environment variable
        os.environ["CYLESTIO_API_ENDPOINT"] = "https://example.com/api/events"
        
        # Get client instance
        client1 = get_api_client()
        
        # Get another client instance
        client2 = get_api_client()
        
        # Assert they are the same instance
        self.assertIs(client1, client2)
        
        # Assert the endpoint is correct
        self.assertEqual(client1.endpoint, "https://example.com/api/events")
    
    @patch("cylestio_monitor.api_client.ApiClient")
    def test_get_api_client_creation(self, mock_api_client):
        """Test that get_api_client creates a new client when needed."""
        # Set up mock
        mock_instance = MagicMock()
        mock_api_client.return_value = mock_instance
        
        # Reset global instance
        import cylestio_monitor.api_client
        cylestio_monitor.api_client._api_client = None
        
        # Get client instance
        client = get_api_client()
        
        # Assert that ApiClient constructor was called
        mock_api_client.assert_called_once()
        
        # Assert the returned client is the mock instance
        self.assertIs(client, mock_instance)
    
    @patch("cylestio_monitor.api_client.get_api_client")
    def test_send_event_to_api(self, mock_get_client):
        """Test the send_event_to_api function."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.send_event.return_value = True
        mock_get_client.return_value = mock_client
        
        # Current time for testing
        now = datetime.now()
        
        # Test sending an event
        result = send_event_to_api(
            agent_id="test-agent",
            event_type="test-event",
            data={"content": "This is a test event"},
            channel="TEST",
            level="info",
            timestamp=now,
            direction="incoming"
        )
        
        # Assert the result is True (success)
        self.assertTrue(result)
        
        # Assert get_api_client was called
        mock_get_client.assert_called_once()
        
        # Assert send_event was called on the client
        mock_client.send_event.assert_called_once()
        
        # Get the event argument
        event = mock_client.send_event.call_args[0][0]
        
        # Assert the event structure is correct
        self.assertEqual(event["agent_id"], "test-agent")
        self.assertEqual(event["event_type"], "test-event")
        self.assertEqual(event["channel"], "TEST")
        self.assertEqual(event["level"], "INFO")
        self.assertEqual(event["data"], {"content": "This is a test event"})
        self.assertEqual(event["direction"], "incoming")
        self.assertEqual(event["timestamp"], now.isoformat())
    
    @patch("cylestio_monitor.api_client.get_api_client")
    def test_send_event_to_api_default_timestamp(self, mock_get_client):
        """Test that send_event_to_api creates a timestamp if none is provided."""
        # Set up mock client
        mock_client = MagicMock()
        mock_client.send_event.return_value = True
        mock_get_client.return_value = mock_client
        
        # Test sending an event without timestamp
        send_event_to_api(
            agent_id="test-agent",
            event_type="test-event",
            data={"content": "This is a test event"},
            channel="TEST",
            level="info"
        )
        
        # Get the event argument
        event = mock_client.send_event.call_args[0][0]
        
        # Assert timestamp is present
        self.assertIn("timestamp", event)
        # Assert timestamp is a string in ISO format (roughly)
        self.assertIsInstance(event["timestamp"], str)
        self.assertGreater(len(event["timestamp"]), 10)
        self.assertIn("T", event["timestamp"])


if __name__ == "__main__":
    unittest.main() 