"""
Tests for the Core Architecture Components.

This module tests the new core architecture components:
- TraceContext
- Event Logging
- Basic Instrumentation
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, call, ANY
import time

from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_logging import log_event, log_error
from cylestio_monitor.utils.instrumentation import (
    instrument_function, 
    instrument_method,
    Span
)
from cylestio_monitor.config import ConfigManager


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
        self.assertIn("parent_span_id", span_info)
        self.assertIn("trace_id", span_info)
        self.assertIn("name", span_info)
        
        # Parent should be None for the first span
        self.assertIsNone(span_info["parent_span_id"])
        
        # Start a child span
        child_span = TraceContext.start_span("child-span")
        
        # Parent should be the first span
        self.assertEqual(child_span["parent_span_id"], span_info["span_id"])
    
    def test_end_span(self):
        """Test ending a span."""
        agent_id = "test-agent"
        TraceContext.initialize_trace(agent_id)
        
        # Start two spans
        first_span = TraceContext.start_span("first-span")
        second_span = TraceContext.start_span("second-span")
        
        # End the second span
        ended_span_id = TraceContext.end_span()
        
        # Should return the ID of the ended span
        self.assertEqual(ended_span_id, second_span["span_id"])
        
        # Current span should now be the first span
        context = TraceContext.get_current_context()
        self.assertEqual(context["span_id"], first_span["span_id"])
        
        # End the first span
        ended_span_id = TraceContext.end_span()
        self.assertEqual(ended_span_id, first_span["span_id"])
        
        # No spans should be active
        context = TraceContext.get_current_context()
        self.assertIsNone(context["span_id"])


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
        event = log_event(
            name="test.event",
            attributes={"test_key": "test_value"},
            level="INFO"
        )
        
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
        
        # Verify the mock functions were called
        mock_write_to_log_file.assert_called_once_with(event)
        mock_send_to_api.assert_called_once_with(event)
    
    @patch("cylestio_monitor.utils.event_logging.log_event")
    def test_log_error(self, mock_log_event):
        """Test logging an error event."""
        # Configure the mock
        mock_event = {
            "name": "test.error",
            "level": "ERROR",
            "attributes": {
                "error.type": "ValueError",
                "error.message": "Test error message",
                "test_key": "test_value"
            }
        }
        mock_log_event.return_value = mock_event
        
        # Create a test exception
        test_exception = ValueError("Test error message")
        
        # Log an error event
        event = log_error(
            name="test.error",
            error=test_exception,
            attributes={"test_key": "test_value"}
        )
        
        # Verify the error attributes
        self.assertEqual(event["name"], "test.error")
        self.assertEqual(event["level"], "ERROR")
        self.assertEqual(event["attributes"]["error.type"], "ValueError")
        self.assertEqual(event["attributes"]["error.message"], "Test error message")
        self.assertEqual(event["attributes"]["test_key"], "test_value")
        
        # Verify log_event was called with correct arguments
        mock_log_event.assert_called_once_with(
            name="test.error",
            attributes={
                "error.type": "ValueError",
                "error.message": "Test error message",
                "test_key": "test_value"
            },
            level="ERROR"
        )


class TestInstrumentation(unittest.TestCase):
    """Test the Basic Instrumentation utilities."""
    
    def setUp(self):
        """Set up the test case."""
        TraceContext.reset()
        TraceContext.initialize_trace("test-agent")
    
    @patch("cylestio_monitor.utils.instrumentation.log_event")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.start_span")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.end_span")
    def test_instrument_function(self, mock_end_span, mock_start_span, mock_log_event):
        """Test instrumenting a function."""
        # Configure mocks
        mock_start_span.return_value = {
            "span_id": "test-span-id",
            "parent_span_id": None,
            "trace_id": "test-trace-id",
            "name": "function.test_function"
        }
        mock_end_span.return_value = "test-span-id"
        
        # Create a test function
        @instrument_function
        def test_function(x, y):
            return x + y
        
        # Call the function
        result = test_function(3, 4)
        
        # Function should work normally
        self.assertEqual(result, 7)
        
        # Verify start_span was called
        mock_start_span.assert_called_once()
        
        # Verify end_span was called
        mock_end_span.assert_called_once()
        
        # Verify log_event was called twice (start and end)
        self.assertEqual(mock_log_event.call_count, 2)
        
        # Check that the first call was for function.start
        self.assertEqual(mock_log_event.call_args_list[0][1]["name"], "function.start")
        
        # Check that the second call was for function.end with success status
        self.assertEqual(mock_log_event.call_args_list[1][1]["name"], "function.end")
        self.assertEqual(mock_log_event.call_args_list[1][1]["attributes"]["function.status"], "success")
    
    @patch("cylestio_monitor.utils.instrumentation.log_event")
    @patch("cylestio_monitor.utils.instrumentation.log_error")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.start_span")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.end_span")
    def test_instrument_function_error(self, mock_end_span, mock_start_span, mock_log_error, mock_log_event):
        """Test instrumenting a function that raises an error."""
        # Configure mocks
        mock_start_span.return_value = {
            "span_id": "test-span-id",
            "parent_span_id": None,
            "trace_id": "test-trace-id",
            "name": "function.error_function"
        }
        mock_end_span.return_value = "test-span-id"
        
        # Create a test function that raises an error
        @instrument_function
        def error_function():
            raise ValueError("Test error")
        
        # Call the function
        with self.assertRaises(ValueError):
            error_function()
        
        # Verify start_span was called
        mock_start_span.assert_called_once()
        
        # Verify end_span was called
        mock_end_span.assert_called_once()
        
        # Verify log_event was called once (for start)
        self.assertEqual(mock_log_event.call_count, 1)
        self.assertEqual(mock_log_event.call_args[1]["name"], "function.start")
        
        # Verify log_error was called once
        mock_log_error.assert_called_once()
        error_call_args = mock_log_error.call_args[1]
        self.assertEqual(error_call_args["name"], "function.error")
        self.assertIsInstance(error_call_args["error"], ValueError)
        self.assertEqual(str(error_call_args["error"]), "Test error")
        self.assertEqual(error_call_args["attributes"]["function.status"], "error")
    
    @patch("cylestio_monitor.utils.instrumentation.log_event")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.start_span")
    @patch("cylestio_monitor.utils.instrumentation.TraceContext.end_span")
    def test_span_context_manager(self, mock_end_span, mock_start_span, mock_log_event):
        """Test using the Span context manager."""
        # Configure mocks
        mock_start_span.return_value = {
            "span_id": "test-span-id",
            "parent_span_id": None,
            "trace_id": "test-trace-id",
            "name": "test-operation"
        }
        mock_end_span.return_value = "test-span-id"
        
        # Use the Span context manager
        with Span("test-operation", attributes={"test_key": "test_value"}):
            # Do something
            time.sleep(0.01)
        
        # Verify start_span was called
        mock_start_span.assert_called_once_with("test-operation")
        
        # Verify end_span was called
        mock_end_span.assert_called_once()
        
        # Verify log_event was called twice (start and end)
        self.assertEqual(mock_log_event.call_count, 2)
        
        # Check the calls to log_event
        calls = [
            call(
                name="test-operation.start",
                attributes={"test_key": "test_value"}
            ),
            call(
                name="test-operation.end",
                attributes=ANY
            )
        ]
        mock_log_event.assert_has_calls(calls)
        
        # Verify status and duration_ms are in the attributes
        end_call_attrs = mock_log_event.call_args_list[1][1]["attributes"]
        self.assertEqual(end_call_attrs["status"], "success")
        self.assertIn("duration_ms", end_call_attrs)


if __name__ == "__main__":
    unittest.main() 