"""
Tests for the default event converter.

This module contains tests for verifying the correct behavior of the default event converter,
which is used for events that don't match any specific framework.
"""

import unittest
from datetime import datetime

from cylestio_monitor.events.converters.default import DefaultEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestDefaultConverter(unittest.TestCase):
    """Test case for the default event converter."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.converter = DefaultEventConverter()
        
        # Create sample events for testing
        self.unknown_request_event = {
            "timestamp": "2025-03-17T14:08:09.925710",
            "level": "INFO",
            "agent_id": "unknown-agent",
            "event_type": "unknown_request",
            "channel": "UNKNOWN",
            "direction": "outgoing",
            "data": {
                "content": "Unknown request data",
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 10, "function": "test_func"}
                ]
            }
        }
        
        self.unknown_response_event = {
            "timestamp": "2025-03-17T14:08:11.006702",
            "level": "INFO",
            "agent_id": "unknown-agent",
            "event_type": "unknown_response",
            "channel": "UNKNOWN",
            "direction": "incoming",
            "data": {
                "content": "Unknown response data",
                "run_id": "1742216889.9256918",
                "call_stack": [
                    {"file": "test_file.py", "line": 20, "function": "test_response"}
                ]
            }
        }
        
        self.generic_event = {
            "timestamp": "2025-03-17T14:08:12.345678",
            "level": "INFO",
            "agent_id": "unknown-agent",
            "event_type": "generic_event",
            "channel": "UNKNOWN",
            "data": {
                "some_field": "some_value",
                "another_field": 123,
                "nested": {
                    "value": "nested_value"
                }
            }
        }
        
    def test_convert_unknown_request_event(self):
        """Test conversion of an unknown request event."""
        # Convert the event
        standardized = self.converter.convert(self.unknown_request_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:09.925710")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "unknown-agent")
        self.assertEqual(standardized.event_type, "unknown_request")
        self.assertEqual(standardized.channel, "UNKNOWN")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # Check that call stack was extracted
        self.assertEqual(len(standardized.call_stack), 1)
        
        # For a request event with direction "outgoing", data should be in request
        self.assertIsNotNone(standardized.request)
        
        # Original data should be preserved in extra
        self.assertEqual(standardized.extra["content"], "Unknown request data")
        
    def test_convert_unknown_response_event(self):
        """Test conversion of an unknown response event."""
        # Convert the event
        standardized = self.converter.convert(self.unknown_response_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:11.006702")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "unknown-agent")
        self.assertEqual(standardized.event_type, "unknown_response")
        self.assertEqual(standardized.channel, "UNKNOWN")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
        
        # For a response event with direction "incoming", data should be in response
        self.assertIsNotNone(standardized.response)
        
        # Original data should be preserved in extra
        self.assertEqual(standardized.extra["content"], "Unknown response data")
        
    def test_convert_generic_event(self):
        """Test conversion of a generic event with no clear type."""
        # Convert the event
        standardized = self.converter.convert(self.generic_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.timestamp, "2025-03-17T14:08:12.345678")
        self.assertEqual(standardized.level, "INFO")
        self.assertEqual(standardized.agent_id, "unknown-agent")
        self.assertEqual(standardized.event_type, "generic_event")
        self.assertEqual(standardized.channel, "UNKNOWN")
        
        # Check that all original data is preserved in extra
        self.assertEqual(standardized.extra["some_field"], "some_value")
        self.assertEqual(standardized.extra["another_field"], 123)
        self.assertEqual(standardized.extra["nested"]["value"], "nested_value")


if __name__ == "__main__":
    unittest.main() 