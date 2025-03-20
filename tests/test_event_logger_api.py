"""Integration tests for the event logger with API client."""

import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from cylestio_monitor.event_logger import log_to_db, process_and_log_event
from cylestio_monitor.api_client import ApiClient, send_event_to_api


class TestEventLoggerWithApi(unittest.TestCase):
    """Test the integration of event logger with the API client."""

    def setUp(self):
        """Set up the test environment."""
        # Clear environment variable to ensure clean test
        if "CYLESTIO_API_ENDPOINT" in os.environ:
            del os.environ["CYLESTIO_API_ENDPOINT"]
            
        # Set up the API endpoint for tests
        os.environ["CYLESTIO_API_ENDPOINT"] = "https://example.com/api/events"

    @patch("cylestio_monitor.api_client.requests.post")
    def test_log_to_db_sends_to_api(self, mock_post):
        """Test that log_to_db function sends events to the API."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        # Call the log_to_db function
        log_to_db(
            agent_id="test-agent",
            event_type="test-event",
            data={"foo": "bar"},
            channel="TEST",
            level="info",
            direction="incoming"
        )
        
        # Assert the post call
        mock_post.assert_called_once()
        
        # Get the API call arguments
        args, kwargs = mock_post.call_args
        
        # Assert the endpoint
        self.assertEqual(kwargs["json"]["agent_id"], "test-agent")
        self.assertEqual(kwargs["json"]["event_type"], "test-event")
        self.assertEqual(kwargs["json"]["channel"], "TEST")
        self.assertEqual(kwargs["json"]["level"], "INFO")
        self.assertEqual(kwargs["json"]["direction"], "incoming")
        self.assertEqual(kwargs["json"]["data"], {"foo": "bar", "session_id": kwargs["json"]["data"]["session_id"], "conversation_id": kwargs["json"]["data"]["conversation_id"]})

    @patch("cylestio_monitor.event_logger.log_to_file")
    @patch("cylestio_monitor.api_client.requests.post")
    def test_process_and_log_event(self, mock_post, mock_log_to_file):
        """Test that process_and_log_event function logs to both file and API."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        # Call the process_and_log_event function
        process_and_log_event(
            agent_id="test-agent",
            event_type="test-event",
            data={"foo": "bar"},
            channel="TEST",
            level="info"
        )
        
        # Assert log_to_file was called
        mock_log_to_file.assert_called_once()
        
        # Assert the post call
        mock_post.assert_called_once()
        
        # Get the API call arguments
        args, kwargs = mock_post.call_args
        
        # Assert the event properties
        self.assertEqual(kwargs["json"]["agent_id"], "test-agent")
        self.assertEqual(kwargs["json"]["event_type"], "test-event")
        self.assertEqual(kwargs["json"]["data"], {"foo": "bar", "session_id": kwargs["json"]["data"]["session_id"], "conversation_id": kwargs["json"]["data"]["conversation_id"]})

    @patch("cylestio_monitor.api_client.requests.post")
    def test_session_and_conversation_tracking(self, mock_post):
        """Test that session and conversation IDs are tracked correctly."""
        # Set up mock response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_post.return_value = mock_response
        
        # Call log_to_db multiple times
        log_to_db(
            agent_id="test-agent",
            event_type="test-event-1",
            data={"message": "first"},
            channel="TEST",
            level="info"
        )
        
        # Get the first call args
        first_call_kwargs = mock_post.call_args[1]
        first_session_id = first_call_kwargs["json"]["data"]["session_id"]
        first_conv_id = first_call_kwargs["json"]["data"]["conversation_id"]
        
        # Call again with the same agent
        log_to_db(
            agent_id="test-agent",
            event_type="test-event-2",
            data={"message": "second"},
            channel="TEST",
            level="info"
        )
        
        # Get the second call args
        second_call_kwargs = mock_post.call_args_list[1][1]
        second_session_id = second_call_kwargs["json"]["data"]["session_id"]
        second_conv_id = second_call_kwargs["json"]["data"]["conversation_id"]
        
        # Session ID should be the same for the same agent
        self.assertEqual(first_session_id, second_session_id)
        
        # Conversation ID should also be the same (no conversation end event)
        self.assertEqual(first_conv_id, second_conv_id)
        
        # Test that a new conversation is started
        log_to_db(
            agent_id="test-agent",
            event_type="conversation_start",
            data={"message": "new conversation"},
            channel="TEST",
            level="info"
        )
        
        # Get the third call args
        third_call_kwargs = mock_post.call_args_list[2][1]
        third_session_id = third_call_kwargs["json"]["data"]["session_id"]
        third_conv_id = third_call_kwargs["json"]["data"]["conversation_id"]
        
        # Session ID should be the same for the same agent
        self.assertEqual(first_session_id, third_session_id)
        
        # Conversation ID should be different after conversation_start
        self.assertNotEqual(second_conv_id, third_conv_id)


if __name__ == "__main__":
    unittest.main() 