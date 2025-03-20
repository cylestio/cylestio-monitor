"""Simple tests for the API client."""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the src directory to the path so we can import the modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import the api_client module directly from the source
from cylestio_monitor.api_client import ApiClient


class TestApiClient(unittest.TestCase):
    """Simple tests for the API client."""

    def test_api_client_init(self):
        """Test initializing the API client with an explicit endpoint."""
        client = ApiClient("https://example.com/api/events")
        self.assertEqual(client.endpoint, "https://example.com/api/events")

    @patch("cylestio_monitor.api_client.requests.post")
    def test_send_event(self, mock_post):
        """Test sending an event."""
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


if __name__ == "__main__":
    unittest.main() 