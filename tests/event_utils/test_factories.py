"""
Tests for event factory functions in cylestio_monitor.events.factories.

These tests verify that event factory functions handle timestamps correctly,
including both datetime objects and ISO8601 strings.
"""

import datetime
from datetime import timezone
import pytest

from cylestio_monitor.events.factories import (
    create_llm_request_event,
    create_llm_response_event,
    create_tool_call_event,
    create_tool_result_event,
    create_system_event,
    create_agent_startup_event,
    create_agent_shutdown_event,
    create_error_event
)


class TestEventFactoryFunctions:
    """Tests for event factory functions."""

    def test_create_llm_request_event_with_datetime(self):
        """Test LLM request event creation with datetime timestamp."""
        # Create a timezone-aware datetime
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        
        # Create event with datetime
        event = create_llm_request_event(
            agent_id="test-agent",
            provider="openai",
            model="gpt-4",
            prompt="Test prompt",
            timestamp=test_dt
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.123456Z"
        # Verify timestamp in attributes
        assert event["attributes"]["llm.request.timestamp"] == "2023-09-15T14:30:45.123456Z"

    def test_create_llm_request_event_with_string(self):
        """Test LLM request event creation with ISO8601 string timestamp."""
        # Create event with ISO8601 string
        event = create_llm_request_event(
            agent_id="test-agent",
            provider="openai",
            model="gpt-4",
            prompt="Test prompt",
            timestamp="2023-09-15T14:30:45.123456+00:00"
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.123456Z"
        # Verify timestamp in attributes
        assert event["attributes"]["llm.request.timestamp"] == "2023-09-15T14:30:45.123456Z"

    def test_create_llm_request_event_with_naive_datetime(self):
        """Test LLM request event creation with naive datetime timestamp."""
        # Create a naive datetime (no timezone)
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456)
        
        # Create event with naive datetime
        event = create_llm_request_event(
            agent_id="test-agent",
            provider="openai",
            model="gpt-4",
            prompt="Test prompt",
            timestamp=test_dt
        )
        
        # Verify timestamp in event (should have Z suffix)
        assert event["timestamp"].endswith("Z")
        # Verify timestamp in attributes
        assert event["attributes"]["llm.request.timestamp"].endswith("Z")

    def test_create_llm_response_event_with_string(self):
        """Test LLM response event creation with ISO8601 string timestamp."""
        # Create event with ISO8601 string with Z suffix
        event = create_llm_response_event(
            agent_id="test-agent",
            provider="openai",
            model="gpt-4",
            response="Test response",
            timestamp="2023-09-15T14:30:45Z"
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
        # Verify timestamp in attributes
        assert event["attributes"]["llm.response.timestamp"] == "2023-09-15T14:30:45.000000Z"

    def test_create_tool_call_event_with_datetime(self):
        """Test tool call event creation with datetime timestamp."""
        # Create a timezone-aware datetime
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        
        # Create event with datetime
        event = create_tool_call_event(
            agent_id="test-agent",
            tool_name="test-tool",
            inputs={"param1": "value1"},
            timestamp=test_dt
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.123456Z"
        # Verify timestamp in attributes
        assert event["attributes"]["tool.call.timestamp"] == "2023-09-15T14:30:45.123456Z"

    def test_create_tool_result_event_with_string(self):
        """Test tool result event creation with ISO8601 string timestamp."""
        # Create event with ISO8601 string
        event = create_tool_result_event(
            agent_id="test-agent",
            tool_name="test-tool",
            inputs={"param1": "value1"},
            output="Tool result",
            timestamp="2023-09-15T14:30:45+00:00"
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
        # Verify timestamp in attributes
        assert event["attributes"]["tool.result.timestamp"] == "2023-09-15T14:30:45.000000Z"

    def test_create_system_event_with_datetime(self):
        """Test system event creation with datetime timestamp."""
        # Create a timezone-aware datetime
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        
        # Create event with datetime
        event = create_system_event(
            agent_id="test-agent",
            event_type="test-event",
            data={"key1": "value1"},
            timestamp=test_dt
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.123456Z"
        # Verify timestamp in attributes
        assert event["attributes"]["system.timestamp"] == "2023-09-15T14:30:45.123456Z"

    def test_create_agent_startup_event_with_string(self):
        """Test agent startup event creation with ISO8601 string timestamp."""
        # Create event with ISO8601 string
        event = create_agent_startup_event(
            agent_id="test-agent",
            version="1.0.0",
            configuration={"setting1": "value1"},
            timestamp="2023-09-15T14:30:45Z"
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.000000Z"
        # Verify timestamp in attributes
        assert event["attributes"]["agent.startup.timestamp"] == "2023-09-15T14:30:45.000000Z"

    def test_create_error_event_with_datetime(self):
        """Test error event creation with datetime timestamp."""
        # Create a timezone-aware datetime
        test_dt = datetime.datetime(2023, 9, 15, 14, 30, 45, 123456, tzinfo=timezone.utc)
        
        # Create event with datetime
        event = create_error_event(
            agent_id="test-agent",
            error_type="ValueError",
            message="Test error message",
            timestamp=test_dt
        )
        
        # Verify timestamp in event
        assert event["timestamp"] == "2023-09-15T14:30:45.123456Z"
        # Verify timestamp in attributes
        assert event["attributes"]["error.timestamp"] == "2023-09-15T14:30:45.123456Z"

    def test_default_timestamp(self):
        """Test event creation with default timestamp (None)."""
        # Create event without specifying timestamp
        event = create_llm_request_event(
            agent_id="test-agent",
            provider="openai",
            model="gpt-4",
            prompt="Test prompt"
        )
        
        # Verify timestamp exists and has correct format
        assert "timestamp" in event
        assert event["timestamp"].endswith("Z")  # Should end with Z suffix
        assert "T" in event["timestamp"]  # Should have T separator
        
        # Verify timestamp in attributes
        assert "llm.request.timestamp" in event["attributes"]
        assert event["attributes"]["llm.request.timestamp"].endswith("Z") 