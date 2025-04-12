"""
Tests for the Events Module in Cylestio Monitor.

This file contains tests for the event logging, creation, and processing 
functionality in the events module, focusing on OpenTelemetry-based interfaces.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from cylestio_monitor.events import (
    StandardizedEvent,
    log_event,
    log_info,
    log_warning,
    log_error
)
from cylestio_monitor.utils.trace_context import TraceContext
from cylestio_monitor.utils.event_utils import format_timestamp


class TestEventSchema:
    """Tests for the event schema and conversion functionality."""
    
    def test_standardized_event_creation(self):
        """Test creating a StandardizedEvent instance."""
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        
        # Basic assertions
        assert event.level == "INFO"
        assert event.agent_id == "test-agent"
        assert event.name == "test.event"
        assert event.event_category == "system"  # Default category
        
    def test_standardized_event_with_attributes(self):
        """Test StandardizedEvent with attributes."""
        attributes = {
            "key1": "value1",
            "key2": 123,
            "key3": {"nested": "value"}
        }
        
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="test.event",
            attributes=attributes
        )
        
        # Check that attributes are properly set
        assert event.attributes == attributes
        
        # Check to_dict includes attributes
        event_dict = event.to_dict()
        assert "attributes" in event_dict
        assert event_dict["attributes"] == attributes
        
    def test_standardized_event_category_determination(self):
        """Test event category determination based on name."""
        # User event
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="user.input"
        )
        assert event.event_category == "user_interaction"
        
        # LLM event
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="llm.completion"
        )
        assert event.event_category == "llm"
        
        # Tool event
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="tool.execution"
        )
        assert event.event_category == "tool"
        
    def test_standardized_event_timestamp_handling(self):
        """Test standardized event handles various timestamp formats correctly."""
        # Test with datetime without timezone (naive)
        naive_dt = datetime(2023, 1, 1, 12, 0, 0)
        event = StandardizedEvent(
            timestamp=naive_dt,
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        assert event.timestamp.endswith('Z')  # Should end with Z
        assert "2023-01-01T12:00:00" in event.timestamp  # Base time should be preserved
        
        # Test with datetime with UTC timezone
        utc_dt = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        event = StandardizedEvent(
            timestamp=utc_dt,
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T12:00:00" in event.timestamp
        
        # Test with ISO string with Z suffix
        iso_z = "2023-01-01T12:00:00Z"
        event = StandardizedEvent(
            timestamp=iso_z,
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T12:00:00" in event.timestamp
        
        # Test with ISO string with +00:00 suffix
        iso_offset = "2023-01-01T12:00:00+00:00"
        event = StandardizedEvent(
            timestamp=iso_offset,
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T12:00:00" in event.timestamp
        assert "+00:00" not in event.timestamp
        
        # Test with non-UTC timezone string
        non_utc = "2023-01-01T12:00:00+05:00"  # UTC+5
        event = StandardizedEvent(
            timestamp=non_utc,
            level="INFO",
            agent_id="test-agent",
            name="test.event"
        )
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T07:00:00" in event.timestamp  # Should be converted to UTC (12-5=7)
        
    def test_from_dict_timestamp_handling(self):
        """Test from_dict method handles timestamps correctly."""
        # Test with ISO string with Z suffix
        event_dict = {
            "timestamp": "2023-01-01T12:00:00Z",
            "level": "INFO",
            "agent_id": "test-agent",
            "name": "test.event"
        }
        event = StandardizedEvent.from_dict(event_dict)
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T12:00:00" in event.timestamp
        
        # Test with ISO string with timezone offset
        event_dict = {
            "timestamp": "2023-01-01T12:00:00+05:00",
            "level": "INFO",
            "agent_id": "test-agent",
            "name": "test.event"
        }
        event = StandardizedEvent.from_dict(event_dict)
        assert event.timestamp.endswith('Z')
        assert "2023-01-01T07:00:00" in event.timestamp  # Should be converted to UTC
        
        # Test with no timestamp (should use current time)
        event_dict = {
            "level": "INFO",
            "agent_id": "test-agent",
            "name": "test.event"
        }
        event = StandardizedEvent.from_dict(event_dict)
        assert event.timestamp.endswith('Z')
        
        # Test that the timestamp is in the right format by comparing with format_timestamp output
        iso_string = "2023-01-01T12:00:00Z"
        expected = format_timestamp(iso_string)
        event_dict = {
            "timestamp": iso_string,
            "level": "INFO",
            "agent_id": "test-agent",
            "name": "test.event"
        }
        event = StandardizedEvent.from_dict(event_dict)
        assert event.timestamp == expected
        
    def test_from_dict_conversion(self):
        """Test creating StandardizedEvent from dictionary."""
        event_dict = {
            "timestamp": "2023-01-01T12:00:00Z",
            "level": "WARNING",
            "agent_id": "test-agent",
            "name": "test.warning",
            "trace_id": "trace123",
            "span_id": "span456",
            "attributes": {"key": "value"}
        }
        
        event = StandardizedEvent.from_dict(event_dict)
        
        assert event.level == "WARNING"
        assert event.name == "test.warning"
        assert event.trace_id == "trace123"
        assert event.span_id == "span456"
        assert event.attributes["key"] == "value"
        
    def test_legacy_fields_migration(self):
        """Test migration of legacy fields to attributes."""
        # Create event with legacy fields
        event = StandardizedEvent(
            timestamp=datetime.now(),
            level="INFO",
            agent_id="test-agent",
            name="test.event",
            channel="LLM",
            direction="outgoing",
            session_id="session123",
            model={"name": "gpt-4", "temperature": 0.7}
        )
        
        # Check that legacy fields are moved to attributes
        assert "channel" in event.attributes
        assert event.attributes["channel"] == "LLM"
        assert "direction" in event.attributes
        assert event.attributes["direction"] == "outgoing"
        assert "session_id" in event.attributes
        assert event.attributes["session_id"] == "session123"
        assert "llm.name" in event.attributes
        assert event.attributes["llm.name"] == "gpt-4"
        assert "llm.temperature" in event.attributes
        assert event.attributes["llm.temperature"] == 0.7


class TestEventLogging:
    """Tests for event logging functionality."""
    
    def setup_method(self):
        """Set up for each test - initialize trace context."""
        # Reset trace context
        TraceContext.reset()
        # Initialize a new trace
        TraceContext.initialize_trace("test-agent")
        
    @patch("cylestio_monitor.utils.event_logging._write_to_log_file")
    @patch("cylestio_monitor.utils.event_logging._send_to_api")
    def test_log_event(self, mock_send_to_api, mock_write_to_log_file):
        """Test logging an event."""
        event_dict = log_event(
            name="test.event",
            attributes={"key": "value"},
            level="info"
        )
        
        assert isinstance(event_dict, dict)
        assert event_dict["name"] == "test.event"
        assert event_dict["level"] == "INFO"
        assert event_dict["attributes"]["key"] == "value"
        assert "trace_id" in event_dict
        
        # Check that write and send functions were called
        mock_write_to_log_file.assert_called_once()
        mock_send_to_api.assert_called_once()
        
    @patch("cylestio_monitor.utils.event_logging._write_to_log_file")
    @patch("cylestio_monitor.utils.event_logging._send_to_api")
    def test_log_event_with_trace_context(self, mock_send_to_api, mock_write_to_log_file):
        """Test logging an event with trace context."""
        # Start a span
        span_info = TraceContext.start_span("test-span")
        
        # Log event
        event_dict = log_event(
            name="test.event",
            attributes={"key": "value"}
        )
        
        # Verify trace context
        assert event_dict["trace_id"] == span_info["trace_id"]
        assert event_dict["span_id"] == span_info["span_id"]
        
        # End span
        TraceContext.end_span()
        
    @patch("cylestio_monitor.utils.event_logging._write_to_log_file")
    @patch("cylestio_monitor.utils.event_logging._send_to_api")
    def test_log_event_with_attributes(self, mock_send_to_api, mock_write_to_log_file):
        """Test logging an event with attributes."""
        attributes = {
            "component": "test-component",
            "operation": "test-operation",
            "details": {"subkey": "value"}
        }
        
        event_dict = log_event(
            name="test.event",
            attributes=attributes
        )
        
        # Check that attributes are properly included
        for key, value in attributes.items():
            assert event_dict["attributes"][key] == value
        
    @patch("cylestio_monitor.utils.event_logging.log_event")
    def test_log_info(self, mock_log_event):
        """Test log_info function."""
        log_info(
            name="test.info",
            attributes={"key": "value"}
        )
        
        # Verify log_event was called with INFO level
        mock_log_event.assert_called_once_with(
            name="test.info",
            attributes={"key": "value"},
            level="INFO"
        )
        
    @patch("cylestio_monitor.utils.event_logging.log_event")
    def test_log_warning(self, mock_log_event):
        """Test log_warning function."""
        log_warning(
            name="test.warning",
            attributes={"key": "value"}
        )
        
        # Verify log_event was called with WARNING level
        mock_log_event.assert_called_once_with(
            name="test.warning",
            attributes={"key": "value"},
            level="WARNING"
        )
        
    @patch("cylestio_monitor.utils.event_logging.log_event")
    def test_log_error(self, mock_log_event):
        """Test log_error function."""
        error = ValueError("Test error")
        
        log_error(
            name="test.error",
            error=error
        )
        
        # Get the call arguments
        args, kwargs = mock_log_event.call_args
        
        # Verify log_event was called with ERROR level
        assert kwargs["name"] == "test.error"
        assert kwargs["level"] == "ERROR"
        assert "error.type" in kwargs["attributes"]
        assert kwargs["attributes"]["error.type"] == "ValueError"
        assert "error.message" in kwargs["attributes"]
        assert kwargs["attributes"]["error.message"] == "Test error" 