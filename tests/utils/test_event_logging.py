"""Test event logging functionality."""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock

from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.event_context import set_context, clear_context, ContextManager


class TestEventLogging(unittest.TestCase):
    """Test case for event logging module."""
    
    def setUp(self):
        """Set up test fixture."""
        # Create a temporary log file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()
        
        # Set up config manager mock
        self.config_patcher = patch('cylestio_monitor.utils.event_logging.ConfigManager')
        self.mock_config_manager = self.config_patcher.start()
        self.mock_config_instance = MagicMock()
        self.mock_config_manager.return_value = self.mock_config_instance
        self.mock_config_instance.get.return_value = self.temp_file.name
        
        # Patch trace context
        self.trace_patcher = patch('cylestio_monitor.utils.event_logging.TraceContext')
        self.mock_trace = self.trace_patcher.start()
        self.mock_trace.get_current_context.return_value = {
            "trace_id": "test-trace-123",
            "span_id": "test-span-456",
            "agent_id": "test-agent-789"
        }
        
        # Patch API client
        self.api_patcher = patch('cylestio_monitor.utils.event_logging.send_event_to_api')
        self.mock_api = self.api_patcher.start()
        
        # Clear event context
        clear_context()
    
    def tearDown(self):
        """Tear down test fixture."""
        # Stop patches
        self.config_patcher.stop()
        self.trace_patcher.stop()
        self.api_patcher.stop()
        
        # Delete temp file
        try:
            os.unlink(self.temp_file.name)
        except Exception:
            pass
        
        # Clear event context
        clear_context()
    
    def test_log_event_basic(self):
        """Test basic event logging."""
        event = log_event(
            name="test.event",
            attributes={"test.attribute": "test_value"}
        )
        
        # Check basic fields
        self.assertEqual(event["name"], "test.event")
        self.assertEqual(event["level"], "INFO")
        self.assertEqual(event["trace_id"], "test-trace-123")
        self.assertEqual(event["span_id"], "test-span-456")
        self.assertEqual(event["agent_id"], "test-agent-789")
        self.assertEqual(event["attributes"]["test.attribute"], "test_value")
        
        # Check schema version
        self.assertEqual(event["schema_version"], "1.0")
        
        # Check the event was written to the file
        with open(self.temp_file.name, 'r') as f:
            logged_event = json.loads(f.read())
        
        self.assertEqual(logged_event["name"], "test.event")
        self.assertEqual(logged_event["level"], "INFO")
        
        # Check API was called
        self.mock_api.assert_called_once()
    
    def test_log_event_with_context(self):
        """Test event logging with context."""
        # Set context values
        set_context("user.id", "test-user-123")
        set_context("environment", "testing")
        
        event = log_event(
            name="test.context_event",
            attributes={"test.attribute": "test_value"}
        )
        
        # Check context values were added to attributes
        self.assertEqual(event["attributes"]["user.id"], "test-user-123")
        self.assertEqual(event["attributes"]["environment"], "testing")
        self.assertIn("session.id", event["attributes"])
    
    def test_log_event_with_context_manager(self):
        """Test event logging with context manager."""
        # Set initial context
        set_context("user.id", "default-user")
        
        # Log event with temporary context
        with ContextManager(request_id="temp-request", operation="test-op"):
            event = log_event(
                name="test.context_manager_event",
                attributes={"test.attribute": "test_value"}
            )
            
            # Check temporary context values were added
            self.assertEqual(event["attributes"]["request_id"], "temp-request")
            self.assertEqual(event["attributes"]["operation"], "test-op")
            self.assertEqual(event["attributes"]["user.id"], "default-user")
    
    def test_log_error(self):
        """Test error event logging."""
        # Create an exception
        try:
            raise ValueError("Test error message")
        except ValueError as e:
            error = e
        
        # Log error event
        event = log_error(
            name="test.error",
            error=error,
            attributes={"source": "test_case"}
        )
        
        # Check error fields
        self.assertEqual(event["name"], "test.error")
        self.assertEqual(event["level"], "ERROR")
        self.assertEqual(event["attributes"]["error.type"], "ValueError")
        self.assertEqual(event["attributes"]["error.message"], "Test error message")
        self.assertEqual(event["attributes"]["source"], "test_case")
    
    def test_log_event_disabled_context(self):
        """Test event logging with context disabled."""
        # Set context values
        set_context("user.id", "test-user-123")
        
        event = log_event(
            name="test.no_context_event",
            attributes={"test.attribute": "test_value"},
            add_thread_context=False
        )
        
        # Check context values were NOT added to attributes
        self.assertNotIn("user.id", event["attributes"])
        self.assertIn("session.id", event["attributes"])  # Session ID always added


if __name__ == "__main__":
    unittest.main() 