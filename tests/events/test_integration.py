"""
Integration tests for the event conversion pipeline.

This module contains tests that verify the complete event conversion process,
from raw event to standardized schema.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from cylestio_monitor.events.registry import converter_factory
from cylestio_monitor.events.processor import create_standardized_event, process_event
from cylestio_monitor.events.schema import StandardizedEvent
from cylestio_monitor.events_processor import process_standardized_event


class TestEventConversionPipeline(unittest.TestCase):
    """Test case for the end-to-end event conversion pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample events for testing
        self.sample_event = {
            "timestamp": "2025-03-17T14:08:09.925710",
            "level": "INFO",
            "agent_id": "chatbot-agent",
            "event_type": "model_request",
            "channel": "LANGCHAIN",
            "direction": "outgoing",
            "session_id": "langchain-1742216889.9256918",
            "data": {
                "llm_type": "ChatAnthropic",
                "model": {"name": "ChatAnthropic", "type": "completion"},
                "prompts": ["System prompt", "User message"],
                "run_id": "1742216889.9256918"
            }
        }
        
        # Create sample input for create_standardized_event
        self.sample_input = {
            "agent_id": "chatbot-agent",
            "event_type": "model_request",
            "data": {
                "llm_type": "ChatAnthropic",
                "model": {"name": "ChatAnthropic", "type": "completion"},
                "prompts": ["System prompt", "User message"],
                "run_id": "1742216889.9256918"
            },
            "channel": "LANGCHAIN",
            "level": "info",
            "direction": "outgoing",
            "session_id": "langchain-1742216889.9256918"
        }
        
    def test_process_event(self):
        """Test the process_event function with a sample event."""
        # Process the event
        standardized = process_event(self.sample_event)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_request")
        self.assertEqual(standardized.channel, "LANGCHAIN")
        
        # Check that request data was extracted
        self.assertIsNotNone(standardized.request)
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
    
    def test_create_standardized_event(self):
        """Test the create_standardized_event function with sample input."""
        # Create a standardized event
        standardized = create_standardized_event(**self.sample_input)
        
        # Check that it's a StandardizedEvent instance
        self.assertIsInstance(standardized, StandardizedEvent)
        
        # Check common fields
        self.assertEqual(standardized.agent_id, "chatbot-agent")
        self.assertEqual(standardized.event_type, "model_request")
        self.assertEqual(standardized.channel, "LANGCHAIN")
        self.assertEqual(standardized.direction, "outgoing")
        self.assertEqual(standardized.session_id, "langchain-1742216889.9256918")
        
        # Check that trace_id was extracted
        self.assertEqual(standardized.trace_id, "1742216889.9256918")
    
    @patch('cylestio_monitor.events_processor.log_to_file')
    @patch('cylestio_monitor.events_processor.log_to_db')
    @patch('cylestio_monitor.events_processor.config_manager.get')
    def test_process_standardized_event(self, mock_config_get, mock_log_to_db, mock_log_to_file):
        """Test the process_standardized_event function with mocked logging."""
        # Configure mocks
        mock_log_to_db.return_value = None
        mock_log_to_file.return_value = None
        # Mock the config_manager.get call to return a log file path
        mock_config_get.return_value = "test_log_file.json"
        
        # Call the function
        process_standardized_event(**self.sample_input)
        
        # Check that log_to_file was called
        mock_log_to_file.assert_called_once()
        
        # Check that log_to_db was called
        mock_log_to_db.assert_called_once()
        
        # Check the arguments passed to log_to_db
        args, kwargs = mock_log_to_db.call_args
        self.assertEqual(kwargs["agent_id"], "chatbot-agent")
        self.assertEqual(kwargs["event_type"], "model_request")
        self.assertEqual(kwargs["channel"], "LANGCHAIN")
        self.assertEqual(kwargs["level"], "info")
        self.assertEqual(kwargs["direction"], "outgoing")
        
        # Check that the data passed to log_to_db is a dictionary
        self.assertIsInstance(kwargs["data"], dict)
        self.assertIn("event_category", kwargs["data"])
        self.assertEqual(kwargs["data"]["event_category"], "llm_request")
    
    def test_end_to_end_conversion(self):
        """Test the complete end-to-end conversion process."""
        # Create a standardized event
        standardized = create_standardized_event(**self.sample_input)
        
        # Convert to dictionary
        event_dict = standardized.to_dict()
        
        # Check that the dictionary contains all expected fields
        self.assertIn("timestamp", event_dict)
        self.assertIn("level", event_dict)
        self.assertIn("agent_id", event_dict)
        self.assertIn("event_type", event_dict)
        self.assertIn("channel", event_dict)
        self.assertIn("event_category", event_dict)
        self.assertIn("direction", event_dict)
        self.assertIn("session_id", event_dict)
        self.assertIn("trace_id", event_dict)
        
        # Check that we can recreate a StandardizedEvent from the dictionary
        reconstructed = StandardizedEvent.from_dict(event_dict)
        
        # Check that the reconstructed event has the same values
        self.assertEqual(reconstructed.agent_id, standardized.agent_id)
        self.assertEqual(reconstructed.event_type, standardized.event_type)
        self.assertEqual(reconstructed.channel, standardized.channel)
        self.assertEqual(reconstructed.direction, standardized.direction)
        self.assertEqual(reconstructed.session_id, standardized.session_id)
        self.assertEqual(reconstructed.trace_id, standardized.trace_id)
        self.assertEqual(reconstructed.event_category, standardized.event_category)


if __name__ == "__main__":
    unittest.main() 