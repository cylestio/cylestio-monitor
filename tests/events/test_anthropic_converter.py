"""
Tests for the Anthropic event converter.

This module contains tests for verifying the correct behavior of the Anthropic event converter.
"""

import unittest
from datetime import datetime

from cylestio_monitor.events.converters.anthropic import AnthropicEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestAnthropicConverter(unittest.TestCase):
    """Test case for the Anthropic event converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = AnthropicEventConverter()
        
        # Create sample events for testing
        self.request_event = {
            "timestamp": "2025-03-17T14:08:09.925710",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "model_request",
            "channel": "ANTHROPIC",
            "direction": "outgoing",
            "session_id": "anthropic-1742216889.9256918",
            "data": {
                "model": "claude-3-haiku-20240307",
                "messages": [
                    {"role": "system", "content": "You are a helpful AI assistant."},
                    {"role": "user", "content": "Hello, can you help me?"}
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 10, "function": "test_func"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "anthropic",
                    "version": "0.8.1"
                },
                "performance": {"timestamp": "2025-03-17T14:08:09.927911"}
            }
        }
        
        self.response_event = {
            "timestamp": "2025-03-17T14:08:11.006702",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "model_response",
            "channel": "ANTHROPIC",
            "direction": "incoming",
            "session_id": "anthropic-1742216889.9256918",
            "data": {
                "completion": "I'm Claude, an AI assistant. How can I help you today?",
                "model": "claude-3-haiku-20240307",
                "stop_reason": "end_turn",
                "usage": {
                    "input_tokens": 29,
                    "output_tokens": 13
                },
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 20, "function": "test_response"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "anthropic",
                    "version": "0.8.1"
                },
                "performance": {"duration_ms": "1080.8489322662354"}
            }
        }
        
    def test_convert_request_event(self):
        """Test conversion of an Anthropic request event."""
        # Convert the event
        standardized = self.converter.convert(self.request_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.925710")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_request")
        self.assertEqual(standardized.channel, "ANTHROPIC")
        self.assertEqual(standardized.direction, "outgoing")
        self.assertEqual(standardized.session_id, "anthropic-1742216889.9256918")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that request data was extracted
        self.assertIsNotNone(standardized.request)
        self.assertIn("messages", standardized.request)
        self.assertEqual(len(standardized.request["messages"]), 2)
        self.assertEqual(standardized.request["max_tokens"], 1000)
        self.assertEqual(standardized.request["temperature"], 0.7)
        
        # Check that framework info was extracted
        self.assertEqual(standardized.framework.get("name"), "anthropic")
        self.assertEqual(standardized.framework.get("version"), "0.8.1")
        
        # Check that model info was extracted
        self.assertEqual(standardized.model.get("name"), "claude-3-haiku-20240307")
        self.assertEqual(standardized.model.get("type"), "completion")
        
        # Check event category
        self.assertEqual(standardized.event_category, "llm_request")
        
    def test_convert_response_event(self):
        """Test conversion of an Anthropic response event."""
        # Convert the event
        standardized = self.converter.convert(self.response_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:11.006702")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_response")
        self.assertEqual(standardized.channel, "ANTHROPIC")
        self.assertEqual(standardized.direction, "incoming")
        self.assertEqual(standardized.session_id, "anthropic-1742216889.9256918")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that response data was extracted
        self.assertIsNotNone(standardized.response)
        self.assertIn("completion", standardized.response)
        self.assertEqual(standardized.response["completion"], "I'm Claude, an AI assistant. How can I help you today?")
        self.assertEqual(standardized.response["stop_reason"], "end_turn")
        
        # Check that performance metrics were extracted
        self.assertTrue("duration_ms" in standardized.performance)
        self.assertTrue("usage_input_tokens" in standardized.performance)
        self.assertTrue("usage_output_tokens" in standardized.performance)
        
        # Check event category
        self.assertEqual(standardized.event_category, "llm_response")
        
    def test_request_response_binding(self):
        """Test that request and response events are properly bound together."""
        # Convert both events
        request_standardized = self.converter.convert(self.request_event)
        response_standardized = self.converter.convert(self.response_event)
        
        # Check that they have the same trace ID
        self.assertEqual(request_standardized.trace_id, response_standardized.trace_id)
        
        # Check that they have the same session ID
        self.assertEqual(request_standardized.session_id, response_standardized.session_id)
        
        # Check that one is a request and one is a response based on direction
        self.assertEqual(request_standardized.direction, "outgoing")
        self.assertEqual(response_standardized.direction, "incoming")
        
        # Check categories
        self.assertEqual(request_standardized.event_category, "llm_request")
        self.assertEqual(response_standardized.event_category, "llm_response")


if __name__ == "__main__":
    unittest.main() 