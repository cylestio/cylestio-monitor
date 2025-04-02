"""
Tests for LangChain callback handler for tool monitoring.
"""

import logging
import time
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

# Import the module to test
from cylestio_monitor.patchers.langchain_callbacks import (
    ToolMonitorCallbackHandler,
    get_callback_handler
)

# Define mock classes for testing
class MockTool:
    """Mock tool for testing."""
    
    def __init__(self, name: str = "test_tool"):
        self.name = name
        self.description = f"Test tool named {name}"
    
    def __call__(self, input_str: str):
        """Execute the tool."""
        return f"Output from {self.name} with input {input_str}"


class TestToolMonitorCallbackHandler(unittest.TestCase):
    """Tests for the ToolMonitorCallbackHandler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock trace context and logging
        self.trace_context_patch = patch("cylestio_monitor.patchers.langchain_callbacks.TraceContext")
        self.mock_trace_context = self.trace_context_patch.start()
        
        # Set up trace context mock
        self.mock_trace_context.start_span.return_value = {
            "span_id": "test-span-id",
            "trace_id": "test-trace-id",
            "parent_span_id": None,
            "name": "tool.test_tool"
        }
        self.mock_trace_context.get_current_context.return_value = {
            "span_id": "test-span-id",
            "trace_id": "test-trace-id",
            "agent_id": "test-agent-id"
        }
        
        self.log_event_patch = patch("cylestio_monitor.patchers.langchain_callbacks.log_event")
        self.mock_log_event = self.log_event_patch.start()
        
        self.log_error_patch = patch("cylestio_monitor.patchers.langchain_callbacks.log_error")
        self.mock_log_error = self.log_error_patch.start()
        
        # Create handler instance
        self.handler = ToolMonitorCallbackHandler()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.trace_context_patch.stop()
        self.log_event_patch.stop()
        self.log_error_patch.stop()
    
    def test_initialization(self):
        """Test that the handler initializes correctly."""
        self.assertEqual(self.handler.active_tool_runs, {})
        self.assertIsNotNone(self.handler.initialization_ts)
        
    def test_is_available(self):
        """Test the _is_available method."""
        with patch("cylestio_monitor.patchers.langchain_callbacks.HAS_LANGCHAIN", True):
            self.assertTrue(self.handler._is_available())
        
        with patch("cylestio_monitor.patchers.langchain_callbacks.HAS_LANGCHAIN", False):
            self.assertFalse(self.handler._is_available())
    
    def test_start_tool_span(self):
        """Test the _start_tool_span method."""
        tool_name = "test_tool"
        tool_input = "test_input"
        
        # Call the method
        result = self.handler._start_tool_span(tool_name, tool_input)
        
        # Check that TraceContext.start_span was called with the correct arguments
        self.mock_trace_context.start_span.assert_called_once_with(f"tool.{tool_name}")
        
        # Check that the span was tracked in active_tool_runs
        self.assertEqual(len(self.handler.active_tool_runs), 1)
        self.assertIn("test-span-id", self.handler.active_tool_runs)
        tracked_run = self.handler.active_tool_runs["test-span-id"]
        self.assertEqual(tracked_run["tool_name"], tool_name)
        self.assertEqual(tracked_run["tool_input"], tool_input)
        
        # Check return value
        self.assertEqual(result, self.mock_trace_context.start_span.return_value)
    
    def test_end_tool_span(self):
        """Test the _end_tool_span method."""
        # Set up an active tool run
        span_id = "test-span-id"
        tool_name = "test_tool"
        tool_input = "test_input"
        self.handler.active_tool_runs[span_id] = {
            "start_time": time.time() - 1,  # 1 second ago
            "tool_name": tool_name,
            "tool_input": tool_input,
            "span_info": {
                "span_id": span_id,
                "trace_id": "test-trace-id",
                "parent_span_id": None,
                "name": f"tool.{tool_name}"
            }
        }
        
        # Call the method with a successful output
        output = "test_output"
        self.handler._end_tool_span(span_id, output=output)
        
        # Check that the tool run was removed from active_tool_runs
        self.assertEqual(len(self.handler.active_tool_runs), 0)
        
        # Check that TraceContext.end_span was called
        self.mock_trace_context.end_span.assert_called_once()
    
    def test_on_tool_start(self):
        """Test the on_tool_start method."""
        # Mock LangChain availability
        with patch("cylestio_monitor.patchers.langchain_callbacks.HAS_LANGCHAIN", True):
            # Set up a serialized tool
            tool_name = "test_tool"
            tool_input = "test_input"
            serialized = {"name": tool_name}
            
            # Call the method
            self.handler.on_tool_start(serialized, tool_input)
            
            # Check that _start_tool_span was called (indirectly through TraceContext.start_span)
            self.mock_trace_context.start_span.assert_called_once_with(f"tool.{tool_name}")
            
            # Check that log_event was called
            self.mock_log_event.assert_called_once()
            call_args = self.mock_log_event.call_args[1]
            self.assertEqual(call_args["name"], "tool.start")
            self.assertEqual(call_args["attributes"]["tool.name"], tool_name)
            self.assertEqual(call_args["attributes"]["tool.input"], tool_input)
            self.assertEqual(call_args["attributes"]["tool.type"], "langchain")
    
    def test_on_tool_end(self):
        """Test the on_tool_end method."""
        # Mock LangChain availability
        with patch("cylestio_monitor.patchers.langchain_callbacks.HAS_LANGCHAIN", True):
            # Set up an active tool run
            span_id = "test-span-id"
            tool_name = "test_tool"
            tool_input = "test_input"
            self.handler.active_tool_runs[span_id] = {
                "start_time": time.time() - 1,  # 1 second ago
                "tool_name": tool_name,
                "tool_input": tool_input,
                "span_info": {
                    "span_id": span_id,
                    "trace_id": "test-trace-id",
                    "parent_span_id": None,
                    "name": f"tool.{tool_name}"
                }
            }
            
            # Call the method
            output = "test_output"
            self.handler.on_tool_end(output)
            
            # Check that log_event was called
            self.mock_log_event.assert_called_once()
            call_args = self.mock_log_event.call_args[1]
            self.assertEqual(call_args["name"], "tool.end")
            self.assertEqual(call_args["attributes"]["tool.name"], tool_name)
            self.assertEqual(call_args["attributes"]["tool.output"], output)
            self.assertEqual(call_args["attributes"]["tool.status"], "success")
    
    def test_on_tool_error(self):
        """Test the on_tool_error method."""
        # Mock LangChain availability
        with patch("cylestio_monitor.patchers.langchain_callbacks.HAS_LANGCHAIN", True):
            # Set up an active tool run
            span_id = "test-span-id"
            tool_name = "test_tool"
            tool_input = "test_input"
            self.handler.active_tool_runs[span_id] = {
                "start_time": time.time() - 1,  # 1 second ago
                "tool_name": tool_name,
                "tool_input": tool_input,
                "span_info": {
                    "span_id": span_id,
                    "trace_id": "test-trace-id",
                    "parent_span_id": None,
                    "name": f"tool.{tool_name}"
                }
            }
            
            # Call the method
            error = ValueError("Test error")
            self.handler.on_tool_error(error)
            
            # Check that log_error was called
            self.mock_log_error.assert_called_once()
            call_args = self.mock_log_error.call_args[1]
            self.assertEqual(call_args["name"], "tool.error")
            self.assertEqual(call_args["error"], error)
            self.assertEqual(call_args["attributes"]["tool.name"], tool_name)
            self.assertEqual(call_args["attributes"]["tool.status"], "error")
            self.assertEqual(call_args["attributes"]["error.type"], "ValueError")
    
    def test_async_methods(self):
        """Test the async versions of the callback methods."""
        # Mock synchronous methods
        self.handler.on_tool_start = MagicMock()
        self.handler.on_tool_end = MagicMock()
        self.handler.on_tool_error = MagicMock()
        
        # Call async methods
        import asyncio
        
        # Set up inputs
        serialized = {"name": "test_tool"}
        input_str = "test_input"
        output = "test_output"
        error = ValueError("Test error")
        
        # Run the async methods
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(self.handler.async_on_tool_start(serialized, input_str))
        loop.run_until_complete(self.handler.async_on_tool_end(output))
        loop.run_until_complete(self.handler.async_on_tool_error(error))
        
        # Check that the synchronous methods were called
        self.handler.on_tool_start.assert_called_once_with(serialized, input_str)
        self.handler.on_tool_end.assert_called_once_with(output)
        self.handler.on_tool_error.assert_called_once_with(error)
        
        loop.close()
    
    def test_get_callback_handler(self):
        """Test the get_callback_handler function."""
        # Clear the singleton
        import cylestio_monitor.patchers.langchain_callbacks
        cylestio_monitor.patchers.langchain_callbacks._callback_handler_instance = None
        
        # Get an instance
        handler1 = get_callback_handler()
        
        # Get another instance
        handler2 = get_callback_handler()
        
        # They should be the same object
        self.assertIs(handler1, handler2)


if __name__ == "__main__":
    unittest.main() 