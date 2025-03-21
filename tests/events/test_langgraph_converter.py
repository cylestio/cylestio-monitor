"""
Tests for the LangGraph event converter.

This module contains tests for verifying the correct behavior of the LangGraph event converter.
"""

import unittest
from datetime import datetime

from cylestio_monitor.events.converters.langgraph import LangGraphEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestLangGraphConverter(unittest.TestCase):
    """Test case for the LangGraph event converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = LangGraphEventConverter()
        
        # Create sample events for testing
        self.framework_patch_event = {
            "timestamp": "2025-03-17T14:08:09.920211",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "framework_patch",
            "channel": "LANGGRAPH",
            "data": {
                "framework": "langgraph",
                "version": "unknown",
                "patch_time": "2025-03-17T14:08:09.920206",
                "method": "monkey_patch",
                "note": "Using monkey patching as callbacks module is not available",
                "agent_id": "chatbot-agent",
                "call_stack": [
                    {"file": "test_file.py", "line": 10, "function": "test_func"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "performance": {"timestamp": "2025-03-17T14:08:09.920598"}
            }
        }
        
        self.graph_execution_event = {
            "timestamp": "2025-03-17T14:08:11.023456",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "graph_start",
            "channel": "LANGGRAPH",
            "data": {
                "graph_id": "test-graph-1",
                "node_id": "start-node",
                "node_type": "entry",
                "input": {"query": "What is AI?"},
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 20, "function": "test_graph"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "langgraph",
                    "version": "0.0.16"
                },
                "performance": {"timestamp": "2025-03-17T14:08:11.023456"}
            }
        }
        
        self.graph_end_event = {
            "timestamp": "2025-03-17T14:08:12.123456",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "graph_end",
            "channel": "LANGGRAPH",
            "data": {
                "graph_id": "test-graph-1",
                "node_id": "end-node",
                "node_type": "exit",
                "output": {"answer": "AI is artificial intelligence"},
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 25, "function": "test_graph_end"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "langgraph",
                    "version": "0.0.16"
                },
                "performance": {"duration_ms": "1100.0"}
            }
        }
        
    def test_convert_framework_patch_event(self):
        """Test conversion of a LangGraph framework patch event."""
        # Convert the event
        standardized = self.converter.convert(self.framework_patch_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.920211")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "framework_patch")
        self.assertEqual(standardized.channel, "LANGGRAPH")
        
        # Check that framework info was extracted
        self.assertEqual(standardized.framework.get("name"), "langgraph")
        self.assertEqual(standardized.framework.get("version"), "unknown")
        
        # Check that request data was extracted
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("method"), "monkey_patch")
        self.assertEqual(standardized.request.get("patch_time"), "2025-03-17T14:08:09.920206")
        self.assertEqual(standardized.request.get("note"), "Using monkey patching as callbacks module is not available")
        
        # Check that call stack was extracted
        self.assertEqual(len(standardized.call_stack), 1)
        self.assertEqual(standardized.call_stack[0].get("file"), "test_file.py")
        
        # Check event category (should be system since it's not a direct LLM interaction)
        self.assertEqual(standardized.event_category, "system")
        
    def test_convert_graph_execution_event(self):
        """Test conversion of a LangGraph execution event."""
        # Convert the event
        standardized = self.converter.convert(self.graph_execution_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:11.023456")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "graph_start")
        self.assertEqual(standardized.channel, "LANGGRAPH")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that framework info was extracted
        self.assertEqual(standardized.framework.get("name"), "langgraph")
        self.assertEqual(standardized.framework.get("version"), "0.0.16")
        
        # Check that graph specific data was extracted into request
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("graph_id"), "test-graph-1")
        self.assertEqual(standardized.request.get("node_id"), "start-node")
        self.assertEqual(standardized.request.get("node_type"), "entry")
        self.assertEqual(standardized.request.get("input"), {"query": "What is AI?"})
        
    def test_convert_graph_end_event(self):
        """Test conversion of a LangGraph end event."""
        # Convert the event
        standardized = self.converter.convert(self.graph_end_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:12.123456")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "graph_end")
        self.assertEqual(standardized.channel, "LANGGRAPH")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that graph specific data was extracted into response (since it's an end event)
        self.assertIsNotNone(standardized.response)
        self.assertEqual(standardized.response.get("graph_id"), "test-graph-1")
        self.assertEqual(standardized.response.get("node_id"), "end-node")
        self.assertEqual(standardized.response.get("node_type"), "exit")
        self.assertEqual(standardized.response.get("output"), {"answer": "AI is artificial intelligence"})
        
        # Check that performance metrics were extracted
        self.assertTrue("duration_ms" in standardized.performance)
        
    def test_execution_event_binding(self):
        """Test that start and end events are properly bound together by trace_id."""
        # Convert both events
        start_standardized = self.converter.convert(self.graph_execution_event)
        end_standardized = self.converter.convert(self.graph_end_event)
        
        # Check that they have the same trace ID
        self.assertEqual(start_standardized.trace_id, end_standardized.trace_id)
        
        # Check that graph_id is consistent between start and end events
        self.assertEqual(
            start_standardized.request.get("graph_id"),
            end_standardized.response.get("graph_id")
        )


if __name__ == "__main__":
    unittest.main() 