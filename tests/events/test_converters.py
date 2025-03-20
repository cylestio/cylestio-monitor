"""
Tests for event converters.

This module contains tests for verifying the correct behavior of event converters.
"""

import unittest
from datetime import datetime

from cylestio_monitor.events.converters.langchain import LangChainEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestLangChainConverter(unittest.TestCase):
    """Test case for the LangChain event converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = LangChainEventConverter()
        
        # Create sample events for testing
        self.request_event = {
            "timestamp": "2025-03-17T14:08:09.925710",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "model_request",
            "channel": "LANGCHAIN",
            "direction": "outgoing",
            "session_id": "langchain-1742216889.9256918",
            "data": {
                "llm_type": "ChatAnthropic",
                "model": {
                    "name": "ChatAnthropic",
                    "type": "completion",
                    "provider": "None",
                    "metadata": {}
                },
                "prompts": ["System prompt", "User message"],
                "metadata": {},
                "run_id": "1742216889.9256918",
                "framework_version": "0.3.44",
                "components": {
                    "chain_type": "None",
                    "llm_type": "ChatAnthropic",
                    "tool_type": "None"
                },
                "session_id": "langchain-1742216889.9256918",
                "agent_id": "chatbot-agent",
                "call_stack": [
                    {"file": "test_file.py", "line": 10, "function": "test_func"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "langchain",
                    "version": "0.3.44",
                    "components": {}
                },
                "performance": {"timestamp": "2025-03-17T14:08:09.927911"}
            }
        }
        
        self.response_event = {
            "timestamp": "2025-03-17T14:08:11.006702",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "model_response",
            "channel": "LANGCHAIN",
            "direction": "incoming",
            "session_id": "langchain-1742216889.9256918",
            "data": {
                "response": {
                    "text": "Test response text",
                    "generation_info": None
                },
                "llm_output": {
                    "id": "msg_test",
                    "model": "claude-3-haiku-20240307",
                    "stop_reason": "end_turn",
                    "usage": {
                        "input_tokens": "29",
                        "output_tokens": "108"
                    }
                },
                "performance": {"duration_ms": "1080.8489322662354"},
                "run_id": "1742216889.9256918",
                "framework_version": "0.3.44",
                "components": {
                    "chain_type": "None",
                    "llm_type": "None",
                    "tool_type": "None"
                },
                "session_id": "langchain-1742216889.9256918",
                "agent_id": "chatbot-agent",
                "call_stack": [
                    {"file": "test_file.py", "line": 20, "function": "test_response"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "langchain",
                    "version": "0.3.44",
                    "components": {}
                }
            }
        }
        
    def test_convert_request_event(self):
        """Test conversion of a LangChain request event."""
        # Convert the event
        standardized = self.converter.convert(self.request_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.925710")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_request")
        self.assertEqual(standardized.channel, "LANGCHAIN")
        self.assertEqual(standardized.direction, "outgoing")
        self.assertEqual(standardized.session_id, "langchain-1742216889.9256918")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that request data was extracted
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("prompts"), ["System prompt", "User message"])
        
        # Check that framework info was extracted
        self.assertEqual(standardized.framework.get("name"), "langchain")
        self.assertEqual(standardized.framework.get("version"), "0.3.44")
        
        # Check that model info was extracted
        self.assertEqual(standardized.model.get("name"), "ChatAnthropic")
        self.assertEqual(standardized.model.get("type"), "completion")
        
        # Check that call stack was extracted
        self.assertEqual(len(standardized.call_stack), 1)
        self.assertEqual(standardized.call_stack[0].get("file"), "test_file.py")
        
        # Check that security info was extracted
        self.assertEqual(standardized.security.get("alert_level"), "none")
        
        # Check that performance metrics were extracted
        self.assertTrue("timestamp" in standardized.performance)
        
        # Check event category
        self.assertEqual(standardized.event_category, "llm_request")
        
    def test_convert_response_event(self):
        """Test conversion of a LangChain response event."""
        # Convert the event
        standardized = self.converter.convert(self.response_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:11.006702")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_response")
        self.assertEqual(standardized.channel, "LANGCHAIN")
        self.assertEqual(standardized.direction, "incoming")
        self.assertEqual(standardized.session_id, "langchain-1742216889.9256918")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that response data was extracted
        self.assertIsNotNone(standardized.response)
        self.assertTrue("content" in standardized.response)
        self.assertTrue("llm_output" in standardized.response)
        
        # Check that performance metrics were extracted
        self.assertTrue("duration_ms" in standardized.performance)
        
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