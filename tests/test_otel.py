"""
Tests for the OpenTelemetry ID generation and event structure.
"""

import unittest
import re
from datetime import datetime
from typing import Dict, Any

from cylestio_monitor.utils.otel import (
    generate_trace_id,
    generate_span_id,
    generate_trace_context,
    get_or_create_agent_trace_context,
    create_child_span
)
from cylestio_monitor.events.schema import StandardizedEvent


class TestOtelIdGeneration(unittest.TestCase):
    """Test case for OpenTelemetry ID generation."""
    
    def test_trace_id_format(self):
        """Test that generated trace IDs have the correct format."""
        trace_id = generate_trace_id()
        
        # Trace ID should be a 32-character hex string
        self.assertEqual(len(trace_id), 32)
        # Should match hexadecimal pattern
        self.assertTrue(re.match(r'^[0-9a-f]{32}$', trace_id))
    
    def test_span_id_format(self):
        """Test that generated span IDs have the correct format."""
        span_id = generate_span_id()
        
        # Span ID should be a 16-character hex string
        self.assertEqual(len(span_id), 16)
        # Should match hexadecimal pattern
        self.assertTrue(re.match(r'^[0-9a-f]{16}$', span_id))
    
    def test_generate_trace_context(self):
        """Test generating a complete trace context."""
        context = generate_trace_context()
        
        # Should have trace_id and span_id
        self.assertIn('trace_id', context)
        self.assertIn('span_id', context)
        self.assertIn('parent_span_id', context)
        
        # Parent span ID should be None if not provided
        self.assertIsNone(context['parent_span_id'])
        
        # With parent span ID
        parent_span_id = generate_span_id()
        context = generate_trace_context(parent_span_id)
        self.assertEqual(context['parent_span_id'], parent_span_id)
    
    def test_agent_trace_context(self):
        """Test getting or creating a trace context for an agent."""
        agent_id = "test-agent"
        
        # First call should create a new context
        context1 = get_or_create_agent_trace_context(agent_id)
        
        # Should have trace_id and span_id
        self.assertIn('trace_id', context1)
        self.assertIn('span_id', context1)
        
        # Second call should return the same trace ID but the same span ID
        context2 = get_or_create_agent_trace_context(agent_id)
        self.assertEqual(context1['trace_id'], context2['trace_id'])
        self.assertEqual(context1['span_id'], context2['span_id'])
        
        # Different agent should have different trace ID
        other_agent_context = get_or_create_agent_trace_context("other-agent")
        self.assertNotEqual(context1['trace_id'], other_agent_context['trace_id'])
    
    def test_create_child_span(self):
        """Test creating a child span for the current trace."""
        agent_id = "test-agent-for-child-span"  # Use a unique agent ID to avoid conflicts with other tests
        
        # First call initializes the context
        trace_id, span_id, parent_span_id = create_child_span(agent_id)
        
        # Save the first span ID
        first_span_id = span_id
        
        # Second call should create a child span
        new_trace_id, new_span_id, new_parent_span_id = create_child_span(agent_id)
        
        # Trace ID should remain the same
        self.assertEqual(trace_id, new_trace_id)
        # Span ID should change
        self.assertNotEqual(first_span_id, new_span_id)
        # Parent span ID should be the previous span ID
        self.assertEqual(first_span_id, new_parent_span_id)


class TestOtelEventStructure(unittest.TestCase):
    """Test case for OpenTelemetry event structure."""
    
    def test_standardized_event_with_otel_fields(self):
        """Test that StandardizedEvent properly handles OTel fields."""
        # Create a standardized event with OTel fields
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            event_type="llm.completion",
            channel="LLM",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            parent_span_id="85e2534a0d55617a",
            model={"llm.model": "claude-3-haiku-20240307"},
            performance={"llm.usage.input_tokens": 493, "llm.usage.output_tokens": 51}
        )
        
        # Convert to dict
        event_dict = event.to_dict()
        
        # Check OTel fields
        self.assertEqual(event_dict['trace_id'], "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(event_dict['span_id'], "00f067aa0ba902b7")
        self.assertEqual(event_dict['parent_span_id'], "85e2534a0d55617a")
        
        # Check standardized field structure
        self.assertEqual(event_dict['event_type'], "llm.completion")
        self.assertEqual(event_dict['model']['llm.model'], "claude-3-haiku-20240307")
        self.assertEqual(event_dict['performance']['llm.usage.input_tokens'], 493)
    
    def test_standardized_event_from_dict(self):
        """Test creating a StandardizedEvent from a dictionary."""
        # Create a dictionary with OTel fields
        data = {
            "timestamp": datetime.now().isoformat(),
            "level": "INFO",
            "agent_id": "weather-agent",
            "event_type": "llm.completion",
            "channel": "LLM",
            "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
            "span_id": "00f067aa0ba902b7",
            "parent_span_id": "85e2534a0d55617a",
            "model": {
                "llm.model": "claude-3-haiku-20240307",
                "llm.temperature": 0.7
            },
            "performance": {
                "llm.usage.prompt_tokens": 493,
                "llm.usage.completion_tokens": 51
            },
            "request": {
                "caller.file": "weather_client.py",
                "caller.line": 117,
                "caller.function": "process_query"
            }
        }
        
        # Create event from dict
        event = StandardizedEvent.from_dict(data)
        
        # Check fields
        self.assertEqual(event.trace_id, "4bf92f3577b34da6a3ce929d0e0e4736")
        self.assertEqual(event.span_id, "00f067aa0ba902b7")
        self.assertEqual(event.parent_span_id, "85e2534a0d55617a")
        self.assertEqual(event.event_type, "llm.completion")
        
        # Convert back to dict and check
        event_dict = event.to_dict()
        self.assertEqual(event_dict['model']['llm.model'], "claude-3-haiku-20240307")
        self.assertEqual(event_dict['performance']['llm.usage.prompt_tokens'], 493)
        self.assertEqual(event_dict['request']['caller.file'], "weather_client.py")


if __name__ == '__main__':
    unittest.main() 