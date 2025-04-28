import json
from typing import Dict, Any

import pytest

from cylestio_monitor.events.converters.openai import OpenAIEventConverter
from cylestio_monitor.events.schema import StandardizedEvent


class TestOpenAIConverter:
    """Tests for the OpenAI event converter."""

    def test_response_with_token_usage(self):
        """Test that token usage is properly included in converted events."""
        # Create a mock OpenAI response event with token usage information
        openai_event = {
            "timestamp": "2023-01-01T00:00:00.000000Z",
            "level": "INFO",
            "agent_id": "test-agent",
            "channel": "OPENAI",
            "event_type": "llm.call.finish",
            "data": {
                "model": "gpt-4",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150
                },
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "This is a test response"
                        },
                        "finish_reason": "stop"
                    }
                ]
            }
        }

        # Convert the event using the OpenAI converter
        converter = OpenAIEventConverter()
        standardized_event = converter.convert(openai_event)

        # Check if the standardized event is returned
        assert isinstance(standardized_event, StandardizedEvent)

        # Check that token usage metrics are included in the performance section
        assert "llm.usage.input_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.input_tokens"] == 100
        
        assert "llm.usage.output_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.output_tokens"] == 50
        
        assert "llm.usage.total_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.total_tokens"] == 150

    def test_response_from_patcher_format(self):
        """Test that token usage from patcher format is also included."""
        # Create a mock event as it would come from the OpenAI patcher
        patcher_event = {
            "timestamp": "2023-01-01T00:00:00.000000Z",
            "level": "INFO",
            "agent_id": "test-agent",
            "channel": "OPENAI",
            "event_type": "llm.call.finish",
            "data": {
                "model": "gpt-4",
                "llm.usage.input_tokens": 100,
                "llm.usage.output_tokens": 50,
                "llm.usage.total_tokens": 150
            }
        }

        # Convert the event using the OpenAI converter
        converter = OpenAIEventConverter()
        standardized_event = converter.convert(patcher_event)

        # Check that token usage metrics are included in the performance section
        assert "llm.usage.input_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.input_tokens"] == 100
        
        assert "llm.usage.output_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.output_tokens"] == 50
        
        assert "llm.usage.total_tokens" in standardized_event.performance
        assert standardized_event.performance["llm.usage.total_tokens"] == 150 