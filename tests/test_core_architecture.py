"""
Tests for the Core Architecture Components.

This module tests the essential core architecture components for MVP:
- TraceContext
- Basic Event Logging
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from cylestio_monitor.config import ConfigManager
from cylestio_monitor.utils.event_logging import log_event
from cylestio_monitor.utils.trace_context import TraceContext


class TestTraceContext(unittest.TestCase):
    """Test the TraceContext class."""

    def setUp(self):
        """Set up the test case."""
        TraceContext.reset()

    def test_initialize_trace(self):
        """Test initializing a trace."""
        agent_id = "test-agent"
        trace_id = TraceContext.initialize_trace(agent_id)

        # Trace ID should be a 32-character hex string
        self.assertEqual(len(trace_id), 32)

        # Context should contain the agent ID
        context = TraceContext.get_current_context()
        self.assertEqual(context["agent_id"], agent_id)
        self.assertEqual(context["trace_id"], trace_id)
        self.assertIsNone(context["span_id"])

    def test_start_span(self):
        """Test starting a span."""
        agent_id = "test-agent"
        TraceContext.initialize_trace(agent_id)

        # Start a span
        span_info = TraceContext.start_span("test-span")

        # Span info should contain the expected fields
        self.assertIn("span_id", span_info)
        self.assertIn("trace_id", span_info)
        self.assertIn("name", span_info)


class TestEventLogging(unittest.TestCase):
    """Test the Event Logging utilities."""

    def setUp(self):
        """Set up the test case."""
        TraceContext.reset()
        TraceContext.initialize_trace("test-agent")

        # Create a temporary log file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test_log.json")

        # Configure logging to use the temporary file
        self.config_manager = ConfigManager()
        self.config_manager.set("monitoring.log_file", self.log_file)
        self.config_manager.save()

    def tearDown(self):
        """Clean up after the test."""
        self.temp_dir.cleanup()

    @patch("cylestio_monitor.utils.event_logging._write_to_log_file")
    @patch("cylestio_monitor.utils.event_logging._send_to_api")
    def test_log_event(self, mock_send_to_api, mock_write_to_log_file):
        """Test logging an event."""
        # Configure the mocks
        mock_send_to_api.return_value = None
        mock_write_to_log_file.return_value = None

        # Log an event
        event = log_event(name="test.event", attributes={"test_key": "test_value"}, level="INFO")

        # Event should have the expected fields
        self.assertIn("timestamp", event)
        self.assertIn("trace_id", event)
        self.assertIn("name", event)
        self.assertIn("level", event)
        self.assertIn("attributes", event)
        self.assertIn("agent_id", event)

        # Verify the event data
        self.assertEqual(event["name"], "test.event")
        self.assertEqual(event["level"], "INFO")
        self.assertEqual(event["attributes"]["test_key"], "test_value")


if __name__ == "__main__":
    unittest.main()
