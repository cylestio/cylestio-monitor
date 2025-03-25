"""
Tests for the MCP event converter.

This module contains tests for verifying the correct behavior of the MCP event converter.
"""

import unittest
from datetime import datetime

from cylestio_monitor.events.converters.mcp import MCPEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestMCPConverter(unittest.TestCase):
    """Test case for the MCP event converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = MCPEventConverter()
        
        # Create sample events for testing
        self.mcp_patch_event = {
            "timestamp": "2025-03-17T14:08:09.822263",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "MCP_patch",
            "channel": "SYSTEM",
            "data": {
                "message": "MCP client patched",
                "call_stack": [
                    {"file": "test_file.py", "line": 10, "function": "test_func"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {"message": {"alert_level": "none"}}
                },
                "framework": {
                    "name": "system",
                    "version": None,
                    "components": {}
                },
                "performance": {"timestamp": "2025-03-17T14:08:09.868375"}
            }
        }
        
        self.monitoring_enabled_event = {
            "timestamp": "2025-03-17T14:08:09.921630",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "monitoring_enabled",
            "channel": "SYSTEM",
            "data": {
                "agent_id": "chatbot-agent",
                "LLM_provider": "MCP",
                "call_stack": [
                    {"file": "test_file.py", "line": 20, "function": "test_enable"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                },
                "framework": {
                    "name": "system",
                    "version": None,
                    "components": {}
                },
                "performance": {"timestamp": "2025-03-17T14:08:09.921882"}
            }
        }
        
        self.user_message_event = {
            "timestamp": "2025-03-17T14:08:09.930000",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "user_message",
            "channel": "SYSTEM",
            "data": {
                "content": "Hello, can you help me?",
                "metadata": {"session_id": "user-123"},
                "call_stack": [
                    {"file": "test_file.py", "line": 30, "function": "test_user_message"}
                ],
                "security": {
                    "alert_level": "none",
                    "field_checks": {}
                }
            }
        }
        
    def test_convert_mcp_patch_event(self):
        """Test conversion of an MCP patch event."""
        # Convert the event
        standardized = self.converter.convert(self.mcp_patch_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.822263")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "MCP_patch")
        self.assertEqual(standardized.channel, "SYSTEM")
        
        # Check that framework info was extracted
        self.assertEqual(standardized.framework.get("name"), "system")
        
        # Check that message was extracted into request
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("message"), "MCP client patched")
        
        # Check that call stack was extracted
        self.assertEqual(len(standardized.call_stack), 1)
        self.assertEqual(standardized.call_stack[0].get("file"), "test_file.py")
        
        # Check that security info was extracted
        self.assertEqual(standardized.security.get("alert_level"), "none")
        
        # Check event category
        self.assertEqual(standardized.event_category, "system")
        
    def test_convert_monitoring_enabled_event(self):
        """Test conversion of a monitoring enabled event."""
        # Convert the event
        standardized = self.converter.convert(self.monitoring_enabled_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.921630")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "monitoring_enabled")
        self.assertEqual(standardized.channel, "SYSTEM")
        
        # Check that monitoring details were extracted into request
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("agent_id"), "chatbot-agent")
        self.assertEqual(standardized.request.get("LLM_provider"), "MCP")
        
        # Check event category
        self.assertEqual(standardized.event_category, "system")
        
    def test_convert_user_message_event(self):
        """Test conversion of a user message event."""
        # Convert the event
        standardized = self.converter.convert(self.user_message_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.930000")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "user_message")
        self.assertEqual(standardized.channel, "SYSTEM")
        
        # Check that user message details were extracted into request
        self.assertIsNotNone(standardized.request)
        self.assertEqual(standardized.request.get("content"), "Hello, can you help me?")
        self.assertEqual(standardized.request.get("metadata"), {"session_id": "user-123"})
        
        # Check event category
        self.assertEqual(standardized.event_category, "user_interaction")


if __name__ == "__main__":
    unittest.main() 